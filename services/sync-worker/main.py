"""Mealie Firebase Outbound Sync Worker Daemon.

This service acts as a secure, real-time data bridge between a local self-hosted
Mealie instance and Google Cloud Firestore. It uses real-time snapshot listeners
to capture cloud changes, resolves conflicts using Last-Write-Wins (LWW), and
interfaces back to Mealie's REST API.
"""

import os
import time
import logging
import hashlib
import json
from datetime import datetime
from threading import Thread, Event
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

# HTTPX Client configuration for local Mealie calls
MEALIE_HEADERS = {
    "Authorization": f"Bearer {MEALIE_API_TOKEN}",
    "Content-Type": "application/json"
}


class MealieSyncWorker:
    """Outbound Sync Worker orchestrating local Mealie and Firebase Firestore data synchronization."""

    def __init__(self) -> None:
        """Initialize Sync Worker configurations, client state, and events."""
        self.db: Optional[firestore.client.Client] = None
        self.http_client = httpx.Client(base_url=MEALIE_API_URL, headers=MEALIE_HEADERS, timeout=10.0)
        self.shutdown_event = Event()
        self.heartbeat_thread: Optional[Thread] = None
        self.config_checker_thread: Optional[Thread] = None
        self.is_enabled = False

    def check_config_loop(self) -> None:
        """Periodically check the local bridge config file to update status dynamically."""
        while not self.shutdown_event.wait(10):  # Check every 10 seconds
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

    def initialize_firebase(self) -> bool:
        """Initialize Firebase Admin SDK using the local service account key."""
        if not os.path.exists(FIREBASE_KEY_PATH):
            logger.warning(f"Waiting for Firebase service account JSON key to be uploaded at: {FIREBASE_KEY_PATH}")
            return False

        try:
            cred = credentials.Certificate(FIREBASE_KEY_PATH)
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            logger.info("Firebase Admin SDK successfully initialized.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            return False

    def update_heartbeat(self) -> None:
        """Periodically write a host health status heartbeat document to Firestore."""
        while not self.shutdown_event.wait(300):  # Run every 5 minutes
            if not self.is_enabled or not self.db:
                continue

            try:
                # Check local Mealie connectivity
                mealie_reachable = False
                try:
                    response = self.http_client.get("/api/users/me")
                    mealie_reachable = response.status_code == 200
                except httpx.HTTPError:
                    pass

                status_ref = self.db.collection("status").document("sync_worker")
                status_ref.set({
                    "last_ping": firestore.SERVER_TIMESTAMP,
                    "status": "online",
                    "mealie_reachable": mealie_reachable
                })
                logger.debug("Heartbeat status document updated in Firestore.")
            except Exception as e:
                logger.error(f"Failed to update health heartbeat: {e}")

    def process_incoming_cloud_recipe(self, doc_id: str, cloud_data: Dict[str, Any]) -> None:
        """Process a recipe updated in the cloud and sync back to local Mealie if applicable.

        Args:
            doc_id: The Firestore document identifier (matches Mealie recipe UUID).
            cloud_data: The document data dictionary retrieved from Firestore.
        """
        # Do not run if disabled
        if not self.is_enabled:
            return

        # Loop Prevention: Skip updates originated by this worker itself
        if cloud_data.get("updated_by") == "sync_worker":
            return

        logger.info(f"Incoming cloud modification detected for recipe: {doc_id}")

        # Defensive Parsing / Schema Resilience
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

        # Fetch current local Mealie recipe status to resolve conflicts
        try:
            response = self.http_client.get(f"/api/recipes/{doc_id}")
            if response.status_code == 200:
                local_data = response.json()
                local_updated_str = local_data.get("updated_at", "1970-01-01T00:00:00Z")
                local_updated = datetime.fromisoformat(local_updated_str.replace("Z", "+00:00"))

                # Last-Write-Wins (LWW) Conflict Resolution
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

        # Construct Mealie payload format (mapping from our Firestore schema defensively)
        mealie_payload = {
            "name": recipe_name,
            "description": cloud_data.get("description", ""),
            "recipeIngredient": [{"note": ing} for ing in cloud_data.get("ingredients", [])],
            "recipeInstructions": [{"text": step} for step in cloud_data.get("steps", [])],
        }

        # Write updates back to local Mealie
        try:
            if response.status_code == 404:
                post_resp = self.http_client.post("/api/recipes", json=mealie_payload)
                if post_resp.status_code == 201:
                    logger.info(f"Successfully created recipe {doc_id} locally.")
                else:
                    logger.error(f"Failed to create recipe locally. Status: {post_resp.status_code}")
            else:
                put_resp = self.http_client.put(f"/api/recipes/{doc_id}", json=mealie_payload)
                if put_resp.status_code == 200:
                    logger.info(f"Successfully updated recipe {doc_id} locally.")
                else:
                    logger.error(f"Failed to update recipe locally. Status: {put_resp.status_code}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to push updates back to Mealie REST API: {e}")

    def start_listeners(self) -> None:
        """Register real-time snapshot listeners for Firebase Firestore collections.

        Includes an outer loop to recover and reconnect on network failures.
        """
        while not self.shutdown_event.is_set():
            if not self.is_enabled:
                time.sleep(5)
                continue

            if not self.db:
                if not self.initialize_firebase():
                    time.sleep(15)
                    continue

            logger.info("Setting up real-time snapshot listeners...")

            def on_recipe_snapshot(col_snapshot, changes, read_time) -> None:
                for doc in col_snapshot:
                    try:
                        self.process_incoming_cloud_recipe(doc.id, doc.to_dict())
                    except Exception as ex:
                        logger.error(f"Failed processing snapshot document {doc.id}: {ex}")

            recipes_ref = self.db.collection("recipes")
            
            try:
                logger.info("Registering snapshot listener on 'recipes'...")
                recipes_watch = recipes_ref.on_snapshot(on_recipe_snapshot)

                # Keep the thread alive while listening
                while not self.shutdown_event.wait(10):
                    if not self.is_enabled:
                        logger.info("Sync Worker disabled. Unsubscribing listeners.")
                        break
                
                recipes_watch.unsubscribe()
            except Exception as e:
                logger.error(f"Firestore snapshot listener encountered an error: {e}. Reconnecting in 15 seconds...")
                time.sleep(15)

    def start(self) -> None:
        """Start the sync worker daemon, config loop, heartbeat updates, and snapshot listeners."""
        logger.info("Starting Sync Worker daemon...")
        
        # Start config checker thread
        self.config_checker_thread = Thread(target=self.check_config_loop, daemon=True)
        self.config_checker_thread.start()

        # Start health check heartbeat thread
        self.heartbeat_thread = Thread(target=self.update_heartbeat, daemon=True)
        self.heartbeat_thread.start()

        # Start snapshot listener blocking loop
        self.start_listeners()

    def stop(self) -> None:
        """Stop the sync worker and clean up active threads."""
        logger.info("Shutting down Sync Worker...")
        self.shutdown_event.set()
        if self.heartbeat_thread:
            self.heartbeat_thread.join()
        if self.config_checker_thread:
            self.config_checker_thread.join()
        logger.info("Sync Worker successfully stopped.")


if __name__ == "__main__":
    worker = MealieSyncWorker()
    try:
        worker.start()
    except KeyboardInterrupt:
        worker.stop()
