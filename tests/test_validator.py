"""Tests for the Validator module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.core.validator import call_validator, _try_extract_json, VALIDATOR_SYSTEM_PROMPT


class TestValidatorPrompt:
    def test_prompt_has_json_format_example(self):
        assert "verdict" in VALIDATOR_SYSTEM_PROMPT
        assert "math_correct" in VALIDATOR_SYSTEM_PROMPT

    def test_braces_are_escaped_for_format(self):
        assert "{{" in VALIDATOR_SYSTEM_PROMPT
        assert "}}" in VALIDATOR_SYSTEM_PROMPT

    def test_placeholders_are_present(self):
        assert "{student_input}" in VALIDATOR_SYSTEM_PROMPT
        assert "{tutor_response}" in VALIDATOR_SYSTEM_PROMPT
        assert "{scaffolding_level}" in VALIDATOR_SYSTEM_PROMPT

    def test_format_works_with_valid_args(self):
        result = VALIDATOR_SYSTEM_PROMPT.format(
            student_input="teste",
            tutor_response="resposta",
            scaffolding_level="N1",
        )
        assert "teste" in result
        assert "resposta" in result
        assert "N1" in result
        assert '"verdict"' in result
        assert '"math_correct"' in result

    def test_format_produces_valid_json_literal(self):
        result = VALIDATOR_SYSTEM_PROMPT.format(
            student_input="q", tutor_response="r", scaffolding_level="N1"
        )
        assert '"verdict"' in result
        assert '"math_correct"' in result
        assert "{{" not in result
        assert "}}" not in result


class TestTryExtractJson:
    def test_extracts_valid_json(self):
        text = 'Texto antes {"a": 1} texto depois'
        result = _try_extract_json(text)
        assert result == {"a": 1}

    def test_returns_none_for_no_braces(self):
        assert _try_extract_json("texto sem json") is None

    def test_returns_none_for_malformed_json(self):
        assert _try_extract_json('{"a": semfechamento') is None

    def test_handles_nested_objects(self):
        text = 'fora {"a": {"b": 2}} fora'
        result = _try_extract_json(text)
        assert result == {"a": {"b": 2}}

    def test_handles_empty_object(self):
        assert _try_extract_json("{}") == {}

    def test_handles_non_greedy_json_user_said_the_regex_changed(self):
        text = '{"v":1} lixo {"v":2}'
        result = _try_extract_json(text)
        assert result is not None


class TestCallValidator:
    def test_returns_approve_for_valid_json(self, mock_ollama_json):
        result = call_validator(
            student_input="2+2?",
            tutor_response="4",
            scaffolding_level="N1",
            client=mock_ollama_json,
        )
        assert result["verdict"] == "approve"
        assert result["math_correct"] is True

    def test_reject_on_json_decode_error(self, mock_ollama_client):
        mock_ollama_client.generate.return_value = "json invalido"
        result = call_validator(
            student_input="pergunta",
            tutor_response="resposta",
            scaffolding_level="N1",
            client=mock_ollama_client,
        )
        assert result["verdict"] == "reject"
        assert result["_error"] is True

    def test_reject_on_http_error(self, mock_ollama_client):
        from requests.exceptions import HTTPError

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_ollama_client.generate.side_effect = HTTPError(response=mock_resp)
        result = call_validator(
            student_input="p",
            tutor_response="r",
            scaffolding_level="N1",
            client=mock_ollama_client,
        )
        assert result["verdict"] == "reject"
        assert result["_error"] is True

    def test_reject_on_missing_keys(self, mock_ollama_client):
        mock_ollama_client.generate.return_value = '{"verdict": "approve"}'
        result = call_validator(
            student_input="p",
            tutor_response="r",
            scaffolding_level="N1",
            client=mock_ollama_client,
        )
        assert result["verdict"] == "reject"
        assert result["_error"] is True

    def test_clamps_confidence_above_1(self, mock_ollama_client):
        mock_ollama_client.generate.return_value = (
            '{"verdict":"approve","math_correct":true,'
            '"issues":[],"suggestions":[],"confidence":1.5}'
        )
        result = call_validator(
            client=mock_ollama_client,
            student_input="p",
            tutor_response="r",
            scaffolding_level="N1",
        )
        assert result["confidence"] == 1.0

    def test_clamps_confidence_below_0(self, mock_ollama_client):
        mock_ollama_client.generate.return_value = (
            '{"verdict":"approve","math_correct":true,'
            '"issues":[],"suggestions":[],"confidence":-0.5}'
        )
        result = call_validator(
            client=mock_ollama_client,
            student_input="p",
            tutor_response="r",
            scaffolding_level="N1",
        )
        assert result["confidence"] == 0.0

    def test_defaults_confidence_for_non_numeric(self, mock_ollama_client):
        mock_ollama_client.generate.return_value = (
            '{"verdict":"approve","math_correct":true,'
            '"issues":[],"suggestions":[],"confidence":"alto"}'
        )
        result = call_validator(
            client=mock_ollama_client,
            student_input="p",
            tutor_response="r",
            scaffolding_level="N1",
        )
        assert result["confidence"] == 0.0

    def test_defaults_issues_to_list(self, mock_ollama_client):
        mock_ollama_client.generate.return_value = (
            '{"verdict":"approve","math_correct":true,'
            '"issues":null,"suggestions":null,"confidence":0.5}'
        )
        result = call_validator(
            client=mock_ollama_client,
            student_input="p",
            tutor_response="r",
            scaffolding_level="N1",
        )
        assert result["issues"] == []
        assert result["suggestions"] == []

    def test_normalizes_invalid_verdict(self, mock_ollama_client):
        mock_ollama_client.generate.return_value = (
            '{"verdict":"maybe","math_correct":true,'
            '"issues":[],"suggestions":[],"confidence":0.5}'
        )
        result = call_validator(
            client=mock_ollama_client,
            student_input="p",
            tutor_response="r",
            scaffolding_level="N1",
        )
        assert result["verdict"] == "reject"

    def test_passes_correct_model(self, mock_ollama_json):
        mock_ollama_json.generate.reset_mock()
        call_validator(
            client=mock_ollama_json,
            student_input="p",
            tutor_response="r",
            scaffolding_level="N1",
        )
        _, kwargs = mock_ollama_json.generate.call_args
        assert kwargs["model"] == "phi4-mini"

    def test_uses_json_mode(self, mock_ollama_json):
        mock_ollama_json.generate.reset_mock()
        call_validator(
            client=mock_ollama_json,
            student_input="p",
            tutor_response="r",
            scaffolding_level="N1",
        )
        _, kwargs = mock_ollama_json.generate.call_args
        assert kwargs["json_mode"] is True
