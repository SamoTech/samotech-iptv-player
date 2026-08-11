"""Tests for provider-independent stream URI and protocol classification."""

from __future__ import annotations

import pytest

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.entities.stream import Stream
from samotech_iptv.domain.services.stream_classifier import StreamClassifier
from samotech_iptv.domain.value_objects.stream_id import StreamId
from samotech_iptv.domain.value_objects.stream_protocol import StreamManifest, StreamTransport
from samotech_iptv.domain.value_objects.stream_uri import StreamURI


@pytest.mark.parametrize(
    ("value", "transport", "manifest"),
    [
        ("http://stream.example.test/live/channel.ts", StreamTransport.HTTP, None),
        (
            "https://stream.example.test/live/channel.m3u8?token=test",
            StreamTransport.HTTPS,
            StreamManifest.HLS,
        ),
        ("https://provider.example.test/playlist.m3u", StreamTransport.HTTPS, StreamManifest.M3U),
        (
            "https://stream.example.test/live/manifest.mpd",
            StreamTransport.HTTPS,
            StreamManifest.DASH,
        ),
        ("rtmp://stream.example.test/live/channel", StreamTransport.RTMP, None),
        ("rtmps://stream.example.test/live/channel", StreamTransport.RTMPS, None),
        ("rtsp://camera.example.test/live", StreamTransport.RTSP, None),
        ("udp://239.0.0.1:1234", StreamTransport.UDP, None),
        ("rtp://239.0.0.2:5004", StreamTransport.RTP, None),
        ("srt://stream.example.test:9000", StreamTransport.SRT, None),
    ],
)
def test_stream_classifier_identifies_transport_and_manifest_indicators(
    value: str, transport: StreamTransport, manifest: StreamManifest | None
) -> None:
    """Classification derives transport and manifest indicators from the URI."""
    classification = StreamClassifier.classify(StreamURI(value))

    assert classification.transport is transport
    assert classification.manifest is manifest


def test_stream_classifier_prefers_explicit_provider_metadata() -> None:
    """Provider-supplied metadata takes precedence over URI-derived fallback indicators."""
    classification = StreamClassifier.classify(
        StreamURI("https://stream.example.test/live/channel.m3u8"),
        declared_transport=StreamTransport.HTTP,
        declared_manifest=StreamManifest.M3U,
    )

    assert classification.transport is StreamTransport.HTTP
    assert classification.manifest is StreamManifest.M3U


@pytest.mark.parametrize(
    "value",
    [
        "ftp://stream.example.test/channel.ts",
        "https://",
        "https://stream.example.test path",
    ],
)
def test_stream_uri_rejects_unsupported_or_malformed_transports(value: str) -> None:
    """Only explicitly modeled whitespace-free transport URIs enter the stream domain."""
    with pytest.raises(ValidationError, match="Invalid stream URI"):
        StreamURI(value)


def test_stream_representing_rtmp_remains_protocol_independent() -> None:
    """The canonical Stream can represent RTMP without claiming player-backend support."""
    stream = Stream(
        id=StreamId("rtmp-stream"),
        url=StreamURI("rtmp://stream.example.test/live/channel"),
        container="flv",
    )

    assert stream.transport is StreamTransport.RTMP
    assert stream.manifest is None
