import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent
scripts = root / "scripts"
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
if str(scripts) not in sys.path:
    sys.path.insert(0, str(scripts))

from typing import List, Tuple
from config.project_state import ProjectGate, GateBlocked
from validation.registry import ValidationRegistry
from validation.manifest import EXPECTED_VALIDATORS


def run_validation_suite(verbose: bool = True, require_gates: bool = False) -> Tuple[List[Tuple[str, int, int]], float]:
    gate_status = ProjectGate.status()

    if require_gates:
        ProjectGate.require_technical_readiness(origin="validate_all")
        ProjectGate.require_hypothesis_validated(origin="validate_all")

    if verbose:
        print(f"{'='*60}")
        print(f"  PR-3 Validation Suite")
        print(f"{'='*60}")
        print(f"  Gates: technical_ready={gate_status['technical_ready']}, "
              f"hypothesis_validated={gate_status['hypothesis_validated']}")
        print(f"  Integrity: {gate_status.get('integrity', 'unknown')}")

    start = time.perf_counter()
    results = ValidationRegistry.run_all(verbose=verbose)
    elapsed = time.perf_counter() - start

    if verbose:
        print(f"\n{'='*60}")
        print(f"  SUMMARY")
        print(f"{'='*60}")
        total_p, total_t = 0, 0
        for name, p, t in results:
            status = "PASS" if p == t else f"FAIL ({t-p} failures)"
            print(f"  {name:45s} {p:3d}/{t:<3d}  {status}")
            total_p += p
            total_t += t
        print(f"\n  {'TOTAL':45s} {total_p:3d}/{total_t:<3d}  ({elapsed:.2f}s)")

    return results, elapsed


def main():
    import argparse
    parser = argparse.ArgumentParser(description="PR-3 Validation Suite")
    parser.add_argument("--require-gates", action="store_true", help="Fail if gates not green")
    parser.add_argument("--select", nargs="+", help="Run only matching validators (substring match)")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    gate_status = ProjectGate.status()
    if args.require_gates:
        try:
            ProjectGate.require_technical_readiness(origin="validate_all")
            ProjectGate.require_hypothesis_validated(origin="validate_all")
        except GateBlocked as e:
            print(f"ERROR: {e}")
            sys.exit(1)

    start = time.perf_counter()

    if args.select:
        results = ValidationRegistry.run_selected(args.select, verbose=True)
    else:
        results, _ = run_validation_suite(verbose=True)

    elapsed = time.perf_counter() - start
    total_p = sum(p for _, p, _ in results)
    total_t = sum(t for _, _, t in results)

    if args.json:
        import json
        report = {
            "gates": gate_status,
            "validators": [{"name": n, "passed": p, "total": t} for n, p, t in results],
            "total_passed": total_p,
            "total_tests": total_t,
            "elapsed_seconds": round(elapsed, 2),
        }
        print(json.dumps(report, indent=2))

    if total_p < total_t:
        print(f"\n{'='*60}")
        print(f"  VALIDATION FAILED: {total_t - total_p} check(s) failed")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  ALL VALIDATIONS PASSED ({total_p}/{total_t}) in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
