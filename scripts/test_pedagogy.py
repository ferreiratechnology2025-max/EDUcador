#!/usr/bin/env python3

import sys
import os
from datetime import datetime
from uuid import uuid4
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pedagogy.models.evidence import Evidence, EvidenceType
from src.pedagogy.models.probe import Probe
from src.pedagogy.models.context import PedagogicalContext, LearningContext
from src.pedagogy.models.action import PedagogicalAction, ActionType as PedagogyActionType
from src.pedagogy.memory.event_store import EventStore
from src.pedagogy.planner.rule_based import RuleBasedPlanner
from src.pedagogy.probes.repository import ProbeRepository
from src.pedagogy.probes.evaluator import EvaluatorFactory
from src.pedagogy.composer.instruction_composer import InstructionComposer
from src.pedagogy.runtime import PedagogicalRuntime as LegacyRuntime
from src.pedagogy.knowledge.graph_repository import KnowledgeGraphRepository
from src.pedagogy.extractors.evidence_extractor import EvidenceExtractor

from src.learning.domain import PedagogicalDecision, ActionType
from src.learning.presentation import TutorResponse
from src.learning.executor import StrategyExecutor, ExecutionResult
from src.learning.tutor import LLMTutor
from src.learning.inspector import EngineInspector
from src.learning.runtime import PedagogicalRuntime
from src.learning.engine import LearningEngine, CurrentPipelineEngine, PedagogicalEngine


def test_evidence_creation():
    print("1. Criando evidencias...")
    e1 = Evidence(
        id=str(uuid4()), session_id="s_teste",
        type=EvidenceType.CORRECT_ANSWER, competency="isolar_incognita_adicao",
        timestamp=datetime.now(), raw_data={"resposta": "4"}, probe_id="p1",
    )
    e2 = Evidence(
        id=str(uuid4()), session_id="s_teste",
        type=EvidenceType.WRONG_ANSWER, competency="isolar_incognita_adicao",
        timestamp=datetime.now(), raw_data={"resposta": "10"}, probe_id="p2",
    )
    assert e1.type == EvidenceType.CORRECT_ANSWER
    assert e2.type == EvidenceType.WRONG_ANSWER
    print("   [OK] Evidencias criadas com sucesso")


def test_event_store():
    print("2. Testando EventStore...")
    with tempfile.TemporaryDirectory() as tmpdir:
        store = EventStore(storage_path=tmpdir)
        e1 = Evidence(id=str(uuid4()), session_id="s_es", type=EvidenceType.CORRECT_ANSWER,
                       competency="c1", timestamp=datetime.now(), raw_data={})
        e2 = Evidence(id=str(uuid4()), session_id="s_es", type=EvidenceType.WRONG_ANSWER,
                       competency="c1", timestamp=datetime.now(), raw_data={})
        store.append("s_es", e1)
        store.append("s_es", e2)
        assert len(store.get_evidence_by_session("s_es")) == 2
        assert len(store.get_recent_evidence("s_es", limit=1)) == 1
        store.clear_session("s_es")
        assert len(store.get_evidence_by_session("s_es")) == 0
    print("   [OK] EventStore funcional")


def test_planner_rules():
    print("3. Testando Planner baseado em regras...")
    planner = RuleBasedPlanner()

    learner = LearningContext(session_id="t", current_competency="isolar_incognita_adicao")
    errors_3 = [Evidence(id=str(uuid4()), session_id="t", type=EvidenceType.WRONG_ANSWER,
                          competency="c", timestamp=datetime.now(), raw_data={}) for _ in range(3)]
    ctx = PedagogicalContext(student=learner, recent_evidence=errors_3)
    assert planner.decide(ctx).type == PedagogyActionType.RECOVER_BASE
    print("   [OK] Regra de recuperacao (3 erros)")

    ok_3 = [Evidence(id=str(uuid4()), session_id="t", type=EvidenceType.CORRECT_ANSWER,
                      competency="c", timestamp=datetime.now(), raw_data={}) for _ in range(3)]
    ctx2 = PedagogicalContext(student=learner, recent_evidence=ok_3)
    assert planner.decide(ctx2).type == PedagogyActionType.ADVANCE
    print("   [OK] Regra de avanco (3 acertos)")

    ctx3 = PedagogicalContext(student=learner, recent_evidence=[])
    assert planner.decide(ctx3).type == PedagogyActionType.PROBE
    print("   [OK] Regra de primeira interacao")

    ajuda = [Evidence(id=str(uuid4()), session_id="t", type=EvidenceType.HELP_REQUESTED,
                       competency="c", timestamp=datetime.now(), raw_data={})]
    ctx4 = PedagogicalContext(student=learner, recent_evidence=ajuda)
    assert planner.decide(ctx4).type == PedagogyActionType.EXPLAIN
    print("   [OK] Regra de pedido de ajuda")

    hypothesis = planner.get_hypothesis(ctx)
    assert hypothesis is not None
    print(f"   [OK] Hipótese gerada: {hypothesis}")


def test_planner_with_knowledge_graph():
    print("3b. Planner com KnowledgeGraph...")
    kg = KnowledgeGraphRepository()
    kg._competencies = {
        "isolar_incognita_multiplicacao": {"id": "isolar_incognita_multiplicacao", "prerequisites": ["isolar_incognita_adicao"]},
    }
    planner = RuleBasedPlanner(max_consecutive_errors_to_recover=2, knowledge_graph=kg)
    learner = LearningContext(session_id="t", current_competency="isolar_incognita_multiplicacao")
    recent = [Evidence(id=str(uuid4()), session_id="t", type=EvidenceType.WRONG_ANSWER,
                        competency="isolar_incognita_multiplicacao", timestamp=datetime.now(), raw_data={}) for _ in range(2)]
    ctx = PedagogicalContext(student=learner, recent_evidence=recent)
    action = planner.decide(ctx)
    assert action.target_competency == "isolar_incognita_adicao"
    print("   [OK] Planner consulta KnowledgeGraph")


def test_evaluator():
    print("4. Testando Evaluators...")
    factory = EvaluatorFactory()
    p = Probe(id="t", competency="c", difficulty_level=1, prompt_template="x+3=7",
              expected_response_schema="numeric", evidence_weight=1,
              evaluator_type="exact_match", evaluator_config={"expected": "4"})
    assert factory.create("exact_match").evaluate("4", p) is True
    assert factory.create("exact_match").evaluate("5", p) is False
    print("   [OK] ExactMatchEvaluator")


def test_probe_repository():
    print("5. Testando ProbeRepository...")
    repo = ProbeRepository({"p1": Probe(id="p1", competency="c", difficulty_level=1, prompt_template="t",
                                         expected_response_schema="n", evidence_weight=1,
                                         evaluator_type="exact_match", evaluator_config={})})
    assert repo.get("p1") is not None
    assert repo.get("x") is None
    print("   [OK] ProbeRepository")


def test_composer():
    print("6. Testando InstructionComposer...")
    composer = InstructionComposer()
    learner = LearningContext(session_id="s", current_competency="c")
    ctx = PedagogicalContext(student=learner)
    action = PedagogicalAction(type=PedagogyActionType.EXPLAIN, target_competency="c",
                                strategy_params={"tone": "encouraging"})
    instruction = composer.compose(action, ctx)
    assert instruction.role == "explicador"
    assert "encorajador" in instruction.content
    print("   [OK] Composer")


def test_evidence_extractor():
    print("7. EvidenceExtractor...")
    repo = ProbeRepository({"p1": Probe(id="p1", competency="c", difficulty_level=1, prompt_template="t",
                                         expected_response_schema="n", evidence_weight=1,
                                         evaluator_type="exact_match", evaluator_config={"expected": "4"})})
    factory = EvaluatorFactory()
    extractor = EvidenceExtractor(repo, factory)
    learner = LearningContext(session_id="s", current_competency="c")
    ctx = PedagogicalContext(student=learner)
    action = PedagogicalAction(type=PedagogyActionType.PROBE, target_competency="c", probe_id="p1")
    ev = extractor.extract("4", ctx, action)
    assert ev is not None and ev.type == EvidenceType.CORRECT_ANSWER
    print("   [OK] EvidenceExtractor")


def test_legacy_runtime():
    print("8. Runtime legado...")
    with tempfile.TemporaryDirectory() as tmpdir:
        store = EventStore(storage_path=tmpdir)
        planner = RuleBasedPlanner(probe_ids_by_competency={"c": ["p1"]})
        repo = ProbeRepository({"p1": Probe(id="p1", competency="c", difficulty_level=1, prompt_template="t",
                                             expected_response_schema="n", evidence_weight=1,
                                             evaluator_type="exact_match", evaluator_config={"expected": "4"})})
        runtime = LegacyRuntime(planner=planner, probe_repo=repo, event_store=store,
                                 composer=InstructionComposer(), evaluator_factory=EvaluatorFactory())
        response = runtime.process(student_input="4", session_id="r", competency="c")
        assert response.instruction is not None
        print(f"   [OK] Acao: {response.action.type.value}")


def test_pedagogical_decision():
    print("9. PedagogicalDecision (fronteira do dominio)...")
    d = PedagogicalDecision(action=ActionType.PROBE, target_competency="c", probe_id="p1")
    assert d.action == ActionType.PROBE
    assert d.target_competency == "c"
    assert d.probe_id == "p1"
    assert not hasattr(d, "message")
    assert not hasattr(d, "reasoning")
    assert not hasattr(d, "hypothesis")
    print("   [OK] PedagogicalDecision sem message/reasoning/hypothesis")


def test_tutor_response():
    print("10. TutorResponse (fronteira da apresentacao)...")
    r = TutorResponse(session_id="s", message="Resolva: x+3=7", action_type="probe", probe_id="p1")
    assert r.message == "Resolva: x+3=7"
    assert r.action_type == "probe"
    print("   [OK] TutorResponse com message e action_type")


def test_strategy_executor():
    print("11. StrategyExecutor...")
    repo = ProbeRepository({"p1": Probe(id="p1", competency="c", difficulty_level=1, prompt_template="Resolva: x+3=7",
                                         expected_response_schema="n", evidence_weight=1,
                                         evaluator_type="exact_match", evaluator_config={"expected": "4"})})
    executor = StrategyExecutor(repo, InstructionComposer())
    decision = PedagogicalDecision(action=ActionType.PROBE, target_competency="c", probe_id="p1")
    learner = LearningContext(session_id="s", current_competency="c")
    ctx = PedagogicalContext(student=learner)
    result = executor.execute(decision, ctx)
    assert result.type == "probe"
    assert result.prompt == "Resolva: x+3=7"
    print("   [OK] StrategyExecutor executa sonda")

    decision2 = PedagogicalDecision(action=ActionType.ADVANCE)
    result2 = executor.execute(decision2, ctx)
    assert result2.type == "advance"
    print("   [OK] StrategyExecutor executa advance")


def test_llm_tutor():
    print("12. LLMTutor...")
    tutor = LLMTutor()
    er = ExecutionResult(type="probe", prompt="Resolva: x+3=7", probe_id="p1")
    response = tutor.generate(er, session_id="s")
    assert response.message == "Resolva: x+3=7"
    assert response.action_type == "probe"
    print("   [OK] LLMTutor gera TutorResponse para probe")

    er2 = ExecutionResult(type="advance", message="Otimo! Avancando.")
    response2 = tutor.generate(er2, session_id="s")
    assert response2.action_type == "advance"
    print("   [OK] LLMTutor gera TutorResponse para advance")


def test_new_runtime():
    print("13. Novo Runtime (orquestrador)...")
    with tempfile.TemporaryDirectory() as tmpdir:
        event_store = EventStore(storage_path=tmpdir)
        probe_repo = ProbeRepository({"p1": Probe(id="p1", competency="c", difficulty_level=1, prompt_template="Resolva: x+3=7",
                                                   expected_response_schema="n", evidence_weight=1,
                                                   evaluator_type="exact_match", evaluator_config={"expected": "4"})})
        planner = RuleBasedPlanner(probe_ids_by_competency={"c": ["p1"]})
        extractor = EvidenceExtractor(probe_repo, EvaluatorFactory())
        executor = StrategyExecutor(probe_repo, InstructionComposer())
        tutor = LLMTutor()
        runtime = PedagogicalRuntime(extractor, event_store, planner, executor, tutor)
        response = runtime.process("4", "nova_r", competency="c")
        assert isinstance(response, TutorResponse)
        assert response.action_type in ("probe", "tutor", "explicador")
        print(f"   [OK] Runtime processou -> action_type={response.action_type}")


def test_pedagogical_engine():
    print("14. PedagogicalEngine wrapper...")
    with tempfile.TemporaryDirectory() as tmpdir:
        event_store = EventStore(storage_path=tmpdir)
        probe_repo = ProbeRepository({"p1": Probe(id="p1", competency="c", difficulty_level=1, prompt_template="t",
                                                   expected_response_schema="n", evidence_weight=1,
                                                   evaluator_type="exact_match", evaluator_config={"expected": "4"})})
        planner = RuleBasedPlanner(probe_ids_by_competency={"c": ["p1"]})
        extractor = EvidenceExtractor(probe_repo, EvaluatorFactory())
        executor = StrategyExecutor(probe_repo, InstructionComposer())
        tutor = LLMTutor()
        runtime = PedagogicalRuntime(extractor, event_store, planner, executor, tutor)
        engine = PedagogicalEngine(runtime)
        response = engine.process("4", "engine_t")
        assert isinstance(response, TutorResponse)
        info = engine.get_session_info("engine_t")
        assert info["engine"] == "pedagogical"
        print(f"   [OK] PedagogicalEngine: action_type={response.action_type}")


def test_engine_inspector():
    print("15. EngineInspector...")
    with tempfile.TemporaryDirectory() as tmpdir:
        store = EventStore(storage_path=tmpdir)
        planner = RuleBasedPlanner()
        inspector = EngineInspector(store, planner)
        e = Evidence(id=str(uuid4()), session_id="si", type=EvidenceType.WRONG_ANSWER,
                      competency="c", timestamp=datetime.now(), raw_data={})
        store.append("si", e)
        evs = inspector.get_session_evidence("si")
        assert len(evs) == 1

        learner = LearningContext(session_id="si", current_competency="c", evidence_window=evs)
        ctx = PedagogicalContext(student=learner, recent_evidence=evs)
        traces = inspector.get_planner_trace(ctx)
        assert len(traces) > 0
        print(f"   [OK] EngineInspector: {traces[0].context_summary}")


def test_current_pipeline_engine():
    print("16. CurrentPipelineEngine...")
    engine = CurrentPipelineEngine()
    info = engine.get_session_info("test")
    assert info["engine"] == "current_pipeline"
    print("   [OK] CurrentPipelineEngine instancia sem erros")


def test_learning_engine_abc():
    print("17. LearningEngine (ABC)...")
    assert hasattr(LearningEngine, "process")
    assert hasattr(LearningEngine, "get_session_info")
    assert issubclass(PedagogicalEngine, LearningEngine)
    assert issubclass(CurrentPipelineEngine, LearningEngine)
    print("   [OK] Ambos os engines implementam LearningEngine")


def test_compose_decision():
    print("18. InstructionComposer.compose_decision...")
    composer = InstructionComposer()
    learner = LearningContext(session_id="s", current_competency="isolar_incognita_adicao")
    ctx = PedagogicalContext(student=learner)
    decision = PedagogicalDecision(action=ActionType.EXPLAIN, target_competency="isolar_incognita_adicao",
                                    strategy_params={"tone": "encouraging"})
    instruction = composer.compose_decision(decision, ctx)
    assert instruction is not None
    assert "encorajador" in instruction.content
    print("   [OK] compose_decision mapeia PedagogicalDecision corretamente")


if __name__ == "__main__":
    print("=" * 60)
    print("  Testes do Motor Pedagogico - Fase 1.6a")
    print("=" * 60)

    test_evidence_creation()
    test_event_store()
    test_planner_rules()
    test_planner_with_knowledge_graph()
    test_evaluator()
    test_probe_repository()
    test_composer()
    test_evidence_extractor()
    test_legacy_runtime()
    test_pedagogical_decision()
    test_tutor_response()
    test_strategy_executor()
    test_llm_tutor()
    test_new_runtime()
    test_pedagogical_engine()
    test_engine_inspector()
    test_current_pipeline_engine()
    test_learning_engine_abc()
    test_compose_decision()

    print("\n" + "=" * 60)
    print("  Todos os testes passaram!")
    print("=" * 60)
