"""
Scanner de Cache de Shaders de Placas de Vídeo (NVIDIA, AMD, DirectX e Intel).
Recupera grandes volumes de espaço (5 GB - 30 GB+) ocupados por shaders pré-compilados obsoletos.
"""

import os
from pathlib import Path
from typing import Callable, List, Optional

from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import Finding, ScanCategory
from cleanpc_core.whitelist import is_whitelisted
from .base import BaseScanner
from .utils import get_dir_size_and_meta


class GpuShadersScanner(BaseScanner):
    @property
    def category(self) -> ScanCategory:
        return ScanCategory.GPU_SHADERS

    @property
    def name(self) -> str:
        return "Cache de Shaders de GPU (NVIDIA / AMD / DirectX)"

    @property
    def description(self) -> str:
        return "Localiza caches de shaders gráficos pré-compilados de DirectX, NVIDIA, AMD Radeon e Intel"

    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        findings: List[Finding] = []

        local_app_data = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")))
        app_data = Path(os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming")))

        shader_targets = [
            # DirectX Geral
            (local_app_data / "D3DSCache", "DirectX D3D Shader Cache", "DirectX"),
            (local_app_data / "DirectX Shader Cache", "DirectX Shader Cache", "DirectX"),
            # NVIDIA
            (local_app_data / "NVIDIA" / "DXCache", "NVIDIA DirectX Cache", "NVIDIA"),
            (local_app_data / "NVIDIA" / "GLCache", "NVIDIA OpenGL Cache", "NVIDIA"),
            (local_app_data / "NVIDIA Corporation" / "NV_Cache", "NVIDIA NV_Cache", "NVIDIA"),
            (local_app_data / "NVIDIA" / "ComputeCache", "NVIDIA Compute Cache", "NVIDIA"),
            # AMD Radeon
            (local_app_data / "AMD" / "DxCache", "AMD Radeon DxCache", "AMD"),
            (local_app_data / "AMD" / "GLCache", "AMD Radeon GLCache", "AMD"),
            (local_app_data / "AMD" / "OglShaders64", "AMD Radeon OpenGL Shaders", "AMD"),
            # Intel
            (local_app_data / "Intel" / "ShaderCache", "Intel Graphics Shader Cache", "Intel")
        ]

        total = len(shader_targets)
        for idx, (folder, desc, vendor) in enumerate(shader_targets):
            if progress_callback:
                progress_callback(f"Verificando {desc}", idx + 1, total)

            if not folder.exists() or is_whitelisted(folder):
                continue

            try:
                size, count, last_mod, _ = get_dir_size_and_meta(folder)
                if size > 0:
                    confidence, reason = RiskClassifier.classify_gpu_shader_cache(vendor, desc)
                    findings.append(Finding(
                        category=self.category,
                        path=str(folder.resolve()),
                        size_bytes=size,
                        confidence=confidence,
                        reason=reason,
                        last_modified=last_mod,
                        related_software=vendor,
                        is_directory=True,
                        file_count=count,
                        metadata={"vendor": vendor, "shader_type": desc}
                    ))
            except (PermissionError, OSError):
                continue

        return findings
