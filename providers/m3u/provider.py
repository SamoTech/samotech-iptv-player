"""Minimal M3U provider stub (expanded separately)."""

from typing import Any

from ..base import BaseProvider
from ..registry import register


@register("m3u")
class M3UProvider(BaseProvider):
    async def connect(self) -> None: ...
    async def close(self) -> None: ...
    async def authenticate(self) -> None: ...
    async def refresh_token(self) -> None: ...
    async def get_profile(self) -> dict[str, Any]:
        return {}

    async def get_channels(self) -> list[dict[str, Any]]:
        return []

    async def get_vod(
        self, page: int = 0, category_id: int | None = None
    ) -> list[dict[str, object]]:
        return []

    async def get_series(
        self, page: int = 0, category_id: int | None = None
    ) -> list[dict[str, object]]:
        return []

    async def get_epg(
        self, channel_ids: list[int] | None = None, period: int = 3
    ) -> dict[int, list[dict[str, object]]]:
        return {}

    async def get_stream_url(self, stream_id: int, stream_type: str = "live") -> str:
        return ""
