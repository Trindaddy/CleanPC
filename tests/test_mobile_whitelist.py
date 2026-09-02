"""
Testes unitários para a Whitelist de proteção de armazenamento de smartphones.
"""

from cleanpc_mobile.mobile_whitelist import is_mobile_path_protected


def test_camera_photos_are_protected():
    assert is_mobile_path_protected("DCIM/Camera/IMG_20260901.jpg") is True
    assert is_mobile_path_protected("/sdcard/DCIM/Camera/VID_123.mp4") is True
    assert is_mobile_path_protected("Pictures/Camera/photo.jpg") is True


def test_documents_and_music_protected():
    assert is_mobile_path_protected("Documents/Contrato.pdf") is True
    assert is_mobile_path_protected("Music/musica.mp3") is True
    assert is_mobile_path_protected("WhatsApp/Databases/msgstore.db.crypt14") is True


def test_thumbnails_and_statuses_allowed():
    # Miniaturas e Status do WhatsApp NÃO são protegidos (são seguros para limpeza)
    assert is_mobile_path_protected("DCIM/.thumbnails/thumbdata4_123") is False
    assert is_mobile_path_protected("WhatsApp/Media/.Statuses/status_video.mp4") is False
