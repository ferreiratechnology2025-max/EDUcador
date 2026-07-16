#!/usr/bin/env python3

import sys
import os
from datetime import datetime
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pedagogy.models.evidence import Evidence, EvidenceType
from src.pedagogy.models.context import PedagogicalContext, LearningContext
from src.pedagogy.planner.rule_based import RuleBasedPlanner
from src.pedagogy.knowledge.graph_repository import KnowledgeGraphRepository
from src.learning.domain import ActionType


def make_evidence(etype, competency, session="bench") -> Evidence:
    return Evidence(
        id=str(uuid4()),
        session_id=session,
        type=etype,
        competency=competency,
        timestamp=datetime.now(),
        raw_data={},
    )


SCENARIOS = [
    {
        "name": "Sem competencia ativa -> PROBE",
        "competency": None,
        "evidence": [],
        "expected": ActionType.PROBE,
    },
    {
        "name": "Primeira interacao com competencia -> PROBE",
        "competency": "isolar_incognita_adicao",
        "evidence": [],
        "expected": ActionType.PROBE,
    },
    {
        "name": "3 erros consecutivos -> RECOVER_BASE",
        "competency": "isolar_incognita_adicao",
        "evidence": [make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_adicao") for _ in range(3)],
        "expected": ActionType.RECOVER_BASE,
    },
    {
        "name": "2 erros consecutivos -> ainda PROBE (threshold=3)",
        "competency": "isolar_incognita_adicao",
        "evidence": [make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_adicao") for _ in range(2)],
        "expected": ActionType.PROBE,
    },
    {
        "name": "3 acertos consecutivos -> ADVANCE",
        "competency": "isolar_incognita_adicao",
        "evidence": [make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao") for _ in range(3)],
        "expected": ActionType.ADVANCE,
    },
    {
        "name": "2 acertos consecutivos -> ainda PROBE (threshold=3)",
        "competency": "isolar_incognita_adicao",
        "evidence": [make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao") for _ in range(2)],
        "expected": ActionType.PROBE,
    },
    {
        "name": "Pedido de ajuda -> EXPLAIN",
        "competency": "isolar_incognita_adicao",
        "evidence": [make_evidence(EvidenceType.HELP_REQUESTED, "isolar_incognita_adicao")],
        "expected": ActionType.EXPLAIN,
    },
    {
        "name": "Ultimo evento e HELP_REQUESTED -> EXPLAIN",
        "competency": "isolar_incognita_adicao",
        "evidence": [
            make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.HELP_REQUESTED, "isolar_incognita_adicao"),
        ],
        "expected": ActionType.EXPLAIN,
    },
    {
        "name": "RECOVER_BASE com KnowledgeGraph -> pre-requisito",
        "competency": "isolar_incognita_multiplicacao",
        "use_kg": True,
        "evidence": [make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_multiplicacao") for _ in range(3)],
        "expected": ActionType.RECOVER_BASE,
        "expected_target": "isolar_incognita_adicao",
    },
    {
        "name": "ADVANCE com KnowledgeGraph",
        "competency": "isolar_incognita_adicao",
        "use_kg": True,
        "evidence": [make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao") for _ in range(3)],
        "expected": ActionType.ADVANCE,
    },
    {
        "name": "Alternados (acerto,erro,acerto) -> PROBE",
        "competency": "isolar_incognita_adicao",
        "evidence": [
            make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao"),
        ],
        "expected": ActionType.PROBE,
    },
    {
        "name": "5 com probe_id -> EXERCISE (max sondas=5)",
        "competency": "isolar_incognita_adicao",
        "evidence": [
            Evidence(id=str(uuid4()), session_id="bench",
                     type=(EvidenceType.CORRECT_ANSWER if i % 2 == 0 else EvidenceType.WRONG_ANSWER),
                     competency="isolar_incognita_adicao",
                     timestamp=datetime.now(), raw_data={}, probe_id=f"p{i}")
            for i in range(5)
        ],
        "expected": ActionType.EXERCISE,
    },
]


def build_kg():
    kg = KnowledgeGraphRepository()
    kg._competencies = {
        "isolar_incognita_adicao": {"id": "isolar_incognita_adicao", "prerequisites": []},
        "isolar_incognita_multiplicacao": {
            "id": "isolar_incognita_multiplicacao",
            "prerequisites": ["isolar_incognita_adicao"],
        },
    }
    return kg


def benchmark_planner(planner, scenarios) -> float:
    correct = 0
    for s in scenarios:
        kg = build_kg() if s.get("use_kg") else None
        p = RuleBasedPlanner(
            knowledge_graph=kg,
            max_probes_per_competency=5,
        )
        learner = LearningContext(
            session_id="bench",
            current_competency=s["competency"],
            evidence_window=s["evidence"],
        )
        ctx = PedagogicalContext(student=learner, recent_evidence=s["evidence"])
        action = p.decide(ctx)

        action_ok = action.type.value == s["expected"].value
        target_ok = True
        if "expected_target" in s:
            target_ok = action.target_competency == s["expected_target"]

        if action_ok and target_ok:
            correct += 1
            print(f"  PASS - {s['name']}")
        else:
            print(f"  FAIL - {s['name']}")
            print(f"    Esperado: {s['expected'].value}", end="")
            if "expected_target" in s:
                print(f" / alvo: {s['expected_target']}", end="")
            print()
            print(f"    Obtido:   {action.type.value}", end="")
            if "expected_target" in s:
                print(f" / alvo: {action.target_competency}", end="")
            print()
    return correct / len(scenarios)


def main():
    print("=" * 60)
    print("  Benchmark do Planner")
    print("=" * 60)
    print()

    planner = RuleBasedPlanner(max_probes_per_competency=5)
    accuracy = benchmark_planner(planner, SCENARIOS)
    total = len(SCENARIOS)
    passed = int(accuracy * total)

    print()
    print("=" * 60)
    print(f"  Resultado: {passed}/{total} passaram ({accuracy*100:.0f}%)")
    print("=" * 60)
    return accuracy >= 1.0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
