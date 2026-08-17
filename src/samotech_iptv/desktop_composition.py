"""Production composition root for the Qt/libVLC desktop application.

This module constructs the existing application graph without reading or exposing
provider credentials, MAC identities, session tokens, secure sources, or resolved
playback URLs. Runtime start/stop ownership is intentionally left to the next
lifecycle increment.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from samotech_iptv.application.channel_catalogue_cache import ChannelCatalogueCache
from samotech_iptv.application.use_cases.browse_channels import BrowseChannels
from samotech_iptv.application.use_cases.browse_content import BrowseContent
from samotech_iptv.application.use_cases.check_provider_health import CheckProviderHealth
from samotech_iptv.application.use_cases.clear_history import ClearHistory
from samotech_iptv.application.use_cases.configure_xmltv_binding import ConfigureXMLTVBinding
from samotech_iptv.application.use_cases.list_favorites import ListFavorites
from samotech_iptv.application.use_cases.list_providers import ListProviders
from samotech_iptv.application.use_cases.load_categories import LoadCategories
from samotech_iptv.application.use_cases.load_history import LoadHistory
from samotech_iptv.application.use_cases.load_movie_details import LoadMovieDetails
from samotech_iptv.application.use_cases.load_provider_capabilities import (
    LoadProviderCapabilities,
)
from samotech_iptv.application.use_cases.load_registered_epg import LoadRegisteredEPG
from samotech_iptv.application.use_cases.load_theme_preference import LoadThemePreference
from samotech_iptv.application.use_cases.play_registered_channel import PlayRegisteredChannel
from samotech_iptv.application.use_cases.playback_controls import (
    PausePlayback,
    ResumePlayback,
    StopPlayback,
)
from samotech_iptv.application.use_cases.provider_lifecycle import (
    RemoveProvider,
    UpdateProvider,
)
from samotech_iptv.application.use_cases.record_history import RecordHistory
from samotech_iptv.application.use_cases.refresh_xmltv_guide import RefreshXMLTVGuide
from samotech_iptv.application.use_cases.register_m3u_provider import RegisterM3UProvider
from samotech_iptv.application.use_cases.register_mag_provider import RegisterMAGProvider
from samotech_iptv.application.use_cases.register_xtream_provider import RegisterXtreamProvider
from samotech_iptv.application.use_cases.remove_favorite import RemoveFavorite
from samotech_iptv.application.use_cases.save_favorite import SaveFavorite
from samotech_iptv.application.use_cases.save_theme_preference import SaveThemePreference
from samotech_iptv.application.use_cases.search_registered_channels import (
    SearchRegisteredChannels,
)
from samotech_iptv.application.use_cases.series_discovery import (
    LoadSeasonEpisodes,
    LoadSeriesSeasons,
)
from samotech_iptv.application.use_cases.start_recording import StartRecording
from samotech_iptv.application.use_cases.stop_recording import StopRecording
from samotech_iptv.core.logging import configure_logging
from samotech_iptv.desktop_bootstrap import DesktopApplication, build_desktop_application
from samotech_iptv.infrastructure.artwork_loader import BoundedArtworkLoader
from samotech_iptv.infrastructure.database.sqlite_favorite_repository import (
    SQLiteFavoriteRepository,
)
from samotech_iptv.infrastructure.database.sqlite_history_repository import SQLiteHistoryRepository
from samotech_iptv.infrastructure.database.sqlite_provider_metadata_repository import (
    SQLiteProviderMetadataRepository,
)
from samotech_iptv.infrastructure.database.sqlite_theme_preference_repository import (
    SQLiteThemePreferenceRepository,
)
from samotech_iptv.infrastructure.database.sqlite_xmltv_binding_repository import (
    SQLiteXMLTVBindingRepository,
)
from samotech_iptv.infrastructure.parsing.xmltv_guide_service import XMLTVGuideService
from samotech_iptv.infrastructure.parsing.xmltv_source_loader import LocalXMLTVSourceLoader
from samotech_iptv.infrastructure.player.composition import build_player
from samotech_iptv.infrastructure.providers.m3u_adapter import register_m3u_with_factory
from samotech_iptv.infrastructure.providers.mag_adapter import register_with_factory
from samotech_iptv.infrastructure.providers.provider_catalog_service import ProviderCatalogService
from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
from samotech_iptv.infrastructure.providers.provider_registration_service import (
    ProviderRegistrationService,
)
from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry
from samotech_iptv.infrastructure.providers.provider_resolution_service import (
    ProviderResolutionService,
)
from samotech_iptv.infrastructure.providers.provider_runtime_cache import ProviderRuntimeCache
from samotech_iptv.infrastructure.providers.xtream_adapter import register_xtream_with_factory
from samotech_iptv.presentation.task_owner import close_all_task_owners

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

__all__ = ["build_production_desktop_application"]

_DATABASE_FILENAME = "samotech_iptv.sqlite3"
_RECORDINGS_DIRECTORY = "recordings"


async def build_production_desktop_application(
    argv: Sequence[str] | None = None,
    config_overrides: Mapping[str, object] | None = None,
) -> DesktopApplication:
    """Construct the desktop shell from initialized, credential-safe infrastructure.

    The returned application is ready for the existing qasync runtime boundary.
    This composition function does not start the event loop or close runtime resources.
    """
    registry = ProviderRegistry()
    context = ProviderContext.build(overrides=config_overrides, registry=registry)
    application_config = context.config.app_config()
    configure_logging(
        application_config.log_level,
        debug=application_config.debug,
    )
    data_directory = Path(application_config.data_dir).expanduser()
    database_path = data_directory / _DATABASE_FILENAME

    provider_metadata_repository = SQLiteProviderMetadataRepository(database_path)
    favorite_repository = SQLiteFavoriteRepository(database_path)
    history_repository = SQLiteHistoryRepository(database_path)
    theme_preference_repository = SQLiteThemePreferenceRepository(database_path)
    xmltv_binding_repository = SQLiteXMLTVBindingRepository(database_path)
    await provider_metadata_repository.initialise()
    await favorite_repository.initialise()
    await history_repository.initialise()
    await theme_preference_repository.initialise()
    await xmltv_binding_repository.initialise()
    await provider_metadata_repository.restore_into(registry)

    factory = ProviderFactory()
    register_m3u_with_factory(factory)
    register_xtream_with_factory(factory)
    register_with_factory(factory)

    runtime_cache = ProviderRuntimeCache(factory, context)
    registration_service = ProviderRegistrationService(
        registry,
        context.credential_store,
        provider_metadata_repository,
        xmltv_binding_repository,
        runtime_cache,
    )
    provider_catalog_service = ProviderCatalogService(registry)
    provider_resolution_service = ProviderResolutionService(
        registry,
        factory,
        context,
        runtime_cache,
    )
    player = build_player(
        buffer_size_mb=application_config.player.buffer_size_mb,
        hardware_decode=application_config.player.hardware_decode,
    )
    record_history = RecordHistory(history_repository)
    play_registered_channel = PlayRegisteredChannel(
        provider_resolution_service,
        player,
        record_history,
        provider_resolution_service,
        history_repository=history_repository,
    )
    list_favorites = ListFavorites(favorite_repository)
    remove_favorite = RemoveFavorite(favorite_repository)
    load_history = LoadHistory(history_repository)
    clear_history = ClearHistory(history_repository)
    load_theme_preference = LoadThemePreference(theme_preference_repository)
    initial_theme = await load_theme_preference.execute()

    catalogue_cache = ChannelCatalogueCache()
    artwork_loader = BoundedArtworkLoader(context.http_client)
    desktop = build_desktop_application(
        RegisterXtreamProvider(registration_service),
        RegisterM3UProvider(registration_service),
        RegisterMAGProvider(registration_service),
        ListProviders(provider_catalog_service),
        LoadCategories(provider_resolution_service),
        UpdateProvider(registration_service, catalogue_cache),
        RemoveProvider(registration_service, catalogue_cache),
        BrowseChannels(provider_resolution_service, catalogue_cache),
        play_registered_channel,
        SearchRegisteredChannels(provider_resolution_service, catalogue_cache),
        SaveFavorite(favorite_repository),
        list_favorites,
        remove_favorite,
        load_history,
        clear_history,
        LoadRegisteredEPG(provider_resolution_service),
        ConfigureXMLTVBinding(provider_resolution_service, xmltv_binding_repository),
        RefreshXMLTVGuide(
            xmltv_binding_repository,
            XMLTVGuideService(LocalXMLTVSourceLoader()),
        ),
        load_theme_preference,
        SaveThemePreference(theme_preference_repository),
        StartRecording(player, data_directory / _RECORDINGS_DIRECTORY),
        StopRecording(player),
        PausePlayback(player),
        ResumePlayback(player),
        StopPlayback(player),
        initial_theme=initial_theme,
        argv=argv,
        player=player,
        browse_content=BrowseContent(provider_resolution_service),
        load_provider_capabilities=LoadProviderCapabilities(provider_resolution_service),
        load_movie_details=LoadMovieDetails(provider_resolution_service),
        load_series_seasons=LoadSeriesSeasons(provider_resolution_service),
        load_season_episodes=LoadSeasonEpisodes(provider_resolution_service),
        artwork_loader=artwork_loader,
        record_history=record_history,
        check_provider_health=CheckProviderHealth(provider_resolution_service),
    )

    async def close() -> None:
        """Cancel UI tasks, then release providers, player, and HTTP resources."""
        try:
            await close_all_task_owners()
            await runtime_cache.close_all()
        finally:
            try:
                await player.close()
            finally:
                await context.http_client.close()

    return replace(
        desktop,
        start=context.http_client.open,
        close=close,
    )
