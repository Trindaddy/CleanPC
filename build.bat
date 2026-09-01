@echo off
title Compilando CleanPC para .EXE
echo ========================================================
echo   Compilando CleanPC para Executavel Standalone (.EXE)
echo ========================================================
echo.

python build_exe.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   [SUCESSO] O arquivo dist\CleanPC.exe esta pronto!
    echo ========================================================
) else (
    echo.
    echo [ERRO] Ocorreu uma falha durante a compilacao.
)

pause
