"""
Testes unitários específicos para as heurísticas de pastas órfãs.
"""

from datetime import datetime, timedelta
from cleanpc_core.classifier import RiskClassifier
from cleanpc_core.models import RiskLevel


def test_orphan_folder_with_dlls_is_risky():
    risk, reason = RiskClassifier.classify_orphan_folder(
        folder_path="C:\\Program Files\\OldTool",
        files_info={"size_bytes": 10000},
        has_executables=False,
        has_dlls=True,
        last_modified=datetime.now() - timedelta(days=60),
        matched_software_name="OldTool"
    )
    assert risk == RiskLevel.RISKY
    assert "dll" in reason.lower()


def test_orphan_folder_with_executables_is_unknown():
    risk, reason = RiskClassifier.classify_orphan_folder(
        folder_path="C:\\Program Files\\OldTool",
        files_info={"size_bytes": 10000},
        has_executables=True,
        has_dlls=False,
        last_modified=datetime.now() - timedelta(days=60),
        matched_software_name="OldTool"
    )
    assert risk == RiskLevel.UNKNOWN
    assert "manual" in reason.lower() or "executáveis" in reason.lower()


def test_orphan_folder_configs_only_old_is_safe():
    old_mod = datetime.now() - timedelta(days=45)
    risk, reason = RiskClassifier.classify_orphan_folder(
        folder_path="C:\\Users\\User\\AppData\\Local\\OldUninstalledApp",
        files_info={"size_bytes": 150000},
        has_executables=False,
        has_dlls=False,
        last_modified=old_mod,
        matched_software_name="OldUninstalledApp"
    )
    assert risk == RiskLevel.SAFE
    assert "resíduo inativo" in reason.lower()


def test_orphan_folder_configs_only_recent_is_moderate():
    recent_mod = datetime.now() - timedelta(days=2)
    risk, reason = RiskClassifier.classify_orphan_folder(
        folder_path="C:\\Users\\User\\AppData\\Local\\RecentlyUninstalled",
        files_info={"size_bytes": 150000},
        has_executables=False,
        has_dlls=False,
        last_modified=recent_mod,
        matched_software_name="RecentlyUninstalled"
    )
    assert risk == RiskLevel.MODERATE
