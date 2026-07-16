import re
from abc import ABC, abstractmethod
from typing import Any, Dict

from ..models.probe import Probe


class BaseEvaluator(ABC):
    @abstractmethod
    def evaluate(self, student_response: str, probe: Probe) -> bool:
        pass


class ExactMatchEvaluator(BaseEvaluator):
    def evaluate(self, student_response: str, probe: Probe) -> bool:
        expected = probe.evaluator_config.get("expected", "")
        return student_response.strip() == str(expected).strip()


class RegexEvaluator(BaseEvaluator):
    def evaluate(self, student_response: str, probe: Probe) -> bool:
        pattern = probe.evaluator_config.get("pattern", "")
        return bool(re.search(pattern, student_response.strip()))


class SympyEvaluator(BaseEvaluator):
    def evaluate(self, student_response: str, probe: Probe) -> bool:
        try:
            expected = probe.evaluator_config.get("expected", "")
            return self._sympy_compare(student_response.strip(), str(expected).strip())
        except Exception:
            return False

    def _sympy_compare(self, response: str, expected: str) -> bool:
        try:
            import sympy
            resp_expr = sympy.sympify(response)
            expected_expr = sympy.sympify(expected)
            return sympy.simplify(resp_expr - expected_expr) == 0
        except ImportError:
            return response == expected


class EvaluatorFactory:
    _evaluators: Dict[str, type] = {
        "exact_match": ExactMatchEvaluator,
        "regex": RegexEvaluator,
        "sympy": SympyEvaluator,
    }

    @classmethod
    def register(cls, name: str, evaluator_class: type) -> None:
        cls._evaluators[name] = evaluator_class

    @classmethod
    def create(cls, evaluator_type: str) -> BaseEvaluator:
        evaluator_cls = cls._evaluators.get(evaluator_type)
        if evaluator_cls is None:
            raise ValueError(
                f"Unknown evaluator type: {evaluator_type}. "
                f"Available: {list(cls._evaluators.keys())}"
            )
        return evaluator_cls()
