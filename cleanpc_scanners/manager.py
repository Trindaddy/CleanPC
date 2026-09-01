"""
Gerenciador Central de Scanners do CleanPc.
Coordena a execução de todos os módulos de varredura com suporte a paralelismo e progresso.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional

from cleanpc_core.config import MAX_PARALLEL_WORKERS
from cleanpc_core.models import Finding, RiskLevel, ScanCategory
from .base import BaseScanner
from .browser_cache import BrowserCacheScanner
from .gpu_shaders import GpuShadersScanner
from .app_caches import AppCachesScanner
from .windows_logs import WindowsLogsScanner
from .dev_caches import DevCachesScanner
from .duplicates import DuplicateFilesScanner
from .error_dumps import ErrorDumpsScanner
from .orphan_folders import OrphanFoldersScanner
from .recycle_bin import RecycleBinScanner
from .system_optimizations import SystemOptimizationsScanner
from .temp_files import TempFilesScanner
from .thumbnails import ThumbnailsScanner


@dataclass
class ScanSummary:
    timestamp: datetime = field(default_factory=datetime.now)
    total_findings: int = 0
    total_size_bytes: int = 0
    safe_size_bytes: int = 0
    moderate_size_bytes: int = 0
    risky_size_bytes: int = 0
    unknown_size_bytes: int = 0
    findings_by_category: Dict[str, List[Finding]] = field(default_factory=dict)
    findings_by_risk: Dict[str, List[Finding]] = field(default_factory=dict)
    duration_seconds: float = 0.0


class ScannerManager:
    def __init__(self):
        self.scanners: List[BaseScanner] = [
            TempFilesScanner(),
            BrowserCacheScanner(),
            GpuShadersScanner(),
            AppCachesScanner(),
            WindowsLogsScanner(),
            RecycleBinScanner(),
            ErrorDumpsScanner(),
            DevCachesScanner(),
            ThumbnailsScanner(),
            OrphanFoldersScanner(),
            SystemOptimizationsScanner()
        ]

    def get_scanner(self, category: ScanCategory) -> Optional[BaseScanner]:
        for s in self.scanners:
            if s.category == category:
                return s
        return None

    def run_all(
        self,
        categories: Optional[List[ScanCategory]] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> tuple[List[Finding], ScanSummary]:
        """
        Executa todos os scanners selecionados e calcula o sumário.
        """
        start_time = datetime.now()
        active_scanners = self.scanners
        if categories:
            active_scanners = [s for s in self.scanners if s.category in categories]

        all_findings: List[Finding] = []
        total_scanners = len(active_scanners)

        for idx, scanner in enumerate(active_scanners):
            if progress_callback:
                progress_callback(f"Executando {scanner.name}...", idx + 1, total_scanners)

            try:
                findings = scanner.scan(progress_callback=progress_callback)
                all_findings.extend(findings)
            except Exception as e:
                # Log e continua sem interromper os demais scanners
                pass

        # Cria sumário analítico
        summary = self._build_summary(all_findings, (datetime.now() - start_time).total_seconds())
        return all_findings, summary

    def _build_summary(self, findings: List[Finding], duration: float) -> ScanSummary:
        summary = ScanSummary(
            timestamp=datetime.now(),
            total_findings=len(findings),
            duration_seconds=round(duration, 2)
        )

        for f in findings:
            summary.total_size_bytes += f.size_bytes
            cat_name = f.category.value
            if cat_name not in summary.findings_by_category:
                summary.findings_by_category[cat_name] = []
            summary.findings_by_category[cat_name].append(f)

            risk_name = f.confidence.value
            if risk_name not in summary.findings_by_risk:
                summary.findings_by_risk[risk_name] = []
            summary.findings_by_risk[risk_name].append(f)

            if f.confidence == RiskLevel.SAFE:
                summary.safe_size_bytes += f.size_bytes
            elif f.confidence == RiskLevel.MODERATE:
                summary.moderate_size_bytes += f.size_bytes
            elif f.confidence == RiskLevel.RISKY:
                summary.risky_size_bytes += f.size_bytes
            elif f.confidence == RiskLevel.UNKNOWN:
                summary.unknown_size_bytes += f.size_bytes

        return summary
