from .registry import ValidationRegistry
from .scenarios import PLANNER_SCENARIOS, build_pedagogical_engine_for_test


def run(verbose=True):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

    from src.pedagogy.models.evidence import Evidence, EvidenceType
    from src.pedagogy.models.context import PedagogicalContext, LearningContext
    from src.pedagogy.models.probe import Probe
    from src.pedagogy.probes.repository import ProbeRepository
    from src.pedagogy.knowledge.graph_repository import KnowledgeGraphRepository
    from datetime import datetime
    from uuid import uuid4

    type_map = {
        "wrong_answer": EvidenceType.WRONG_ANSWER,
        "correct_answer": EvidenceType.CORRECT_ANSWER,
        "help_requested": EvidenceType.HELP_REQUESTED,
    }

    passed = 0
    total = len(PLANNER_SCENARIOS)

    for scenario in PLANNER_SCENARIOS:
        try:
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

            engine, es = build_pedagogical_engine_for_test(probe_repo=probe_repo)
            session_id = "planner-test"

            if scenario.expected_target == "isolar_incognita_adicao" and scenario.competency == "isolar_incognita_multiplicacao":
                kg = KnowledgeGraphRepository()
                kg._competencies = {
                    "isolar_incognita_multiplicacao": {
                        "id": "isolar_incognita_multiplicacao",
                        "prerequisites": ["isolar_incognita_adicao"],
                    }
                }
                engine._runtime._planner._knowledge_graph = kg

            competency = scenario.competency or ""
            for cfg in scenario.evidence_config:
                ev = Evidence(
                    id=str(uuid4()),
                    session_id=session_id,
                    type=type_map[cfg["type"]],
                    competency=competency,
                    timestamp=datetime.now(),
                    raw_data={},
                    probe_id=cfg.get("probe_id"),
                )
                es.append(session_id, ev)

            recent = es.get_recent_evidence(session_id, limit=20)
            learner = LearningContext(
                session_id=session_id,
                current_competency=scenario.competency,
                evidence_window=recent,
            )
            context = PedagogicalContext(student=learner, recent_evidence=recent)

            action = engine._runtime._planner.decide(context)
            action_type = action.type.value
            action_target = action.target_competency

            ok = action_type == scenario.expected_action
            if scenario.expected_target:
                ok = ok and (action_target == scenario.expected_target)

            if ok:
                passed += 1
                if verbose:
                    print(f"  [PASS] {scenario.name}")
            else:
                msg = f"  [FAIL] {scenario.name}: expected action={scenario.expected_action}"
                if action_type != scenario.expected_action:
                    msg += f", got action={action_type}"
                if scenario.expected_target and action_target != scenario.expected_target:
                    msg += f", expected target={scenario.expected_target}, got target={action_target}"
                print(msg)

        except Exception as e:
            import traceback
            print(f"  [FAIL] {scenario.name}: {e}")
            traceback.print_exc()

    return (passed, total)


ValidationRegistry.register("Planner Validation", run)
