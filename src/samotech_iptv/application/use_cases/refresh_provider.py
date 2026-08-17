"""RefreshProvider use-case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from samotech_iptv.core.diagnostics import log_exception
from samotech_iptv.core.error_taxonomy import safe_user_message
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from samotech_iptv.application.ports import ProviderPort

_log = get_logger("use_cases.refresh_provider")


@dataclass(frozen=True)
class RefreshProviderRequest:
    provider_id: str


@dataclass(frozen=True)
class RefreshProviderResponse:
    success: bool
    error: str | None = None


class RefreshProvider:
    """Refresh an active provider session (token renewal, re-auth, etc.)."""

    def __init__(self, provider: ProviderPort) -> None:
        self._provider = provider

    async def execute(self, request: RefreshProviderRequest) -> RefreshProviderResponse:
        _log.info("Refreshing provider session: %s", request.provider_id)
        try:
            success = await self._provider.refresh_session()
        except Exception as exc:  # noqa: BLE001
            log_exception(_log, "RefreshProvider error", exc, provider_id=request.provider_id)
            return RefreshProviderResponse(
                success=False,
                error=safe_user_message(exc, fallback="Unable to refresh provider"),
            )
        return RefreshProviderResponse(success=success)
