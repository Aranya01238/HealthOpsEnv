"""
server/app.py — OpenEnv multi-mode deployment entry point.
Delegates to the root app.py FastAPI application.
"""
import uvicorn
from app import app  # noqa: F401 — re-export for ASGI


def main() -> None:
    """Entry point for [project.scripts] server command."""
    uvicorn.run("app:app", host="0.0.0.0", port=7860, log_level="info")


if __name__ == "__main__":
    main()
