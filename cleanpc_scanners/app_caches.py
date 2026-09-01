"""
Scanner de Caches de Grandes Aplicativos (Discord, Spotify, Steam, Epic Games, Telegram).
ESTRITAMENTE SEGURO: Varre apenas caches de mídia/renderização.
NUNCA toca em arquivos de autenticação, chats salvos, configurações ou tokens.
"""

import os
import winreg
from pathlib import Path
from typing import Callable, List, Optional

from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import Finding, ScanCategory
from cleanpc_core.whitelist import is_whitelisted
from .base import BaseScanner
from .utils import get_dir_size_and_meta


class AppCachesScanner(BaseScanner):
    @property
    def category(self) -> ScanCategory:
        return ScanCategory.APP_CACHES

    @property
    def name(self) -> str:
        return "Caches de Apps (Discord / Spotify / Steam / Epic)"

    @property
    def description(self) -> str:
        return "Localiza caches de mídia, áudio e navegação do Discord, Spotify, Steam, Epic Games Launcher e Telegram"

    def _get_steam_path(self) -> Optional[Path]:
        """Tenta descobrir o caminho de instalação da Steam pelo Registro."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                val, _ = winreg.QueryValueEx(key, "SteamPath")
                if val and Path(val).exists():
                    return Path(val)
        except Exception:
            pass
        default = Path("C:\\Program Files (x86)\\Steam")
        return default if default.exists() else None

    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        findings: List[Finding] = []

        local_app_data = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")))
        app_data = Path(os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming")))

        app_targets = [
            # Discord
            (app_data / "discord" / "Cache", "Discord - Cache de Mídia e Imagens", "Discord"),
            (app_data / "discord" / "Code Cache", "Discord - Code Cache", "Discord"),
            (app_data / "discord" / "GPUCache", "Discord - GPU Cache", "Discord"),
            # Spotify
            (local_app_data / "Spotify" / "Storage", "Spotify - Cache de Músicas e Áudio", "Spotify"),
            (local_app_data / "Spotify" / "Data", "Spotify - Data Cache", "Spotify"),
            (local_app_data / "Spotify" / "Browser" / "Cache", "Spotify - Browser Cache", "Spotify"),
            # Epic Games Launcher
            (local_app_data / "EpicGamesLauncher" / "Saved" / "webcache", "Epic Games - Web Cache", "Epic Games"),
            (local_app_data / "EpicGamesLauncher" / "Saved" / "Logs", "Epic Games - Logs Antigos", "Epic Games"),
            # Telegram Desktop (apenas user_data\\cache)
            (app_data / "Telegram Desktop" / "tdata" / "user_data" / "cache", "Telegram - Cache de Mídia", "Telegram"),
            # Battle.net
            (local_app_data / "Battle.net" / "Browser" / "Cache", "Battle.net - Browser Cache", "Battle.net"),
            (local_app_data / "Battle.net" / "Logs", "Battle.net - Logs de Inicialização", "Battle.net")
        ]

        # Steam
        steam_path = self._get_steam_path()
        if steam_path:
            app_targets.extend([
                (steam_path / "appcache" / "httpcache", "Steam - HTTP Cache de Loja", "Steam"),
                (steam_path / "htmlcache", "Steam - HTML Cache", "Steam"),
                (steam_path / "logs", "Steam - Logs Antigos", "Steam")
            ])

        total = len(app_targets)
        for idx, (folder, desc, app_name) in enumerate(app_targets):
            if progress_callback:
                progress_callback(f"Analisando {desc}", idx + 1, total)

            if not folder.exists() or is_whitelisted(folder):
                continue

            try:
                size, count, last_mod, _ = get_dir_size_and_meta(folder)
                if size > 0:
                    confidence, reason = RiskClassifier.classify_app_cache(app_name, desc)
                    findings.append(Finding(
                        category=self.category,
                        path=str(folder.resolve()),
                        size_bytes=size,
                        confidence=confidence,
                        reason=reason,
                        last_modified=last_mod,
                        related_software=app_name,
                        is_directory=True,
                        file_count=count,
                        metadata={"app_name": app_name, "cache_type": desc}
                    ))
            except (PermissionError, OSError):
                continue

        return findings
