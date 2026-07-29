"""Structured-logging factory.

Wraps stdlib ``logging`` so all layers obtain loggers through a single
entry-point.  Format and level are controlled by ``AppConfig.log_level``.
"""
from __future__ import annotations

import logging
import sys
from typing import Optional

__all__ = ["get_logger", "configure_logging"]

_FORMATTER = logging.Formatter(
    fmt="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


def configure_logging(level: str = "INFO", *, stream: bool = True) -> None:
    """Bootstrap root logger.  Call once at application startup."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    if stream and not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_FORMATTER)
        root.addHandler(handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a named logger under the ``samotech_iptv`` hierarchy."""
    qualified = f"samotech_iptv.{name}" if name else "samotech_iptv"
    return logging.getLogger(qualified)
