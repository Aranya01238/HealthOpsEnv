from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List


class Observation(BaseModel):
    """
    All information visible to the AI agent for a given task step.
    Fields are nullable for tasks that don't use them.
    """
    task_id: str
    ticket_type: str
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    symptoms: Optional[List[str]] = None
    department_requested: Optional[str] = None
    doctor_availability: Optional[List[str]] = None
    doctor_available: Optional[bool] = None
    clinic_location: Optional[str] = None
    item: Optional[str] = None
    stock_remaining: Optional[int] = None
    daily_usage: Optional[int] = None
    ambulance_eta: Optional[int] = None
    lab_status: Optional[str] = None
    staff_available: Optional[int] = None
    current_status: str
