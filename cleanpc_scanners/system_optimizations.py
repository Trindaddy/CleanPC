"""
Scanner de Otimizações de Sistema, Memória e Inicialização (Startup, Processos e TRIM).
"""

import os
import subprocess
import winreg
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional
import psutil

from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import Finding, RiskLevel, ScanCategory
from .base import BaseScanner


@dataclass
class StartupItem:
    name: str
    command: str
    location: str
    publisher: Optional[str] = None
    exists_on_disk: bool = True


class SystemOptimizationsScanner(BaseScanner):
    @property
    def category(self) -> ScanCategory:
        return ScanCategory.SYSTEM_OPTIMIZATIONS

    @property
    def name(self) -> str:
        return "Otimização de Desempenho e Inicialização"

    @property
    def description(self) -> str:
        return "Analisa programas de inicialização (Startup), processos em segundo plano e saúde do disco (TRIM/SSD)"

    def _get_startup_items_from_registry(self) -> List[StartupItem]:
        items: List[StartupItem] = []
        reg_targets = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "HKLM (32-bit) Run")
        ]

        for hive, subkey, loc_name in reg_targets:
            try:
                with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ) as key:
                    num_values = winreg.QueryInfoKey(key)[1]
                    for i in range(num_values):
                        try:
                            name, val, _ = winreg.EnumValue(key, i)
                            cmd_str = str(val)
                            # Extrai caminho do executável
                            exe_path = cmd_str.strip('"').split('"')[0].split(" /")[0].split(" -")[0]
                            exists = Path(exe_path).exists() if exe_path else True

                            items.append(StartupItem(
                                name=name,
                                command=cmd_str,
                                location=loc_name,
                                exists_on_disk=exists
                            ))
                        except (OSError, PermissionError):
                            continue
            except (OSError, PermissionError):
                continue

        return items

    def _get_top_memory_processes(self) -> List[dict]:
        """Identifica os processos em segundo plano com maior consumo de RAM."""
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info', 'username']):
            try:
                mem = p.info['memory_info']
                if mem and mem.rss > 100 * 1024 * 1024:  # Mais de 100 MB
                    procs.append({
                        "pid": p.info['pid'],
                        "name": p.info['name'],
                        "memory_mb": round(mem.rss / (1024 * 1024), 1),
                        "memory_percent": round(p.info['memory_percent'] or 0.0, 1),
                        "user": p.info['username']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        procs.sort(key=lambda x: x["memory_mb"], reverse=True)
        return procs[:15]

    def _detect_disk_types(self) -> List[dict]:
        """Detecta unidades de disco e se são SSD ou HDD via PowerShell/WMI."""
        disk_info = []
        try:
            cmd = "Get-PhysicalDisk | Select-Object DeviceId, MediaType, FriendlyName, Size | ConvertTo-Json"
            result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    data = [data]
                for d in data:
                    media = d.get("MediaType", "Unspecified")
                    disk_info.append({
                        "id": d.get("DeviceId"),
                        "name": d.get("FriendlyName"),
                        "media_type": media,
                        "size_gb": round((d.get("Size", 0) or 0) / (1024**3), 1)
                    })
        except Exception:
            pass
        return disk_info

    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        findings: List[Finding] = []

        if progress_callback:
            progress_callback("Lendo aplicativos de inicialização do Windows...", 1, 3)

        startup_items = self._get_startup_items_from_registry()
        for item in startup_items:
            # Se o executável de startup nem existe no disco, é um resíduo seguro de limpar do registro
            if not item.exists_on_disk:
                findings.append(Finding(
                    category=ScanCategory.STARTUP_ITEMS,
                    path=f"Registro Startup: {item.location}\\{item.name}",
                    size_bytes=0,
                    confidence=RiskLevel.SAFE,
                    reason=f"Item de inicialização '{item.name}' aponta para um executável inexistente no disco ({item.command}). Resíduo de inicialização.",
                    related_software=item.name,
                    metadata={"startup_name": item.name, "command": item.command, "location": item.location}
                ))
            else:
                findings.append(Finding(
                    category=ScanCategory.STARTUP_ITEMS,
                    path=f"Startup: {item.name}",
                    size_bytes=0,
                    confidence=RiskLevel.MODERATE,
                    reason=f"Programa configurado para iniciar automaticamente com o Windows: '{item.command}'. Desabilitar pode acelerar o boot.",
                    related_software=item.name,
                    action_available=["disable", "ignore"],
                    metadata={"startup_name": item.name, "command": item.command, "location": item.location}
                ))

        if progress_callback:
            progress_callback("Analisando saúde de discos e suporte a TRIM...", 2, 3)

        disks = self._detect_disk_types()
        for d in disks:
            media = d.get("media_type", "HDD")
            if media == "SSD":
                findings.append(Finding(
                    category=ScanCategory.SYSTEM_OPTIMIZATIONS,
                    path=f"Disco SSD: {d.get('name', 'SSD')}",
                    size_bytes=0,
                    confidence=RiskLevel.SAFE,
                    reason=f"Unidade SSD identificada ({d.get('size_gb')} GB). Otimização recomendada: comando TRIM periódica para manter a velocidade de gravação dos blocos flash.",
                    metadata={"disk": d, "optimization_type": "TRIM"}
                ))
            elif media == "HDD":
                findings.append(Finding(
                    category=ScanCategory.SYSTEM_OPTIMIZATIONS,
                    path=f"Disco HDD: {d.get('name', 'HDD')}",
                    size_bytes=0,
                    confidence=RiskLevel.MODERATE,
                    reason=f"Unidade de Disco Rígido Mecânico (HDD) ({d.get('size_gb')} GB). Recomendado verificar índice de fragmentação.",
                    metadata={"disk": d, "optimization_type": "DEFRAG"}
                ))

        return findings
