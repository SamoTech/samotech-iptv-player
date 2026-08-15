"""Capability-oriented Xtream live-channel provider adapter."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from samotech_iptv.application.ports.provider_capabilities import (
    AuthenticationProvider,
    CapabilityProvider,
    CatalogProvider,
    CategoryProvider,
    EPGProvider,
    EpisodePlaybackProvider,
    MovieDetailProvider,
    MoviePlaybackProvider,
    PlaybackProvider,
    SearchProvider,
    SeriesDetailProvider,
    SeriesProvider,
    VodProvider,
)
from samotech_iptv.core.diagnostics import DiagnosticTrace
from samotech_iptv.core.exceptions import AuthenticationError, ValidationError
from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.url import URL
from samotech_iptv.infrastructure.providers.xtream_api_client import XtreamApiClient
from samotech_iptv.infrastructure.providers.xtream_domain_translator import XtreamDomainTranslator
from samotech_iptv.infrastructure.providers.xtream_request_builder import XtreamRequestBuilder

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.domain.entities.category import Category
    from samotech_iptv.domain.entities.channel import Channel
    from samotech_iptv.domain.entities.epg_entry import EPGEntry
    from samotech_iptv.domain.entities.episode import Episode
    from samotech_iptv.domain.entities.movie import Movie
    from samotech_iptv.domain.entities.season import Season
    from samotech_iptv.domain.entities.series import Series
    from samotech_iptv.domain.value_objects.channel_id import ChannelId
    from samotech_iptv.domain.value_objects.credential import Credential
    from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
    from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
    from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

__all__ = ["XtreamProviderAdapter", "register_xtream_with_factory"]

_CAPABILITIES = frozenset(
    {
        ProviderCapability.AUTHENTICATION,
        ProviderCapability.LIVE,
        ProviderCapability.CATEGORIES,
        ProviderCapability.EPG,
        ProviderCapability.STREAM_RESOLUTION,
        ProviderCapability.VOD,
        ProviderCapability.SERIES,
        ProviderCapability.MOVIE_PLAYBACK,
        ProviderCapability.SERIES_DETAILS,
        ProviderCapability.EPISODE_PLAYBACK,
        ProviderCapability.SEARCH,
    }
)


class XtreamProviderAdapter(
    AuthenticationProvider,
    CatalogProvider,
    CategoryProvider,
    EPGProvider,
    PlaybackProvider,
    VodProvider,
    SeriesProvider,
    MovieDetailProvider,
    MoviePlaybackProvider,
    SeriesDetailProvider,
    EpisodePlaybackProvider,
    SearchProvider,
    CapabilityProvider,
):
    """Retrieve Xtream content through canonical, credential-safe boundaries."""

    def __init__(self, metadata: InfraProviderMetadata, context: ProviderContext) -> None:
        self._metadata = metadata
        self._context = context
        self._authenticated = False

    @property
    def provider_id(self) -> ProviderId:
        """Return the registered provider identity."""
        return ProviderId(self._metadata.provider_id)

    @property
    def is_authenticated(self) -> bool:
        """Return the result of the latest authentication attempt."""
        return self._authenticated

    def supported_capabilities(self) -> frozenset[ProviderCapability]:
        """Advertise only executable authentication, live-catalogue, and search support."""
        return _CAPABILITIES

    async def authenticate(self, credential: Credential) -> bool:
        """Validate credentials remotely before storing them in the configured credential store."""
        client = self._client_for(credential)
        self._authenticated = await client.authenticate()
        if self._authenticated:
            await self._context.credential_store.store(self.provider_id, credential)
        return self._authenticated

    async def load_channels(self) -> Sequence[Channel]:
        """Retrieve the stored credential and translate Xtream live DTOs into channels."""
        trace = DiagnosticTrace("LOAD_CHANNELS", str(self.provider_id), "XtreamProviderAdapter")
        trace.start()
        with trace.stage("Credential retrieval", provider_id=self._metadata.provider_id):
            client = await self._stored_client()
        with trace.stage("Response processing", provider_id=self._metadata.provider_id):
            records = await client.live_streams()
        with trace.stage("Domain translation", records_received=len(records)):
            channels = [
                XtreamDomainTranslator.channel(record, self.provider_id, record_index=index)
                for index, record in enumerate(records, start=1)
            ]
        trace.result("PASS", records_received=len(records), records_translated=len(channels))
        return channels

    async def load_live_categories(self) -> Sequence[Category]:
        """Retrieve stored credentials then translate Xtream live categories."""
        trace = DiagnosticTrace(
            "LOAD_LIVE_CATEGORIES", str(self.provider_id), "XtreamProviderAdapter"
        )
        trace.start()
        with trace.stage("Credential retrieval", provider_id=self._metadata.provider_id):
            client = await self._stored_client()
        with trace.stage("Response processing", provider_id=self._metadata.provider_id):
            records = await client.live_categories()
        with trace.stage("Domain translation", records_received=len(records)):
            categories = XtreamDomainTranslator.categories(records, self.provider_id)
        trace.result("PASS", categories_received=len(categories))
        return categories

    async def load_vod_categories(self) -> Sequence[Category]:
        """Retrieve stored credentials then translate Xtream VOD categories."""
        client = await self._stored_client()
        return XtreamDomainTranslator.categories(await client.vod_categories(), self.provider_id)

    async def load_series_categories(self) -> Sequence[Category]:
        """Retrieve stored credentials then translate Xtream series categories."""
        client = await self._stored_client()
        return XtreamDomainTranslator.categories(await client.series_categories(), self.provider_id)

    async def resolve_stream(self, channel_id: ChannelId) -> URL:
        """Resolve an owned live channel to its validated Xtream playback URL."""
        client = await self._stored_client()
        stream_id = self._stream_id_for(channel_id)
        for record in await client.live_streams():
            if str(record.get("stream_id") or "").strip() == stream_id:
                return client.live_stream_url(stream_id, self._live_extension(record))
        raise ValidationError("channel_id", "Xtream live channel is not available")

    async def load_epg(self, channel_id: ChannelId) -> Sequence[EPGEntry]:
        """Retrieve and translate short-EPG data for an owned Xtream live channel."""
        client = await self._stored_client()
        return XtreamDomainTranslator.epg_entries(
            await client.short_epg(self._stream_id_for(channel_id)), channel_id
        )

    async def load_movies(self) -> Sequence[Movie]:
        """Retrieve stored credentials then translate Xtream VOD DTOs into movies."""
        client = await self._stored_client()
        return [
            XtreamDomainTranslator.movie(record, self.provider_id)
            for record in await client.vod_streams()
        ]

    async def load_series(self) -> Sequence[Series]:
        """Retrieve stored credentials then translate Xtream series DTOs into series."""
        client = await self._stored_client()
        return [
            XtreamDomainTranslator.series(record, self.provider_id)
            for record in await client.series()
        ]

    async def resolve_movie_stream(self, movie_id: str, resource_id: str) -> URL:
        """Resolve one provider-owned opaque movie descriptor to a playback URL."""
        stream_id, extension = XtreamDomainTranslator.split_playback_resource(resource_id)
        if movie_id != f"{self.provider_id.value}:{stream_id}":
            raise ValidationError("movie_id", "movie does not belong to this Xtream provider")
        return (await self._stored_client()).vod_stream_url(stream_id, extension)

    async def load_movie_details(self, movie_id: str) -> Movie:
        """Load one owned Xtream VOD detail record through the shared client."""
        raw_stream_id = self._raw_owned_id(movie_id, "movie_id")
        detail = await (await self._stored_client()).vod_info(raw_stream_id)
        movie_data = detail.get("movie_data")
        info = detail.get("info")
        if not isinstance(movie_data, Mapping):
            raise ValidationError("movie_data", "Xtream VOD detail must include movie metadata")
        merged: dict[str, object] = dict(movie_data)
        if isinstance(info, Mapping):
            merged.update(info)
        movie = XtreamDomainTranslator.movie(merged, self.provider_id)
        if movie.id != movie_id:
            raise ValidationError("movie_id", "Xtream VOD detail does not match requested movie")
        return movie

    async def load_seasons(self, series_id: str) -> Sequence[Season]:
        """Load canonical seasons from one owned Xtream Series detail response."""
        raw_series_id = self._raw_owned_id(series_id, "series_id")
        detail = await (await self._stored_client()).series_info(raw_series_id)
        return XtreamDomainTranslator.seasons(detail, self.provider_id, series_id)

    async def load_episodes(self, series_id: str, season_number: int) -> Sequence[Episode]:
        """Load canonical episodes for one owned Xtream Series season."""
        if season_number < 1:
            raise ValidationError("season_number", "must be >= 1")
        raw_series_id = self._raw_owned_id(series_id, "series_id")
        detail = await (await self._stored_client()).series_info(raw_series_id)
        return XtreamDomainTranslator.episodes(detail, series_id, season_number)

    async def resolve_episode_stream(self, episode_id: str, resource_id: str) -> URL:
        """Resolve one provider-owned opaque episode descriptor to a playback URL."""
        self._raw_owned_id(episode_id, "episode_id")
        stream_id, extension = XtreamDomainTranslator.split_playback_resource(resource_id)
        return (await self._stored_client()).episode_stream_url(stream_id, extension)

    async def search_channels(self, query: str, limit: int = 100) -> Sequence[Channel]:
        """Search retrieved canonical live channels locally without exposing provider DTOs."""
        if limit <= 0:
            return []
        normalized_query = query.strip().casefold()
        return [
            channel
            for channel in await self.load_channels()
            if not normalized_query or normalized_query in channel.name.casefold()
        ][:limit]

    async def _stored_client(self) -> XtreamApiClient:
        credential = await self._context.credential_store.retrieve(self.provider_id)
        if credential is None:
            raise AuthenticationError("Xtream credentials are not available")
        return self._client_for(credential)

    def _stream_id_for(self, channel_id: ChannelId) -> str:
        prefix = f"{self.provider_id.value}:"
        if not channel_id.value.startswith(prefix) or channel_id.value == prefix:
            raise ValidationError("channel_id", "channel does not belong to this Xtream provider")
        return channel_id.value.removeprefix(prefix)

    def _raw_owned_id(self, canonical_id: str, field: str) -> str:
        prefix = f"{self.provider_id.value}:"
        if not canonical_id.startswith(prefix) or canonical_id == prefix:
            raise ValidationError(field, "content does not belong to this Xtream provider")
        return canonical_id.removeprefix(prefix)

    @staticmethod
    def _live_extension(record: Mapping[str, object]) -> str:
        extension = str(record.get("container_extension") or "ts").strip().lower()
        if not extension.isalnum():
            raise ValidationError("container_extension", "Xtream stream extension is invalid")
        return extension

    def _client_for(self, credential: Credential) -> XtreamApiClient:
        builder = XtreamRequestBuilder(URL(self._metadata.base_url), credential)
        return XtreamApiClient(self._context.http_client, builder)


def _build_xtream_adapter(
    metadata: InfraProviderMetadata, context: ProviderContext
) -> XtreamProviderAdapter:
    return XtreamProviderAdapter(metadata, context)


def register_xtream_with_factory(factory: ProviderFactory) -> None:
    """Register Xtream construction with the application-owned provider factory."""
    factory.register_type("xtream", _build_xtream_adapter)
