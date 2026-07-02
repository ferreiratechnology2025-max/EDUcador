"""
Validador: Avalia respostas do tutor usando Phi-4-mini com fallback estrutural.
"""

import json
import re
import requests
from typing import Optional, Dict, Any

from config.settings import ModelConfig
from src.utils.ollama_client import OllamaClient

VALIDATOR_SYSTEM_PROMPT = """Você é o validador matemático do EDUcador. Sua função é revisar a resposta gerada pelo tutor ANTES de enviá-la ao aluno.

Avalie 4 critérios nesta ordem:

1. **Correção matemática**: execute você mesmo as contas / resolva a equação / verifique a fórmula. Está certo?

2. **Didática**: a explicação é clara para um aluno do ensino médio brasileiro? Há analogias úteis? O passo a passo é coerente?

3. **Ausência de alucinação**: o tutor inventou alguma fórmula, propriedade, regra ou fato que não existe?

4. **Adequação ao nível**: a profundidade da resposta é apropriada para o nível de dificuldade pedido?

Responda EXCLUSIVAMENTE em JSON válido (sem markdown, sem ```), no formato:

{{
  "verdict": "approve" | "revise" | "reject",
  "math_correct": true | false,
  "issues": ["lista de problemas encontrados em português"],
  "suggestions": ["lista de melhorias ESPECÍFICAS que o tutor deve aplicar"],
  "confidence": 0.0 a 1.0
}}

Critérios de veredito:
- approve: tudo certo, pode mandar pro aluno
- revise: tem problemas corrigíveis, pedir pro tutor reescrever aplicando as sugestões
- reject: erro matemático grave, alucinação óbvia, ou problema que reescrita não conserta — escalar para fallback

Se você não tem certeza da resposta do tutor, marque revise e indique onde está a dúvida.

[PERGUNTA DO ALUNO]
{student_input}

[RESPOSTA DO TUTOR]
{tutor_response}

[NÍVEL DE DIFICULDADE PEDIDO]
{scaffolding_level}
"""

def _try_extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Tenta extrair JSON do texto. Usa pilha para capturar {} completos."""
    stack = []
    for i, ch in enumerate(text):
        if ch == "{":
            stack.append(i)
        elif ch == "}":
            if stack:
                start = stack.pop()
                if not stack:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        pass
    return None

def call_validator(
    student_input: str,
    tutor_response: str,
    scaffolding_level: str,
    client: OllamaClient = None,
    config: ModelConfig = None,
) -> Dict[str, Any]:
    """
    Valida a resposta do tutor com fallback estrutural estrito.
    Retorna dict com as chaves: verdict, math_correct, issues, suggestions, confidence, _error (opcional)
    """
    if client is None:
        client = OllamaClient()
    if config is None:
        config = ModelConfig()

    system = VALIDATOR_SYSTEM_PROMPT.format(
        student_input=student_input,
        tutor_response=tutor_response,
        scaffolding_level=scaffolding_level,
    )

    try:
        raw = client.generate(
            prompt="Faça a validação agora. Retorne APENAS o JSON válido.",
            system=system,
            model=config.validator_model,
            temperature=config.validator_temperature,
            max_tokens=config.validator_max_tokens,
            json_mode=True,
        )
        verdict = json.loads(raw)
    except (json.JSONDecodeError, requests.RequestException) as e:
        return {
            "verdict": "reject",
            "math_correct": False,
            "issues": [f"Falha na validação: {type(e).__name__}: {str(e)[:100]}"],
            "suggestions": [],
            "confidence": 0.0,
            "_error": True
        }
    except Exception as e:
        return {
            "verdict": "reject",
            "math_correct": False,
            "issues": [f"Erro inesperado na validação: {type(e).__name__}: {str(e)[:100]}"],
            "suggestions": [],
            "confidence": 0.0,
            "_error": True
        }

    required_keys = {"verdict", "math_correct", "issues", "suggestions", "confidence"}
    if not required_keys.issubset(verdict.keys()):
        return {
            "verdict": "reject",
            "math_correct": False,
            "issues": ["Validador retornou JSON incompleto"],
            "suggestions": [],
            "confidence": 0.0,
            "_error": True
        }

    if verdict.get("verdict") not in ["approve", "revise", "reject"]:
        verdict["verdict"] = "reject"

    if not isinstance(verdict.get("issues"), list):
        verdict["issues"] = []
    if not isinstance(verdict.get("suggestions"), list):
        verdict["suggestions"] = []

    if not isinstance(verdict.get("confidence"), (int, float)):
        verdict["confidence"] = 0.0
    verdict["confidence"] = max(0.0, min(1.0, verdict["confidence"]))

    return verdict
