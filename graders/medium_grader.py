from __future__ import annotations
from models.action import Action
from models.reward import RewardResult
from utils.helpers import clip_reward


EXPECTED = {
    "priority": "high",
    "department": "procurement",
    "action": "emergency_restock",
    "notify": ["inventory_manager", "regional_coordinator"],
    "escalation_level": None,
}


def grade(task_id: str, action: Action) -> RewardResult:
    """
    Deterministic grader for Task 2: Medicine Stock Shortage (Medium).

    Stock remaining = 3, daily usage = 10 → ~0.3 days left → HIGH priority.

    Scoring breakdown:
      +0.25  correct priority
      +0.25  correct department
      +0.30  correct action
      +0.10  correct notify list
      +0.10  correct escalation_level

    Penalties:
      -0.10  wrong priority
      -0.15  wrong department
      -0.30  dangerous under-prioritization (low/medium when stock is critical)
      -0.25  missing escalation (not applicable here but still enforced)
      -0.20  invalid action
    """
    score = 0.0
    breakdown: dict[str, float] = {}
    penalties: dict[str, float] = {}

    # Priority — medium or low counts as dangerous under-prioritization
    if action.priority == EXPECTED["priority"]:
        score += 0.25
        breakdown["correct_priority"] = 0.25
    elif action.priority in ("low", "medium"):
        score -= 0.30
        penalties["dangerous_under_prioritization"] = -0.30
    else:
        score -= 0.10
        penalties["wrong_priority"] = -0.10

    # Department
    if action.department == EXPECTED["department"]:
        score += 0.25
        breakdown["correct_department"] = 0.25
    else:
        score -= 0.15
        penalties["wrong_department"] = -0.15

    # Action
    if action.action == EXPECTED["action"]:
        score += 0.30
        breakdown["correct_action"] = 0.30
    else:
        score -= 0.20
        penalties["invalid_action"] = -0.20

    # Notify
    if sorted(action.notify) == sorted(EXPECTED["notify"]):
        score += 0.10
        breakdown["correct_notify"] = 0.10

    # Escalation
    if action.escalation_level == EXPECTED["escalation_level"]:
        score += 0.10
        breakdown["correct_escalation"] = 0.10

    final_reward = clip_reward(score)

    return RewardResult(
        task_id=task_id,
        raw_score=round(score, 4),
        final_reward=round(final_reward, 4),
        breakdown=breakdown,
        penalties=penalties,
        passed=final_reward >= 0.7,
        notes="Medium: Insulin shortage at Rural Camp A. ~0.3 days of stock remaining.",
    )
