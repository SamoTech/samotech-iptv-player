"""Tests for the ProviderRegistry."""

import providers.m3u  # noqa: F401
import providers.mag  # noqa: F401
import pytest
from providers.m3u.provider import M3UProvider
from providers.mag.provider import MAGProvider
from providers.registry import ProviderRegistry


def test_registry_has_mag() -> None:
    assert "mag" in ProviderRegistry.available()


def test_registry_has_m3u() -> None:
    assert "m3u" in ProviderRegistry.available()


def test_registry_returns_correct_class() -> None:
    assert ProviderRegistry.get("mag") is MAGProvider
    assert ProviderRegistry.get("m3u") is M3UProvider


def test_registry_raises_on_unknown() -> None:
    with pytest.raises(KeyError):
        ProviderRegistry.get("nonexistent_provider")
