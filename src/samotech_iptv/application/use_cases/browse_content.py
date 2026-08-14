"""Browse registered non-live catalogues through existing provider capabilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.content import (
    BrowseContentResponse,
    ContentItemDTO,
    ContentType,
)
from samotech_iptv.core.diagnostics import DiagnosticTrace, log_exception, safe_label
from samotech_iptv.core.exceptions import ProviderError
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.content import BrowseContentRequest
    from samotech_iptv.application.ports.provider_content_resolver_port import (
        ProviderContentResolverPort,
    )
    from samotech_iptv.domain.entities.movie import Movie
    from samotech_iptv.domain.entities.series import Series

__all__ = ["BrowseContent"]

_LOG = get_logger(__name__)


class BrowseContent:
    """Translate existing VOD and series entities into presentation-safe catalogues."""

    def __init__(self, provider_resolver: ProviderContentResolverPort) -> None:
        self._provider_resolver = provider_resolver

    async def execute(self, request: BrowseContentRequest) -> BrowseContentResponse:
        """Load one explicitly requested non-live content family with no cache side effects."""
        trace = DiagnosticTrace(
            f"BROWSE_{request.content_type.value.upper()}", request.provider_id, "registered"
        )
        trace.start()
        try:
            if request.content_type is ContentType.MOVIE:
                vod_provider = self._provider_resolver.resolve_vod_provider(request.provider_id)
                items = tuple(self._movie_dto(movie) for movie in await vod_provider.load_movies())
            elif request.content_type is ContentType.SERIES:
                series_provider = self._provider_resolver.resolve_series_provider(
                    request.provider_id
                )
                items = tuple(
                    self._series_dto(series) for series in await series_provider.load_series()
                )
            else:
                trace.result("UNSUPPORTED", reason=request.content_type.value)
                return BrowseContentResponse(unsupported=True)
        except ProviderError:
            trace.result("UNSUPPORTED", reason=request.content_type.value)
            return BrowseContentResponse(unsupported=True)
        except Exception as exc:  # noqa: BLE001
            log_exception(
                _LOG,
                "Unable to browse registered provider content",
                exc,
                provider_id=request.provider_id,
                content_type=request.content_type.value,
            )
            trace.result("FAIL", error_type=type(exc).__name__, error=safe_label(exc))
            return BrowseContentResponse(error="Unable to load content")
        trace.result("PASS", records_received=len(items))
        return BrowseContentResponse(items=items, total=len(items))

    @staticmethod
    def _movie_dto(movie: Movie) -> ContentItemDTO:
        return ContentItemDTO(
            id=movie.id,
            provider_id=movie.provider_id.value,
            content_type=ContentType.MOVIE,
            title=movie.title,
            stream_id=movie.stream_id.value,
            category_id=movie.category_id,
            poster_url=str(movie.poster_url) if movie.poster_url is not None else None,
            year=movie.year,
            rating=movie.rating,
            plot=movie.plot,
        )

    @staticmethod
    def _series_dto(series: Series) -> ContentItemDTO:
        return ContentItemDTO(
            id=series.id,
            provider_id=series.provider_id.value,
            content_type=ContentType.SERIES,
            title=series.title,
            category_id=series.category_id,
            poster_url=str(series.poster_url) if series.poster_url is not None else None,
            year=series.year,
            rating=series.rating,
            plot=series.plot,
        )
