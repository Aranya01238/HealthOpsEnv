"""
HealthOpsEnv — FastAPI Application

Exposes the OpenEnv-compatible HTTP interface:

  GET  /               → Interactive UI Dashboard
  POST /reset           → Start a new task, returns Observation
  POST /step            → Submit action, returns reward/done/info
  GET  /state           → Current environment state
  GET  /health          → Health check
  GET  /tasks           → List all available tasks
  GET  /openenv.yaml    → Serve the OpenEnv spec file
"""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import PlainTextResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from env import HealthOpsEnv
from models.observation import Observation
from models.action import Action

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="HealthOpsEnv",
    description=(
        "An OpenEnv-compatible healthcare operations workflow simulation environment "
        "for training and evaluating AI agents."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Serve static files (UI dashboard)
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# Single global environment instance (stateful per server process)
env = HealthOpsEnv()

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class ResetRequest(BaseModel):
    task_id: str = "easy_1"

    model_config = {"extra": "ignore"}


class StepRequest(BaseModel):
    action: Action


class StepResponse(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: dict[str, Any]


class ResetResponse(BaseModel):
    observation: Observation
    task_id: str
    message: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse, tags=["meta"])
async def dashboard() -> HTMLResponse:
    """Serve the interactive UI dashboard."""
    ui_path = Path(__file__).parent / "static" / "index.html"
    if not ui_path.exists():
        return HTMLResponse(content="<p>UI dashboard not found. Run the server from the HealthOpsEnv directory.</p>", status_code=404)
    return HTMLResponse(content=ui_path.read_text(encoding="utf-8"))


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Return 204 to silence browser favicon requests (icon is set via HTML data URI)."""
    from fastapi.responses import Response
    return Response(status_code=204)


@app.get("/health", tags=["meta"])
async def health_check() -> dict[str, str]:
    """Basic liveness check. Returns 200 if the server is running."""
    return {"status": "ok", "env": "HealthOpsEnv", "version": "1.0.0"}


@app.get("/tasks", tags=["meta"])
async def list_tasks() -> dict[str, Any]:
    """Return all available task IDs with descriptions."""
    return {
        "tasks": [
            {
                "task_id": "easy_1",
                "difficulty": "easy",
                "name": "Appointment Scheduling",
                "description": "Schedule a specialist appointment for a cardiac patient.",
            },
            {
                "task_id": "medium_1",
                "difficulty": "medium",
                "name": "Medicine Stock Shortage",
                "description": "Handle critically low insulin stock at a rural clinic.",
            },
            {
                "task_id": "hard_1",
                "difficulty": "hard",
                "name": "Emergency Coordination",
                "description": (
                    "Multi-factor emergency: chest pain patient, ambulance ETA 35min, "
                    "no doctor, pending lab results."
                ),
            },
        ]
    }


@app.post("/reset", response_model=ResetResponse, tags=["environment"])
async def reset(request: Optional[ResetRequest] = Body(default=None)) -> ResetResponse:
    """
    Reset the environment and start a new task.

    - **task_id**: One of `easy_1`, `medium_1`, `hard_1` (defaults to `easy_1` if omitted)

    Returns the initial observation the agent should act on.
    """
    if request is None:
        request = ResetRequest()

    try:
        observation = env.reset(task_id=request.task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ResetResponse(
        observation=observation,
        task_id=request.task_id,
        message=f"Environment reset successfully. Task '{request.task_id}' is ready.",
    )


@app.post("/step", response_model=StepResponse, tags=["environment"])
async def step(request: StepRequest) -> StepResponse:
    """
    Submit the agent's action and receive a reward.

    - **action**: The agent's typed decision (priority, department, action, notify, escalation_level)

    Returns the observation, reward [0.0–1.0], done flag, and full scoring breakdown.
    """
    try:
        observation, reward, done, info = env.step(request.action)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return StepResponse(
        observation=observation,
        reward=reward,
        done=done,
        info=info,
    )


@app.get("/state", tags=["environment"])
async def state() -> dict[str, Any]:
    """
    Return the current environment state including last reward and observation.
    Safe to call at any time.
    """
    return env.state()


@app.get("/openenv.yaml", response_class=PlainTextResponse, tags=["meta"])
async def serve_openenv_spec() -> str:
    """Serve the openenv.yaml specification file."""
    spec_path = Path(__file__).parent / "openenv.yaml"
    if not spec_path.exists():
        raise HTTPException(status_code=404, detail="openenv.yaml not found")
    return spec_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "hint": "Check action fields: priority, department, action, notify, escalation_level"},
    )


# ---------------------------------------------------------------------------
# Entry point (local dev)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=7860, reload=True, log_level="info")
