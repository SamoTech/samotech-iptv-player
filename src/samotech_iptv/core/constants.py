"""Application-wide named constants.

Only primitive values (str, int, float).  No imports from other layers.
"""

from __future__ import annotations

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "DEFAULT_PAGE_SIZE",
    "MAX_SEARCH_RESULTS",
    "EPG_LOOKAHEAD_HOURS",
    "TOKEN_REFRESH_MARGIN_SECONDS",
    "PROVIDER_REGISTRY_KEY",
]

APP_NAME: str = "SamoTech IPTV Player"
APP_VERSION: str = "0.1.0"

# Pagination
DEFAULT_PAGE_SIZE: int = 100
MAX_SEARCH_RESULTS: int = 500

# EPG
EPG_LOOKAHEAD_HOURS: int = 24

# Provider session
TOKEN_REFRESH_MARGIN_SECONDS: int = 300  # refresh 5 min before expiry

# Plugin / registry
PROVIDER_REGISTRY_KEY: str = "samotech_iptv.providers"
