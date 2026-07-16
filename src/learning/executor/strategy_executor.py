from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..domain import PedagogicalDecision, ActionType
from src.pedagogy.models.context import PedagogicalContext
from src.pedagogy.models.probe import Probe
from src.pedagogy.probes.repository import ProbeRepository
from src.pedagogy.composer.instruction_composer import (
    InstructionComposer,
    Instruction,
)


@dataclass
class ExecutionResult:
    type: str
    instruction: Optional[Instruction] = None
    prompt: Optional[str] = None
    probe_id: Optional[str] = None
    probe: Optional[Probe] = None
    target_competency: Optional[str] = None
    message: Optional[str] = None
    evidence: Optional[Any] = None  # Evidence produced during execution. Runtime writes to EventStore.
    # Contract: Executor -> ExecutionResult (evidence) -> Runtime -> EventStore.
    # Executor MUST NOT import EventStore directly.


class StrategyExecutor:
    def __init__(
        self,
        probe_repo: ProbeRepository,
        composer: InstructionComposer,
    ):
        self._probe_repo = probe_repo
        self._composer = composer

    def execute(
        self, decision: PedagogicalDecision, context: PedagogicalContext
    ) -> ExecutionResult:
        mapping = {
            ActionType.PROBE: self._execute_probe,
            ActionType.EXPLAIN: self._execute_explain,
            ActionType.ANALOGY: self._execute_analogy,
            ActionType.RECOVER_BASE: self._execute_recover_base,
            ActionType.ADVANCE: self._execute_advance,
            ActionType.EXERCISE: self._execute_exercise,
            ActionType.EXAMPLE: self._execute_example,
        }
        handler = mapping.get(decision.action, self._execute_fallback)
        return handler(decision, context)

    def _execute_probe(
        self, decision: PedagogicalDecision, context: PedagogicalContext
    ) -> ExecutionResult:
        probe = None
        if decision.probe_id:
            probe = self._probe_repo.get(decision.probe_id)
        if not probe and decision.target_competency:
            probes = self._probe_repo.get_by_competency(decision.target_competency)
            if probes:
                probe = probes[0]
        if probe:
            return ExecutionResult(
                type="probe",
                prompt=probe.prompt_template,
                probe_id=probe.id,
                probe=probe,
                target_competency=probe.competency,
            )
        return ExecutionResult(
            type="probe",
            prompt="Vamos testar seus conhecimentos.",
        )

    def _execute_explain(
        self, decision: PedagogicalDecision, context: PedagogicalContext
    ) -> ExecutionResult:
        instruction = self._composer.compose_decision(decision, context)
        return ExecutionResult(
            type="instruction",
            instruction=instruction,
            target_competency=decision.target_competency,
        )

    def _execute_analogy(
        self, decision: PedagogicalDecision, context: PedagogicalContext
    ) -> ExecutionResult:
        instruction = self._composer.compose_decision(decision, context)
        return ExecutionResult(
            type="instruction",
            instruction=instruction,
            target_competency=decision.target_competency,
        )

    def _execute_recover_base(
        self, decision: PedagogicalDecision, context: PedagogicalContext
    ) -> ExecutionResult:
        instruction = self._composer.compose_decision(decision, context)
        return ExecutionResult(
            type="instruction",
            instruction=instruction,
            target_competency=decision.target_competency,
        )

    def _execute_advance(
        self,
        decision: PedagogicalDecision,
        context: PedagogicalContext,
    ) -> ExecutionResult:
        return ExecutionResult(
            type="advance",
            message="Otim! Vamos para o proximo conceito.",
        )

    def _execute_exercise(
        self, decision: PedagogicalDecision, context: PedagogicalContext
    ) -> ExecutionResult:
        instruction = self._composer.compose_decision(decision, context)
        return ExecutionResult(
            type="instruction",
            instruction=instruction,
        )

    def _execute_example(
        self, decision: PedagogicalDecision, context: PedagogicalContext
    ) -> ExecutionResult:
        instruction = self._composer.compose_decision(decision, context)
        return ExecutionResult(
            type="instruction",
            instruction=instruction,
        )

    def _execute_fallback(
        self, decision: PedagogicalDecision, context: PedagogicalContext
    ) -> ExecutionResult:
        return ExecutionResult(type="instruction", message="Vamos continuar praticando.")
