"""
Scanner para Celulares Conectados via MTP (Windows Portable Devices) ou Armazenamento Montado.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from cleanpc_core.models import Finding, RiskLevel, ScanCategory
from cleanpc_scanners.utils import get_dir_size_and_meta
from .detector import ConnectedMobileDevice
from .mobile_whitelist import is_mobile_path_protected


class MtpDeviceScanner:
    def __init__(self, device: ConnectedMobileDevice):
        self.device = device

    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        findings: List[Finding] = []

        # Se tiver caminho de montagem direto (cartão SD ou unidade mapeada)
        if self.device.mount_path:
            root = Path(self.device.mount_path)
            if not root.exists():
                return findings

            # 1. Miniaturas (.thumbnails)
            thumb_candidates = [
                root / "DCIM" / ".thumbnails",
                root / "Pictures" / ".thumbnails"
            ]
            for t_dir in thumb_candidates:
                if t_dir.exists() and t_dir.is_dir():
                    size, count, last_mod, _ = get_dir_size_and_meta(t_dir)
                    if size > 0:
                        findings.append(Finding(
                            category=ScanCategory.MOBILE_THUMBNAILS,
                            path=str(t_dir.resolve()),
                            size_bytes=size,
                            confidence=RiskLevel.SAFE,
                            reason="Cache de miniaturas da Galeria de fotos do celular. Recriado automaticamente para fotos ativas.",
                            related_software="Galeria Mobile",
                            is_directory=True,
                            file_count=count,
                            metadata={"device": self.device.name, "mode": "MassStorage"}
                        ))

            # 2. WhatsApp Status
            wa_candidates = [
                root / "WhatsApp" / "Media" / ".Statuses",
                root / "Android" / "media" / "com.whatsapp" / "WhatsApp" / "Media" / ".Statuses"
            ]
            for wa_dir in wa_candidates:
                if wa_dir.exists() and wa_dir.is_dir():
                    size, count, last_mod, _ = get_dir_size_and_meta(wa_dir)
                    if size > 0:
                        findings.append(Finding(
                            category=ScanCategory.MOBILE_WHATSAPP_STATUS,
                            path=str(wa_dir.resolve()),
                            size_bytes=size,
                            confidence=RiskLevel.SAFE,
                            reason="Fotos e vídeos de Status visualizados no WhatsApp salvos temporariamente na memória.",
                            related_software="WhatsApp",
                            is_directory=True,
                            file_count=count,
                            metadata={"device": self.device.name, "mode": "MassStorage"}
                        ))

            # 3. APKs antigos em Download
            download_dir = root / "Download"
            if download_dir.exists() and download_dir.is_dir():
                for apk in download_dir.glob("*.apk"):
                    if not is_mobile_path_protected(str(apk)):
                        try:
                            st = apk.stat()
                            findings.append(Finding(
                                category=ScanCategory.MOBILE_APKS,
                                path=str(apk.resolve()),
                                size_bytes=st.st_size,
                                confidence=RiskLevel.SAFE,
                                reason=f"Instalador APK antigo '{apk.name}' guardado na pasta de Downloads do celular.",
                                related_software="Instalador APK",
                                is_directory=False,
                                metadata={"device": self.device.name, "mode": "MassStorage"}
                            ))
                        except Exception:
                            pass

        return findings
