"""MAG provider adapter for the canonical domain-oriented provider ports.

The adapter owns protocol translation and keeps MAG-specific credentials and
session state inside infrastructure.  Application code sees only domain value
objects and entities.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Literal, Protocol, TypeVar, cast

from samotech_iptv.application.dtos.playback import ResolvedPlayback
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
from samotech_iptv.core.diagnostics import log_exception
from samotech_iptv.core.exceptions import AuthenticationError, ProviderError, ValidationError
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.entities.category import Category
from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.infrastructure.providers.mag_credential import MagCredential
from samotech_iptv.infrastructure.providers.mag_domain_translator import (
    MagDomainTranslator,
)
from samotech_iptv.infrastructure.providers.mag_error_translator import translate_mag_error

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Mapping, Sequence

    from samotech_iptv.domain.entities.channel import Channel
    from samotech_iptv.domain.entities.epg_entry import EPGEntry
    from samotech_iptv.domain.value_objects.channel_id import ChannelId
    from samotech_iptv.domain.value_objects.credential import Credential
    from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
    from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
    from samotech_iptv.infrastructure.providers.provider_metadata import (
        InfraProviderMetadata,
    )

__all__ = ["MagProviderAdapter", "register_with_factory"]

_LOG = get_logger(__name__)
_T = TypeVar("_T")
MagSessionState = Literal[
    "no_session", "authenticating", "authenticated", "authentication_failed", "session_expired"
]
_MAG_CAPABILITIES = frozenset(
    {
        ProviderCapability.AUTHENTICATION,
        ProviderCapability.SESSION,
        ProviderCapability.LIVE,
        ProviderCapability.CATEGORIES,
        ProviderCapability.EPG,
        ProviderCapability.SEARCH,
        ProviderCapability.STREAM_RESOLUTION,
    }
)


class _LegacyMagProvider(Protocol):
    """Minimal legacy MAG facade required by this adapter."""

    async def connect(self) -> None: ...

    async def close(self) -> None: ...

    async def refresh_token(self) -> None: ...

    async def get_live_categories(self) -> list[dict[str, object]]: ...

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
        self._session_state: MagSessionState = "no_session"
        self._auth_lock = asyncio.Lock()
        self._runtime_failure_callback: Callable[[str], Awaitable[None]] | None = None

    def set_runtime_failure_callback(
        self,
        callback: Callable[[str], Awaitable[None]],
    ) -> None:
        """Register an infrastructure-only callback for terminal session failures."""
        self._runtime_failure_callback = callback

    @property
    def provider_id(self) -> ProviderId:
        """Return this registered provider's stable application identity."""
        return ProviderId(self._meta.provider_id)

    @property
    def is_authenticated(self) -> bool:
        """Whether this adapter holds a successfully established MAG session."""
        return self._is_authenticated

    @property
    def session_state(self) -> MagSessionState:
        """Return the explicit, testable MAG lifecycle state."""
        return self._session_state

    def supported_capabilities(self) -> frozenset[ProviderCapability]:
        """Return only the capabilities implemented by this MAG adapter."""
        return _MAG_CAPABILITIES

    async def authenticate(self, credential: Credential) -> bool:
        """Authenticate using the MAG MAC address supplied by the application."""
        self._set_credential(
            MagCredential.from_application_credential(credential, self._meta.base_url)
        )
        return await self._authenticate_current()

    async def refresh_session(self) -> bool:
        """Refresh the active MAG session token without exposing it."""
        await self._ensure_authenticated()
        try:
            await self._call_once(lambda provider: provider.refresh_token())
        except AuthenticationError:
            await self._notify_runtime_failure("authentication_failure")
            raise
        self._session_token = self._read_session_token(self._ensure_provider())
        self._is_authenticated = True
        self._session_state = "authenticated"
        return True

    async def close_session(self) -> None:
        """Close the legacy connection and discard volatile session state."""
        try:
            if self._legacy is not None:
                await self._legacy.close()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - shutdown must be best effort
            _LOG.warning("[%s] Error during MAG session close: %s", self._meta.provider_id, exc)
        finally:
            self._is_authenticated = False
            self._session_token = None
            self._session_state = "no_session"

    async def load_live_categories(self) -> Sequence[Category]:
        """Translate compatibility-profile live genres into canonical categories."""
        await self._ensure_authenticated()
        provider = self._ensure_provider()
        if not bool(getattr(provider, "supports_live_categories", False)):
            raise ProviderError("Provider does not support category browsing")
        try:
            raw = await self._call_once(lambda current: current.get_live_categories())
        except AuthenticationError:
            await self._notify_runtime_failure("authentication_failure")
            raise
        categories: list[Category] = []
        for record in raw:
            category_id = str(record.get("id") or "").strip()
            name = str(record.get("title") or record.get("name") or "").strip()
            if not category_id or not name:
                continue
            categories.append(Category(id=category_id, name=name, provider_id=self.provider_id))
        _LOG.info(
            "[IPTV] MAG LIVE_CATEGORIES provider_id=%s records=%d translated=%d",
            self._meta.provider_id,
            len(raw),
            len(categories),
        )
        return categories

    async def load_channels(self) -> Sequence[Channel]:
        """Fetch and translate the MAG live-TV catalogue."""
        started = time.perf_counter()
        _LOG.info("[IPTV] MAG LOAD_CHANNELS provider_id=%s", self._meta.provider_id)
        raw = await self._call(lambda provider: provider.get_channels())
        channels = MagDomainTranslator.channels(raw, self.provider_id)
        _LOG.info(
            "[IPTV] MAG LOAD_CHANNELS SUCCESS provider_id=%s records=%d elapsed=%.3fs",
            self._meta.provider_id,
            len(channels),
            time.perf_counter() - started,
        )
        return channels

    async def load_epg(self, channel_id: ChannelId) -> Sequence[EPGEntry]:
        """Fetch and translate EPG records for a single channel."""
        numeric_channel_id = self._as_mag_numeric_id(channel_id)
        _LOG.info("[IPTV] MAG LOAD_EPG provider_id=%s", self._meta.provider_id)
        raw = await self._call(lambda provider: provider.get_epg(channel_ids=[numeric_channel_id]))
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

    async def resolve_stream(self, channel_id: ChannelId) -> ResolvedPlayback:
        """Resolve a playable URL for a MAG channel identifier."""
        started = time.perf_counter()
        _LOG.info("[IPTV] MAG STREAM_RESOLUTION provider_id=%s", self._meta.provider_id)
        stream_id = self._as_mag_numeric_id(channel_id)
        raw_url = await self._call(
            lambda provider: provider.get_stream_url(stream_id=stream_id, stream_type="live")
        )
        resolved = MagDomainTranslator.stream_url(raw_url)
        _LOG.info(
            "[IPTV] MAG STREAM_RESOLUTION SUCCESS provider_id=%s elapsed=%.3fs",
            self._meta.provider_id,
            time.perf_counter() - started,
        )
        return ResolvedPlayback.from_url(resolved)

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
        """Authenticate, run one operation, and retry once after session expiry."""
        await self._ensure_authenticated()
        try:
            return await self._call_once(operation)
        except AuthenticationError:
            if self._credential is None:
                raise
            self._session_state = "session_expired"
            self._is_authenticated = False
            _LOG.warning(
                "[IPTV] MAG SESSION EXPIRED provider_id=%s operation=retry",
                self._meta.provider_id,
            )
            await self._authenticate_current()
            _LOG.info("[IPTV] MAG REAUTH provider_id=%s", self._meta.provider_id)
            return await self._call_once(operation)

    async def _call_once(self, operation: Callable[[_LegacyMagProvider], Awaitable[_T]]) -> _T:
        try:
            return await operation(self._ensure_provider())
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            translated = translate_mag_error(exc)
            raise translated from exc

    async def _ensure_authenticated(self) -> None:
        if self._is_authenticated and self._session_token:
            return
        if self._credential is None:
            stored = await self._ctx.credential_store.retrieve(self.provider_id)
            if stored is None:
                self._session_state = "authentication_failed"
                await self._notify_runtime_failure("authentication_failure")
                raise AuthenticationError("MAG credentials are not available")
            self._set_credential(
                MagCredential.from_application_credential(stored, self._meta.base_url)
            )
        await self._authenticate_current()

    async def _authenticate_current(self) -> bool:
        if self._credential is None:
            self._session_state = "authentication_failed"
            await self._notify_runtime_failure("authentication_failure")
            raise AuthenticationError("MAG credentials are not available")
        async with self._auth_lock:
            if self._is_authenticated and self._session_token:
                return True
            started = time.perf_counter()
            self._session_state = "authenticating"
            _LOG.info(
                "[IPTV] MAG AUTH START provider_id=%s operation=connect",
                self._meta.provider_id,
            )
            try:
                provider = self._ensure_provider()
                await provider.connect()
                self._session_token = self._read_session_token(provider)
                if not self._session_token:
                    raise AuthenticationError("MAG handshake did not establish a session")
                self._is_authenticated = True
                self._session_state = "authenticated"
                _LOG.info(
                    "[IPTV] MAG AUTH SUCCESS provider_id=%s elapsed=%.3fs",
                    self._meta.provider_id,
                    time.perf_counter() - started,
                )
                return True
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._is_authenticated = False
                self._session_token = None
                self._session_state = "authentication_failed"
                log_exception(
                    _LOG,
                    "[IPTV] MAG AUTH FAILURE",
                    exc,
                    provider_id=self._meta.provider_id,
                )
                translated = translate_mag_error(exc)
                if isinstance(translated, AuthenticationError):
                    await self._notify_runtime_failure("authentication_failure")
                raise translated from exc

    async def _notify_runtime_failure(self, reason: str) -> None:
        callback = self._runtime_failure_callback
        if callback is None:
            return
        try:
            await callback(reason)
        except asyncio.CancelledError:
            raise
        except Exception:
            _LOG.debug("MAG runtime failure callback was unavailable", exc_info=True)

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
