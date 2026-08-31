"""
Scanner da Lixeira do Windows ($Recycle.Bin).
"""

import os
from pathlib import Path
from typing import Callable, List, Optional
import psutil

from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import Finding, ScanCategory
from .base import BaseScanner
from .utils import get_dir_size_and_meta


class RecycleBinScanner(BaseScanner):
    @property
    def category(self) -> ScanCategory:
        return ScanCategory.RECYCLE_BIN

    @property
    def name(self) -> str:
        return "Lixeira do Windows"

    @property
    def description(self) -> str:
        return "Inspeciona o volume de arquivos descartados na Lixeira em todas as unidades de disco"

    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        findings: List[Finding] = []
        drives = []

        try:
            partitions = psutil.disk_partitions(all=False)
            for p in partitions:
                if "fixed" in p.opts.lower() or p.fstype.lower() in ("ntfs", "fat32", "exfat"):
                    drives.append(p.mountpoint)
        except Exception:
            drives = ["C:\\"]

        for idx, drive in enumerate(drives):
            if progress_callback:
                progress_callback(f"Verificando Lixeira na unidade {drive}", idx + 1, len(drives))

            recycle_path = Path(drive) / "$Recycle.Bin"
            if not recycle_path.exists():
                continue

            try:
                # Percorre as pastas de SID de usuário dentro de $Recycle.Bin
                for sid_folder in recycle_path.iterdir():
                    if sid_folder.is_dir():
                        size, count, last_mod, _ = get_dir_size_and_meta(sid_folder)
                        if count > 0 or size > 0:
                            confidence, reason = RiskClassifier.classify_recycle_bin(count, size)
                            findings.append(Finding(
                                category=self.category,
                                path=str(sid_folder.resolve()),
                                size_bytes=size,
                                confidence=confidence,
                                reason=reason,
                                last_modified=last_mod,
                                is_directory=True,
                                file_count=count,
                                metadata={"drive": drive, "sid_folder": sid_folder.name}
                            ))
            except (PermissionError, OSError):
                continue

        return findings
