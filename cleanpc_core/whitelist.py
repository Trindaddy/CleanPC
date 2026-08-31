"""
Sistema de Whitelist Estrita para Proteção de Pastas e Arquivos Críticos do Windows.
NUNCA permite que caminhos essenciais do sistema operacional sejam excluídos ou modificados.
"""

import os
from pathlib import Path
from typing import List, Set

def _get_system_drive() -> str:
    return os.environ.get("SystemDrive", "C:")

def _get_windir() -> str:
    return os.environ.get("SystemRoot", os.environ.get("windir", f"{_get_system_drive()}\\Windows"))

def _get_program_files() -> str:
    return os.environ.get("ProgramFiles", f"{_get_system_drive()}\\Program Files")

def _get_program_files_x86() -> str:
    return os.environ.get("ProgramFiles(x86)", f"{_get_system_drive()}\\Program Files (x86)")

def _get_program_data() -> str:
    return os.environ.get("ProgramData", f"{_get_system_drive()}\\ProgramData")

def _get_user_profile() -> str:
    return os.environ.get("USERPROFILE", os.path.expanduser("~"))

# Diretórios raízes absolutamente protegidos
PROTECTED_EXACT_OR_ANCESTOR_PATHS: List[str] = [
    _get_windir(),
    f"{_get_windir()}\\System32",
    f"{_get_windir()}\\SysWOW64",
    f"{_get_windir()}\\WinSxS",
    f"{_get_windir()}\\Boot",
    f"{_get_windir()}\\SystemApps",
    f"{_get_windir()}\\assembly",
    f"{_get_windir()}\\Microsoft.NET",
    f"{_get_windir()}\\servicing",
    f"{_get_windir()}\\system",
    f"{_get_program_files()}\\Windows Defender",
    f"{_get_program_files()}\\WindowsApps",
    f"{_get_program_files()}\\Common Files\\Microsoft Shared",
    f"{_get_program_files_x86()}\\Common Files\\Microsoft Shared",
    f"{_get_program_data()}\\Microsoft\\Windows",
    f"{_get_program_data()}\\Microsoft\\Windows Defender",
    f"{_get_program_data()}\\Microsoft\\Crypto",
    # Pastas pessoais protegidas
    f"{_get_user_profile()}\\Desktop",
    f"{_get_user_profile()}\\Documents",
    f"{_get_user_profile()}\\Pictures",
    f"{_get_user_profile()}\\Music",
    f"{_get_user_profile()}\\Videos",
    f"{_get_user_profile()}\\OneDrive",
    # AppData do sistema
    f"{_get_user_profile()}\\AppData\\Roaming\\Microsoft\\Windows",
    f"{_get_user_profile()}\\AppData\\Local\\Microsoft\\Windows"
]

# Nomes de arquivos de sistema que nunca devem ser tocados
PROTECTED_FILENAMES: Set[str] = {
    "bootmgr",
    "bootnxt",
    "bootstat.dat",
    "ntldr",
    "ntdetect.com",
    "pagefile.sys",
    "swapfile.sys",
    "hiberfil.sys",
    "dumpstack.log",
    "desktop.ini",
    "ntuser.dat",
    "ntuser.ini",
    "usrclass.dat"
}

def normalize_path(path: str | Path) -> str:
    """Normaliza o caminho para comparação canônica em minúsculas."""
    try:
        p = Path(path).resolve()
        return str(p).lower().rstrip("\\/")
    except Exception:
        return str(path).lower().rstrip("\\/")

def is_whitelisted(path: str | Path) -> bool:
    """
    Verifica se um caminho está protegido pela Whitelist.
    Retorna True se o caminho for protegido e NUNCA deva ser tocado.
    """
    if not path:
        return True

    norm_target = normalize_path(path)
    file_name = Path(norm_target).name.lower()

    # Verifica nomes de arquivo protegidos
    if file_name in PROTECTED_FILENAMES:
        return True

    # Verifica se o caminho é igual ou ancestral de uma pasta protegida
    for protected in PROTECTED_EXACT_OR_ANCESTOR_PATHS:
        norm_protected = normalize_path(protected)
        # Se for o mesmo caminho
        if norm_target == norm_protected:
            return True
        # Se o alvo for pai da pasta protegida (ex.: C:\Windows tentar apagar C:\Windows\System32)
        if norm_protected.startswith(norm_target + "\\"):
            return True
        # Se o alvo estiver DENTRO de uma pasta de sistema estrita (exceto Temp permitido)
        # Nota: C:\Windows\Temp é explicitamente tratado como exceção controlada no scanner de Temp
        if norm_target.startswith(norm_protected + "\\"):
            # Exceção especial: C:\Windows\Temp ou C:\Windows\Prefetch sob regras do scanner
            if norm_target.startswith(normalize_path(f"{_get_windir()}\\temp")):
                return False
            if norm_target.startswith(normalize_path(f"{_get_windir()}\\prefetch")):
                return False
            if norm_target.startswith(normalize_path(f"{_get_windir()}\\softwaredistribution\\download")):
                return False
            return True

    # Protege a raiz de qualquer drive (ex.: C:\, D:\)
    if len(norm_target) <= 3 and norm_target.endswith(":"):
        return True

    return False
