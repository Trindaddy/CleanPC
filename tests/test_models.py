"""
Testes unitários para os modelos de dados centrais.
"""

from datetime import datetime
from cleanpc_core.models import Finding, RiskLevel, ScanCategory, QuarantineRecord, BatchQuarantineManifest


def test_finding_serialization():
    finding = Finding(
        category=ScanCategory.TEMP_FILES,
        path="C:\\Test\\temp.tmp",
        size_bytes=1024,
        confidence=RiskLevel.SAFE,
        reason="Arquivo temporário antigo",
        last_modified=datetime(2026, 1, 1, 12, 0, 0),
        related_software="TestApp",
        is_directory=False,
        file_count=1
    )

    data = finding.to_dict()
    assert data["category"] == "temp_files"
    assert data["confidence"] == "safe"
    assert data["size_bytes"] == 1024
    assert data["is_directory"] is False

    reconstructed = Finding.from_dict(data)
    assert reconstructed.category == finding.category
    assert reconstructed.path == finding.path
    assert reconstructed.size_bytes == finding.size_bytes
    assert reconstructed.confidence == finding.confidence
    assert reconstructed.reason == finding.reason


def test_quarantine_record_serialization():
    now = datetime.now()
    record = QuarantineRecord(
        id="test-uuid-123",
        batch_id="batch-456",
        original_path="C:\\Test\\orphan_cache",
        quarantine_path="C:\\AppData\\quarantine\\batch-456\\test-uuid-123",
        size_bytes=4096,
        is_directory=True,
        category="orphan_folders",
        quarantined_at=now,
        sha256=None,
        reason="Pasta órfã sem executáveis"
    )

    data = record.to_dict()
    assert data["id"] == "test-uuid-123"
    assert data["size_bytes"] == 4096
    assert data["is_directory"] is True

    reconstructed = QuarantineRecord.from_dict(data)
    assert reconstructed.id == record.id
    assert reconstructed.batch_id == record.batch_id
    assert reconstructed.original_path == record.original_path
