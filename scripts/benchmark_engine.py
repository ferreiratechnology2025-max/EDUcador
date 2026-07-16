#!/usr/bin/env python3

import sys
import os
from datetime import datetime
from uuid import uuid4
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pedagogy.models.evidence import Evidence, EvidenceType
from src.pedagogy.models.probe import Probe
from src.pedagogy.memory.event_store import EventStore
from src.pedagogy.planner.rule_based import RuleBasedPlanner
from src.pedagogy.probes.repository import ProbeRepository
from src.pedagogy.probes.evaluator import EvaluatorFactory
from src.pedagogy.composer.instruction_composer import InstructionComposer
from src.pedagogy.extractors.evidence_extractor import EvidenceExtractor
from src.learning.runtime import PedagogicalRuntime
from src.learning.executor.strategy_executor import StrategyExecutor
from src.learning.tutor.llm_tutor import LLMTutor
from src.learning.engine import PedagogicalEngine, CurrentPipelineEngine


USER_SCENARIOS = [
    {
        "name": "Resposta correta -> action_type=probe",
        "user_input": "4",
        "competency": "isolar_incognita_adicao",
        "expected_type": "probe",
    },
    {
        "name": "Resposta errada -> action_type=probe (segunda sonda)",
        "user_input": "99",
        "competency": "isolar_incognita_adicao",
        "expected_type": "probe",
    },
    {
        "name": "Sem competencia -> action_type=probe",
        "user_input": "nao sei",
        "competency": None,
        "expected_type": "probe",
    },
]


def benchmark_engine(engine, scenarios) -> float:
    correct = 0
    for s in scenarios:
        try:
            response = engine.process(s["user_input"], f"session_{s['name']}")
            if response.action_type == s["expected_type"]:
                correct += 1
                print(f"  PASS - {s['name']}")
            else:
                print(f"  FAIL - {s['name']}")
                print(f"    Esperado: {s['expected_type']}, Obtido: {response.action_type}")
        except Exception as e:
            print(f"  FAIL - {s['name']} (erro: {e})")
    return correct / len(scenarios)


def build_pedagogical_engine() -> PedagogicalEngine:
    tmpdir = tempfile.mkdtemp()
    event_store = EventStore(storage_path=tmpdir)

    probe_repo = ProbeRepository({
        "p1": Probe(
            id="p1",
            competency="isolar_incognita_adicao",
            difficulty_level=1,
            prompt_template="Resolva: x + 3 = 7",
            expected_response_schema="numeric",
            evidence_weight=1,
            evaluator_type="exact_match",
            evaluator_config={"expected": "4"},
        ),
    })
    planner = RuleBasedPlanner(
        probe_ids_by_competency={"isolar_incognita_adicao": ["p1"]},
    )
    composer = InstructionComposer()
    evaluator_factory = EvaluatorFactory()
    extractor = EvidenceExtractor(probe_repo, evaluator_factory)
    executor = StrategyExecutor(probe_repo, composer)
    tutor = LLMTutor()

    runtime = PedagogicalRuntime(
        extractor=extractor,
        event_store=event_store,
        planner=planner,
        executor=executor,
        tutor=tutor,
    )
    return PedagogicalEngine(runtime)


def main():
    print("=" * 60)
    print("  Benchmark do Engine (End-to-End)")
    print("=" * 60)
    print()

    print("[Engine Pedagogico]")
    ped_engine = build_pedagogical_engine()
    ped_accuracy = benchmark_engine(ped_engine, USER_SCENARIOS)

    print()
    total = len(USER_SCENARIOS)
    ped_passed = int(ped_accuracy * total)

    print("=" * 60)
    print(f"  Engine Pedagogico: {ped_passed}/{total} ({ped_accuracy*100:.0f}%)")
    print("=" * 60)
    return ped_accuracy >= 1.0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
