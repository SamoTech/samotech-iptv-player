from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.provider import (
    ProviderHealth,
    ProviderHealthStatus,
)
from samotech_iptv.core.exceptions import ProviderError
from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_content_resolver_port import (
        ProviderContentResolverPort,
    )

__all__ = ["CheckProviderHealth", "CheckProviderHealthRequest", "CheckProviderHealthResponse"]


@dataclass(frozen=True)
class CheckProviderHealthRequest:
    provider_id: str


@dataclass(frozen=True)
class CheckProviderHealthResponse:
    health: ProviderHealth
    error: str | None = None


class CheckProviderHealth:
    """Build a safe runtime health snapshot without loading full catalogues."""

    def __init__(self, provider_resolver: ProviderContentResolverPort) -> None:
        self._provider_resolver = provider_resolver

    def execute(self, request: CheckProviderHealthRequest) -> CheckProviderHealthResponse:
        """Read declared capabilities and current adapter auth state synchronously."""
        started = perf_counter()
        checked_at = datetime.now(UTC).isoformat()
        protocol = "unknown"
        try:
            provider = self._provider_resolver.resolve_capability_provider(request.provider_id)
            capabilities = provider.supported_capabilities()
            protocol = type(provider).__name__.removesuffix("ProviderAdapter").lower()
            authentication_status = self._authentication_state(provider)
            if authentication_status is True:
                status = ProviderHealthStatus.CONNECTED
                message = "Provider session is authenticated"
            elif authentication_status is False:
                status = ProviderHealthStatus.AUTHENTICATION_FAILED
                message = "Provider session is not authenticated"
            else:
                status = ProviderHealthStatus.UNKNOWN
                message = "Provider health is not initialized"
            return CheckProviderHealthResponse(
                health=ProviderHealth(
                    provider_id=request.provider_id,
                    protocol=protocol,
                    status=status,
                    authentication_status=authentication_status,
                    last_checked=checked_at,
                    response_time_ms=(perf_counter() - started) * 1_000,
                    live_available=ProviderCapability.LIVE in capabilities,
                    vod_available=ProviderCapability.VOD in capabilities,
                    series_available=ProviderCapability.SERIES in capabilities,
                    epg_available=ProviderCapability.EPG in capabilities,
                    message=message,
                )
            )
        except ProviderError:
            return CheckProviderHealthResponse(
                health=ProviderHealth(
                    provider_id=request.provider_id,
                    protocol=protocol,
                    status=ProviderHealthStatus.UNKNOWN,
                    last_checked=checked_at,
                    response_time_ms=(perf_counter() - started) * 1_000,
                    message="Provider health is unavailable",
                ),
                error="Provider health is unavailable",
            )
        except Exception:
            return CheckProviderHealthResponse(
                health=ProviderHealth(
                    provider_id=request.provider_id,
                    protocol=protocol,
                    status=ProviderHealthStatus.UNKNOWN,
                    last_checked=checked_at,
                    response_time_ms=(perf_counter() - started) * 1_000,
                    message="Provider health could not be read",
                ),
                error="Provider health could not be read",
            )

    @staticmethod
    def _authentication_state(provider: object) -> bool | None:
        """Read only a public auth/session state; never request or expose credentials."""
        state = getattr(provider, "session_state", None)
        state_value = getattr(state, "value", state)
        if isinstance(state_value, str):
            normalized = state_value.casefold()
            if normalized in {"authenticated", "active"}:
                return True
            if normalized in {"authentication_failed", "session_expired", "unauthenticated"}:
                return False
        authenticated = getattr(provider, "is_authenticated", None)
        return authenticated if isinstance(authenticated, bool) else None
