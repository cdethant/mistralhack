"""
Feedback persistence – saves poke classification feedback to Supabase.
"""
import os
from pydantic import BaseModel, Field
from typing import Literal

SUPABASE_URL      = os.getenv("SUPABASE_URL")
SUPABASE_KEY      = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
MOCK_MODE         = os.getenv("MOCK_MODE", "false").lower() == "true"


class FeedbackPayload(BaseModel):
    poke_id: str
    user_id: str  # set server-side from JWT; Electron passes the current user's UUID
    user_feedback: Literal["CORRECT", "WRONG_OFF_TASK", "WRONG_ON_TASK"]
    comment: str | None = None


async def save_feedback(payload: FeedbackPayload) -> bool:
    """Insert feedback row into Supabase. Returns True on success."""
    if MOCK_MODE or not SUPABASE_URL:
        print(f"[feedback] MOCK: {payload.model_dump()}")
        return True

    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        client.table("feedback").insert({
            "poke_id":       payload.poke_id,
            "user_id":       payload.user_id,
            "user_feedback": payload.user_feedback,
            "comment":       payload.comment,
        }).execute()
        return True
    except Exception as e:
        print(f"[feedback] Supabase error: {e}")
        return False
