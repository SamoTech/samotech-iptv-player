from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QModelIndex, QObject, QStringListModel, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from samotech_iptv.application.dtos import (
    BrowseContentRequest,
    ChannelDTO,
    ContentItemDTO,
    ContentType,
    LoadCategoriesRequest,
    LoadChannelsRequest,
    ProviderCapabilities,
    SearchRegisteredChannelsRequest,
)
from samotech_iptv.presentation.viewmodels.channel_list_model import ChannelListModel
from samotech_iptv.presentation.viewmodels.content_list_model import ContentListModel

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Sequence

    from samotech_iptv.application.use_cases.browse_channels import BrowseChannels
    from samotech_iptv.application.use_cases.browse_content import BrowseContent
    from samotech_iptv.application.use_cases.list_providers import ListProviders
    from samotech_iptv.application.use_cases.load_categories import LoadCategories
    from samotech_iptv.application.use_cases.load_provider_capabilities import (
        LoadProviderCapabilities,
    )
    from samotech_iptv.application.use_cases.save_favorite import SaveFavorite
    from samotech_iptv.application.use_cases.search_registered_channels import (
        SearchRegisteredChannels,
    )

__all__ = ["PlayerShell"]


class PlayerShell(QWidget):
    """Player-first desktop shell around the existing application use cases."""

    _STYLESHEET = """
    QWidget#playerShell {
        background: #0b0f14;
        color: #e9eef5;
    }
    QLabel#brand {
        color: #f6f8fb;
        font-size: 18px;
        font-weight: 700;
        letter-spacing: 1px;
    }
    QLabel#eyebrow {
        color: #7f8da1;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.4px;
    }
    QLabel#status {
        color: #63d6a5;
        font-size: 12px;
    }
    QLineEdit {
        background: #151c25;
        border: 1px solid #273342;
        border-radius: 7px;
        padding: 8px 10px;
        color: #e9eef5;
        selection-background-color: #2d78c8;
    }
    QLineEdit:focus {
        border: 1px solid #3d9cff;
    }
    QPushButton {
        background: #182230;
        border: 1px solid #2a394b;
        border-radius: 7px;
        padding: 8px 12px;
        color: #e9eef5;
    }
    QPushButton:hover {
        background: #223147;
        border-color: #3d9cff;
    }
    QPushButton#primary {
        background: #2d78c8;
        border-color: #3d9cff;
        font-weight: 700;
    }
    QPushButton#primary:hover {
        background: #398bdc;
    }
    QListView#navigation {
        background: #10161e;
        border: 0;
        padding: 8px;
        outline: 0;
    }
    QListView#navigation::item {
        padding: 10px 12px;
        margin: 2px 0;
        border-radius: 7px;
        color: #9caabd;
    }
    QListView#navigation::item:selected {
        background: #1d3a57;
        color: #f2f7ff;
        font-weight: 700;
    }
    QListView#channels {
        background: #10161e;
        border: 1px solid #223043;
        border-radius: 8px;
        padding: 6px;
        outline: 0;
    }
    QListView#channels::item {
        padding: 10px 12px;
        border-radius: 5px;
        color: #c8d2df;
    }
    QListView#channels::item:selected {
        background: #1c456d;
        color: #ffffff;
    }
    QFrame#playerCard, QFrame#contentCard {
        background: #10161e;
        border: 1px solid #202d3c;
        border-radius: 10px;
    }
    QLabel#playerViewport {
        background: #030507;
        color: #6f7f92;
        border-radius: 8px;
    }
    QLabel#pageTitle {
        color: #f6f8fb;
        font-size: 22px;
        font-weight: 700;
    }
    QLabel#pageSubtitle {
        color: #8998aa;
        font-size: 13px;
    }
    QLabel#emptyState {
        color: #8f9daf;
        font-size: 14px;
    }
    QSlider::groove:horizontal {
        height: 4px;
        background: #2a394b;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        width: 12px;
        margin: -4px 0;
        border-radius: 6px;
        background: #4ca3ff;
    }
    """

    def __init__(
        self,
        video_surface: QWidget,
        browse_channels: BrowseChannels,
        play_selected_channel: Callable[[str, str], Awaitable[None]],
        search_channels: SearchRegisteredChannels,
        save_favorite: SaveFavorite,
        pause_playback: Callable[[], Awaitable[None]],
        resume_playback: Callable[[], Awaitable[None]],
        stop_playback: Callable[[], Awaitable[None]],
        list_providers: ListProviders,
        open_favorites_dialog: Callable[[], object],
        open_history_dialog: Callable[[], object],
        open_category_dialog: Callable[[], object],
        open_epg_dialog: Callable[[], object],
        open_provider_list_dialog: Callable[[], object],
        open_settings_dialog: Callable[[], object],
        load_categories: LoadCategories | None = None,
        browse_content: BrowseContent | None = None,
        load_provider_capabilities: LoadProviderCapabilities | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("playerShell")
        self.setStyleSheet(self._STYLESHEET)
        self._browse_channels = browse_channels
        self._load_categories = load_categories
        self._browse_content = browse_content
        self._load_provider_capabilities = load_provider_capabilities
        self._play_selected_channel = play_selected_channel
        self._search_channels = search_channels
        self._save_favorite = save_favorite
        self._pause_playback = pause_playback
        self._resume_playback = resume_playback
        self._stop_playback = stop_playback
        self._open_favorites_dialog = open_favorites_dialog
        self._open_history_dialog = open_history_dialog
        self._open_category_dialog = open_category_dialog
        self._open_epg_dialog = open_epg_dialog
        self._open_provider_list_dialog = open_provider_list_dialog
        self._open_settings_dialog = open_settings_dialog
        self._list_providers = list_providers
        self._channels: list[ChannelDTO] = []
        self._catalogue_channels: tuple[ChannelDTO, ...] = ()
        self._search_channels_result: tuple[ChannelDTO, ...] | None = None
        self._content_catalogues: dict[ContentType, tuple[ContentItemDTO, ...]] = {}
        self._content_categories: dict[ContentType, tuple[tuple[str, str], ...]] = {}
        self._active_content_type = ContentType.LIVE
        self._active_content_category_id: str | None = None
        self._provider_capabilities = ProviderCapabilities()
        self._content_lists: dict[ContentType, QListView] = {}
        self._content_category_selectors: dict[ContentType, QComboBox] = {}
        self._content_status_labels: dict[ContentType, QLabel] = {}
        self._content_detail_labels: dict[ContentType, QLabel] = {}
        self._provider_ids: list[str] = []
        self._active_category_id: str | None = None
        self._request_generation = 0
        self._loading = False
        self.selected_channel: ChannelDTO | None = None
        self.playing_channel: ChannelDTO | None = None
        self.loading_channel: ChannelDTO | None = None
        self.playback_error_channel: ChannelDTO | None = None
        self.selected_content: ContentItemDTO | None = None
        self.channel_model = ChannelListModel()
        self.content_model = ContentListModel()
        self.provider_selector = QComboBox()
        self.provider_selector.setEditable(True)
        self.provider_selector.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.provider_selector.setPlaceholderText("Select provider or enter ID")
        self.provider_selector.setAccessibleName("Active IPTV provider")
        self.provider_selector.setToolTip("Choose the registered provider for live TV")
        self.provider_selector.currentIndexChanged.connect(self._provider_changed)
        self.category_selector = QComboBox()
        self.category_selector.addItem("All live channels", None)
        self.category_selector.setAccessibleName("Live channel category")
        self.category_selector.setToolTip("Filter the loaded catalogue without playback")
        self.category_selector.currentIndexChanged.connect(self._category_changed)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search live channels")
        self.search_input.setAccessibleName("Live channel search")
        self.search_input.setToolTip("Search the selected provider's channels")
        self.search_input.returnPressed.connect(self._schedule_search)
        self.status_label = QLabel("● Ready")
        self.status_label.setObjectName("status")
        self.status_label.setAccessibleName("Player status")
        self.current_channel_label = QLabel("Selected · No channel selected")
        self.current_channel_label.setAccessibleName("Current channel")
        self.playback_context_label = QLabel("Playback · Ready")
        self.playback_context_label.setAccessibleName("Playback channel state")
        self.navigation = QListView()
        self.navigation.setObjectName("navigation")
        self.navigation.setAccessibleName("Main navigation")
        self.navigation.setToolTip("Navigate IPTV sections")
        self.navigation.setFixedWidth(154)
        self.navigation_model = QStringListModel()
        self._navigation_pages: list[int] = []
        self.navigation.setModel(self.navigation_model)
        self.navigation.clicked.connect(lambda index: self._change_page(index.row()))
        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_home_page())
        self.pages.addWidget(self._build_live_page())
        self.pages.addWidget(self._build_content_page(ContentType.MOVIE))
        self.pages.addWidget(self._build_content_page(ContentType.SERIES))
        self.pages.addWidget(
            self._build_library_page(
                "Favorites", "Your saved channels appear here.", self._open_favorites_dialog
            )
        )
        self.pages.addWidget(
            self._build_library_page(
                "History", "Recently watched channels appear here.", self._open_history_dialog
            )
        )
        self.pages.addWidget(
            self._build_library_page(
                "EPG", "Browse the electronic programme guide.", self._open_epg_dialog
            )
        )
        self.pages.addWidget(
            self._build_library_page(
                "Providers",
                "Manage your M3U, Xtream, and MAG sources.",
                self._open_provider_list_dialog,
            )
        )
        self.pages.addWidget(
            self._build_library_page(
                "Settings", "Tune the player experience and appearance.", self._open_settings_dialog
            )
        )
        self._refresh_navigation()
        self.navigation.setCurrentIndex(self.navigation_model.index(0, 0))
        self._build_layout(video_surface)
        self.setTabOrder(self.provider_selector, self.search_input)
        self.setTabOrder(self.search_input, self.navigation)
        self.setTabOrder(self.navigation, self.channel_list)
        self.setTabOrder(self.channel_list, self.load_button)
        self.setTabOrder(self.load_button, self.search_button)
        self.setTabOrder(self.search_button, self.favorite_button)
        try:
            asyncio.get_running_loop().create_task(self.refresh_providers())
        except RuntimeError:
            pass
        self.installEventFilter(self)
        self.channel_list.installEventFilter(self)
        self.navigation.installEventFilter(self)
        self.fullscreen_button.installEventFilter(self)

    async def refresh_providers(self) -> None:
        """Populate the selector from safe provider summaries."""
        try:
            providers = await self._list_providers.execute()
            provider_items = list(providers)
            current_id = self._provider_id()
            self._provider_ids = [provider.id for provider in provider_items]
            self.provider_selector.blockSignals(True)
            self.provider_selector.clear()
            self.provider_selector.addItem("Select provider", "")
            for provider in provider_items:
                label = f"{provider.name} · {provider.type}"
                self.provider_selector.addItem(label, provider.id)
            self.provider_selector.blockSignals(False)
            if current_id:
                index = self.provider_selector.findData(current_id)
                if index >= 0:
                    self.provider_selector.setCurrentIndex(index)
            if not provider_items:
                self.status_label.setText("● No providers")
        except asyncio.CancelledError:
            raise
        except Exception:
            self.provider_selector.blockSignals(False)
            self.status_label.setText("● Providers unavailable")

    def _refresh_navigation(self) -> None:
        """Show content domains only when the selected provider declares them executable."""
        entries: list[tuple[str, int]] = [("Home", 0)]
        if self._provider_capabilities.live_tv:
            entries.append(("Live TV", 1))
        if self._provider_capabilities.vod_movies:
            entries.append(("Movies", 2))
        if self._provider_capabilities.vod_series:
            entries.append(("Series", 3))
        entries.extend([("Favorites", 4), ("History", 5)])
        if self._provider_capabilities.epg:
            entries.append(("EPG", 6))
        entries.extend([("Providers", 7), ("Settings", 8)])
        current_page = self.pages.currentIndex() if hasattr(self, "pages") else 0
        self.navigation_model.setStringList([label for label, _ in entries])
        self._navigation_pages = [page for _, page in entries]
        try:
            navigation_row = self._navigation_pages.index(current_page)
        except ValueError:
            navigation_row = 0
            self.pages.setCurrentIndex(self._navigation_pages[navigation_row])
        self.navigation.setCurrentIndex(self.navigation_model.index(navigation_row, 0))

    def _provider_changed(self, _: int) -> None:
        """Clear stale channel results when the active provider changes."""
        self._request_generation += 1
        self._set_loading(False)
        self._catalogue_channels = ()
        self._search_channels_result = None
        self._content_catalogues.clear()
        self._content_categories.clear()
        self._active_content_type = ContentType.LIVE
        self._active_content_category_id = None
        self.selected_content = None
        self._active_category_id = None
        self.category_selector.blockSignals(True)
        self.category_selector.clear()
        self.category_selector.addItem("All live channels", None)
        self.category_selector.blockSignals(False)
        self.selected_channel = None
        self.loading_channel = None
        self.playback_error_channel = None
        self._render_channels(())
        self._update_channel_context()
        provider_id = self._provider_id()
        self._provider_capabilities = ProviderCapabilities()
        self._refresh_navigation()
        self.status_label.setText("● Provider selected" if provider_id else "● Select a provider")
        self.channel_status.setText("No channels loaded")
        if provider_id:
            try:
                asyncio.get_running_loop().create_task(self.refresh_categories(provider_id))
                asyncio.get_running_loop().create_task(
                    self.refresh_provider_capabilities(provider_id)
                )
            except RuntimeError:
                pass

    async def refresh_provider_capabilities(self, provider_id: str) -> None:
        """Read executable capabilities once on selection without loading catalogue data."""
        if self._load_provider_capabilities is None:
            return
        capabilities = self._load_provider_capabilities.execute(provider_id)
        if provider_id != self._provider_id():
            return
        self._provider_capabilities = capabilities
        self._refresh_navigation()

    def _provider_id(self) -> str:
        """Return the selected provider ID, retaining editable fallback semantics."""
        index = self.provider_selector.currentIndex()
        text = self.provider_selector.currentText().strip()
        data = self.provider_selector.itemData(index)
        if index == 0 and text == "Select provider":
            return ""
        return str(data or text)

    async def refresh_categories(self, provider_id: str) -> None:
        """Populate persistent category navigation through the existing application boundary."""
        if self._load_categories is None:
            self.category_selector.setToolTip("Categories are unavailable in this session")
            return
        try:
            response = await self._load_categories.execute(
                LoadCategoriesRequest(provider_id=provider_id)
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            self.category_selector.setToolTip("Categories are unavailable for this provider")
            return
        if response.error is not None or response.unsupported:
            self.category_selector.setToolTip("Categories are unavailable for this provider")
            return
        if provider_id != self._provider_id():
            return
        self.category_selector.blockSignals(True)
        self.category_selector.clear()
        self.category_selector.addItem("All live channels", None)
        for category in response.categories:
            self.category_selector.addItem(category.name, category.id)
        self.category_selector.blockSignals(False)
        self.category_selector.setToolTip("Filter the loaded catalogue without playback")

    def _category_changed(self, _: int) -> None:
        """Filter the loaded presentation snapshot without a provider request or playback."""
        self._active_category_id = self.category_selector.currentData()
        self._render_active_catalogue()
        self.channel_status.setText(
            f"{self.channel_model.rowCount():,} channels in category"
            if self.channel_model.rowCount()
            else "No channels in category"
        )

    def _filtered_channels(self, channels: Sequence[ChannelDTO]) -> tuple[ChannelDTO, ...]:
        if self._active_category_id is None:
            return tuple(channels)
        return tuple(
            channel for channel in channels if channel.category_id == self._active_category_id
        )

    def _render_active_catalogue(self) -> None:
        """Render the current local search or complete catalogue view without network I/O."""
        source = (
            self._search_channels_result
            if self._search_channels_result is not None
            else self._catalogue_channels
        )
        self._render_channels(self._filtered_channels(source))

    def _build_layout(self, video_surface: QWidget) -> None:
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(18, 14, 18, 10)
        top_bar.setSpacing(12)
        brand_column = QVBoxLayout()
        brand_column.setSpacing(1)
        brand = QLabel("SAMOTECH IPTV")
        brand.setObjectName("brand")
        eyebrow = QLabel("LIVE TELEVISION")
        eyebrow.setObjectName("eyebrow")
        brand_column.addWidget(brand)
        brand_column.addWidget(eyebrow)
        top_bar.addLayout(brand_column)
        top_bar.addSpacing(10)
        top_bar.addWidget(self.provider_selector, 0)
        top_bar.addWidget(self.search_input, 1)
        top_bar.addWidget(self.status_label, 0)
        settings_button = QPushButton("Settings")
        settings_button.setAccessibleName("Open settings")
        settings_button.setToolTip("Open player settings")
        settings_button.clicked.connect(self._open_settings_dialog)
        top_bar.addWidget(settings_button, 0)

        player_card = QFrame()
        player_card.setObjectName("playerCard")
        player_layout = QVBoxLayout(player_card)
        player_layout.setContentsMargins(10, 10, 10, 10)
        player_layout.setSpacing(8)
        video_surface.setMinimumSize(420, 260)
        player_layout.addWidget(video_surface, 1)
        player_layout.addWidget(self.current_channel_label)
        player_layout.addWidget(self.playback_context_label)
        controls = QHBoxLayout()
        controls.setSpacing(6)
        self.pause_button = QPushButton("Pause")
        self.pause_button.setAccessibleName("Pause playback")
        self.pause_button.setToolTip("Pause the current stream")
        self.pause_button.clicked.connect(lambda: asyncio.ensure_future(self._pause_playback()))
        self.resume_button = QPushButton("Play")
        self.resume_button.setObjectName("primary")
        self.resume_button.setAccessibleName("Resume playback")
        self.resume_button.setToolTip("Resume the current stream")
        self.resume_button.clicked.connect(lambda: asyncio.ensure_future(self._resume_playback()))
        self.stop_button = QPushButton("Stop")
        self.stop_button.setAccessibleName("Stop playback")
        self.stop_button.setToolTip("Stop the current stream")
        self.stop_button.clicked.connect(lambda: asyncio.ensure_future(self._stop_playback()))
        self.fullscreen_button = QPushButton("Fullscreen")
        self.fullscreen_button.setAccessibleName("Toggle fullscreen")
        self.fullscreen_button.setToolTip("Enter or exit fullscreen mode (F)")
        self.fullscreen_button.clicked.connect(self._toggle_fullscreen)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.resume_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.fullscreen_button)
        controls.addStretch(1)
        player_layout.addLayout(controls)

        catalogue_body = QSplitter(Qt.Orientation.Horizontal)
        catalogue_body.setChildrenCollapsible(False)
        catalogue_body.addWidget(self.navigation)
        catalogue_body.addWidget(self.pages)
        catalogue_body.setStretchFactor(0, 0)
        catalogue_body.setStretchFactor(1, 1)
        catalogue_body.setSizes([154, 960])

        body = QSplitter(Qt.Orientation.Vertical)
        body.setChildrenCollapsible(False)
        body.addWidget(player_card)
        body.addWidget(catalogue_body)
        body.setStretchFactor(0, 3)
        body.setStretchFactor(1, 2)
        body.setSizes([500, 420])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(top_bar)
        layout.addWidget(body, 1)

    def _build_home_page(self) -> QWidget:
        page = QFrame()
        page.setObjectName("contentCard")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        title = QLabel("Welcome back")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Choose a destination and start watching.")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        live = QPushButton("Open Live TV")
        live.setObjectName("primary")
        live.clicked.connect(
            lambda: self.navigation.setCurrentIndex(self.navigation_model.index(1, 0))
        )
        providers = QPushButton("Manage Providers")
        providers.clicked.connect(self._open_provider_list_dialog)
        layout.addWidget(live)
        layout.addWidget(providers)
        layout.addStretch(1)
        return page

    def _build_live_page(self) -> QWidget:
        page = QFrame()
        page.setObjectName("contentCard")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        title = QLabel("Live TV")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Search locally cached channels; browsing is loaded only when requested.")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        actions = QHBoxLayout()
        self.load_button = QPushButton("Load channels")
        self.load_button.setObjectName("primary")
        self.load_button.setAccessibleName("Load live channels")
        self.load_button.clicked.connect(self._schedule_load)
        self.search_button = QPushButton("Search")
        self.search_button.setAccessibleName("Search live channels")
        self.search_button.clicked.connect(self._schedule_search)
        category_button = QPushButton("Categories")
        category_button.setToolTip("Browse live categories")
        category_button.clicked.connect(self._open_category_dialog)
        self.favorite_button = QPushButton("Add favorite")
        self.favorite_button.setAccessibleName("Add selected channel to favorites")
        self.favorite_button.clicked.connect(self._schedule_add_favorite)
        actions.addWidget(self.load_button)
        actions.addWidget(self.search_button)
        actions.addWidget(self.category_selector)
        actions.addWidget(category_button)
        actions.addWidget(self.favorite_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        self.channel_list = QListView()
        self.channel_list.setObjectName("channels")
        self.channel_list.setAccessibleName("Live channel list")
        self.channel_list.setToolTip("Select a channel and press Enter or double-click to play")
        self.channel_list.setModel(self.channel_model)
        self.channel_list.clicked.connect(self._select_index)
        self.channel_list.doubleClicked.connect(self._schedule_selected_channel)
        layout.addWidget(self.channel_list, 1)
        self.channel_status = QLabel("No channels loaded")
        self.channel_status.setObjectName("pageSubtitle")
        layout.addWidget(self.channel_status)
        return page

    def _build_content_page(self, content_type: ContentType) -> QWidget:
        """Build one scalable non-live catalogue page without replacing the live model."""
        page = QFrame()
        page.setObjectName("contentCard")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        title_text = "Movies" if content_type is ContentType.MOVIE else "Series"
        title = QLabel(title_text)
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            f"Load {title_text.lower()} explicitly; "
            "searches and genre filters stay local afterward."
        )
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        actions = QHBoxLayout()
        load_button = QPushButton(f"Load {title_text.lower()}")
        load_button.setObjectName("primary")
        load_button.setAccessibleName(f"Load {title_text.lower()}")
        load_button.clicked.connect(lambda: self._schedule_content_load(content_type))
        category_selector = QComboBox()
        category_selector.addItem(f"All {title_text.lower()}", None)
        category_selector.setAccessibleName(f"{title_text} category")
        category_selector.setToolTip("Filter the loaded catalogue without network activity")
        category_selector.currentIndexChanged.connect(
            lambda _: self._content_category_changed(content_type)
        )
        actions.addWidget(load_button)
        actions.addWidget(category_selector)
        actions.addStretch(1)
        layout.addLayout(actions)
        content_list = QListView()
        content_list.setObjectName("channels")
        content_list.setAccessibleName(f"{title_text} catalogue")
        content_list.setToolTip("Select an item and press Enter or double-click to activate")
        content_list.setModel(self.content_model)
        content_list.clicked.connect(lambda index: self._select_content_index(content_type, index))
        content_list.doubleClicked.connect(
            lambda index: self._activate_content_index(content_type, index)
        )
        layout.addWidget(content_list, 1)
        detail = QLabel("No content selected")
        detail.setObjectName("pageSubtitle")
        status = QLabel(f"No {title_text.lower()} loaded")
        status.setObjectName("pageSubtitle")
        layout.addWidget(detail)
        layout.addWidget(status)
        self._content_lists[content_type] = content_list
        self._content_category_selectors[content_type] = category_selector
        self._content_status_labels[content_type] = status
        self._content_detail_labels[content_type] = detail
        content_list.installEventFilter(self)
        return page

    def _build_library_page(
        self, title_text: str, subtitle_text: str, action: Callable[[], object]
    ) -> QWidget:
        page = QFrame()
        page.setObjectName("contentCard")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel(title_text)
        title.setObjectName("pageTitle")
        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("pageSubtitle")
        open_button = QPushButton(f"Open {title_text}")
        open_button.setObjectName("primary")
        open_button.clicked.connect(action)
        empty = QLabel("This section uses the existing application workflow.")
        empty.setObjectName("emptyState")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        layout.addWidget(open_button)
        layout.addWidget(empty)
        layout.addStretch(1)
        return page

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        """Handle player shortcuts without intercepting text-editor input."""
        focused = self.focusWidget()
        if isinstance(focused, (QLineEdit, QComboBox)):
            super().keyPressEvent(event)
            return
        key = event.key()
        if key == Qt.Key.Key_F:
            self._toggle_fullscreen()
            event.accept()
            return
        if key == Qt.Key.Key_Escape and self.window().isFullScreen():
            self.window().showNormal()
            event.accept()
            return
        super().keyPressEvent(event)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        """Handle IPTV shortcuts without triggering network work on navigation."""
        if isinstance(event, QKeyEvent):
            key = event.key()
            if key == Qt.Key.Key_F:
                self._toggle_fullscreen()
                event.accept()
                return True
            if key == Qt.Key.Key_Escape and self.window().isFullScreen():
                self.window().showNormal()
                event.accept()
                return True
            if watched is self.channel_list:
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    index = self.channel_list.currentIndex()
                    if index.isValid():
                        self._schedule_selected_channel(index)
                    event.accept()
                    return True
                if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                    row = self.channel_list.currentIndex().row()
                    delta = -1 if key == Qt.Key.Key_Up else 1
                    target = max(0, min(self.channel_model.rowCount() - 1, row + delta))
                    if self.channel_model.rowCount() > 0:
                        target_index = self.channel_model.index(target, 0)
                        self.channel_list.setCurrentIndex(target_index)
                        self._select_index(target_index)
                    event.accept()
                    return True
            content_type = next(
                (
                    kind
                    for kind, content_list in self._content_lists.items()
                    if watched is content_list
                ),
                None,
            )
            if content_type is None:
                return super().eventFilter(watched, event)
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                index = self._content_lists[content_type].currentIndex()
                if index.isValid():
                    self._activate_content_index(content_type, index)
                event.accept()
                return True
            if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                row = self._content_lists[content_type].currentIndex().row()
                delta = -1 if key == Qt.Key.Key_Up else 1
                target = max(0, min(self.content_model.rowCount() - 1, row + delta))
                if self.content_model.rowCount() > 0:
                    target_index = self.content_model.index(target, 0)
                    self._content_lists[content_type].setCurrentIndex(target_index)
                    self._select_content_index(content_type, target_index)
                event.accept()
                return True
        return super().eventFilter(watched, event)

    def _change_page(self, index: int) -> None:
        if not 0 <= index < len(self._navigation_pages):
            return
        page_index = self._navigation_pages[index]
        self.pages.setCurrentIndex(page_index)
        if page_index == 1:
            self._active_content_type = ContentType.LIVE
            self.search_input.setPlaceholderText("Search live channels")
            self.search_input.setAccessibleName("Live channel search")
        elif page_index == 2:
            self._activate_content_page(ContentType.MOVIE)
        elif page_index == 3:
            self._activate_content_page(ContentType.SERIES)
        label = self.navigation_model.data(
            self.navigation_model.index(index, 0), Qt.ItemDataRole.DisplayRole
        )
        self.status_label.setText(f"● {label}")

    def _activate_content_page(self, content_type: ContentType) -> None:
        """Make one non-live catalogue active without performing provider work."""
        self._active_content_type = content_type
        title = "Movies" if content_type is ContentType.MOVIE else "Series"
        self.search_input.setPlaceholderText(f"Search {title.lower()}")
        self.search_input.setAccessibleName(f"{title} search")
        self._active_content_category_id = self._content_category_selectors[
            content_type
        ].currentData()
        self._render_content_catalogue(content_type)

    def _schedule_content_load(self, content_type: ContentType) -> None:
        if not self._loading:
            asyncio.create_task(self.load_content(content_type, self._begin_request()))

    async def load_content(self, content_type: ContentType, generation: int | None = None) -> None:
        """Explicitly load existing movie or series catalogues through application use cases."""
        request_generation = generation if generation is not None else self._begin_request()
        provider_id = self._provider_id()
        if self._browse_content is None:
            self._content_status_labels[content_type].setText("Content browsing is unavailable")
            self._set_loading(False)
            return
        try:
            response = await self._browse_content.execute(
                BrowseContentRequest(provider_id=provider_id, content_type=content_type)
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            if request_generation == self._request_generation:
                self._content_status_labels[content_type].setText("Unable to load content")
                self.status_label.setText("● Load error")
            return
        finally:
            if request_generation == self._request_generation:
                self._set_loading(False)
        if request_generation != self._request_generation:
            return
        if response.error is not None or response.unsupported:
            self._content_status_labels[content_type].setText(
                "Content is unavailable for this provider"
            )
            self.status_label.setText("● Content unavailable")
            return
        self._content_catalogues[content_type] = tuple(response.items)
        await self.refresh_content_categories(content_type, provider_id, request_generation)
        if request_generation != self._request_generation or provider_id != self._provider_id():
            return
        self._render_content_catalogue(content_type)
        title = "movies" if content_type is ContentType.MOVIE else "series"
        self._content_status_labels[content_type].setText(f"{response.total:,} {title} loaded")
        self.status_label.setText("● Ready")

    async def refresh_content_categories(
        self,
        content_type: ContentType,
        provider_id: str,
        generation: int | None = None,
    ) -> None:
        """Populate a non-live category selector only after an explicit catalogue load."""
        if self._load_categories is None:
            return
        try:
            response = await self._load_categories.execute(
                LoadCategoriesRequest(provider_id=provider_id, content_type=content_type)
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            return
        if (
            provider_id != self._provider_id()
            or generation is not None
            and generation != self._request_generation
            or response.error is not None
            or response.unsupported
        ):
            return
        categories = tuple((category.name, category.id) for category in response.categories)
        self._content_categories[content_type] = categories
        selector = self._content_category_selectors[content_type]
        selector.blockSignals(True)
        selector.clear()
        title = "movies" if content_type is ContentType.MOVIE else "series"
        selector.addItem(f"All {title}", None)
        for name, category_id in categories:
            selector.addItem(name, category_id)
        selector.blockSignals(False)

    def _content_category_changed(self, content_type: ContentType) -> None:
        """Filter local non-live content without provider, resolver, or playback work."""
        if self._active_content_type is not content_type:
            return
        self._active_content_category_id = self._content_category_selectors[
            content_type
        ].currentData()
        self._render_content_catalogue(content_type)

    def _render_content_catalogue(self, content_type: ContentType) -> None:
        """Render local title, genre, and year matches from the active non-live snapshot."""
        items = self._content_catalogues.get(content_type, ())
        category_id = self._active_content_category_id
        query = self.search_input.text().strip().casefold()
        category_names = dict(self._content_categories.get(content_type, ()))
        filtered = tuple(
            item
            for item in items
            if (category_id is None or item.category_id == category_id)
            and (
                not query
                or query
                in " ".join(
                    filter(
                        None,
                        (
                            item.title,
                            item.category_id,
                            category_names.get(item.category_id or ""),
                            str(item.year) if item.year is not None else None,
                        ),
                    )
                ).casefold()
            )
        )
        self.content_model.replace_items(filtered)
        title = "movies" if content_type is ContentType.MOVIE else "series"
        self._content_status_labels[content_type].setText(
            f"{len(filtered):,} {title} shown" if filtered else f"No {title} match"
        )

    def _select_content_index(self, content_type: ContentType, index: QModelIndex) -> None:
        """Record content selection locally without implicitly starting playback."""
        if content_type is not self._active_content_type:
            return
        row = index.row()
        if 0 <= row < self.content_model.rowCount():
            self.selected_content = self.content_model.item_at(row)
            item = self.selected_content
            metadata = " · ".join(
                filter(
                    None,
                    (
                        str(item.year) if item.year is not None else None,
                        f"★ {item.rating:g}" if item.rating is not None else None,
                        item.plot,
                    ),
                )
            )
            self._content_detail_labels[content_type].setText(
                f"Selected · {item.title}" + (f" · {metadata}" if metadata else "")
            )

    def _activate_content_index(self, content_type: ContentType, index: QModelIndex) -> None:
        """Open non-live context without moving unimplemented stream resolution into the UI."""
        self._select_content_index(content_type, index)
        item = self.selected_content
        if item is None:
            return
        if content_type is ContentType.SERIES:
            self._content_detail_labels[content_type].setText(
                f"Series selected · {item.title} · "
                "Episode browsing is unavailable for this provider path"
            )
        else:
            self._content_detail_labels[content_type].setText(
                f"Movie selected · {item.title} · "
                "VOD playback is not exposed by the current provider boundary"
            )

    def _begin_request(self) -> int:
        self._request_generation += 1
        self._set_loading(True)
        return self._request_generation

    def _set_loading(self, loading: bool) -> None:
        self._loading = loading
        for button in (self.load_button, self.search_button, self.favorite_button):
            button.setEnabled(not loading)
        if loading:
            self.channel_status.setText("Loading…")
            self.status_label.setText("● Loading")

    def _schedule_load(self) -> None:
        if not self._loading:
            asyncio.create_task(self.load_channels(self._begin_request()))

    def _schedule_search(self) -> None:
        if not self._loading:
            if self._active_content_type is not ContentType.LIVE:
                self._render_content_catalogue(self._active_content_type)
                self.status_label.setText("● Ready")
                return
            asyncio.create_task(self.search_channels(self._begin_request()))

    def _schedule_add_favorite(self) -> None:
        row = self.channel_list.currentIndex().row()
        if 0 <= row < self.channel_model.rowCount():
            channel = self.channel_model.channel_at(row)
            asyncio.create_task(self.add_favorite(channel))

    def _schedule_selected_channel(self, index: QModelIndex) -> None:
        row = index.row()
        if 0 <= row < self.channel_model.rowCount():
            channel = self.channel_model.channel_at(row)
            asyncio.create_task(self.play_channel(channel))

    def _select_index(self, index: QModelIndex) -> None:
        """Record local selection without provider, resolver, cache, or playback work."""
        row = index.row()
        if 0 <= row < self.channel_model.rowCount():
            self.selected_channel = self.channel_model.channel_at(row)
            self._update_channel_context()

    def _channel_summary(self, channel: ChannelDTO) -> str:
        """Format only stable, presentation-safe channel identity fields."""
        number = f"{channel.number:04d} · " if channel.number is not None else ""
        category = f" · {channel.category_id}" if channel.category_id else ""
        return f"{number}{channel.name}{category}"

    def _update_channel_context(self) -> None:
        """Render selected, loading, playing, and error identities as separate state."""
        if self.selected_channel is None:
            self.current_channel_label.setText("Selected · No channel selected")
        else:
            self.current_channel_label.setText(
                f"Selected · {self._channel_summary(self.selected_channel)}"
            )
        if self.loading_channel is not None:
            self.playback_context_label.setText(
                f"Playback · Loading {self._channel_summary(self.loading_channel)}"
            )
        elif self.playback_error_channel is not None:
            self.playback_context_label.setText(
                f"Playback · Unable to play {self._channel_summary(self.playback_error_channel)}"
            )
        elif self.playing_channel is not None:
            self.playback_context_label.setText(
                f"Playing · {self._channel_summary(self.playing_channel)}"
            )
        else:
            self.playback_context_label.setText("Playback · Ready")

    async def load_channels(self, generation: int | None = None) -> None:
        request_generation = generation if generation is not None else self._begin_request()
        try:
            response = await self._browse_channels.execute(
                LoadChannelsRequest(provider_id=self._provider_id())
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            if request_generation == self._request_generation:
                self._render_channels(())
                self.channel_status.setText("Unable to load channels")
                self.status_label.setText("● Load error")
            return
        finally:
            if request_generation == self._request_generation:
                self._set_loading(False)
        if request_generation != self._request_generation:
            return
        if response.error is not None:
            self._render_channels(())
            self.channel_status.setText("Unable to load channels")
            self.status_label.setText("● Load error")
            return
        self._catalogue_channels = tuple(response.channels)
        self._search_channels_result = None
        self._render_active_catalogue()
        if self.selected_channel is None and response.channels:
            self.selected_channel = response.channels[0]
            self._update_channel_context()
        self.channel_status.setText(
            f"{response.total:,} channels loaded" if response.total else "No channels found"
        )
        self.status_label.setText("● Ready")

    async def search_channels(self, generation: int | None = None) -> None:
        request_generation = generation if generation is not None else self._begin_request()
        query = self.search_input.text().strip()
        if not query and self._catalogue_channels:
            if request_generation == self._request_generation:
                self._search_channels_result = None
                self._render_active_catalogue()
                self.channel_status.setText(f"{self.channel_model.rowCount():,} channels loaded")
                self.status_label.setText("● Ready")
                self._set_loading(False)
            return
        try:
            response = await self._search_channels.execute(
                SearchRegisteredChannelsRequest(
                    provider_id=self._provider_id(),
                    query=query,
                )
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            if request_generation == self._request_generation:
                self._render_channels(())
                self.channel_status.setText("Unable to search channels")
                self.status_label.setText("● Search error")
            return
        finally:
            if request_generation == self._request_generation:
                self._set_loading(False)
        if request_generation != self._request_generation:
            return
        self._search_channels_result = tuple(response.channels)
        self._render_active_catalogue()
        self.channel_status.setText(
            f"{response.total:,} channels found" if response.total else "No matching channels"
        )
        self.status_label.setText("● Ready")

    async def add_favorite(self, channel: ChannelDTO) -> None:
        from samotech_iptv.application.dtos import SaveFavoriteRequest

        try:
            response = await self._save_favorite.execute(
                SaveFavoriteRequest(item_id=channel.id, item_type="channel")
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            self.channel_status.setText("Unable to add favorite")
            return
        self.channel_status.setText(
            "Channel added to favorites" if response.success else "Unable to add favorite"
        )

    async def play_channel(self, channel: ChannelDTO) -> None:
        self.selected_channel = channel
        self.loading_channel = channel
        self.playback_error_channel = None
        self._update_channel_context()
        self.status_label.setText("● Loading playback")
        try:
            await self._play_selected_channel(channel.provider_id, channel.id)
        except asyncio.CancelledError:
            raise
        except Exception:
            self.loading_channel = None
            self.playback_error_channel = channel
            self._update_channel_context()
            self.channel_status.setText("Unable to play selected channel")
            self.status_label.setText("● Playback error")
            return
        self.loading_channel = None
        self.playback_error_channel = None
        self.playing_channel = channel
        self._update_channel_context()
        self.status_label.setText("● Playing")

    def _render_channels(self, channels: Sequence[ChannelDTO]) -> None:
        self._channels = list(channels)
        self.channel_model.replace_channels(self._channels)

    def _toggle_fullscreen(self) -> None:
        window = self.window()
        if window.isFullScreen():
            window.showNormal()
        else:
            window.showFullScreen()
