from dataclasses import dataclass
from typing import Optional

from ..models.action import PedagogicalAction, ActionType as PedagogyActionType
from ..models.context import PedagogicalContext
from ..models.probe import Probe


@dataclass
class Instruction:
    role: str
    content: str
    parameters: dict


class InstructionComposer:
    def compose(
        self, action: PedagogicalAction, context: PedagogicalContext
    ) -> Instruction:
        mapping = {
            PedagogyActionType.PROBE: self._compose_probe_generic,
            PedagogyActionType.EXPLAIN: self._compose_explanation,
            PedagogyActionType.ANALOGY: self._compose_analogy,
            PedagogyActionType.RECOVER_BASE: self._compose_recover_base,
            PedagogyActionType.ADVANCE: self._compose_advance,
            PedagogyActionType.EXERCISE: self._compose_exercise,
            PedagogyActionType.EXAMPLE: self._compose_example,
        }
        handler = mapping.get(action.type, self._compose_fallback)
        return handler(action, context)

    def compose_decision(
        self, decision, context: PedagogicalContext
    ) -> Instruction:
        action_value = (
            decision.action.value
            if hasattr(decision.action, "value")
            else str(decision.action)
        )
        action_type_map = {
            "probe": PedagogyActionType.PROBE,
            "explain": PedagogyActionType.EXPLAIN,
            "analogy": PedagogyActionType.ANALOGY,
            "recover_base": PedagogyActionType.RECOVER_BASE,
            "advance": PedagogyActionType.ADVANCE,
            "exercise": PedagogyActionType.EXERCISE,
            "example": PedagogyActionType.EXAMPLE,
        }
        internal_type = action_type_map.get(action_value, PedagogyActionType.PROBE)
        internal_action = PedagogicalAction(
            type=internal_type,
            target_competency=(
                decision.target_competency
                if hasattr(decision, "target_competency")
                else None
            ),
            probe_id=decision.probe_id if hasattr(decision, "probe_id") else None,
            strategy_params=(
                decision.strategy_params
                if hasattr(decision, "strategy_params")
                else None
            ),
        )
        return self.compose(internal_action, context)

    def compose_probe_prompt(self, probe: Probe) -> str:
        return probe.prompt_template

    def compose_explanation_prompt(
        self, competency: str, context: PedagogicalContext
    ) -> str:
        return f"Explique o conceito de {competency.replace('_', ' ')} de forma clara e didática para o aluno."

    def _compose_probe_generic(
        self, action: PedagogicalAction, context: PedagogicalContext
    ) -> Instruction:
        return Instruction(
            role="tutor",
            content=(
                f"Vamos testar seus conhecimentos sobre "
                f"{action.target_competency.replace('_', ' ') if action.target_competency else 'o tópico atual'}."
            ),
            parameters={"type": "probe", "difficulty": "adaptive"},
        )

    def _compose_explanation(
        self, action: PedagogicalAction, context: PedagogicalContext
    ) -> Instruction:
        tone = "encorajador" if action.strategy_params and action.strategy_params.get("tone") == "encouraging" else "neutro"
        competency = action.target_competency or "o tópico"
        return Instruction(
            role="explicador",
            content=f"Explique {competency.replace('_', ' ')} com tom {tone}.",
            parameters={"tone": tone, "type": "explanation"},
        )

    def _compose_analogy(
        self, action: PedagogicalAction, context: PedagogicalContext
    ) -> Instruction:
        return Instruction(
            role="analogista",
            content=(
                f"Crie uma analogia para explicar "
                f"{action.target_competency.replace('_', ' ') if action.target_competency else 'o conceito'}."
            ),
            parameters={"type": "analogy"},
        )

    def _compose_recover_base(
        self, action: PedagogicalAction, context: PedagogicalContext
    ) -> Instruction:
        return Instruction(
            role="tutor",
            content=(
                f"Parece que você está com dificuldade em "
                f"{action.target_competency.replace('_', ' ') if action.target_competency else 'este tópico'}. "
                f"Vamos revisar os fundamentos."
            ),
            parameters={"type": "recovery", "difficulty": "easy"},
        )

    def _compose_advance(
        self, action: PedagogicalAction, context: PedagogicalContext
    ) -> Instruction:
        return Instruction(
            role="tutor",
            content="Ótimo trabalho! Vamos avançar para o próximo nível.",
            parameters={"type": "advance", "difficulty": "harder"},
        )

    def _compose_exercise(
        self, action: PedagogicalAction, context: PedagogicalContext
    ) -> Instruction:
        return Instruction(
            role="tutor",
            content=(
                f"Resolva o exercício sobre "
                f"{action.target_competency.replace('_', ' ') if action.target_competency else 'o tópico atual'}."
            ),
            parameters={"type": "exercise"},
        )

    def _compose_example(
        self, action: PedagogicalAction, context: PedagogicalContext
    ) -> Instruction:
        return Instruction(
            role="explicador",
            content=(
                f"Mostre um exemplo prático de "
                f"{action.target_competency.replace('_', ' ') if action.target_competency else 'o conceito'}."
            ),
            parameters={"type": "example"},
        )

    def _compose_fallback(
        self, action: PedagogicalAction, context: PedagogicalContext
    ) -> Instruction:
        return Instruction(
            role="tutor",
            content="Vamos continuar praticando.",
            parameters={"type": "general"},
        )
