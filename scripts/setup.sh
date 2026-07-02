#!/bin/bash

echo "===================================="
echo "  EDUcador - Setup Inicial"
echo "===================================="

echo ""
echo "[1/3] Instalando dependencias Python..."
pip install -r requirements.txt

echo ""
echo "[2/3] Verificando Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "ERRO: Ollama nao encontrado. Instale de: https://ollama.com/"
    exit 1
fi

echo ""
echo "[3/3] Baixando modelos..."
echo "Baixando gemma3:4b (pode levar alguns minutos)..."
ollama pull gemma3:4b
echo "Baixando phi4-mini (pode levar alguns minutos)..."
ollama pull phi4-mini
echo "Baixando qwen3:8b (opcional - Ctrl+C para pular)..."
ollama pull qwen3:8b

echo ""
echo "===================================="
echo "  Setup concluido!"
echo ""
echo "Para iniciar o Ollama: ollama serve"
echo "Para rodar o EDUcador: python run.py \"sua pergunta\""
echo "===================================="
