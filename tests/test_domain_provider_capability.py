"""Tests for the canonical provider capability domain vocabulary."""

from __future__ import annotations

from samotech_iptv.domain.value_objects.provider_capability import ProviderCapability


def test_provider_capability_defines_the_supported_canonical_vocabulary() -> None:
    """Capability declarations distinguish discovery, sessions, and stream resolution."""
    assert set(ProviderCapability) == {
        ProviderCapability.AUTHENTICATION,
        ProviderCapability.SESSION,
        ProviderCapability.LIVE,
        ProviderCapability.VOD,
        ProviderCapability.SERIES,
        ProviderCapability.EPG,
        ProviderCapability.CATCHUP,
        ProviderCapability.SEARCH,
        ProviderCapability.STREAM_RESOLUTION,
    }


def test_provider_capability_preserves_its_canonical_wire_value() -> None:
    """Capabilities remain safe to serialize into configuration or presentation boundaries."""
    assert str(ProviderCapability.STREAM_RESOLUTION) == "stream_resolution"
    assert ProviderCapability.LIVE == "live"
