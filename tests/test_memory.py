"""
Teste do sistema de memória do EDUcador.
"""

from src.memory.history import Memory


def test_memory():
    memory = Memory(max_size=3)

    memory.add_interaction(
        user="professor não tô conseguindo resolver 2x + 5 = 17",
        assistant="Vamos resolver juntos...",
        topic="equação do 1º grau",
        scaffolding="Nível 2"
    )

    memory.add_interaction(
        user="como eu acho o vértice da parábola?",
        assistant="O vértice é dado por x = -b/2a...",
        topic="função quadrática",
        scaffolding="Nível 3"
    )

    memory.add_interaction(
        user="oq é Bhaskara?",
        assistant="Bhaskara é a fórmula...",
        topic="fórmula de Bhaskara",
        scaffolding="Nível 1"
    )

    context = memory.get_context(last_n=2)
    assert "Bhaskara" in context
    assert "vértice" in context
    assert "2x + 5" not in context
    print("[OK] Teste 1: Contexto OK")

    summary = memory.get_summary()
    assert summary["total_interactions"] == 3
    assert summary["current_topic"] == "fórmula de Bhaskara"
    print("[OK] Teste 2: Sumário OK")

    data = memory.to_dict()
    assert len(data) == 3
    print("[OK] Teste 3: Serialização OK")

    new_memory = Memory.from_dict(data, max_size=3)
    assert new_memory.get_summary()["total_interactions"] == 3
    print("[OK] Teste 4: Deserialização OK")

    memory.add_interaction("teste", "resposta", "teste")
    assert len(memory.history) == 3
    print("[OK] Teste 5: Limite de tamanho OK")

    topics = memory.get_recent_topics(n=2)
    assert "teste" in topics
    assert "fórmula de Bhaskara" in topics
    print("[OK] Teste 6: Tópicos recentes OK")

    print("[OK] Todos os testes do Memory passaram!")


if __name__ == "__main__":
    test_memory()
