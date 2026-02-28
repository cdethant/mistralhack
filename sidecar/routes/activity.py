"""Activity snapshot route."""
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from pydantic import BaseModel

from activity.snapshot import get_active_window, ActivitySnapshot, ActivityContext
from activity.privacy import anonymize_title, anonymize_app

router = APIRouter()

# Runtime config (mutated by /config endpoint)
_config = {"privacy_mode": False, "app_whitelist": []}


@router.get("/activity-snapshot", response_model=ActivitySnapshot)
async def activity_snapshot(request: Request):
    tracker = request.app.state.tracker
    app_name, window_title = get_active_window()
    privacy = _config["privacy_mode"]

    if privacy:
        app_name = anonymize_app(app_name, _config["app_whitelist"])
        window_title = anonymize_title(window_title)

    now = datetime.now(timezone.utc)
    context = ActivityContext(
        focus_duration_sec=tracker.current_focus_duration(app_name, window_title),
        app_switches_last_5min=tracker.app_switches(300),
        app_switches_last_30min=tracker.app_switches(1800),
        time_of_day=now.astimezone().strftime("%H:%M"),
        is_work_hours=tracker.is_work_hours(),
        recent_apps=tracker.recent_apps(5),
    )

    return ActivitySnapshot(
        app_name=app_name,
        window_title=window_title,
        timestamp=now.isoformat(),
        context=context,
        privacy_mode=privacy,
    )


def get_config():
    return _config


def update_config(new_config: dict):
    _config.update(new_config)
