"""Application configuration data structures.

Configuration is composed once by the infrastructure ``ConfigurationProvider``
and injected into downstream code.  Core models are deliberately free of
process-environment reads so that they remain deterministic and testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["AppConfig", "NetworkConfig", "PlayerConfig"]


@dataclass(frozen=True)
class NetworkConfig:
    """HTTP and network-level tunables."""

    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    max_retries: int = 3
    tls_verify: bool = True


@dataclass(frozen=True)
class PlayerConfig:
    """Media-player tunables for the future player adapter."""

    buffer_size_mb: int = 16
    hardware_decode: bool = True


@dataclass(frozen=True)
class AppConfig:
    """Root configuration assembled by the infrastructure composition boundary."""

    debug: bool = False
    log_level: str = "INFO"
    data_dir: str = "~/.samotech_iptv"
    network: NetworkConfig = field(default_factory=NetworkConfig)
    player: PlayerConfig = field(default_factory=PlayerConfig)
