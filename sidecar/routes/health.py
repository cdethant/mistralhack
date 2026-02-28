"""Health check route."""
import os
import subprocess
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class HealthResponse(BaseModel):
    status: str
    activity_service: str
    llm_service: str
    local_model: str


@router.get("/health", response_model=HealthResponse)
async def health():
    # Check local Ollama availability
    local_model_status = "unavailable"
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                local_model_status = "available"
    except Exception:
        pass

    return HealthResponse(
        status="healthy",
        activity_service="ready",
        llm_service="ready",
        local_model=local_model_status,
    )
