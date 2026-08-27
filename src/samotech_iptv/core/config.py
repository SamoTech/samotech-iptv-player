"""Application configuration data structures.

Configuration is composed once by the infrastructure ``ConfigurationProvider``
and injected into downstream code.  Core models are deliberately free of
process-environment reads so that they remain deterministic and testable.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["AppConfig", "NetworkConfig", "PlayerConfig", "default_data_dir"]


def _home_dir() -> Path:
    """Return a deterministic home fallback for cross-platform configuration tests."""
    try:
        return Path.home()
    except RuntimeError:
        return Path(".")


def default_data_dir() -> str:
    """Return the platform’s conventional per-user application-data directory."""
    if sys.platform == "win32":
        root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        base = Path(root) if root else _home_dir() / "AppData" / "Local"
    elif sys.platform == "darwin":
        base = _home_dir() / "Library" / "Application Support"
    else:
        root = os.environ.get("XDG_DATA_HOME")
        base = Path(root) if root else _home_dir() / ".local" / "share"
    return str(base / "SamoTech" / "IPTV Player")


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
    data_dir: str = field(default_factory=default_data_dir)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    player: PlayerConfig = field(default_factory=PlayerConfig)
