from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None


class KnowledgeGraphRepository:
    def __init__(self, competencies_path: Optional[str] = None):
        self._competencies: Dict[str, dict] = {}
        if competencies_path:
            self.load(competencies_path)

    def load(self, path: str) -> None:
        if yaml is None:
            raise ImportError("PyYAML is required to load competency files")
        filepath = Path(path)
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for comp in data.get("competencies", []):
            self._competencies[comp["id"]] = comp

    def get_prerequisites(self, competency: str) -> List[str]:
        comp = self._competencies.get(competency)
        if comp is None:
            return []
        return comp.get("prerequisites", [])

    def get_next_competencies(self, competency: str) -> List[str]:
        return [
            cid
            for cid, comp in self._competencies.items()
            if competency in comp.get("prerequisites", [])
        ]

    def get_difficulty(self, competency: str) -> int:
        comp = self._competencies.get(competency)
        if comp is None:
            return 1
        return comp.get("difficulty", 1)

    def get_probes(self, competency: str) -> List[str]:
        comp = self._competencies.get(competency)
        if comp is None:
            return []
        return comp.get("probes", [])

    def all_competencies(self) -> List[str]:
        return list(self._competencies.keys())
