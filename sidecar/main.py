"""
mistralhack Python Sidecar – FastAPI entry point.
Starts on http://localhost:8765 (configurable via SIDECAR_PORT env var).
"""
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

WANDB_API_KEY = os.getenv("WANDB_API_KEY")
WANDB_PROJECT = os.getenv("WANDB_PROJECT", "mistralhack")
MOCK_MODE     = os.getenv("MOCK_MODE", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    # Init Weave tracing at server start (not import time)
    if WANDB_API_KEY and not MOCK_MODE:
        try:
            import weave
            weave.init(WANDB_PROJECT)
        except Exception as e:
            print(f"[weave] init failed: {e}")

    from activity.context import ActivityContextTracker
    app.state.tracker = ActivityContextTracker()
    app.state.mock_mode = MOCK_MODE
    yield
    # Graceful cleanup on shutdown
    app.state.tracker.stop()


app = FastAPI(
    title="mistralhack Sidecar",
    version="0.1.0",
    description="Local AI agent for social accountability nudges.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Electron can be any origin
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ────────────────────────────────────────────────────────────
from routes.health     import router as health_router
from routes.activity   import router as activity_router
from routes.nudge      import router as nudge_router
from routes.classify   import router as classify_router
from routes.feedback   import router as feedback_router
from routes.config     import router as config_router

app.include_router(health_router)
app.include_router(activity_router)
app.include_router(nudge_router)
app.include_router(classify_router)
app.include_router(feedback_router)
app.include_router(config_router)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SIDECAR_PORT", 8765))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False, log_level="info")
