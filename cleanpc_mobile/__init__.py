"""
CleanPc Mobile Package — Detecção e Limpeza Segura de Smartphones Conectados via USB
"""

from .detector import MobileDeviceDetector, ConnectedMobileDevice
from .mobile_whitelist import is_mobile_path_protected
from .adb_scanner import AdbDeviceScanner
from .mtp_scanner import MtpDeviceScanner
from .mobile_cleaner import SafeMobileCleaner, MobileCleaningReport

__all__ = [
    "MobileDeviceDetector",
    "ConnectedMobileDevice",
    "is_mobile_path_protected",
    "AdbDeviceScanner",
    "MtpDeviceScanner",
    "SafeMobileCleaner",
    "MobileCleaningReport"
]
