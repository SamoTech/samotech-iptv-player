"""ProviderCapability value object — canonical provider feature declarations."""

from __future__ import annotations

from enum import StrEnum

__all__ = ["ProviderCapability"]


class ProviderCapability(StrEnum):
    """A provider feature that is explicitly implemented and available at runtime."""

    AUTHENTICATION = "authentication"
    SESSION = "session"
    LIVE = "live"
    CATEGORIES = "categories"
    VOD = "vod"
    SERIES = "series"
    MOVIE_PLAYBACK = "movie_playback"
    SERIES_DETAILS = "series_details"
    EPISODE_PLAYBACK = "episode_playback"
    EPG = "epg"
    CATCHUP = "catchup"
    SEARCH = "search"
    STREAM_RESOLUTION = "stream_resolution"
