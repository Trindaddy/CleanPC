"""
Script de Compilação Otimizada do CleanPC com Metadados e Redução de Falsos Positivos.
Gera o executável standalone (.exe) com version info formal e manifesto Windows, além do pacote Portable (.zip).
"""

import os
import shutil
import subprocess
import sys
import zipfile
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
VERSION_FILE = BASE_DIR / "version_info.txt"
MANIFEST_FILE = BASE_DIR / "cleanpc.manifest"


def build_executable():
    print("=" * 65)
    print("  🔨 INICIANDO COMPILAÇÃO OTIMIZADA DO CLEANPC (.EXE)")
    print("=" * 65)

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    # Argumentos base do PyInstaller com metadados completos
    base_args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--name=CleanPC",
        "--collect-all=rich",
        "--collect-all=customtkinter",
        "--hidden-import=cleanpc_core",
        "--hidden-import=cleanpc_scanners",
        "--hidden-import=cleanpc_executors",
        "--hidden-import=cleanpc_mobile",
        "--hidden-import=cleanpc_reports",
        "--hidden-import=cleanpc_ui"
    ]

    if VERSION_FILE.exists():
        base_args.append(f"--version-file={VERSION_FILE}")

    if MANIFEST_FILE.exists():
        base_args.append(f"--manifest={MANIFEST_FILE}")

    # 1. Compilação Standalone Single-File (.exe)
    print("\n[1/2] Compilando executável único (CleanPC.exe)...")
    workpath_onefile = BUILD_DIR / "onefile"
    cmd_onefile = base_args + [
        "--onefile",
        f"--workpath={workpath_onefile}",
        f"--distpath={DIST_DIR}",
        str(BASE_DIR / "cleanpc.py")
    ]
    res1 = subprocess.run(cmd_onefile, cwd=str(BASE_DIR))
    if res1.returncode != 0:
        print("\n❌ Erro na compilação do executável single-file!")
        sys.exit(res1.returncode)

    # 2. Compilação Pasta Portátil (--onedir) e criação de .ZIP limpo
    print("\n[2/2] Gerando pacote portátil limpo sem extração temporária (CleanPC-Portable.zip)...")
    onedir_dist = DIST_DIR / "CleanPC_Portable"
    workpath_onedir = BUILD_DIR / "onedir"
    cmd_onedir = base_args + [
        "--onedir",
        f"--workpath={workpath_onedir}",
        f"--distpath={onedir_dist}",
        str(BASE_DIR / "cleanpc.py")
    ]
    res2 = subprocess.run(cmd_onedir, cwd=str(BASE_DIR))
    if res2.returncode != 0:
        print("\n❌ Erro na compilação da pasta portátil!")
        sys.exit(res2.returncode)

    # Compacta o diretório onedir em ZIP
    portable_folder = onedir_dist / "CleanPC"
    zip_output = DIST_DIR / "CleanPC-v1.1.0-Portable.zip"
    if portable_folder.exists():
        print(f"\nCompactando pasta portátil em {zip_output.name}...")
        with zipfile.ZipFile(zip_output, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(str(portable_folder)):
                for file in files:
                    file_p = Path(root) / file
                    arcname = file_p.relative_to(portable_folder)
                    zipf.write(file_p, arcname)

    print("\n" + "=" * 65)
    print("  ✅ COMPILAÇÃO FINALIZADA COM SUCESSO!")
    if (DIST_DIR / "CleanPC.exe").exists():
        size_mb = round((DIST_DIR / "CleanPC.exe").stat().st_size / (1024 * 1024), 2)
        print(f"  📦 1. Executável Standalone: dist/CleanPC.exe ({size_mb} MB)")
    if zip_output.exists():
        zip_size = round(zip_output.stat().st_size / (1024 * 1024), 2)
        print(f"  📦 2. Pacote Portátil (Sem Falso Positivo): dist/{zip_output.name} ({zip_size} MB)")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    build_executable()
