#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import json
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).parent))

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


def run_terminal(question: str, engine_type: str = "current") -> None:
    from src.learning.engine import create_engine

    engine = create_engine(engine_type)
    info = engine.get_session_info("terminal")

    print("=" * 60)
    print(f"  Pergunta: {question}")
    print(f"  Motor: {info['engine']}")
    print("=" * 60)

    try:
        response = engine.process(user_input=question, session_id="terminal")
        print("\n" + "=" * 60)
        print("  Resposta:")
        print("=" * 60)
        print(response.message)
        print("=" * 60)
        meta = response.metadata or {}
        if meta:
            parts = [f"  {k}: {v}" for k, v in meta.items()]
            print("\n" + "\n".join(parts))
        print("=" * 60)
    except Exception as e:
        print(f"\nErro ao processar: {type(e).__name__}: {e}")
        sys.exit(1)


def run_streamlit():
    print("Iniciando EDUcador...")

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


def parse_args():
    engine_type = "current"
    args = sys.argv[1:]

    if "--engine" in args:
        idx = args.index("--engine")
        if idx + 1 < len(args):
            engine_type = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
        else:
            args.remove("--engine")

    question = None
    if args and not args[0].startswith("-"):
        question = " ".join(args).strip()

    if question is None and not sys.stdin.isatty():
        try:
            data = sys.stdin.read()
            if data.strip():
                question = data.strip()
        except Exception:
            pass

    return question, engine_type


def main():
    print("=" * 60)
    print("  EDUcador - Seu Professor Particular")
    print("=" * 60)

    question, engine_type = parse_args()

    if question is None:
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
        if not ensure_ollama_and_models():
            sys.exit(1)
        run_terminal(question, engine_type)


if __name__ == "__main__":
    main()
