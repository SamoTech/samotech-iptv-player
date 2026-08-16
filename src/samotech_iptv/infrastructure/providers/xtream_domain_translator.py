"""Translate Xtream-compatible DTOs into canonical domain objects."""

from __future__ import annotations

from base64 import b64decode
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.core.logging import get_logger
from samotech_iptv.domain.entities.account_info import AccountInfo
from samotech_iptv.domain.entities.category import Category
from samotech_iptv.domain.entities.channel import Channel
from samotech_iptv.domain.entities.epg_entry import EPGEntry
from samotech_iptv.domain.entities.episode import Episode
from samotech_iptv.domain.entities.movie import Movie
from samotech_iptv.domain.entities.season import Season
from samotech_iptv.domain.entities.series import Series
from samotech_iptv.domain.entities.server_info import ServerInfo
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.stream_id import StreamId
from samotech_iptv.domain.value_objects.url import URL

if TYPE_CHECKING:
    from collections.abc import Sequence

    from samotech_iptv.domain.value_objects.provider_id import ProviderId

__all__ = ["XtreamDomainTranslator"]

_LOG = get_logger(__name__)


class XtreamDomainTranslator:
    """Stateless mappings from Xtream API records to canonical entities."""

    @staticmethod
    def account_info(raw: Mapping[str, object], provider_id: ProviderId) -> AccountInfo:
        """Map Xtream ``user_info`` without retaining credentials or URLs."""
        auth = str(raw.get("auth") or "").strip().casefold()
        status = str(raw.get("status") or "").strip().casefold()
        normalized_status: Literal["active", "expired", "blocked", "unknown"]
        if auth in {"0", "false"} or status in {"expired", "inactive"}:
            normalized_status = "expired"
        elif status in {"blocked", "disabled", "banned"}:
            normalized_status = "blocked"
        elif auth in {"1", "true", "active"} or status in {"active", "enabled"}:
            normalized_status = "active"
        else:
            normalized_status = "unknown"
        return AccountInfo(
            provider_id=provider_id,
            status=normalized_status,
            expires_at=XtreamDomainTranslator._optional_timestamp(raw.get("exp_date")),
            active_connections=XtreamDomainTranslator._optional_nonnegative_int(
                raw.get("active_cons")
            ),
            max_connections=XtreamDomainTranslator._optional_nonnegative_int(
                raw.get("max_connections")
            ),
            message=str(raw.get("message") or "").strip() or None,
        )

    @staticmethod
    def server_info(raw: Mapping[str, object], provider_id: ProviderId) -> ServerInfo:
        """Map non-secret Xtream server metadata; never expose server URLs."""
        return ServerInfo(
            provider_id=provider_id,
            name=str(raw.get("server_name") or raw.get("name") or "").strip() or None,
            version=str(raw.get("version") or "").strip() or None,
            timezone=str(raw.get("timezone") or "").strip() or None,
            protocol=str(raw.get("server_protocol") or raw.get("protocol") or "").strip() or None,
        )

    @staticmethod
    def categories(
        raw_records: Sequence[Mapping[str, object]], provider_id: ProviderId
    ) -> list[Category]:
        """Map a single Xtream category family to canonical category entities."""
        return [XtreamDomainTranslator.category(record, provider_id) for record in raw_records]

    @staticmethod
    def category(raw: Mapping[str, object], provider_id: ProviderId) -> Category:
        """Map an Xtream category record while preserving its content-facing identifier."""
        return Category(
            id=XtreamDomainTranslator._required_text(raw, "category_id"),
            name=XtreamDomainTranslator._required_text(raw, "category_name"),
            provider_id=provider_id,
            parent_id=str(raw.get("parent_id") or "").strip() or None,
        )

    @staticmethod
    def channel(
        raw: Mapping[str, object], provider_id: ProviderId, record_index: int | None = None
    ) -> Channel:
        """Map a live-stream record while tolerating invalid optional logo metadata."""
        stream_id = XtreamDomainTranslator._required_text(raw, "stream_id")
        name = XtreamDomainTranslator._required_text(raw, "name")
        logo = XtreamDomainTranslator._optional_logo(
            raw.get("stream_icon"), provider_id, name, record_index
        )
        category_id = str(raw.get("category_id") or "").strip() or None
        epg_channel_id = str(raw.get("epg_channel_id") or "").strip() or None
        number = XtreamDomainTranslator._optional_int(raw.get("num"))
        return Channel(
            id=ChannelId(f"{provider_id.value}:{stream_id}"),
            name=name,
            provider_id=provider_id,
            stream_id=StreamId(stream_id),
            category_id=category_id,
            logo_url=logo,
            epg_channel_id=epg_channel_id,
            number=number,
        )

    @staticmethod
    def _optional_logo(
        value: object,
        provider_id: ProviderId,
        channel_name: str,
        record_index: int | None,
    ) -> URL | None:
        """Validate optional logo metadata without allowing it to abort a channel."""
        logo = str(value or "").replace("\u00a0", " ").strip()
        if not logo:
            return None
        try:
            return URL(logo)
        except ValidationError:
            _LOG.warning(
                "[IPTV][WARN] Provider=%s Record=%s Field=logo_url Reason=invalid URL "
                "Action=ignored Channel=%s",
                provider_id.value,
                record_index if record_index is not None else "unknown",
                XtreamDomainTranslator._safe_label(channel_name),
            )
            return None

    @staticmethod
    def _safe_label(value: str) -> str:
        """Keep diagnostic labels short and free from control characters."""
        return " ".join(value.split())[:120]

    @staticmethod
    def movie(raw: Mapping[str, object], provider_id: ProviderId) -> Movie:
        """Map a VOD record returned by ``get_vod_streams`` to a canonical movie."""
        stream_id = XtreamDomainTranslator._required_text(raw, "stream_id")
        title = XtreamDomainTranslator._required_text(raw, "name")
        extension = XtreamDomainTranslator._container_extension(raw)
        return Movie(
            id=f"{provider_id.value}:{stream_id}",
            title=title,
            provider_id=provider_id,
            stream_id=StreamId(XtreamDomainTranslator.playback_resource(stream_id, extension)),
            category_id=str(raw.get("category_id") or "").strip() or None,
            poster_url=XtreamDomainTranslator._optional_artwork(
                raw.get("stream_icon") or raw.get("movie_image") or raw.get("cover_big"),
                title,
                "movie",
            ),
            year=XtreamDomainTranslator._optional_catalogue_int(raw.get("year")),
            rating=XtreamDomainTranslator._optional_catalogue_float(
                raw.get("rating") or raw.get("rating_5based")
            ),
            plot=str(raw.get("plot") or raw.get("description") or "").strip() or None,
            duration_seconds=XtreamDomainTranslator._optional_duration(raw),
            genre=XtreamDomainTranslator._optional_text(raw.get("genre")),
            director=XtreamDomainTranslator._optional_text(raw.get("director")),
            cast=XtreamDomainTranslator._optional_text(raw.get("cast") or raw.get("actors")),
            country=XtreamDomainTranslator._optional_text(raw.get("country")),
            release_date=XtreamDomainTranslator._optional_text(
                raw.get("releasedate") or raw.get("release_date") or raw.get("releaseDate")
            ),
            backdrop_url=XtreamDomainTranslator._optional_backdrop(
                raw.get("backdrop_path"), title, "movie"
            ),
            container_extension=extension,
        )

    @staticmethod
    def series(raw: Mapping[str, object], provider_id: ProviderId) -> Series:
        """Map a series record returned by ``get_series`` to a canonical series."""
        series_id = XtreamDomainTranslator._required_text(raw, "series_id")
        title = XtreamDomainTranslator._required_text(raw, "name")
        raw_seasons = raw.get("seasons")
        raw_episodes = raw.get("episodes")
        season_count = XtreamDomainTranslator._optional_catalogue_int(raw.get("season_count"))
        if season_count is None and isinstance(raw_seasons, list):
            season_count = len(raw_seasons) or None
        episode_count = XtreamDomainTranslator._optional_catalogue_int(raw.get("episode_count"))
        if episode_count is None and isinstance(raw_episodes, list):
            episode_count = len(raw_episodes) or None
        return Series(
            id=f"{provider_id.value}:{series_id}",
            title=title,
            provider_id=provider_id,
            category_id=str(raw.get("category_id") or "").strip() or None,
            poster_url=XtreamDomainTranslator._optional_artwork(
                raw.get("cover") or raw.get("cover_big") or raw.get("movie_image"),
                title,
                "series",
            ),
            year=XtreamDomainTranslator._optional_catalogue_int(
                raw.get("year") or raw.get("releaseDate")
            ),
            rating=XtreamDomainTranslator._optional_catalogue_float(
                raw.get("rating") or raw.get("rating_5based")
            ),
            plot=str(raw.get("plot") or "").strip() or None,
            genre=XtreamDomainTranslator._optional_text(raw.get("genre")),
            backdrop_url=XtreamDomainTranslator._optional_backdrop(
                raw.get("backdrop_path"), title, "series"
            ),
            season_count=season_count,
            episode_count=episode_count,
        )

    @staticmethod
    def seasons(
        raw_detail: Mapping[str, object], provider_id: ProviderId, series_id: str
    ) -> list[Season]:
        """Translate an Xtream ``get_series_info`` season collection safely."""
        raw_seasons = raw_detail.get("seasons")
        if not isinstance(raw_seasons, list) or not all(
            isinstance(item, Mapping) for item in raw_seasons
        ):
            raise ValidationError("seasons", "Xtream series detail must include a list of seasons")
        seasons: list[Season] = []
        for raw in raw_seasons:
            number = XtreamDomainTranslator._season_number(raw)
            title = str(raw.get("name") or raw.get("title") or "").strip() or None
            seasons.append(
                Season(
                    id=f"{series_id}:season:{number}",
                    series_id=series_id,
                    provider_id=provider_id,
                    number=number,
                    title=title,
                )
            )
        return seasons

    @staticmethod
    def episodes(
        raw_detail: Mapping[str, object], series_id: str, season_number: int
    ) -> list[Episode]:
        """Translate one Xtream detail season into canonical opaque-ID episodes."""
        raw_episodes = raw_detail.get("episodes")
        if not isinstance(raw_episodes, Mapping):
            raise ValidationError(
                "episodes", "Xtream series detail must include episodes by season"
            )
        candidates = raw_episodes.get(str(season_number))
        if not isinstance(candidates, list) or not all(
            isinstance(item, Mapping) for item in candidates
        ):
            raise ValidationError(
                "episodes", "Xtream series detail season must include an episode list"
            )
        episodes: list[Episode] = []
        for raw in candidates:
            episode_id = XtreamDomainTranslator._required_text(raw, "id")
            episode_number = XtreamDomainTranslator._episode_number(raw)
            info = raw.get("info")
            details = info if isinstance(info, Mapping) else {}
            title = str(raw.get("title") or details.get("title") or "").strip()
            if not title:
                title = f"Episode {episode_number}"
            episodes.append(
                Episode(
                    id=f"{series_id}:episode:{episode_id}",
                    series_id=series_id,
                    title=title,
                    stream_id=StreamId(
                        XtreamDomainTranslator.playback_resource(
                            episode_id, XtreamDomainTranslator._container_extension(raw, details)
                        )
                    ),
                    season=season_number,
                    episode_number=episode_number,
                    duration_seconds=XtreamDomainTranslator._optional_duration(details),
                    plot=str(details.get("plot") or raw.get("plot") or "").strip() or None,
                )
            )
        return episodes

    @staticmethod
    def playback_resource(stream_id: str, extension: str) -> str:
        """Encode a validated opaque non-live stream descriptor without a URL."""
        if "|" in stream_id or not stream_id.strip():
            raise ValidationError("stream_id", "Xtream stream identifier is invalid")
        if not extension.isalnum():
            raise ValidationError("container_extension", "Xtream stream extension is invalid")
        return f"{stream_id}|{extension}"

    @staticmethod
    def split_playback_resource(resource_id: str) -> tuple[str, str]:
        """Decode a validated opaque non-live descriptor at the provider boundary."""
        stream_id, separator, extension = resource_id.partition("|")
        if not separator or not stream_id or not extension or "|" in extension:
            raise ValidationError("resource_id", "Xtream playback resource is invalid")
        if not extension.isalnum():
            raise ValidationError("container_extension", "Xtream stream extension is invalid")
        return stream_id, extension

    @staticmethod
    def epg_entries(
        raw_records: Sequence[Mapping[str, object]], channel_id: ChannelId
    ) -> list[EPGEntry]:
        """Map Xtream short-EPG records for a channel to canonical EPG entries."""
        return [XtreamDomainTranslator.epg_entry(record, channel_id) for record in raw_records]

    @staticmethod
    def epg_entry(raw: Mapping[str, object], channel_id: ChannelId) -> EPGEntry:
        """Map one Xtream short-EPG record to a canonical programme entry."""
        start_timestamp = XtreamDomainTranslator._required_timestamp(raw, "start_timestamp")
        end_timestamp = XtreamDomainTranslator._required_timestamp(raw, "stop_timestamp")
        title = XtreamDomainTranslator._decoded_required_text(raw, "title")
        entry_id = str(raw.get("id") or f"{channel_id.value}:{start_timestamp}:{title}").strip()
        return EPGEntry(
            id=entry_id,
            channel_id=channel_id,
            title=title,
            start=datetime.fromtimestamp(start_timestamp, tz=UTC),
            end=datetime.fromtimestamp(end_timestamp, tz=UTC),
            description=XtreamDomainTranslator._decoded_optional_text(raw.get("description")),
            category=str(raw.get("category") or "").strip() or None,
        )

    @staticmethod
    def _optional_timestamp(value: object) -> datetime | None:
        if value in (None, "", "0", 0):
            return None
        try:
            return datetime.fromtimestamp(int(str(value)), tz=UTC)
        except (TypeError, ValueError, OSError):
            return None

    @staticmethod
    def _optional_nonnegative_int(value: object) -> int | None:
        if value in (None, ""):
            return None
        try:
            parsed = int(str(value))
        except (TypeError, ValueError):
            return None
        return parsed if parsed >= 0 else None

    @staticmethod
    def _required_text(raw: Mapping[str, object], field: str) -> str:
        value = str(raw.get(field) or "").strip()
        if not value:
            raise ValidationError(field, f"Xtream response is missing {field}")
        return value

    @staticmethod
    def _decoded_required_text(raw: Mapping[str, object], field: str) -> str:
        value = XtreamDomainTranslator._decoded_optional_text(raw.get(field))
        if not value:
            raise ValidationError(field, f"Xtream response is missing {field}")
        return value

    @staticmethod
    def _decoded_optional_text(value: object) -> str | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            decoded = b64decode(text, validate=True).decode("utf-8").strip()
        except (UnicodeDecodeError, ValueError):
            return text
        return decoded or text

    @staticmethod
    def _required_timestamp(raw: Mapping[str, object], field: str) -> int:
        value = raw.get(field)
        if value in (None, "", 0, "0"):
            raise ValidationError(field, f"Xtream response is missing {field}")
        try:
            return int(str(value))
        except (TypeError, ValueError) as exc:
            raise ValidationError(field, "Xtream timestamp must be an integer") from exc

    @staticmethod
    def _container_extension(
        raw: Mapping[str, object], fallback: Mapping[str, object] | None = None
    ) -> str:
        value = (
            str(
                raw.get("container_extension")
                or (fallback or {}).get("container_extension")
                or "mp4"
            )
            .strip()
            .lower()
        )
        if not value.isalnum():
            raise ValidationError("container_extension", "Xtream stream extension is invalid")
        return value

    @staticmethod
    def _season_number(raw: Mapping[str, object]) -> int:
        value = raw.get("season_number") or raw.get("season") or raw.get("id")
        return XtreamDomainTranslator._positive_int(value, "season")

    @staticmethod
    def _episode_number(raw: Mapping[str, object]) -> int:
        value = raw.get("episode_num") or raw.get("episode_number") or raw.get("id")
        return XtreamDomainTranslator._positive_int(value, "episode_number")

    @staticmethod
    def _optional_duration(raw: Mapping[str, object]) -> int | None:
        value = raw.get("duration_secs") or raw.get("duration_seconds")
        if value in (None, ""):
            return None
        try:
            return XtreamDomainTranslator._positive_int(value, "duration_seconds", allow_zero=True)
        except ValidationError:
            return None

    @staticmethod
    def _positive_int(value: object, field: str, *, allow_zero: bool = False) -> int:
        try:
            parsed = int(str(value))
        except (TypeError, ValueError) as exc:
            raise ValidationError(field, f"Xtream {field} must be an integer") from exc
        if parsed < 0 or (parsed == 0 and not allow_zero):
            raise ValidationError(field, f"Xtream {field} must be positive")
        return parsed

    @staticmethod
    def _optional_int(value: object) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(str(value))
        except ValueError as exc:
            raise ValidationError("num", "Xtream channel number must be an integer") from exc

    @staticmethod
    def _optional_float(value: object) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(str(value))
        except ValueError as exc:
            raise ValidationError("rating", "Xtream rating must be numeric") from exc

    @staticmethod
    def _optional_catalogue_int(value: object) -> int | None:
        """Ignore malformed optional Movie/Series years without dropping the record."""
        if value in (None, ""):
            return None
        try:
            parsed = int(str(value))
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    @staticmethod
    def _optional_catalogue_float(value: object) -> float | None:
        """Ignore malformed optional Movie/Series ratings without dropping the record."""
        if value in (None, ""):
            return None
        try:
            parsed = float(str(value))
        except (TypeError, ValueError):
            return None
        return parsed if 0.0 <= parsed <= 10.0 else None

    @staticmethod
    def _optional_text(value: object) -> str | None:
        """Normalize optional descriptive text while ignoring non-string payload noise."""
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _first_artwork_value(value: object) -> str:
        """Select the first usable artwork string from scalar or list-shaped payloads."""
        if isinstance(value, (list, tuple)):
            for candidate in value:
                text = str(candidate or "").replace("\u00a0", " ").strip()
                if text:
                    return text
            return ""
        return str(value or "").replace("\u00a0", " ").strip()

    @staticmethod
    def _optional_backdrop(value: object, title: str, content_label: str) -> URL | None:
        """Translate the first provider backdrop without requiring remote image loading."""
        return XtreamDomainTranslator._optional_artwork(value, title, f"{content_label}-backdrop")

    @staticmethod
    def _optional_artwork(value: object, title: str, content_label: str) -> URL | None:
        """Ignore malformed optional artwork while retaining the catalogue item."""
        artwork = XtreamDomainTranslator._first_artwork_value(value)
        if not artwork:
            return None
        try:
            return URL(artwork)
        except ValidationError:
            _LOG.warning(
                "[IPTV][WARN] Provider content=%s Field=artwork Reason=invalid URL "
                "Action=ignored Label=%s",
                content_label,
                XtreamDomainTranslator._safe_label(title),
            )
            return None
