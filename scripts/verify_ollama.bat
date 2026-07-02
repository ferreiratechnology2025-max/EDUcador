@echo off
title EDUcador - Verificacao do Ollama
echo ====================================
echo  Verificando instalacao do Ollama
echo ====================================
echo.

where ollama >nul 2>&1
if "%ERRORLEVEL%" NEQ "0" (
    echo [ERRO] Ollama nao encontrado.
    echo.
    echo Para instalar, acesse: https://ollama.com/
    echo.
    pause
    exit /b 1
)

echo [OK] Ollama encontrado em:
where ollama
echo.

ollama --version
echo.

echo ====================================
echo  Verificando modelos...
echo ====================================
echo.

set MODELS=gemma3:4b phi4-mini llama3.2-vision

for %%m in (%MODELS%) do (
    ollama show %%m >nul 2>&1
    if "%ERRORLEVEL%" EQU "0" (
        echo [OK] %%m instalado
    ) else (
        echo [..] %%m nao encontrado
    )
)

echo.
echo ====================================
echo  Verificacao concluida!
echo ====================================
pause
