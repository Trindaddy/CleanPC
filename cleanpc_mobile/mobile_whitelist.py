"""
Whitelist Estrita de Proteção para Armazenamento de Celulares (Android / iOS).
Garante que fotos reais da câmera, documentos pessoais, músicas e backups do WhatsApp NUNCA sejam tocados.
"""

from pathlib import Path
from typing import Set

# Pastas e caminhos que NUNCA podem ser excluídos no celular
PROTECTED_MOBILE_DIRECTORIES: Set[str] = {
    "dcim/camera",
    "dcim/100media",
    "dcim/screenshots",
    "pictures/camera",
    "pictures/screenshots",
    "pictures/instagram",
    "pictures/whatsapp",
    "documents",
    "music",
    "movies",
    "podcasts",
    "audiobooks",
    "ringtones",
    "alarms",
    "notifications",
    "whatsapp/databases",
    "whatsapp/backups"
}

PROTECTED_MOBILE_EXTENSIONS: Set[str] = {
    ".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".key", ".mp3", ".flac", ".wav", ".m4a"
}


def is_mobile_path_protected(path: str) -> bool:
    """Verifica se um caminho no smartphone está protegido pela Whitelist."""
    norm = path.replace("\\", "/").lower().strip("/")
    
    # Remove prefixos comuns do Android (/sdcard/, /storage/emulated/0/, etc.)
    for prefix in ["sdcard/", "storage/emulated/0/", "storage/self/primary/", "storage/"]:
        if norm.startswith(prefix):
            norm = norm[len(prefix):].lstrip("/")

    # Protege se for uma pasta raiz protegida
    for protected in PROTECTED_MOBILE_DIRECTORIES:
        if norm == protected or norm.startswith(protected + "/"):
            # Exceção permitida: se estiver dentro de uma subpasta .thumbnails
            if ".thumbnails" in norm:
                return False
            # Exceção permitida: se for pasta .Statuses do WhatsApp
            if ".statuses" in norm:
                return False
            return True

    # Protege extensões de documentos essenciais
    ext = Path(path).suffix.lower()
    if ext in PROTECTED_MOBILE_EXTENSIONS:
        return True

    return False
