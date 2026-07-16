from typing import Dict, List, Optional

from ..models.probe import Probe


class ProbeRepository:
    def __init__(self, probes: Optional[Dict[str, Probe]] = None):
        self._probes: Dict[str, Probe] = probes or {}

    def get(self, probe_id: str) -> Optional[Probe]:
        return self._probes.get(probe_id)

    def get_by_competency(self, competency: str) -> List[Probe]:
        return [p for p in self._probes.values() if p.competency == competency]

    def add(self, probe: Probe) -> None:
        self._probes[probe.id] = probe

    def all(self) -> List[Probe]:
        return list(self._probes.values())
