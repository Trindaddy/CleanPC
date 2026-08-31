"""
Testes unitários para o sistema de Whitelist estrita.
"""

import os
from pathlib import Path
from cleanpc_core.whitelist import is_whitelisted, normalize_path


def test_windows_system32_is_protected():
    windir = os.environ.get("SystemRoot", "C:\\Windows")
    assert is_whitelisted(f"{windir}\\System32") is True
    assert is_whitelisted(f"{windir}\\System32\\calc.exe") is True
    assert is_whitelisted(f"{windir}\\System32\\drivers") is True
    assert is_whitelisted(windir) is True


def test_program_files_critical_protected():
    sys_drive = os.environ.get("SystemDrive", "C:")
    assert is_whitelisted(f"{sys_drive}\\Program Files\\Windows Defender") is True
    assert is_whitelisted(f"{sys_drive}\\Program Files\\WindowsApps") is True


def test_user_personal_folders_protected():
    user_home = os.path.expanduser("~")
    assert is_whitelisted(f"{user_home}\\Desktop") is True
    assert is_whitelisted(f"{user_home}\\Documents") is True
    assert is_whitelisted(f"{user_home}\\Pictures") is True


def test_critical_filenames_protected():
    assert is_whitelisted("C:\\pagefile.sys") is True
    assert is_whitelisted("C:\\hiberfil.sys") is True
    assert is_whitelisted("C:\\bootmgr") is True
    assert is_whitelisted("C:\\Users\\User\\NTUSER.DAT") is True


def test_allowed_temp_path_not_whitelisted():
    user_temp = os.environ.get("TEMP", "C:\\Users\\User\\AppData\\Local\\Temp")
    # Subpastas ou arquivos dentro do Temp de usuário NÃO são bloqueados pela whitelist
    test_temp_file = Path(user_temp) / "scratch_cleanpc_test.tmp"
    assert is_whitelisted(test_temp_file) is False
