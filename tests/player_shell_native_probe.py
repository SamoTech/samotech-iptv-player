from __future__ import annotations

import asyncio
import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QLabel

from samotech_iptv.application.dtos import (
    ChannelDTO,
    LoadChannelsResponse,
    ProviderMetadata,
    SearchChannelsResponse,
)
from samotech_iptv.presentation.player_shell import PlayerShell

N = 3


def make_channel(name: str) -> ChannelDTO:
    return ChannelDTO(id=name.lower(), name=name, provider_id="provider-a", stream_id=name)


class FakeBrowse:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.response = LoadChannelsResponse(channels=(), total=0)

    async def execute(self, _: object) -> LoadChannelsResponse:
        if self.error:
            raise self.error
        return self.response


class FakeSearch:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.response = SearchChannelsResponse(channels=(), total=0)
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.wait_for_release = False

    async def execute(self, _: object) -> SearchChannelsResponse:
        self.started.set()
        if self.wait_for_release:
            await self.release.wait()
        if self.error:
            raise self.error
        return self.response


class FakeFavorite:
    def __init__(self) -> None:
        self.ids: list[str] = []

    async def execute(self, request: object) -> SimpleNamespace:
        self.ids.append(request.item_id)
        return SimpleNamespace(success=True)


class FakeProviders:
    def __init__(self, providers: tuple[ProviderMetadata, ...]) -> None:
        self.providers = providers

    async def execute(self) -> tuple[ProviderMetadata, ...]:
        return self.providers


async def noop() -> None:
    return None


def make_shell(
    browse: FakeBrowse,
    search: FakeSearch,
    favorite: FakeFavorite,
    play: object,
    providers: FakeProviders | None = None,
) -> PlayerShell:
    return PlayerShell(
        QLabel(),
        browse,
        play,  # type: ignore[arg-type]
        search,  # type: ignore[arg-type]
        favorite,  # type: ignore[arg-type]
        noop,
        noop,
        noop,
        providers or FakeProviders(()),
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
        lambda: None,
    )


async def main() -> None:
    app = QApplication.instance() or QApplication([])
    a, b, c = make_channel("A"), make_channel("B"), make_channel("C")
    played: list[str] = []

    async def play(_: str, channel_id: str) -> None:
        played.append(channel_id)

    favorite = FakeFavorite()
    shell = make_shell(FakeBrowse(), FakeSearch(), favorite, play)
    shell._render_channels((a, b, c))
    shell.channel_list.setCurrentIndex(shell.channel_model.index(1, 0))
    shell._schedule_selected_channel(shell.channel_model.index(1, 0))
    shell._schedule_add_favorite()
    shell._render_channels((a, c))
    await asyncio.sleep(0)
    assert played == ["b"]
    assert favorite.ids == ["b"]

    failure_shell = make_shell(
        FakeBrowse(error=RuntimeError("provider failed")),
        FakeSearch(error=RuntimeError("search failed")),
        FakeFavorite(),
        play,
    )
    await failure_shell.load_channels()
    assert failure_shell.channel_status.text() == "Unable to load channels"
    assert failure_shell.load_button.isEnabled()
    await failure_shell.search_channels()
    assert failure_shell.channel_status.text() == "Unable to search channels"
    assert failure_shell.search_button.isEnabled()

    old, new = make_channel("Old"), make_channel("New")
    search = FakeSearch()
    search.wait_for_release = True
    stale_shell = make_shell(FakeBrowse(), search, FakeFavorite(), play)
    first = asyncio.create_task(stale_shell.search_channels(stale_shell._begin_request()))
    await search.started.wait()
    search.wait_for_release = False
    search.response = SearchChannelsResponse(channels=(new,), total=1)
    second = asyncio.create_task(stale_shell.search_channels(stale_shell._begin_request()))
    await second
    search.release.set()
    search.response = SearchChannelsResponse(channels=(old,), total=1)
    await first
    assert stale_shell.channel_model.channel_at(0) is new

    providers = FakeProviders(
        (ProviderMetadata("provider-a", "Provider A", "m3u", "https://safe.invalid", True),)
    )
    provider_shell = make_shell(FakeBrowse(), FakeSearch(), FakeFavorite(), play, providers)
    await provider_shell.refresh_providers()
    provider_shell.provider_selector.setCurrentIndex(1)
    assert provider_shell._provider_id() == "provider-a"
    assert provider_shell.provider_selector.accessibleName() == "Active IPTV provider"
    assert provider_shell.channel_list.accessibleName() == "Live channel list"
    assert provider_shell.navigation.accessibleName() == "Main navigation"

    provider_shell._render_channels((a, b))
    provider_shell.channel_list.setCurrentIndex(provider_shell.channel_model.index(0, 0))
    down = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
    assert provider_shell.eventFilter(provider_shell.channel_list, down)
    assert provider_shell.channel_list.currentIndex().row() == 1
    fullscreen = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_F, Qt.KeyboardModifier.NoModifier)
    assert provider_shell.eventFilter(provider_shell.navigation, fullscreen)
    assert provider_shell.isFullScreen()
    escape = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
    assert provider_shell.eventFilter(provider_shell.navigation, escape)
    assert not provider_shell.isFullScreen()
    enter = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
    assert provider_shell.eventFilter(provider_shell.channel_list, enter)
    await asyncio.sleep(0)

    print(f"records={N}")
    print("stale_identity=PASS")
    print("async_error_cleanup=PASS")
    print("stale_request_protection=PASS")
    print("provider_selection=PASS")
    print("keyboard_accessibility=PASS")
    print("player_shell_native_probe=PASS")
    app.quit()


if __name__ == "__main__":
    asyncio.run(main())
