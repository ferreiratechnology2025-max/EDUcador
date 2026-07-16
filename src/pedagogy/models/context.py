from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .evidence import Evidence
from .action import PedagogicalAction


@dataclass
class LearningContext:
    session_id: str
    current_competency: Optional[str] = None
    evidence_window: List[Evidence] = field(default_factory=list)
    current_hypothesis: Optional[str] = None
    session_goal: Optional[str] = None


@dataclass
class PedagogicalContext:
    student: LearningContext
    recent_evidence: List[Evidence] = field(default_factory=list)
    last_action: Optional[PedagogicalAction] = None
    active_hypothesis: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    competency_id: Optional[str] = None
    last_evidence: Optional[Evidence] = None
    evidence_count: int = 0
    recent_results: List[Any] = field(default_factory=list)
