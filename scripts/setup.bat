@echo off
echo ====================================
echo  EDUcador - Setup Inicial
echo ====================================

echo.
echo [1/3] Instalando dependencias Python...
pip install -r requirements.txt

echo.
echo [2/3] Verificando Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Ollama nao encontrado. Instale de: https://ollama.com/
    pause
    exit /b 1
)

echo.
echo [3/3] Baixando modelos...
echo Baixando gemma3:4b (pode levar alguns minutos)...
ollama pull gemma3:4b
echo Baixando phi4-mini (pode levar alguns minutos)...
ollama pull phi4-mini
echo Baixando qwen3:8b (opcional - pressione Ctrl+C para pular)...
ollama pull qwen3:8b

echo.
echo ====================================
echo  Setup concluido!
echo.
echo Para iniciar o Ollama: ollama serve
echo Para rodar o EDUcador: python run.py "sua pergunta"
echo ====================================
pause
