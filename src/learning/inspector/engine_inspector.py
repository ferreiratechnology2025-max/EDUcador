from typing import List

from src.pedagogy.models.evidence import Evidence
from src.pedagogy.models.context import PedagogicalContext
from src.pedagogy.memory.event_store import EventStore
from src.pedagogy.planner.interface import DecisionPlanner
from ..domain import PedagogicalDecision


class DecisionTrace:
    def __init__(
        self,
        context_summary: str,
        decision: PedagogicalDecision,
        rule_triggered: str = "",
    ):
        self.context_summary = context_summary
        self.decision = decision
        self.rule_triggered = rule_triggered


class EngineInspector:
    def __init__(
        self,
        event_store: EventStore,
        planner: DecisionPlanner,
    ):
        self._event_store = event_store
        self._planner = planner

    def get_session_evidence(self, session_id: str) -> List[Evidence]:
        return self._event_store.get_evidence_by_session(session_id)

    def get_planner_trace(
        self, context: PedagogicalContext
    ) -> List[DecisionTrace]:
        evidence_count = len(context.recent_evidence)
        last_type = (
            context.recent_evidence[-1].type.value
            if context.recent_evidence
            else "none"
        )
        return [
            DecisionTrace(
                context_summary=(
                    f"{evidence_count} evidencias, "
                    f"ultima: {last_type}, "
                    f"competencia: {context.student.current_competency}"
                ),
                decision=PedagogicalDecision(
                    action=self._planner.decide(context).type,
                    target_competency=self._planner.decide(context).target_competency,
                ),
                rule_triggered=self._infer_rule(context),
            )
        ]

    def _infer_rule(self, context: PedagogicalContext) -> str:
        recent = context.recent_evidence
        if not recent:
            return "first_interaction"
        last = recent[-1]
        if last.type.value == "help_requested":
            return "help_requested"
        errors = sum(1 for e in reversed(recent[-3:]) if e.type.value == "wrong_answer")
        if errors >= 3:
            return "max_errors_reached"
        successes = sum(
            1 for e in reversed(recent[-3:]) if e.type.value == "correct_answer"
        )
        if successes >= 3:
            return "max_successes_reached"
        return "default_probe"
