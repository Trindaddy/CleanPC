"""
Sistema de Quarentena Reversível (Undo & Restore) para o Mega Limpador & Otimizador de PC.
Garante que nenhum item seja apagado permanentemente por padrão.
"""

import hashlib
import json
import os
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from .config import (
    CHUNK_SIZE_HASH,
    DEFAULT_QUARANTINE_RETENTION_DAYS,
    QUARANTINE_DIR,
    QUARANTINE_MANIFESTS_DIR,
    ensure_directories
)
from .logger import app_logger
from .models import BatchQuarantineManifest, Finding, QuarantineRecord
from .whitelist import is_whitelisted


def calculate_file_hash(file_path: Path) -> Optional[str]:
    """Calcula o hash SHA256 de um arquivo de forma segura em streaming."""
    if not file_path.is_file():
        return None
    try:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE_HASH):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None


class QuarantineManager:
    def __init__(self):
        ensure_directories()

    def _get_batch_manifest_path(self, batch_id: str) -> Path:
        return QUARANTINE_MANIFESTS_DIR / f"{batch_id}.json"

    def create_batch(self, note: str = "") -> str:
        """Cria um novo lote de quarentena com ID único."""
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
        manifest = BatchQuarantineManifest(
            batch_id=batch_id,
            created_at=datetime.now(),
            items=[],
            total_size_bytes=0,
            note=note
        )
        self._save_batch_manifest(manifest)
        batch_dir = QUARANTINE_DIR / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)
        return batch_id

    def _save_batch_manifest(self, manifest: BatchQuarantineManifest):
        path = self._get_batch_manifest_path(manifest.batch_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2, ensure_ascii=False)

    def load_batch_manifest(self, batch_id: str) -> Optional[BatchQuarantineManifest]:
        path = self._get_batch_manifest_path(batch_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                items = [QuarantineRecord.from_dict(it) for it in data.get("items", [])]
                return BatchQuarantineManifest(
                    batch_id=data["batch_id"],
                    created_at=datetime.fromisoformat(data["created_at"]),
                    items=items,
                    total_size_bytes=data.get("total_size_bytes", 0),
                    note=data.get("note", "")
                )
        except Exception as e:
            app_logger.error(f"Erro ao carregar manifesto de quarentena {batch_id}: {e}")
            return None

    def move_to_quarantine(self, finding: Finding, batch_id: str) -> Tuple[bool, Optional[QuarantineRecord], Optional[str]]:
        """
        Move um item encontrado para a pasta de quarentena de forma reversível.
        Retorna (sucesso, QuarantineRecord, mensagem_de_erro).
        """
        target_path = Path(finding.path)

        if not target_path.exists():
            return False, None, f"O caminho '{finding.path}' não existe mais no disco."

        # BLINDAGEM MÁXIMA: Verifica Whitelist
        if is_whitelisted(target_path):
            msg = f"AÇÃO BLOQUEADA: '{target_path}' está protegido pela Whitelist do sistema!"
            app_logger.warning(msg)
            app_logger.log_event("quarantine_blocked", {"path": str(target_path), "reason": "whitelist"}, status="blocked")
            return False, None, msg

        item_id = str(uuid.uuid4())
        batch_dir = QUARANTINE_DIR / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)

        dest_name = f"{item_id}_{target_path.name}"
        quarantine_dest = batch_dir / dest_name

        try:
            is_dir = target_path.is_dir()
            file_hash = None
            if not is_dir:
                file_hash = calculate_file_hash(target_path)

            # Move o arquivo/pasta para a quarentena
            shutil.move(str(target_path), str(quarantine_dest))

            record = QuarantineRecord(
                id=item_id,
                batch_id=batch_id,
                original_path=str(target_path.resolve()),
                quarantine_path=str(quarantine_dest.resolve()),
                size_bytes=finding.size_bytes,
                is_directory=is_dir,
                category=finding.category.value,
                quarantined_at=datetime.now(),
                sha256=file_hash,
                reason=finding.reason
            )

            # Atualiza manifesto do lote
            manifest = self.load_batch_manifest(batch_id)
            if manifest:
                manifest.items.append(record)
                manifest.total_size_bytes += finding.size_bytes
                self._save_batch_manifest(manifest)

            app_logger.info(f"Item movido para quarentena: {finding.path} -> {quarantine_dest}")
            app_logger.log_event("quarantine_success", record.to_dict(), status="success")

            return True, record, None

        except Exception as e:
            err_msg = f"Falha ao mover para quarentena '{finding.path}': {e}"
            app_logger.error(err_msg)
            app_logger.log_event("quarantine_failed", {"path": finding.path, "error": str(e)}, status="error", error=str(e))
            return False, None, err_msg

    def restore_item(self, record: QuarantineRecord) -> Tuple[bool, Optional[str]]:
        """
        Restaura um item da quarentena para o caminho original no sistema.
        """
        q_path = Path(record.quarantine_path)
        orig_path = Path(record.original_path)

        if not q_path.exists():
            return False, f"Arquivo em quarentena não encontrado em '{q_path}'"

        try:
            # Garante que a pasta pai de destino original exista
            orig_path.parent.mkdir(parents=True, exist_ok=True)

            # Se já existir algo no destino original, renomeia ou avisa
            if orig_path.exists():
                backup_existing = orig_path.with_suffix(orig_path.suffix + f".bak_{uuid.uuid4().hex[:4]}")
                shutil.move(str(orig_path), str(backup_existing))

            # Move de volta
            shutil.move(str(q_path), str(orig_path))

            # Remove do manifesto
            manifest = self.load_batch_manifest(record.batch_id)
            if manifest:
                manifest.items = [it for it in manifest.items if it.id != record.id]
                manifest.total_size_bytes = max(0, manifest.total_size_bytes - record.size_bytes)
                self._save_batch_manifest(manifest)

            app_logger.info(f"Item restaurado da quarentena com sucesso: {record.original_path}")
            app_logger.log_event("restore_success", record.to_dict(), status="success")
            return True, None

        except Exception as e:
            err_msg = f"Erro ao restaurar '{record.original_path}': {e}"
            app_logger.error(err_msg)
            app_logger.log_event("restore_failed", {"record": record.to_dict(), "error": str(e)}, status="error", error=str(e))
            return False, err_msg

    def restore_batch(self, batch_id: str) -> Tuple[int, int, List[str]]:
        """
        Restaura todos os itens de um determinado lote de quarentena.
        Retorna (sucessos, falhas, lista_de_erros).
        """
        manifest = self.load_batch_manifest(batch_id)
        if not manifest or not manifest.items:
            return 0, 0, [f"Lote '{batch_id}' não encontrado ou vazio."]

        successes = 0
        failures = 0
        errors = []

        for item in list(manifest.items):
            ok, err = self.restore_item(item)
            if ok:
                successes += 1
            else:
                failures += 1
                if err:
                    errors.append(err)

        return successes, failures, errors

    def list_all_batches(self) -> List[BatchQuarantineManifest]:
        """Lista todos os lotes de quarentena disponíveis no sistema."""
        manifests = []
        if not QUARANTINE_MANIFESTS_DIR.exists():
            return []
        for file in QUARANTINE_MANIFESTS_DIR.glob("*.json"):
            batch_id = file.stem
            m = self.load_batch_manifest(batch_id)
            if m:
                manifests.append(m)
        manifests.sort(key=lambda x: x.created_at, reverse=True)
        return manifests

    def get_all_quarantined_items(self) -> List[QuarantineRecord]:
        """Retorna todos os itens individuais atualmente em quarentena."""
        all_items = []
        for batch in self.list_all_batches():
            all_items.extend(batch.items)
        return all_items

    def purge_item(self, record: QuarantineRecord) -> Tuple[bool, Optional[str]]:
        """Exclui permanentemente um item que já está dentro da quarentena."""
        q_path = Path(record.quarantine_path)
        try:
            if q_path.exists():
                if record.is_directory:
                    shutil.rmtree(str(q_path), ignore_errors=True)
                else:
                    q_path.unlink(missing_ok=True)

            manifest = self.load_batch_manifest(record.batch_id)
            if manifest:
                manifest.items = [it for it in manifest.items if it.id != record.id]
                manifest.total_size_bytes = max(0, manifest.total_size_bytes - record.size_bytes)
                self._save_batch_manifest(manifest)

            app_logger.info(f"Item purgado permanentemente da quarentena: {record.original_path}")
            app_logger.log_event("purge_item_success", record.to_dict(), status="success")
            return True, None
        except Exception as e:
            err_msg = f"Erro ao purgar item da quarentena: {e}"
            app_logger.error(err_msg)
            return False, err_msg

    def purge_batch(self, batch_id: str) -> Tuple[bool, Optional[str]]:
        """Exclui permanentemente um lote inteiro e seu manifesto."""
        manifest = self.load_batch_manifest(batch_id)
        if not manifest:
            return False, f"Lote '{batch_id}' não encontrado."

        batch_dir = QUARANTINE_DIR / batch_id
        if batch_dir.exists():
            shutil.rmtree(str(batch_dir), ignore_errors=True)

        manifest_path = self._get_batch_manifest_path(batch_id)
        manifest_path.unlink(missing_ok=True)

        app_logger.info(f"Lote de quarentena purgado: {batch_id}")
        app_logger.log_event("purge_batch_success", {"batch_id": batch_id}, status="success")
        return True, None

    def purge_expired(self, days: int = DEFAULT_QUARANTINE_RETENTION_DAYS) -> Tuple[int, int]:
        """Purga lotes de quarentena que ultrapassaram o período de retenção."""
        cutoff = datetime.now() - timedelta(days=days)
        purged_count = 0
        freed_bytes = 0

        for batch in self.list_all_batches():
            if batch.created_at < cutoff:
                freed_bytes += batch.total_size_bytes
                ok, _ = self.purge_batch(batch.batch_id)
                if ok:
                    purged_count += 1

        return purged_count, freed_bytes


# Instância global compartilhada
quarantine_manager = QuarantineManager()
