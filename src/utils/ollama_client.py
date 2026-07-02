"""
Cliente HTTP para comunicação com Ollama, com retry e backoff exponencial.
"""

import json
import time
import requests
from typing import Optional, Dict, Any

from config.settings import OllamaConfig, ModelConfig


class OllamaClient:
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()

    def generate(
        self,
        prompt: str,
        system: str,
        model: str,
        temperature: float = 0.5,
        max_tokens: int = 512,
        json_mode: bool = False,
    ) -> str:
        """
        Faz uma chamada síncrona ao Ollama com retry e backoff exponencial.

        Tenta até 3 vezes em caso de:
        - ConnectionError (Ollama reiniciando, rede instavel)
        - Timeout (modelo lento)
        - 5xx (erro interno do Ollama)

        Nao faz retry em 4xx (erro do cliente, ex: modelo nao existe).
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if json_mode:
            payload["format"] = "json"

        max_attempts = 3
        last_error: Optional[Exception] = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(
                    self.config.url,
                    json=payload,
                    timeout=self.config.timeout,
                )
                response.raise_for_status()
                return response.json()["response"]

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else None
                if status and 400 <= status < 500:
                    raise
                last_error = e
                print(f"  [OllamaClient] tentativa {attempt}/{max_attempts} falhou (HTTP {status})")

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_error = e
                print(f"  [OllamaClient] tentativa {attempt}/{max_attempts} falhou ({type(e).__name__})")

            if attempt < max_attempts:
                wait = 2 ** attempt
                time.sleep(wait)

        raise RuntimeError(
            f"Ollama nao respondeu apos {max_attempts} tentativas: {type(last_error).__name__}: {last_error}"
        )