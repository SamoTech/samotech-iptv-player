from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from samotech_iptv.core.exceptions import StorageError
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.infrastructure.security.keyring_credential_store import (
    KeyringCredentialStore,
)

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch

_SENSITIVE_BACKEND_MESSAGE = "backend rejected password=opaque-secret"


class FakeKeyringBackend:
    """In-memory keyring double used to validate the adapter contract."""

    def __init__(self) -> None:
        self.entries: dict[tuple[str, str], str] = {}

    def set_password(self, service: str, username: str, password: str) -> None:
        self.entries[(service, username)] = password

    def get_credential(self, service: str, _: None) -> SimpleNamespace | None:
        for (stored_service, username), password in self.entries.items():
            if stored_service == service:
                return SimpleNamespace(username=username, password=password)
        return None

    def delete_password(self, service: str, username: str) -> None:
        del self.entries[(service, username)]


class FailingKeyringBackend(FakeKeyringBackend):
    """Keyring double that exposes sensitive backend details if not sanitized."""

    def set_password(self, service: str, username: str, password: str) -> None:
        del service, username, password
        raise RuntimeError(_SENSITIVE_BACKEND_MESSAGE)


def _install_keyring_backend(monkeypatch: MonkeyPatch, backend: FakeKeyringBackend) -> None:
    module = ModuleType("keyring")
    module.set_password = backend.set_password
    module.get_credential = backend.get_credential
    module.delete_password = backend.delete_password
    monkeypatch.setitem(sys.modules, "keyring", module)


@pytest.mark.asyncio
async def test_keyring_store_retrieve_exists_and_delete_credentials(
    monkeypatch: MonkeyPatch,
) -> None:
    backend = FakeKeyringBackend()
    _install_keyring_backend(monkeypatch, backend)
    store = KeyringCredentialStore()
    provider_id = ProviderId("demo")
    credential = Credential(username="user", _password="opaque-secret")  # noqa: S106

    await store.store(provider_id, credential)

    assert await store.exists(provider_id) is True
    assert await store.retrieve(provider_id) == credential
    assert await store.delete(provider_id) is True
    assert await store.delete(provider_id) is False
    assert await store.retrieve(provider_id) is None


@pytest.mark.asyncio
async def test_keyring_store_hides_backend_exception_details(
    monkeypatch: MonkeyPatch,
    caplog: LogCaptureFixture,
) -> None:
    _install_keyring_backend(monkeypatch, FailingKeyringBackend())
    credential = Credential(username="user", _password="opaque-secret")  # noqa: S106

    with pytest.raises(StorageError, match="Credential storage is unavailable") as error:
        await KeyringCredentialStore().store(ProviderId("demo"), credential)

    assert _SENSITIVE_BACKEND_MESSAGE not in str(error.value)
    assert _SENSITIVE_BACKEND_MESSAGE not in caplog.text
