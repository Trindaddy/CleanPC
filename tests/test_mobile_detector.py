"""
Testes unitários para o detector de dispositivos móveis.
"""

from cleanpc_mobile.detector import MobileDeviceDetector, ConnectedMobileDevice


def test_connected_mobile_device_dataclass():
    dev = ConnectedMobileDevice(
        name="Samsung Galaxy S23",
        mode="ADB",
        device_id="R5CN123456",
        description="Conectado via Depuração USB (ADB)",
        serial="R5CN123456"
    )
    assert dev.name == "Samsung Galaxy S23"
    assert dev.mode == "ADB"
    assert dev.serial == "R5CN123456"


def test_detect_all_devices_runs_safely():
    # Garante que o detector roda sem levantar exceções não tratadas
    devices = MobileDeviceDetector.detect_all_devices()
    assert isinstance(devices, list)
