from typing import Optional
from pydantic import BaseModel


class FirebaseBridgeSettings(BaseModel):
    """Pydantic model representing the stored configuration settings for the bridge."""
    enabled: bool
    sync_strategy: str
    mealie_host_url: str
    credentials_uploaded: bool


class FirebaseBridgeSave(BaseModel):
    """Pydantic model representing the save payload from the admin screen."""
    enabled: bool
    sync_strategy: str
    mealie_host_url: str
    credentials_json: Optional[str] = None


class FirebaseBridgeStatus(BaseModel):
    """Pydantic model representing diagnostic state of the sync worker sidecar."""
    sync_worker_status: str
    firebase_auth_status: bool
    firestore_db_status: bool
    mealie_api_status: bool
    last_heartbeat: Optional[str] = None
    recipe_count: int
    shopping_list_count: int
    meal_plan_count: int


class FirebaseBridgeTestRequest(BaseModel):
    """Pydantic model for test key request."""
    credentials_json: str


class FirebaseBridgeTestResponse(BaseModel):
    """Pydantic model for test key response."""
    success: bool
    error: Optional[str] = None
