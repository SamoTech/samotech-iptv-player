from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from samotech_iptv.domain.entities.xmltv_binding import XMLTVBinding, XMLTVChannelMapping
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.infrastructure.parsing.xmltv_guide_service import XMLTVGuideService
from samotech_iptv.infrastructure.parsing.xmltv_source_loader import (
    LocalXMLTVSourceLoader,
    XMLTVSourceError,
)

if TYPE_CHECKING:
    from pathlib import Path

_XMLTV = """<tv>
  <programme channel="source.news" start="20260813010000Z" stop="20260813013000Z">
    <title>Morning News</title>
  </programme>
  <programme channel="source.unmapped" start="20260813010000Z" stop="20260813013000Z">
    <title>Unmapped</title>
  </programme>
</tv>"""


def _binding(source: str) -> XMLTVBinding:
    return XMLTVBinding(
        provider_id=ProviderId("demo"),
        source=source,
        mappings=(
            XMLTVChannelMapping(source_channel_id="source.news", channel_id=ChannelId("news")),
        ),
    )


@pytest.mark.asyncio
async def test_loader_reads_local_path_and_local_file_uri(tmp_path: Path) -> None:
    source_path = tmp_path / "guide.xml"
    source_path.write_text(_XMLTV, encoding="utf-8")
    loader = LocalXMLTVSourceLoader()

    assert await loader.load(str(source_path)) == _XMLTV
    assert await loader.load(source_path.as_uri()) == _XMLTV


@pytest.mark.asyncio
async def test_loader_rejects_remote_source_without_calling_network() -> None:
    with pytest.raises(XMLTVSourceError, match="local path or file URI"):
        await LocalXMLTVSourceLoader().load("https://guides.example.invalid/demo.xml")


@pytest.mark.asyncio
async def test_guide_service_loads_only_explicitly_mapped_entries(tmp_path: Path) -> None:
    source_path = tmp_path / "guide.xml"
    source_path.write_text(_XMLTV, encoding="utf-8")

    entries = await XMLTVGuideService(LocalXMLTVSourceLoader()).refresh(_binding(str(source_path)))

    assert len(entries) == 1
    assert entries[0].channel_id == ChannelId("news")
    assert entries[0].title == "Morning News"
