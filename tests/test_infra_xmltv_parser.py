from __future__ import annotations

import pytest

from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.infrastructure.parsing.xmltv_parser import XMLTVParser, XMLTVParserError

_XMLTV_DOCUMENT = """<?xml version="1.0" encoding="UTF-8"?>
<tv>
  <programme channel="news.example" start="20260812100000 +0300" stop="20260812103000 +0300">
    <title lang="en">Morning News</title>
    <desc lang="en">Headlines and weather.</desc>
    <category lang="en">News</category>
  </programme>
  <programme channel="sport.example" start="20260812110000" stop="20260812113000">
    <title>Unmapped Sport</title>
  </programme>
  <programme channel="news.example" start="20260812103000Z" stop="20260812110000Z">
    <title>Market Update</title>
  </programme>
</tv>
"""


def test_xmltv_parser_translates_mapped_programmes_with_stable_canonical_ids() -> None:
    parser = XMLTVParser()
    channel_id = ChannelId("m3u-demo:news")

    entries = parser.parse(_XMLTV_DOCUMENT, {"news.example": channel_id})

    assert len(entries) == 2
    assert entries[0].id == "m3u-demo:news:xmltv:5065c5f4b2056a27044f"
    assert entries[0].channel_id == channel_id
    assert entries[0].title == "Morning News"
    assert entries[0].start.isoformat() == "2026-08-12T10:00:00+03:00"
    assert entries[0].end.isoformat() == "2026-08-12T10:30:00+03:00"
    assert entries[0].description == "Headlines and weather."
    assert entries[0].category == "News"
    assert entries[1].title == "Market Update"
    assert entries[1].start.isoformat() == "2026-08-12T10:30:00+00:00"


def test_xmltv_parser_ignores_programmes_for_unmapped_channels() -> None:
    entries = XMLTVParser().parse(_XMLTV_DOCUMENT, {})

    assert entries == ()


@pytest.mark.parametrize(
    ("programme", "message"),
    [
        (
            (
                '<programme channel="news.example" stop="20260812103000 +0000">'
                "<title>News</title></programme>"
            ),
            "missing start",
        ),
        (
            (
                '<programme channel="news.example" start="20260812100000 +0000">'
                "<title>News</title></programme>"
            ),
            "missing stop",
        ),
        (
            (
                '<programme channel="news.example" start="20260812100000 +0000" '
                'stop="20260812103000 +0000"/>'
            ),
            "missing title",
        ),
        (
            (
                '<programme channel="news.example" start="invalid" '
                'stop="20260812103000 +0000"><title>News</title></programme>'
            ),
            "invalid start timestamp",
        ),
        (
            (
                '<programme channel="news.example" start="20260812103000 +0000" '
                'stop="20260812100000 +0000"><title>News</title></programme>'
            ),
            "invalid schedule",
        ),
    ],
)
def test_xmltv_parser_rejects_invalid_mapped_programmes(programme: str, message: str) -> None:
    with pytest.raises(XMLTVParserError, match=message):
        XMLTVParser().parse(f"<tv>{programme}</tv>", {"news.example": ChannelId("news")})


def test_xmltv_parser_rejects_non_xmltv_and_unsafe_documents() -> None:
    parser = XMLTVParser()

    with pytest.raises(XMLTVParserError, match="tv root"):
        parser.parse("<guide/>", {})
    with pytest.raises(XMLTVParserError, match="not well-formed or is unsafe"):
        parser.parse(
            "<!DOCTYPE tv [<!ENTITY prohibited 'value'>]><tv>&prohibited;</tv>",
            {},
        )


def test_xmltv_parser_limits_document_and_result_sizes() -> None:
    small_parser = XMLTVParser(max_document_characters=10, max_entries=1)

    with pytest.raises(XMLTVParserError, match="size limit"):
        small_parser.parse("<tv></tv>" * 2, {})

    limited_entries = XMLTVParser(max_entries=1).parse(
        _XMLTV_DOCUMENT,
        {"news.example": ChannelId("news")},
    )

    assert [entry.title for entry in limited_entries] == ["Morning News"]


@pytest.mark.parametrize("value", [0, -1])
def test_xmltv_parser_rejects_nonpositive_limits(value: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        XMLTVParser(max_document_characters=value)
    with pytest.raises(ValueError, match="positive"):
        XMLTVParser(max_entries=value)
