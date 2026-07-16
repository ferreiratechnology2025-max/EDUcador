#!/usr/bin/env python3

import sys
import os
from datetime import datetime
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pedagogy.models.evidence import Evidence, EvidenceType
from src.pedagogy.models.context import PedagogicalContext, LearningContext
from src.pedagogy.models.action import ActionType
from src.pedagogy.planner.rule_based import RuleBasedPlanner
from src.pedagogy.knowledge.graph_repository import KnowledgeGraphRepository


def make_evidence(etype: EvidenceType, competency: str, session: str = "bench") -> Evidence:
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
        "name": "Primeira interação sem competência ativa",
        "competency": None,
        "evidence": [],
        "expected": ActionType.PROBE,
    },
    {
        "name": "Primeira interação com competência definida",
        "competency": "isolar_incognita_adicao",
        "evidence": [],
        "expected": ActionType.PROBE,
    },
    {
        "name": "Tres erros consecutivos -> RECOVER_BASE",
        "competency": "isolar_incognita_adicao",
        "evidence": [
            make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_adicao"),
        ],
        "expected": ActionType.RECOVER_BASE,
    },
    {
        "name": "Dois erros consecutivos -> ainda PROBE (threshold=3)",
        "competency": "isolar_incognita_adicao",
        "evidence": [
            make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_adicao"),
        ],
        "expected": ActionType.PROBE,
    },
    {
        "name": "Tres acertos consecutivos -> ADVANCE",
        "competency": "isolar_incognita_adicao",
        "evidence": [
            make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao"),
        ],
        "expected": ActionType.ADVANCE,
    },
    {
        "name": "Dois acertos consecutivos -> ainda PROBE (threshold=3)",
        "competency": "isolar_incognita_adicao",
        "evidence": [
            make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao"),
        ],
        "expected": ActionType.PROBE,
    },
    {
        "name": "Pedido de ajuda -> EXPLAIN (tom encorajador)",
        "competency": "isolar_incognita_adicao",
        "evidence": [
            make_evidence(EvidenceType.HELP_REQUESTED, "isolar_incognita_adicao"),
        ],
        "expected": ActionType.EXPLAIN,
    },
    {
        "name": "Misterio: erro, erro, ajuda -> HELP_REQUESTED priority",
        "competency": "isolar_incognita_adicao",
        "evidence": [
            make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.HELP_REQUESTED, "isolar_incognita_adicao"),
        ],
        "expected": ActionType.EXPLAIN,
    },
    {
        "name": "RECOVER_BASE com KnowledgeGraph -> retorna pre-requisito",
        "competency": "isolar_incognita_multiplicacao",
        "evidence": [
            make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_multiplicacao"),
            make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_multiplicacao"),
            make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_multiplicacao"),
        ],
        "expected": ActionType.RECOVER_BASE,
        "expected_target": "isolar_incognita_adicao",
        "use_kg": True,
    },
    {
        "name": "ADVANCE com KnowledgeGraph -> avanca para proximo",
        "competency": "isolar_incognita_adicao",
        "evidence": [
            make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao"),
        ],
        "expected": ActionType.ADVANCE,
        "use_kg": True,
    },
    {
        "name": "Misterio: acerto, erro, acerto -> PROBE (nao bate threshold)",
        "competency": "isolar_incognita_adicao",
        "evidence": [
            make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.WRONG_ANSWER, "isolar_incognita_adicao"),
            make_evidence(EvidenceType.CORRECT_ANSWER, "isolar_incognita_adicao"),
        ],
        "expected": ActionType.PROBE,
    },
    {
        "name": "5 sondas aplicadas sem 3 consecutivos -> EXERCISE",
        "competency": "isolar_incognita_adicao",
        "evidence": [
            Evidence(
                id=str(uuid4()), session_id="bench",
                type=(EvidenceType.CORRECT_ANSWER if i % 2 == 0 else EvidenceType.WRONG_ANSWER),
                competency="isolar_incognita_adicao",
                timestamp=datetime.now(), raw_data={},
                probe_id=f"probe_{i}",
            )
            for i in range(5)
        ],
        "expected": ActionType.EXERCISE,
    },
]


def build_kg() -> KnowledgeGraphRepository:
    kg = KnowledgeGraphRepository()
    kg._competencies = {
        "isolar_incognita_adicao": {
            "id": "isolar_incognita_adicao",
            "prerequisites": [],
        },
        "isolar_incognita_multiplicacao": {
            "id": "isolar_incognita_multiplicacao",
            "prerequisites": ["isolar_incognita_adicao"],
        },
    }
    return kg


def run_benchmark():
    print("=" * 60)
    print("  Benchmark do Motor Pedagógico")
    print("=" * 60)
    print()

    total = len(SCENARIOS)
    passed = 0
    failed = 0

    for i, scenario in enumerate(SCENARIOS, 1):
        kg = build_kg() if scenario.get("use_kg") else None
        if kg and scenario.get("expected_target"):
            planner = RuleBasedPlanner(knowledge_graph=kg, max_probes_per_competency=5)
        else:
            planner = RuleBasedPlanner(
                knowledge_graph=kg,
                max_probes_per_competency=scenario.get("expected") != ActionType.EXERCISE or 5,
            )

        evidence_list = scenario["evidence"]
        learner = LearningContext(
            session_id="bench",
            current_competency=scenario["competency"],
            evidence_window=evidence_list,
        )
        ctx = PedagogicalContext(student=learner, recent_evidence=evidence_list)
        action = planner.decide(ctx)

        action_ok = action.type == scenario["expected"]
        target_ok = True
        if "expected_target" in scenario:
            target_ok = action.target_competency == scenario["expected_target"]

        if action_ok and target_ok:
            print(f"  [{i}/{total}] PASS - {scenario['name']}")
            print(f"         Ação: {action.type.value}")
            if "expected_target" in scenario:
                print(f"         Alvo: {action.target_competency}")
            passed += 1
        else:
            print(f"  [{i}/{total}] FAIL - {scenario['name']}")
            print(f"         Esperado: {scenario['expected'].value}", end="")
            if "expected_target" in scenario:
                print(f" / alvo: {scenario['expected_target']}", end="")
            print()
            print(f"         Obtido:   {action.type.value}", end="")
            if "expected_target" in scenario:
                print(f" / alvo: {action.target_competency}", end="")
            print()
            failed += 1

    print()
    print("=" * 60)
    accuracy = (passed / total) * 100
    print(f"  Resultado: {passed}/{total} passaram ({accuracy:.0f}%)")
    if failed > 0:
        print(f"  Falhas: {failed}")
    else:
        print("  Todas as decisões estão corretas!")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
