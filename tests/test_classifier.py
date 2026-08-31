"""
Testes unitários para o classificador de risco.
"""

from datetime import datetime, timedelta
from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import RiskLevel


def test_classify_old_temp_file():
    old_date = datetime.now() - timedelta(days=5)
    risk, reason = RiskClassifier.classify_temp_file("C:\\Temp\\old.tmp", old_date, False)
    assert risk == RiskLevel.SAFE


def test_classify_recent_temp_file():
    recent_date = datetime.now() - timedelta(minutes=10)
    risk, reason = RiskClassifier.classify_temp_file("C:\\Temp\\fresh.tmp", recent_date, False)
    assert risk == RiskLevel.MODERATE


def test_classify_browser_cache():
    risk, reason = RiskClassifier.classify_browser_cache("Google Chrome", "GPUCache")
    assert risk == RiskLevel.SAFE
    assert "senhas" in reason.lower()


def test_classify_recycle_bin():
    risk, reason = RiskClassifier.classify_recycle_bin(item_count=15, total_size_bytes=50000000)
    assert risk == RiskLevel.MODERATE


def test_classify_error_dump():
    risk, reason = RiskClassifier.classify_error_dump("Minidump", None)
    assert risk == RiskLevel.SAFE
