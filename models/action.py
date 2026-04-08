from __future__ import annotations
from pydantic import BaseModel, field_validator
from typing import Optional, List

VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_DEPARTMENTS = {
    "appointments", "procurement", "emergency", "cardiology",
    "orthopedics", "laboratory", "operations", "administration", "ambulance"
}
VALID_ESCALATION_LEVELS = {"low", "medium", "high", "highest", None}


class Action(BaseModel):
    """
    The decision returned by the AI agent after observing a task state.
    """
    priority: str
    department: str
    action: str
    notify: List[str]
    escalation_level: Optional[str] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {VALID_PRIORITIES}, got '{v}'")
        return v

    @field_validator("department")
    @classmethod
    def validate_department(cls, v: str) -> str:
        if v not in VALID_DEPARTMENTS:
            raise ValueError(f"department must be one of {VALID_DEPARTMENTS}, got '{v}'")
        return v

    @field_validator("escalation_level")
    @classmethod
    def validate_escalation_level(cls, v: Optional[str]) -> Optional[str]:
        if v not in VALID_ESCALATION_LEVELS:
            raise ValueError(f"escalation_level must be one of {VALID_ESCALATION_LEVELS}, got '{v}'")
        return v
