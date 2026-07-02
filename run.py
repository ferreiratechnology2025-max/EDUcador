#!/usr/bin/env python
"""
Ponto de entrada do EDUcador.

Modos de uso:
- python run.py                 -> abre interface Streamlit (padrao)
- python run.py "pergunta aqui" -> roda pipeline no terminal com a pergunta
- echo "pergunta" | python run.py -> le pergunta do stdin
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path
import requests

REQUIRED_MODELS = ["gemma3:4b", "phi4-mini"]
OPTIONAL_MODELS = ["llama3.2-vision"]


def check_ollama_running():
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def start_ollama():
    print("Iniciando Ollama...")

    if sys.platform == "win32":
        subprocess.Popen(
            ["ollama", "serve"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    max_wait = 30
    for _ in range(max_wait):
        time.sleep(1)
        if check_ollama_running():
            print("Ollama iniciado com sucesso!")
            return True

    print(f"Nao foi possivel iniciar o Ollama apos {max_wait}s.")
    return False


def check_model_installed(model_name):
    try:
        response = requests.post(
            "http://localhost:11434/api/show",
            json={"name": model_name},
            timeout=5,
        )
        return response.status_code == 200
    except Exception:
        return False


def pull_model(model_name):
    print(f"Baixando {model_name}... (pode levar alguns minutos)")

    try:
        response = requests.post(
            "http://localhost:11434/api/pull",
            json={"name": model_name},
            stream=True,
            timeout=None,
        )

        last_status = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if "status" in data:
                        status = data["status"]
                        if status != last_status:
                            print(f"  {status}")
                            last_status = status
                except Exception:
                    pass

        print(f"{model_name} baixado com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao baixar {model_name}: {e}")
        return False


def ensure_models():
    missing = []
    for model in REQUIRED_MODELS:
        if not check_model_installed(model):
            missing.append(model)

    if missing:
        print(f"\nModelos nao encontrados: {', '.join(missing)}")
        print("Serao baixados automaticamente.\n")

        for model in missing:
            if not pull_model(model):
                print(f"Falha ao baixar {model}")
                return False

    for model in OPTIONAL_MODELS:
        if not check_model_installed(model):
            print(f"Modelo opcional {model} nao encontrado. OCR nao estara disponivel.")

    return True


def ensure_ollama_and_models() -> bool:
    """Garante que Ollama esta rodando e os modelos necessarios estao instalados."""
    if not check_ollama_running():
        if not start_ollama():
            print("\nOllama nao esta instalado.")
            print("   Baixe em: https://ollama.com/")
            print("   Ou execute: ollama serve")
            return False

    if not ensure_models():
        print("\nFalha ao verificar modelos.")
        print("   Execute manualmente: ollama pull gemma3:4b")
        return False

    return True


def run_terminal(question: str) -> None:
    """Roda o pipeline no terminal com a pergunta fornecida."""
    sys.path.insert(0, str(Path(__file__).parent))

    from src.core.pipeline import run_pipeline
    from src.rag.simple_rag import SimpleRAG
    from src.memory.history import Memory
    from config.settings import CORPUS_PATH

    print("=" * 60)
    print(f"  Pergunta: {question}")
    print("=" * 60)

    rag = None
    if CORPUS_PATH.exists():
        try:
            rag = SimpleRAG(str(CORPUS_PATH))
        except Exception as e:
            print(f"[Aviso] RAG indisponivel: {e}")

    memory = Memory(max_size=10)

    try:
        result = run_pipeline(
            student_input=question,
            memory=memory,
            rag=rag,
            verbose=True,
        )
        print("\n" + "=" * 60)
        print("  Resposta:")
        print("=" * 60)
        print(result.final_response)
        print("=" * 60)
        print(f"  Tempo: {result.total_time_s:.1f}s | Iteracoes: {result.iterations} | RAG: {result.rag_used} | Fallback: {result.fallback_used}")
        print("=" * 60)
    except Exception as e:
        print(f"\nErro ao processar: {type(e).__name__}: {e}")
        sys.exit(1)


def run_streamlit():
    print("Iniciando EDUcador...")

    sys.path.insert(0, str(Path(__file__).parent))

    import streamlit.web.cli as stcli

    interface_path = Path(__file__).parent / "interface.py"

    if not interface_path.exists():
        print(f"interface.py nao encontrado em {interface_path}")
        return

    sys.argv = [
        "streamlit",
        "run",
        str(interface_path),
        "--server.headless",
        "true",
        "--server.runOnSave",
        "false",
    ]

    stcli.main()


def get_question_from_args_or_stdin():
    """
    Detecta o modo de uso:
    1. Argumento posicional: python run.py "pergunta"
    2. Stdin nao-vazio: echo "pergunta" | python run.py
    3. Nenhum: retorna None (abrir Streamlit)
    """
    if len(sys.argv) > 1 and sys.argv[1] and not sys.argv[1].startswith("-"):
        return " ".join(sys.argv[1:]).strip()

    if not sys.stdin.isatty():
        try:
            data = sys.stdin.read()
            if data.strip():
                return data.strip()
        except Exception:
            pass

    return None


def main():
    print("=" * 60)
    print("  EDUcador - Seu Professor Particular")
    print("=" * 60)

    question = get_question_from_args_or_stdin()

    if question is None:
        # Modo UI
        if not ensure_ollama_and_models():
            input("\nPressione Enter para sair...")
            sys.exit(1)

        print("\n" + "=" * 60)
        print("  Tudo pronto! Abrindo interface...")
        print("=" * 60)

        try:
            run_streamlit()
        except KeyboardInterrupt:
            print("\nAte logo!")
        except Exception as e:
            print(f"Erro ao iniciar: {e}")
            input("\nPressione Enter para sair...")
    else:
        # Modo terminal - pergunta unica
        if not ensure_ollama_and_models():
            sys.exit(1)
        run_terminal(question)


if __name__ == "__main__":
    main()
