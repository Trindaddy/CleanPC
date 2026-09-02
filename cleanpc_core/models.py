"""
Modelos de dados para o Mega Limpador & Otimizador de PC.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class RiskLevel(str, Enum):
    SAFE = "safe"              # Seguro: arquivos temporários, caches puros sem dados de usuário
    MODERATE = "moderate"      # Moderado: lixeira antiga, thumbnails, logs antigos
    RISKY = "risky"            # Arriscado: requer atenção redobrada, itens com dependências
    UNKNOWN = "unknown"        # Desconhecido: requer revisão humana detalhada (nunca remover sozinho)

    @property
    def display_name(self) -> str:
        names = {
            "safe": "Seguro",
            "moderate": "Moderado",
            "risky": "Arriscado",
            "unknown": "Requer Análise"
        }
        return names.get(self.value, self.value)

    @property
    def color(self) -> str:
        colors = {
            "safe": "green",
            "moderate": "yellow",
            "risky": "red",
            "unknown": "magenta"
        }
        return colors.get(self.value, "white")


class ScanCategory(str, Enum):
    TEMP_FILES = "temp_files"
    BROWSER_CACHE = "browser_cache"
    GPU_SHADERS = "gpu_shaders"
    APP_CACHES = "app_caches"
    WINDOWS_LOGS = "windows_logs"
    RECYCLE_BIN = "recycle_bin"
    ERROR_DUMPS = "error_dumps"
    DEV_CACHES = "dev_caches"
    THUMBNAILS = "thumbnails"
    ORPHAN_FOLDERS = "orphan_folders"
    DUPLICATES = "duplicates"
    STARTUP_ITEMS = "startup_items"
    SERVICES = "services"
    SYSTEM_OPTIMIZATIONS = "system_optimizations"
    # Categorias de Celular / Smartphone
    MOBILE_THUMBNAILS = "mobile_thumbnails"
    MOBILE_WHATSAPP_STATUS = "mobile_whatsapp_status"
    MOBILE_APKS = "mobile_apks"
    MOBILE_ORPHAN_DATA = "mobile_orphan_data"
    MOBILE_APP_CACHES = "mobile_app_caches"

    @property
    def display_name(self) -> str:
        names = {
            "temp_files": "Arquivos Temporários",
            "browser_cache": "Cache de Navegadores",
            "gpu_shaders": "Cache de Shaders de GPU (NVIDIA / AMD / DirectX)",
            "app_caches": "Caches de Apps (Discord / Spotify / Steam / Epic)",
            "windows_logs": "Logs e Histórico do Windows Update (CBS / DISM)",
            "recycle_bin": "Lixeira do Windows",
            "error_dumps": "Dumps e Relatórios de Erro",
            "dev_caches": "Caches de Desenvolvimento (npm/pip/gradle/docker)",
            "thumbnails": "Cache de Miniaturas (Thumbnails)",
            "orphan_folders": "Pastas Órfãs de Programas Desinstalados",
            "duplicates": "Arquivos Duplicados",
            "startup_items": "Itens de Inicialização (Startup)",
            "services": "Serviços do Windows",
            "system_optimizations": "Otimizações de Sistema (Disco/Memória)",
            # Mobile
            "mobile_thumbnails": "Celular: Miniaturas da Galeria (.thumbnails)",
            "mobile_whatsapp_status": "Celular: WhatsApp Status Ocultos (.Statuses)",
            "mobile_apks": "Celular: Instaladores APK Antigos",
            "mobile_orphan_data": "Celular: Pastas Órfãs de Apps Desinstalados (Android/data)",
            "mobile_app_caches": "Celular: Caches de Mídia de Mensageiros (Telegram/TikTok)"
        }
        return names.get(self.value, self.value)


@dataclass
class Finding:
    """Representa um item identificado durante a varredura."""
    category: ScanCategory
    path: str
    size_bytes: int
    confidence: RiskLevel
    reason: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    last_modified: Optional[datetime] = None
    related_software: Optional[str] = None
    action_available: List[str] = field(default_factory=lambda: ["quarantine", "ignore"])
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_directory: bool = False
    file_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category.value,
            "category_name": self.category.display_name,
            "path": self.path,
            "size_bytes": self.size_bytes,
            "confidence": self.confidence.value,
            "confidence_display": self.confidence.display_name,
            "reason": self.reason,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "related_software": self.related_software,
            "action_available": self.action_available,
            "metadata": self.metadata,
            "is_directory": self.is_directory,
            "file_count": self.file_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Finding":
        last_mod = None
        if data.get("last_modified"):
            try:
                last_mod = datetime.fromisoformat(data["last_modified"])
            except Exception:
                pass

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            category=ScanCategory(data["category"]),
            path=data["path"],
            size_bytes=data.get("size_bytes", 0),
            confidence=RiskLevel(data.get("confidence", "unknown")),
            reason=data.get("reason", ""),
            last_modified=last_mod,
            related_software=data.get("related_software"),
            action_available=data.get("action_available", ["quarantine", "ignore"]),
            metadata=data.get("metadata", {}),
            is_directory=data.get("is_directory", False),
            file_count=data.get("file_count", 1)
        )


@dataclass
class QuarantineRecord:
    """Registro de um item em quarentena para possibilitar restauração 100% reversível."""
    id: str
    batch_id: str
    original_path: str
    quarantine_path: str
    size_bytes: int
    is_directory: bool
    category: str
    quarantined_at: datetime
    sha256: Optional[str] = None
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "original_path": self.original_path,
            "quarantine_path": self.quarantine_path,
            "size_bytes": self.size_bytes,
            "is_directory": self.is_directory,
            "category": self.category,
            "quarantined_at": self.quarantined_at.isoformat(),
            "sha256": self.sha256,
            "reason": self.reason
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuarantineRecord":
        return cls(
            id=data["id"],
            batch_id=data["batch_id"],
            original_path=data["original_path"],
            quarantine_path=data["quarantine_path"],
            size_bytes=data["size_bytes"],
            is_directory=data.get("is_directory", False),
            category=data.get("category", "unknown"),
            quarantined_at=datetime.fromisoformat(data["quarantined_at"]),
            sha256=data.get("sha256"),
            reason=data.get("reason", "")
        )


@dataclass
class BatchQuarantineManifest:
    """Manifesto de uma sessão de quarentena."""
    batch_id: str
    created_at: datetime
    items: List[QuarantineRecord] = field(default_factory=list)
    total_size_bytes: int = 0
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "created_at": self.created_at.isoformat(),
            "total_size_bytes": self.total_size_bytes,
            "note": self.note,
            "item_count": len(self.items),
            "items": [item.to_dict() for item in self.items]
        }
