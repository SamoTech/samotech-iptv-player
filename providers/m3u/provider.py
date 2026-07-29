"""Minimal M3U provider stub (expanded separately)."""
from ..base import BaseProvider
from ..registry import register
from typing import Any


@register("m3u")
class M3UProvider(BaseProvider):
    async def connect(self) -> None: ...
    async def close(self) -> None: ...
    async def authenticate(self) -> None: ...
    async def refresh_token(self) -> None: ...
    async def get_profile(self) -> dict[str, Any]: return {}
    async def get_channels(self) -> list[dict[str, Any]]: return []
    async def get_vod(self, page=0, category_id=None): return []
    async def get_series(self, page=0, category_id=None): return []
    async def get_epg(self, channel_ids=None, period=3): return {}
    async def get_stream_url(self, stream_id, stream_type="live"): return ""
