"""OS keyring-backed credential store.

Implements ``CredentialStorePort`` using the ``keyring`` library which
delegates to the platform-native secret store:
  - Windows: Windows Credential Manager
  - macOS:   Keychain
  - Linux:   SecretService / KWallet
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.ports.credential_store_port import CredentialStorePort
from samotech_iptv.core.exceptions import StorageError
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.value_objects.credential import Credential

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["KeyringCredentialStore"]

_log = get_logger(__name__)
_SERVICE_PREFIX = "samotech_iptv"


class KeyringCredentialStore(CredentialStorePort):
    """OS keyring-backed implementation of ``CredentialStorePort``.

    Each provider's credentials are stored under a namespaced key::

        service  = "samotech_iptv:<provider_id>"
        username = <credential.username>
        password = <credential.password>  # stored as the secret
    """

    def _service_name(self, provider_id: ProviderId) -> str:
        return f"{_SERVICE_PREFIX}:{provider_id.value}"

    async def store(self, provider_id: ProviderId, credential: Credential) -> None:
        """Persist credentials to the OS keyring."""
        try:
            import keyring  # noqa: PLC0415

            service = self._service_name(provider_id)
            keyring.set_password(service, credential.username, credential.password)
            _log.info(
                "Stored credential for provider=%s user=%s",
                provider_id.value,
                credential.username,
            )
        except Exception as exc:
            _log.error("Failed to store credential for provider=%s: %s", provider_id.value, exc)
            raise StorageError(f"keyring.set_password failed: {exc}") from exc

    async def retrieve(self, provider_id: ProviderId) -> Credential | None:
        """Retrieve credentials from the OS keyring, or None if not found."""
        try:
            import keyring  # noqa: PLC0415

            service = self._service_name(provider_id)
            # keyring.get_credential returns (username, password) or None
            entry = keyring.get_credential(service, None)
            if entry is None:
                _log.debug("No credential found for provider=%s", provider_id.value)
                return None
            _log.debug(
                "Retrieved credential for provider=%s user=%s",
                provider_id.value,
                entry.username,
            )
            return Credential(username=entry.username, _password=entry.password)
        except Exception as exc:
            _log.error(
                "Failed to retrieve credential for provider=%s: %s",
                provider_id.value,
                exc,
            )
            raise StorageError(f"keyring.get_credential failed: {exc}") from exc

    async def delete(self, provider_id: ProviderId) -> bool:
        """Delete credentials from the OS keyring.  Returns True if deleted."""
        try:
            import keyring  # noqa: PLC0415
            import keyring.errors  # noqa: PLC0415

            service = self._service_name(provider_id)
            entry = keyring.get_credential(service, None)
            if entry is None:
                return False
            keyring.delete_password(service, entry.username)
            _log.info("Deleted credential for provider=%s", provider_id.value)
            return True
        except keyring.errors.PasswordDeleteError:
            return False
        except Exception as exc:
            _log.error(
                "Failed to delete credential for provider=%s: %s",
                provider_id.value,
                exc,
            )
            raise StorageError(f"keyring.delete_password failed: {exc}") from exc

    async def exists(self, provider_id: ProviderId) -> bool:
        """Return True if credentials exist for this provider."""
        try:
            import keyring  # noqa: PLC0415

            service = self._service_name(provider_id)
            return keyring.get_credential(service, None) is not None
        except Exception as exc:
            _log.warning(
                "keyring.get_credential check failed for provider=%s: %s",
                provider_id.value,
                exc,
            )
            return False
