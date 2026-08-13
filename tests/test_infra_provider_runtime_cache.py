from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata
from samotech_iptv.infrastructure.providers.provider_runtime_cache import ProviderRuntimeCache


class FakeRuntimeProvider:
    """Provider double with observable safe lifecycle behavior."""

    def __init__(self, provider_id: str, *, fail_on_close: bool = False) -> None:
        self.provider_id = provider_id
        self.fail_on_close = fail_on_close
        self.close_calls = 0
        self._failure_callback: Callable[[str], Awaitable[None]] | None = None

    def set_runtime_failure_callback(
        self,
        callback: Callable[[str], Awaitable[None]],
    ) -> None:
        self._failure_callback = callback

    async def close(self) -> None:
        self.close_calls += 1
        if self.fail_on_close:
            raise RuntimeError("close failure")

    async def fail_terminal_authentication(self) -> None:
        assert self._failure_callback is not None
        await self._failure_callback("authentication_failure")


def _metadata(
    provider_id: str,
    *,
    base_url: str = "https://example.invalid",
) -> InfraProviderMetadata:
    return InfraProviderMetadata(
        provider_id=provider_id,
        provider_type="fake",
        base_url=f"{base_url}/{provider_id}",
    )


def _build_cache(
    created: list[FakeRuntimeProvider],
    *,
    fail_on_close: bool = False,
) -> ProviderRuntimeCache:
    factory = ProviderFactory()

    def build(metadata: InfraProviderMetadata, **_: object) -> FakeRuntimeProvider:
        provider = FakeRuntimeProvider(metadata.provider_id, fail_on_close=fail_on_close)
        created.append(provider)
        return provider

    factory.register_type("fake", build)
    return ProviderRuntimeCache(factory, object())  # type: ignore[arg-type]


def test_get_or_create_reuses_one_provider_instance() -> None:
    created: list[FakeRuntimeProvider] = []
    cache = _build_cache(created)
    metadata = _metadata("provider-a")

    first = cache.get_or_create(metadata)
    second = cache.get_or_create(metadata)

    assert first is second
    assert created == [first]
    assert cache.provider_creation_count == 1


def test_provider_ids_are_isolated() -> None:
    created: list[FakeRuntimeProvider] = []
    cache = _build_cache(created)

    provider_a = cache.get_or_create(_metadata("provider-a"))
    provider_b = cache.get_or_create(_metadata("provider-b"))

    assert provider_a is not provider_b
    assert cache.provider_creation_count == 2


@pytest.mark.asyncio
async def test_metadata_change_replaces_and_closes_old_runtime() -> None:
    created: list[FakeRuntimeProvider] = []
    cache = _build_cache(created)
    original = _metadata("provider-a")
    changed = replace(original, base_url="https://changed.example.invalid/provider-a")

    old = cache.get_or_create(original)
    new = cache.get_or_create(changed)
    await asyncio.sleep(0)

    assert new is not old
    assert old.close_calls == 1
    assert cache.provider_creation_count == 2


@pytest.mark.asyncio
async def test_invalidate_if_current_does_not_evict_replacement() -> None:
    created: list[FakeRuntimeProvider] = []
    cache = _build_cache(created)
    metadata = _metadata("provider-a")

    old = cache.get_or_create(metadata)
    await cache.invalidate("provider-a", "metadata_update")
    replacement = cache.get_or_create(metadata)
    await cache.invalidate_if_current("provider-a", old, "late_failure")

    assert old.close_calls == 1
    assert replacement.close_calls == 0
    assert cache.get_or_create(metadata) is replacement


@pytest.mark.asyncio
async def test_terminal_failure_callback_invalidates_current_runtime() -> None:
    created: list[FakeRuntimeProvider] = []
    cache = _build_cache(created)
    provider = cache.get_or_create(_metadata("provider-a"))

    await provider.fail_terminal_authentication()

    assert provider.close_calls == 1
    replacement = cache.get_or_create(_metadata("provider-a"))
    assert replacement is not provider
    assert cache.provider_creation_count == 2


@pytest.mark.asyncio
async def test_close_all_is_idempotent_and_continues_after_close_failure() -> None:
    created: list[FakeRuntimeProvider] = []
    cache = _build_cache(created, fail_on_close=True)
    first = cache.get_or_create(_metadata("provider-a"))
    second = cache.get_or_create(_metadata("provider-b"))

    await cache.close_all()
    await cache.close_all()

    assert first.close_calls == 1
    assert second.close_calls == 1
    assert cache.diagnostics()["active_provider_runtime_count"] == 0


def test_diagnostics_expose_only_aggregate_counts() -> None:
    created: list[FakeRuntimeProvider] = []
    cache = _build_cache(created)
    cache.get_or_create(_metadata("provider-a"))

    diagnostics = cache.diagnostics()

    assert diagnostics == {
        "provider_creation_count": 1,
        "active_provider_runtime_count": 1,
    }
    assert all("example.invalid" not in str(value) for value in diagnostics.values())
