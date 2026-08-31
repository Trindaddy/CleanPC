"""
Scanner de Dumps de Erro e Relatórios de Falhas do Windows (CrashDumps, Minidumps, WER).
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


class ErrorDumpsScanner(BaseScanner):
    @property
    def category(self) -> ScanCategory:
        return ScanCategory.ERROR_DUMPS

    @property
    def name(self) -> str:
        return "Dumps e Relatórios de Erro"

    @property
    def description(self) -> str:
        return "Localiza relatórios de falha (WER), CrashDumps de aplicativos e Minidumps do Windows"

    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        findings: List[Finding] = []

        local_app_data = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")))
        program_data = Path(os.environ.get("ProgramData", "C:\\ProgramData"))
        win_dir = Path(os.environ.get("SystemRoot", "C:\\Windows"))

        dump_targets = [
            (local_app_data / "CrashDumps", "Crash Dumps de Aplicativos de Usuário"),
            (win_dir / "Minidump", "Minidumps de Tela Azul (BSOD)"),
            (program_data / "Microsoft" / "Windows" / "WER" / "ReportArchive", "Arquivo de Relatórios de Erros (WER)"),
            (program_data / "Microsoft" / "Windows" / "WER" / "ReportQueue", "Fila de Relatórios de Erros (WER)"),
            (program_data / "Microsoft" / "Windows" / "WER" / "Temp", "Arquivos Temporários de Relatórios de Erro")
        ]

        # Arquivo de despejo de memória completo (se existir)
        memory_dmp = win_dir / "MEMORY.DMP"
        if memory_dmp.exists() and not is_whitelisted(memory_dmp):
            try:
                st = memory_dmp.stat()
                last_mod = datetime.fromtimestamp(st.st_mtime)
                confidence, reason = RiskClassifier.classify_error_dump("Memory Dump Completo do Windows", last_mod)
                findings.append(Finding(
                    category=self.category,
                    path=str(memory_dmp.resolve()),
                    size_bytes=st.st_size,
                    confidence=confidence,
                    reason=reason,
                    last_modified=last_mod,
                    is_directory=False,
                    file_count=1
                ))
            except (PermissionError, OSError):
                pass

        total_targets = len(dump_targets)
        for idx, (folder, label) in enumerate(dump_targets):
            if progress_callback:
                progress_callback(f"Verificando {label}", idx + 1, total_targets)

            if not folder.exists() or is_whitelisted(folder):
                continue

            try:
                # Escaneia subpastas/arquivos dentro de cada diretório de relatório
                for item in folder.iterdir():
                    if is_whitelisted(item):
                        continue

                    if item.is_dir():
                        size, count, last_mod, _ = get_dir_size_and_meta(item)
                        if size > 0 or count > 0:
                            confidence, reason = RiskClassifier.classify_error_dump(label, last_mod)
                            findings.append(Finding(
                                category=self.category,
                                path=str(item.resolve()),
                                size_bytes=size,
                                confidence=confidence,
                                reason=reason,
                                last_modified=last_mod,
                                is_directory=True,
                                file_count=count,
                                metadata={"dump_type": label}
                            ))
                    elif item.is_file():
                        st = item.stat()
                        last_mod = datetime.fromtimestamp(st.st_mtime)
                        confidence, reason = RiskClassifier.classify_error_dump(label, last_mod)
                        findings.append(Finding(
                            category=self.category,
                            path=str(item.resolve()),
                            size_bytes=st.st_size,
                            confidence=confidence,
                            reason=reason,
                            last_modified=last_mod,
                            is_directory=False,
                            file_count=1,
                            metadata={"dump_type": label}
                        ))
            except (PermissionError, OSError):
                continue

        return findings
