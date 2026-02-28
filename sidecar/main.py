import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import weave
import os
from contextlib import asynccontextmanager
from collector import collector
from dotenv import load_dotenv

load_dotenv()

# Weave initialization
weave.init("mistral-hackathon-focus")

# LLM configuration - Defaults to tunnelled Brev / Local vLLM
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:8000/v1/chat/completions")

class FocusStatus(BaseModel):
    is_focused: bool
    score: int
    insight: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting sidecar collector...")
    collector.start()
    yield
    print("Stopping sidecar collector...")
    collector.stop()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Sidecar is running"}

@app.get("/metrics")
async def get_metrics():
    """Returns the current raw activity data."""
    return collector.get_context_for_llm()

@app.get("/analyze")
@weave.op()
async def analyze_focus():
    """Sends current context to Mistral for analysis."""
    context = collector.get_context_for_llm()
    if not context:
        return {"is_focused": True, "score": 10, "insight": "No activity data yet."}

    # Prepare prompt for Mistral
    prompt = f"""
    Analyze the following user activity log and determine if the user is focused on their primary task.
    Primary Task: Hackathon project development.
    
    Log:
    {context[-10:]}  # Last 10 samples (roughly 50 seconds)
    
    Response format: JSON with fields: 'is_focused' (bool), 'score' (int 1-10), 'insight' (string).
    """

    # For now, we mock the LLM response OR if an endpoint exists, we call it.
    # In a real scenario, this would be a POST to LLM_ENDPOINT.
    
    # Mock Response
    return {
        "is_focused": True,
        "score": 8,
        "insight": "User is actively engaged in terminal and editor windows."
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
