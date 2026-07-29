"""Ports package — re-exports all application port interfaces.

Usage (unchanged from Phase A)::

    from samotech_iptv.application.ports import ProviderPort, PlayerPort

Or via ISP capability interfaces::

    from samotech_iptv.application.ports import (
        AuthenticationProvider,
        CatalogProvider,
        EPGProvider,
    )
"""
# Original coarse-grained ports (backward compatibility)
from samotech_iptv.application.ports.provider_port import ProviderPort
from samotech_iptv.application.ports.player_port import PlayerPort
from samotech_iptv.application.ports.storage_port import StoragePort
from samotech_iptv.application.ports.credential_store_port import CredentialStorePort
from samotech_iptv.application.ports.notification_port import NotificationPort

# ISP fine-grained capability interfaces
from samotech_iptv.application.ports.provider_capabilities import (
    AuthenticationProvider,
    CatalogProvider,
    EPGProvider,
    SearchProvider,
    PlaybackProvider,
    SessionProvider,
    CapabilityProvider,
)

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
    "EPGProvider",
    "SearchProvider",
    "PlaybackProvider",
    "SessionProvider",
    "CapabilityProvider",
]
