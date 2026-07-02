"""Tests for the Ollama HTTP client with retry logic."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.utils.ollama_client import OllamaClient
from config.settings import OllamaConfig


@pytest.fixture
def client():
    cfg = OllamaConfig(url="http://test:11434/api/generate", timeout=5)
    return OllamaClient(config=cfg)


class TestPayloadStructure:
    def test_payload_contains_model(self, client):
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"response": "ok"}
            mock_post.return_value.raise_for_status.return_value = None
            client.generate(prompt="teste", system="seja util", model="gemma")
            payload = mock_post.call_args[1]["json"]
            assert payload["model"] == "gemma"

    def test_payload_does_not_stream(self, client):
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"response": "ok"}
            mock_post.return_value.raise_for_status.return_value = None
            client.generate(prompt="teste", system="s", model="m")
            payload = mock_post.call_args[1]["json"]
            assert payload["stream"] is False

    def test_json_mode_adds_format_key(self, client):
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"response": "ok"}
            mock_post.return_value.raise_for_status.return_value = None
            client.generate(prompt="teste", system="s", model="m", json_mode=True)
            payload = mock_post.call_args[1]["json"]
            assert payload["format"] == "json"

    def test_options_contain_temperature(self, client):
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"response": "ok"}
            mock_post.return_value.raise_for_status.return_value = None
            client.generate(prompt="teste", system="s", model="m", temperature=0.7)
            payload = mock_post.call_args[1]["json"]
            assert payload["options"]["temperature"] == 0.7

    def test_options_contain_num_predict(self, client):
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"response": "ok"}
            mock_post.return_value.raise_for_status.return_value = None
            client.generate(prompt="teste", system="s", model="m", max_tokens=128)
            payload = mock_post.call_args[1]["json"]
            assert payload["options"]["num_predict"] == 128


class TestRetryLogic:
    def test_no_retry_on_4xx(self, client):
        with patch("requests.post") as mock_post:
            resp = MagicMock()
            resp.status_code = 404
            resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
                response=resp
            )
            mock_post.return_value = resp

            with pytest.raises(requests.exceptions.HTTPError):
                client.generate(prompt="teste", system="s", model="inexistente")

            assert mock_post.call_count == 1

    def test_retry_on_5xx(self, client):
        with patch("requests.post") as mock_post:
            resp = MagicMock()
            resp.status_code = 503
            resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
                response=resp
            )
            mock_post.return_value = resp

            with pytest.raises(RuntimeError, match="3 tentativas"):
                client.generate(prompt="teste", system="s", model="m")

            assert mock_post.call_count == 3

    def test_retry_on_connection_error(self, client):
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("no route")

            with pytest.raises(RuntimeError, match="3 tentativas"):
                client.generate(prompt="teste", system="s", model="m")

            assert mock_post.call_count == 3

    def test_retry_on_timeout(self, client):
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("timed out")

            with pytest.raises(RuntimeError, match="3 tentativas"):
                client.generate(prompt="teste", system="s", model="m")

            assert mock_post.call_count == 3

    def test_succeeds_on_second_attempt_after_connection_error(self, client):
        with patch("requests.post") as mock_post:
            ok_resp = MagicMock()
            ok_resp.json.return_value = {"response": "funcionou"}
            ok_resp.raise_for_status.return_value = None
            mock_post.side_effect = [
                requests.exceptions.ConnectionError("fail"),
                ok_resp,
            ]

            result = client.generate(prompt="teste", system="s", model="m")
            assert result == "funcionou"
            assert mock_post.call_count == 2


class TestTimeoutEdgeCases:
    def test_uses_config_timeout(self, client):
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"response": "ok"}
            mock_post.return_value.raise_for_status.return_value = None
            client.generate(prompt="teste", system="s", model="m")
            assert mock_post.call_args[1]["timeout"] == 5

    def test_long_timeout(self):
        cfg = OllamaConfig(timeout=300)
        c = OllamaClient(config=cfg)
        with patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"response": "ok"}
            mock_post.return_value.raise_for_status.return_value = None
            c.generate(prompt="teste", system="s", model="m")
            assert mock_post.call_args[1]["timeout"] == 300
