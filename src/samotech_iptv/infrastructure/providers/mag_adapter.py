"""MAG provider adapter for the canonical domain-oriented provider ports.

The adapter owns protocol translation and keeps MAG-specific credentials and
session state inside infrastructure.  Application code sees only domain value
objects and entities.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Protocol, TypeVar, cast

from samotech_iptv.application.ports.provider_capabilities import (
    AuthenticationProvider,
    CapabilityProvider,
    CatalogProvider,
    EPGProvider,
    PlaybackProvider,
    SearchProvider,
    SessionProvider,
)
from samotech_iptv.application.ports.provider_port import ProviderPort
from samotech_iptv.core.exceptions import ProviderError, ValidationError
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.infrastructure.providers.mag_credential import MagCredential
from samotech_iptv.infrastructure.providers.mag_domain_translator import MagDomainTranslator
from samotech_iptv.infrastructure.providers.mag_error_translator import translate_mag_and_raise

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Mapping, Sequence

    from samotech_iptv.domain.entities.channel import Channel
    from samotech_iptv.domain.entities.epg_entry import EPGEntry
    from samotech_iptv.domain.value_objects.channel_id import ChannelId
    from samotech_iptv.domain.value_objects.credential import Credential
    from samotech_iptv.domain.value_objects.url import URL
    from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
    from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
    from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

__all__ = ["MagProviderAdapter", "register_with_factory"]

_LOG = get_logger(__name__)
_T = TypeVar("_T")


class _LegacyMagProvider(Protocol):
    """Minimal legacy MAG facade required by this adapter."""

    async def connect(self) -> None: ...

    async def close(self) -> None: ...

    async def refresh_token(self) -> None: ...

    async def get_channels(self) -> list[dict[str, object]]: ...

    async def get_epg(
        self, channel_ids: list[int] | None = None, period: int = 3
    ) -> dict[int | str, list[dict[str, object]]]: ...

    async def get_stream_url(self, stream_id: int, stream_type: str = "live") -> str: ...


class MagProviderAdapter(
    ProviderPort,
    AuthenticationProvider,
    CatalogProvider,
    EPGProvider,
    SearchProvider,
    PlaybackProvider,
    SessionProvider,
    CapabilityProvider,
):
    """Adapt the legacy MAG/Stalker provider to the application provider ports.

    ``Credential.username`` is the authorised MAG MAC address.  The adapter
    combines it with the registered provider's portal URL only when an
    authentication attempt occurs.  Short-lived portal tokens remain private
    runtime state and are never stored in provider metadata.
    """

    def __init__(
        self,
        metadata: InfraProviderMetadata,
        context: ProviderContext,
        legacy_provider: _LegacyMagProvider | None = None,
    ) -> None:
        self._meta = metadata
        self._ctx = context
        self._legacy = legacy_provider
        self._credential: MagCredential | None = None
        self._session_token: str | None = None
        self._is_authenticated = False

    @property
    def provider_id(self) -> ProviderId:
        """Return this registered provider's stable application identity."""
        return ProviderId(self._meta.provider_id)

    @property
    def is_authenticated(self) -> bool:
        """Whether this adapter holds a successfully established MAG session."""
        return self._is_authenticated

    def supported_capabilities(self) -> frozenset[str]:
        """Return the canonical capability names supported by MAG."""
        return frozenset(
            {"authentication", "catalog", "epg", "search", "playback", "session"}
        )

    async def authenticate(self, credential: Credential) -> bool:
        """Authenticate using the MAG MAC address supplied by the application.

        The generic credential's username maps to the MAG subscription MAC.
        The legacy protocol does not submit its password field; no session
        token is persisted or copied into registration metadata.
        """
        mag_credential = MagCredential.from_application_credential(
            credential, self._meta.base_url
        )
        self._set_credential(mag_credential)
        _LOG.info("[%s] Authenticating MAG provider", self._meta.provider_id)
        try:
            provider = self._ensure_provider()
            await provider.connect()
            self._session_token = self._read_session_token(provider)
            self._is_authenticated = True
            return True
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._is_authenticated = False
            self._session_token = None
            translate_mag_and_raise(exc)

    async def refresh_session(self) -> bool:
        """Refresh the active MAG session token without exposing it."""
        await self._call(lambda provider: provider.refresh_token())
        self._session_token = self._read_session_token(self._ensure_provider())
        self._is_authenticated = True
        return True

    async def close_session(self) -> None:
        """Close the legacy connection and discard volatile session state."""
        if self._legacy is None:
            return
        try:
            await self._legacy.close()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - shutdown must be best effort
            _LOG.warning("[%s] Error during MAG session close: %s", self._meta.provider_id, exc)
        finally:
            self._is_authenticated = False
            self._session_token = None

    async def load_channels(self) -> Sequence[Channel]:
        """Fetch and translate the MAG live-TV catalogue."""
        raw = await self._call(lambda provider: provider.get_channels())
        return MagDomainTranslator.channels(raw, self.provider_id)

    async def load_epg(self, channel_id: ChannelId) -> Sequence[EPGEntry]:
        """Fetch and translate EPG records for a single channel."""
        numeric_channel_id = self._as_mag_numeric_id(channel_id)
        raw = await self._call(
            lambda provider: provider.get_epg(channel_ids=[numeric_channel_id])
        )
        records = self._epg_records_for_channel(raw, numeric_channel_id)
        return MagDomainTranslator.epg_entries(records, channel_id)

    async def search_channels(self, query: str, limit: int = 100) -> Sequence[Channel]:
        """Search the MAG catalogue locally because MAG has no search endpoint."""
        if limit <= 0:
            return []
        normalized_query = query.strip().casefold()
        channels = await self.load_channels()
        matches = (
            channel
            for channel in channels
            if not normalized_query or normalized_query in channel.name.casefold()
        )
        return list(matches)[:limit]

    async def resolve_stream(self, channel_id: ChannelId) -> URL:
        """Resolve a playable URL for a MAG channel identifier."""
        stream_id = self._as_mag_numeric_id(channel_id)
        raw_url = await self._call(
            lambda provider: provider.get_stream_url(stream_id=stream_id, stream_type="live")
        )
        return MagDomainTranslator.stream_url(raw_url)

    def _set_credential(self, credential: MagCredential) -> None:
        """Set the connection credential while rejecting identity changes in-session."""
        if self._credential is not None and self._credential != credential:
            raise ProviderError(
                "MAG credentials cannot be changed on an active provider instance; "
                "create a new provider session instead."
            )
        self._credential = credential

    def _ensure_provider(self) -> _LegacyMagProvider:
        """Return a legacy provider, building it only after credentials are supplied."""
        if self._legacy is not None:
            return self._legacy
        if self._credential is None:
            raise ProviderError("Authenticate before invoking a MAG provider operation")

        try:
            from providers.mag.provider import MAGProvider
        except ImportError as exc:  # pragma: no cover - exercised by packaging smoke tests
            raise ProviderError(
                "Legacy MAG provider package not found. Ensure the providers package is installed."
            ) from exc

        network = self._ctx.config.network_config()
        legacy_config = self._credential.as_legacy_config(
            timeout_s=network.connect_timeout + network.read_timeout,
            max_retries=network.max_retries,
        )
        self._legacy = cast("_LegacyMagProvider", MAGProvider(config=legacy_config))
        return self._legacy

    async def _call(self, operation: Callable[[_LegacyMagProvider], Awaitable[_T]]) -> _T:
        """Run a legacy operation and translate all non-cancellation errors."""
        try:
            return await operation(self._ensure_provider())
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            translate_mag_and_raise(exc)

    @staticmethod
    def _as_mag_numeric_id(channel_id: ChannelId) -> int:
        try:
            return int(str(channel_id))
        except (TypeError, ValueError) as exc:
            raise ValidationError("channel_id", "MAG channel IDs must be numeric") from exc

    @staticmethod
    def _epg_records_for_channel(
        raw: Mapping[int | str, list[dict[str, object]]], channel_id: int
    ) -> list[dict[str, object]]:
        return raw.get(channel_id) or raw.get(str(channel_id), [])

    @staticmethod
    def _read_session_token(provider: _LegacyMagProvider) -> str | None:
        """Read the legacy runtime token without leaking it from infrastructure."""
        session = getattr(provider, "_session", None)
        token = getattr(session, "token", None)
        return str(token) if token else None


def _build_mag_adapter(
    metadata: InfraProviderMetadata,
    context: ProviderContext,
    legacy_provider: _LegacyMagProvider | None = None,
) -> MagProviderAdapter:
    return MagProviderAdapter(
        metadata=metadata,
        context=context,
        legacy_provider=legacy_provider,
    )


def register_with_factory(factory: ProviderFactory) -> None:
    """Register MAG adapter construction with an application-owned factory."""
    factory.register_type("mag", _build_mag_adapter)
    _LOG.info("MAG provider adapter registered with ProviderFactory")
