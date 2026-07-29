"""Tests for the ProviderRegistry."""
import pytest
import providers.mag  # noqa: F401
import providers.m3u  # noqa: F401

from providers.registry import ProviderRegistry
from providers.mag.provider import MAGProvider
from providers.m3u.provider import M3UProvider


def test_registry_has_mag():
    assert "mag" in ProviderRegistry.available()


def test_registry_has_m3u():
    assert "m3u" in ProviderRegistry.available()


def test_registry_returns_correct_class():
    assert ProviderRegistry.get("mag") is MAGProvider
    assert ProviderRegistry.get("m3u") is M3UProvider


def test_registry_raises_on_unknown():
    with pytest.raises(KeyError):
        ProviderRegistry.get("nonexistent_provider")
