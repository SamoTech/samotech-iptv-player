"""Provider infrastructure package.

Contains:
- ``ProviderRegistry``  — register and resolve providers by ID
- ``ProviderFactory``   — instantiate providers by type name
- ``InfraProviderMetadata`` — mutable runtime metadata for a registered provider

No provider adapters live here.  Adapters are added in Phase B.2+.
"""
from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry
from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata

__all__ = ["ProviderRegistry", "ProviderFactory", "InfraProviderMetadata"]
