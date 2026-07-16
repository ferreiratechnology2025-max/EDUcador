from datetime import datetime
from typing import Optional
from uuid import uuid4

from ..models.evidence import Evidence, EvidenceType
from ..models.context import PedagogicalContext
from ..models.action import PedagogicalAction
from ..probes.repository import ProbeRepository
from ..probes.evaluator import EvaluatorFactory


class EvidenceExtractor:
    def __init__(
        self, probe_repo: ProbeRepository, evaluator_factory: EvaluatorFactory
    ):
        self._probe_repo = probe_repo
        self._evaluator_factory = evaluator_factory

    def extract(
        self,
        student_input: str,
        context: PedagogicalContext,
        action: PedagogicalAction,
    ) -> Optional[Evidence]:
        probe_id = action.probe_id
        if not probe_id and action.target_competency:
            probes = self._probe_repo.get_by_competency(action.target_competency)
            if probes:
                probe_id = probes[0].id

        if not probe_id:
            return None

        probe = self._probe_repo.get(probe_id)
        if not probe:
            return None

        evaluator = self._evaluator_factory.create(probe.evaluator_type)
        is_correct = evaluator.evaluate(student_input, probe)

        evidence_type = (
            EvidenceType.CORRECT_ANSWER if is_correct else EvidenceType.WRONG_ANSWER
        )
        return Evidence(
            id=str(uuid4()),
            session_id=context.student.session_id,
            type=evidence_type,
            competency=probe.competency,
            timestamp=datetime.now(),
            raw_data={
                "student_input": student_input,
                "expected_schema": probe.expected_response_schema,
                "evaluator_used": probe.evaluator_type,
            },
            probe_id=probe.id,
        )

    def extract_direct(
        self, student_input: str, session_id: str, probe_id: str
    ) -> Evidence:
        probe = self._probe_repo.get(probe_id)
        if not probe:
            raise ValueError(f"Unknown probe: {probe_id}")
        evaluator = self._evaluator_factory.create(probe.evaluator_type)
        is_correct = evaluator.evaluate(student_input, probe)
        evidence_type = (
            EvidenceType.CORRECT_ANSWER if is_correct else EvidenceType.WRONG_ANSWER
        )
        return Evidence(
            id=str(uuid4()),
            session_id=session_id,
            type=evidence_type,
            competency=probe.competency,
            timestamp=datetime.now(),
            raw_data={
                "student_input": student_input,
                "probe_id": probe_id,
                "evaluator_used": probe.evaluator_type,
            },
            probe_id=probe.id,
        )
