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

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sync-worker")

# Load environment configurations
load_dotenv()

MEALIE_API_URL = os.getenv("MEALIE_API_URL", "http://mealie:9000")
MEALIE_API_TOKEN = os.getenv("MEALIE_API_TOKEN")
FIREBASE_KEY_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "/app/secrets/firebase_service_account.json")

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

    def initialize_firebase(self) -> None:
        """Initialize Firebase Admin SDK using the local service account key."""
        logger.info("Initializing Firebase Admin SDK...")
        if not os.path.exists(FIREBASE_KEY_PATH):
            raise FileNotFoundError(f"Firebase service account JSON not found at: {FIREBASE_KEY_PATH}")

        cred = credentials.Certificate(FIREBASE_KEY_PATH)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        logger.info("Firebase Admin SDK successfully initialized.")

    def update_heartbeat(self) -> None:
        """Periodically write a host health status heartbeat document to Firestore."""
        while not self.shutdown_event.wait(300):  # Run every 5 minutes
            if not self.db:
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

    def generate_payload_hash(self, data: Dict[str, Any]) -> str:
        """Generate a SHA-256 hash of a payload dictionary to detect duplicate states.

        Args:
            data: The payload dictionary to hash.

        Returns:
            The hex digest representing the payload state.
        """
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def process_incoming_cloud_recipe(self, doc_id: str, cloud_data: Dict[str, Any]) -> None:
        """Process a recipe updated in the cloud and sync back to local Mealie if applicable.

        Args:
            doc_id: The Firestore document identifier (matches Mealie recipe UUID).
            cloud_data: The document data dictionary retrieved from Firestore.
        """
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
            # Extend with other fields defensively
        }

        # Write updates back to local Mealie
        try:
            if response.status_code == 404:
                # Create recipe in Mealie
                post_resp = self.http_client.post("/api/recipes", json=mealie_payload)
                if post_resp.status_code == 201:
                    logger.info(f"Successfully created recipe {doc_id} locally.")
                else:
                    logger.error(f"Failed to create recipe locally. Status: {post_resp.status_code}")
            else:
                # Update recipe in Mealie
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
        if not self.db:
            logger.error("Database connection missing. Cannot start listeners.")
            return

        logger.info("Setting up real-time snapshot listeners...")

        def on_recipe_snapshot(col_snapshot, changes, read_time) -> None:
            for doc in col_snapshot:
                try:
                    self.process_incoming_cloud_recipe(doc.id, doc.to_dict())
                except Exception as ex:
                    logger.error(f"Failed processing snapshot document {doc.id}: {ex}")

        # Real-time listener for the recipes collection
        recipes_ref = self.db.collection("recipes")
        
        while not self.shutdown_event.is_set():
            try:
                # Register snapshot listener
                logger.info("Registering snapshot listener on 'recipes'...")
                recipes_watch = recipes_ref.on_snapshot(on_recipe_snapshot)

                # Keep the thread alive while listening
                while not self.shutdown_event.wait(10):
                    pass
                
                # Unsubscribe on shutdown
                recipes_watch.unsubscribe()
                break
            except Exception as e:
                logger.error(f"Firestore snapshot listener encountered an error: {e}. Reconnecting in 15 seconds...")
                time.sleep(15)

    def start(self) -> None:
        """Start the sync worker daemon, heartbeat updates, and snapshot listeners."""
        try:
            self.initialize_firebase()
        except Exception as e:
            logger.critical(f"Failed to start Sync Worker due to initialization error: {e}")
            return

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
        logger.info("Sync Worker successfully stopped.")


if __name__ == "__main__":
    worker = MealieSyncWorker()
    try:
        worker.start()
    except KeyboardInterrupt:
        worker.stop()
