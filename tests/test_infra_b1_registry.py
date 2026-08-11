"""Unit tests for ProviderRegistry and ProviderFactory."""

from __future__ import annotations

import pytest

from samotech_iptv.core.exceptions import NotFoundError
from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
from samotech_iptv.infrastructure.providers.provider_metadata import (
    InfraProviderMetadata,
)
from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry


@pytest.fixture
def registry() -> ProviderRegistry:
    return ProviderRegistry()


@pytest.fixture
def mag_meta() -> InfraProviderMetadata:
    return InfraProviderMetadata(
        provider_id="mag1",
        provider_type="mag",
        base_url="http://example.com",
    )


class TestProviderRegistry:
    def test_register_and_get(
        self, registry: ProviderRegistry, mag_meta: InfraProviderMetadata
    ) -> None:
        registry.register(mag_meta)
        retrieved = registry.get("mag1")
        assert retrieved.provider_id == "mag1"

    def test_get_raises_not_found_for_unknown(self, registry: ProviderRegistry) -> None:
        with pytest.raises(NotFoundError):
            registry.get("nonexistent")

    def test_find_returns_none_for_unknown(self, registry: ProviderRegistry) -> None:
        assert registry.find("nonexistent") is None

    def test_deregister_returns_true(
        self, registry: ProviderRegistry, mag_meta: InfraProviderMetadata
    ) -> None:
        registry.register(mag_meta)
        assert registry.deregister("mag1") is True
        assert "mag1" not in registry

    def test_deregister_returns_false_when_not_present(self, registry: ProviderRegistry) -> None:
        assert registry.deregister("ghost") is False

    def test_list_all(self, registry: ProviderRegistry, mag_meta: InfraProviderMetadata) -> None:
        registry.register(mag_meta)
        registry.register(
            InfraProviderMetadata(
                provider_id="m3u1",
                provider_type="m3u",
                base_url="http://m3u.example.com",
            )
        )
        assert len(registry.list_all()) == 2

    def test_list_by_type(
        self, registry: ProviderRegistry, mag_meta: InfraProviderMetadata
    ) -> None:
        registry.register(mag_meta)
        registry.register(
            InfraProviderMetadata(
                provider_id="m3u1",
                provider_type="m3u",
                base_url="http://m3u.example.com",
            )
        )
        mag_list = registry.list_by_type("mag")
        assert len(mag_list) == 1
        assert mag_list[0].provider_id == "mag1"

    def test_list_active_filters_inactive(self, registry: ProviderRegistry) -> None:
        registry.register(
            InfraProviderMetadata(
                provider_id="active",
                provider_type="mag",
                base_url="http://a.com",
                is_active=True,
            )
        )
        registry.register(
            InfraProviderMetadata(
                provider_id="inactive",
                provider_type="mag",
                base_url="http://b.com",
                is_active=False,
            )
        )
        assert len(registry.list_active()) == 1
        assert registry.list_active()[0].provider_id == "active"

    def test_contains_operator(
        self, registry: ProviderRegistry, mag_meta: InfraProviderMetadata
    ) -> None:
        registry.register(mag_meta)
        assert "mag1" in registry
        assert "ghost" not in registry

    def test_len(self, registry: ProviderRegistry, mag_meta: InfraProviderMetadata) -> None:
        assert len(registry) == 0
        registry.register(mag_meta)
        assert len(registry) == 1


class TestProviderFactory:
    def test_register_type_and_create(self, mag_meta: InfraProviderMetadata) -> None:
        factory = ProviderFactory()
        sentinel = object()
        factory.register_type("mag", lambda meta, **kw: sentinel)
        result = factory.create(mag_meta)
        assert result is sentinel

    def test_create_raises_not_found_for_unregistered_type(
        self, mag_meta: InfraProviderMetadata
    ) -> None:
        factory = ProviderFactory()
        with pytest.raises(NotFoundError):
            factory.create(mag_meta)

    def test_supported_types(self) -> None:
        factory = ProviderFactory()
        factory.register_type("mag", lambda m, **kw: None)
        factory.register_type("m3u", lambda m, **kw: None)
        assert factory.supported_types() == frozenset({"mag", "m3u"})

    def test_is_registered(self) -> None:
        factory = ProviderFactory()
        factory.register_type("mag", lambda m, **kw: None)
        assert factory.is_registered("mag") is True
        assert factory.is_registered("xtream") is False

    def test_kwargs_forwarded_to_constructor(self, mag_meta: InfraProviderMetadata) -> None:
        factory = ProviderFactory()
        received: dict = {}

        def constructor(meta: InfraProviderMetadata, **kwargs: object) -> None:
            received.update(kwargs)

        factory.register_type("mag", constructor)
        factory.create(mag_meta, http_client="mock_client")
        assert received["http_client"] == "mock_client"
