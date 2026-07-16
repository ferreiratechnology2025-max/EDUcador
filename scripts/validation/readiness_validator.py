import json
from pathlib import Path

from config.project_state import GateBlocked, ProjectGate
from .registry import ValidationRegistry


def run(verbose=True):
    passed = 0
    total = 0

    s = ProjectGate.status()

    total += 1
    tr = s.get("technical_ready")
    if isinstance(tr, bool):
        if verbose:
            print(f"  [PASS] technical_ready = {tr}")
        passed += 1
    elif verbose:
        print(f"  [WARN] technical_ready should be bool, got {type(tr).__name__} = {tr}")

    total += 1
    hv = s.get("hypothesis_validated")
    if isinstance(hv, bool):
        if verbose:
            print(f"  [PASS] hypothesis_validated = {hv}")
        passed += 1
    elif verbose:
        print(f"  [WARN] hypothesis_validated should be bool, got {type(hv).__name__} = {hv}")

    total += 1
    gate_file = Path(s.get("gate_state_file", "config/.gate_state.json"))
    file_exists = gate_file.exists()
    if file_exists:
        if verbose:
            print(f"  [PASS] .gate_state.json exists at {gate_file}")
        passed += 1
    elif verbose:
        print(f"  [WARN] .gate_state.json not found at {gate_file}")

    total += 1
    schema_ok = False
    data = None
    if file_exists:
        try:
            with open(gate_file) as f:
                data = json.load(f)
            required_keys = [
                "hypothesis_validated", "technical_ready",
                "hypothesis_validation_date", "hypothesis_evidence_path",
                "hypothesis_evidence_hash",
                "technical_ready_date", "technical_ready_evidence",
                "technical_ready_hash", "last_updated",
            ]
            missing = [k for k in required_keys if k not in data]
            if not missing:
                schema_ok = True
                if verbose:
                    print(f"  [PASS] .gate_state.json schema valid ({len(required_keys)} keys)")
                passed += 1
            elif verbose:
                print(f"  [WARN] .gate_state.json missing keys: {missing}")
        except (json.JSONDecodeError, IOError) as e:
            if verbose:
                print(f"  [WARN] .gate_state.json is not valid JSON: {e}")
    elif verbose:
        print(f"  [WARN] Cannot validate schema: .gate_state.json not found")

    total += 1
    hash_ok = True
    if file_exists and schema_ok and data:
        for evidence_key, hash_key in [
            ("hypothesis_evidence_path", "hypothesis_evidence_hash"),
            ("technical_ready_evidence", "technical_ready_hash"),
        ]:
            ev_path = data.get(evidence_key)
            stored_hash = data.get(hash_key)
            if ev_path and stored_hash:
                actual_hash = ProjectGate._compute_hash(ev_path)
                if actual_hash != stored_hash:
                    hash_ok = False
                    if verbose:
                        print(f"  [WARN] Hash mismatch for {evidence_key}: "
                              f"stored={stored_hash}, actual={actual_hash}")
                    break
        if hash_ok:
            if verbose:
                print(f"  [PASS] Gate state hashes verified")
            passed += 1
    elif verbose:
        print(f"  [WARN] Cannot verify hashes: .gate_state.json unavailable")

    total += 1
    try:
        ProjectGate.require_technical_readiness("ReadinessValidation")
        if verbose:
            print(f"  [PASS] require_technical_readiness() passed")
        passed += 1
    except GateBlocked as e:
        if verbose:
            print(f"  [WARN] Gate 'technical_ready' not green: the motor must be "
                  f"technically ready before proceeding")

    total += 1
    try:
        ProjectGate.require_hypothesis_validated("ReadinessValidation")
        if verbose:
            print(f"  [PASS] require_hypothesis_validated() passed")
        passed += 1
    except GateBlocked as e:
        if verbose:
            print(f"  [WARN] Gate 'hypothesis_validated' not green: "
                  f"the pedagogical hypothesis must be validated with real users")

    return (passed, total)


ValidationRegistry.register("Readiness Validation", run)
