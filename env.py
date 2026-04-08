"""
HealthOpsEnv — Core Environment

Implements the OpenEnv-compatible interface:
  - reset(task_id)   → Observation
  - step(action)     → (Observation, float, bool, dict)
  - state()          → dict

Supports tasks: easy_1, medium_1, hard_1
"""
from __future__ import annotations

import importlib
from typing import Any, Optional, Tuple

from models.observation import Observation
from models.action import Action
from models.reward import RewardResult
from utils.helpers import load_task, task_id_to_difficulty

# All known task IDs
VALID_TASK_IDS = {"easy_1", "medium_1", "hard_1"}

# Map difficulty -> grader module function name
GRADER_MAP = {
    "easy": ("graders.easy_grader", "grade"),
    "medium": ("graders.medium_grader", "grade"),
    "hard": ("graders.hard_grader", "grade"),
}


class HealthOpsEnv:
    """
    OpenEnv-compatible Healthcare Operations simulation environment.

    Each episode consists of exactly one step:
      1. Call reset(task_id) to load the task and get the initial observation.
      2. Call step(action) with the agent's decision.
      3. Receive (observation, reward, done=True, info).

    The environment is stateful — only one task is active at a time.
    """

    def __init__(self) -> None:
        self._task_data: Optional[dict[str, Any]] = None
        self._current_task_id: Optional[str] = None
        self._current_observation: Optional[Observation] = None
        self._done: bool = False
        self._step_count: int = 0
        self._last_reward: Optional[float] = None
        self._last_result: Optional[RewardResult] = None

    # ------------------------------------------------------------------
    # OpenEnv Interface
    # ------------------------------------------------------------------

    def reset(self, task_id: str = "easy_1") -> Observation:
        """
        Start a new episode for the given task_id.

        Args:
            task_id: One of 'easy_1', 'medium_1', 'hard_1'

        Returns:
            Observation with all task-relevant fields populated.

        Raises:
            ValueError: If task_id is not recognised.
        """
        if task_id not in VALID_TASK_IDS:
            raise ValueError(
                f"Unknown task_id '{task_id}'. Valid IDs: {sorted(VALID_TASK_IDS)}"
            )

        difficulty = task_id_to_difficulty(task_id)
        self._task_data = load_task(difficulty)
        self._current_task_id = task_id
        self._done = False
        self._step_count = 0
        self._last_reward = None
        self._last_result = None

        # Build observation from task JSON (exclude 'expected' key)
        obs_fields = {
            k: v for k, v in self._task_data.items() if k != "expected"
        }
        self._current_observation = Observation(**obs_fields)
        return self._current_observation

    def step(self, action: Action) -> Tuple[Observation, float, bool, dict]:
        """
        Execute the agent's action and score it.

        Args:
            action: Agent's typed Action decision.

        Returns:
            Tuple of (observation, reward, done, info)
              - observation: same initial observation (single-step env)
              - reward: float in [0.0, 1.0]
              - done: always True after one step
              - info: dict with full reward breakdown and result details
        """
        if self._current_observation is None:
            raise RuntimeError("Environment not initialised. Call reset() first.")
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        self._step_count += 1

        # Load and call the appropriate grader
        difficulty = task_id_to_difficulty(self._current_task_id)
        module_path, fn_name = GRADER_MAP[difficulty]
        grader_module = importlib.import_module(module_path)
        grade_fn = getattr(grader_module, fn_name)

        result: RewardResult = grade_fn(self._current_task_id, action)
        self._last_reward = result.final_reward
        self._last_result = result
        self._done = True

        info = {
            "task_id": self._current_task_id,
            "difficulty": difficulty,
            "raw_score": result.raw_score,
            "breakdown": result.breakdown,
            "penalties": result.penalties,
            "passed": result.passed,
            "notes": result.notes,
            "steps": self._step_count,
        }

        return self._current_observation, result.final_reward, True, info

    def state(self) -> dict[str, Any]:
        """
        Return the current environment state. Readable at any time.
        """
        return {
            "task_id": self._current_task_id,
            "done": self._done,
            "step_count": self._step_count,
            "last_reward": self._last_reward,
            "observation": (
                self._current_observation.model_dump()
                if self._current_observation
                else None
            ),
            "last_result": (
                self._last_result.model_dump()
                if self._last_result
                else None
            ),
        }
