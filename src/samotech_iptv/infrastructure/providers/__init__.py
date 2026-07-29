"""Provider infrastructure package.

Contains:
- ``ProviderContext``       — immutable runtime service bundle
- ``ProviderRegistry``     — register and resolve providers by ID
- ``ProviderFactory``      — instantiate providers by type name
- ``InfraProviderMetadata``— mutable runtime metadata for a registered provider
- ``MagProviderAdapter``   — wraps legacy MAGProvider (Phase B.2)
- ``MagDtoTranslator``     — translates MAG dicts to domain/app DTOs
- ``translate_mag_error``  — maps legacy errors to core domain errors
"""
from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry
from samotech_iptv.infrastructure.providers.provider_factory import ProviderFactory
from samotech_iptv.infrastructure.providers.provider_metadata import InfraProviderMetadata
from samotech_iptv.infrastructure.providers.provider_context import ProviderContext
from samotech_iptv.infrastructure.providers.mag_adapter import (
    MagProviderAdapter,
    register_with_factory,
)
from samotech_iptv.infrastructure.providers.mag_dto_translator import MagDtoTranslator
from samotech_iptv.infrastructure.providers.mag_error_translator import (
    translate_mag_error,
    translate_mag_and_raise,
)

__all__ = [
    "ProviderRegistry",
    "ProviderFactory",
    "InfraProviderMetadata",
    "ProviderContext",
    "MagProviderAdapter",
    "register_with_factory",
    "MagDtoTranslator",
    "translate_mag_error",
    "translate_mag_and_raise",
]
