"""Shared fixtures for EDUcador tests."""

from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import pytest

from src.rag.simple_rag import SimpleRAG
from src.memory.history import Memory
from config.settings import CORPUS_PATH, OllamaConfig, ModelConfig, PipelineConfig


@pytest.fixture
def corpus_path():
    return str(CORPUS_PATH)


@pytest.fixture
def rag(corpus_path):
    return SimpleRAG(corpus_path)


@pytest.fixture
def memory():
    return Memory(max_size=10)


@pytest.fixture
def small_memory():
    return Memory(max_size=3)


@pytest.fixture
def ollama_config():
    return OllamaConfig()


@pytest.fixture
def model_config():
    return ModelConfig()


@pytest.fixture
def pipeline_config():
    return PipelineConfig()


@pytest.fixture
def mock_ollama_client():
    """Cria um mock do OllamaClient que retorna texto fixo."""
    mock = MagicMock()
    mock.generate.return_value = "Resposta simulada do modelo."
    return mock


@pytest.fixture
def mock_ollama_json():
    """Cria um mock do OllamaClient que retorna JSON valido."""
    mock = MagicMock()
    mock.generate.return_value = (
        '{"verdict": "approve", "math_correct": true, '
        '"issues": [], "suggestions": [], "confidence": 0.95}'
    )
    return mock


@pytest.fixture
def sample_corpus_lines():
    """Linhas de corpus para teste com corpus temporario."""
    return [
        '{"id": 1, "assunto": "Teste A", "tags": ["tag_a"], "enunciado": "resolva x + 1 = 2", "resolucao": "x = 1"}',
        '{"id": 2, "assunto": "Teste B", "tags": ["tag_b"], "enunciado": "resolva x^2 = 4", "resolucao": "x = +-2"}',
    ]


@pytest.fixture
def temp_corpus(tmp_path, sample_corpus_lines):
    """Cria um corpus temporario para testes."""
    path = tmp_path / "corpus.jsonl"
    path.write_text("\n".join(sample_corpus_lines), encoding="utf-8")
    return str(path)
