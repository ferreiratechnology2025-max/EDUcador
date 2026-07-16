# PR-3: Validation Framework — Execution Plan

> **Execution strategy:** Phase 1 (inline: ProjectGate, manifest, registry) -> Phase 2 (parallel subagents: 6 validators) -> Phase 3 (inline: orchestrator, regression suite, verification)

**Goal:** Build validation framework with 6 validators, persisted ProjectGate (two gates, symmetric validation, SHA-256 integrity hashes, CI-aware override), explicit module discovery with manifest verification.

**Architecture:** `config/project_state.py` (ProjectGate, persisted `.gate_state.json` with hashes, `status()` never raises, `reviewer_approved` as process protection). `scripts/validation/` (6 validators + ValidationRegistry + InvariantRegistry + manifest.py). Registry uses pkgutil + manifest check raises RuntimeError on mismatch.

**Tech Stack:** Python 3.10+, pytest, ast, pkgutil, hashlib, json, os.environ

**Hypothesis Status:** Central hypothesis NOT validated. Investment is acknowledged bet.

---

## Phase 1: Inline — Interdependent Components

### Task 1: ProjectGate — persisted two-gate system

**Files:** `config/__init__.py`, `config/project_state.py`, `config/.gate_state.json`

- [ ] **Create `config/__init__.py`** (empty)

- [ ] **Create `config/.gate_state.json`** (initial state, versioned, NOT in .gitignore):
```json
{"hypothesis_validated": false, "technical_ready": false, "hypothesis_validation_date": null, "hypothesis_evidence_path": null, "hypothesis_evidence_hash": null, "technical_ready_date": null, "technical_ready_evidence": null, "technical_ready_hash": null, "last_updated": null}
```

- [ ] **Create `config/project_state.py`** with:

  **Types:**
  - `class GateBlocked(Exception)` 
  - `@dataclass GateStatus` with all fields + `integrity: str = "unknown"`

  **State I/O:**
  - `_compute_hash(file_path: str) -> str` — SHA-256 hex digest, returns None if file missing
  - `_load_state()` — reads `.gate_state.json`, verifies hashes for both evidence paths, raises GateBlocked on mismatch
  - `_save_state()` — writes `.gate_state.json` with computed hashes of evidence files

  **Technical Readiness Gate:**
  - `require_technical_readiness(feature_name: str)` — raises GateBlocked
  - `mark_technical_ready(evidence_path: str)` — validates readiness report (all_gates_passed, intervention_success_rate >= 1.0, planner_determinism_rate >= 1.0)
  - `_load_and_validate_readiness_report(path: str) -> dict`
  - `reset_technical_readiness()`

  **Hypothesis Validation Gate:**
  - `require_hypothesis_validated(feature_name: str, override: bool = False)` — CI-aware override
  - `mark_hypothesis_validated(evidence_path: str, reviewer_approved: bool = False)` — validates benchmark report (tier1 >= 0.95, tier2 >= 0.90, tier3 > baseline). `reviewer_approved` documented as PROCESS protection, not technical.
  - `_load_and_validate_benchmark_report(path: str) -> dict`

  **Status (NEVER raises):**
  - `status() -> dict` — returns dict with all fields + `integrity` key. Catches all exceptions internally and sets `integrity: "broken: ..."` or `integrity: "error: ..."`. Never raises.

- [ ] **Test:** `python -c "from config.project_state import ProjectGate, GateBlocked; s=ProjectGate.status(); print(f'hypothesis={s["hypothesis_validated"]}, ready={s["technical_ready"]}, integrity={s["integrity"]}')"`

- [ ] **Test status with tampered state:** `python -c "import json; json.dump({'hypothesis_validated': True, 'technical_ready': True}, open('config/.gate_state.json', 'w')); from config.project_state import ProjectGate; s=ProjectGate.status(); print(f'integrity={s["integrity"]}'); assert 'broken' in s['integrity'] or 'error' in s['integrity'], 'FAIL: tampered state not detected'"`

- [ ] **Commit:** `git add config/ && git commit -m "feat: ProjectGate with symmetric validation, integrity hashes, process protections"`

---

### Task 2: Manifest + Registry + Invariants + Scenarios

**Files:** `scripts/validation/__init__.py`, `manifest.py`, `registry.py`, `invariants.py`, `scenarios.py`

- [ ] **Create `__init__.py`** (empty)

- [ ] **Create `manifest.py`:**
```python
EXPECTED_VALIDATORS = [
    "Contract Validation", "Planner Validation", "Intervention Validation",
    "Architecture Validation", "Dependency Validation", "Readiness Validation",
]
```

- [ ] **Create `registry.py`:** ValidationRegistry with pkgutil discover + manifest verification. `run_all()` checks registered names match EXPECTED_VALIDATORS exactly; raises RuntimeError with details of missing/extra validators.

- [ ] **Create `invariants.py`:** InvariantRegistry with register/run_all returning list of InvariantResult.

- [ ] **Create `scenarios.py`:** 12 PlannerScenario + 8 InterventionScenario.

- [ ] **Test:** `python -c "import sys; sys.path.insert(0, 'scripts'); from validation.manifest import EXPECTED_VALIDATORS; print(f'Manifest: {len(EXPECTED_VALIDATORS)} validators')"`

- [ ] **Commit:** `git add scripts/validation/ && git commit -m "feat: scaffold with manifest, registry, invariants, scenarios"`

---

### Task 3: ExecutionResult — document Executor -> EventStore contract

**File:** `src/learning/executor/strategy_executor.py`

- [ ] Add `evidence: Optional[Any] = None` to ExecutionResult (typed as Any). Add comment documenting the contract.

- [ ] Verify: `python -c "import ast; t=ast.parse(open('src/learning/executor/strategy_executor.py').read()); imps=[n.module for n in ast.walk(t) if isinstance(n, ast.ImportFrom) and n.module]; assert all('event_store' not in i for i in imps if i)"`

- [ ] **Commit:** `git add src/learning/executor/strategy_executor.py && git commit -m "feat: evidence field in ExecutionResult"`

---

## Phase 2: Parallel Subagents — 6 Validators

### Task 4: Contract Validation (subagent)

**File:** `scripts/validation/contract_validator.py`
**Modify:** `scripts/validation/scenarios.py` — add engine builder helpers

- [ ] Add `build_pedagogical_engine_for_test()` and `build_current_engine_for_test()` to scenarios.py

- [ ] Write `contract_validator.py` — self-registers. 12 tests (6 x 2 engines): implements LearningEngine, returns TutorResponse, required fields, no exception, get_session_info returns dict with session_id.

- [ ] Run: `python scripts/validation/contract_validator.py`

- [ ] **Commit:** `git add scripts/validation/contract_validator.py && git commit -m "feat: contract validation"`

---

### Task 5: Planner Validation — 100% determinism (subagent)

**File:** `scripts/validation/planner_validator.py`

- [ ] Write `planner_validator.py` — self-registers. 5 scenarios x 100 executions. Verifies (action, target, probe_id) identical.

- [ ] Run: `python scripts/validation/planner_validator.py`

- [ ] **Commit:** `git add scripts/validation/planner_validator.py && git commit -m "feat: planner validation"`

---

### Task 6: Intervention Validation — 8 scenarios (subagent)

**File:** `scripts/validation/intervention_validator.py`

- [ ] Write `intervention_validator.py` — self-registers. 8 scenarios. Pre-loads evidence in EventStore, calls engine.process(), verifies action_type.

- [ ] Run: `python scripts/validation/intervention_validator.py`

- [ ] **Commit:** `git add scripts/validation/intervention_validator.py && git commit -m "feat: intervention validation"`

---

### Task 7: Architecture Validation (subagent)

**File:** `scripts/validation/architecture_validator.py`

- [ ] Write `architecture_validator.py` — self-registers. 6 ast rules: domain/tutor, planner/executor, executor/event_store, presentation/planner, planner/ollama, engine/streamlit.

- [ ] Run: `python scripts/validation/architecture_validator.py`

- [ ] **Commit:** `git add scripts/validation/architecture_validator.py && git commit -m "feat: architecture validation"`

---

### Task 8: Dependency Validation (subagent)

**File:** `scripts/validation/dependency_validator.py`

- [ ] Write `dependency_validator.py` — self-registers. 3 rules: runtime imports dependencies, pedagogical_engine depends on runtime not executor, current_pipeline avoids pedagogy.

- [ ] Run: `python scripts/validation/dependency_validator.py`

- [ ] **Commit:** `git add scripts/validation/dependency_validator.py && git commit -m "feat: dependency validation"`

---

### Task 9: Readiness Validation — generates JSON report, triggers gate (subagent)

**File:** `scripts/validation/readiness_validator.py`

- [ ] Write `readiness_validator.py` — self-registers. Discovers all validators, runs each (excluding self), generates `scripts/validation/.readiness_report.json` with:
  - `all_gates_passed`, `intervention_success_rate`, `planner_determinism_rate`, `failures`, `timestamp`, `validator_results`
  - If all pass, calls `ProjectGate.mark_technical_ready(evidence_path)` with the report path

- [ ] Run: `python scripts/validation/readiness_validator.py`

- [ ] Verify: `python -c "from config.project_state import ProjectGate; s=ProjectGate.status(); print(f'ready={s["technical_ready"]}, integrity={s["integrity"]}')"`

- [ ] **Commit:** `git add scripts/validation/readiness_validator.py && git commit -m "feat: readiness validation with JSON report and gate trigger"`

---

## Phase 3: Inline — Integration

### Task 10: Orchestrator

**File:** `scripts/run_validation.py`

- [ ] Write `run_validation.py` — uses ValidationRegistry.run_all() or run_selected(names). Default runs all. Flags match validator names via substring.

- [ ] Test: `python scripts/run_validation.py && python scripts/run_validation.py --contract --planner`

- [ ] **Commit:** `git add scripts/run_validation.py && git commit -m "feat: validation orchestrator"`

---

### Task 11: Regression Suite

**File:** `scripts/regression_suite.py`

- [ ] Write `regression_suite.py` — runs pytest (offline or --all), then ValidationRegistry.run_all(), then (if all pass and no --no-mark) calls `ProjectGate.mark_technical_ready()` with readiness report path.

- [ ] Test: `python scripts/regression_suite.py --skip-tests`

- [ ] Verify: `python -c "from config.project_state import ProjectGate; s=ProjectGate.status(); print(f'ready={s["technical_ready"]}, hypothesis={s["hypothesis_validated"]}, integrity={s["integrity"]}')"`

- [ ] **Commit:** `git add scripts/regression_suite.py && git commit -m "feat: regression suite"`

---

### Task 12: Final Verification

- [ ] **Run existing offline tests:** `python tests/run_all_tests.py`
- [ ] **Run full validation:** `python scripts/run_validation.py`
- [ ] **Run regression:** `python scripts/regression_suite.py --skip-tests`

- [ ] **Verify chain:**

```python
python -c "
from config.project_state import ProjectGate, GateBlocked

# 1. Status never raises
s = ProjectGate.status()
print(f'1. Status OK: integrity={s["integrity"]}, ready={s["technical_ready"]}')

# 2. Technical readiness gate blocks when not ready (after reset)
ProjectGate.reset_technical_readiness()
try:
    ProjectGate.require_technical_readiness('test')
    print('3. FAIL: gate should block')
except GateBlocked as e:
    print(f'3. Gate blocks: {str(e)[:50]}...')

# 3. Hypothesis gate blocks when not validated
try:
    ProjectGate.require_hypothesis_validated('test')
    print('4. FAIL: gate should block')
except GateBlocked as e:
    print(f'4. Gate blocks: {str(e)[:50]}...')

# 4. Re-run readiness to restore state
print('5. Re-running readiness...')
"
python scripts/validation/readiness_validator.py
```

- [ ] **Final commit:** `git add -A && git commit -m "chore: final integration — all validations pass, gates operational"`

---

## Trust Chain Summary

```
   Readiness Validator (runs 5 validators)
   ├── Generates .readiness_report.json (all_gates_passed, rates)
   │
   ▼
   ProjectGate.mark_technical_ready(report_path)
   ├── Validates report structure + minimum thresholds
   ├── Sets technical_ready = true
   ├── Stores SHA-256(report) as technical_ready_hash
   └── Persists to .gate_state.json
       │
       ▼
   require_technical_readiness(feature)
   ├── Loads .gate_state.json
   ├── Verifies SHA-256(evidence) == stored hash  ← tamper detection
   └── Blocks if not ready
       │
       ▼   (future: benchmark with real users)
   mark_hypothesis_validated(report, reviewer_approved=True)
   ├── Validates tier1 >= 95%, tier2 >= 90%, tier3 > baseline
   ├── Sets hypothesis_validated = true
   ├── Stores SHA-256(report) as hypothesis_evidence_hash
   └── Persists to .gate_state.json
       │
       ▼
   require_hypothesis_validated(feature, override=False)
   ├── Loads state, verifies hash
   ├── override=True blocked in CI
   └── Blocks if not validated
```

**Properties:**
- `status()` never raises — always returns dict with `integrity` field
- Tampering detected via SHA-256 hash mismatch on load
- CI cannot bypass hypothesis gate (override blocked when CI=true)
- `reviewer_approved` is explicit process protection (future: Git API integration)
