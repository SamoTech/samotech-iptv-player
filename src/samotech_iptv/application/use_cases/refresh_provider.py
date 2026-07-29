"""RefreshProvider use-case."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from samotech_iptv.application.ports import ProviderPort
from samotech_iptv.core.logging import get_logger

_log = get_logger("use_cases.refresh_provider")


@dataclass(frozen=True)
class RefreshProviderRequest:
    provider_id: str


@dataclass(frozen=True)
class RefreshProviderResponse:
    success: bool
    error: Optional[str] = None


class RefreshProvider:
    """Refresh an active provider session (token renewal, re-auth, etc.)."""

    def __init__(self, provider: ProviderPort) -> None:
        self._provider = provider

    async def execute(self, request: RefreshProviderRequest) -> RefreshProviderResponse:
        _log.info("Refreshing provider session: %s", request.provider_id)
        try:
            success = await self._provider.refresh_session()
        except Exception as exc:  # noqa: BLE001
            _log.error("RefreshProvider error: %s", exc)
            return RefreshProviderResponse(success=False, error=str(exc))
        return RefreshProviderResponse(success=success)
