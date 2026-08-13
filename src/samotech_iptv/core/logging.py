"""Structured-logging factory.

Wraps stdlib ``logging`` so all layers obtain loggers through a single
entry-point.  Format and level are controlled by ``AppConfig.log_level``.
"""

from __future__ import annotations

import logging
import sys

__all__ = ["get_logger", "configure_logging"]

_FORMATTER = logging.Formatter(
    fmt="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
_DEBUG_FORMATTER = logging.Formatter(
    fmt="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


def configure_logging(level: str = "INFO", *, stream: bool = True, debug: bool = False) -> None:
    """Bootstrap root logger with optional detailed development diagnostics."""
    root = logging.getLogger()
    effective_level = "DEBUG" if debug else level.upper()
    root.setLevel(getattr(logging, effective_level, logging.INFO))
    if stream and not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_DEBUG_FORMATTER if debug else _FORMATTER)
        root.addHandler(handler)
    elif debug:
        for handler in root.handlers:
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(_DEBUG_FORMATTER)


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a named logger under the ``samotech_iptv`` hierarchy."""
    qualified = f"samotech_iptv.{name}" if name else "samotech_iptv"
    return logging.getLogger(qualified)
