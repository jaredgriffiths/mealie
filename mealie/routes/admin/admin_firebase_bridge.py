import json
from fastapi import APIRouter, HTTPException

from mealie.routes._base import BaseAdminController, controller
from mealie.schema.admin.firebase_bridge import (
    FirebaseBridgeSave,
    FirebaseBridgeSettings,
    FirebaseBridgeStatus,
    FirebaseBridgeTestRequest,
    FirebaseBridgeTestResponse,
)
from mealie.schema.response import SuccessResponse
from mealie.services.firebase_bridge_service import FirebaseBridgeService

router = APIRouter(prefix="/settings/firebase-bridge")


@controller(router)
class AdminFirebaseBridgeController(BaseAdminController):
    @property
    def service(self) -> FirebaseBridgeService:
        return FirebaseBridgeService(self.folders)

    @router.get("", response_model=FirebaseBridgeSettings, tags=["Admin: Firebase Bridge"])
    def get_firebase_bridge_settings(self):
        """Retrieve current configuration settings for the Firebase bridge."""
        return self.service.load_settings()

    @router.post("", response_model=SuccessResponse, tags=["Admin: Firebase Bridge"])
    def save_firebase_bridge_settings(self, data: FirebaseBridgeSave):
        """Save configuration settings and credentials JSON."""
        try:
            self.service.save_settings(data)
            return SuccessResponse.respond("Firebase bridge settings saved successfully")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save settings: {str(e)}")

    @router.post("/test", response_model=FirebaseBridgeTestResponse, tags=["Admin: Firebase Bridge"])
    def test_firebase_credentials(self, data: FirebaseBridgeTestRequest):
        """Dry-run test to validate Firebase credentials format."""
        success, error = self.service.test_credentials(data.credentials_json)
        return FirebaseBridgeTestResponse(success=success, error=error)

    @router.get("/logs", response_model=list[str], tags=["Admin: Firebase Bridge"])
    def get_sync_worker_logs(self):
        """Retrieve the last 50 lines of logs from the sync worker daemon."""
        return self.service.get_logs_tail()

    @router.post("/sync", response_model=SuccessResponse, tags=["Admin: Firebase Bridge"])
    def trigger_force_sync(self):
        """Trigger an immediate reconciliation sync by writing a local trigger file."""
        trigger_path = self.folders.DATA_DIR.joinpath("force_sync.trigger")
        try:
            with open(trigger_path, "w") as f:
                f.write("trigger")
            return SuccessResponse.respond("Reconciliation sync triggered successfully")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to trigger sync: {str(e)}")

    @router.get("/status", response_model=FirebaseBridgeStatus, tags=["Admin: Firebase Bridge"])
    def get_sync_status(self):
        """Retrieve runtime sync metrics and sidecar connection statuses."""
        settings = self.service.load_settings()
        
        # Read heartbeat status
        sync_worker_status = "offline"
        firebase_auth_status = False
        firestore_db_status = False
        last_heartbeat = None

        # Check sync worker status from heartbeat file/config
        heartbeat_path = self.folders.DATA_DIR.joinpath("sync_worker_heartbeat.json")
        if heartbeat_path.exists():
            try:
                with open(heartbeat_path) as f:
                    hb = json.load(f)
                    last_heartbeat = hb.get("last_ping")
                    sync_worker_status = hb.get("status", "offline")
                    firebase_auth_status = hb.get("firebase_auth_status", False)
                    firestore_db_status = hb.get("firestore_db_status", False)
            except Exception:
                pass

        # Query local counts
        recipe_count = self.repos.recipes.count()
        shopping_list_count = self.repos.shopping_lists.count()
        meal_plan_count = self.repos.meal_plans.count()

        return FirebaseBridgeStatus(
            sync_worker_status=sync_worker_status if settings.enabled else "disabled",
            firebase_auth_status=firebase_auth_status,
            firestore_db_status=firestore_db_status,
            mealie_api_status=True,
            last_heartbeat=last_heartbeat,
            recipe_count=recipe_count,
            shopping_list_count=shopping_list_count,
            meal_plan_count=meal_plan_count
        )
