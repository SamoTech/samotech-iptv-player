"""Pure provider-independent classification for supported stream URIs."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from samotech_iptv.domain.value_objects.stream_protocol import (
    StreamClassification,
    StreamManifest,
    StreamTransport,
)

if TYPE_CHECKING:
    from samotech_iptv.domain.value_objects.stream_uri import StreamURI

__all__ = ["StreamClassifier"]

_MANIFEST_SUFFIXES = {
    ".m3u": StreamManifest.M3U,
    ".m3u8": StreamManifest.HLS,
    ".mpd": StreamManifest.DASH,
}


class StreamClassifier:
    """Classify a stream URI without fetching a manifest or invoking a player backend."""

    @staticmethod
    def classify(
        stream_uri: StreamURI,
        *,
        declared_transport: StreamTransport | None = None,
        declared_manifest: StreamManifest | None = None,
    ) -> StreamClassification:
        """Prefer explicit metadata, then derive transport and manifest indicators from the URI."""
        parsed = urlsplit(stream_uri.value)
        transport = declared_transport or StreamTransport(parsed.scheme.casefold())
        manifest = declared_manifest or StreamClassifier._manifest_from_path(parsed.path)
        return StreamClassification(transport=transport, manifest=manifest)

    @staticmethod
    def _manifest_from_path(path: str) -> StreamManifest | None:
        suffix = PurePosixPath(path).suffix.casefold()
        return _MANIFEST_SUFFIXES.get(suffix)
