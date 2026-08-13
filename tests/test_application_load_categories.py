"""Tests for browse-only registered live-category discovery."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from samotech_iptv.application.dtos.categories import LoadCategoriesRequest
from samotech_iptv.application.use_cases.load_categories import LoadCategories
from samotech_iptv.core.exceptions import ProviderError
from samotech_iptv.domain.entities.category import Category
from samotech_iptv.domain.value_objects.provider_id import ProviderId

if TYPE_CHECKING:
    from samotech_iptv.application.ports.provider_resolver_port import ProviderResolverPort


class FakeCategoryProvider:
    """Category provider double returning canonical objects only."""

    def __init__(self, categories: list[Category] | None = None, should_fail: bool = False) -> None:
        self.categories = categories or []
        self.should_fail = should_fail
        self.calls = 0

    async def load_live_categories(self) -> list[Category]:
        self.calls += 1
        if self.should_fail:
            raise RuntimeError("credential-bearing provider failure")
        return self.categories


class UnsupportedResolver:
    def resolve_category_provider(self, provider_id: str) -> object:
        raise ProviderError("Provider does not support category browsing")


class FakeResolver:
    """Registered-provider resolver double exposing only category resolution."""

    def __init__(self, provider: FakeCategoryProvider, should_fail: bool = False) -> None:
        self.provider = provider
        self.should_fail = should_fail
        self.provider_ids: list[str] = []

    def resolve_category_provider(self, provider_id: str) -> FakeCategoryProvider:
        self.provider_ids.append(provider_id)
        if self.should_fail:
            raise RuntimeError("credential-bearing resolver failure")
        return self.provider


@pytest.mark.asyncio
async def test_load_categories_resolves_registered_provider_and_translates_canonical_output() -> (
    None
):
    """The use case requests live categories through the provider resolver only."""
    provider = FakeCategoryProvider(
        [
            Category(
                id="news",
                name="News",
                provider_id=ProviderId("xtream-demo"),
                parent_id="root",
            )
        ]
    )
    resolver = FakeResolver(provider)

    response = await LoadCategories(cast("ProviderResolverPort", resolver)).execute(
        LoadCategoriesRequest(provider_id="xtream-demo")
    )

    assert response.error is None
    assert [
        (item.id, item.name, item.provider_id, item.parent_id) for item in response.categories
    ] == [("news", "News", "xtream-demo", "root")]
    assert resolver.provider_ids == ["xtream-demo"]
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_load_categories_returns_empty_catalogue_without_error() -> None:
    """An available provider may legitimately have no live categories."""
    provider = FakeCategoryProvider()

    response = await LoadCategories(cast("ProviderResolverPort", FakeResolver(provider))).execute(
        LoadCategoriesRequest(provider_id="xtream-demo")
    )

    assert response.categories == []
    assert response.error is None


@pytest.mark.asyncio
async def test_load_categories_returns_controlled_unsupported_result() -> None:
    response = await LoadCategories(cast("ProviderResolverPort", UnsupportedResolver())).execute(
        LoadCategoriesRequest(provider_id="mag-test")
    )

    assert response.categories == []
    assert response.error is None
    assert response.unsupported is True


@pytest.mark.asyncio
async def test_load_categories_returns_generic_failure_without_provider_details() -> None:
    """Provider failure detail cannot cross the application/presentation boundary."""
    provider = FakeCategoryProvider(should_fail=True)

    response = await LoadCategories(cast("ProviderResolverPort", FakeResolver(provider))).execute(
        LoadCategoriesRequest(provider_id="xtream-demo")
    )

    assert response.categories == []
    assert response.error == "Unable to load categories"
    assert "credential" not in response.error
