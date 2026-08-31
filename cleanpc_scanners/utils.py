"""
Utilitários de sistema de arquivos para os scanners.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set, Tuple


def get_dir_size_and_meta(
    dir_path: Path,
    max_depth: int = 10
) -> Tuple[int, int, Optional[datetime], Set[str]]:
    """
    Calcula tamanho total, quantidade de arquivos, data da última modificação
    e conjunto de extensões encontradas dentro de um diretório.
    Lida silenciosamente com exceções de permissão.
    """
    total_size = 0
    file_count = 0
    newest_mtime = 0.0
    extensions: Set[str] = set()

    try:
        if not dir_path.exists() or not dir_path.is_dir():
            return 0, 0, None, extensions
    except PermissionError:
        return 0, 0, None, extensions

    base_depth = len(dir_path.parts)

    try:
        for root, dirs, files in os.walk(str(dir_path)):
            current_depth = len(Path(root).parts) - base_depth
            if current_depth > max_depth:
                dirs.clear()  # Interrompe recursão além de max_depth
                continue

            for f in files:
                f_path = os.path.join(root, f)
                try:
                    stat = os.stat(f_path)
                    total_size += stat.st_size
                    file_count += 1
                    if stat.st_mtime > newest_mtime:
                        newest_mtime = stat.st_mtime
                    ext = Path(f).suffix.lower()
                    if ext:
                        extensions.add(ext)
                except (PermissionError, FileNotFoundError, OSError):
                    continue

    except (PermissionError, FileNotFoundError, OSError):
        pass

    last_mod = datetime.fromtimestamp(newest_mtime) if newest_mtime > 0 else None
    return total_size, file_count, last_mod, extensions


def inspect_folder_for_orphan_analysis(folder_path: Path) -> Dict[str, any]:
    """
    Inspeciona uma pasta detalhadamente para subsidiar a heurística de pasta órfã.
    """
    total_size, file_count, last_mod, exts = get_dir_size_and_meta(folder_path)

    has_executables = bool(exts.intersection({".exe", ".bat", ".cmd", ".ps1", ".vbs"}))
    has_dlls = bool(exts.intersection({".dll", ".sys", ".drv", ".ocx"}))
    has_configs_only = bool(exts.issubset({".ini", ".json", ".xml", ".yaml", ".yml", ".cfg", ".conf", ".log", ".txt", ".dat", ".cache", ".tmp", ".db", ""}))

    return {
        "size_bytes": total_size,
        "file_count": file_count,
        "last_modified": last_mod,
        "extensions": list(exts),
        "has_executables": has_executables,
        "has_dlls": has_dlls,
        "has_configs_only": has_configs_only
    }
