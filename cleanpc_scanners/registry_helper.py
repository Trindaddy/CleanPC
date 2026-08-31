"""
Leitor e analisador do Registro do Windows para programas instalados e chaves de desinstalação.
"""

import os
import winreg
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class InstalledAppInfo:
    display_name: str
    publisher: Optional[str] = None
    install_location: Optional[str] = None
    uninstall_string: Optional[str] = None
    display_version: Optional[str] = None
    registry_key_name: str = ""
    source_hive: str = ""


class RegistryHelper:
    """Extrai com precisão a lista de todos os programas registrados no Windows."""

    UNINSTALL_PATHS = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM_WOW64"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKCU")
    ]

    @classmethod
    def get_installed_programs(cls) -> List[InstalledAppInfo]:
        programs: List[InstalledAppInfo] = []
        seen_names: Set[str] = set()

        for hive, subkey_path, hive_name in cls.UNINSTALL_PATHS:
            try:
                with winreg.OpenKey(hive, subkey_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as root_key:
                    num_subkeys, _, _ = winreg.QueryInfoKey(root_key)
                    for i in range(num_subkeys):
                        try:
                            key_name = winreg.EnumKey(root_key, i)
                            with winreg.OpenKey(root_key, key_name, 0, winreg.KEY_READ) as app_key:
                                display_name = cls._safe_read_reg_value(app_key, "DisplayName")
                                if not display_name:
                                    continue

                                # Normaliza para evitar duplicatas entre hives 32/64
                                clean_name = display_name.strip()
                                if clean_name.lower() in seen_names:
                                    continue

                                seen_names.add(clean_name.lower())
                                publisher = cls._safe_read_reg_value(app_key, "Publisher")
                                install_loc = cls._safe_read_reg_value(app_key, "InstallLocation")
                                uninstall_str = cls._safe_read_reg_value(app_key, "UninstallString")
                                version = cls._safe_read_reg_value(app_key, "DisplayVersion")

                                programs.append(InstalledAppInfo(
                                    display_name=clean_name,
                                    publisher=publisher.strip() if publisher else None,
                                    install_location=install_loc.strip() if install_loc else None,
                                    uninstall_string=uninstall_str.strip() if uninstall_str else None,
                                    display_version=version.strip() if version else None,
                                    registry_key_name=key_name,
                                    source_hive=hive_name
                                ))
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue

        return programs

    @staticmethod
    def _safe_read_reg_value(key, value_name: str) -> Optional[str]:
        try:
            val, _ = winreg.QueryValueEx(key, value_name)
            return str(val)
        except (OSError, FileNotFoundError):
            return None

    @classmethod
    def build_installed_software_tokens(cls) -> Set[str]:
        """
        Gera um conjunto de tokens normalizados (nomes de programas, publishers, pastas)
        para validação cruzada rápida com o sistema de arquivos.
        """
        programs = cls.get_installed_programs()
        tokens: Set[str] = set()

        # Adiciona nomes essenciais da Microsoft e do Windows
        system_vendors = {
            "microsoft", "windows", "dotnet", "directx", "powershell", "system",
            "intel", "amd", "nvidia", "realtek", "qualcomm", "common files",
            "windows nt", "windows defender", "windows mail", "windows media player",
            "windows security", "cleanpc", "megalimpador"
        }
        tokens.update(system_vendors)

        for p in programs:
            # Nome do programa em minúsculas
            name_lower = p.display_name.lower()
            tokens.add(name_lower)

            # Quebra em palavras-chave relevantes (> 2 caracteres)
            for word in name_lower.replace("-", " ").replace("_", " ").split():
                if len(word) >= 3 and not word.isdigit():
                    tokens.add(word)

            if p.publisher:
                pub_lower = p.publisher.lower()
                tokens.add(pub_lower)
                for word in pub_lower.replace("-", " ").replace("_", " ").split():
                    if len(word) >= 3 and not word.isdigit():
                        tokens.add(word)

            if p.install_location:
                try:
                    loc_name = Path(p.install_location).name.lower()
                    if loc_name:
                        tokens.add(loc_name)
                except Exception:
                    pass

        return tokens
