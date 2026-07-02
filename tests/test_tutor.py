"""Tests for the Tutor module."""

from unittest.mock import MagicMock, patch

import pytest

from src.core.tutor import call_tutor, call_tutor_with_feedback, TUTOR_SYSTEM_PROMPT


class TestTutorPrompt:
    def test_prompt_contains_scaffolding_placeholder(self):
        assert "{scaffolding_level}" in TUTOR_SYSTEM_PROMPT

    def test_prompt_contains_student_context_placeholder(self):
        assert "{student_context}" in TUTOR_SYSTEM_PROMPT

    def test_prompt_contains_rag_context_placeholder(self):
        assert "{rag_context}" in TUTOR_SYSTEM_PROMPT

    def test_prompt_contains_subject_placeholder(self):
        assert "{subject}" in TUTOR_SYSTEM_PROMPT

    def test_prompt_in_portuguese(self):
        assert "português brasileiro" in TUTOR_SYSTEM_PROMPT

    def test_prompt_mentions_scaffolding_levels(self):
        assert "Nível 1" in TUTOR_SYSTEM_PROMPT
        assert "Nível 2" in TUTOR_SYSTEM_PROMPT
        assert "Nível 3" in TUTOR_SYSTEM_PROMPT


class TestCallTutor:
    def test_basic_call_returns_string(self, mock_ollama_client):
        result = call_tutor(
            student_input="como resolver 2x + 5 = 17",
            student_context="",
            rag_context="",
            scaffolding_level="Nível 2",
            client=mock_ollama_client,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_passes_correct_model(self, mock_ollama_client):
        mock_ollama_client.generate.reset_mock()
        call_tutor(
            student_input="pergunta",
            student_context="",
            rag_context="",
            scaffolding_level="Nível 1",
            client=mock_ollama_client,
        )
        _, kwargs = mock_ollama_client.generate.call_args
        assert kwargs["model"] == "gemma3:4b"

    def test_uses_tutor_temperature(self, mock_ollama_client):
        mock_ollama_client.generate.reset_mock()
        call_tutor(
            student_input="pergunta",
            student_context="",
            rag_context="",
            scaffolding_level="Nível 2",
            client=mock_ollama_client,
        )
        _, kwargs = mock_ollama_client.generate.call_args
        assert kwargs["temperature"] == 0.5

    def test_default_client_and_config(self):
        with patch("src.core.tutor.OllamaClient") as mock_client_cls:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = "ok"
            mock_client_cls.return_value = mock_instance
            result = call_tutor(
                student_input="teste",
                student_context="ctx",
                rag_context="rag",
                scaffolding_level="N1",
            )
            assert result == "ok"


class TestCallTutorWithFeedback:
    def test_basic_call_returns_string(self, mock_ollama_client):
        result = call_tutor_with_feedback(
            student_input="resolva x^2=4",
            feedback=["explique passo a passo"],
            student_context="",
            rag_context="",
            scaffolding_level="Nível 3",
            client=mock_ollama_client,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_includes_feedback_in_prompt(self, mock_ollama_client):
        mock_ollama_client.generate.reset_mock()
        feedback = ["erro no sinal", "falta unidade"]
        call_tutor_with_feedback(
            student_input="teste",
            feedback=feedback,
            student_context="",
            rag_context="",
            scaffolding_level="Nível 2",
            client=mock_ollama_client,
        )
        prompt = mock_ollama_client.generate.call_args[1]["prompt"]
        assert "erro no sinal" in prompt
        assert "falta unidade" in prompt

    def test_empty_feedback_is_handled(self, mock_ollama_client):
        mock_ollama_client.generate.reset_mock()
        call_tutor_with_feedback(
            student_input="teste",
            feedback=[],
            student_context="",
            rag_context="",
            scaffolding_level="Nível 2",
            client=mock_ollama_client,
        )
        prompt = mock_ollama_client.generate.call_args[1]["prompt"]
        assert "nenhuma sugestão" in prompt
