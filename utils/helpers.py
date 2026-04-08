from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any


def clip_reward(score: float, low: float = 0.001, high: float = 0.999) -> float:
    """Clip a reward score to (0, 1) exclusive, as required by OpenEnv validator."""
    return max(low, min(high, score))


def load_task(difficulty: str) -> dict[str, Any]:
    """
    Load a task JSON file by difficulty name (easy | medium | hard).
    Searches relative to this file's location.
    """
    tasks_dir = Path(__file__).parent.parent / "tasks"
    task_file = tasks_dir / f"{difficulty}.json"
    if not task_file.exists():
        raise FileNotFoundError(f"Task file not found: {task_file}")
    with open(task_file, "r", encoding="utf-8") as f:
        return json.load(f)


def task_id_to_difficulty(task_id: str) -> str:
    """
    Map a task_id string to its difficulty level.
    e.g. 'easy_1' -> 'easy', 'hard_1' -> 'hard'
    """
    prefix = task_id.split("_")[0].lower()
    valid = {"easy", "medium", "hard"}
    if prefix not in valid:
        raise ValueError(f"Cannot determine difficulty from task_id '{task_id}'. Expected prefix in {valid}")
    return prefix


def format_log_start(task_id: str, env_name: str, model: str) -> str:
    return f"[START] task={task_id} env={env_name} model={model}"


def format_log_step(step: int, action: str, reward: float, done: bool) -> str:
    # Keep enough precision so exclusive (0, 1) values are not rounded to 0.00/1.00.
    return f"[STEP] step={step} action={action} reward={reward:.4f} done={str(done).lower()}"


def format_log_end(
    success: bool,
    steps: int,
    score: float,
    rewards: float,
    error: str | None = None,
) -> str:
    err_str = error if error else "null"
    # Keep enough precision so exclusive (0, 1) values are not rounded to 0.00/1.00.
    return f"[END] success={str(success).lower()} steps={steps} score={score:.4f} rewards={rewards:.4f} error={err_str}"


def get_env_var(name: str, default: str | None = None) -> str:
    """Read required environment variable, raise if missing and no default."""
    value = os.environ.get(name, default)
    if value is None:
        raise EnvironmentError(
            f"Required environment variable '{name}' is not set. "
            f"Please export it before running."
        )
    return value
