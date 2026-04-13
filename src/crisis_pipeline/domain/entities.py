from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

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
# 4. Crisis Event (from news extraction)
# ---------------------------
@dataclass
class CrisisEvent:
    event_id: str
    event_type: str
    location: str
    severity: Status
    description: str
    detected_at: datetime