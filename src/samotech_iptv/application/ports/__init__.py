"""Ports package — re-exports all application port interfaces.

Usage (unchanged from Phase A)::

    from samotech_iptv.application.ports import ProviderPort, PlayerPort

Or via ISP capability interfaces::

    from samotech_iptv.application.ports import (
        AuthenticationProvider,
        CatalogProvider,
        VodProvider,
        SeriesProvider,
        EPGProvider,
    )
"""

# Original coarse-grained ports (backward compatibility)
from samotech_iptv.application.ports.credential_store_port import CredentialStorePort
from samotech_iptv.application.ports.notification_port import NotificationPort
from samotech_iptv.application.ports.player_port import PlayerPort

# ISP fine-grained capability interfaces
from samotech_iptv.application.ports.provider_capabilities import (
    AuthenticationProvider,
    CapabilityProvider,
    CatalogProvider,
    EPGProvider,
    PlaybackProvider,
    SearchProvider,
    SeriesProvider,
    SessionProvider,
    VodProvider,
)
from samotech_iptv.application.ports.provider_port import ProviderPort
from samotech_iptv.application.ports.storage_port import StoragePort

__all__ = [
    # Original ports
    "ProviderPort",
    "PlayerPort",
    "StoragePort",
    "CredentialStorePort",
    "NotificationPort",
    # ISP capability interfaces
    "AuthenticationProvider",
    "CatalogProvider",
    "VodProvider",
    "SeriesProvider",
    "EPGProvider",
    "SearchProvider",
    "PlaybackProvider",
    "SessionProvider",
    "CapabilityProvider",
]
