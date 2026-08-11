"""Protocol-independent stream transport and manifest classifications."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

__all__ = ["StreamClassification", "StreamManifest", "StreamTransport"]


class StreamTransport(StrEnum):
    """Media delivery transport identified independently from the content provider."""

    HTTP = "http"
    HTTPS = "https"
    RTMP = "rtmp"
    RTMPS = "rtmps"
    RTSP = "rtsp"
    UDP = "udp"
    RTP = "rtp"
    SRT = "srt"
    UNKNOWN = "unknown"


class StreamManifest(StrEnum):
    """A manifest or content-playlist type when determinable without fetching it."""

    M3U = "m3u"
    HLS = "hls"
    DASH = "dash"


@dataclass(frozen=True)
class StreamClassification:
    """Provider-independent transport and optional manifest classification for a stream URI."""

    transport: StreamTransport
    manifest: StreamManifest | None = None
