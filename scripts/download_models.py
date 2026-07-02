#!/usr/bin/env python
"""
Download dos modelos Ollama para empacotamento no instalador.
Baixa os modelos e os salva na pasta models/ em formato compativel.
"""

import os
import sys
import json
import requests
from pathlib import Path

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

MODELS = [
    {"name": "gemma3:4b", "size_gb": 2.5},
    {"name": "phi4-mini", "size_gb": 2.5},
    {"name": "qwen3:8b", "size_gb": 5.0},
    {"name": "llama3.2-vision", "size_gb": 2.5},
]


def get_ollama_models_path():
    if sys.platform == "win32":
        return Path(os.environ.get("USERPROFILE", "")) / ".ollama" / "models"
    return Path.home() / ".ollama" / "models"


def pull_model(model_name):
    print(f"Baixando {model_name}... (pode levar varios minutos)")

    try:
        response = requests.post(
            "http://localhost:11434/api/pull",
            json={"name": model_name},
            stream=True,
            timeout=None,
        )

        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if "status" in data:
                        print(f"  {data['status']}")
                except Exception:
                    pass

        return True
    except Exception as e:
        print(f"Erro ao baixar {model_name}: {e}")
        return False


def copy_model_to_dist(model_name):
    src = get_ollama_models_path()
    if not src.exists():
        print(f"Diretorio de modelos nao encontrado: {src}")
        return False

    model_dir = None
    for item in src.iterdir():
        if item.is_dir() and (
            model_name.replace(":", "-") in item.name
            or model_name.split(":")[0] in item.name
        ):
            model_dir = item
            break

    if not model_dir:
        print(f"Modelo {model_name} nao encontrado no Ollama")
        return False

    import shutil

    dest = MODELS_DIR / model_name.replace(":", "-")
    dest.mkdir(exist_ok=True)

    for file in model_dir.rglob("*"):
        if file.is_file():
            rel_path = file.relative_to(model_dir)
            dest_file = dest / rel_path
            dest_file.parent.mkdir(exist_ok=True)
            shutil.copy2(file, dest_file)

    print(f"{model_name} copiado para {dest}")
    return True


def main():
    print("=" * 60)
    print("  Download de Modelos para Empacotamento")
    print("=" * 60)

    try:
        requests.get("http://localhost:11434/api/tags", timeout=2)
    except Exception:
        print("Ollama nao esta rodando. Execute 'ollama serve' e tente novamente.")
        sys.exit(1)

    total_size = sum(m["size_gb"] for m in MODELS)
    print(f"\nSerao baixados {len(MODELS)} modelos (~{total_size:.1f} GB)")
    print("Isso pode levar 1-2 horas dependendo da sua conexao.\n")

    for model in MODELS:
        print(f"\n--- {model['name']} ({model['size_gb']} GB) ---")
        if pull_model(model["name"]):
            copy_model_to_dist(model["name"])

    print("\n" + "=" * 60)
    print(f"Modelos salvos em: {MODELS_DIR}")
    print(f"   Tamanho total: ~{total_size:.1f} GB")
    print("=" * 60)


if __name__ == "__main__":
    main()
