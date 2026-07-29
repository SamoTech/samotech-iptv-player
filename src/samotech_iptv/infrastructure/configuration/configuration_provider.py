"""Environment-variable and override-dict backed configuration provider.

Priority order (highest wins):
  1. Explicit overrides passed at construction
  2. OS environment variables
  3. Hardcoded defaults in ``core.config.AppConfig``
"""
from __future__ import annotations

import os
from typing import Any, Optional

from samotech_iptv.core.config import AppConfig, NetworkConfig, PlayerConfig
from samotech_iptv.core.logging import get_logger

__all__ = ["ConfigurationProvider"]

_log = get_logger(__name__)


class ConfigurationProvider:
    """Reads configuration from environment variables and/or a dict of overrides.

    Usage::

        provider = ConfigurationProvider(overrides={"debug": True})
        cfg = provider.app_config()
        net = provider.network_config()

    Environment variables (uppercase, prefix ``SAMOTECH_``)::

        SAMOTECH_DEBUG=true
        SAMOTECH_LOG_LEVEL=DEBUG
        SAMOTECH_CONNECT_TIMEOUT=15.0
        SAMOTECH_READ_TIMEOUT=60.0
        SAMOTECH_MAX_RETRIES=5
        SAMOTECH_PAGE_SIZE=200
    """

    _ENV_PREFIX = "SAMOTECH_"

    def __init__(self, overrides: Optional[dict[str, Any]] = None) -> None:
        self._overrides: dict[str, Any] = overrides or {}

    # ------------------------------------------------------------------ public API

    def app_config(self) -> AppConfig:
        """Return a fully resolved ``AppConfig``."""
        debug = self._get_bool("debug", False)
        log_level = self._get_str("log_level", "INFO")
        page_size = self._get_int("page_size", 100)
        _log.debug("AppConfig resolved: debug=%s log_level=%s page_size=%d",
                   debug, log_level, page_size)
        return AppConfig(debug=debug, log_level=log_level, page_size=page_size)

    def network_config(self) -> NetworkConfig:
        """Return a fully resolved ``NetworkConfig``."""
        connect_timeout = self._get_float("connect_timeout", 10.0)
        read_timeout = self._get_float("read_timeout", 30.0)
        max_retries = self._get_int("max_retries", 3)
        _log.debug("NetworkConfig: connect=%.1f read=%.1f retries=%d",
                   connect_timeout, read_timeout, max_retries)
        return NetworkConfig(
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            max_retries=max_retries,
        )

    def player_config(self) -> PlayerConfig:
        """Return a fully resolved ``PlayerConfig``."""
        return PlayerConfig()

    def get(self, key: str, default: Any = None) -> Any:
        """Generic typed getter: override > env > default."""
        return self._resolve(key, default)

    # ------------------------------------------------------------------ internals

    def _resolve(self, key: str, default: Any) -> Any:
        if key in self._overrides:
            return self._overrides[key]
        env_key = self._ENV_PREFIX + key.upper()
        env_val = os.environ.get(env_key)
        if env_val is not None:
            return env_val
        return default

    def _get_bool(self, key: str, default: bool) -> bool:
        raw = self._resolve(key, default)
        if isinstance(raw, bool):
            return raw
        return str(raw).lower() in ("true", "1", "yes")

    def _get_str(self, key: str, default: str) -> str:
        return str(self._resolve(key, default))

    def _get_int(self, key: str, default: int) -> int:
        return int(self._resolve(key, default))

    def _get_float(self, key: str, default: float) -> float:
        return float(self._resolve(key, default))
