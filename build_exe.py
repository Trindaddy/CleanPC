"""
Script de Compilação Automatizada do CleanPC em Executável Standalone (.exe).
Gera um único executável portátil em dist/CleanPC.exe sem necessidade de Python instalado.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Configura encoding UTF-8 seguro
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).parent.resolve()
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"


def build_executable():
    print("=" * 60)
    print("  🔨 INICIANDO COMPILAÇÃO DO CLEANPC (.EXE PORTÁTIL)")
    print("=" * 60)

    # Coleta o diretório de dados do customtkinter
    try:
        import customtkinter
        ctk_path = Path(customtkinter.__file__).parent
        add_data_ctk = f"--add-data={ctk_path}{os.pathsep}customtkinter"
    except ImportError:
        add_data_ctk = "--collect-all=customtkinter"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--name=CleanPC",
        add_data_ctk,
        "--collect-all=rich",
        "--collect-all=customtkinter",
        "--hidden-import=cleanpc_core",
        "--hidden-import=cleanpc_scanners",
        "--hidden-import=cleanpc_executors",
        "--hidden-import=cleanpc_reports",
        "--hidden-import=cleanpc_ui",
        str(BASE_DIR / "cleanpc.py")
    ]

    print(f"\nComando de build:\n{' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=str(BASE_DIR))

    if result.returncode == 0:
        exe_path = DIST_DIR / "CleanPC.exe"
        print("\n" + "=" * 60)
        print("  ✅ COMPILAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"  📦 Executável standalone gerado em: {exe_path}")
        if exe_path.exists():
            size_mb = round(exe_path.stat().st_size / (1024 * 1024), 2)
            print(f"  📏 Tamanho do arquivo: {size_mb} MB")
        print("=" * 60 + "\n")
    else:
        print("\n❌ Falha na compilação do executável.\n")


if __name__ == "__main__":
    build_executable()
