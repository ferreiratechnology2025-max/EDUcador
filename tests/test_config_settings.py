"""Tests for configuration settings."""

from pathlib import Path

import pytest

from config.settings import (
    OllamaConfig,
    ModelConfig,
    PipelineConfig,
    BASE_DIR,
    DATA_DIR,
    CORPUS_PATH,
    validate_paths,
)


class TestOllamaConfig:
    def test_default_url(self):
        cfg = OllamaConfig()
        assert cfg.url == "http://localhost:11434/api/generate"

    def test_default_timeout(self):
        cfg = OllamaConfig()
        assert cfg.timeout == 180

    def test_custom_url(self):
        cfg = OllamaConfig(url="http://other:11434/generate")
        assert cfg.url == "http://other:11434/generate"

    def test_custom_timeout(self):
        cfg = OllamaConfig(timeout=60)
        assert cfg.timeout == 60

    def test_url_is_string(self):
        assert isinstance(OllamaConfig().url, str)


class TestModelConfig:
    def test_default_tutor_model(self):
        cfg = ModelConfig()
        assert cfg.tutor_model == "gemma3:4b"

    def test_default_validator_model(self):
        cfg = ModelConfig()
        assert cfg.validator_model == "phi4-mini"

    def test_validator_temperature_is_zero(self):
        cfg = ModelConfig()
        assert cfg.validator_temperature == 0.0

    def test_tutor_temperature(self):
        cfg = ModelConfig()
        assert cfg.tutor_temperature == 0.5

    def test_fallback_model(self):
        cfg = ModelConfig()
        assert cfg.fallback_model == "qwen3:8b"


class TestPipelineConfig:
    def test_max_revisions_default(self):
        cfg = PipelineConfig()
        assert cfg.max_revisions == 2

    def test_history_size_default(self):
        cfg = PipelineConfig()
        assert cfg.history_size == 3

    def test_default_scaffolding_not_empty(self):
        cfg = PipelineConfig()
        assert len(cfg.default_scaffolding) > 0

    def test_default_scaffolding_mentions_nivel_2(self):
        cfg = PipelineConfig()
        assert "Nivel 2" in cfg.default_scaffolding


class TestPaths:
    def test_base_dir_exists(self):
        assert BASE_DIR.exists()

    def test_data_dir_is_relative_to_base(self):
        assert DATA_DIR == BASE_DIR / "data"

    def test_corpus_path_is_relative_to_data(self):
        assert CORPUS_PATH == DATA_DIR / "corpus.jsonl"

    def test_validate_paths_returns_bool(self):
        result = validate_paths()
        assert isinstance(result, bool)
