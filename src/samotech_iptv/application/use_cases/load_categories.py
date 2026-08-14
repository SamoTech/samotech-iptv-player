"""Browse-only registered-provider live-category discovery."""

from __future__ import annotations

from typing import TYPE_CHECKING

from samotech_iptv.application.dtos.categories import CategoryDTO, LoadCategoriesResponse
from samotech_iptv.application.dtos.content import ContentType
from samotech_iptv.core.diagnostics import DiagnosticTrace, log_exception, safe_label
from samotech_iptv.core.exceptions import ProviderError
from samotech_iptv.core.logging import get_logger

if TYPE_CHECKING:
    from samotech_iptv.application.dtos.categories import LoadCategoriesRequest
    from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort

__all__ = ["LoadCategories"]

_LOG = get_logger(__name__)


class LoadCategories:
    """Load canonical live categories for one registered provider without playback."""

    def __init__(self, provider_resolver: ProviderResolverPort) -> None:
        self._provider_resolver = provider_resolver

    async def execute(self, request: LoadCategoriesRequest) -> LoadCategoriesResponse:
        """Resolve a registered category provider and return only safe category data."""
        trace = DiagnosticTrace(
            f"LOAD_{request.content_type.value.upper()}_CATEGORIES",
            str(request.provider_id),
            "registered",
        )
        trace.start()
        try:
            with trace.stage("Provider resolution", provider=str(request.provider_id)):
                provider = self._provider_resolver.resolve_category_provider(request.provider_id)
            with trace.stage("Category request", provider=type(provider).__name__):
                if request.content_type is ContentType.LIVE:
                    categories = await provider.load_live_categories()
                elif request.content_type is ContentType.MOVIE:
                    categories = await provider.load_vod_categories()
                elif request.content_type is ContentType.SERIES:
                    categories = await provider.load_series_categories()
                else:
                    trace.result("UNSUPPORTED", reason=request.content_type.value)
                    return LoadCategoriesResponse(unsupported=True)
        except ProviderError as exc:
            if str(exc) == "Provider does not support category browsing":
                trace.result("UNSUPPORTED", reason="category_browsing")
                return LoadCategoriesResponse(unsupported=True)
            log_exception(
                _LOG,
                "Unable to load registered provider categories",
                exc,
                provider_id=request.provider_id,
            )
            trace.result("FAIL", error_type=type(exc).__name__, error=safe_label(exc))
            return LoadCategoriesResponse(error="Unable to load categories")
        except Exception as exc:  # noqa: BLE001
            log_exception(
                _LOG,
                "Unable to load registered provider categories",
                exc,
                provider_id=request.provider_id,
            )
            trace.result("FAIL", error_type=type(exc).__name__, error=safe_label(exc))
            return LoadCategoriesResponse(error="Unable to load categories")
        trace.result("PASS", categories_received=len(categories))
        return LoadCategoriesResponse(
            categories=[
                CategoryDTO(
                    id=category.id,
                    name=category.name,
                    provider_id=category.provider_id.value,
                    parent_id=category.parent_id,
                )
                for category in categories
            ]
        )
