"""Unit tests for MAGCredentials."""
from unittest.mock import MagicMock

import pytest
from providers.mag.credentials import MAGCredentials
from pytest import MonkeyPatch

_RUNTIME_VALUE = "session-value-for-test"


def test_repr_redacts_mac() -> None:
    creds = MAGCredentials(portal_url="https://p.example.com", mac_address="AA:BB:CC:DD:EE:FF")
    r = repr(creds)
    assert "AA:BB:CC:DD:EE:FF" not in r
    assert "redacted" in r


def test_token_setter_and_getter() -> None:
    creds = MAGCredentials(portal_url="https://p.example.com", mac_address="00:11:22:33:44:55")
    assert creds.token == ""
    creds.token = _RUNTIME_VALUE
    assert creds.token == _RUNTIME_VALUE


def test_from_keyring_raises_when_not_installed() -> None:
    import providers.mag.credentials as creds_mod
    original = creds_mod._KEYRING_AVAILABLE
    creds_mod._KEYRING_AVAILABLE = False
    try:
        with pytest.raises(RuntimeError, match="not installed"):
            MAGCredentials.from_keyring("https://p.example.com")
    finally:
        creds_mod._KEYRING_AVAILABLE = original


def test_from_keyring_happy(monkeypatch: MonkeyPatch) -> None:
    import providers.mag.credentials as creds_mod
    mock_kr = MagicMock()
    mock_kr.get_password.side_effect = lambda svc, key: (
        "AA:BB:CC:DD:EE:FF" if "mac" in key else ""
    )
    monkeypatch.setattr(creds_mod, "_keyring", mock_kr)
    monkeypatch.setattr(creds_mod, "_KEYRING_AVAILABLE", True)
    creds = MAGCredentials.from_keyring("https://portal.example.com")
    assert creds.mac_address == "AA:BB:CC:DD:EE:FF"
