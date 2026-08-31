"""
Scanner de Caches de Ferramentas de Desenvolvimento (npm, pip, yarn, gradle, maven, pnpm, cargo, docker).
"""

import os
from pathlib import Path
from typing import Callable, List, Optional

from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import Finding, ScanCategory
from cleanpc_core.whitelist import is_whitelisted
from .base import BaseScanner
from .utils import get_dir_size_and_meta


class DevCachesScanner(BaseScanner):
    @property
    def category(self) -> ScanCategory:
        return ScanCategory.DEV_CACHES

    @property
    def name(self) -> str:
        return "Caches de Desenvolvimento"

    @property
    def description(self) -> str:
        return "Varre pastas de cache de ferramentas de programação (npm, pip, yarn, pnpm, gradle, cargo)"

    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        findings: List[Finding] = []

        user_home = Path(os.path.expanduser("~"))
        local_app_data = Path(os.environ.get("LOCALAPPDATA", user_home / "AppData" / "Local"))
        app_data = Path(os.environ.get("APPDATA", user_home / "AppData" / "Roaming"))

        dev_targets = [
            ("npm Cache", app_data / "npm-cache", "npm"),
            ("npm Home Cache", user_home / ".npm", "npm"),
            ("pip Cache", local_app_data / "pip" / "cache", "pip"),
            ("pip Home Cache", user_home / ".cache" / "pip", "pip"),
            ("Yarn Cache", local_app_data / "Yarn" / "Cache", "yarn"),
            ("pnpm Store", local_app_data / "pnpm" / "store", "pnpm"),
            ("Gradle Caches", user_home / ".gradle" / "caches", "gradle"),
            ("Cargo Registry Cache", user_home / ".cargo" / "registry" / "cache", "cargo"),
            ("Composer Cache (PHP)", local_app_data / "Composer" / "cache", "composer"),
            ("NuGet Cache (.NET)", user_home / ".nuget" / "packages", "nuget")
        ]

        total = len(dev_targets)
        for idx, (label, target_path, tool_name) in enumerate(dev_targets):
            if progress_callback:
                progress_callback(f"Analisando cache de dev: {label}", idx + 1, total)

            if not target_path.exists() or is_whitelisted(target_path):
                continue

            try:
                size, count, last_mod, _ = get_dir_size_and_meta(target_path)
                if size > 0:
                    confidence, reason = RiskClassifier.classify_dev_cache(label, size)
                    findings.append(Finding(
                        category=self.category,
                        path=str(target_path.resolve()),
                        size_bytes=size,
                        confidence=confidence,
                        reason=reason,
                        last_modified=last_mod,
                        related_software=tool_name,
                        is_directory=True,
                        file_count=count,
                        metadata={"tool": tool_name, "cache_label": label}
                    ))
            except (PermissionError, OSError):
                continue

        return findings
