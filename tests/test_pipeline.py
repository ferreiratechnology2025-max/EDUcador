"""
Teste de integracao do pipeline completo.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.pipeline import run_pipeline
from src.rag.simple_rag import SimpleRAG
from src.memory.history import Memory


def test_pipeline_basic():
    """Teste basico do pipeline com uma pergunta simples."""
    print("\n=== Teste 1: Pipeline Basico ===")

    memory = Memory()
    rag = SimpleRAG("data/corpus.jsonl")

    result = run_pipeline(
        student_input="como resolver 2x + 5 = 17",
        memory=memory,
        rag=rag,
        verbose=True,
    )

    assert result.final_response
    assert result.iterations >= 1
    assert result.total_time_s > 0
    print(f"Pipeline executou em {result.total_time_s:.1f}s com {result.iterations} iteracoes")
    return result


def test_pipeline_with_history():
    """Teste com historico de interacoes."""
    print("\n=== Teste 2: Pipeline com Historico ===")

    memory = Memory()
    rag = SimpleRAG("data/corpus.jsonl")

    r1 = run_pipeline(
        student_input="oq e funcao afim?",
        memory=memory,
        rag=rag,
        verbose=False,
    )
    assert r1.final_response

    r2 = run_pipeline(
        student_input="como calculo f(3) para f(x) = 2x - 5?",
        memory=memory,
        rag=rag,
        verbose=False,
    )
    assert r2.final_response
    assert len(memory.history) == 2

    context = memory.get_context()
    assert "funcao" in context.lower()
    print(f"Historico funcionou: {len(memory.history)} interacoes")
    return r2


if __name__ == "__main__":
    print("=" * 62)
    print("TESTES DE INTEGRACAO DO PIPELINE")
    print("=" * 62)

    try:
        test_pipeline_basic()
        test_pipeline_with_history()
        print("\n" + "=" * 62)
        print("TODOS OS TESTES PASSARAM!")
        print("=" * 62)
    except Exception as e:
        print(f"\nErro nos testes: {e}")
        import traceback
        traceback.print_exc()
