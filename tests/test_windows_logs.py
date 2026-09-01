"""
Testes unitários para o scanner de logs CBS e DISM do Windows.
"""

from datetime import datetime
from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import RiskLevel, ScanCategory
from cleanpc_scanners.windows_logs import WindowsLogsScanner


def test_windows_logs_scanner_metadata():
    scanner = WindowsLogsScanner()
    assert scanner.category == ScanCategory.WINDOWS_LOGS
    assert "CBS" in scanner.name or "Logs" in scanner.name


def test_classify_windows_log():
    risk, reason = RiskClassifier.classify_windows_log("CBS Log Persistido", datetime.now())
    assert risk == RiskLevel.SAFE
    assert "log" in reason.lower()
