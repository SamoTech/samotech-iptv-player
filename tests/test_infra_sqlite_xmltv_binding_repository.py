from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from samotech_iptv.domain.entities.xmltv_binding import XMLTVBinding, XMLTVChannelMapping
from samotech_iptv.domain.value_objects.channel_id import ChannelId
from samotech_iptv.domain.value_objects.provider_id import ProviderId
from samotech_iptv.infrastructure.database.sqlite_xmltv_binding_repository import (
    SQLiteXMLTVBindingRepository,
)

if TYPE_CHECKING:
    from pathlib import Path


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


@pytest.mark.asyncio
async def test_repository_persists_and_replaces_one_binding_atomically(tmp_path: Path) -> None:
    repository = SQLiteXMLTVBindingRepository(tmp_path / "state.sqlite3")
    await repository.initialise()
    await repository.save(_binding())
    replacement = _binding(
        source="file:///guides/replacement.xml",
        mappings=(
            XMLTVChannelMapping(source_channel_id="source.sport", channel_id=ChannelId("sport")),
        ),
    )

    await repository.save(replacement)
    restored = await repository.load(ProviderId("demo"))

    assert restored == replacement
    assert restored is not None
    assert restored.channel_mapping == {"source.sport": ChannelId("sport")}


@pytest.mark.asyncio
async def test_repository_deletes_a_binding_and_its_mappings(tmp_path: Path) -> None:
    repository = SQLiteXMLTVBindingRepository(tmp_path / "state.sqlite3")
    await repository.initialise()
    await repository.save(_binding())

    assert await repository.delete(ProviderId("demo")) is True
    assert await repository.delete(ProviderId("demo")) is False
    assert await repository.load(ProviderId("demo")) is None
