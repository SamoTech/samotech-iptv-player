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

from samotech_iptv.core.exceptions import (
    SamotechError,
    ConfigurationError,
    ValidationError,
)
from samotech_iptv.core.result import Result, Ok, Err
from samotech_iptv.core.events import DomainEvent

__all__ = [
    "SamotechError",
    "ConfigurationError",
    "ValidationError",
    "Result",
    "Ok",
    "Err",
    "DomainEvent",
]
