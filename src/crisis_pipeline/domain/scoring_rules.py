from .entities import IncidentRecord
from .enums import Priority


def compute_incident_score(incident: IncidentRecord) -> float:
    """
    Deterministic scoring logic.
    Converts structured signals → numeric score.
    """

    score = 0.0

    # ---------------------------
    # 1. People count impact
    # ---------------------------
    if incident.people_count >= 10:
        score += 5
    elif incident.people_count >= 5:
        score += 3
    else:
        score += 1

    # ---------------------------
    # 2. Urgency keywords impact
    # ---------------------------
    urgency_map = {
        "drowning": 5,
        "trapped": 4,
        "injured": 3,
        "hungry": 2,
        "need water": 2
    }

    for keyword in incident.urgency_keywords:
        score += urgency_map.get(keyword.lower(), 0)

    # ---------------------------
    # 3. Intent weighting
    # ---------------------------
    if incident.intent.value == "rescue":
        score += 5
    elif incident.intent.value == "supply":
        score += 2
    else:
        score += 1

    return score


def assign_priority(score: float) -> Priority:
    """
    Convert score → priority label
    """
    if score >= 8:
        return Priority.HIGH
    return Priority.LOW