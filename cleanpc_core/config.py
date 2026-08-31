"""
Configurações e caminhos padrão do Mega Limpador & Otimizador de PC.
"""

import os
from pathlib import Path

# Nome da Aplicação
APP_NAME = "MegaLimpador"
APP_VERSION = "1.0.0"

# Diretórios base no AppData do usuário
_LOCALAPPDATA = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
BASE_DATA_DIR = Path(_LOCALAPPDATA) / APP_NAME

# Diretório de Quarentena
QUARANTINE_DIR = BASE_DATA_DIR / "quarantine"
QUARANTINE_MANIFESTS_DIR = QUARANTINE_DIR / "manifests"

# Diretório de Logs
LOGS_DIR = BASE_DATA_DIR / "logs"
ACTIVITY_LOG_FILE = LOGS_DIR / "cleanpc_activity.jsonl"
DEBUG_LOG_FILE = LOGS_DIR / "cleanpc_debug.log"

# Diretório de Relatórios
REPORTS_DIR = BASE_DATA_DIR / "reports"

# Configurações de Retenção e Segurança
DEFAULT_QUARANTINE_RETENTION_DAYS = 15
MAX_PARALLEL_WORKERS = min(32, (os.cpu_count() or 4) * 4)
CHUNK_SIZE_HASH = 65536  # 64KB para cálculo de hash streaming

def ensure_directories():
    """Garante que as pastas essenciais do aplicativo existam."""
    BASE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    QUARANTINE_MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
