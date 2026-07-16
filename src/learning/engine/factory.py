from src.pedagogy.memory.event_store import EventStore
from src.pedagogy.planner.rule_based import RuleBasedPlanner
from src.pedagogy.probes.repository import ProbeRepository
from src.pedagogy.probes.evaluator import EvaluatorFactory
from src.pedagogy.composer.instruction_composer import InstructionComposer
from src.pedagogy.extractors.evidence_extractor import EvidenceExtractor
from src.pedagogy.knowledge.graph_repository import KnowledgeGraphRepository
from ..executor.strategy_executor import StrategyExecutor
from ..tutor.llm_tutor import LLMTutor
from ..runtime import PedagogicalRuntime
from .current_pipeline import CurrentPipelineEngine
from .pedagogical_engine import PedagogicalEngine
from .learning_engine import LearningEngine


def create_engine(engine_type: str = "current") -> LearningEngine:
    if engine_type == "current":
        return CurrentPipelineEngine()
    if engine_type == "pedagogy":
        return _build_pedagogical_engine()
    raise ValueError(f"Unknown engine type: {engine_type}. Use 'current' or 'pedagogy'.")


def _build_pedagogical_engine() -> PedagogicalEngine:
    event_store = EventStore(storage_path="data/events/")

    kg = KnowledgeGraphRepository()
    try:
        kg.load("config/competencies.yaml")
    except Exception:
        pass

    probe_repo = ProbeRepository()
    try:
        import yaml
        with open("config/probes.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for p in data.get("probes", []):
            from src.pedagogy.models.probe import Probe
            probe_repo.add(Probe(
                id=p["id"],
                competency=p["competency"],
                difficulty_level=p["difficulty_level"],
                prompt_template=p["prompt_template"],
                expected_response_schema=p["expected_response_schema"],
                evidence_weight=p.get("evidence_weight", 1),
                evaluator_type=p["evaluator_type"],
                evaluator_config=p["evaluator_config"],
            ))
    except Exception:
        pass

    planner = RuleBasedPlanner(
        knowledge_graph=kg,
        probe_ids_by_competency={
            c: kg.get_probes(c) for c in kg.all_competencies()
        } if kg.all_competencies() else {},
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
