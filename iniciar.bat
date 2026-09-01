@echo off
title CleanPC — Mega Limpador e Otimizador
echo ========================================================
echo   Iniciando CleanPC...
echo ========================================================
echo.

:: Verifica se Python esta instalado
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Python nao foi encontrado no sistema.
    echo Por favor, instale o Python em https://www.python.org/downloads/
    echo e lembre-se de marcar "Add python.exe to PATH".
    pause
    exit /b
)

:: Se nao houver venv, cria e instala dependencias automaticamente
if not exist "venv" (
    echo Criando ambiente virtual e instalando dependencias (apenas na 1a execucao)...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

:: Executa a ferramenta
python cleanpc.py

pause
