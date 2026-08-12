"""OS keyring-backed credential storage with secret-safe error handling."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from samotech_iptv.application.ports.credential_store_port import CredentialStorePort
from samotech_iptv.core.exceptions import StorageError
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.value_objects.credential import Credential

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["KeyringCredentialStore"]

_LOG = get_logger(__name__)
_SERVICE_PREFIX = "samotech_iptv"


class KeyringCredentialStore(CredentialStorePort):
    """Store provider credentials through the operating system's native keyring."""

    def _service_name(self, provider_id: ProviderId) -> str:
        return f"{_SERVICE_PREFIX}:{provider_id.value}"

    async def store(self, provider_id: ProviderId, credential: Credential) -> None:
        """Persist one provider credential without blocking the application event loop."""
        try:
            import keyring  # noqa: PLC0415

            await asyncio.to_thread(
                keyring.set_password,
                self._service_name(provider_id),
                credential.username,
                credential.password,
            )
            _LOG.info("Stored provider credential")
        except Exception as exc:
            _LOG.error("Unable to store provider credential")
            raise StorageError("Credential storage is unavailable") from exc

    async def retrieve(self, provider_id: ProviderId) -> Credential | None:
        """Retrieve one provider credential, returning ``None`` when it is absent."""
        try:
            import keyring  # noqa: PLC0415

            entry = await asyncio.to_thread(
                keyring.get_credential,
                self._service_name(provider_id),
                None,
            )
            if entry is None:
                _LOG.debug("No provider credential found")
                return None
            _LOG.debug("Retrieved provider credential")
            return Credential(username=entry.username, _password=entry.password)
        except Exception as exc:
            _LOG.error("Unable to retrieve provider credential")
            raise StorageError("Credential storage is unavailable") from exc

    async def delete(self, provider_id: ProviderId) -> bool:
        """Delete one provider credential and report whether an entry existed."""
        try:
            import keyring  # noqa: PLC0415

            service = self._service_name(provider_id)
            entry = await asyncio.to_thread(keyring.get_credential, service, None)
            if entry is None:
                return False
            await asyncio.to_thread(keyring.delete_password, service, entry.username)
            _LOG.info("Deleted provider credential")
            return True
        except Exception as exc:
            _LOG.error("Unable to delete provider credential")
            raise StorageError("Credential storage is unavailable") from exc

    async def exists(self, provider_id: ProviderId) -> bool:
        """Return whether a provider credential is available without exposing its value."""
        try:
            import keyring  # noqa: PLC0415

            return (
                await asyncio.to_thread(
                    keyring.get_credential,
                    self._service_name(provider_id),
                    None,
                )
            ) is not None
        except Exception:
            _LOG.warning("Provider credential availability check failed")
            return False
