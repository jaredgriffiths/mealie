import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from mealie.core.settings.directories import AppDirectories
from mealie.schema.admin.firebase_bridge import FirebaseBridgeSettings, FirebaseBridgeSave, FirebaseBridgeStatus

logger = logging.getLogger("mealie.firebase-bridge-service")


class FirebaseBridgeService:
    """Service layer managing the Firebase Bridge configuration and diagnostics."""

    def __init__(self, folders: AppDirectories) -> None:
        self.folders = folders
        self.config_path = self.folders.DATA_DIR.joinpath("firebase_bridge_config.json")
        self.credentials_path = self.folders.DATA_DIR.joinpath("firebase_service_account.json")
        self.log_path = self.folders.DATA_DIR.joinpath("sync_worker.log")

    def load_settings(self) -> FirebaseBridgeSettings:
        """Load settings from JSON config file, returning defaults if file doesn't exist."""
        enabled = False
        sync_strategy = "Hybrid Sync (LAN + Cloud Fallback)"
        mealie_host_url = "http://localhost:9925"

        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    config = json.load(f)
                    enabled = config.get("enabled", False)
                    sync_strategy = config.get("sync_strategy", sync_strategy)
                    mealie_host_url = config.get("mealie_host_url", mealie_host_url)
            except Exception as e:
                logger.error(f"Failed to read Firebase bridge config file: {e}")

        credentials_uploaded = self.credentials_path.exists()

        return FirebaseBridgeSettings(
            enabled=enabled,
            sync_strategy=sync_strategy,
            mealie_host_url=mealie_host_url,
            credentials_uploaded=credentials_uploaded
        )

    def save_settings(self, data: FirebaseBridgeSave) -> None:
        """Save settings and credentials JSON to data directory files."""
        # Save configuration settings
        config = {
            "enabled": data.enabled,
            "sync_strategy": data.sync_strategy,
            "mealie_host_url": data.mealie_host_url
        }

        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write Firebase bridge config: {e}")
            raise IOError("Could not save configuration settings") from e

        # Save credentials JSON if provided
        if data.credentials_json:
            try:
                # Validate JSON structure
                parsed_creds = json.loads(data.credentials_json)
                if not isinstance(parsed_creds, dict) or "type" not in parsed_creds:
                    raise ValueError("Invalid service account structure")

                with open(self.credentials_path, "w") as f:
                    json.dump(parsed_creds, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save Firebase credentials file: {e}")
                raise ValueError("Invalid Firebase Service Account JSON key format") from e

    def get_logs_tail(self, lines_count: int = 50) -> list[str]:
        """Read the last N lines from the sync worker log file in the data directory."""
        if not self.log_path.exists():
            return ["No sync worker logs found. Ensure the sync-worker container is running and mounted correctly."]

        try:
            with open(self.log_path) as f:
                lines = f.readlines()
                return [line.strip() for line in lines[-lines_count:]]
        except Exception as e:
            logger.error(f"Failed to read sync worker logs: {e}")
            return [f"Failed to retrieve logs: {str(e)}"]

    def test_credentials(self, credentials_json: str) -> tuple[bool, Optional[str]]:
        """Validate JSON format of the Firebase Credentials string."""
        try:
            creds = json.loads(credentials_json)
            required_keys = ["project_id", "private_key", "client_email", "type"]
            missing_keys = [k for k in required_keys if k not in creds]
            if missing_keys:
                return False, f"Missing required fields in service account: {', '.join(missing_keys)}"
            
            if creds.get("type") != "service_account":
                return False, "Invalid credential type. Must be 'service_account'."
            
            return True, None
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON string format: {str(e)}"
        except Exception as e:
            return False, str(e)
