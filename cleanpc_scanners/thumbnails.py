"""
Scanner do Cache de Miniaturas e Ícones do Windows Explorer (Thumbnails & IconCache).
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import Finding, ScanCategory
from cleanpc_core.whitelist import is_whitelisted
from .base import BaseScanner


class ThumbnailsScanner(BaseScanner):
    @property
    def category(self) -> ScanCategory:
        return ScanCategory.THUMBNAILS

    @property
    def name(self) -> str:
        return "Cache de Miniaturas (Thumbnails)"

    @property
    def description(self) -> str:
        return "Localiza arquivos thumbcache_*.db e iconcache_*.db do Windows Explorer"

    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        findings: List[Finding] = []

        local_app_data = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")))
        explorer_dir = local_app_data / "Microsoft" / "Windows" / "Explorer"

        # IconCache.db na raiz do LocalAppData (Windows legados ou compatibilidade)
        root_icon_cache = local_app_data / "IconCache.db"
        if root_icon_cache.exists() and not is_whitelisted(root_icon_cache):
            try:
                st = root_icon_cache.stat()
                confidence, reason = RiskClassifier.classify_thumbnails()
                findings.append(Finding(
                    category=self.category,
                    path=str(root_icon_cache.resolve()),
                    size_bytes=st.st_size,
                    confidence=confidence,
                    reason=reason,
                    last_modified=datetime.fromtimestamp(st.st_mtime),
                    is_directory=False,
                    file_count=1
                ))
            except (PermissionError, OSError):
                pass

        if not explorer_dir.exists():
            return findings

        try:
            db_files = list(explorer_dir.glob("thumbcache_*.db")) + list(explorer_dir.glob("iconcache_*.db"))
            total = len(db_files)

            for idx, db_file in enumerate(db_files):
                if progress_callback:
                    progress_callback(f"Analisando cache de miniatura: {db_file.name}", idx + 1, total)

                if is_whitelisted(db_file):
                    continue

                try:
                    st = db_file.stat()
                    confidence, reason = RiskClassifier.classify_thumbnails()
                    findings.append(Finding(
                        category=self.category,
                        path=str(db_file.resolve()),
                        size_bytes=st.st_size,
                        confidence=confidence,
                        reason=reason,
                        last_modified=datetime.fromtimestamp(st.st_mtime),
                        is_directory=False,
                        file_count=1,
                        metadata={"filename": db_file.name}
                    ))
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            pass

        return findings
