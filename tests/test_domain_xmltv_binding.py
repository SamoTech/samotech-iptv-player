from __future__ import annotations

import pytest

from samotech_iptv.core.exceptions import ValidationError
from samotech_iptv.domain.entities.xmltv_binding import XMLTVBinding, XMLTVChannelMapping
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId


def _binding(
    *,
    source: str = "/guides/demo.xml",
    mappings: tuple[XMLTVChannelMapping, ...] | None = None,
) -> XMLTVBinding:
    return XMLTVBinding(
        provider_id=ProviderId("demo"),
        source=source,
        mappings=mappings
        or (XMLTVChannelMapping(source_channel_id="source.news", channel_id=ChannelId("news")),),
    )


def test_binding_accepts_local_path_and_exposes_parser_ready_mapping() -> None:
    binding = _binding()

    assert binding.channel_mapping == {"source.news": ChannelId("news")}


def test_binding_accepts_local_file_uri() -> None:
    binding = _binding(source="file:///guides/demo.xml")

    assert binding.source == "file:///guides/demo.xml"


@pytest.mark.parametrize(
    "source",
    [
        "https://guides.example.invalid/demo.xml",
        "ftp://guides.example.invalid/demo.xml",
        "file://remote-host/guides/demo.xml",
        "file:///guides/demo.xml#fragment",
    ],
)
def test_binding_rejects_non_local_or_non_canonical_sources(source: str) -> None:
    with pytest.raises(ValidationError, match="XMLTV"):
        _binding(source=source)


def test_binding_rejects_duplicate_source_channel_ids() -> None:
    with pytest.raises(ValidationError, match="unique"):
        _binding(
            mappings=(
                XMLTVChannelMapping(source_channel_id="source.news", channel_id=ChannelId("news")),
                XMLTVChannelMapping(
                    source_channel_id="source.news", channel_id=ChannelId("sports")
                ),
            )
        )


def test_mapping_rejects_blank_source_channel_id() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        XMLTVChannelMapping(source_channel_id=" ", channel_id=ChannelId("news"))
