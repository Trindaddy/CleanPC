"""
Testes unitários para o scanner de Shaders de GPU (NVIDIA, AMD, DirectX).
"""

from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import RiskLevel, ScanCategory
from cleanpc_scanners.gpu_shaders import GpuShadersScanner


def test_gpu_shaders_scanner_metadata():
    scanner = GpuShadersScanner()
    assert scanner.category == ScanCategory.GPU_SHADERS
    assert "Shaders" in scanner.name


def test_classify_gpu_shader_cache():
    risk, reason = RiskClassifier.classify_gpu_shader_cache("NVIDIA", "DXCache")
    assert risk == RiskLevel.SAFE
    assert "shaders" in reason.lower()
