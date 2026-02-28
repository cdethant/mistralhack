"""Feedback endpoint."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal, Optional

from classification.feedback import save_feedback, FeedbackPayload

router = APIRouter()


class FeedbackRequest(BaseModel):
    poke_id: str
    user_id: str
    user_feedback: Literal["CORRECT", "WRONG_OFF_TASK", "WRONG_ON_TASK"]
    comment: Optional[str] = None


@router.post("/feedback")
async def feedback(req: FeedbackRequest):
    success = await save_feedback(
        FeedbackPayload(
            poke_id=req.poke_id,
            user_id=req.user_id,
            user_feedback=req.user_feedback,
            comment=req.comment,
        )
    )
    if success:
        return {"success": True, "message": "Thanks for the feedback!"}
    return {"success": False, "message": "Failed to save feedback."}
