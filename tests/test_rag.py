"""
Teste simples do RAG.
"""

from src.rag.simple_rag import SimpleRAG

def test_rag():
    rag = SimpleRAG("data/corpus.jsonl")

    results = rag.retrieve("como resolver equação 2x + 5 = 17", top_k=1)
    assert results, "Nenhum resultado para equação"
    assert "equacao_1grau" in results[0].get("tags", [])
    print("[OK] Teste 1: Matemática OK")

    results = rag.retrieve("velocidade inicial zero com aceleração", top_k=1)
    assert results, "Nenhum resultado para física"
    print("[OK] Teste 2: Física OK")

    results = rag.retrieve("cruzamento de genes", top_k=1)
    assert results, "Nenhum resultado para genética"
    print("[OK] Teste 3: Biologia OK")

    results = rag.retrieve("tutor me ajuda com função", top_k=1)
    assert results, "Fallback BM25 falhou"
    print("[OK] Teste 4: Fallback BM25 OK")

    print("[OK] Todos os testes do RAG passaram!")

if __name__ == "__main__":
    test_rag()
