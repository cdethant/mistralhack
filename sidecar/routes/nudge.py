"""Nudge endpoint – the main poke-to-nudge pipeline."""
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from activity.snapshot import get_active_window, ActivityContext
from activity.privacy import anonymize_title, anonymize_app
from classification.nudge import generate_nudge
from routes.activity import get_config

router = APIRouter()


class NudgeRequest(BaseModel):
    sender_name: str


@router.post("/nudge")
async def nudge(req: NudgeRequest, request: Request):
    try:
        tracker = request.app.state.tracker
        config  = get_config()
        privacy = config.get("privacy_mode", False)

        # Fetch activity
        app_name, window_title = get_active_window()
        if privacy:
            app_name     = anonymize_app(app_name, config.get("app_whitelist", []))
            window_title = anonymize_title(window_title)

        now = datetime.now(timezone.utc)
        context = {
            "focus_duration_sec":    tracker.current_focus_duration(app_name, window_title),
            "app_switches_last_5min": tracker.app_switches(300),
            "app_switches_last_30min": tracker.app_switches(1800),
            "time_of_day":           now.astimezone().strftime("%H:%M"),
            "is_work_hours":         tracker.is_work_hours(),
            "recent_apps":           tracker.recent_apps(5),
        }

        result = await generate_nudge(
            sender_name=req.sender_name,
            app_name=app_name,
            window_title=window_title,
            context=context,
        )
        return result.model_dump()

    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "error": f"Nudge service error: {str(e)}",
                "fallback_message": f"{req.sender_name} sent you a poke!",
            },
        )
