from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class InvariantResult:
    name: str
    passed: bool
    error: str = ""


@dataclass
class Invariant:
    name: str
    check: Callable[[], bool]


class InvariantRegistry:
    _invariants: List[Invariant] = field(default_factory=list, init=False)

    @classmethod
    def register(cls, invariant: Invariant):
        cls._invariants.append(invariant)

    @classmethod
    def run_all(cls) -> List[InvariantResult]:
        results = []
        for inv in cls._invariants:
            try:
                ok = inv.check()
                results.append(InvariantResult(name=inv.name, passed=ok))
            except Exception as e:
                results.append(InvariantResult(name=inv.name, passed=False, error=str(e)))
        return results
