import sys
from pathlib import Path

from .registry import ValidationRegistry


def run(verbose=True):
    root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(root))

    passed = 0
    total = 0

    pd_fields = ['action', 'target_competency', 'probe_id', 'params', 'reasoning']
    total += len(pd_fields)
    try:
        from src.learning.domain import PedagogicalDecision
        _pd_fields = PedagogicalDecision.__dataclass_fields__
        for f in pd_fields:
            try:
                ok = f in _pd_fields
                if ok:
                    passed += 1
                if verbose:
                    print(f"{'[PASS]' if ok else '[FAIL]'} PedagogicalDecision.{f}")
            except Exception:
                if verbose:
                    print(f"[FAIL] PedagogicalDecision.{f}")
    except ImportError as e:
        for f in pd_fields:
            if verbose:
                print(f"[FAIL] PedagogicalDecision.{f} (import error: {e})")

    at_values = ['PROBE', 'EXPLAIN', 'ANALOGY', 'RECOVER_BASE', 'ADVANCE', 'EXERCISE', 'EXAMPLE', 'FALLBACK']
    total += len(at_values)
    try:
        from src.learning.domain import ActionType
        for v in at_values:
            try:
                ok = hasattr(ActionType, v)
                if ok:
                    passed += 1
                if verbose:
                    print(f"{'[PASS]' if ok else '[FAIL]'} ActionType.{v}")
            except Exception:
                if verbose:
                    print(f"[FAIL] ActionType.{v}")
    except ImportError as e:
        for v in at_values:
            if verbose:
                print(f"[FAIL] ActionType.{v} (import error: {e})")

    er_fields = ['type', 'evidence']
    total += len(er_fields)
    try:
        from src.learning.executor.strategy_executor import ExecutionResult
        _er_fields = ExecutionResult.__dataclass_fields__
        for f in er_fields:
            try:
                ok = f in _er_fields
                if ok:
                    passed += 1
                if verbose:
                    print(f"{'[PASS]' if ok else '[FAIL]'} ExecutionResult.{f}")
            except Exception:
                if verbose:
                    print(f"[FAIL] ExecutionResult.{f}")
    except ImportError as e:
        for f in er_fields:
            if verbose:
                print(f"[FAIL] ExecutionResult.{f} (import error: {e})")

    pc_fields = ['competency_id', 'last_evidence', 'evidence_count', 'recent_results']
    total += len(pc_fields)
    try:
        from src.pedagogy.models.context import PedagogicalContext
        _pc_fields = PedagogicalContext.__dataclass_fields__
        for f in pc_fields:
            try:
                ok = f in _pc_fields
                if ok:
                    passed += 1
                if verbose:
                    print(f"{'[PASS]' if ok else '[FAIL]'} PedagogicalContext.{f}")
            except Exception:
                if verbose:
                    print(f"[FAIL] PedagogicalContext.{f}")
    except ImportError as e:
        for f in pc_fields:
            if verbose:
                print(f"[FAIL] PedagogicalContext.{f} (import error: {e})")

    es_methods = ['append', 'get_history']
    total += len(es_methods)
    try:
        from src.pedagogy.memory.event_store import EventStore
        for m in es_methods:
            try:
                ok = hasattr(EventStore, m) and callable(getattr(EventStore, m))
                if ok:
                    passed += 1
                if verbose:
                    print(f"{'[PASS]' if ok else '[FAIL]'} EventStore.{m}")
            except Exception:
                if verbose:
                    print(f"[FAIL] EventStore.{m}")
    except ImportError as e:
        for m in es_methods:
            if verbose:
                print(f"[FAIL] EventStore.{m} (import error: {e})")

    total += 1
    try:
        from src.learning.engine.pedagogical_engine import PedagogicalEngine
        try:
            ok = hasattr(PedagogicalEngine, 'process') and callable(getattr(PedagogicalEngine, 'process'))
            if ok:
                passed += 1
            if verbose:
                print(f"{'[PASS]' if ok else '[FAIL]'} PedagogicalEngine.process")
        except Exception:
            if verbose:
                print(f"[FAIL] PedagogicalEngine.process")
    except ImportError as e:
        if verbose:
            print(f"[FAIL] PedagogicalEngine.process (import error: {e})")

    return (passed, total)


ValidationRegistry.register("Contract Validation", run)
