print("Sidecar script started execution...")
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import weave
import os
from contextlib import asynccontextmanager
from collector import collector
from dotenv import load_dotenv
from elevenlabs_utils import generate_roast_audio

load_dotenv()

# Weave initialization
weave.init("mistral-hackathon-focus")

# LLM configuration - local llama-server (local/serve.sh) runs on port 8000
# Sidecar FastAPI runs on port 8080 to avoid collision
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://127.0.0.1:8000/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "local-model")  # llama-server exposes this name
SIDECAR_PORT = int(os.getenv("SIDECAR_PORT", "8080"))

class FocusStatus(BaseModel):
    is_focused: bool
    roast: str | None = None

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

@app.post("/poke")
async def receive_poke():
    """Triggered by an external accountability partner."""
    print("[Poke] Received a poke! Triggering focus assessment...")
    collector.pause()
    try:
        result = await analyze_focus()
        audio_b64 = None
        if not result.get("is_focused", True) and result.get("roast"):
            audio_result = await generate_roast_audio(result["roast"])
            if audio_result and audio_result.get("status") == "success":
                audio_b64 = audio_result.get("audio_b64")
    finally:
        collector.resume()
    
    return {"status": "processed", "analysis": result, "audio_b64": audio_b64}

@app.get("/analyze")
@weave.op()
async def analyze_focus():
    """Sends current context to Mistral for analysis."""
    context_str = collector.get_context_for_llm()
    if not context_str or "No activity recorded" in context_str:
        return {"is_focused": True, "roast": None}

    prompt = f"""You are a productivity guardian.
Analyze the following sequence of active window activity data and determine if the user has gone off-task.
Primary Task: On-task & productivity analysis.

Window Log:
{context_str}

Rules:
- If the user is on-task (coding, terminal, docs, relevant research, team comms), respond with exactly: null
- If the user is clearly off-task (social media, shopping, entertainment, unrelated browsing), respond with a single short, quippy roast in plain text. No JSON, no quotes, just the roast.
- Be concise and funny. Do not over-explain.
"""

    async with httpx.AsyncClient() as client:
        try:
            print(f"[LLM Input Prompt]\n{prompt}")
            response = await client.post(
                LLM_ENDPOINT,
                json={
                    "model": LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"].strip()
                is_focused = content == "null"
                print(f"[LLM Analysis] focused={is_focused} roast={content}")
                return {"is_focused": is_focused, "roast": content}
            else:
                print(f"[LLM Error] {response.status_code}: {response.text}")
                return {"is_focused": "error", "roast": None}
        except Exception as e:
            print(f"[LLM Exception] {str(e)}")
            return {"is_focused": "error", "roast": None}

class TestRoastPayload(BaseModel):
    text: str

@app.post("/test-roast")
async def test_roast(payload: TestRoastPayload):
    audio_result = await generate_roast_audio(payload.text)
    audio_b64 = None
    if audio_result and audio_result.get("status") == "success":
        audio_b64 = audio_result.get("audio_b64")
    return {"status": "success", "roast": payload.text, "audio_b64": audio_b64}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=SIDECAR_PORT)
