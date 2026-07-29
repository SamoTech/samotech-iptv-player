"""Application configuration dataclasses.

Configuration is read once at startup.  Downstream layers receive a
``AppConfig`` instance through dependency injection — they never read
environment variables directly.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

__all__ = ["AppConfig", "PlayerConfig", "NetworkConfig"]


@dataclass(frozen=True)
class NetworkConfig:
    """HTTP / network-level tunables."""

    connect_timeout: float = float(os.getenv("IPTV_CONNECT_TIMEOUT", "10"))
    read_timeout: float = float(os.getenv("IPTV_READ_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("IPTV_MAX_RETRIES", "3"))
    tls_verify: bool = os.getenv("IPTV_TLS_VERIFY", "true").lower() != "false"


@dataclass(frozen=True)
class PlayerConfig:
    """Media-player tunables (player abstraction wired in Phase C)."""

    buffer_size_mb: int = int(os.getenv("IPTV_BUFFER_MB", "16"))
    hardware_decode: bool = os.getenv("IPTV_HW_DECODE", "true").lower() != "false"


@dataclass(frozen=True)
class AppConfig:
    """Root application configuration."""

    debug: bool = os.getenv("IPTV_DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("IPTV_LOG_LEVEL", "INFO").upper()
    data_dir: str = os.getenv("IPTV_DATA_DIR", "~/.samotech_iptv")
    network: NetworkConfig = field(default_factory=NetworkConfig)
    player: PlayerConfig = field(default_factory=PlayerConfig)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Construct configuration from environment variables."""
        return cls()
