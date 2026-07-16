import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..models.evidence import Evidence, EvidenceType


class EventStore:
    def __init__(self, storage_path: str = "data/events/"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, List[Evidence]] = {}

    def _session_path(self, session_id: str) -> Path:
        return self.storage_path / f"{session_id}.jsonl"

    def append(self, session_id: str, evidence: Evidence) -> None:
        entry = {
            "id": evidence.id,
            "session_id": evidence.session_id,
            "type": evidence.type.value,
            "competency": evidence.competency,
            "timestamp": evidence.timestamp.isoformat(),
            "raw_data": evidence.raw_data,
            "probe_id": evidence.probe_id,
        }
        filepath = self._session_path(session_id)
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        if session_id in self._cache:
            self._cache[session_id].append(evidence)

    def get_evidence_by_session(self, session_id: str) -> List[Evidence]:
        if session_id not in self._cache:
            self._cache[session_id] = self._load_session(session_id)
        return list(self._cache[session_id])

    def get_history(self, session_id: str) -> List[Evidence]:
        return self.get_evidence_by_session(session_id)

    def get_evidence_by_competency(
        self, session_id: str, competency: str
    ) -> List[Evidence]:
        all_evidence = self.get_evidence_by_session(session_id)
        return [e for e in all_evidence if e.competency == competency]

    def get_recent_evidence(
        self, session_id: str, limit: int = 10
    ) -> List[Evidence]:
        all_evidence = self.get_evidence_by_session(session_id)
        return all_evidence[-limit:]

    def _load_session(self, session_id: str) -> List[Evidence]:
        filepath = self._session_path(session_id)
        if not filepath.exists():
            return []
        evidence_list = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                evidence_list.append(
                    Evidence(
                        id=data["id"],
                        session_id=data["session_id"],
                        type=EvidenceType(data["type"]),
                        competency=data["competency"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        raw_data=data["raw_data"],
                        probe_id=data.get("probe_id"),
                    )
                )
        return evidence_list

    def clear_session(self, session_id: str) -> None:
        filepath = self._session_path(session_id)
        if filepath.exists():
            os.remove(filepath)
        self._cache.pop(session_id, None)
