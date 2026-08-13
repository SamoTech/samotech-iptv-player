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
    def __init__(self, connection: MAGConnection, session: MAGSession) -> None:
        # The connection remains constructor-injected for legacy compatibility;
        # profile-owned requests are issued through the session.
        self._conn = connection
        self._sess = session

    async def get_stream_url(self, stream_id: int, stream_type: str = "live") -> str:
        """Resolve one provider-confirmed stream command through the selected profile."""
        operation = (
            MAGOperation.CREATE_VOD_LINK
            if stream_type in ("vod", "series")
            else MAGOperation.CREATE_LIVE_LINK
        )
        params = {
            "cmd": f"ffmpeg http://localhost/ch/{stream_id}_",
            "forced_storage": "undefined",
            "disable_ad": "0",
            "JsHttpRequest": "1-xml",
        }
        data = await self._sess.request(operation, params=params)

        envelope = data if isinstance(data, Mapping) else {}
        raw_js = envelope.get("js", {})
        js = raw_js if isinstance(raw_js, Mapping) else {}
        raw_cmd = js.get("cmd", "")
        cmd = raw_cmd if isinstance(raw_cmd, str) else ""
        if not cmd:
            raise StreamError(
                f"Portal returned no stream command for stream_id={stream_id}. "
                "Verify you are authorised to access this content."
            )

        url = cmd.strip()
        for part in cmd.split():
            if part.startswith("http"):
                url = part
                break

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https", "rtsp", "rtmp"):
            raise StreamError(f"Unexpected stream URL scheme: {parsed.scheme!r} in {url!r}")

        log.info("Resolved MAG stream URL (scheme=%s)", parsed.scheme)
        return url
