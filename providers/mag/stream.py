"""Stream URL resolution for the MAG provider."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from ..base.errors import StreamError
from .protocol_profile import MAGOperation

if TYPE_CHECKING:
    from .connection import MAGConnection
    from .session import MAGSession

log = logging.getLogger(__name__)


class MAGStream:
    """Resolve portal-confirmed commands through the selected profile."""

    def __init__(self, connection: MAGConnection, session: MAGSession) -> None:
        self._conn = connection
        self._sess = session

    async def get_stream_url(
        self,
        stream_id: int,
        stream_type: str = "live",
        channel_command: str | None = None,
    ) -> str:
        """Resolve one live/VOD stream while keeping portal commands private."""
        operation = (
            MAGOperation.CREATE_VOD_LINK
            if stream_type in ("vod", "series")
            else MAGOperation.CREATE_LIVE_LINK
        )
        command = channel_command or f"ffmpeg http://localhost/ch/{stream_id}_"
        data = await self._sess.request(
            operation, params=self._sess.profile.live_link_params(command)
        )

        envelope = data if isinstance(data, Mapping) else {}
        raw_js = envelope.get("js", {})
        js = raw_js if isinstance(raw_js, Mapping) else {}
        raw_value = js.get("url") or js.get("cmd") or ""
        value = raw_value if isinstance(raw_value, str) else ""
        if not value:
            raise StreamError(
                "Portal returned no stream command. "
                "Verify you are authorised to access this content."
            )

        url = value.strip()
        for part in value.split():
            if part.startswith(("http://", "https://", "rtsp://", "rtmp://")):
                url = part
                break

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https", "rtsp", "rtmp"):
            raise StreamError(f"Unexpected stream URL scheme: {parsed.scheme!r}")

        log.info("Resolved MAG stream URL (scheme=%s)", parsed.scheme)
        return url
