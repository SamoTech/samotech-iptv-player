"""Unit tests for MAGCredentials."""
import pytest
from unittest.mock import patch, MagicMock

from providers.mag.credentials import MAGCredentials


def test_repr_redacts_mac():
    creds = MAGCredentials(portal_url="https://p.example.com", mac_address="AA:BB:CC:DD:EE:FF")
    r = repr(creds)
    assert "AA:BB:CC:DD:EE:FF" not in r
    assert "redacted" in r


def test_token_setter_and_getter():
    creds = MAGCredentials(portal_url="https://p.example.com", mac_address="00:11:22:33:44:55")
    assert creds.token == ""
    creds.token = "my-token"
    assert creds.token == "my-token"


def test_from_keyring_raises_when_not_installed():
    import providers.mag.credentials as creds_mod
    original = creds_mod._KEYRING_AVAILABLE
    creds_mod._KEYRING_AVAILABLE = False
    try:
        with pytest.raises(RuntimeError, match="not installed"):
            MAGCredentials.from_keyring("https://p.example.com")
    finally:
        creds_mod._KEYRING_AVAILABLE = original


def test_from_keyring_happy(monkeypatch):
    import providers.mag.credentials as creds_mod
    mock_kr = MagicMock()
    mock_kr.get_password.side_effect = lambda svc, key: (
        "AA:BB:CC:DD:EE:FF" if "mac" in key else ""
    )
    monkeypatch.setattr(creds_mod, "_keyring", mock_kr)
    monkeypatch.setattr(creds_mod, "_KEYRING_AVAILABLE", True)
    creds = MAGCredentials.from_keyring("https://portal.example.com")
    assert creds.mac_address == "AA:BB:CC:DD:EE:FF"
