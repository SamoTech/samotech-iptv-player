"""AuthenticateProvider use-case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos import AuthenticateRequest, AuthenticateResponse
from samotech_iptv.core.diagnostics import log_exception
from samotech_iptv.core.error_taxonomy import safe_user_message
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.value_objects import Credential

if TYPE_CHECKING:
    from samotech_iptv.application.ports import CredentialStorePort, ProviderPort

_log = get_logger("use_cases.authenticate_provider")


class AuthenticateProvider:
    """Authenticate a provider and persist credentials on success."""

    def __init__(
        self,
        provider: ProviderPort,
        credential_store: CredentialStorePort,
    ) -> None:
        self._provider = provider
        self._store = credential_store

    async def execute(self, request: AuthenticateRequest) -> AuthenticateResponse:
        _log.info("Authenticating provider %s", request.provider_id)
        try:
            credential = Credential(username=request.username, _password=request.password)
            success = await self._provider.authenticate(credential)
        except Exception as exc:  # noqa: BLE001
            log_exception(_log, "Authentication error", exc, provider_id=request.provider_id)
            return AuthenticateResponse(
                success=False,
                provider_id=request.provider_id,
                error=safe_user_message(exc, fallback="Authentication failed"),
            )
        if success:
            await self._store.store(self._provider.provider_id, credential)
        return AuthenticateResponse(
            success=success,
            provider_id=request.provider_id,
            error=None if success else "Authentication rejected by provider",
        )
