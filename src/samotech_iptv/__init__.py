"""SamoTech IPTV Player — canonical package root.

Import convention::

    from samotech_iptv.domain.entities import Channel
    from samotech_iptv.application.ports import ProviderPort

Do NOT import from ``providers.*`` in new code; that namespace is
kept for backward-compatibility during the migration period only.
"""

from samotech_iptv.version import __version__

__all__ = ["__version__"]
