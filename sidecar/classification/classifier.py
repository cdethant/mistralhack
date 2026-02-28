"""
Task classifier – uses Mistral API (or mock) to determine if user is ON_TASK or OFF_TASK.
Weave tracing is applied lazily when WANDB_API_KEY is present.
"""
import os
import json
import random
from functools import wraps

from mistralai import Mistral
from pydantic import BaseModel


MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MOCK_MODE       = os.getenv("MOCK_MODE", "false").lower() == "true"
WANDB_API_KEY   = os.getenv("WANDB_API_KEY")
CONFIDENCE_THRESHOLD = 0.75


def _maybe_weave_op(fn):
    """Apply @weave.op() only when WANDB_API_KEY is configured."""
    if WANDB_API_KEY and not MOCK_MODE:
        try:
            import weave
            return weave.op()(fn)
        except Exception:
            pass
    return fn

# Primary model with fallback
PRIMARY_MODEL  = "mistral-large-latest"
FALLBACK_MODEL = "mistral-small-latest"

# ── Few-shot prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a productivity assistant that classifies whether a user is currently ON_TASK or OFF_TASK based on their active application and behavioral context.

Rules:
- ON_TASK: coding, writing docs, work emails, reading research papers, video calls, Slack/Teams, project management tools, spreadsheets for work
- OFF_TASK: social media (Twitter, Reddit, Instagram, TikTok), shopping, entertainment streaming (YouTube non-tutorial, Netflix), gaming, news browsing during work hours
- AMBIGUOUS signals: YouTube tutorials = ON_TASK; YouTube music/trending = OFF_TASK; news = context-dependent
- Evening/weekend hours (not work hours): lower threshold for OFF_TASK judgment — be more lenient

Respond ONLY with valid JSON in this exact format:
{
  "status": "ON_TASK" | "OFF_TASK",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}"""

FEW_SHOT_EXAMPLES = [
    {"role": "user", "content": json.dumps({
        "app_name": "VSCode", "window_title": "main.py – mistralhack",
        "context": {"focus_duration_sec": 1800, "app_switches_last_5min": 1, "time_of_day": "10:30", "is_work_hours": True}
    })},
    {"role": "assistant", "content": '{"status": "ON_TASK", "confidence": 0.97, "reasoning": "Active coding session on a project during work hours."}'},

    {"role": "user", "content": json.dumps({
        "app_name": "Chrome", "window_title": "YouTube – Trending",
        "context": {"focus_duration_sec": 300, "app_switches_last_5min": 8, "time_of_day": "14:15", "is_work_hours": True}
    })},
    {"role": "assistant", "content": '{"status": "OFF_TASK", "confidence": 0.92, "reasoning": "Browsing trending YouTube during work hours with high context switching."}'},

    {"role": "user", "content": json.dumps({
        "app_name": "Chrome", "window_title": "arXiv: Attention Is All You Need",
        "context": {"focus_duration_sec": 720, "app_switches_last_5min": 2, "time_of_day": "11:00", "is_work_hours": True}
    })},
    {"role": "assistant", "content": '{"status": "ON_TASK", "confidence": 0.88, "reasoning": "Reading research paper during work hours with low context switching."}'},

    {"role": "user", "content": json.dumps({
        "app_name": "Chrome", "window_title": "Twitter / X – Home",
        "context": {"focus_duration_sec": 600, "app_switches_last_5min": 5, "time_of_day": "15:45", "is_work_hours": True}
    })},
    {"role": "assistant", "content": '{"status": "OFF_TASK", "confidence": 0.90, "reasoning": "Social media browsing during work hours."}'},

    {"role": "user", "content": json.dumps({
        "app_name": "Slack", "window_title": "# engineering",
        "context": {"focus_duration_sec": 180, "app_switches_last_5min": 3, "time_of_day": "09:20", "is_work_hours": True}
    })},
    {"role": "assistant", "content": '{"status": "ON_TASK", "confidence": 0.85, "reasoning": "Communicating in work Slack channel during work hours."}'},

    {"role": "user", "content": json.dumps({
        "app_name": "Chrome", "window_title": "Amazon – Men's Running Shoes",
        "context": {"focus_duration_sec": 240, "app_switches_last_5min": 6, "time_of_day": "13:10", "is_work_hours": True}
    })},
    {"role": "assistant", "content": '{"status": "OFF_TASK", "confidence": 0.88, "reasoning": "Online shopping during work hours."}'},

    {"role": "user", "content": json.dumps({
        "app_name": "Chrome", "window_title": "YouTube – Python FastAPI Tutorial",
        "context": {"focus_duration_sec": 900, "app_switches_last_5min": 1, "time_of_day": "10:00", "is_work_hours": True}
    })},
    {"role": "assistant", "content": '{"status": "ON_TASK", "confidence": 0.82, "reasoning": "Watching a programming tutorial related to tech stack during work hours."}'},

    {"role": "user", "content": json.dumps({
        "app_name": "Netflix", "window_title": "Stranger Things – S4E1",
        "context": {"focus_duration_sec": 2400, "app_switches_last_5min": 0, "time_of_day": "21:30", "is_work_hours": False}
    })},
    {"role": "assistant", "content": '{"status": "OFF_TASK", "confidence": 0.70, "reasoning": "Streaming entertainment — but evening hours so confidence reduced."}'},

    {"role": "user", "content": json.dumps({
        "app_name": "Notion", "window_title": "Q1 2025 Project Roadmap",
        "context": {"focus_duration_sec": 1500, "app_switches_last_5min": 2, "time_of_day": "14:00", "is_work_hours": True}
    })},
    {"role": "assistant", "content": '{"status": "ON_TASK", "confidence": 0.94, "reasoning": "Working on project planning documentation during work hours."}'},

    {"role": "user", "content": json.dumps({
        "app_name": "Chrome", "window_title": "Reddit – r/programmerhumor",
        "context": {"focus_duration_sec": 120, "app_switches_last_5min": 9, "time_of_day": "16:00", "is_work_hours": True}
    })},
    {"role": "assistant", "content": '{"status": "OFF_TASK", "confidence": 0.89, "reasoning": "Browsing Reddit entertainment during work hours with very high context switching."}'},
]


class ClassificationResult(BaseModel):
    status: str        # "ON_TASK" | "OFF_TASK"
    confidence: float
    reasoning: str


@_maybe_weave_op
async def classify_activity(
    app_name: str,
    window_title: str,
    context: dict,
    sender_name: str = "A friend",
) -> ClassificationResult:
    """Classify user activity using Mistral API with Weave tracing."""

    if MOCK_MODE:
        return _mock_classify(app_name, window_title)

    user_content = json.dumps({
        "app_name": app_name,
        "window_title": window_title,
        "context": context,
        "sender_name": sender_name,
    })

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *FEW_SHOT_EXAMPLES,
        {"role": "user", "content": user_content},
    ]

    client = Mistral(api_key=MISTRAL_API_KEY)

    for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
        try:
            response = client.chat.complete(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=256,
            )
            raw = response.choices[0].message.content
            data = json.loads(raw)
            return ClassificationResult(
                status=data.get("status", "OFF_TASK"),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
            )
        except Exception as e:
            print(f"[classifier] {model} failed: {e}, trying fallback…")
            continue

    # Ultimate fallback if both models fail
    return ClassificationResult(
        status="OFF_TASK",
        confidence=0.5,
        reasoning="Classification service error – defaulting to OFF_TASK",
    )


def _mock_classify(app_name: str, window_title: str) -> ClassificationResult:
    work_apps = {"VSCode", "PyCharm", "Slack", "Zoom", "Notion", "Terminal", "iTerm2"}
    distracted_keywords = {"YouTube", "Reddit", "Twitter", "Instagram", "Netflix", "Amazon", "Shopping"}

    if app_name in work_apps:
        return ClassificationResult(status="ON_TASK", confidence=0.95, reasoning="Mock: work app detected")
    for kw in distracted_keywords:
        if kw.lower() in window_title.lower():
            return ClassificationResult(status="OFF_TASK", confidence=0.88, reasoning=f"Mock: distraction keyword '{kw}' in title")
    # Random for ambiguous cases
    status = random.choice(["ON_TASK", "OFF_TASK"])
    return ClassificationResult(status=status, confidence=0.70, reasoning="Mock: ambiguous activity")
