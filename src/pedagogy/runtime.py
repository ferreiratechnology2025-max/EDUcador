from dataclasses import dataclass, field
from typing import Optional

from .models.evidence import Evidence, EvidenceType
from .models.context import PedagogicalContext, LearningContext
from .models.action import PedagogicalAction
from .planner.interface import DecisionPlanner
from .probes.repository import ProbeRepository
from .probes.evaluator import EvaluatorFactory
from .memory.event_store import EventStore
from .composer.instruction_composer import InstructionComposer, Instruction
from .extractors.evidence_extractor import EvidenceExtractor


@dataclass
class PedagogicalResponse:
    instruction: Instruction
    evidence: Optional[Evidence] = None
    action: Optional[PedagogicalAction] = None
    hypothesis: Optional[str] = None


class PedagogicalRuntime:
    def __init__(
        self,
        planner: DecisionPlanner,
        probe_repo: ProbeRepository,
        event_store: EventStore,
        composer: InstructionComposer,
        evaluator_factory: EvaluatorFactory,
    ):
        self.planner = planner
        self.probe_repo = probe_repo
        self.event_store = event_store
        self.composer = composer
        self.evaluator_factory = evaluator_factory
        self._evidence_extractor = EvidenceExtractor(probe_repo, evaluator_factory)

    def process(
        self,
        student_input: str,
        session_id: str,
        competency: Optional[str] = None,
    ) -> PedagogicalResponse:
        context = self._build_context(session_id, competency)
        action = self.planner.decide(context)
        hypothesis = self.planner.get_hypothesis(context)

        if action.type == action.type.PROBE and action.target_competency:
            evidence = self._evidence_extractor.extract(
                student_input, context, action
            )
            if evidence:
                self.event_store.append(session_id, evidence)
                context.recent_evidence.append(evidence)
                context.student.evidence_window.append(evidence)
                action = self.planner.decide(context)
                hypothesis = self.planner.get_hypothesis(context)

        instruction = self._execute_action(action, context)
        return PedagogicalResponse(
            instruction=instruction,
            action=action,
            hypothesis=hypothesis,
        )

    def _build_context(
        self, session_id: str, competency: Optional[str] = None
    ) -> PedagogicalContext:
        recent = self.event_store.get_recent_evidence(session_id, limit=20)
        learner = LearningContext(
            session_id=session_id,
            current_competency=competency,
            evidence_window=recent,
        )
        return PedagogicalContext(
            student=learner,
            recent_evidence=recent,
        )

    def _execute_action(
        self, action: PedagogicalAction, context: PedagogicalContext
    ) -> Instruction:
        return self.composer.compose(action, context)

    def add_student_response(
        self, student_input: str, session_id: str, probe_id: str
    ) -> Evidence:
        evidence = self._evidence_extractor.extract_direct(
            student_input, session_id, probe_id
        )
        self.event_store.append(session_id, evidence)
        return evidence
