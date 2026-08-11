"""Core layer — infrastructure-independent primitives.

This package contains only:
- Configuration dataclasses
- Application-wide constants
- Logging factory
- Base exception hierarchy
- Result / Either monad
- Domain event base types
- Shared type aliases

Allowed dependencies: stdlib only.
Forbidden: domain, application, infrastructure, presentation, providers.
"""

from samotech_iptv.core.events import DomainEvent
from samotech_iptv.core.exceptions import (
    ConfigurationError,
    SamotechError,
    ValidationError,
)
from samotech_iptv.core.result import Err, Ok, Result

__all__ = [
    "SamotechError",
    "ConfigurationError",
    "ValidationError",
    "Result",
    "Ok",
    "Err",
    "DomainEvent",
]
