from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Dict


class RewardResult(BaseModel):
    """
    Encapsulates the full breakdown of a reward calculation.
    final_reward is always clipped to [0.0, 1.0].
    """
    task_id: str
    raw_score: float
    final_reward: float
    breakdown: Dict[str, float]
    penalties: Dict[str, float]
    passed: bool
    notes: Optional[str] = None
