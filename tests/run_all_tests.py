#!/usr/bin/env python
"""
Executa todos os testes do EDUcador via pytest.

Uso:
    python tests/run_all_tests.py           # testes offline
    python tests/run_all_tests.py --all     # offline + integracao
    python tests/run_all_tests.py --integration  # so integracao
"""

import sys
import subprocess
from pathlib import Path


def run_pytest(marker: str = "not integration", timeout: int = 120) -> int:
    cmd = [
        sys.executable, "-m", "pytest",
        "-x",  # stop on first failure
        "-v",
        "-m", marker,
        "--tb=short",
        "-p", "no:cacheprovider",
    ]
    print(f"Executando: {' '.join(cmd)}")
    result = subprocess.run(cmd, timeout=timeout)
    return result.returncode


def main():
    print("=" * 60)
    print("  EDUcador - Suite de Testes")
    print("=" * 60)

    args = set(sys.argv[1:])

    if "--integration" in args:
        codes = [run_pytest("integration", timeout=300)]
        label = "INTEGRACAO"
    elif "--all" in args:
        print("\n>>> TESTES OFFLINE")
        c1 = run_pytest("not integration", timeout=120)
        print("\n>>> TESTES DE INTEGRACAO")
        c2 = run_pytest("integration", timeout=300)
        codes = [c1, c2]
        label = "COMPLETOS"
    else:
        c1 = run_pytest("not integration", timeout=120)
        codes = [c1]
        label = "OFFLINE"
        print("\nDica: use --all para rodar tambem os testes de integracao (requer Ollama).")

    passed = all(c == 0 for c in codes)
    total = len(codes)
    ok = sum(1 for c in codes if c == 0)
    print(f"\n{'=' * 60}")
    print(f"  TESTES {label}: {ok}/{total} suites passaram")
    print(f"{'=' * 60}")

    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
