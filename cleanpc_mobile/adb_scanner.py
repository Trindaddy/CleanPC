"""
Scanner Especializado para Celulares Android Conectados via ADB (Depuração USB).
Identifica miniaturas, status ocultos do WhatsApp, APKs antigos e pastas órfãs de apps desinstalados.
"""

import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Set

from cleanpc_core.models import Finding, RiskLevel, ScanCategory
from .detector import ConnectedMobileDevice
from .mobile_whitelist import is_mobile_path_protected


class AdbDeviceScanner:
    def __init__(self, device: ConnectedMobileDevice):
        self.device = device
        self.adb_bin = shutil.which("adb") or "adb"

    def _adb_exec(self, cmd_args: List[str], timeout: int = 15) -> str:
        cmd = [self.adb_bin]
        if self.device.serial:
            cmd.extend(["-s", self.device.serial])
        cmd.extend(cmd_args)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return res.stdout.strip()
        except Exception:
            return ""

    def _get_installed_android_packages(self) -> Set[str]:
        """Obtém a lista de pacotes de aplicativos instalados no Android."""
        out = self._adb_exec(["shell", "pm", "list", "packages"])
        packages = set()
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("package:"):
                pkg_name = line.split(":", 1)[1].strip()
                if pkg_name:
                    packages.add(pkg_name)
        return packages

    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        findings: List[Finding] = []

        if progress_callback:
            progress_callback("Lendo catálogo de pacotes instalados no Android...", 1, 5)

        installed_packages = self._get_installed_android_packages()

        # 1. Miniaturas da Galeria (.thumbnails)
        if progress_callback:
            progress_callback("Verificando miniaturas de fotos (.thumbnails)...", 2, 5)

        thumb_paths = [
            "/sdcard/DCIM/.thumbnails",
            "/sdcard/Pictures/.thumbnails",
            "/sdcard/Android/data/com.sec.android.gallery3d/cache"
        ]
        for p in thumb_paths:
            size_str = self._adb_exec(["shell", f"du -sk '{p}' 2>/dev/null"])
            if size_str:
                try:
                    kb_size = int(size_str.split()[0])
                    size_bytes = kb_size * 1024
                    if size_bytes > 0:
                        findings.append(Finding(
                            category=ScanCategory.MOBILE_THUMBNAILS,
                            path=f"Android:{p}",
                            size_bytes=size_bytes,
                            confidence=RiskLevel.SAFE,
                            reason="Cache de miniaturas da Galeria de fotos. A galeria recria as miniaturas das fotos existentes automaticamente.",
                            related_software="Galeria Android",
                            is_directory=True,
                            metadata={"mobile_device": self.device.name, "remote_path": p, "mode": "ADB"}
                        ))
                except Exception:
                    pass

        # 2. Status Temporários do WhatsApp (.Statuses)
        if progress_callback:
            progress_callback("Verificando mídias e status ocultos do WhatsApp...", 3, 5)

        whatsapp_statuses = [
            "/sdcard/WhatsApp/Media/.Statuses",
            "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/.Statuses"
        ]
        for p in whatsapp_statuses:
            size_str = self._adb_exec(["shell", f"du -sk '{p}' 2>/dev/null"])
            if size_str:
                try:
                    kb_size = int(size_str.split()[0])
                    size_bytes = kb_size * 1024
                    if size_bytes > 0:
                        findings.append(Finding(
                            category=ScanCategory.MOBILE_WHATSAPP_STATUS,
                            path=f"Android:{p}",
                            size_bytes=size_bytes,
                            confidence=RiskLevel.SAFE,
                            reason="Fotos e vídeos temporários de Status do WhatsApp visualizados que ficaram salvos na memória do celular.",
                            related_software="WhatsApp",
                            is_directory=True,
                            metadata={"mobile_device": self.device.name, "remote_path": p, "mode": "ADB"}
                        ))
                except Exception:
                    pass

        # 3. Instaladores APK Esquecidos
        if progress_callback:
            progress_callback("Buscando instaladores APK antigos na pasta Download...", 4, 5)

        apks_out = self._adb_exec(["shell", "find /sdcard/Download -maxdepth 2 -name '*.apk' -exec ls -l {} + 2>/dev/null"])
        if apks_out:
            for line in apks_out.splitlines():
                parts = line.strip().split()
                if len(parts) >= 5 and parts[-1].endswith(".apk"):
                    apk_path = parts[-1]
                    try:
                        size_bytes = int(parts[4])
                        findings.append(Finding(
                            category=ScanCategory.MOBILE_APKS,
                            path=f"Android:{apk_path}",
                            size_bytes=size_bytes,
                            confidence=RiskLevel.SAFE,
                            reason=f"Pacote de instalação APK '{Path(apk_path).name}' esquecido na pasta Download.",
                            related_software="Instalador APK",
                            is_directory=False,
                            metadata={"mobile_device": self.device.name, "remote_path": apk_path, "mode": "ADB"}
                        ))
                    except Exception:
                        pass

        # 4. Pastas Órfãs em /sdcard/Android/data e /sdcard/Android/obb
        if progress_callback:
            progress_callback("Cruzando pastas de jogos e apps com lista de desinstalados...", 5, 5)

        data_dirs_out = self._adb_exec(["shell", "ls -1 /sdcard/Android/data 2>/dev/null"])
        if data_dirs_out:
            for folder_name in data_dirs_out.splitlines():
                folder_name = folder_name.strip()
                if not folder_name or folder_name in (".", ".."):
                    continue

                # Se a pasta é de um app que NÃO está mais instalado
                if installed_packages and folder_name not in installed_packages:
                    full_p = f"/sdcard/Android/data/{folder_name}"
                    if is_mobile_path_protected(full_p):
                        continue

                    size_str = self._adb_exec(["shell", f"du -sk '{full_p}' 2>/dev/null"])
                    if size_str:
                        try:
                            kb_size = int(size_str.split()[0])
                            size_bytes = kb_size * 1024
                            if size_bytes > 100 * 1024:  # Mais de 100 KB
                                findings.append(Finding(
                                    category=ScanCategory.MOBILE_ORPHAN_DATA,
                                    path=f"Android:{full_p}",
                                    size_bytes=size_bytes,
                                    confidence=RiskLevel.SAFE,
                                    reason=f"Resíduo de aplicativo desinstalado do celular: o pacote '{folder_name}' não consta nos apps ativos.",
                                    related_software=folder_name,
                                    is_directory=True,
                                    metadata={"mobile_device": self.device.name, "remote_path": full_p, "mode": "ADB"}
                                ))
                        except Exception:
                            pass

        return findings
