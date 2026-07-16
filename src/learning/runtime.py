from typing import Optional, Dict

from src.pedagogy.models.evidence import Evidence
from src.pedagogy.models.context import PedagogicalContext, LearningContext
from src.pedagogy.planner.interface import DecisionPlanner
from src.pedagogy.probes.repository import ProbeRepository
from src.pedagogy.probes.evaluator import EvaluatorFactory
from src.pedagogy.memory.event_store import EventStore
from src.pedagogy.composer.instruction_composer import InstructionComposer
from src.pedagogy.extractors.evidence_extractor import EvidenceExtractor
from .domain import PedagogicalDecision, ActionType
from .executor.strategy_executor import StrategyExecutor
from .tutor.llm_tutor import LLMTutor
from .presentation.response import TutorResponse


class PedagogicalRuntime:
    def __init__(
        self,
        extractor: EvidenceExtractor,
        event_store: EventStore,
        planner: DecisionPlanner,
        executor: StrategyExecutor,
        tutor: LLMTutor,
    ):
        self._extractor = extractor
        self._event_store = event_store
        self._planner = planner
        self._executor = executor
        self._tutor = tutor

    def process(
        self,
        user_input: str,
        session_id: str,
        competency: Optional[str] = None,
    ) -> TutorResponse:
        context = self._build_context(session_id, competency)
        action = self._planner.decide(context)

        if self._is_probe_action(action) and action.target_competency:
            evidence = self._extractor.extract(user_input, context, action)
            if evidence:
                self._event_store.append(session_id, evidence)
                context.student.evidence_window.append(evidence)
                action = self._planner.decide(context)

        decision = self._to_domain_decision(action)
        execution_result = self._executor.execute(decision, context)
        return self._tutor.generate(execution_result, session_id=session_id)

    def _build_context(
        self, session_id: str, competency: Optional[str] = None
    ) -> PedagogicalContext:
        recent = self._event_store.get_recent_evidence(session_id, limit=20)
        learner = LearningContext(
            session_id=session_id,
            current_competency=competency,
            evidence_window=recent,
        )
        ctx = PedagogicalContext(
            student=learner,
            recent_evidence=recent,
            competency_id=competency,
            evidence_count=len(recent),
        )
        if recent:
            ctx.last_evidence = recent[-1]
        return ctx

    def _is_probe_action(self, action) -> bool:
        return hasattr(action, "type") and action.type.value == "probe"

    def _to_domain_decision(self, action) -> PedagogicalDecision:
        action_type_map = {
            "probe": ActionType.PROBE,
            "explain": ActionType.EXPLAIN,
            "analogy": ActionType.ANALOGY,
            "recover_base": ActionType.RECOVER_BASE,
            "advance": ActionType.ADVANCE,
            "exercise": ActionType.EXERCISE,
            "example": ActionType.EXAMPLE,
        }
        internal_type = getattr(action, "type", None)
        type_value = internal_type.value if internal_type else "probe"
        mapped = action_type_map.get(type_value, ActionType.PROBE)
        return PedagogicalDecision(
            action=mapped,
            target_competency=getattr(action, "target_competency", None),
            probe_id=getattr(action, "probe_id", None),
            strategy_params=getattr(action, "strategy_params", None),
        )
