"""Legacy plugin namespace with automatic discovery permanently disabled."""

from __future__ import annotations

__all__ = ["load_plugins"]


def load_plugins() -> None:
    """Reject legacy automatic imports in favor of explicit trusted-plugin activation."""
    raise RuntimeError(
        "Automatic plugin discovery is disabled; use TrustedLocalPluginLoader with an explicit path"
    )
