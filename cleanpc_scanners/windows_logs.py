"""
Scanner de Logs de Atualização e Manutenção do Windows (CBS, DISM e Setup).
Identifica logs antigos de instalação do Windows Update que frequentemente acumulam gigabytes no disco C:.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import Finding, ScanCategory
from cleanpc_core.whitelist import is_whitelisted
from .base import BaseScanner


class WindowsLogsScanner(BaseScanner):
    @property
    def category(self) -> ScanCategory:
        return ScanCategory.WINDOWS_LOGS

    @property
    def name(self) -> str:
        return "Logs de Atualização do Windows (CBS / DISM)"

    @property
    def description(self) -> str:
        return "Localiza logs de histórico do Windows Update e CBS persistidos (C:\\Windows\\Logs\\CBS)"

    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        findings: List[Finding] = []

        win_dir = Path(os.environ.get("SystemRoot", "C:\\Windows"))
        cbs_dir = win_dir / "Logs" / "CBS"
        dism_dir = win_dir / "Logs" / "DISM"
        panther_dir = win_dir / "Panther"

        # 1. Logs persistidos do CBS (CbsPersist_*.log e CbsPersist_*.cab)
        if cbs_dir.exists():
            if progress_callback:
                progress_callback("Analisando logs CBS do Windows Update...", 1, 3)

            try:
                for file_path in cbs_dir.glob("CbsPersist_*.log"):
                    if is_whitelisted(file_path):
                        continue
                    try:
                        st = file_path.stat()
                        last_mod = datetime.fromtimestamp(st.st_mtime)
                        confidence, reason = RiskClassifier.classify_windows_log("CBS Update Log Persistido", last_mod)
                        findings.append(Finding(
                            category=self.category,
                            path=str(file_path.resolve()),
                            size_bytes=st.st_size,
                            confidence=confidence,
                            reason=reason,
                            last_modified=last_mod,
                            is_directory=False,
                            file_count=1,
                            metadata={"log_type": "CBS_Persist"}
                        ))
                    except (PermissionError, OSError):
                        continue

                for file_path in cbs_dir.glob("CbsPersist_*.cab"):
                    if is_whitelisted(file_path):
                        continue
                    try:
                        st = file_path.stat()
                        last_mod = datetime.fromtimestamp(st.st_mtime)
                        confidence, reason = RiskClassifier.classify_windows_log("CBS CAB Compactado Antigo", last_mod)
                        findings.append(Finding(
                            category=self.category,
                            path=str(file_path.resolve()),
                            size_bytes=st.st_size,
                            confidence=confidence,
                            reason=reason,
                            last_modified=last_mod,
                            is_directory=False,
                            file_count=1,
                            metadata={"log_type": "CBS_CAB"}
                        ))
                    except (PermissionError, OSError):
                        continue
            except (PermissionError, OSError):
                pass

        # 2. Logs do DISM
        if dism_dir.exists() and progress_callback:
            progress_callback("Verificando logs DISM...", 2, 3)
            try:
                dism_log = dism_dir / "dism.log"
                if dism_log.exists() and not is_whitelisted(dism_log):
                    st = dism_log.stat()
                    # Apenas se tiver tamanho considerável (> 10MB)
                    if st.st_size > 10 * 1024 * 1024:
                        last_mod = datetime.fromtimestamp(st.st_mtime)
                        confidence, reason = RiskClassifier.classify_windows_log("DISM Log Grande", last_mod)
                        findings.append(Finding(
                            category=self.category,
                            path=str(dism_log.resolve()),
                            size_bytes=st.st_size,
                            confidence=confidence,
                            reason=reason,
                            last_modified=last_mod,
                            is_directory=False,
                            file_count=1,
                            metadata={"log_type": "DISM_Log"}
                        ))
            except (PermissionError, OSError):
                pass

        return findings
