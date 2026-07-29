"""Compatibility shim — Phase A import surface.

All public names re-exported from the new ``value_objects/`` package.

.. deprecated::
    Import directly from ``samotech_iptv.domain.value_objects.<module>``
    or from ``samotech_iptv.domain.value_objects`` (the package).
"""
from samotech_iptv.domain.value_objects import (  # noqa: F401
    ProviderId,
    ChannelId,
    StreamId,
    Credential,
    URL,
)

__all__ = ["ProviderId", "ChannelId", "StreamId", "Credential", "URL"]
