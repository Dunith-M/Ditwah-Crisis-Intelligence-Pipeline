from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field

from .enums import Intent, Priority, Status


# ---------------------------
# 1. Classified Message
# ---------------------------
@dataclass
class ClassifiedMessage:
    message_id: str
    text: str
    intent: Intent
    location: Optional[str]
    people_count: Optional[int]
    timestamp: datetime


# ---------------------------
# 2. Incident Record
# ---------------------------
@dataclass
class IncidentRecord:
    incident_id: str
    source_message_id: str
    intent: Intent
    people_count: int
    urgency_keywords: List[str]
    created_at: datetime
    priority: Optional[Priority] = None
    score: Optional[float] = None


# ---------------------------
# 3. Scenario Record (for stability experiments)
# ---------------------------
@dataclass
class ScenarioRecord:
    scenario_id: str
    description: str
    inputs: dict
    outputs: dict
    created_at: datetime


# ---------------------------
# 4. Crisis Event (Internal Domain Model)
# ---------------------------
@dataclass
class CrisisEvent:
    event_id: str
    event_type: str
    location: str
    severity: Status
    description: str
    detected_at: datetime


# ---------------------------
# 5. Crisis Event Extract (LLM Output Schema)
# ---------------------------
class CrisisEventExtract(BaseModel):
    district: str
    flood_level_meters: float = Field(ge=0)
    victim_count: int = Field(ge=0)
    main_need: str
    status: str