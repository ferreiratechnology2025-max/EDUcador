"""
Configuracoes centralizadas do EDUcador.
"""

from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CORPUS_PATH = DATA_DIR / "corpus.jsonl"


@dataclass
class OllamaConfig:
    url: str = "http://localhost:11434/api/generate"
    timeout: int = 180


@dataclass
class ModelConfig:
    tutor_model: str = "gemma3:4b"
    validator_model: str = "phi4-mini"
    fallback_model: str = "qwen3:8b"

    tutor_temperature: float = 0.5
    validator_temperature: float = 0.0
    fallback_temperature: float = 0.3

    tutor_max_tokens: int = 512
    validator_max_tokens: int = 256
    fallback_max_tokens: int = 2048


@dataclass
class PipelineConfig:
    max_revisions: int = 2
    default_scaffolding: str = "Nivel 2 (intermediario): mostra um passo-chave e deixa o aluno completar o resto"
    history_size: int = 3


@dataclass
class EngineConfig:
    engine: str = "current"
    session_timeout_minutes: int = 30


def validate_paths():
    DATA_DIR.mkdir(exist_ok=True)
    if not CORPUS_PATH.exists():
        print(f"Corpus nao encontrado em {CORPUS_PATH}")
        print("  Crie o arquivo ou rode 'python scripts/setup.py'")
    return CORPUS_PATH.exists()
