from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class EvidenceType(Enum):
    CORRECT_ANSWER = "correct_answer"
    WRONG_ANSWER = "wrong_answer"
    HINT_REQUESTED = "hint_requested"
    TIME_EXCEEDED = "time_exceeded"
    INDEPENDENT_TRANSFER = "independent_transfer"
    HELP_REQUESTED = "help_requested"
    NEW_CAPABILITY_OBSERVED = "new_capability_observed"
    PERSISTENT_DIFFICULTY = "persistent_difficulty"
    RECOVERED_COMPETENCY = "recovered_competency"


@dataclass
class Evidence:
    id: str
    session_id: str
    type: EvidenceType
    competency: str
    timestamp: datetime
    raw_data: dict
    probe_id: Optional[str] = None
