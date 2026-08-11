"""Value objects package — re-exports every value object.

Usage (unchanged from Phase A)::

    from samotech_iptv.domain.value_objects import ProviderId, URL, Credential

Or directly::

    from samotech_iptv.domain.value_objects.url import URL
"""
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.credential import Credential
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.domain.value_objects.stream_id import StreamId
from samotech_iptv.domain.value_objects.url import URL

__all__ = ["ProviderId", "ChannelId", "StreamId", "Credential", "URL"]
