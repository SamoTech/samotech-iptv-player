"""MagProviderAdapter — bridges the Clean Architecture and the legacy MAGProvider.

This adapter:
  - Owns one ``MAGProvider`` instance (injected or lazily created).
  - Implements all seven ISP capability interfaces.
  - Translates legacy dicts → domain DTOs via ``MagDtoTranslator``.
  - Translates legacy exceptions → core domain errors via
    ``translate_mag_error``.
  - Registers itself with ``ProviderFactory`` at import time.
  - Never duplicates protocol logic.
  - Never exposes any ``providers.mag.*`` type to callers.

Dependency direction::

    Application (ports)
          ↓
    MagProviderAdapter
          ↓
    ProviderContext  +  MAGProvider (legacy)
          ↓
    Infrastructure Runtime (B.1)
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from samotech_iptv.application.ports.provider_capabilities import (
    AuthenticationProvider,
    CatalogProvider,
    CapabilityProvider,
    EPGProvider,
    PlaybackProvider,
    SearchProvider,
    SessionProvider,
)
from samotech_iptv.application.dtos.auth import AuthenticateRequest, AuthenticateResponse
from samotech_iptv.application.dtos.channels import ChannelDTO, LoadChannelsRequest, LoadChannelsResponse
from samotech_iptv.application.dtos.categories import CategoryDTO
from samotech_iptv.application.dtos.epg import EPGEntryDTO, LoadEPGRequest, LoadEPGResponse
from samotech_iptv.application.dtos.stream import ResolveStreamRequest, ResolveStreamResponse
from samotech_iptv.core.exceptions import ProviderError, ValidationError
from samotech_iptv.core.logging import get_logger
from samotech_iptv.infrastructure.providers.mag_dto_translator import MagDtoTranslator
from samotech_iptv.infrastructure.providers.mag_error_translator import translate_mag_and_raise
from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

__all__ = ["MagProviderAdapter"]

_log = get_logger(__name__)


class MagProviderAdapter(
    AuthenticationProvider,
    CatalogProvider,
    EPGProvider,
    SearchProvider,
    PlaybackProvider,
    SessionProvider,
    CapabilityProvider,
):
    """Adapter that wraps the legacy ``MAGProvider`` behind the ISP interfaces.

    Constructor arguments
    ---------------------
    metadata:  Runtime registration metadata (id, type, base_url).
    context:   Shared infrastructure services bundle.
    legacy_provider:
        Optional pre-built ``MAGProvider`` for testing.  When None
        the adapter constructs one lazily on first ``authenticate()``.

    Usage (production)::

        registry = ProviderRegistry()
        factory  = ProviderFactory()
        # factory already has "mag" registered (see module bottom)
        ctx = ProviderContext.build()
        adapter = factory.create(meta, context=ctx)

    Usage (test)::

        adapter = MagProviderAdapter(
            metadata=meta,
            context=ctx,
            legacy_provider=mock_mag_provider,
        )
    """

    def __init__(
        self,
        metadata: InfraProviderMetadata,
        context: ProviderContext,
        legacy_provider: Any = None,
    ) -> None:
        self._meta = metadata
        self._ctx = context
        self._legacy: Any = legacy_provider  # MAGProvider — type erased to avoid hard dep
        self._is_authenticated = False

    # ------------------------------------------------------------------ helpers

    def _ensure_provider(self) -> Any:
        """Lazily construct the legacy MAGProvider if not injected."""
        if self._legacy is None:
            try:
                from providers.mag.provider import MAGProvider  # noqa: PLC0415
            except ImportError as exc:
                raise ProviderError(
                    "Legacy MAGProvider package not found. "
                    "Ensure the 'providers' package is on sys.path."
                ) from exc

            net_cfg = self._ctx.config.network_config()
            self._legacy = MAGProvider(config={
                "portal_url": self._meta.base_url,
                "mac_address": self._meta.auth_token or "",
                "timeout_s": net_cfg.connect_timeout + net_cfg.read_timeout,
                "max_retries": net_cfg.max_retries,
                "use_keyring": False,  # keyring handled by CredentialStore
            })
        return self._legacy

    async def _call(self, coro_fn, *args, **kwargs) -> Any:  # type: ignore[no-untyped-def]
        """Invoke a legacy provider coroutine, translating any exception."""
        try:
            provider = self._ensure_provider()
            return await coro_fn(provider, *args, **kwargs)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            translate_mag_and_raise(exc)

    # ------------------------------------------------------------------ AuthenticationProvider

    async def authenticate(self, request: AuthenticateRequest) -> AuthenticateResponse:
        """Authenticate with the MAG portal and store the token."""
        _log.info("[%s] Authenticating", self._meta.provider_id)
        try:
            provider = self._ensure_provider()
            await provider.connect()
            token = provider._session.token
            self._is_authenticated = True
            self._meta.auth_token = token
            _log.info("[%s] Authentication successful", self._meta.provider_id)
            return MagDtoTranslator.auth_response(
                portal_url=self._meta.base_url,
                token=token,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._is_authenticated = False
            translate_mag_and_raise(exc)

    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated

    # ------------------------------------------------------------------ SessionProvider

    async def refresh_session(self) -> None:
        """Refresh the MAG portal token."""
        _log.info("[%s] Refreshing session", self._meta.provider_id)
        await self._call(lambda p: p.refresh_token())

    async def close_session(self) -> None:
        """Close the underlying MAGProvider connection gracefully."""
        if self._legacy is not None:
            try:
                await self._legacy.close()
                _log.info("[%s] Session closed", self._meta.provider_id)
            except Exception as exc:  # noqa: BLE001
                _log.warning("[%s] Error during close: %s", self._meta.provider_id, exc)

    # ------------------------------------------------------------------ CatalogProvider

    async def load_channels(
        self, request: LoadChannelsRequest
    ) -> LoadChannelsResponse:
        """Fetch live TV channels from the MAG catalogue."""
        _log.info("[%s] Loading channels", self._meta.provider_id)
        raw: list[dict] = await self._call(lambda p: p.get_channels())
        dtos = MagDtoTranslator.channels(raw or [])
        _log.info("[%s] Loaded %d channels", self._meta.provider_id, len(dtos))
        return LoadChannelsResponse(channels=dtos, total=len(dtos))

    async def load_categories(self, category_type: str = "live") -> list[CategoryDTO]:
        """Return an empty list — MAG does not have a standalone categories endpoint.

        Categories are embedded within channel records.  A dedicated endpoint
        may be added in a future MAG protocol extension phase.
        """
        return []

    # ------------------------------------------------------------------ EPGProvider

    async def load_epg(
        self, request: LoadEPGRequest
    ) -> LoadEPGResponse:
        """Fetch EPG data from the MAG portal."""
        _log.info("[%s] Loading EPG (channel_ids=%s)",
                  self._meta.provider_id, request.channel_ids)
        channel_ids: list[int] | None = (
            [int(cid) for cid in request.channel_ids]
            if request.channel_ids else None
        )
        raw: dict = await self._call(
            lambda p: p.get_epg(channel_ids=channel_ids, period=request.period_days)
        )
        entries_by_channel = MagDtoTranslator.epg(raw or {})
        _log.info("[%s] EPG loaded for %d channels",
                  self._meta.provider_id, len(entries_by_channel))
        return LoadEPGResponse(entries_by_channel=entries_by_channel)

    # ------------------------------------------------------------------ SearchProvider

    async def search_channels(
        self, query: str, channels: Optional[list[ChannelDTO]] = None
    ) -> list[ChannelDTO]:
        """Search channels by name prefix (client-side, no server round-trip).

        MAG does not expose a server-side search endpoint.  We filter the
        already-loaded channel list in memory.
        """
        if channels is None:
            raw: list[dict] = await self._call(lambda p: p.get_channels())
            channels = MagDtoTranslator.channels(raw or [])

        q = query.strip().lower()
        if not q:
            return channels
        return [ch for ch in channels if q in ch.name.lower()]

    # ------------------------------------------------------------------ PlaybackProvider

    async def resolve_stream(
        self, request: ResolveStreamRequest
    ) -> ResolveStreamResponse:
        """Resolve a playback URL for the given stream ID."""
        _log.info("[%s] Resolving stream id=%s type=%s",
                  self._meta.provider_id, request.stream_id, request.stream_type)
        try:
            stream_id_int = int(request.stream_id)
        except (ValueError, TypeError) as exc:
            raise ValidationError(
                f"Invalid stream_id {request.stream_id!r}: must be an integer string"
            ) from exc

        url: str = await self._call(
            lambda p: p.get_stream_url(
                stream_id=stream_id_int,
                stream_type=request.stream_type or "live",
            )
        )
        _log.info("[%s] Stream resolved -> %s", self._meta.provider_id, url[:60])
        return MagDtoTranslator.stream_response(url=url, stream_id=request.stream_id)

    # ------------------------------------------------------------------ CapabilityProvider

    def capabilities(self) -> frozenset[str]:
        """Declare all capabilities this adapter supports."""
        return frozenset({
            "authentication",
            "catalog",
            "epg",
            "search",
            "playback",
            "session",
        })

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities()


# ---------------------------------------------------------------------------
# Factory registration — executed once when this module is first imported.
# ---------------------------------------------------------------------------

def _build_mag_adapter(
    metadata: InfraProviderMetadata,
    context: ProviderContext,
    legacy_provider: Any = None,
) -> MagProviderAdapter:
    return MagProviderAdapter(
        metadata=metadata,
        context=context,
        legacy_provider=legacy_provider,
    )


def register_with_factory(factory) -> None:  # type: ignore[no-untyped-def]
    """Register the MAG adapter type with a ``ProviderFactory``.

    Called explicitly by application startup code::

        from samotech_iptv.infrastructure.providers.mag_adapter import register_with_factory
        register_with_factory(provider_factory)

    We do *not* auto-register against a module-level singleton factory because
    that would require a global instance, which violates the no-globals rule.
    """
    factory.register_type("mag", _build_mag_adapter)
    _log.info("MagProviderAdapter registered with ProviderFactory")
