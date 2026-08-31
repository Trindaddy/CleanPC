"""
Sistema de Log Estruturado (JSON Lines e Texto) para Auditoria e Transparência.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import ACTIVITY_LOG_FILE, DEBUG_LOG_FILE, LOGS_DIR, ensure_directories

class StructuredLogger:
    def __init__(self):
        ensure_directories()
        self._setup_standard_logger()

    def _setup_standard_logger(self):
        self.logger = logging.getLogger("CleanPc")
        self.logger.setLevel(logging.DEBUG)
        
        # Previne handlers duplicados
        if not self.logger.handlers:
            file_handler = logging.FileHandler(DEBUG_LOG_FILE, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log_event(self, action: str, details: Dict[str, Any], status: str = "success", error: Optional[str] = None):
        """Grava uma entrada no arquivo JSON Lines de auditoria."""
        ensure_directories()
        event = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "status": status,
            "details": details,
            "error": error
        }
        try:
            with open(ACTIVITY_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.error(f"Falha ao gravar log de auditoria JSONL: {e}")

    def debug(self, msg: str):
        self.logger.debug(msg)

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def read_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Lê os eventos mais recentes do log de auditoria."""
        if not ACTIVITY_LOG_FILE.exists():
            return []
        events = []
        try:
            with open(ACTIVITY_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines[-limit:]):
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))
        except Exception as e:
            self.logger.error(f"Falha ao ler eventos de auditoria: {e}")
        return events


# Instância global compartilhada
app_logger = StructuredLogger()
