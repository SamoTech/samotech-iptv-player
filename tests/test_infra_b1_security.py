"""Unit tests for the security infrastructure layer.

The OS keyring is fully mocked — no real keyring access.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from samotech_iptv.core.exceptions import StorageError
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.domain.value_objects.provider_id import ProviderId

_AUTH_VALUE = "test-auth-value"


@pytest.fixture
def provider_id() -> ProviderId:
    return ProviderId("test-provider")


@pytest.fixture
def credential() -> Credential:
    return Credential(username="user1", _password=_AUTH_VALUE)


class TestKeyringCredentialStore:
    """Tests for KeyringCredentialStore with mocked keyring."""

    @pytest.mark.asyncio
    async def test_store_calls_keyring_set_password(
        self, provider_id: ProviderId, credential: Credential
    ) -> None:
        mock_keyring = MagicMock()
        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            from samotech_iptv.infrastructure.security.keyring_credential_store import (
                KeyringCredentialStore,
            )

            store = KeyringCredentialStore()
            await store.store(provider_id, credential)
            mock_keyring.set_password.assert_called_once_with(
                "samotech_iptv:test-provider",
                "user1",
                _AUTH_VALUE,
            )

    @pytest.mark.asyncio
    async def test_retrieve_returns_credential(self, provider_id: ProviderId) -> None:
        mock_keyring = MagicMock()
        mock_entry = MagicMock()
        mock_entry.username = "user1"
        mock_entry.password = _AUTH_VALUE
        mock_keyring.get_credential.return_value = mock_entry

        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            import sys
            from importlib import import_module

            # Force reimport with mocked keyring
            sys.modules.pop("samotech_iptv.infrastructure.security.keyring_credential_store", None)
            mod = import_module("samotech_iptv.infrastructure.security.keyring_credential_store")
            store = mod.KeyringCredentialStore()
            result = await store.retrieve(provider_id)
            assert result is not None
            assert result.username == "user1"
            assert result.password == _AUTH_VALUE

    @pytest.mark.asyncio
    async def test_retrieve_returns_none_when_not_found(self, provider_id: ProviderId) -> None:
        mock_keyring = MagicMock()
        mock_keyring.get_credential.return_value = None

        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            import sys

            sys.modules.pop("samotech_iptv.infrastructure.security.keyring_credential_store", None)
            from samotech_iptv.infrastructure.security.keyring_credential_store import (
                KeyringCredentialStore,
            )

            store = KeyringCredentialStore()
            result = await store.retrieve(provider_id)
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_returns_true_when_deleted(self, provider_id: ProviderId) -> None:
        mock_keyring = MagicMock()
        mock_entry = MagicMock()
        mock_entry.username = "user1"
        mock_keyring.get_credential.return_value = mock_entry
        mock_keyring.errors = MagicMock()
        mock_keyring.errors.PasswordDeleteError = Exception

        with patch.dict(
            "sys.modules",
            {
                "keyring": mock_keyring,
                "keyring.errors": mock_keyring.errors,
            },
        ):
            import sys

            sys.modules.pop("samotech_iptv.infrastructure.security.keyring_credential_store", None)
            from samotech_iptv.infrastructure.security.keyring_credential_store import (
                KeyringCredentialStore,
            )

            store = KeyringCredentialStore()
            result = await store.delete(provider_id)
            assert result is True

    @pytest.mark.asyncio
    async def test_store_raises_storage_error_on_keyring_failure(
        self, provider_id: ProviderId, credential: Credential
    ) -> None:
        mock_keyring = MagicMock()
        mock_keyring.set_password.side_effect = RuntimeError("keyring unavailable")

        with patch.dict("sys.modules", {"keyring": mock_keyring}):
            import sys

            sys.modules.pop("samotech_iptv.infrastructure.security.keyring_credential_store", None)
            from samotech_iptv.infrastructure.security.keyring_credential_store import (
                KeyringCredentialStore,
            )

            store = KeyringCredentialStore()
            with pytest.raises(StorageError):
                await store.store(provider_id, credential)
