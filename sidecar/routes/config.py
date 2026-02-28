"""Runtime config endpoint – lets Electron update sidecar behaviour."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from routes.activity import update_config

router = APIRouter()


class ConfigRequest(BaseModel):
    privacy_mode: Optional[bool] = None
    use_local_model: Optional[bool] = None
    mute_start: Optional[str] = None   # "HH:MM"
    mute_end: Optional[str] = None     # "HH:MM"
    app_whitelist: Optional[list[str]] = None  # apps to never report


# In-memory mute/model state
_runtime = {
    "use_local_model": False,
    "mute_start": "22:00",
    "mute_end": "08:00",
}


@router.post("/config")
async def config(req: ConfigRequest):
    update = req.model_dump(exclude_none=True)
    # Persist to activity config
    update_config({k: v for k, v in update.items() if k in ("privacy_mode", "app_whitelist")})
    _runtime.update({k: v for k, v in update.items() if k not in ("privacy_mode", "app_whitelist")})
    return {"success": True, "config": {**update, **_runtime}}


@router.get("/config")
async def get_config_route():
    return _runtime
