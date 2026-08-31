"""
Scanner de Cache de Navegadores (Chrome, Edge, Firefox, Brave, Opera).
ESTRITAMENTE SEGURO: Varre apenas caches puros de renderização e mídia.
NUNCA toca em senhas, cookies, histórico, favoritos ou sessões de usuário.
"""

import os
from pathlib import Path
from typing import Callable, List, Optional

from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import Finding, ScanCategory
from cleanpc_core.whitelist import is_whitelisted
from .base import BaseScanner
from .utils import get_dir_size_and_meta


class BrowserCacheScanner(BaseScanner):
    @property
    def category(self) -> ScanCategory:
        return ScanCategory.BROWSER_CACHE

    @property
    def name(self) -> str:
        return "Cache de Navegadores"

    @property
    def description(self) -> str:
        return "Localiza caches de mídia, renderização e bytecode de Chrome, Edge, Firefox, Brave e Opera"

    def _get_chromium_cache_paths(self, base_user_data: Path, browser_name: str) -> List[tuple[Path, str]]:
        cache_folders = []
        if not base_user_data.exists():
            return cache_folders

        try:
            # Perfis Chromium (Default, Profile 1, Profile 2, etc.)
            for item in base_user_data.iterdir():
                if item.is_dir() and (item.name == "Default" or item.name.startswith("Profile ")):
                    # Subpastas de cache estritas
                    candidate_caches = [
                        (item / "Cache", "Cache Geral"),
                        (item / "Code Cache", "Bytecode Cache"),
                        (item / "GPUCache", "GPU Shader Cache"),
                        (item / "Service Worker" / "CacheStorage", "Service Worker Cache"),
                        (item / "Service Worker" / "ScriptCache", "Script Cache")
                    ]
                    for path, c_type in candidate_caches:
                        if path.exists() and path.is_dir():
                            cache_folders.append((path, f"{browser_name} ({item.name}) - {c_type}"))
        except (PermissionError, OSError):
            pass

        return cache_folders

    def _get_firefox_cache_paths(self, local_mozilla_profiles: Path) -> List[tuple[Path, str]]:
        cache_folders = []
        if not local_mozilla_profiles.exists():
            return cache_folders

        try:
            for item in local_mozilla_profiles.iterdir():
                if item.is_dir():
                    cache2 = item / "cache2"
                    if cache2.exists() and cache2.is_dir():
                        cache_folders.append((cache2, f"Mozilla Firefox ({item.name}) - Cache2"))
        except (PermissionError, OSError):
            pass

        return cache_folders

    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        findings: List[Finding] = []
        local_app_data = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")))

        targets_to_check = [
            ("Google Chrome", local_app_data / "Google" / "Chrome" / "User Data", "chromium"),
            ("Microsoft Edge", local_app_data / "Microsoft" / "Edge" / "User Data", "chromium"),
            ("Brave Browser", local_app_data / "BraveSoftware" / "Brave-Browser" / "User Data", "chromium"),
            ("Opera Stable", local_app_data / "Opera Software" / "Opera Stable", "direct"),
            ("Opera GX", local_app_data / "Opera Software" / "Opera GX Stable", "direct"),
            ("Mozilla Firefox", local_app_data / "Mozilla" / "Firefox" / "Profiles", "firefox")
        ]

        discovered_caches: List[tuple[Path, str, str]] = []

        for b_name, b_path, b_kind in targets_to_check:
            if b_kind == "chromium":
                for c_path, desc in self._get_chromium_cache_paths(b_path, b_name):
                    discovered_caches.append((c_path, desc, b_name))
            elif b_kind == "firefox":
                for c_path, desc in self._get_firefox_cache_paths(b_path):
                    discovered_caches.append((c_path, desc, b_name))
            elif b_kind == "direct":
                for sub in ["Cache", "GPUCache", "Code Cache"]:
                    c_path = b_path / sub
                    if c_path.exists() and c_path.is_dir():
                        discovered_caches.append((c_path, f"{b_name} - {sub}", b_name))

        total_caches = len(discovered_caches)
        for idx, (folder, desc, browser_name) in enumerate(discovered_caches):
            if progress_callback:
                progress_callback(f"Analisando cache: {desc}", idx + 1, total_caches)

            if is_whitelisted(folder):
                continue

            size, count, last_mod, _ = get_dir_size_and_meta(folder)
            if size > 0:
                confidence, reason = RiskClassifier.classify_browser_cache(browser_name, desc)
                findings.append(Finding(
                    category=self.category,
                    path=str(folder.resolve()),
                    size_bytes=size,
                    confidence=confidence,
                    reason=reason,
                    last_modified=last_mod,
                    related_software=browser_name,
                    is_directory=True,
                    file_count=count,
                    metadata={"browser": browser_name, "cache_description": desc}
                ))

        return findings
