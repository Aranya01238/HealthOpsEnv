"""
HealthOpsEnv — Inference Script

Runs a full evaluation pass of all 3 tasks (easy, medium, hard) using
an OpenAI-compatible LLM. Prints logs in the required OpenEnv format.

Required environment variables:
  API_BASE_URL    - Base URL of the OpenAI-compatible API
  MODEL_NAME      - Model to use (e.g. gpt-4o, gpt-4)
  OPENAI_API_KEY  - API key
  HF_TOKEN        - Hugging Face token (used for HF-hosted inference)

Usage:
  python inference.py
  python inference.py --task easy_1
  python inference.py --all   (default: runs all 3 tasks)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any

import httpx
from openai import OpenAI

from utils.helpers import (
    get_env_var,
    format_log_start,
    format_log_step,
    format_log_end,
    clip_reward,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ENV_NAME = "HealthOpsEnv"
SERVER_BASE_URL = os.environ.get("SERVER_URL", "http://localhost:7860")

ALL_TASKS = ["easy_1", "medium_1", "hard_1"]

SYSTEM_PROMPT = """You are a healthcare operations AI agent.
You will receive a JSON observation describing a healthcare administration situation.
You must respond with a JSON action object with exactly these fields:
  - priority: one of "low", "medium", "high", "critical"
  - department: one of "appointments", "procurement", "emergency", "cardiology",
    "orthopedics", "laboratory", "operations", "administration", "ambulance"
  - action: a concise action string (e.g. "schedule_consultation", "emergency_restock",
    "dispatch_backup_and_escalate")
  - notify: a list of strings naming parties to notify
  - escalation_level: null, or one of "low", "medium", "high", "highest"

Respond ONLY with valid JSON. No explanation, no markdown, no extra text.
"""

# ---------------------------------------------------------------------------
# LLM Client
# ---------------------------------------------------------------------------


def build_client() -> OpenAI:
    # On Hugging Face Spaces, the API key is HF_TOKEN.
    # Locally (OpenAI), use OPENAI_API_KEY.
    # HF_TOKEN takes priority when both are set.
    hf_token = os.environ.get("HF_TOKEN")
    openai_key = os.environ.get("OPENAI_API_KEY")
    api_key = hf_token or openai_key
    if not api_key:
        raise EnvironmentError(
            "No API key found. Set HF_TOKEN (for HF-hosted inference) "
            "or OPENAI_API_KEY (for OpenAI)."
        )
    base_url = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def reset_env(task_id: str) -> dict[str, Any]:
    resp = httpx.post(
        f"{SERVER_BASE_URL}/reset",
        json={"task_id": task_id},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


def step_env(action: dict[str, Any]) -> dict[str, Any]:
    resp = httpx.post(
        f"{SERVER_BASE_URL}/step",
        json={"action": action},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Agent inference
# ---------------------------------------------------------------------------


def get_agent_action(client: OpenAI, model: str, observation: dict[str, Any]) -> dict[str, Any]:
    """Send observation to LLM and parse the JSON action response."""
    obs_text = json.dumps(observation, indent=2)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Observation:\n{obs_text}\n\nRespond with your action JSON:"},
        ],
        temperature=0.0,  # deterministic for benchmarking
        max_tokens=512,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    return json.loads(raw)


# ---------------------------------------------------------------------------
# Run one task
# ---------------------------------------------------------------------------


def run_task(client: OpenAI, model: str, task_id: str) -> dict[str, Any]:
    """Run one full task episode and return results."""
    print(format_log_start(task_id, ENV_NAME, model))

    error_msg = None
    # Keep score in strict (0, 1) even on failures, matching validator rules.
    reward = 0.001
    success = False

    try:
        # Reset
        reset_data = reset_env(task_id)
        observation = reset_data["observation"]

        # Agent action
        action = get_agent_action(client, model, observation)

        # Step
        step_data = step_env(action)
        reward = clip_reward(float(step_data["reward"]))
        done = step_data["done"]
        info = step_data["info"]

        action_str = action.get("action", "unknown")
        print(format_log_step(1, action_str, reward, done))

        success = info.get("passed", False)

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        print(f"[ERROR] {error_msg}", file=sys.stderr)
    except json.JSONDecodeError as e:
        error_msg = f"LLM returned invalid JSON: {e}"
        print(f"[ERROR] {error_msg}", file=sys.stderr)
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] {error_msg}", file=sys.stderr)

    print(format_log_end(success, steps=1, score=reward, rewards=reward, error=error_msg))

    return {
        "task_id": task_id,
        "reward": reward,
        "success": success,
        "error": error_msg,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="HealthOpsEnv inference runner")
    parser.add_argument("--task", type=str, default=None, help="Run a single task by ID")
    parser.add_argument("--all", action="store_true", default=True, help="Run all tasks (default)")
    args = parser.parse_args()

    model = get_env_var("MODEL_NAME", "gpt-4o")
    client = build_client()

    tasks_to_run = [args.task] if args.task else ALL_TASKS

    results = []
    for task_id in tasks_to_run:
        result = run_task(client, model, task_id)
        results.append(result)
        print()  # blank line between tasks

    # Summary
    total_score = sum(r["reward"] for r in results)
    avg_score = total_score / len(results) if results else 0.0
    passed = sum(1 for r in results if r["success"])

    print("=" * 60)
    print(f"SUMMARY: {passed}/{len(results)} tasks passed")
    print(f"Average score: {avg_score:.4f}")
    print("=" * 60)
    for r in results:
        status = "✓ PASS" if r["success"] else "✗ FAIL"
        print(f"  {status}  {r['task_id']:12s}  score={r['reward']:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
