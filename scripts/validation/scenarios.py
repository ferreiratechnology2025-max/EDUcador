from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PlannerScenario:
    name: str
    competency: Optional[str]
    evidence_config: List[dict]
    expected_action: str
    expected_target: Optional[str] = None


@dataclass
class InterventionScenario:
    name: str
    preload_evidence: List[dict]
    user_input: str
    expected_action_type: str


PLANNER_SCENARIOS = [
    PlannerScenario(name="Sem competencia ativa -> PROBE", competency=None, evidence_config=[], expected_action="probe"),
    PlannerScenario(name="Primeira interacao com competencia -> PROBE", competency="isolar_incognita_adicao", evidence_config=[], expected_action="probe"),
    PlannerScenario(name="3 erros consecutivos -> RECOVER_BASE", competency="isolar_incognita_adicao", evidence_config=[{"type": "wrong_answer"}] * 3, expected_action="recover_base"),
    PlannerScenario(name="2 erros consecutivos -> PROBE (threshold=3)", competency="isolar_incognita_adicao", evidence_config=[{"type": "wrong_answer"}] * 2, expected_action="probe"),
    PlannerScenario(name="3 acertos consecutivos -> ADVANCE", competency="isolar_incognita_adicao", evidence_config=[{"type": "correct_answer"}] * 3, expected_action="advance"),
    PlannerScenario(name="2 acertos consecutivos -> PROBE (threshold=3)", competency="isolar_incognita_adicao", evidence_config=[{"type": "correct_answer"}] * 2, expected_action="probe"),
    PlannerScenario(name="Pedido de ajuda -> EXPLAIN", competency="isolar_incognita_adicao", evidence_config=[{"type": "help_requested"}], expected_action="explain"),
    PlannerScenario(name="Ultimo HELP_REQUESTED -> EXPLAIN", competency="isolar_incognita_adicao", evidence_config=[{"type": "wrong_answer"}, {"type": "wrong_answer"}, {"type": "help_requested"}], expected_action="explain"),
    PlannerScenario(name="RECOVER_BASE com KnowledgeGraph", competency="isolar_incognita_multiplicacao", evidence_config=[{"type": "wrong_answer"}] * 3, expected_action="recover_base", expected_target="isolar_incognita_adicao"),
    PlannerScenario(name="ADVANCE com KnowledgeGraph", competency="isolar_incognita_adicao", evidence_config=[{"type": "correct_answer"}] * 3, expected_action="advance"),
    PlannerScenario(name="Alternados -> PROBE", competency="isolar_incognita_adicao", evidence_config=[{"type": "correct_answer"}, {"type": "wrong_answer"}, {"type": "correct_answer"}], expected_action="probe"),
    PlannerScenario(name="5 com probe_id -> EXERCISE", competency="isolar_incognita_adicao", evidence_config=[{"type": "correct_answer" if i % 2 == 0 else "wrong_answer", "probe_id": f"p{i}"} for i in range(5)], expected_action="exercise"),
]

import tempfile
from pathlib import Path


def build_pedagogical_engine_for_test(probe_repo=None, event_store_path=None):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from src.pedagogy.models.probe import Probe
    from src.pedagogy.probes.repository import ProbeRepository
    from src.pedagogy.memory.event_store import EventStore
    from src.pedagogy.planner.rule_based import RuleBasedPlanner
    from src.pedagogy.composer.instruction_composer import InstructionComposer
    from src.pedagogy.extractors.evidence_extractor import EvidenceExtractor
    from src.pedagogy.probes.evaluator import EvaluatorFactory
    from src.learning.executor.strategy_executor import StrategyExecutor
    from src.learning.tutor.llm_tutor import LLMTutor
    from src.learning.runtime import PedagogicalRuntime
    from src.learning.engine.pedagogical_engine import PedagogicalEngine
    if probe_repo is None:
        probe_repo = ProbeRepository({
            "p1": Probe(
                id="p1", competency="isolar_incognita_adicao",
                difficulty_level=1, prompt_template="Resolva: x + 3 = 7",
                expected_response_schema="numeric", evidence_weight=1,
                evaluator_type="exact_match", evaluator_config={"expected": "4"},
            ),
        })
    es = EventStore(storage_path=event_store_path or tempfile.mkdtemp())
    planner = RuleBasedPlanner(probe_ids_by_competency={"isolar_incognita_adicao": ["p1"]})
    comp = InstructionComposer()
    ef = EvaluatorFactory()
    ext = EvidenceExtractor(probe_repo, ef)
    exec_ = StrategyExecutor(probe_repo, comp)
    tutor = LLMTutor()
    rt = PedagogicalRuntime(extractor=ext, event_store=es, planner=planner, executor=exec_, tutor=tutor)
    return PedagogicalEngine(rt), es


def build_current_engine_for_test():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from src.learning.engine.current_pipeline import CurrentPipelineEngine
    return CurrentPipelineEngine()


INTERVENTION_SCENARIOS = [
    InterventionScenario(name="Nenhuma evidencia -> PROBE", preload_evidence=[], user_input="nao sei", expected_action_type="probe"),
    InterventionScenario(name="1 erro -> PROBE", preload_evidence=[{"type": "wrong_answer"}], user_input="4", expected_action_type="probe"),
    InterventionScenario(name="2 erros consecutivos -> PROBE", preload_evidence=[{"type": "wrong_answer"}, {"type": "wrong_answer"}], user_input="4", expected_action_type="probe"),
    InterventionScenario(name="3 erros consecutivos -> RECOVER_BASE", preload_evidence=[{"type": "wrong_answer"}, {"type": "wrong_answer"}, {"type": "wrong_answer"}], user_input="nao sei", expected_action_type="recover_base"),
    InterventionScenario(name="3 acertos consecutivos -> ADVANCE", preload_evidence=[{"type": "correct_answer"}, {"type": "correct_answer"}, {"type": "correct_answer"}], user_input="nao sei", expected_action_type="advance"),
    InterventionScenario(name="Pedido de ajuda -> EXPLAIN", preload_evidence=[{"type": "help_requested"}], user_input="me ajuda", expected_action_type="explain"),
    InterventionScenario(name="Erro em sonda -> RECOVER_BASE", preload_evidence=[{"type": "wrong_answer"}, {"type": "wrong_answer"}], user_input="99", expected_action_type="recover_base"),
    InterventionScenario(name="Acerto em sonda -> PROBE (nova)", preload_evidence=[{"type": "correct_answer"}], user_input="4", expected_action_type="probe"),
]
