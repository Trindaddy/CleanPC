"""
Detector de Smartphones e Dispositivos Móveis Conectados via USB (MTP, ADB e Armazenamento em Massa).
"""

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import psutil

from cleanpc_core.logger import app_logger


@dataclass
class ConnectedMobileDevice:
    name: str
    mode: str                      # "MTP", "ADB", "MassStorage"
    device_id: str
    description: str
    mount_path: Optional[str] = None
    serial: Optional[str] = None
    storage_capacity: Optional[str] = None


class MobileDeviceDetector:
    """Identifica smartphones conectados ao computador."""

    @classmethod
    def detect_all_devices(cls) -> List[ConnectedMobileDevice]:
        devices: List[ConnectedMobileDevice] = []

        # 1. Tenta detectar via ADB (Modo Desenvolvedor / Depuração USB)
        adb_devs = cls._detect_adb_devices()
        devices.extend(adb_devs)

        # 2. Tenta detectar via Windows Portable Devices (MTP - Modo Padrão de Transferência de Arquivos)
        mtp_devs = cls._detect_wpd_devices()
        for d in mtp_devs:
            # Evita duplicar se o mesmo aparelho já foi detectado por ADB
            if not any(d.name.lower() in existing.name.lower() or existing.name.lower() in d.name.lower() for existing in devices):
                devices.append(d)

        # 3. Tenta detectar cartões SD / Armazenamento em Massa montado com letra de unidade
        mass_devs = cls._detect_mass_storage_devices()
        for d in mass_devs:
            if not any(d.mount_path == existing.mount_path for existing in devices):
                devices.append(d)

        return devices

    @classmethod
    def _detect_adb_devices(cls) -> List[ConnectedMobileDevice]:
        devices = []
        adb_bin = shutil.which("adb")
        if not adb_bin:
            # Verifica caminhos padrão do Android SDK / Platform-Tools no Windows
            candidates = [
                Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk" / "platform-tools" / "adb.exe",
                Path("C:\\platform-tools\\adb.exe"),
                Path("C:\\adb\\adb.exe")
            ]
            for c in candidates:
                if c.exists():
                    adb_bin = str(c)
                    break

        if not adb_bin:
            return []

        try:
            result = subprocess.run([adb_bin, "devices", "-l"], capture_output=True, text=True, timeout=4)
            if result.returncode == 0:
                lines = result.stdout.strip().splitlines()
                for line in lines[1:]:
                    line = line.strip()
                    if line and "device" in line and not line.startswith("*"):
                        parts = line.split()
                        serial = parts[0]
                        model_name = "Android Smartphone"
                        for p in parts:
                            if p.startswith("model:"):
                                model_name = p.split(":")[1].replace("_", " ")
                            elif p.startswith("device:"):
                                model_name += f" ({p.split(':')[1]})"

                        devices.append(ConnectedMobileDevice(
                            name=model_name,
                            mode="ADB",
                            device_id=serial,
                            description="Conectado via Depuração USB (ADB)",
                            serial=serial
                        ))
        except Exception as e:
            app_logger.debug(f"Detecção ADB não retornou dispositivos: {e}")

        return devices

    @classmethod
    def _detect_wpd_devices(cls) -> List[ConnectedMobileDevice]:
        """Detecta dispositivos portáteis do Windows (WPD / MTP)."""
        devices = []
        try:
            cmd = "Get-PnpDevice -Class PortableDevice, WPD -Status OK | Select-Object FriendlyName, InstanceId, Status | ConvertTo-Json"
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = item.get("FriendlyName")
                    inst_id = item.get("InstanceId", "")
                    if name and not any(ignored in name.lower() for ignored in ["generic", "volume"]):
                        devices.append(ConnectedMobileDevice(
                            name=name,
                            mode="MTP",
                            device_id=inst_id,
                            description="Conectado via MTP (Transferência de Arquivos do Windows)"
                        ))
        except Exception as e:
            app_logger.debug(f"Detecção WPD PowerShell: {e}")

        return devices

    @classmethod
    def _detect_mass_storage_devices(cls) -> List[ConnectedMobileDevice]:
        """Detecta unidades removíveis que contenham estruturas típicas de smartphones (DCIM, Android, WhatsApp)."""
        devices = []
        try:
            partitions = psutil.disk_partitions(all=False)
            for p in partitions:
                if "removable" in p.opts.lower() or p.mountpoint.upper() not in ("C:\\", "D:\\"):
                    mount = Path(p.mountpoint)
                    # Verifica se contém pastas características de celular
                    has_dcim = (mount / "DCIM").exists()
                    has_android = (mount / "Android").exists()
                    has_whatsapp = (mount / "WhatsApp").exists()
                    if has_dcim or has_android or has_whatsapp:
                        devices.append(ConnectedMobileDevice(
                            name=f"Armazenamento de Celular ({p.mountpoint})",
                            mode="MassStorage",
                            device_id=p.mountpoint,
                            description="Cartão de Memória / Armazenamento Montado",
                            mount_path=str(mount.resolve())
                        ))
        except Exception:
            pass

        return devices
