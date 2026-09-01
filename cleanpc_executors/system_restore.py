"""
Gerenciador de Ponto de Restauração do Windows (System Restore Point).
Invoca comandos nativos do PowerShell para criar pontos de restauração de segurança antes de limpezas.
"""

import subprocess
from typing import Tuple

from cleanpc_core.logger import app_logger


class SystemRestoreManager:
    @staticmethod
    def create_restore_point(description: str = "Ponto de Segurança CleanPC") -> Tuple[bool, str]:
        """
        Cria um Ponto de Restauração do Sistema no Windows via PowerShell.
        Requer privilégios de Administrador.
        """
        safe_desc = description.replace('"', '').replace("'", "")
        cmd = f'Checkpoint-Computer -Description "{safe_desc}" -RestorePointType "MODIFY_SETTINGS"'

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=45
            )

            if result.returncode == 0:
                msg = f"Ponto de Restauração '{safe_desc}' criado com sucesso no Windows!"
                app_logger.info(msg)
                app_logger.log_event("create_restore_point_success", {"description": safe_desc}, status="success")
                return True, msg
            else:
                err_text = result.stderr.strip() or result.stdout.strip()
                # Tratamento amigável de limitação de 24 horas do Windows
                if "0x80070422" in err_text or "disabled" in err_text.lower():
                    msg = "A Proteção do Sistema (Pontos de Restauração) está desativada no seu Windows."
                elif "limit" in err_text.lower() or "frequency" in err_text.lower():
                    msg = "O Windows já criou um ponto de restauração recentemente nas últimas 24 horas (limite nativo do SO atingido)."
                else:
                    msg = f"Aviso: Não foi possível criar o Ponto de Restauração (execute como Administrador se desejar): {err_text}"
                
                app_logger.warning(msg)
                return False, msg

        except Exception as e:
            err_msg = f"Erro ao invocar Checkpoint-Computer: {e}"
            app_logger.error(err_msg)
            return False, err_msg
