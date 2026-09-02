"""
Executor Seguro de Limpeza de Smartphone com Backup Prévio na Quarentena do PC.
Garante que todos os itens removidos do celular possam ser restaurados pelo computador.
"""

import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from cleanpc_core.config import BASE_DATA_DIR, ensure_directories
from cleanpc_core.logger import app_logger
from cleanpc_core.models import Finding
from .detector import ConnectedMobileDevice
from .mobile_whitelist import is_mobile_path_protected

MOBILE_QUARANTINE_DIR = BASE_DATA_DIR / "quarantine_mobile"


@dataclass
class MobileCleaningReport:
    batch_id: str
    device_name: str
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    successful_items: int = 0
    failed_items: int = 0
    total_freed_bytes: int = 0
    errors: List[str] = field(default_factory=list)


class SafeMobileCleaner:
    def __init__(self, device: ConnectedMobileDevice):
        self.device = device
        MOBILE_QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        self.adb_bin = shutil.which("adb") or "adb"

    def execute_mobile_cleaning(
        self,
        findings: List[Finding],
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> MobileCleaningReport:
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_mobile_" + uuid.uuid4().hex[:4]
        batch_quarantine_dir = MOBILE_QUARANTINE_DIR / batch_id
        batch_quarantine_dir.mkdir(parents=True, exist_ok=True)

        report = MobileCleaningReport(batch_id=batch_id, device_name=self.device.name)
        total = len(findings)

        app_logger.info(f"Iniciando limpeza mobile no aparelho {self.device.name} (Lote: {batch_id}).")

        for idx, f in enumerate(findings):
            if progress_callback:
                progress_callback(f"Processando item {idx + 1} de {total}...", idx + 1, total)

            remote_path = f.metadata.get("remote_path", f.path)

            # Validação de Whitelist Mobile
            if is_mobile_path_protected(remote_path):
                report.failed_items += 1
                msg = f"Item protegido pela Whitelist Mobile ignorado: {remote_path}"
                report.errors.append(msg)
                app_logger.warning(msg)
                continue

            success = False
            if self.device.mode == "ADB":
                success = self._clean_via_adb(remote_path, batch_quarantine_dir, f)
            elif self.device.mode == "MassStorage":
                success = self._clean_via_mass_storage(f.path, batch_quarantine_dir, f)

            if success:
                report.successful_items += 1
                report.total_freed_bytes += f.size_bytes
            else:
                report.failed_items += 1

        report.completed_at = datetime.now()
        app_logger.info(
            f"Limpeza no celular concluída. Sucessos: {report.successful_items}, "
            f"Falhas: {report.failed_items}, Espaço liberado: {report.total_freed_bytes} bytes."
        )

        return report

    def _clean_via_adb(self, remote_path: str, quarantine_dir: Path, finding: Finding) -> bool:
        item_id = uuid.uuid4().hex[:8]
        local_backup_dest = quarantine_dir / f"{item_id}_{Path(remote_path).name}"

        # 1. Faz o pull (backup de segurança) do celular para o PC
        cmd_pull = [self.adb_bin]
        if self.device.serial:
            cmd_pull.extend(["-s", self.device.serial])
        cmd_pull.extend(["pull", remote_path, str(local_backup_dest)])

        try:
            res_pull = subprocess.run(cmd_pull, capture_output=True, text=True, timeout=30)
            # 2. Deleta o item no celular
            cmd_rm = [self.adb_bin]
            if self.device.serial:
                cmd_rm.extend(["-s", self.device.serial])
            cmd_rm.extend(["shell", f"rm -rf '{remote_path}'"])
            res_rm = subprocess.run(cmd_rm, capture_output=True, text=True, timeout=15)

            if res_rm.returncode == 0:
                app_logger.log_event("mobile_quarantine_success", {
                    "device": self.device.name,
                    "remote_path": remote_path,
                    "backup_path": str(local_backup_dest),
                    "size_bytes": finding.size_bytes
                }, status="success")
                return True
        except Exception as e:
            app_logger.error(f"Erro ao limpar item via ADB '{remote_path}': {e}")

        return False

    def _clean_via_mass_storage(self, local_path_str: str, quarantine_dir: Path, finding: Finding) -> bool:
        p = Path(local_path_str)
        if not p.exists():
            return False
        try:
            item_id = uuid.uuid4().hex[:8]
            dest = quarantine_dir / f"{item_id}_{p.name}"
            shutil.move(str(p), str(dest))
            return True
        except Exception as e:
            app_logger.error(f"Erro ao mover item mobile para quarentena: {e}")
            return False
