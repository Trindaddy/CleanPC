"""
Exportador de Relatórios em Formato JSON Estruturado.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from cleanpc_core.config import REPORTS_DIR, ensure_directories
from cleanpc_core.models import Finding
from cleanpc_scanners.manager import ScanSummary


class JsonReportExporter:
    @staticmethod
    def export(findings: List[Finding], summary: ScanSummary, output_path: Path | None = None) -> Path:
        ensure_directories()
        if output_path is None:
            filename = f"cleanpc_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            output_path = REPORTS_DIR / filename

        report_data = {
            "app": "Mega Limpador & Otimizador de PC",
            "version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_findings": summary.total_findings,
                "total_size_bytes": summary.total_size_bytes,
                "total_size_mb": round(summary.total_size_bytes / (1024 * 1024), 2),
                "total_size_gb": round(summary.total_size_bytes / (1024 * 1024 * 1024), 2),
                "safe_size_bytes": summary.safe_size_bytes,
                "moderate_size_bytes": summary.moderate_size_bytes,
                "risky_size_bytes": summary.risky_size_bytes,
                "unknown_size_bytes": summary.unknown_size_bytes,
                "duration_seconds": summary.duration_seconds
            },
            "findings": [f.to_dict() for f in findings]
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        return output_path
