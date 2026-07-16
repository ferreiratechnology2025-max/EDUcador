from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class TutorResponse:
    session_id: str
    message: str
    action_type: str
    probe_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
