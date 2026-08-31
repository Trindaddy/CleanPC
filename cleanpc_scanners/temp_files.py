r"""
Scanner de Arquivos Temporários do Sistema e Usuário (%TEMP%, C:\Windows\Temp, etc.).
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import Finding, ScanCategory
from cleanpc_core.whitelist import is_whitelisted
from .base import BaseScanner
from .utils import get_dir_size_and_meta


class TempFilesScanner(BaseScanner):
    @property
    def category(self) -> ScanCategory:
        return ScanCategory.TEMP_FILES

    @property
    def name(self) -> str:
        return "Arquivos Temporários"

    @property
    def description(self) -> str:
        return "Varre pastas temporárias de usuários e do sistema (%TEMP%, Windows\\Temp)"

    def _get_target_directories(self) -> List[Path]:
        targets = []
        # User Temp
        env_temp = os.environ.get("TEMP")
        if env_temp and Path(env_temp).exists():
            targets.append(Path(env_temp))

        env_tmp = os.environ.get("TMP")
        if env_tmp and Path(env_tmp).exists() and Path(env_tmp) not in targets:
            targets.append(Path(env_tmp))

        # Windows Temp
        win_dir = os.environ.get("SystemRoot", "C:\\Windows")
        win_temp = Path(win_dir) / "Temp"
        if win_temp.exists() and win_temp not in targets:
            targets.append(win_temp)

        # Windows SoftwareDistribution Download (atualizações antigas já baixadas)
        win_soft_dist = Path(win_dir) / "SoftwareDistribution" / "Download"
        if win_soft_dist.exists():
            targets.append(win_soft_dist)

        return targets

    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        findings: List[Finding] = []
        targets = self._get_target_directories()

        for idx, folder in enumerate(targets):
            if progress_callback:
                progress_callback(f"Escaneando pasta temporária: {folder.name}", idx + 1, len(targets))

            if not folder.exists() or not folder.is_dir():
                continue

            try:
                # Itera diretamente sobre os itens de primeiro nível da pasta temporária
                entries = list(folder.iterdir())
            except (PermissionError, OSError):
                continue

            for item in entries:
                if is_whitelisted(item):
                    continue

                try:
                    if item.is_dir():
                        size, count, last_mod, _ = get_dir_size_and_meta(item)
                        if count == 0 and size == 0:
                            # Diretório temporário vazio
                            confidence, reason = RiskClassifier.classify_temp_file(str(item), last_mod, is_directory=True)
                            findings.append(Finding(
                                category=self.category,
                                path=str(item.resolve()),
                                size_bytes=0,
                                confidence=confidence,
                                reason=reason + " (Pasta temporária vazia)",
                                last_modified=last_mod,
                                is_directory=True,
                                file_count=0
                            ))
                        elif size > 0:
                            confidence, reason = RiskClassifier.classify_temp_file(str(item), last_mod, is_directory=True)
                            findings.append(Finding(
                                category=self.category,
                                path=str(item.resolve()),
                                size_bytes=size,
                                confidence=confidence,
                                reason=reason,
                                last_modified=last_mod,
                                is_directory=True,
                                file_count=count
                            ))
                    elif item.is_file():
                        stat = item.stat()
                        last_mod = datetime.fromtimestamp(stat.st_mtime)
                        confidence, reason = RiskClassifier.classify_temp_file(str(item), last_mod, is_directory=False)
                        findings.append(Finding(
                            category=self.category,
                            path=str(item.resolve()),
                            size_bytes=stat.st_size,
                            confidence=confidence,
                            reason=reason,
                            last_modified=last_mod,
                            is_directory=False,
                            file_count=1
                        ))
                except (PermissionError, FileNotFoundError, OSError):
                    continue

        return findings
