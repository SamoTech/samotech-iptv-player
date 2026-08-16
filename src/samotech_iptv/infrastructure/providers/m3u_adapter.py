"""M3U provider adapter composed from source loading and canonical parsing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.playback import ResolvedPlayback
from samotech_iptv.application.ports.provider_capabilities import (
    CapabilityProvider,
    CatalogProvider,
    PlaybackProvider,
    SearchProvider,
)
from samotech_iptv.core.diagnostics import DiagnosticTrace
from samotech_iptv.core.exceptions import ProviderError, ValidationError
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.url import URL
from samotech_iptv.infrastructure.parsing.m3u_parser import M3UParser
from samotech_iptv.infrastructure.parsing.m3u_source_loader import (
    M3USourceLoader,
    M3USourceLoaderPort,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.domain.entities.channel import Channel
    from samotech_iptv.domain.value_objects.channel_id import ChannelId
    from samotech_iptv.infrastructure.parsing.m3u_parser import ParsedM3UPlaylist
    from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
    from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
    from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

__all__ = ["M3UProviderAdapter", "register_m3u_with_factory"]

_LOG = get_logger(__name__)

_CAPABILITIES = frozenset(
    {
        ProviderCapability.LIVE,
        ProviderCapability.SEARCH,
        ProviderCapability.STREAM_RESOLUTION,
    }
)


class M3UProviderAdapter(CatalogProvider, PlaybackProvider, SearchProvider, CapabilityProvider):
    """Load local or remote M3U content into the canonical live-channel catalogue."""

    def __init__(
        self,
        metadata: InfraProviderMetadata,
        context: ProviderContext,
        source_loader: M3USourceLoaderPort | None = None,
        parser: M3UParser | None = None,
    ) -> None:
        self._metadata = metadata
        self._context = context
        self._source = metadata.base_url
        self._source_loader = source_loader or M3USourceLoader(context.http_client)
        self._parser = parser or M3UParser()

    @property
    def provider_id(self) -> ProviderId:
        """Return the registered provider identity."""
        return ProviderId(self._metadata.provider_id)

    def supported_capabilities(self) -> frozenset[ProviderCapability]:
        """Return only capabilities executable by the current M3U adapter."""
        return _CAPABILITIES

    async def load_channels(self) -> Sequence[Channel]:
        """Load source text then translate it through the canonical M3U parser."""
        return (await self._load_playlist()).channels

    async def resolve_stream(self, channel_id: ChannelId) -> ResolvedPlayback:
        """Resolve one parsed M3U channel through the supported player URL boundary."""
        playlist = await self._load_playlist()
        for channel in playlist.channels:
            if channel.id != channel_id:
                continue
            stream = playlist.stream_for(channel)
            try:
                return ResolvedPlayback.from_url(URL(stream.url.value))
            except ValidationError as exc:
                raise ProviderError("M3U channel has no supported playback URL") from exc
        raise ProviderError("M3U channel was not found")

    async def _load_playlist(self) -> ParsedM3UPlaylist:
        """Fetch and parse the current playlist without retaining sensitive stream URLs."""
        trace = DiagnosticTrace("LOAD_CHANNELS", str(self.provider_id), "M3UProviderAdapter")
        trace.start()
        with trace.stage("Source resolution", provider_id=self._metadata.provider_id):
            source = await self._resolve_source()
        _LOG.debug("M3U provider stage=source_resolved provider_id=%s", self._metadata.provider_id)
        with trace.stage("Response body", provider_id=self._metadata.provider_id):
            source_text = await self._source_loader.load(source)
        _LOG.debug(
            "M3U provider stage=parser_input provider_id=%s bytes=%d",
            self._metadata.provider_id,
            len(source_text),
        )
        with trace.stage("M3U parser", bytes=len(source_text)):
            playlist = self._parser.parse(source_text, self.provider_id)
        _LOG.debug(
            "M3U provider stage=translation provider_id=%s channels=%d",
            self._metadata.provider_id,
            len(playlist.channels),
        )
        trace.result(
            "PASS", records_received=len(playlist.channels), channels=len(playlist.channels)
        )
        return playlist

    async def _resolve_source(self) -> str:
        """Return a securely stored tokenized M3U source when one is configured."""
        if not self._metadata.source_is_secure:
            _LOG.debug(
                "M3U provider stage=source_metadata provider_id=%s secure=false",
                self._metadata.provider_id,
            )
            return self._source
        _LOG.debug(
            "M3U provider stage=credential_retrieval provider_id=%s", self._metadata.provider_id
        )
        credential = await self._context.credential_store.retrieve(self.provider_id)
        if credential is not None and credential.username == "m3u-source":
            _LOG.debug(
                "M3U provider stage=credential_retrieval provider_id=%s result=found",
                self._metadata.provider_id,
            )
            return credential.password
        _LOG.error(
            "M3U provider stage=credential_retrieval provider_id=%s result=missing",
            self._metadata.provider_id,
        )
        return self._source

    async def search_channels(self, query: str, limit: int = 100) -> Sequence[Channel]:
        """Search the loaded M3U catalogue locally."""
        if limit <= 0:
            return []
        normalized_query = query.strip().casefold()
        channels = await self.load_channels()
        return [
            channel
            for channel in channels
            if not normalized_query or normalized_query in channel.name.casefold()
        ][:limit]


def _build_m3u_adapter(
    metadata: InfraProviderMetadata,
    context: ProviderContext,
    source_loader: M3USourceLoaderPort | None = None,
) -> M3UProviderAdapter:
    return M3UProviderAdapter(metadata, context, source_loader=source_loader)


def register_m3u_with_factory(factory: ProviderFactory) -> None:
    """Register M3U adapter construction with the application-owned factory."""
    factory.register_type("m3u", _build_m3u_adapter)
