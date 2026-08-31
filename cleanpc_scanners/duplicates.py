"""
Scanner de Arquivos Duplicados por Hash Criptográfico.
Agrupa previamente por tamanho e compara por hash (Blake2b / SHA256) em streaming.
"""

import hashlib
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.config import CHUNK_SIZE_HASH
from cleanpc_core.models import Finding, ScanCategory
from cleanpc_core.whitelist import is_whitelisted
from .base import BaseScanner


class DuplicateFilesScanner(BaseScanner):
    def __init__(self, target_folders: Optional[List[Path]] = None):
        self.target_folders = target_folders or self._default_target_folders()

    @property
    def category(self) -> ScanCategory:
        return ScanCategory.DUPLICATES

    @property
    def name(self) -> str:
        return "Arquivos Duplicados"

    @property
    def description(self) -> str:
        return "Localiza arquivos idênticos (mesmo hash SHA-256) em pastas de usuário"

    def _default_target_folders(self) -> List[Path]:
        user_home = Path(os.path.expanduser("~"))
        folders = [
            user_home / "Downloads",
            user_home / "Documents",
            user_home / "Pictures"
        ]
        return [f for f in folders if f.exists()]

    def _calculate_file_hash(self, file_path: Path) -> Optional[str]:
        try:
            hasher = hashlib.blake2b(digest_size=20)
            with open(file_path, "rb") as f:
                while chunk := f.read(CHUNK_SIZE_HASH):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (PermissionError, OSError):
            return None

    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        findings: List[Finding] = []
        files_by_size: Dict[int, List[Path]] = defaultdict(list)

        # 1. Coleta e agrupa arquivos por tamanho exato
        for folder in self.target_folders:
            if not folder.exists() or is_whitelisted(folder):
                continue

            try:
                for root, _, files in os.walk(str(folder)):
                    for f in files:
                        p = Path(root) / f
                        if is_whitelisted(p):
                            continue
                        try:
                            st = p.stat()
                            # Apenas arquivos maiores que 1KB para evitar falsos positivos com arquivos vazios
                            if st.st_size > 1024:
                                files_by_size[st.st_size].append(p)
                        except (PermissionError, OSError):
                            continue
            except (PermissionError, OSError):
                continue

        # 2. Filtra apenas tamanhos com 2 ou mais ocorrências
        candidates = {size: paths for size, paths in files_by_size.items() if len(paths) > 1}
        total_candidate_groups = len(candidates)
        processed_groups = 0

        # 3. Calcula hash apenas dos candidatos
        for size, paths in candidates.items():
            processed_groups += 1
            if progress_callback:
                progress_callback(f"Comparando hashes ({len(paths)} arquivos de {size // 1024} KB)...", processed_groups, total_candidate_groups)

            hashes_map: Dict[str, List[Path]] = defaultdict(list)
            for path in paths:
                h = self._calculate_file_hash(path)
                if h:
                    hashes_map[h].append(path)

            for file_hash, dup_paths in hashes_map.items():
                if len(dup_paths) > 1:
                    # Encontrou duplicados reais com o mesmo hash
                    # O primeiro arquivo é a referência; os demais são apontados como duplicados
                    for dup_file in dup_paths[1:]:
                        try:
                            st = dup_file.stat()
                            last_mod = datetime.fromtimestamp(st.st_mtime)
                            confidence, reason = RiskClassifier.classify_duplicate_file(str(dup_file), len(dup_paths))
                            findings.append(Finding(
                                category=self.category,
                                path=str(dup_file.resolve()),
                                size_bytes=st.st_size,
                                confidence=confidence,
                                reason=reason,
                                last_modified=last_mod,
                                is_directory=False,
                                file_count=1,
                                metadata={
                                    "hash": file_hash,
                                    "original_reference": str(dup_paths[0].resolve()),
                                    "total_copies": len(dup_paths)
                                }
                            ))
                        except (PermissionError, OSError):
                            continue

        return findings
