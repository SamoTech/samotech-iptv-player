"""Capability-gated safe VOD detail loading through the existing provider boundary."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.content import (
    ContentItemDTO,
    ContentType,
    LoadMovieDetailsResponse,
)
from samotech_iptv.core.exceptions import ProviderError

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.content import LoadMovieDetailsRequest
    from samotech_iptv.application.ports.provider_non_live_resolver_port import (
        ProviderMovieDetailResolverPort,
    )
    from samotech_iptv.domain.entities.movie import Movie

__all__ = ["LoadMovieDetails"]


class LoadMovieDetails:
    """Load one existing canonical Movie detail through a declared provider capability."""

    def __init__(self, provider_resolver: ProviderMovieDetailResolverPort) -> None:
        self._provider_resolver = provider_resolver

    async def execute(self, request: LoadMovieDetailsRequest) -> LoadMovieDetailsResponse:
        """Return a safe detail projection or one controlled result state."""
        try:
            provider = self._provider_resolver.resolve_movie_detail_provider(request.provider_id)
            movie = await provider.load_movie_details(request.movie_id)
            if movie.provider_id.value != request.provider_id or movie.id != request.movie_id:
                raise ProviderError("Provider returned mismatched movie details")
            return LoadMovieDetailsResponse(self._movie_dto(movie))
        except ProviderError:
            return LoadMovieDetailsResponse(unsupported=True)
        except Exception:
            return LoadMovieDetailsResponse(error="Unable to load movie details")

    @staticmethod
    def _movie_dto(movie: Movie) -> ContentItemDTO:
        return ContentItemDTO(
            id=movie.id,
            provider_id=movie.provider_id.value,
            content_type=ContentType.MOVIE,
            title=movie.title,
            stream_id=movie.stream_id.value,
            category_id=movie.category_id,
            poster_url=movie.poster_url.value if movie.poster_url is not None else None,
            year=movie.year,
            rating=movie.rating,
            plot=movie.plot,
            duration_seconds=movie.duration_seconds,
            genre=movie.genre,
            director=movie.director,
            cast=movie.cast,
            country=movie.country,
            release_date=movie.release_date,
            backdrop_url=movie.backdrop_url.value if movie.backdrop_url is not None else None,
            container_extension=movie.container_extension,
        )
