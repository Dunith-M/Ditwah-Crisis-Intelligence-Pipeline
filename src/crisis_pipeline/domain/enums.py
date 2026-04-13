from enum import Enum


class Intent(str, Enum):
    RESCUE = "rescue"
    SUPPLY = "supply"
    INFO = "info"
    OTHER = "other"


class Priority(str, Enum):
    HIGH = "high"
    LOW = "low"


class Status(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    STABLE = "stable"