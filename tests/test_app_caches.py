"""
Testes unitários para o scanner de Caches de Apps (Discord, Spotify, Steam, Epic Games).
"""

from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import RiskLevel, ScanCategory
from cleanpc_scanners.app_caches import AppCachesScanner


def test_app_caches_scanner_metadata():
    scanner = AppCachesScanner()
    assert scanner.category == ScanCategory.APP_CACHES
    assert "Discord" in scanner.name or "Apps" in scanner.name


def test_classify_app_cache():
    risk, reason = RiskClassifier.classify_app_cache("Discord", "Cache de Mídia")
    assert risk == RiskLevel.SAFE
    assert "desloga" in reason.lower() or "cache" in reason.lower()
