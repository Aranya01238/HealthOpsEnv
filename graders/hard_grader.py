from __future__ import annotations
from models.action import Action
from models.reward import RewardResult
from utils.helpers import clip_reward


EXPECTED = {
    "priority": "critical",
    "department": "emergency",
    "action": "dispatch_backup_and_escalate",
    "notify": ["emergency_head", "ambulance_team", "cardiology_team"],
    "escalation_level": "highest",
}


def grade(task_id: str, action: Action) -> RewardResult:
    """
    Deterministic grader for Task 3: Emergency Coordination (Hard).

    The most critical task: chest pain + ambulance 35min away + no doctor + pending labs.
    Agent MUST use priority=critical, escalation_level=highest, and notify 3 parties.

    Scoring breakdown:
      +0.25  correct priority
      +0.25  correct department
      +0.30  correct action
      +0.10  correct notify list
      +0.10  correct escalation_level

    Penalties:
      -0.30  dangerous under-prioritization (anything < critical)
      -0.25  missing escalation (escalation_level != 'highest')
      -0.15  wrong department
      -0.20  invalid action
      -0.10  wrong priority (not applied if already under-prioritization penalty)
    """
    score = 0.0
    breakdown: dict[str, float] = {}
    penalties: dict[str, float] = {}

    # Priority — anything non-critical is dangerous here
    if action.priority == EXPECTED["priority"]:
        score += 0.25
        breakdown["correct_priority"] = 0.25
    elif action.priority in ("low", "medium"):
        score -= 0.30
        penalties["dangerous_under_prioritization"] = -0.30
    else:
        # "high" is still wrong for a critical emergency
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

    # Notify — partial credit: each correct party counts for a fraction
    expected_notify = sorted(EXPECTED["notify"])
    agent_notify = sorted(action.notify)
    if agent_notify == expected_notify:
        score += 0.10
        breakdown["correct_notify"] = 0.10
    else:
        # Partial: count overlapping notifiees
        overlap = set(agent_notify) & set(expected_notify)
        partial = round(0.10 * len(overlap) / len(expected_notify), 4)
        if partial > 0:
            score += partial
            breakdown["partial_notify"] = partial

    # Escalation — MANDATORY for hard tasks
    if action.escalation_level == EXPECTED["escalation_level"]:
        score += 0.10
        breakdown["correct_escalation"] = 0.10
    else:
        score -= 0.25
        penalties["missing_critical_escalation"] = -0.25

    final_reward = clip_reward(score)

    return RewardResult(
        task_id=task_id,
        raw_score=round(score, 4),
        final_reward=round(final_reward, 4),
        breakdown=breakdown,
        penalties=penalties,
        passed=final_reward >= 0.7,
        notes="Hard: Multi-factor emergency. Chest pain + ambulance ETA 35min + no doctor + pending lab.",
    )
