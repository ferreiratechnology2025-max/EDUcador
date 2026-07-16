from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ActionType(Enum):
    PROBE = "probe"
    EXPLAIN = "explain"
    ANALOGY = "analogy"
    RECOVER_BASE = "recover_base"
    ADVANCE = "advance"
    EXERCISE = "exercise"
    EXAMPLE = "example"
    FALLBACK = "fallback"


@dataclass
class PedagogicalDecision:
    action: ActionType
    target_competency: Optional[str] = None
    probe_id: Optional[str] = None
    strategy_params: Optional[Dict[str, Any]] = None
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None
