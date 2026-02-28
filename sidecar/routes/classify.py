"""Classify endpoint (standalone, also called internally)."""
from fastapi import APIRouter
from pydantic import BaseModel

from classification.classifier import classify_activity

router = APIRouter()


class ClassifyRequest(BaseModel):
    app_name: str
    window_title: str
    context: dict
    sender_name: str = "A friend"


@router.post("/classify")
async def classify(req: ClassifyRequest):
    result = await classify_activity(
        app_name=req.app_name,
        window_title=req.window_title,
        context=req.context,
        sender_name=req.sender_name,
    )
    return result.model_dump()


@router.post("/classify-local")
async def classify_local(req: ClassifyRequest):
    """Route to local Ollama model. Returns 503 if unavailable."""
    import os, json, httpx
    from fastapi.responses import JSONResponse

    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LOCAL_MODEL     = os.getenv("LOCAL_MODEL", "mistral:7b-instruct")

    prompt = (
        "Classify the following user activity as ON_TASK or OFF_TASK. "
        "Return JSON: {status, confidence, reasoning}\n\n"
        f"App: {req.app_name}\nTitle: {req.window_title}\nContext: {json.dumps(req.context)}"
    )
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": LOCAL_MODEL, "prompt": prompt, "stream": False, "format": "json"},
            )
            resp.raise_for_status()
            data = resp.json()
            result = json.loads(data.get("response", "{}"))
            return {
                "status":     result.get("status", "OFF_TASK"),
                "confidence": float(result.get("confidence", 0.5)),
                "reasoning":  result.get("reasoning", ""),
                "model":      LOCAL_MODEL,
            }
    except Exception as e:
        return JSONResponse(status_code=503, content={"error": f"Local model unavailable: {e}"})
