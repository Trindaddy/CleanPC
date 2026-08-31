"""
Scanner Avançado de Pastas Órfãs de Programas Desinstalados.
Cruza o Registro do Windows com as pastas de Program Files, ProgramData e AppData.
"""

import os
from pathlib import Path
from typing import Callable, List, Optional, Set

from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import Finding, ScanCategory
from cleanpc_core.whitelist import is_whitelisted
from .base import BaseScanner
from .registry_helper import RegistryHelper
from .utils import inspect_folder_for_orphan_analysis


class OrphanFoldersScanner(BaseScanner):
    @property
    def category(self) -> ScanCategory:
        return ScanCategory.ORPHAN_FOLDERS

    @property
    def name(self) -> str:
        return "Pastas Órfãs (Resíduos de Desinstalação)"

    @property
    def description(self) -> str:
        return "Identifica diretórios em Program Files, ProgramData e AppData sem programa correspondente no Registro"

    def _get_search_roots(self) -> List[Path]:
        roots = []
        user_home = Path(os.path.expanduser("~"))

        # Program Files
        pf = os.environ.get("ProgramFiles")
        if pf and Path(pf).exists():
            roots.append(Path(pf))

        # Program Files (x86)
        pf_x86 = os.environ.get("ProgramFiles(x86)")
        if pf_x86 and Path(pf_x86).exists() and Path(pf_x86) not in roots:
            roots.append(Path(pf_x86))

        # ProgramData
        pd = os.environ.get("ProgramData")
        if pd and Path(pd).exists():
            roots.append(Path(pd))

        # AppData Roaming
        app_roaming = os.environ.get("APPDATA")
        if app_roaming and Path(app_roaming).exists():
            roots.append(Path(app_roaming))

        # AppData Local
        app_local = os.environ.get("LOCALAPPDATA")
        if app_local and Path(app_local).exists():
            roots.append(Path(app_local))

        return roots

    def _is_known_active_folder(self, folder_name: str, installed_tokens: Set[str]) -> bool:
        name_lower = folder_name.lower().strip()

        # Correspondência exata de token
        if name_lower in installed_tokens:
            return True

        # Verifica se alguma palavra-chave forte do nome bate com os tokens registrados
        words = name_lower.replace("-", " ").replace("_", " ").replace(".", " ").split()
        for w in words:
            if len(w) >= 4 and w in installed_tokens:
                return True

        return False

    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        findings: List[Finding] = []

        if progress_callback:
            progress_callback("Lendo catálogo de programas instalados no Registro do Windows...", 0, 100)

        installed_tokens = RegistryHelper.build_installed_software_tokens()
        search_roots = self._get_search_roots()

        total_roots = len(search_roots)
        for root_idx, root_dir in enumerate(search_roots):
            if progress_callback:
                progress_callback(f"Analisando resíduos em {root_dir.name}...", root_idx + 1, total_roots)

            if not root_dir.exists() or is_whitelisted(root_dir):
                continue

            try:
                subdirs = [p for p in root_dir.iterdir() if p.is_dir()]
            except (PermissionError, OSError):
                continue

            for subfolder in subdirs:
                if is_whitelisted(subfolder):
                    continue

                folder_name = subfolder.name

                # Se a pasta corresponde a um programa atualmente instalado ou fornecedor ativo, ignora
                if self._is_known_active_folder(folder_name, installed_tokens):
                    continue

                # Análise minuciosa dos arquivos internos da pasta suspeita
                inspection = inspect_folder_for_orphan_analysis(subfolder)
                size = inspection["size_bytes"]
                count = inspection["file_count"]

                # Ignora pastas totalmente vazias e sem arquivos (ou classifica se relevante)
                if size == 0 and count == 0:
                    continue

                confidence, reason = RiskClassifier.classify_orphan_folder(
                    folder_path=str(subfolder),
                    files_info=inspection,
                    has_executables=inspection["has_executables"],
                    has_dlls=inspection["has_dlls"],
                    last_modified=inspection["last_modified"],
                    matched_software_name=folder_name
                )

                findings.append(Finding(
                    category=self.category,
                    path=str(subfolder.resolve()),
                    size_bytes=size,
                    confidence=confidence,
                    reason=reason,
                    last_modified=inspection["last_modified"],
                    related_software=folder_name,
                    is_directory=True,
                    file_count=count,
                    metadata={
                        "root_location": str(root_dir),
                        "has_executables": inspection["has_executables"],
                        "has_dlls": inspection["has_dlls"],
                        "has_configs_only": inspection["has_configs_only"],
                        "extensions_found": inspection["extensions"][:10]
                    }
                ))

        return findings
