"""
Testes unitários para o sistema de Quarentena e Restauração reversível (Undo).
"""

import tempfile
from datetime import datetime
from pathlib import Path

from cleanpc_core.models import Finding, RiskLevel, ScanCategory
from cleanpc_core.quarantine import QuarantineManager


def test_quarantine_lifecycle_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # 1. Cria arquivo de teste
        test_file = temp_dir_path / "app_cache.log"
        test_content = "SAMPLE LOG DATA FOR CLEANPC QUARANTINE TEST 123456"
        test_file.write_text(test_content, encoding="utf-8")
        assert test_file.exists()

        qm = QuarantineManager()
        batch_id = qm.create_batch(note="Teste Automatizado")

        finding = Finding(
            category=ScanCategory.TEMP_FILES,
            path=str(test_file.resolve()),
            size_bytes=len(test_content),
            confidence=RiskLevel.SAFE,
            reason="Log temporário de teste",
            last_modified=datetime.now(),
            is_directory=False,
            file_count=1
        )

        # 2. Move para a quarentena
        success, record, err = qm.move_to_quarantine(finding, batch_id)
        assert success is True
        assert record is not None
        assert not test_file.exists()  # Arquivo saiu da pasta original
        assert Path(record.quarantine_path).exists()  # Arquivo está na quarentena

        # 3. Restaura o arquivo de volta
        restore_ok, restore_err = qm.restore_item(record)
        assert restore_ok is True
        assert test_file.exists()  # Arquivo voltou para o local original
        assert test_file.read_text(encoding="utf-8") == test_content  # Conteúdo 100% íntegro


def test_quarantine_lifecycle_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # 1. Cria pasta com arquivos
        orphan_dir = temp_dir_path / "OrphanSoftwareResidue"
        orphan_dir.mkdir()
        (orphan_dir / "config.ini").write_text("[Settings]\nTheme=Dark", encoding="utf-8")
        (orphan_dir / "data.json").write_text('{"user_id": 99}', encoding="utf-8")

        qm = QuarantineManager()
        batch_id = qm.create_batch(note="Teste Diretório Órfão")

        finding = Finding(
            category=ScanCategory.ORPHAN_FOLDERS,
            path=str(orphan_dir.resolve()),
            size_bytes=1024,
            confidence=RiskLevel.SAFE,
            reason="Resíduo de pasta órfã",
            last_modified=datetime.now(),
            is_directory=True,
            file_count=2
        )

        # 2. Move pasta para a quarentena
        success, record, err = qm.move_to_quarantine(finding, batch_id)
        assert success is True
        assert not orphan_dir.exists()
        assert Path(record.quarantine_path).exists()

        # 3. Restaura o lote inteiro
        succ, fail, errs = qm.restore_batch(batch_id)
        assert succ == 1
        assert fail == 0
        assert orphan_dir.exists()
        assert (orphan_dir / "config.ini").exists()
        assert (orphan_dir / "data.json").exists()
