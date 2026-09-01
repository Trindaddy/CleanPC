"""
CleanPc Scanners Package
"""

from .base import BaseScanner
from .manager import ScannerManager, ScanSummary
from .temp_files import TempFilesScanner
from .browser_cache import BrowserCacheScanner
from .gpu_shaders import GpuShadersScanner
from .app_caches import AppCachesScanner
from .windows_logs import WindowsLogsScanner
from .recycle_bin import RecycleBinScanner
from .error_dumps import ErrorDumpsScanner
from .dev_caches import DevCachesScanner
from .thumbnails import ThumbnailsScanner
from .orphan_folders import OrphanFoldersScanner
from .duplicates import DuplicateFilesScanner
from .system_optimizations import SystemOptimizationsScanner

__all__ = [
    "BaseScanner",
    "ScannerManager",
    "ScanSummary",
    "TempFilesScanner",
    "BrowserCacheScanner",
    "GpuShadersScanner",
    "AppCachesScanner",
    "WindowsLogsScanner",
    "RecycleBinScanner",
    "ErrorDumpsScanner",
    "DevCachesScanner",
    "ThumbnailsScanner",
    "OrphanFoldersScanner",
    "DuplicateFilesScanner",
    "SystemOptimizationsScanner"
]
