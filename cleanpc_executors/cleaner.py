"""
Executor Seguro de Limpeza e Quarentena.
Garante que todas as ações passem por quarentena reversível por padrão e registra logs completos.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from cleanpc_core.logger import app_logger
from cleanpc_core.models import Finding, QuarantineRecord
from cleanpc_core.quarantine import quarantine_manager
from cleanpc_core.whitelist import is_whitelisted


@dataclass
class ExecutionReport:
    batch_id: str
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    successful_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    total_freed_bytes: int = 0
    quarantine_records: List[QuarantineRecord] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class SafeCleanerExecutor:
    """Executa ações de limpeza com foco estrito em segurança e reversibilidade."""

    def __init__(self):
        self.quarantine = quarantine_manager

    def execute_cleaning(
        self,
        findings: List[Finding],
        note: str = "Limpeza de Sistema",
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> ExecutionReport:
        """
        Executa a limpeza movendo todos os itens para a quarentena.
        """
        batch_id = self.quarantine.create_batch(note=note)
        report = ExecutionReport(batch_id=batch_id)

        total_items = len(findings)
        app_logger.info(f"Iniciando lote de limpeza {batch_id} com {total_items} itens.")

        for idx, finding in enumerate(findings):
            if progress_callback:
                progress_callback(f"Processando: {Path(finding.path).name}", idx + 1, total_items)

            # 1. Blindagem de segurança: Whitelist
            if is_whitelisted(finding.path):
                report.skipped_items += 1
                msg = f"Item protegido ignorado: {finding.path}"
                report.errors.append(msg)
                app_logger.warning(msg)
                continue

            # 2. Executa movimento para a Quarentena
            success, record, err = self.quarantine.move_to_quarantine(finding, batch_id)

            if success and record:
                report.successful_items += 1
                report.total_freed_bytes += finding.size_bytes
                report.quarantine_records.append(record)
            else:
                report.failed_items += 1
                if err:
                    report.errors.append(err)

        report.completed_at = datetime.now()
        app_logger.info(
            f"Lote de limpeza {batch_id} concluído. Sucesso: {report.successful_items}, "
            f"Falhas: {report.failed_items}, Espaço liberado: {report.total_freed_bytes} bytes."
        )

        return report
