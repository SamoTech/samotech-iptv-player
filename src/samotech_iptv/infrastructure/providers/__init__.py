"""Provider infrastructure package.

Contains:
- ``ProviderContext``       — immutable runtime service bundle
- ``ProviderRegistry``     — register and resolve providers by ID
- ``ProviderFactory``      — instantiate providers by type name
- ``InfraProviderMetadata``— mutable runtime metadata for a registered provider
- ``MagProviderAdapter``   — wraps legacy MAGProvider (Phase B.2)
- ``MagCredential``        — MAG connection identity, separate from sessions
- ``MagDomainTranslator``  — translates MAG dicts to canonical domain objects
- ``translate_mag_error``  — maps legacy errors to core domain errors
"""

from samotech_iptv.infrastructure.providers.mag_adapter import (
    MagProviderAdapter,
    register_with_factory,
)
from samotech_iptv.infrastructure.providers.mag_credential import MagCredential
from samotech_iptv.infrastructure.providers.mag_domain_translator import (
    MagDomainTranslator,
)
from samotech_iptv.infrastructure.providers.mag_error_translator import (
    translate_mag_and_raise,
    translate_mag_error,
)
from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
from samotech_iptv.infrastructure.providers.provider_metadata import (
    InfraProviderMetadata,
)
from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry
from samotech_iptv.infrastructure.providers.provider_resolution_service import (
    ProviderResolutionService,
)

__all__ = [
    "ProviderRegistry",
    "ProviderFactory",
    "InfraProviderMetadata",
    "ProviderContext",
    "ProviderResolutionService",
    "MagProviderAdapter",
    "register_with_factory",
    "MagCredential",
    "MagDomainTranslator",
    "translate_mag_error",
    "translate_mag_and_raise",
]
