"""Configuration infrastructure package.

Provides ``ConfigurationProvider``, a thin env-var + override-dict
backed reader that surfaces ``core.config`` typed settings.
"""
from samotech_iptv.infrastructure.configuration.configuration_provider import (
    ConfigurationProvider,
)

__all__ = ["ConfigurationProvider"]
