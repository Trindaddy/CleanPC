"""
Executor de Otimizações de Desempenho e Manutenção (Startup & SSD TRIM).
"""

import json
import subprocess
import winreg
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from cleanpc_core.config import LOGS_DIR, ensure_directories
from cleanpc_core.logger import app_logger
from cleanpc_core.models import Finding


class OptimizerExecutor:
    """Executa ações de otimização de sistema de forma segura e com backup prévio."""

    def __init__(self):
        ensure_directories()
        self.backup_dir = LOGS_DIR / "optimizations_backup"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def disable_startup_item(self, finding: Finding) -> Tuple[bool, Optional[str]]:
        """
        Desabilita um item de inicialização do registro fazendo backup prévio do valor.
        """
        startup_name = finding.metadata.get("startup_name")
        location = finding.metadata.get("location", "HKCU Run")
        command = finding.metadata.get("command", "")

        if not startup_name:
            return False, "Nome do item de inicialização não especificado."

        hive = winreg.HKEY_CURRENT_USER if "HKCU" in location else winreg.HKEY_LOCAL_MACHINE
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        if "WOW64" in location or "32-bit" in location:
            subkey = r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"

        # 1. Salva backup em JSON
        backup_record = {
            "timestamp": datetime.now().isoformat(),
            "name": startup_name,
            "command": command,
            "location": location,
            "subkey": subkey
        }
        backup_file = self.backup_dir / f"startup_backup_{startup_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(backup_record, f, indent=2)
        except Exception as e:
            return False, f"Falha ao salvar backup do registro: {e}"

        # 2. Remove o valor do Registro
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as key:
                winreg.DeleteValue(key, startup_name)
            
            app_logger.info(f"Item de inicialização '{startup_name}' desabilitado com sucesso. Backup: {backup_file.name}")
            app_logger.log_event("disable_startup_success", backup_record, status="success")
            return True, None
        except Exception as e:
            err_msg = f"Falha ao desabilitar item no Registro: {e}"
            app_logger.error(err_msg)
            return False, err_msg

    def execute_trim_optimization(self, drive_letter: str = "C") -> Tuple[bool, str]:
        """
        Executa comando nativo do Windows para otimização e TRIM de SSD.
        """
        clean_drive = drive_letter.rstrip(":\\/")
        cmd = f"Optimize-Volume -DriveLetter {clean_drive} -ReTrim -Verbose"
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                msg = f"Comando TRIM executado com sucesso na unidade {clean_drive}:. O Windows reotimizou os blocos livres."
                app_logger.info(msg)
                app_logger.log_event("trim_optimization_success", {"drive": clean_drive, "output": result.stdout}, status="success")
                return True, msg
            else:
                err_msg = f"Erro ao executar TRIM na unidade {clean_drive}: {result.stderr.strip()}"
                app_logger.warning(err_msg)
                return False, err_msg
        except Exception as e:
            err_msg = f"Exceção ao invocar Optimize-Volume: {e}"
            app_logger.error(err_msg)
            return False, err_msg
