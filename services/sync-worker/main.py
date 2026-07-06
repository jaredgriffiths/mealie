"""Mealie Firebase Outbound Sync Worker Daemon.

This service acts as a secure, real-time data bridge between a local self-hosted
Mealie instance and Google Cloud Firestore. It uses real-time snapshot listeners
to capture cloud changes, resolves conflicts using Last-Write-Wins (LWW), and
interfaces back to Mealie's REST API.
"""

import os
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment configurations
load_dotenv()

MEALIE_API_URL = os.getenv("MEALIE_API_URL", "http://mealie:9000")
MEALIE_API_TOKEN = os.getenv("MEALIE_API_TOKEN")
FIREBASE_KEY_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "/app/data/firebase_service_account.json")
CONFIG_PATH = "/app/data/firebase_bridge_config.json"
LOG_FILE_PATH = "/app/data/sync_worker.log"
HEARTBEAT_FILE_PATH = "/app/data/sync_worker_heartbeat.json"

# Configure structured logging (to stdout and shared volume log file)
logger = logging.getLogger("sync-worker")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Console Handler
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

# File Handler (if log file path is writable)
try:
    fh = logging.FileHandler(LOG_FILE_PATH, mode="a")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
except Exception:
    pass

# HTTPX Client headers configuration
MEALIE_HEADERS = {
    "Authorization": f"Bearer {MEALIE_API_TOKEN}",
    "Content-Type": "application/json"
}


class MealieSyncWorker:
    """Outbound Sync Worker orchestrating local Mealie and Firebase Firestore data synchronization."""

    def __init__(self) -> None:
        """Initialize Sync Worker configurations, client state, and events."""
        self.db: Optional[firestore.client.Client] = None
        self.async_http_client = httpx.AsyncClient(base_url=MEALIE_API_URL, headers=MEALIE_HEADERS, timeout=10.0)
        self.is_enabled = False
        self.loop = None

    async def check_config_loop(self) -> None:
        """Periodically check the local bridge config file to update status dynamically."""
        while True:
            if os.path.exists(CONFIG_PATH):
                try:
                    with open(CONFIG_PATH) as f:
                        config = json.load(f)
                        enabled = config.get("enabled", False)
                        if enabled != self.is_enabled:
                            self.is_enabled = enabled
                            logger.info(f"Sync Worker enabled state toggled to: {self.is_enabled}")
                except Exception as e:
                    logger.debug(f"Failed to check config file: {e}")
            await asyncio.sleep(10)

    def initialize_firebase(self) -> bool:
        """Initialize Firebase Admin SDK using the local service account key."""
        if not os.path.exists(FIREBASE_KEY_PATH):
            logger.warning(f"Waiting for Firebase service account JSON key to be uploaded at: {FIREBASE_KEY_PATH}")
            return False

        try:
            try:
                firebase_admin.get_app()
            except ValueError:
                cred = credentials.Certificate(FIREBASE_KEY_PATH)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            logger.info("Firebase Admin SDK successfully initialized.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            return False

    async def update_heartbeat(self) -> None:
        """Periodically write status reports locally and to Firestore."""
        while True:
            # 1. Evaluate current health metrics
            mealie_reachable = False
            try:
                response = await self.async_http_client.get("/api/users/me")
                mealie_reachable = response.status_code == 200
            except Exception:
                pass

            firebase_auth_status = firebase_admin._apps is not None and len(firebase_admin._apps) > 0
            firestore_db_status = self.db is not None

            # 2. Write local JSON heartbeat (so the Mealie UI shows "online" instantly)
            try:
                heartbeat_data = {
                    "last_ping": datetime.now().isoformat(),
                    "status": "online" if self.is_enabled else "disabled",
                    "mealie_reachable": mealie_reachable,
                    "firebase_auth_status": firebase_auth_status,
                    "firestore_db_status": firestore_db_status
                }
                with open(HEARTBEAT_FILE_PATH, "w") as f:
                    json.dump(heartbeat_data, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to write local heartbeat file: {e}")

            # 3. Write cloud heartbeat to Firestore (if enabled and initialized)
            if self.is_enabled and self.db:
                try:
                    # Execute blocking firestore call in the executor pool to prevent blocking the event loop
                    await asyncio.to_thread(self._write_firestore_heartbeat, mealie_reachable)
                except Exception as e:
                    logger.debug(f"Failed to update cloud heartbeat in Firestore: {e}")

            await asyncio.sleep(15)

    def _write_firestore_heartbeat(self, mealie_reachable: bool) -> None:
        """Internal synchronous helper for writing heartbeat to Firestore."""
        if not self.db:
            return
        status_ref = self.db.collection("status").document("sync_worker")
        status_ref.set({
            "last_ping": firestore.SERVER_TIMESTAMP,
            "status": "online",
            "mealie_reachable": mealie_reachable
        })

    async def process_incoming_cloud_recipe(self, doc_id: str, cloud_data: Dict[str, Any]) -> None:
        """Process a recipe updated in the cloud and sync back to local Mealie if applicable."""
        if not self.is_enabled:
            return

        if cloud_data.get("updated_by") == "sync_worker":
            return

        logger.info(f"Incoming cloud modification detected for recipe: {doc_id}")

        recipe_name = cloud_data.get("name", "Unnamed Recipe")
        cloud_updated_str = cloud_data.get("updated_at")

        if not cloud_updated_str:
            logger.warning(f"Skipping sync for {doc_id}: missing 'updated_at' field.")
            return

        try:
            cloud_updated = datetime.fromisoformat(cloud_updated_str.replace("Z", "+00:00"))
        except ValueError:
            logger.error(f"Invalid timestamp format in cloud recipe {doc_id}: {cloud_updated_str}")
            return

        try:
            response = await self.async_http_client.get(f"/api/recipes/{doc_id}")
            if response.status_code == 200:
                local_data = response.json()
                local_updated_str = local_data.get("updated_at", "1970-01-01T00:00:00Z")
                local_updated = datetime.fromisoformat(local_updated_str.replace("Z", "+00:00"))

                if local_updated >= cloud_updated:
                    logger.info(f"Local recipe {doc_id} is newer or equal. Skipping write back.")
                    return
            elif response.status_code == 404:
                logger.info(f"Recipe {doc_id} does not exist locally. Creating a new one...")
            else:
                logger.error(f"Failed to fetch local recipe {doc_id} from Mealie: {response.status_code}")
                return
        except httpx.HTTPError as e:
            logger.error(f"Error communicating with local Mealie API: {e}")
            return

        mealie_payload = {
            "name": recipe_name,
            "description": cloud_data.get("description", ""),
            "recipeIngredient": [{"note": ing} for ing in cloud_data.get("ingredients", [])],
            "recipeInstructions": [{"text": step} for step in cloud_data.get("steps", [])],
        }

        try:
            if response.status_code == 404:
                post_resp = await self.async_http_client.post("/api/recipes", json=mealie_payload)
                if post_resp.status_code == 201:
                    logger.info(f"Successfully created recipe {doc_id} locally.")
                else:
                    logger.error(f"Failed to create recipe locally. Status: {post_resp.status_code}")
            else:
                put_resp = await self.async_http_client.put(f"/api/recipes/{doc_id}", json=mealie_payload)
                if put_resp.status_code == 200:
                    logger.info(f"Successfully updated recipe {doc_id} locally.")
                else:
                    logger.error(f"Failed to update recipe locally. Status: {put_resp.status_code}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to push updates back to Mealie REST API: {e}")

    def on_recipe_snapshot(self, col_snapshot, changes, read_time) -> None:
        """Snapshot listener callback executed by firestore thread pool."""
        for doc in col_snapshot:
            # Safely schedule the asynchronous process loop onto the main event loop
            asyncio.run_coroutine_threadsafe(
                self.process_incoming_cloud_recipe(doc.id, doc.to_dict()),
                self.loop
            )

    async def start_listeners(self) -> None:
        """Register real-time snapshot listeners with automatic reconnection loops."""
        while True:
            if not self.is_enabled:
                await asyncio.sleep(5)
                continue

            if not self.db:
                if not self.initialize_firebase():
                    await asyncio.sleep(15)
                    continue

            logger.info("Setting up real-time snapshot listeners...")
            recipes_ref = self.db.collection("recipes")
            
            try:
                logger.info("Registering snapshot listener on 'recipes'...")
                # Start listener thread in the SDK
                recipes_watch = recipes_ref.on_snapshot(self.on_recipe_snapshot)

                # Keep listener active while enabled
                while self.is_enabled:
                    await asyncio.sleep(10)
                
                recipes_watch.unsubscribe()
            except Exception as e:
                logger.error(f"Firestore snapshot listener encountered an error: {e}. Reconnecting in 15 seconds...")
                await asyncio.sleep(15)

    async def run(self) -> None:
        """Run all concurrent worker event loops under the asyncio event loop."""
        logger.info("Starting Sync Worker daemon (asyncio)...")
        self.loop = asyncio.get_running_loop()
        
        # Start config checker, heartbeat, and listener loops concurrently
        await asyncio.gather(
            self.check_config_loop(),
            self.update_heartbeat(),
            self.start_listeners()
        )

    async def shutdown(self) -> None:
        """Shutdown helper closing asynchronous http connections cleanly."""
        logger.info("Shutting down Sync Worker...")
        await self.async_http_client.aclose()
        logger.info("Sync Worker successfully stopped.")


if __name__ == "__main__":
    worker = MealieSyncWorker()
    try:
        asyncio.run(worker.run())
    except (KeyboardInterrupt, SystemExit):
        asyncio.run(worker.shutdown())
