from dataclasses import dataclass
from enum import Enum
from typing import Optional


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
class PedagogicalAction:
    type: ActionType
    target_competency: Optional[str] = None
    probe_id: Optional[str] = None
    strategy_params: Optional[dict] = None
    reasoning: Optional[str] = None
