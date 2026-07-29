"""SamoTech IPTV Player — canonical package root.

Import convention::

    from samotech_iptv.domain.entities import Channel
    from samotech_iptv.application.ports import ProviderPort

Do NOT import from ``providers.*`` in new code; that namespace is
kept for backward-compatibility during the migration period only.
"""
from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__: str = _version("samotech-iptv-player")
except PackageNotFoundError:  # running from source tree
    from samotech_iptv.version import __version__  # type: ignore[assignment]

__all__ = ["__version__"]
