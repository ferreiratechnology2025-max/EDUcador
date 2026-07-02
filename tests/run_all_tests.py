#!/usr/bin/env python
"""
Executa todos os testes do EDUcador.

Testes offline (rodam sempre):
- RAG
- Memoria

Testes de integracao (precisam de Ollama rodando + modelos instalados):
- Pipeline
"""
import sys
import subprocess
from pathlib import Path


def run_test(name: str, module: str, optional: bool = False) -> bool:
    print(f"\n{'=' * 50}")
    print(f"Executando: {name}")
    print('=' * 50)

    try:
        result = subprocess.run(
            [sys.executable, "-m", module],
            capture_output=True,
            text=True,
            timeout=300,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode == 0:
            print(f"OK {name}")
            return True

        print(f"FALHOU {name} (codigo {result.returncode})")
        return False

    except subprocess.TimeoutExpired:
        print(f"FALHOU {name} (timeout - Ollama nao respondeu em 5 min)")
        return False
    except Exception as e:
        print(f"FALHOU {name} (erro ao executar: {e})")
        return False


def main():
    print("=" * 60)
    print("  EDUcador - Suite de Testes")
    print("=" * 60)

    # Testes offline (devem rodar sempre)
    offline_tests = [
        ("RAG", "tests.test_rag"),
        ("Memoria", "tests.test_memory"),
    ]

    # Testes de integracao (precisam de Ollama)
    integration_tests = [
        ("Pipeline (integracao)", "tests.test_pipeline"),
    ]

    passed = 0
    failed = 0
    skipped = 0

    print("\n>>> TESTES OFFLINE")
    for name, module in offline_tests:
        if run_test(name, module):
            passed += 1
        else:
            failed += 1

    print("\n>>> TESTES DE INTEGRACAO (requer Ollama rodando)")
    # Pergunta ao usuario se quer rodar testes de integracao
    if len(sys.argv) > 1 and sys.argv[1] in ("--integration", "--all"):
        run_integration = True
    else:
        try:
            resp = input("Rodar testes de integracao? (s/N): ").strip().lower()
            run_integration = resp in ("s", "sim", "y", "yes")
        except EOFError:
            run_integration = False

    if run_integration:
        for name, module in integration_tests:
            if run_test(name, module):
                passed += 1
            else:
                failed += 1
    else:
        print("Pulando testes de integracao. Use --integration ou --all pra rodar.")
        skipped = len(integration_tests)

    print("\n" + "=" * 60)
    print(f"RESULTADO: {passed} aprovados, {failed} falhas, {skipped} pulados")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()