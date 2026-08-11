"""Infrastructure configuration composition boundary.

Precedence is explicit constructor overrides, then ``IPTV_*`` environment
variables, then the defaults declared in the core configuration data models.
Core and domain code never read process environment variables directly.
"""
from __future__ import annotations

import os
from collections.abc import Mapping

from samotech_iptv.core.config import AppConfig, NetworkConfig, PlayerConfig
from samotech_iptv.core.exceptions import ConfigurationError
from samotech_iptv.core.logging import get_logger

__all__ = ["ConfigurationProvider"]

_LOG = get_logger(__name__)


class ConfigurationProvider:
    """Compose immutable application configuration from overrides and environment.

    Recognised environment variables are ``IPTV_DEBUG``, ``IPTV_LOG_LEVEL``,
    ``IPTV_DATA_DIR``, ``IPTV_CONNECT_TIMEOUT``, ``IPTV_READ_TIMEOUT``,
    ``IPTV_MAX_RETRIES``, ``IPTV_TLS_VERIFY``, ``IPTV_BUFFER_MB`` and
    ``IPTV_HW_DECODE``.
    """

    _ENV_PREFIX = "IPTV_"

    def __init__(self, overrides: Mapping[str, object] | None = None) -> None:
        self._overrides = dict(overrides or {})

    def app_config(self) -> AppConfig:
        """Return a fully composed root configuration object."""
        config = AppConfig(
            debug=self._get_bool("debug", AppConfig.debug),
            log_level=self._get_str("log_level", AppConfig.log_level).upper(),
            data_dir=self._get_str("data_dir", AppConfig.data_dir),
            network=self.network_config(),
            player=self.player_config(),
        )
        _LOG.debug("Application configuration resolved: debug=%s log_level=%s", config.debug, config.log_level)
        return config

    def network_config(self) -> NetworkConfig:
        """Return validated HTTP and retry configuration."""
        connect_timeout = self._get_float("connect_timeout", NetworkConfig.connect_timeout)
        read_timeout = self._get_float("read_timeout", NetworkConfig.read_timeout)
        max_retries = self._get_int("max_retries", NetworkConfig.max_retries)
        tls_verify = self._get_bool("tls_verify", NetworkConfig.tls_verify)

        if connect_timeout <= 0:
            raise ConfigurationError("connect_timeout must be greater than zero")
        if read_timeout <= 0:
            raise ConfigurationError("read_timeout must be greater than zero")
        if max_retries < 1:
            raise ConfigurationError("max_retries must be at least one")

        return NetworkConfig(
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            max_retries=max_retries,
            tls_verify=tls_verify,
        )

    def player_config(self) -> PlayerConfig:
        """Return validated media-player configuration."""
        buffer_size_mb = self._get_int("buffer_mb", PlayerConfig.buffer_size_mb)
        if buffer_size_mb <= 0:
            raise ConfigurationError("buffer_mb must be greater than zero")
        return PlayerConfig(
            buffer_size_mb=buffer_size_mb,
            hardware_decode=self._get_bool("hw_decode", PlayerConfig.hardware_decode),
        )

    def get(self, key: str, default: object | None = None) -> object | None:
        """Return an unresolved value using the standard precedence order."""
        return self._resolve(key, default)

    def _resolve(self, key: str, default: object | None) -> object | None:
        if key in self._overrides:
            return self._overrides[key]
        return os.environ.get(f"{self._ENV_PREFIX}{key.upper()}", default)

    def _get_bool(self, key: str, default: bool) -> bool:
        raw = self._resolve(key, default)
        if isinstance(raw, bool):
            return raw
        normalized = str(raw).strip().casefold()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
        raise ConfigurationError(f"{key} must be a boolean value")

    def _get_str(self, key: str, default: str) -> str:
        raw = self._resolve(key, default)
        value = str(raw).strip()
        if not value:
            raise ConfigurationError(f"{key} must not be blank")
        return value

    def _get_int(self, key: str, default: int) -> int:
        raw = self._resolve(key, default)
        try:
            return int(str(raw))
        except (TypeError, ValueError) as exc:
            raise ConfigurationError(f"{key} must be an integer") from exc

    def _get_float(self, key: str, default: float) -> float:
        raw = self._resolve(key, default)
        try:
            return float(str(raw))
        except (TypeError, ValueError) as exc:
            raise ConfigurationError(f"{key} must be a number") from exc
