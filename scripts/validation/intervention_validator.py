from datetime import datetime
from uuid import uuid4

from .registry import ValidationRegistry
from .scenarios import INTERVENTION_SCENARIOS, build_pedagogical_engine_for_test


COMPETENCY = "isolar_incognita_adicao"


def _make_evidence(raw: dict, session_id: str):
    from src.pedagogy.models.evidence import Evidence, EvidenceType
    return Evidence(
        id=str(uuid4()),
        session_id=session_id,
        type=EvidenceType(raw["type"]),
        competency=COMPETENCY,
        timestamp=datetime.now(),
        raw_data=raw,
        probe_id=raw.get("probe_id"),
    )


def _get_final_action(engine, session_id: str, user_input: str):
    rt = engine._runtime
    ctx = rt._build_context(session_id, competency=COMPETENCY)
    action = rt._planner.decide(ctx)

    if rt._is_probe_action(action) and action.target_competency:
        evidence = rt._extractor.extract(user_input, ctx, action)
        if evidence:
            rt._event_store.append(session_id, evidence)
            ctx.recent_evidence.append(evidence)
            ctx.student.evidence_window.append(evidence)
            action = rt._planner.decide(ctx)

    return action.type.value


def run(verbose=True):
    passed = 0
    total = len(INTERVENTION_SCENARIOS)

    for scenario in INTERVENTION_SCENARIOS:
        engine, es = build_pedagogical_engine_for_test()
        session_id = f"test_{uuid4().hex[:12]}"

        for ev_dict in scenario.preload_evidence:
            ev = _make_evidence(ev_dict, session_id)
            engine._runtime._event_store.append(session_id, ev)

        actual = _get_final_action(engine, session_id, scenario.user_input)
        expected = scenario.expected_action_type

        if actual == expected:
            print(f"  PASS: {scenario.name}")
            passed += 1
        else:
            print(f"  FAIL: {scenario.name} (expected={expected}, actual={actual})")

    return passed, total


ValidationRegistry.register("Intervention Validation", run)
