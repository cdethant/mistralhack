"""
Nudge pipeline: orchestrates activity → classify → message → TTS.
"""
import random
from pydantic import BaseModel

from classification.classifier import classify_activity, ClassificationResult, CONFIDENCE_THRESHOLD
from classification.tts import generate_tts
from classification.cache import get_cached, put_cache


# ── Message templates ──────────────────────────────────────────────────────────
OFF_TASK_TEMPLATES = [
    "Hey! {sender} noticed you drifted—maybe save that for later? 🎯",
    "{sender} is checking in. Looks like a good time to refocus! 💪",
    "Poke from {sender}! You've got this—back to it? 🚀",
    "{sender} says: 'I believe in you!' Time to lock back in. 🔒",
    "Quick check-in from {sender}. You got distracted—wanna reset? ⏱️",
    "Heads up from {sender}! You've got great momentum—keep it going. ✨",
    "{sender} sent you a nudge. Future you will thank present you! 🌟",
]

ON_TASK_TEMPLATES = [
    "{sender} checked in—you're absolutely crushing it! 💪",
    "Poke from {sender}. You're in the zone—keep it up! 🔥",
    "{sender} is proud of you. You're locked in! 🎯",
    "Message from {sender}: you're on fire today! ⚡",
    "{sender} just checked—you're doing amazing. Keep going! 🚀",
]

LOW_CONFIDENCE_TEMPLATE = "{sender} sent you a poke to check in! 👋"


class NudgeResult(BaseModel):
    status: str
    confidence: float
    message_text: str
    audio_base64: str | None
    duration_sec: float
    classification_reasoning: str


async def generate_nudge(
    sender_name: str,
    app_name: str,
    window_title: str,
    context: dict,
) -> NudgeResult:
    """Full pipeline: classify → build message → TTS → return NudgeResult."""

    # 1. Classify
    classification: ClassificationResult = await classify_activity(
        app_name=app_name,
        window_title=window_title,
        context=context,
        sender_name=sender_name,
    )

    activity_summary = f"{app_name}: {window_title}"

    # 2. Pick message
    if classification.confidence < CONFIDENCE_THRESHOLD:
        message = LOW_CONFIDENCE_TEMPLATE.format(sender=sender_name)
    elif classification.status == "OFF_TASK":
        message = random.choice(OFF_TASK_TEMPLATES).format(sender=sender_name)
    else:
        message = random.choice(ON_TASK_TEMPLATES).format(sender=sender_name)

    # 3. Check phrase cache
    cached = get_cached(sender_name, classification.status, activity_summary)
    if cached:
        audio_b64, duration, cached_msg = cached
        message = cached_msg
    else:
        # 4. Generate TTS
        audio_b64, duration = generate_tts(message)
        put_cache(sender_name, classification.status, activity_summary, (audio_b64, duration, message))

    return NudgeResult(
        status=classification.status,
        confidence=classification.confidence,
        message_text=message,
        audio_base64=audio_b64,
        duration_sec=duration,
        classification_reasoning=classification.reasoning,
    )
