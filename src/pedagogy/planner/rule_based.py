from typing import Dict, List, Optional

from ..models.context import PedagogicalContext
from ..models.action import PedagogicalAction, ActionType
from ..models.evidence import Evidence, EvidenceType
from ..knowledge.graph_repository import KnowledgeGraphRepository
from .interface import DecisionPlanner


class RuleBasedPlanner(DecisionPlanner):
    def __init__(
        self,
        max_consecutive_errors_to_recover: int = 3,
        max_consecutive_success_to_advance: int = 3,
        max_probes_per_competency: int = 5,
        probe_ids_by_competency: Optional[Dict[str, List[str]]] = None,
        knowledge_graph: Optional[KnowledgeGraphRepository] = None,
    ):
        self.max_consecutive_errors_to_recover = max_consecutive_errors_to_recover
        self.max_consecutive_success_to_advance = max_consecutive_success_to_advance
        self.max_probes_per_competency = max_probes_per_competency
        self.probe_ids_by_competency = probe_ids_by_competency or {}
        self._knowledge_graph = knowledge_graph

    def decide(self, context: PedagogicalContext) -> PedagogicalAction:
        learner = context.student
        recent = context.recent_evidence
        competency = learner.current_competency

        if not competency:
            return PedagogicalAction(
                type=ActionType.PROBE,
                reasoning="Nenhuma competência ativa — iniciando com sonda.",
            )

        if not recent:
            return self._first_interaction_action(competency)

        last_evidence = recent[-1]
        consecutive_errors = self._count_consecutive(recent, EvidenceType.WRONG_ANSWER)
        consecutive_successes = self._count_consecutive(
            recent, EvidenceType.CORRECT_ANSWER
        )

        if last_evidence.type == EvidenceType.HELP_REQUESTED:
            return PedagogicalAction(
                type=ActionType.EXPLAIN,
                target_competency=competency,
                strategy_params={"tone": "encouraging"},
                reasoning="Aluno pediu ajuda — explicar com tom encorajador.",
            )

        if consecutive_errors >= self.max_consecutive_errors_to_recover:
            prereq = self._find_prerequisite(competency)
            return PedagogicalAction(
                type=ActionType.RECOVER_BASE,
                target_competency=prereq or competency,
                reasoning=(
                    f"{consecutive_errors} erros consecutivos em {competency}. "
                    f"Recuperando base: {prereq or competency}."
                ),
            )

        if consecutive_successes >= self.max_consecutive_success_to_advance:
            return PedagogicalAction(
                type=ActionType.ADVANCE,
                target_competency=competency,
                reasoning=(
                    f"{consecutive_successes} acertos consecutivos em {competency}. "
                    f"Avançando para próximo tópico."
                ),
            )

        probe_count = self._count_probes_for_competency(recent, competency)
        if probe_count < self.max_probes_per_competency:
            return PedagogicalAction(
                type=ActionType.PROBE,
                target_competency=competency,
                reasoning=f"Aplicando sonda {probe_count + 1}/{self.max_probes_per_competency} para {competency}.",
            )

        return PedagogicalAction(
            type=ActionType.EXERCISE,
            target_competency=competency,
            reasoning=f"Máximo de sondas atingido para {competency}. Mudando para exercícios.",
        )

    def get_hypothesis(self, context: PedagogicalContext) -> Optional[str]:
        recent = context.recent_evidence
        if not recent:
            return None
        errors = [e for e in recent if e.type == EvidenceType.WRONG_ANSWER]
        if len(errors) >= 2:
            return (
                f"Dificuldade persistente em {errors[-1].competency} "
                f"({len(errors)} erros observados)."
            )
        return None

    def _first_interaction_action(self, competency: str) -> PedagogicalAction:
        return PedagogicalAction(
            type=ActionType.PROBE,
            target_competency=competency,
            reasoning=f"Primeira interação para {competency} — aplicar sonda diagnóstica.",
        )

    def _count_consecutive(
        self, evidence_list: List[Evidence], etype: EvidenceType
    ) -> int:
        count = 0
        for e in reversed(evidence_list):
            if e.type == etype:
                count += 1
            else:
                break
        return count

    def _count_probes_for_competency(
        self, evidence_list: List[Evidence], competency: str
    ) -> int:
        return sum(
            1
            for e in evidence_list
            if e.competency == competency and e.probe_id is not None
        )

    def _find_prerequisite(self, competency: str) -> Optional[str]:
        if self._knowledge_graph:
            prereqs = self._knowledge_graph.get_prerequisites(competency)
            if prereqs:
                return prereqs[0]
        return None
