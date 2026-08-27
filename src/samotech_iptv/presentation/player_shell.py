from __future__ import annotations

import asyncio
import platform
from typing import TYPE_CHECKING

from PySide6.QtCore import (
    QEvent,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    QSettings,
    QSize,
    QStringListModel,
    Qt,
    QTimer,
)
from PySide6.QtGui import QColor, QFont, QImage, QKeyEvent, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMenu,
    QPushButton,
    QSlider,
    QSplitter,
    QStackedLayout,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
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
    LoadMovieDetailsRequest,
    LoadSeasonEpisodesRequest,
    LoadSeriesSeasonsRequest,
    PlaybackOutcome,
    PlaybackTarget,
    ProviderCapabilities,
    SearchRegisteredChannelsRequest,
)
from samotech_iptv.application.local_subtitles import (
    LocalSubtitleError,
    LocalSubtitleFile,
    inspect_local_subtitle,
)
from samotech_iptv.application.ports.artwork_port import ArtworkRequest, ArtworkRole
from samotech_iptv.core.constants import APP_VERSION
from samotech_iptv.presentation.playback_diagnostics import (
    PlaybackDiagnosticContext,
    format_playback_diagnostic_report,
)
from samotech_iptv.presentation.task_owner import cancel_owned_tasks, create_owned_task
from samotech_iptv.presentation.theme.tokens import COLORS, RADII, SPACING
from samotech_iptv.presentation.user_messages import playback_failure_message
from samotech_iptv.presentation.viewmodels.channel_list_model import ChannelListModel
from samotech_iptv.presentation.viewmodels.content_list_model import ContentListModel

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Sequence

    from samotech_iptv.application.ports.artwork_port import ArtworkPort
    from samotech_iptv.application.ports.player_port import PlayerPort
    from samotech_iptv.application.use_cases.browse_channels import BrowseChannels
    from samotech_iptv.application.use_cases.browse_content import BrowseContent
    from samotech_iptv.application.use_cases.list_providers import ListProviders
    from samotech_iptv.application.use_cases.load_categories import LoadCategories
    from samotech_iptv.application.use_cases.load_movie_details import LoadMovieDetails
    from samotech_iptv.application.use_cases.load_provider_capabilities import (
        LoadProviderCapabilities,
    )
    from samotech_iptv.application.use_cases.load_theme_preference import LoadThemePreference
    from samotech_iptv.application.use_cases.record_history import RecordHistory
    from samotech_iptv.application.use_cases.save_favorite import SaveFavorite
    from samotech_iptv.application.use_cases.save_theme_preference import SaveThemePreference
    from samotech_iptv.application.use_cases.search_registered_channels import (
        SearchRegisteredChannels,
    )
    from samotech_iptv.application.use_cases.series_discovery import (
        LoadSeasonEpisodes,
        LoadSeriesSeasons,
    )

__all__ = ["PlayerShell"]


class ContentCardDelegate(QStyledItemDelegate):
    """Render compact media cards from existing title and metadata strings."""

    def sizeHint(  # noqa: N802
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QSize:  # noqa: N802
        del option, index
        return QSize(172, 214)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect.adjusted(6, 6, -6, -6)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS.primary_muted if selected else COLORS.surface_elevated))
        painter.drawRoundedRect(rect, RADII.md, RADII.md)
        poster = rect.adjusted(8, 8, -8, -70)
        painter.setBrush(QColor(COLORS.primary if selected else COLORS.surface_muted))
        painter.drawRoundedRect(poster, RADII.sm, RADII.sm)
        title = str(index.data(Qt.ItemDataRole.DisplayRole) or "Untitled")
        initials = "".join(part[0] for part in title.split()[:2]).upper() or "?"
        painter.setPen(QColor(COLORS.primary_hover))
        painter.setFont(QFont("Sans", 24, QFont.Weight.Bold))
        painter.drawText(poster, Qt.AlignmentFlag.AlignCenter, initials)
        painter.setPen(QColor(COLORS.text))
        painter.setFont(QFont("Sans", 10, QFont.Weight.Bold))
        text_rect = rect.adjusted(10, poster.bottom() - rect.top() + 14, -10, -10)
        painter.drawText(text_rect, Qt.TextFlag.TextWordWrap, title)
        painter.restore()


class PlayerShell(QWidget):
    """Player-first desktop shell around the existing application use cases."""

    _STYLESHEET = (
        """
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
    QFrame#sidebar {
        background: @COLORS.surface_muted@;
        border-right: 1px solid @COLORS.border@;
    }
    QLabel#sectionKicker {
        color: @COLORS.text_muted@;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.5px;
    }
    QLabel#heroTitle {
        color: @COLORS.text@;
        font-size: 28px;
        font-weight: 800;
    }
    QLabel#heroSubtitle {
        color: @COLORS.text_muted@;
        font-size: 14px;
    }
    QFrame#playerOverlay {
        background: rgba(4, 8, 14, 218);
        border: 1px solid @COLORS.border@;
        border-radius: @RADII.md@px;
    }
    QFrame#playerOverlay QPushButton {
        background: rgba(17, 23, 34, 235);
        border-color: @COLORS.border_strong@;
    }
    QFrame#playerOverlay QPushButton#primary {
        background: @COLORS.primary@;
        border-color: @COLORS.primary_hover@;
    }
    QFrame#emptyPanel {
        background: @COLORS.surface@;
        border: 1px dashed @COLORS.border@;
        border-radius: @RADII.md@px;
    }
    QLabel#contentArtwork {
        background: @COLORS.surface_muted@;
        border: 1px solid @COLORS.border@;
        border-radius: @RADII.sm@px;
        color: @COLORS.text_muted@;
        min-height: 135px;
    }
    QFrame#sidebar QPushButton {
        text-align: left;
        background: transparent;
        border: 0;
        color: @COLORS.text_muted@;
        padding: 10px 12px;
    }
    QFrame#sidebar QPushButton:hover, QFrame#sidebar QPushButton:focus {
        background: @COLORS.primary_muted@;
        color: @COLORS.text@;
    }
    """.replace("@COLORS.surface_muted@", COLORS.surface_muted)
        .replace("@COLORS.border@", COLORS.border)
        .replace("@COLORS.text_muted@", COLORS.text_muted)
        .replace("@COLORS.text@", COLORS.text)
        .replace("@RADII.md@", str(RADII.md))
        .replace("@COLORS.border_strong@", COLORS.border_strong)
        .replace("@COLORS.primary@", COLORS.primary)
        .replace("@COLORS.primary_hover@", COLORS.primary_hover)
        .replace("@COLORS.surface@", COLORS.surface)
        .replace("@COLORS.primary_muted@", COLORS.primary_muted)
    )

    def __init__(
        self,
        video_surface: QWidget,
        browse_channels: BrowseChannels,
        play_selected_channel: Callable[[PlaybackTarget], Awaitable[object]],
        search_channels: SearchRegisteredChannels,
        save_favorite: SaveFavorite,
        pause_playback: Callable[[], Awaitable[None]],
        resume_playback: Callable[[], Awaitable[None]],
        stop_playback: Callable[[], Awaitable[None]],
        list_providers: ListProviders,
        open_favorites_dialog: Callable[[], object],
        open_history_dialog: Callable[[], object],
        open_category_dialog: Callable[[], object],
        open_epg_dialog: Callable[[str | None, str | None], object],
        open_provider_list_dialog: Callable[[], object],
        open_settings_dialog: Callable[[], object],
        load_categories: LoadCategories | None = None,
        browse_content: BrowseContent | None = None,
        load_provider_capabilities: LoadProviderCapabilities | None = None,
        load_movie_details: LoadMovieDetails | None = None,
        load_series_seasons: LoadSeriesSeasons | None = None,
        load_season_episodes: LoadSeasonEpisodes | None = None,
        artwork_loader: ArtworkPort | None = None,
        invalidate_pending_playback: Callable[[], None] | None = None,
        player_port: PlayerPort | None = None,
        progress_recorder: RecordHistory | None = None,
        load_theme_preference: LoadThemePreference | None = None,
        save_theme_preference: SaveThemePreference | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("playerShell")
        self.setStyleSheet(self._STYLESHEET)
        self._browse_channels = browse_channels
        self._load_categories = load_categories
        self._browse_content = browse_content
        self._load_provider_capabilities = load_provider_capabilities
        self._load_movie_details = load_movie_details
        self._load_series_seasons = load_series_seasons
        self._load_season_episodes = load_season_episodes
        self._artwork_loader = artwork_loader
        self._invalidate_pending_playback = invalidate_pending_playback
        self._player_port = player_port
        self._progress_recorder = progress_recorder
        self._load_theme_preference = load_theme_preference
        self._save_theme_preference = save_theme_preference
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
        self._content_sort_selectors: dict[ContentType, QComboBox] = {}
        self._content_status_labels: dict[ContentType, QLabel] = {}
        self._content_detail_labels: dict[ContentType, QLabel] = {}
        self._content_artwork_labels: dict[ContentType, QLabel] = {}
        self._content_back_buttons: dict[ContentType, QPushButton] = {}
        self._content_activate_buttons: dict[ContentType, QPushButton] = {}
        self._content_favorite_buttons: dict[ContentType, QPushButton] = {}
        self._content_load_buttons: dict[ContentType, QPushButton] = {}
        self._global_search_results: list[tuple[str, object]] = []
        self._home_action_buttons: dict[str, QPushButton] = {}
        self._home_status_label: QLabel | None = None
        self._settings_theme_selector: QComboBox | None = None
        self._settings_status_label: QLabel | None = None
        self._series_view_mode = "catalogue"
        self._series_context_id: str | None = None
        self._series_seasons: tuple[ContentItemDTO, ...] = ()
        self._series_episodes: tuple[ContentItemDTO, ...] = ()
        self._provider_ids: list[str] = []
        self._provider_types: dict[str, str] = {}
        self._active_category_id: str | None = None
        self._request_generation = 0
        self._non_live_generation = 0
        self._artwork_generation = 0
        self._active_non_live_action: tuple[ContentType, str, str] | None = None
        self._active_playback_content_type: ContentType | None = None
        self._control_poll_pending = False
        self._last_persisted_progress: tuple[str, int, int] | None = None
        self._subtitle_session_token = 0
        self._local_subtitle_file: LocalSubtitleFile | None = None
        self._disposed = False
        settings = QSettings("SamoTech", "IPTVPlayer")
        self._sidebar_expanded = bool(settings.value("sidebar_expanded", True, type=bool))
        self._sidebar_expanded_width = 188
        self._sidebar_collapsed_width = 64
        self._player_overlay: QFrame | None = None
        self._player_stage: QFrame | None = None
        self._overlay_timer = QTimer(self)
        self._overlay_timer.setSingleShot(True)
        self._overlay_timer.setInterval(3500)
        self._overlay_timer.timeout.connect(self._hide_player_overlay)
        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(500)
        self._progress_timer.timeout.connect(self._schedule_progress_poll)
        self._loading = False
        self.selected_channel: ChannelDTO | None = None
        self.playing_channel: ChannelDTO | None = None
        self.loading_channel: ChannelDTO | None = None
        self.playback_error_channel: ChannelDTO | None = None
        self.selected_content: ContentItemDTO | None = None
        self.channel_model = ChannelListModel()
        self.content_model = ContentListModel()
        self.global_search_model = QStringListModel()
        self.provider_selector = QComboBox()
        self.provider_selector.setEditable(False)
        self.provider_selector.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.provider_selector.setPlaceholderText("Select provider")
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
        self.search_input.textChanged.connect(self._search_query_changed)
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
        self.navigation.setMinimumWidth(self._sidebar_collapsed_width)
        self.navigation.setMaximumWidth(self._sidebar_expanded_width)
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
        self.pages.addWidget(self._build_search_page())
        self.pages.addWidget(
            self._build_library_page(
                "EPG",
                "Browse the electronic programme guide.",
                self._open_selected_channel_epg,
            )
        )
        self.pages.addWidget(
            self._build_library_page(
                "Providers",
                "Manage your M3U, Xtream, and MAG sources.",
                self._open_provider_list_dialog,
            )
        )
        self.pages.addWidget(self._build_settings_page())
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
            create_owned_task(self, self.refresh_providers())
        except RuntimeError:
            pass
        self.installEventFilter(self)
        self.channel_list.installEventFilter(self)
        self.navigation.installEventFilter(self)
        self.fullscreen_button.installEventFilter(self)
        if self._player_stage is not None:
            self._player_stage.installEventFilter(self)
        if self._player_overlay is not None:
            self._player_overlay.installEventFilter(self)
        video_surface.installEventFilter(self)
        if self._player_port is not None:
            self._progress_timer.start()
        self._set_sidebar_expanded(self._sidebar_expanded, persist=False)
        self._show_player_overlay()

    async def refresh_providers(self) -> None:
        """Populate the selector from safe provider summaries."""
        try:
            providers = await self._list_providers.execute()
            provider_items = list(providers)
            current_id = self._provider_id()
            self._provider_ids = [provider.id for provider in provider_items]
            self._provider_types = {provider.id: provider.type for provider in provider_items}
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
                self._set_status_text("● No providers")
        except asyncio.CancelledError:
            raise
        except Exception:
            self.provider_selector.blockSignals(False)
            self._set_status_text("● Providers unavailable")

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
        entries.append(("Search", 6))
        if self._provider_capabilities.epg:
            entries.append(("EPG", 7))
        entries.extend([("Providers", 8), ("Settings", 9)])
        current_page = self.pages.currentIndex() if hasattr(self, "pages") else 0
        self._navigation_entries = entries
        compact_by_page = {
            0: "⌂",
            1: "TV",
            2: "M",
            3: "S",
            4: "★",
            5: "↺",
            6: "⌕",
            7: "EPG",
            8: "P",
            9: "⚙",
        }
        labels = (
            [label for label, _ in entries]
            if self._sidebar_expanded
            else [compact_by_page[page] for _, page in entries]
        )
        self.navigation_model.setStringList(labels)
        for row, (label, _) in enumerate(entries):
            index = self.navigation_model.index(row, 0)
            self.navigation_model.setData(index, label, Qt.ItemDataRole.ToolTipRole)
        self._navigation_pages = [page for _, page in entries]
        try:
            navigation_row = self._navigation_pages.index(current_page)
        except ValueError:
            navigation_row = 0
            self.pages.setCurrentIndex(self._navigation_pages[navigation_row])
        self.navigation.setCurrentIndex(self.navigation_model.index(navigation_row, 0))

    def _provider_changed(self, _: int) -> None:
        """Clear stale channel and artwork results when the active provider changes."""
        previous_provider_id = self._provider_id()
        cancel_owned_tasks(self)
        self._artwork_generation += 1
        self._invalidate_local_subtitle_session()
        if self._artwork_loader is not None:
            self._artwork_loader.clear_provider(previous_provider_id)
        if self._invalidate_pending_playback is not None:
            self._invalidate_pending_playback()
        self._request_generation += 1
        self._invalidate_non_live_requests()
        self._set_loading(False)
        self._catalogue_channels = ()
        self._search_channels_result = None
        self._content_catalogues.clear()
        self._content_categories.clear()
        self._global_search_results.clear()
        self.global_search_model.setStringList([])
        self._clear_series_navigation()
        self._active_content_type = ContentType.LIVE
        self._active_playback_content_type = None
        self._last_persisted_progress = None
        self._set_control_availability()
        self._active_content_category_id = None
        self.selected_content = None
        self._clear_artwork_labels()
        self._active_category_id = None
        self.category_selector.blockSignals(True)
        self.category_selector.clear()
        self.category_selector.addItem("All live channels", None)
        self.category_selector.blockSignals(False)
        self.selected_channel = None
        self.loading_channel = None
        self.playing_channel = None
        self.playback_error_channel = None
        self._render_channels(())
        self._update_channel_context()
        provider_id = self._provider_id()
        self._provider_capabilities = ProviderCapabilities()
        self._refresh_navigation()
        self._refresh_home_actions()
        self._set_status_text("● Provider selected" if provider_id else "● Select a provider")
        self.channel_status.setText("No channels loaded")
        if provider_id:
            try:
                create_owned_task(self, self.refresh_categories(provider_id))
                create_owned_task(self, self.refresh_provider_capabilities(provider_id))
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
        self._refresh_home_actions()

    def _provider_id(self) -> str:
        """Return the registered provider ID stored as safe selector item data."""
        index = self.provider_selector.currentIndex()
        data = self.provider_selector.itemData(index)
        return str(data or "")

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
        top_bar.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.sm)
        top_bar.setSpacing(SPACING.md)
        self.sidebar_toggle = QPushButton("Menu")
        self.sidebar_toggle.setAccessibleName("Toggle navigation sidebar")
        self.sidebar_toggle.setToolTip("Expand or collapse navigation")
        self.sidebar_toggle.clicked.connect(self._toggle_sidebar)
        top_bar.addWidget(self.sidebar_toggle, 0)
        brand_column = QVBoxLayout()
        brand_column.setSpacing(1)
        brand = QLabel("SAMOTECH IPTV")
        brand.setObjectName("brand")
        eyebrow = QLabel("WATCH WITHOUT FRICTION")
        eyebrow.setObjectName("eyebrow")
        brand_column.addWidget(brand)
        brand_column.addWidget(eyebrow)
        top_bar.addLayout(brand_column)
        top_bar.addSpacing(SPACING.sm)
        top_bar.addWidget(self.provider_selector, 0)
        top_bar.addWidget(self.search_input, 1)
        self.provider_badge = QLabel("No provider")
        self.provider_badge.setObjectName("pageSubtitle")
        self.provider_badge.setAccessibleName("Provider connection summary")
        top_bar.addWidget(self.provider_badge, 0)
        top_bar.addWidget(self.status_label, 0)
        settings_button = QPushButton("Settings")
        settings_button.setAccessibleName("Open settings")
        settings_button.setToolTip("Open player settings")
        settings_button.clicked.connect(self.open_settings_page)
        top_bar.addWidget(settings_button, 0)

        player_card = QFrame()
        player_card.setObjectName("playerCard")
        player_layout = QVBoxLayout(player_card)
        player_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        player_layout.setSpacing(SPACING.sm)
        video_surface.setMinimumSize(420, 260)
        self._player_stage = QFrame()
        self._player_stage.setObjectName("playerStage")
        stage_layout = QStackedLayout(self._player_stage)
        stage_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)
        stage_layout.addWidget(video_surface)
        self._player_overlay = QFrame()
        self._player_overlay.setObjectName("playerOverlay")
        overlay_layout = QVBoxLayout(self._player_overlay)
        overlay_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.md)
        overlay_layout.setSpacing(SPACING.md)
        overlay_top = QHBoxLayout()
        overlay_top.addWidget(self.playback_context_label, 1)
        self.overlay_status = QLabel("● Ready")
        self.overlay_status.setObjectName("status")
        self.overlay_status.setText(self.status_label.text())
        overlay_top.addWidget(self.overlay_status, 0)
        overlay_layout.addLayout(overlay_top)

        progress_row = QHBoxLayout()
        self.elapsed_label = QLabel("0:00")
        self.elapsed_label.setAccessibleName("Elapsed playback time")
        self.duration_label = QLabel("0:00")
        self.duration_label.setAccessibleName("Playback duration")
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.setSingleStep(10)
        self.seek_slider.setPageStep(100)
        self.seek_slider.setAccessibleName("Playback seek position")
        self.seek_slider.setToolTip("Seek within the current movie or episode")
        self.seek_slider.sliderMoved.connect(self._preview_seek_position)
        self.seek_slider.sliderReleased.connect(self._commit_seek_position)
        progress_row.addWidget(self.elapsed_label, 0)
        progress_row.addWidget(self.seek_slider, 1)
        progress_row.addWidget(self.duration_label, 0)
        overlay_layout.addLayout(progress_row)

        overlay_center = QHBoxLayout()
        overlay_center.addStretch(1)
        self.pause_button = QPushButton("Pause")
        self.pause_button.setAccessibleName("Pause playback")
        self.pause_button.setToolTip("Pause the current stream")
        self.pause_button.clicked.connect(lambda: create_owned_task(self, self._pause_playback()))
        self.resume_button = QPushButton("Play")
        self.resume_button.setObjectName("primary")
        self.resume_button.setAccessibleName("Resume playback")
        self.resume_button.setToolTip("Resume the current stream")
        self.resume_button.clicked.connect(lambda: create_owned_task(self, self._resume_playback()))
        self.stop_button = QPushButton("Stop")
        self.stop_button.setAccessibleName("Stop playback")
        self.stop_button.setToolTip("Stop the current stream")
        self.stop_button.clicked.connect(lambda: create_owned_task(self, self._stop_playback()))
        overlay_center.addWidget(self.pause_button)
        overlay_center.addWidget(self.resume_button)
        overlay_center.addWidget(self.stop_button)
        self.back_30_button = QPushButton("−30")
        self.back_30_button.setAccessibleName("Seek backward thirty seconds")
        self.back_30_button.clicked.connect(lambda: self._schedule_relative_seek(-30))
        self.back_10_button = QPushButton("−10")
        self.back_10_button.setAccessibleName("Seek backward ten seconds")
        self.back_10_button.clicked.connect(lambda: self._schedule_relative_seek(-10))
        self.forward_10_button = QPushButton("+10")
        self.forward_10_button.setAccessibleName("Seek forward ten seconds")
        self.forward_10_button.clicked.connect(lambda: self._schedule_relative_seek(10))
        self.forward_30_button = QPushButton("+30")
        self.forward_30_button.setAccessibleName("Seek forward thirty seconds")
        self.forward_30_button.clicked.connect(lambda: self._schedule_relative_seek(30))
        for button in (
            self.back_30_button,
            self.back_10_button,
            self.forward_10_button,
            self.forward_30_button,
        ):
            overlay_center.addWidget(button)
        self.restart_button = QPushButton("Restart")
        self.restart_button.setAccessibleName("Restart playback")
        self.restart_button.setToolTip("Restart the current movie or episode")
        self.restart_button.clicked.connect(self._schedule_restart)
        overlay_center.addWidget(self.restart_button)
        self.retry_button = QPushButton("Retry")
        self.retry_button.setAccessibleName("Retry failed playback")
        self.retry_button.setToolTip("Retry the channel that last failed to start")
        self.retry_button.clicked.connect(self._schedule_retry_playback)
        overlay_center.addWidget(self.retry_button)
        self.previous_episode_button = QPushButton("Previous episode")
        self.previous_episode_button.setAccessibleName("Play previous episode")
        self.previous_episode_button.setToolTip("Play the previous episode when available")
        self.previous_episode_button.clicked.connect(lambda: self._schedule_adjacent_episode(-1))
        self.next_episode_button = QPushButton("Next episode")
        self.next_episode_button.setAccessibleName("Play next episode")
        self.next_episode_button.setToolTip("Play the next episode when available")
        self.next_episode_button.clicked.connect(lambda: self._schedule_adjacent_episode(1))
        overlay_center.addWidget(self.previous_episode_button)
        overlay_center.addWidget(self.next_episode_button)
        overlay_center.addStretch(1)
        overlay_layout.addLayout(overlay_center)

        controls_row = QHBoxLayout()
        self.volume_label = QLabel("Volume")
        self.volume_label.setAccessibleName("Volume label")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setMaximumWidth(150)
        self.volume_slider.setAccessibleName("Playback volume")
        self.volume_slider.setToolTip("Set playback volume")
        self.volume_slider.valueChanged.connect(self._schedule_volume_change)
        self.mute_button = QPushButton("Mute")
        self.mute_button.setAccessibleName("Mute playback")
        self.mute_button.setToolTip("Mute or unmute playback")
        self.mute_button.clicked.connect(self._schedule_toggle_mute)
        self.audio_button = QPushButton("Audio")
        self.audio_button.setAccessibleName("Audio track menu")
        self.audio_button.setToolTip("Choose a native audio track")
        self.audio_button.clicked.connect(self._schedule_audio_menu)
        self.subtitle_button = QPushButton("Subtitles")
        self.subtitle_button.setAccessibleName("Subtitle track menu")
        self.subtitle_button.setToolTip("Choose or disable native subtitles")
        self.subtitle_button.clicked.connect(self._schedule_subtitle_menu)
        self.aspect_button = QPushButton("Aspect")
        self.aspect_button.setAccessibleName("Aspect ratio menu")
        self.aspect_button.setToolTip("Choose a native aspect-ratio override")
        self.aspect_button.clicked.connect(self._show_aspect_menu)
        self.info_button = QPushButton("Info")
        self.info_button.setAccessibleName("Playback diagnostics")
        self.info_button.setToolTip("Show safe playback diagnostics")
        self.info_button.clicked.connect(self._show_playback_info)
        controls_row.addWidget(self.volume_label, 0)
        controls_row.addWidget(self.volume_slider, 1)
        controls_row.addWidget(self.mute_button, 0)
        controls_row.addWidget(self.audio_button, 0)
        controls_row.addWidget(self.subtitle_button, 0)
        controls_row.addWidget(self.aspect_button, 0)
        controls_row.addWidget(self.info_button, 0)
        overlay_layout.addLayout(controls_row)

        overlay_bottom = QHBoxLayout()
        self.current_channel_label.setObjectName("pageSubtitle")
        overlay_bottom.addWidget(self.current_channel_label, 1)
        self.fullscreen_button = QPushButton("Fullscreen")
        self.fullscreen_button.setAccessibleName("Toggle fullscreen")
        self.fullscreen_button.setToolTip("Enter or exit fullscreen mode (F)")
        self.fullscreen_button.clicked.connect(self._toggle_fullscreen)
        overlay_bottom.addWidget(self.fullscreen_button, 0)
        overlay_layout.addLayout(overlay_bottom)
        stage_layout.addWidget(self._player_overlay)
        player_layout.addWidget(self._player_stage, 1)
        self._set_control_availability()

        catalogue_body = QSplitter(Qt.Orientation.Horizontal)
        catalogue_body.setChildrenCollapsible(False)
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(SPACING.sm, SPACING.md, SPACING.sm, SPACING.md)
        sidebar_layout.setSpacing(SPACING.sm)
        sidebar_label = QLabel("NAVIGATION")
        sidebar_label.setObjectName("sectionKicker")
        sidebar_layout.addWidget(sidebar_label)
        sidebar_layout.addWidget(self.navigation, 1)
        catalogue_body.addWidget(self.sidebar)
        catalogue_body.addWidget(self.pages)
        catalogue_body.setStretchFactor(0, 0)
        catalogue_body.setStretchFactor(1, 1)
        catalogue_body.setSizes([self._sidebar_expanded_width, 960])

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

    def _toggle_sidebar(self) -> None:
        """Toggle expanded labels while keeping the navigation row stable."""
        self._set_sidebar_expanded(not self._sidebar_expanded)

    def _set_sidebar_expanded(self, expanded: bool, *, persist: bool = True) -> None:
        """Apply and optionally persist the expanded/collapsed sidebar state."""
        self._sidebar_expanded = expanded
        width = self._sidebar_expanded_width if expanded else self._sidebar_collapsed_width
        self.navigation.setMinimumWidth(width)
        self.navigation.setMaximumWidth(width)
        if hasattr(self, "sidebar"):
            self.sidebar.setMinimumWidth(width)
            self.sidebar.setMaximumWidth(width)
        self.sidebar_toggle.setText("Collapse" if expanded else "☰")
        self.sidebar_toggle.setToolTip("Collapse navigation" if expanded else "Expand navigation")
        if hasattr(self, "_navigation_entries"):
            self._refresh_navigation()
        if persist:
            QSettings("SamoTech", "IPTVPlayer").setValue("sidebar_expanded", expanded)

    def _toggle_player_overlay(self) -> None:
        if self._player_overlay is None:
            return
        if self._player_overlay.isVisible():
            self._hide_player_overlay()
        else:
            self._show_player_overlay()

    def _show_player_overlay(self) -> None:
        if self._player_overlay is None:
            return
        self._player_overlay.show()
        self._overlay_timer.start()

    def _hide_player_overlay(self) -> None:
        if self._player_overlay is not None and (
            self.playing_channel is not None or self.selected_content is not None
        ):
            self._player_overlay.hide()

    def _build_home_page(self) -> QWidget:
        page = QFrame()
        page.setObjectName("contentCard")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.md)
        kicker = QLabel("YOUR MEDIA SPACE")
        kicker.setObjectName("sectionKicker")
        layout.addWidget(kicker)
        title = QLabel("Ready when you are")
        title.setObjectName("heroTitle")
        layout.addWidget(title)
        subtitle = QLabel("Connect a provider to load your real channels, movies, and series.")
        subtitle.setObjectName("heroSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        self._home_status_label = QLabel("No provider selected")
        self._home_status_label.setObjectName("pageSubtitle")
        layout.addWidget(self._home_status_label)
        actions_panel = QFrame()
        actions_panel.setObjectName("emptyPanel")
        actions_layout = QHBoxLayout(actions_panel)
        actions_layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        actions_layout.setSpacing(SPACING.sm)
        for key, label, page_index in (
            ("live", "Live TV", 1),
            ("movies", "Movies", 2),
            ("series", "Series", 3),
        ):
            button = QPushButton(label)
            button.setObjectName("primary" if key == "live" else "")
            button.setAccessibleName(f"Open {label}")
            button.clicked.connect(lambda _checked=False, p=page_index: self._navigate_to_page(p))
            actions_layout.addWidget(button, 1)
            self._home_action_buttons[key] = button
        layout.addWidget(actions_panel)
        providers = QPushButton("Manage Providers")
        providers.setAccessibleName("Manage IPTV providers")
        providers.setToolTip("Add, edit, test, or remove providers")
        providers.clicked.connect(self._open_provider_list_dialog)
        layout.addWidget(providers, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)
        self._refresh_home_actions()
        return page

    def _navigate_to_page(self, page_index: int) -> None:
        """Navigate to a capability-backed page through the current sidebar mapping."""
        try:
            row = self._navigation_pages.index(page_index)
        except ValueError:
            return
        self.navigation.setCurrentIndex(self.navigation_model.index(row, 0))
        self._change_page(row)

    def _open_selected_channel_epg(self) -> None:
        """Open EPG with selected Live-TV context rather than requesting opaque IDs."""
        channel = self.selected_channel
        if channel is None:
            self._set_status_text(
                "● Select a loaded live channel before opening its programme guide"
            )
            return
        self._open_epg_dialog(channel.provider_id, channel.id)

    def _refresh_home_actions(self) -> None:
        """Show only provider-backed content destinations on Home."""
        if not self._home_action_buttons:
            return
        capabilities = self._provider_capabilities
        available = {
            "live": capabilities.live_tv,
            "movies": capabilities.vod_movies,
            "series": capabilities.vod_series,
        }
        for key, button in self._home_action_buttons.items():
            button.setVisible(available[key])
        if self._home_status_label is not None:
            if any(available.values()):
                self._home_status_label.setText("Choose a real content area to begin browsing")
            else:
                self._home_status_label.setText("Select a provider to see available content")

    def _build_search_page(self) -> QWidget:
        page = QFrame()
        page.setObjectName("contentCard")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.md)
        kicker = QLabel("SEARCH")
        kicker.setObjectName("sectionKicker")
        layout.addWidget(kicker)
        title = QLabel("Find something to watch")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        subtitle = QLabel("Search only the content already loaded for the active provider.")
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        self.global_search_filter = QComboBox()
        self.global_search_filter.addItem("All", "ALL")
        self.global_search_filter.addItem("Live", "LIVE")
        self.global_search_filter.addItem("Movies", "MOVIES")
        self.global_search_filter.addItem("Series", "SERIES")
        self.global_search_filter.addItem("Episodes", "EPISODES")
        self.global_search_filter.setAccessibleName("Global search content filter")
        self.global_search_filter.currentIndexChanged.connect(
            lambda _: self._render_global_search()
        )
        layout.addWidget(self.global_search_filter)
        self.global_search_list = QListView()
        self.global_search_list.setObjectName("channels")
        self.global_search_list.setAccessibleName("Global search results")
        self.global_search_list.setToolTip(
            "Select a result and press Enter to open its content area"
        )
        self.global_search_list.setModel(self.global_search_model)
        self.global_search_list.doubleClicked.connect(self._activate_search_result)
        self.global_search_list.installEventFilter(self)
        layout.addWidget(self.global_search_list, 1)
        self.global_search_status = QLabel("Type in the search field to search loaded content")
        self.global_search_status.setObjectName("pageSubtitle")
        layout.addWidget(self.global_search_status)
        self._render_global_search()
        return page

    def _search_query_changed(self, query: str) -> None:
        """Update local global-search results without issuing a network request."""
        if self.pages.currentIndex() == 6:
            self._render_global_search(query)

    def _render_global_search(self, query: str | None = None) -> None:
        query = (
            self.search_input.text().strip().casefold()
            if query is None
            else query.strip().casefold()
        )
        if not hasattr(self, "global_search_model"):
            return
        results: list[tuple[str, object]] = []
        filter_kind = getattr(self, "global_search_filter", None)
        selected_kind = filter_kind.currentData() if filter_kind is not None else "ALL"
        if query:
            if selected_kind in {"ALL", "LIVE"}:
                for channel_item in self._catalogue_channels:
                    if query in self._channel_summary(channel_item).casefold():
                        results.append(("LIVE", channel_item))
            for content_item in self._content_catalogues.get(ContentType.MOVIE, ()):
                searchable = " ".join(
                    filter(
                        None,
                        (
                            content_item.title,
                            content_item.plot,
                            content_item.genre,
                            content_item.director,
                            content_item.cast,
                            content_item.country,
                            content_item.release_date,
                            content_item.category_id,
                            str(content_item.year) if content_item.year is not None else None,
                            str(content_item.rating) if content_item.rating is not None else None,
                        ),
                    )
                )
                if selected_kind in {"ALL", "MOVIES"} and query in searchable.casefold():
                    results.append(("MOVIES", content_item))
            for content_item in self._content_catalogues.get(ContentType.SERIES, ()):
                searchable = " ".join(
                    filter(
                        None,
                        (
                            content_item.title,
                            content_item.plot,
                            content_item.genre,
                            content_item.director,
                            content_item.cast,
                            content_item.country,
                            content_item.release_date,
                            content_item.category_id,
                            str(content_item.year) if content_item.year is not None else None,
                            str(content_item.rating) if content_item.rating is not None else None,
                        ),
                    )
                )
                if selected_kind in {"ALL", "SERIES"} and query in searchable.casefold():
                    results.append(("SERIES", content_item))
            if selected_kind in {"ALL", "EPISODES"}:
                for episode in self._series_episodes:
                    searchable = " ".join(
                        filter(
                            None,
                            (
                                episode.title,
                                episode.plot,
                                episode.series_id,
                                str(episode.season) if episode.season is not None else None,
                                (
                                    str(episode.episode_number)
                                    if episode.episode_number is not None
                                    else None
                                ),
                            ),
                        )
                    )
                    if query in searchable.casefold():
                        results.append(("EPISODES", episode))
        self._global_search_results = results
        labels = [
            f"{kind}  ·  {getattr(item, 'title', getattr(item, 'name', ''))}"
            for kind, item in results
        ]
        self.global_search_model.setStringList(labels)
        if query and not results:
            self.global_search_status.setText("No loaded content matches this search")
        elif query:
            self.global_search_status.setText(f"{len(results):,} loaded result(s)")
        else:
            self.global_search_status.setText("Type in the search field to search loaded content")

    def _activate_search_result(self, index: QModelIndex) -> None:
        row = index.row()
        if not 0 <= row < len(self._global_search_results):
            return
        kind, item = self._global_search_results[row]
        if kind == "LIVE":
            self._navigate_to_page(1)
        elif kind == "MOVIES":
            self._navigate_to_page(2)
        else:
            self._navigate_to_page(3)
        self.search_input.setFocus(Qt.FocusReason.OtherFocusReason)

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
        sort_selector = QComboBox()
        sort_selector.addItem("Provider order", "provider")
        sort_selector.addItem("Title A–Z", "title")
        sort_selector.addItem("Newest first", "year_desc")
        sort_selector.addItem("Rating", "rating_desc")
        sort_selector.setAccessibleName(f"{title_text} sort order")
        sort_selector.setToolTip("Sort the loaded catalogue without network activity")
        sort_selector.currentIndexChanged.connect(
            lambda _: self._content_sort_changed(content_type)
        )
        activate_button = QPushButton(
            "Play selected" if content_type is ContentType.MOVIE else "Open series"
        )
        activate_button.setAccessibleName(
            "Play selected movie" if content_type is ContentType.MOVIE else "Open selected series"
        )
        activate_button.clicked.connect(lambda: self._activate_current_content(content_type))
        favorite_button = QPushButton("Add favorite")
        favorite_button.setAccessibleName(
            "Add selected movie to favorites"
            if content_type is ContentType.MOVIE
            else "Add selected series to favorites"
        )
        favorite_button.clicked.connect(lambda: self._schedule_content_favorite(content_type))
        actions.addWidget(load_button)
        actions.addWidget(category_selector)
        actions.addWidget(sort_selector)
        actions.addWidget(activate_button)
        actions.addWidget(favorite_button)
        if content_type is ContentType.SERIES:
            back_button = QPushButton("Back")
            back_button.setAccessibleName("Return to series catalogue")
            back_button.setEnabled(False)
            back_button.clicked.connect(self._back_series_navigation)
            self._content_back_buttons[content_type] = back_button
            actions.addWidget(back_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        content_list = QListView()
        content_list.setObjectName("channels")
        content_list.setAccessibleName(f"{title_text} catalogue")
        content_list.setToolTip("Select an item and press Enter or double-click to activate")
        content_list.setModel(self.content_model)
        content_list.setItemDelegate(ContentCardDelegate(content_list))
        content_list.setViewMode(QListView.ViewMode.IconMode)
        content_list.setFlow(QListView.Flow.LeftToRight)
        content_list.setWrapping(True)
        content_list.setResizeMode(QListView.ResizeMode.Adjust)
        content_list.setUniformItemSizes(True)
        content_list.setSpacing(SPACING.sm)
        content_list.setGridSize(QSize(172, 214))
        content_list.clicked.connect(lambda index: self._select_content_index(content_type, index))
        content_list.doubleClicked.connect(
            lambda index: self._activate_content_index(content_type, index)
        )
        layout.addWidget(content_list, 1)
        artwork = QLabel("Artwork unavailable")
        artwork.setObjectName("contentArtwork")
        artwork.setAlignment(Qt.AlignmentFlag.AlignCenter)
        artwork.setMinimumSize(180, 135)
        artwork.setWordWrap(True)
        detail = QLabel("No content selected")
        detail.setObjectName("contentDetail")
        detail.setWordWrap(True)
        detail.setMinimumHeight(58)
        detail_row = QHBoxLayout()
        detail_row.setSpacing(SPACING.md)
        detail_row.addWidget(artwork, 0)
        detail_row.addWidget(detail, 1)
        status = QLabel(f"No {title_text.lower()} loaded")
        status.setObjectName("pageSubtitle")
        layout.addLayout(detail_row)
        layout.addWidget(status)
        self._content_lists[content_type] = content_list
        self._content_category_selectors[content_type] = category_selector
        self._content_sort_selectors[content_type] = sort_selector
        self._content_status_labels[content_type] = status
        self._content_detail_labels[content_type] = detail
        self._content_artwork_labels[content_type] = artwork
        self._content_activate_buttons[content_type] = activate_button
        self._content_favorite_buttons[content_type] = favorite_button
        self._content_load_buttons[content_type] = load_button
        content_list.installEventFilter(self)
        return page

    def _build_library_page(
        self, title_text: str, subtitle_text: str, action: Callable[[], object]
    ) -> QWidget:
        page = QFrame()
        page.setObjectName("contentCard")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.md)
        kicker = QLabel("LIBRARY")
        kicker.setObjectName("sectionKicker")
        layout.addWidget(kicker)
        title = QLabel(title_text)
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        empty_panel = QFrame()
        empty_panel.setObjectName("emptyPanel")
        empty_layout = QVBoxLayout(empty_panel)
        empty_layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        empty = QLabel("Open this workspace to view its real saved or configured items.")
        empty.setObjectName("emptyState")
        empty.setWordWrap(True)
        empty_layout.addWidget(empty)
        open_button = QPushButton(f"Open {title_text}")
        open_button.setObjectName("primary")
        open_button.setAccessibleName(f"Open {title_text}")
        open_button.clicked.connect(action)
        empty_layout.addWidget(open_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(empty_panel)
        layout.addStretch(1)
        return page

    def _build_settings_page(self) -> QWidget:
        """Build direct settings sections without inventing unsupported configuration controls."""
        from samotech_iptv.domain.value_objects.theme_preference import ThemePreference

        page = QFrame()
        page.setObjectName("contentCard")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.md)
        kicker = QLabel("SETTINGS")
        kicker.setObjectName("sectionKicker")
        layout.addWidget(kicker)
        title = QLabel("Settings")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        subtitle = QLabel(
            "Review local settings and the available playback, diagnostics, and privacy controls."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        def add_section(title_text: str, description: str) -> QVBoxLayout:
            section = QFrame()
            section.setObjectName("emptyPanel")
            section_layout = QVBoxLayout(section)
            section_layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
            section_layout.setSpacing(SPACING.xs)
            section_title = QLabel(title_text)
            section_title.setObjectName("sectionKicker")
            section_layout.addWidget(section_title)
            section_description = QLabel(description)
            section_description.setObjectName("pageSubtitle")
            section_description.setWordWrap(True)
            section_layout.addWidget(section_description)
            layout.addWidget(section)
            return section_layout

        add_section(
            "General",
            "Provider sources, catalogues, and saved preferences remain local to this "
            "installation.",
        )
        add_section(
            "Playback",
            "Use player controls for playback, volume, audio, subtitles, aspect ratio, "
            "and fullscreen when supported by active media.",
        )
        appearance_layout = add_section(
            "Appearance",
            "Choose how SamoTech IPTV Player should follow your desktop appearance.",
        )
        selector = QComboBox()
        selector.addItem("System", ThemePreference.SYSTEM.value)
        selector.addItem("Light", ThemePreference.LIGHT.value)
        selector.addItem("Dark", ThemePreference.DARK.value)
        selector.setAccessibleName("Theme preference")
        selector.setToolTip("Choose system, light, or dark appearance")
        appearance_layout.addWidget(selector)
        save = QPushButton("Save Theme")
        save.setObjectName("primary")
        save.setAccessibleName("Save theme preference")
        save.clicked.connect(self._schedule_save_settings_theme)
        appearance_layout.addWidget(save, 0, Qt.AlignmentFlag.AlignLeft)
        status = QLabel("Theme settings load when this page opens")
        status.setObjectName("pageSubtitle")
        appearance_layout.addWidget(status)
        add_section(
            "Network",
            "Provider adapters connect directly from this device. SamoTech does not "
            "provide a stream proxy, credential relay, or CORS relay.",
        )
        add_section(
            "Diagnostics",
            "Select Info in player controls to open a safe copyable playback diagnostic "
            "report. Values that cannot be measured are shown as NOT_AVAILABLE.",
        )
        add_section(
            "Privacy",
            "Passwords, private playlist URLs, tokens, cookies, authorization headers, "
            "and MAG device identities are not shown in diagnostics or copied reports.",
        )
        layout.addStretch(1)
        self._settings_theme_selector = selector
        self._settings_status_label = status
        return page

    def open_settings_page(self) -> None:
        """Navigate directly to Settings rather than opening a routine top-level dialog."""
        self._navigate_to_page(9)

    def _schedule_save_settings_theme(self) -> None:
        if self._save_theme_preference is not None:
            create_owned_task(self, self._save_settings_theme())

    async def _load_settings_theme(self) -> None:
        selector = self._settings_theme_selector
        status = self._settings_status_label
        if selector is None or status is None:
            return
        if self._load_theme_preference is None:
            status.setText("Theme settings are unavailable in this session")
            return
        try:
            preference = await self._load_theme_preference.execute()
        except asyncio.CancelledError:
            raise
        except Exception:
            status.setText("Unable to load theme preference")
            return
        index = selector.findData(preference.value)
        if index >= 0:
            selector.setCurrentIndex(index)
        status.setText("Choose System, Light, or Dark and save")

    async def _save_settings_theme(self) -> None:
        from samotech_iptv.domain.value_objects.theme_preference import ThemePreference

        selector = self._settings_theme_selector
        status = self._settings_status_label
        if selector is None or status is None or self._save_theme_preference is None:
            return
        try:
            preference = ThemePreference(str(selector.currentData()))
            await self._save_theme_preference.execute(preference)
        except asyncio.CancelledError:
            raise
        except Exception:
            status.setText("Unable to save theme")
            return
        status.setText("Theme preference saved")

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
        if key in (Qt.Key.Key_Left, Qt.Key.Key_J):
            self._schedule_relative_seek(-10)
            event.accept()
            return
        if key in (Qt.Key.Key_Right, Qt.Key.Key_L):
            self._schedule_relative_seek(10)
            event.accept()
            return
        if key == Qt.Key.Key_M:
            self._schedule_toggle_mute()
            event.accept()
            return
        if key == Qt.Key.Key_Escape and self.window().isFullScreen():
            self.window().showNormal()
            event.accept()
            return
        super().keyPressEvent(event)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        """Handle IPTV shortcuts without triggering network work on navigation."""
        if event.type() == QEvent.Type.MouseMove:
            self._show_player_overlay()
        if isinstance(event, QKeyEvent):
            self._show_player_overlay()
            key = event.key()
            if watched is self.fullscreen_button and key == Qt.Key.Key_Space:
                return super().eventFilter(watched, event)
            if key == Qt.Key.Key_Space:
                self._toggle_play_pause()
                event.accept()
                return True
            if key == Qt.Key.Key_F:
                self._toggle_fullscreen()
                event.accept()
                return True
            if key in (Qt.Key.Key_Left, Qt.Key.Key_J):
                self._schedule_relative_seek(-10)
                event.accept()
                return True
            if key in (Qt.Key.Key_Right, Qt.Key.Key_L):
                self._schedule_relative_seek(10)
                event.accept()
                return True
            if key == Qt.Key.Key_M:
                self._schedule_toggle_mute()
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
            if watched is self.global_search_list and key in (
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
            ):
                index = self.global_search_list.currentIndex()
                if index.isValid():
                    self._activate_search_result(index)
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
        self._invalidate_non_live_requests()
        self.pages.setCurrentIndex(page_index)
        if page_index == 1:
            self._active_content_type = ContentType.LIVE
            self.search_input.setPlaceholderText("Search live channels")
            self.search_input.setAccessibleName("Live channel search")
        elif page_index == 2:
            self._activate_content_page(ContentType.MOVIE)
        elif page_index == 3:
            self._activate_content_page(ContentType.SERIES)
        elif page_index == 6:
            self._active_content_type = ContentType.LIVE
            self.search_input.setPlaceholderText("Search loaded Live, Movies, and Series")
            self.search_input.setAccessibleName("Global content search")
            self._render_global_search()
        elif page_index == 9:
            self.search_input.setPlaceholderText("Search loaded content")
            self.search_input.setAccessibleName("Content search")
            try:
                create_owned_task(self, self._load_settings_theme())
            except RuntimeError:
                pass
        else:
            self.search_input.setPlaceholderText("Search loaded content")
            self.search_input.setAccessibleName("Content search")
        label = self.navigation_model.data(
            self.navigation_model.index(index, 0), Qt.ItemDataRole.DisplayRole
        )
        self._set_status_text(f"● {label}")

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
            create_owned_task(self, self.load_content(content_type, self._begin_request()))

    async def load_content(self, content_type: ContentType, generation: int | None = None) -> None:
        """Explicitly load existing movie or series catalogues through application use cases."""
        request_generation = generation if generation is not None else self._begin_request()
        provider_id = self._provider_id()
        title = "movies" if content_type is ContentType.MOVIE else "series"
        self._content_status_labels[content_type].setText(f"Loading {title}…")
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
                self._set_status_text("● Load error")
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
            self._set_status_text("● Content unavailable")
            return
        self._content_catalogues[content_type] = tuple(response.items)
        self._render_global_search()
        await self.refresh_content_categories(content_type, provider_id, request_generation)
        if request_generation != self._request_generation or provider_id != self._provider_id():
            return
        self._render_content_catalogue(content_type)
        title = "movies" if content_type is ContentType.MOVIE else "series"
        self._content_status_labels[content_type].setText(f"{response.total:,} {title} loaded")
        self._set_status_text("● Ready")

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

    def _content_sort_changed(self, content_type: ContentType) -> None:
        """Sort the active local catalogue without issuing another provider request."""
        if self._active_content_type is content_type:
            self._render_content_catalogue(content_type)

    def _render_content_catalogue(self, content_type: ContentType) -> None:
        """Render local title, genre, and year matches from the active non-live snapshot."""
        if content_type is ContentType.SERIES and self._series_view_mode != "catalogue":
            items = (
                self._series_seasons
                if self._series_view_mode == "seasons"
                else self._series_episodes
            )
            self.content_model.replace_items(items)
            noun = "seasons" if self._series_view_mode == "seasons" else "episodes"
            self._content_status_labels[content_type].setText(
                f"{len(items):,} {noun} shown" if items else f"No {noun} available"
            )
            return
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
                            item.genre,
                            item.director,
                            item.cast,
                            item.country,
                            item.release_date,
                            item.plot,
                        ),
                    )
                ).casefold()
            )
        )
        sort_key = self._content_sort_selectors[content_type].currentData()
        if sort_key == "year_desc":
            filtered = tuple(
                sorted(
                    filtered,
                    key=lambda item: (
                        item.year is not None,
                        item.year if item.year is not None else -1,
                        item.title.casefold(),
                    ),
                    reverse=True,
                )
            )
        elif sort_key == "rating_desc":
            filtered = tuple(
                sorted(
                    filtered,
                    key=lambda item: (
                        item.rating is not None,
                        item.rating if item.rating is not None else -1.0,
                        item.title.casefold(),
                    ),
                    reverse=True,
                )
            )
        elif sort_key == "title":
            filtered = tuple(sorted(filtered, key=lambda item: item.title.casefold()))
        self.content_model.replace_items(filtered)
        title = "movies" if content_type is ContentType.MOVIE else "series"
        if filtered:
            status = f"{len(filtered):,} {title} shown"
        elif content_type not in self._content_catalogues:
            status = f"No {title} loaded"
        else:
            status = f"No {title} match"
        self._content_status_labels[content_type].setText(status)

    def _schedule_content_favorite(self, content_type: ContentType) -> None:
        """Schedule a Movie/Series favorite through the existing SQLite use case."""
        item = self.selected_content
        if item is None or item.content_type is ContentType.EPISODE:
            self._content_detail_labels[content_type].setText(
                "Episode favorites are unavailable in the current Favorite contract"
            )
            return
        create_owned_task(self, self._add_content_favorite(content_type, item))

    async def _add_content_favorite(self, content_type: ContentType, item: ContentItemDTO) -> None:
        from samotech_iptv.application.dtos import SaveFavoriteRequest

        try:
            response = await self._save_favorite.execute(
                SaveFavoriteRequest(
                    item_id=item.id,
                    item_type=item.content_type.value,
                    provider_id=item.provider_id,
                )
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            response = None
        button = self._content_favorite_buttons[content_type]
        if response is not None and response.success:
            button.setText("Favorite saved")
            self._content_detail_labels[content_type].setText(f"Favorite saved · {item.title}")
        else:
            self._content_detail_labels[content_type].setText("Unable to save favorite")

    def _select_content_index(self, content_type: ContentType, index: QModelIndex) -> None:
        """Record content selection locally without implicitly starting playback."""
        if content_type is not self._active_content_type:
            return
        row = index.row()
        if 0 <= row < self.content_model.rowCount():
            self.selected_content = self.content_model.item_at(row)
            item = self.selected_content
            self._select_content_metadata(content_type, item)

    def _activate_content_index(self, content_type: ContentType, index: QModelIndex) -> None:
        """Activate one safe non-live context through existing application use cases."""
        self._invalidate_local_subtitle_session()
        self._select_content_index(content_type, index)
        item = self.selected_content
        if item is None:
            return
        if content_type is ContentType.SERIES:
            if self._series_view_mode == "catalogue":
                action = (ContentType.SERIES, item.id, "seasons")
            elif self._series_view_mode == "seasons":
                action = (ContentType.SERIES, item.id, "episodes")
            else:
                action = (ContentType.EPISODE, item.id, "playback")
        else:
            action = (ContentType.MOVIE, item.id, "playback")
        if self._active_non_live_action == action:
            return
        self._active_non_live_action = action
        generation = self._begin_non_live_request()
        if action[2] == "seasons":
            create_owned_task(self, self._load_series_seasons_for(item, generation))
        elif action[2] == "episodes":
            create_owned_task(self, self._load_series_episodes_for(item, generation))
        elif action[0] is ContentType.MOVIE:
            create_owned_task(self, self._load_and_play_movie(item, generation))
        else:
            create_owned_task(self, self._play_content_item(item, generation))

    def _activate_current_content(self, content_type: ContentType) -> None:
        """Activate the selected item without bypassing the list-model selection boundary."""
        index = self._content_lists[content_type].currentIndex()
        if index.isValid():
            self._activate_content_index(content_type, index)

    async def _load_and_play_movie(
        self, item: ContentItemDTO, generation: int | None = None
    ) -> None:
        provider_id = item.provider_id
        action = (ContentType.MOVIE, item.id, "playback")
        if generation is None:
            self._active_non_live_action = action
        request_generation = (
            generation if generation is not None else self._begin_non_live_request()
        )
        try:
            if self._load_movie_details is None:
                if self._non_live_current(request_generation, provider_id, action):
                    self._content_detail_labels[ContentType.MOVIE].setText(
                        "Movie details are unavailable"
                    )
                return
            response = await self._load_movie_details.execute(
                LoadMovieDetailsRequest(provider_id=provider_id, movie_id=item.id)
            )
            if not self._non_live_current(request_generation, provider_id, action):
                return
            if getattr(response, "stale", False) or response.unsupported:
                self._content_detail_labels[ContentType.MOVIE].setText(
                    "Movie playback is unavailable"
                )
                return
            if response.error is not None or response.item is None:
                self._content_detail_labels[ContentType.MOVIE].setText(
                    "Unable to load movie details"
                )
                return
            self.selected_content = response.item
            self._select_content_metadata(ContentType.MOVIE, response.item)
            await self._play_content_item(response.item, request_generation)
        except asyncio.CancelledError:
            raise
        except Exception:
            if self._non_live_current(request_generation, provider_id, action):
                self._content_detail_labels[ContentType.MOVIE].setText(
                    "Unable to load movie details"
                )
        finally:
            self._finish_non_live_request(request_generation, action)

    async def _load_series_seasons_for(
        self, item: ContentItemDTO, generation: int | None = None
    ) -> None:
        provider_id = item.provider_id
        action = (ContentType.SERIES, item.id, "seasons")
        if generation is None:
            self._active_non_live_action = action
        request_generation = (
            generation if generation is not None else self._begin_non_live_request()
        )
        try:
            if self._load_series_seasons is None:
                if self._non_live_current(request_generation, provider_id, action):
                    self._content_detail_labels[ContentType.SERIES].setText(
                        "Series details are unavailable"
                    )
                return
            response = await self._load_series_seasons.execute(
                LoadSeriesSeasonsRequest(provider_id=provider_id, series_id=item.id)
            )
            if not self._non_live_current(request_generation, provider_id, action):
                return
            if getattr(response, "stale", False) or response.unsupported:
                self._content_detail_labels[ContentType.SERIES].setText(
                    "Series details are unavailable"
                )
                return
            if response.error is not None:
                self._content_detail_labels[ContentType.SERIES].setText("Unable to load seasons")
                return
            self._series_context_id = item.id
            self._series_seasons = tuple(
                ContentItemDTO(
                    id=season.id,
                    provider_id=season.provider_id,
                    content_type=ContentType.SERIES,
                    title=season.title or f"Season {season.number}",
                    series_id=season.series_id,
                    season=season.number,
                )
                for season in response.seasons
            )
            self._series_view_mode = "seasons"
            self._content_back_buttons[ContentType.SERIES].setEnabled(True)
            self._content_activate_buttons[ContentType.SERIES].setText("Open season")
            self._render_content_catalogue(ContentType.SERIES)
        except asyncio.CancelledError:
            raise
        except Exception:
            if self._non_live_current(request_generation, provider_id, action):
                self._content_detail_labels[ContentType.SERIES].setText("Unable to load seasons")
        finally:
            self._finish_non_live_request(request_generation, action)

    async def _load_series_episodes_for(
        self, item: ContentItemDTO, generation: int | None = None
    ) -> None:
        provider_id = item.provider_id
        series_id = item.series_id
        season = item.season
        action = (ContentType.SERIES, item.id, "episodes")
        if generation is None:
            self._active_non_live_action = action
        request_generation = (
            generation if generation is not None else self._begin_non_live_request()
        )
        try:
            if self._load_season_episodes is None or series_id is None or season is None:
                if self._non_live_current(request_generation, provider_id, action):
                    self._content_detail_labels[ContentType.SERIES].setText(
                        "Episodes are unavailable"
                    )
                return
            response = await self._load_season_episodes.execute(
                LoadSeasonEpisodesRequest(
                    provider_id=provider_id,
                    series_id=series_id,
                    season=season,
                )
            )
            if not self._non_live_current(request_generation, provider_id, action):
                return
            if getattr(response, "stale", False) or response.unsupported:
                self._content_detail_labels[ContentType.SERIES].setText("Episodes are unavailable")
                return
            if response.error is not None:
                self._content_detail_labels[ContentType.SERIES].setText("Unable to load episodes")
                return
            self._series_episodes = tuple(
                ContentItemDTO(
                    id=episode.id,
                    provider_id=episode.provider_id,
                    content_type=ContentType.EPISODE,
                    title=episode.title,
                    stream_id=episode.resource_id,
                    series_id=episode.series_id,
                    season=episode.season,
                    episode_number=episode.episode_number,
                    duration_seconds=episode.duration_seconds,
                    plot=episode.plot,
                )
                for episode in response.episodes
            )
            self._series_view_mode = "episodes"
            self._content_activate_buttons[ContentType.SERIES].setText("Play episode")
            self._render_content_catalogue(ContentType.SERIES)
            self._set_control_availability()
        except asyncio.CancelledError:
            raise
        except Exception:
            if self._non_live_current(request_generation, provider_id, action):
                self._content_detail_labels[ContentType.SERIES].setText("Unable to load episodes")
        finally:
            self._finish_non_live_request(request_generation, action)

    async def _play_content_item(self, item: ContentItemDTO, generation: int | None = None) -> None:
        self._invalidate_local_subtitle_session()
        provider_id = item.provider_id
        action = (
            ContentType.MOVIE if item.content_type is ContentType.MOVIE else ContentType.EPISODE,
            item.id,
            "playback",
        )
        if generation is None:
            self._active_non_live_action = action
        request_generation = (
            generation if generation is not None else self._begin_non_live_request()
        )
        try:
            if not self._non_live_current(request_generation, provider_id, action):
                return
            if item.content_type is ContentType.MOVIE:
                if not item.stream_id:
                    self._content_detail_labels[ContentType.MOVIE].setText(
                        "Movie playback is unavailable"
                    )
                    return
                target = PlaybackTarget.movie(item.provider_id, item.id, item.stream_id)
            elif item.content_type is ContentType.EPISODE:
                if (
                    not item.stream_id
                    or item.series_id is None
                    or item.season is None
                    or item.episode_number is None
                ):
                    self._content_detail_labels[ContentType.SERIES].setText(
                        "Episode playback is unavailable"
                    )
                    return
                target = PlaybackTarget.episode(
                    item.provider_id,
                    item.id,
                    item.stream_id,
                    item.series_id,
                    item.season,
                    item.episode_number,
                )
            else:
                return
            self._active_playback_content_type = item.content_type
            self._set_control_availability()
            result = await self._play_selected_channel(target)
            if not self._non_live_current(request_generation, provider_id, action):
                return
            label = (
                ContentType.MOVIE if item.content_type is ContentType.MOVIE else ContentType.SERIES
            )
            if getattr(result, "outcome", None) is PlaybackOutcome.PLAYED:
                self._content_detail_labels[label].setText(f"Playing · {item.title}")
                self._set_control_availability()
                return
            self._content_detail_labels[label].setText("Unable to start playback")
        except asyncio.CancelledError:
            raise
        except Exception:
            if self._non_live_current(request_generation, provider_id, action):
                label = (
                    ContentType.MOVIE
                    if item.content_type is ContentType.MOVIE
                    else ContentType.SERIES
                )
                self._content_detail_labels[label].setText("Unable to start playback")
        finally:
            self._finish_non_live_request(request_generation, action)

    def _back_series_navigation(self) -> None:
        """Return from episode or season context without provider calls or player mutation."""
        self._invalidate_non_live_requests()
        if self._series_view_mode == "episodes":
            self._series_view_mode = "seasons"
            self._content_activate_buttons[ContentType.SERIES].setText("Open season")
        else:
            self._clear_series_navigation()
        self._render_content_catalogue(ContentType.SERIES)

    def _clear_series_navigation(self) -> None:
        """Clear local Series detail state whenever its provider context changes."""
        self._series_view_mode = "catalogue"
        self._series_context_id = None
        self._series_seasons = ()
        self._series_episodes = ()
        back_button = self._content_back_buttons.get(ContentType.SERIES)
        if back_button is not None:
            back_button.setEnabled(False)
        activate_button = self._content_activate_buttons.get(ContentType.SERIES)
        if activate_button is not None:
            activate_button.setText("Open series")

    def _select_content_metadata(self, content_type: ContentType, item: ContentItemDTO) -> None:
        """Render a safe inline detail panel without provider calls or resolved URLs."""
        kind = item.content_type.value.title()
        identity = [kind, item.title]
        if item.content_type is ContentType.EPISODE and item.season and item.episode_number:
            identity.append(f"S{item.season:02d} E{item.episode_number:02d}")
        summary = list(
            filter(
                None,
                (
                    str(item.year) if item.year is not None else None,
                    f"★ {item.rating:g}" if item.rating is not None else None,
                    item.genre,
                    self._format_duration(item.duration_seconds),
                    item.container_extension.upper() if item.container_extension else None,
                    f"Category: {item.category_id}" if item.category_id else None,
                ),
            )
        )
        if item.season_count is not None:
            summary.append(f"{item.season_count} season(s)")
        if item.episode_count is not None:
            summary.append(f"{item.episode_count} episode(s)")
        people = list(filter(None, (item.director, item.cast, item.country, item.release_date)))
        lines = [" · ".join(identity)]
        if summary:
            lines.append(" · ".join(summary))
        if people:
            lines.append(" · ".join(people))
        if item.plot:
            lines.append(item.plot)
        if item.poster_url or item.backdrop_url:
            lines.append("Artwork available")
        self._content_detail_labels[content_type].setText("\n".join(lines))
        favorite_button = self._content_favorite_buttons[content_type]
        favorite_button.setEnabled(item.content_type in {ContentType.MOVIE, ContentType.SERIES})
        favorite_button.setText(
            "Add favorite"
            if item.content_type in {ContentType.MOVIE, ContentType.SERIES}
            else "Episode favorites unavailable"
        )
        self._schedule_artwork(content_type, item)

    def _schedule_artwork(self, content_type: ContentType, item: ContentItemDTO) -> None:
        """Load one selected item's artwork without allowing stale UI mutation."""
        self._artwork_generation += 1
        generation = self._artwork_generation
        label = self._content_artwork_labels[content_type]
        artwork_url = item.backdrop_url or item.poster_url
        if artwork_url is None:
            self._set_artwork_placeholder(label, "Artwork unavailable")
            return
        if self._artwork_loader is None:
            self._set_artwork_placeholder(label, "Artwork preview unavailable")
            return
        role = ArtworkRole.BACKDROP if item.backdrop_url else ArtworkRole.POSTER
        self._set_artwork_placeholder(label, "Loading artwork…")
        create_owned_task(
            self,
            self._load_artwork(
                content_type,
                item,
                ArtworkRequest(item.provider_id, item.id, role, artwork_url),
                generation,
            ),
        )

    async def _load_artwork(
        self,
        content_type: ContentType,
        item: ContentItemDTO,
        request: ArtworkRequest,
        generation: int,
    ) -> None:
        loader = self._artwork_loader
        if loader is None:
            return
        try:
            payload = await loader.load(request)
        except asyncio.CancelledError:
            raise
        except Exception:
            payload = None
        if generation != self._artwork_generation or self.selected_content != item:
            return
        label = self._content_artwork_labels[content_type]
        if payload is None:
            self._set_artwork_placeholder(label, "Artwork unavailable")
            return
        image = QImage()
        if not image.loadFromData(payload):
            self._set_artwork_placeholder(label, "Artwork unavailable")
            return
        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            self._set_artwork_placeholder(label, "Artwork unavailable")
            return
        target_size = label.size().expandedTo(QSize(180, 135))
        label.setPixmap(
            pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        label.setText("")

    def _set_artwork_placeholder(self, label: QLabel, text: str) -> None:
        """Render a deterministic placeholder without retaining image bytes in the UI."""
        label.clear()
        label.setText(text)

    def _clear_artwork_labels(self) -> None:
        """Reset every non-live artwork surface when provider context is cleared."""
        for label in self._content_artwork_labels.values():
            self._set_artwork_placeholder(label, "Artwork unavailable")

    @staticmethod
    def _format_duration(duration_seconds: int | None) -> str | None:
        """Format optional duration without inventing a value for missing provider data."""
        if duration_seconds is None or duration_seconds < 0:
            return None
        minutes, seconds = divmod(duration_seconds, 60)
        if minutes >= 60:
            hours, minutes = divmod(minutes, 60)
            return f"{hours}h {minutes:02d}m"
        return f"{minutes}m {seconds:02d}s"

    @property
    def _is_seekable_mode(self) -> bool:
        return self._active_playback_content_type in {
            ContentType.MOVIE,
            ContentType.EPISODE,
        }

    @staticmethod
    def _format_playback_time(position_ms: int | None) -> str:
        if position_ms is None or position_ms < 0:
            return "--:--"
        total_seconds = position_ms // 1_000
        hours, remainder = divmod(total_seconds, 3_600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def _set_control_availability(self) -> None:
        """Keep controls honest: live inputs never expose VOD seek or restart actions."""
        has_player = self._player_port is not None
        seekable = has_player and self._is_seekable_mode
        for button in (
            self.back_30_button,
            self.back_10_button,
            self.forward_10_button,
            self.forward_30_button,
            self.restart_button,
            self.seek_slider,
        ):
            button.setEnabled(seekable)
        episode_index = self._current_episode_index()
        self.previous_episode_button.setEnabled(
            seekable and episode_index is not None and episode_index > 0
        )
        self.next_episode_button.setEnabled(
            seekable
            and episode_index is not None
            and episode_index + 1 < len(self._series_episodes)
        )
        self.retry_button.setEnabled(self.playback_error_channel is not None)
        self.audio_button.setEnabled(has_player)
        self.subtitle_button.setEnabled(has_player)
        self.aspect_button.setEnabled(has_player)
        self.info_button.setEnabled(has_player)
        self.volume_slider.setEnabled(has_player)
        self.mute_button.setEnabled(has_player)
        if not seekable:
            self.seek_slider.blockSignals(True)
            self.seek_slider.setValue(0)
            self.seek_slider.blockSignals(False)
            self.elapsed_label.setText(
                "LIVE" if self._active_playback_content_type is ContentType.LIVE else "--:--"
            )
            self.duration_label.setText(
                "LIVE" if self._active_playback_content_type is ContentType.LIVE else "--:--"
            )

    def _schedule_progress_poll(self) -> None:
        if self._player_port is None or self._control_poll_pending or self._disposed:
            return
        self._control_poll_pending = True
        create_owned_task(self, self._poll_playback_progress())

    async def _poll_playback_progress(self) -> None:
        try:
            if self._player_port is None:
                return
            position_ms, duration_ms, volume, muted = await asyncio.gather(
                self._player_port.get_position_ms(),
                self._player_port.get_duration_ms(),
                self._player_port.get_volume(),
                self._player_port.is_muted(),
            )
            self._render_backend_state()
            if (
                self._is_seekable_mode
                and duration_ms
                and duration_ms > 0
                and position_ms is not None
            ):
                fraction = max(0.0, min(1.0, position_ms / duration_ms))
                self.seek_slider.blockSignals(True)
                self.seek_slider.setValue(round(fraction * self.seek_slider.maximum()))
                self.seek_slider.blockSignals(False)
                self.elapsed_label.setText(self._format_playback_time(position_ms))
                self.duration_label.setText(self._format_playback_time(duration_ms))
            elif self._active_playback_content_type is ContentType.LIVE:
                self.elapsed_label.setText("LIVE")
                self.duration_label.setText("LIVE")
            if self._is_seekable_mode and position_ms is not None and duration_ms is not None:
                self._schedule_progress_persist(position_ms, duration_ms)
            if volume is not None and not self.volume_slider.isSliderDown():
                self.volume_slider.blockSignals(True)
                self.volume_slider.setValue(max(0, min(100, volume)))
                self.volume_slider.blockSignals(False)
            if muted is not None:
                self.mute_button.setText("Unmute" if muted else "Mute")
        except asyncio.CancelledError:
            raise
        except Exception:
            # Poll failures are transient and must not surface backend details or URLs.
            return
        finally:
            self._control_poll_pending = False

    def _schedule_progress_persist(self, position_ms: int, duration_ms: int) -> None:
        if self._progress_recorder is None or self.selected_content is None:
            return
        if self._active_playback_content_type not in {ContentType.MOVIE, ContentType.EPISODE}:
            return
        position_seconds = max(0, position_ms // 1_000)
        duration_seconds = max(0, duration_ms // 1_000)
        identity = f"{self.selected_content.provider_id}:{self.selected_content.id}"
        previous = self._last_persisted_progress
        if previous is not None and previous[0] == identity:
            if abs(position_seconds - previous[1]) < 5 and position_seconds < duration_seconds:
                return
        self._last_persisted_progress = (identity, position_seconds, duration_seconds)
        create_owned_task(
            self,
            self._persist_progress(
                provider_id=self.selected_content.provider_id,
                item_id=self.selected_content.id,
                item_type=(
                    "movie"
                    if self._active_playback_content_type is ContentType.MOVIE
                    else "episode"
                ),
                position_seconds=position_seconds,
                duration_seconds=duration_seconds,
            ),
        )

    async def _persist_progress(
        self,
        *,
        provider_id: str,
        item_id: str,
        item_type: str,
        position_seconds: int,
        duration_seconds: int,
    ) -> None:
        if self._progress_recorder is None:
            return
        try:
            from samotech_iptv.application.dtos import RecordHistoryRequest

            await self._progress_recorder.execute(
                RecordHistoryRequest(
                    provider_id=provider_id,
                    item_id=item_id,
                    item_type=item_type,
                    duration_seconds=duration_seconds,
                    position_seconds=position_seconds,
                    completed=duration_seconds > 0 and position_seconds >= duration_seconds,
                )
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            # Persistence failures are non-fatal and never disclose backend details.
            return

    def _preview_seek_position(self, slider_value: int) -> None:
        if self._is_seekable_mode:
            duration = self.duration_label.text()
            if duration not in {"--:--", "LIVE"}:
                self.elapsed_label.setToolTip(f"Preview position {slider_value / 10:.1f}%")

    def _commit_seek_position(self) -> None:
        if self._player_port is not None and self._is_seekable_mode:
            fraction = self.seek_slider.value() / self.seek_slider.maximum()
            create_owned_task(self, self._seek_fraction(fraction))

    async def _seek_fraction(self, fraction: float) -> None:
        if self._player_port is None or not self._is_seekable_mode:
            return
        try:
            await self._player_port.seek_fraction(fraction)
            self._set_status_text("● Seeking")
        except asyncio.CancelledError:
            raise
        except Exception:
            self._set_status_text("● Seek unavailable")

    def _schedule_relative_seek(self, seconds: int) -> None:
        if self._player_port is not None and self._is_seekable_mode:
            create_owned_task(self, self._seek_relative(seconds))

    async def _seek_relative(self, seconds: int) -> None:
        if self._player_port is None or not self._is_seekable_mode:
            return
        try:
            position_ms = await self._player_port.get_position_ms()
            duration_ms = await self._player_port.get_duration_ms()
            if position_ms is None:
                raise RuntimeError("position unavailable")
            target = max(0, position_ms + seconds * 1_000)
            if duration_ms is not None:
                target = min(target, max(0, duration_ms))
            await self._player_port.seek_ms(target)
            self._set_status_text("● Playing")
        except asyncio.CancelledError:
            raise
        except Exception:
            self._set_status_text("● Seek unavailable")

    def _schedule_volume_change(self, volume: int) -> None:
        if self._player_port is not None:
            create_owned_task(self, self._set_volume(volume))

    async def _set_volume(self, volume: int) -> None:
        if self._player_port is None:
            return
        try:
            await self._player_port.set_volume(volume)
        except asyncio.CancelledError:
            raise
        except Exception:
            self._set_status_text("● Volume unavailable")

    def _schedule_toggle_mute(self) -> None:
        if self._player_port is not None:
            create_owned_task(self, self._toggle_mute())

    async def _toggle_mute(self) -> None:
        if self._player_port is None:
            return
        try:
            muted = await self._player_port.is_muted()
            if muted is None:
                raise RuntimeError("mute unavailable")
            await self._player_port.set_muted(not muted)
            self.mute_button.setText("Mute" if muted else "Unmute")
        except asyncio.CancelledError:
            raise
        except Exception:
            self._set_status_text("● Mute unavailable")

    def _current_episode_index(self) -> int | None:
        """Return the selected episode index only within the active provider-scoped list."""
        if (
            self.selected_content is None
            or self.selected_content.content_type is not ContentType.EPISODE
        ):
            return None
        for index, episode in enumerate(self._series_episodes):
            if (
                episode.id == self.selected_content.id
                and episode.provider_id == self.selected_content.provider_id
            ):
                return index
        return None

    def _schedule_adjacent_episode(self, offset: int) -> None:
        """Schedule a proven adjacent episode through the normal guarded playback path."""
        if offset not in {-1, 1}:
            return
        current_index = self._current_episode_index()
        if current_index is None:
            return
        target_index = current_index + offset
        if not 0 <= target_index < len(self._series_episodes):
            return
        target = self._series_episodes[target_index]
        self.selected_content = target
        self._select_content_metadata(ContentType.SERIES, target)
        self._active_non_live_action = (ContentType.EPISODE, target.id, "playback")
        generation = self._begin_non_live_request()
        create_owned_task(self, self._play_content_item(target, generation))
        self._set_control_availability()

    def _schedule_restart(self) -> None:
        if self._player_port is not None and self._is_seekable_mode:
            create_owned_task(self, self._restart_playback())

    def _schedule_retry_playback(self) -> None:
        """Retry only the last failed typed Live-TV target through the existing path."""
        channel = self.playback_error_channel
        if channel is not None:
            create_owned_task(self, self.play_channel(channel))

    async def _restart_playback(self) -> None:
        if self._player_port is None or not self._is_seekable_mode:
            return
        try:
            await self._player_port.restart()
            self._set_status_text("● Restarted")
        except asyncio.CancelledError:
            raise
        except Exception:
            self._set_status_text("● Restart unavailable")

    def _schedule_audio_menu(self) -> None:
        if self._player_port is not None:
            create_owned_task(self, self._show_audio_menu())

    async def _show_audio_menu(self) -> None:
        if self._player_port is None:
            return
        menu = QMenu(self)
        try:
            tracks = await self._player_port.get_audio_tracks()
        except asyncio.CancelledError:
            raise
        except Exception:
            action = menu.addAction("Audio tracks unavailable")
            action.setEnabled(False)
            menu.popup(self.audio_button.mapToGlobal(self.audio_button.rect().bottomLeft()))
            return
        if not tracks:
            action = menu.addAction("No native audio tracks")
            action.setEnabled(False)
        for track in tracks:
            label = track.description or f"Track {track.id}"
            if track.active:
                label += " ✓"
            action = menu.addAction(label)
            action.triggered.connect(
                lambda _checked=False, selected_id=track.id: create_owned_task(
                    self, self._select_audio_track(selected_id)
                )
            )
        menu.popup(self.audio_button.mapToGlobal(self.audio_button.rect().bottomLeft()))

    async def _select_audio_track(self, track_id: int) -> None:
        if self._player_port is None:
            return
        try:
            await self._player_port.select_audio_track(track_id)
            self._set_status_text("● Audio track changed")
        except asyncio.CancelledError:
            raise
        except Exception:
            self._set_status_text("● Audio track unavailable")

    def _schedule_subtitle_menu(self) -> None:
        if self._player_port is not None:
            create_owned_task(self, self._show_subtitle_menu())

    def _choose_local_subtitle(self) -> None:
        """Open a local-only picker and schedule validation/attachment off the UI path."""
        if self._player_port is None or not self._is_seekable_mode:
            self._set_status_text("● Local subtitles require a movie or episode")
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Local Subtitle",
            "",
            "Subtitles (*.srt *.ass *.ssa *.vtt)",
        )
        if path:
            create_owned_task(self, self._load_local_subtitle(path))

    async def _load_local_subtitle(self, path: str) -> None:
        """Validate and attach one local subtitle only to the current playback session."""
        if self._player_port is None or not self._is_seekable_mode:
            return
        token = self._subtitle_session_token
        expected_generation = getattr(self._player_port, "media_generation", None)
        try:
            subtitle = await asyncio.to_thread(inspect_local_subtitle, path)
            if token != self._subtitle_session_token or not self._is_seekable_mode:
                return
            attach = getattr(self._player_port, "attach_local_subtitle", None)
            if not callable(attach):
                raise RuntimeError("Local subtitle attachment is unavailable")
            await attach(subtitle.path, expected_generation=expected_generation)
            if token != self._subtitle_session_token:
                return
            self._local_subtitle_file = subtitle
            self._set_status_text(f"● Local subtitle attached · {subtitle.display_name}")
        except asyncio.CancelledError:
            raise
        except (LocalSubtitleError, ValueError, RuntimeError):
            if token == self._subtitle_session_token:
                self._set_status_text("● Local subtitle unavailable")

    def _remove_local_subtitle(self) -> None:
        """Remove local subtitle slaves without changing embedded/provider track selection."""
        self._local_subtitle_file = None
        if self._player_port is not None:
            create_owned_task(self, self._clear_local_subtitles())

    async def _clear_local_subtitles(self) -> None:
        if self._player_port is None:
            return
        try:
            await self._player_port.clear_local_subtitles()
            self._set_status_text("● Local subtitles removed")
        except asyncio.CancelledError:
            raise
        except Exception:
            self._set_status_text("● Local subtitle removal unavailable")

    async def _show_subtitle_menu(self) -> None:
        if self._player_port is None:
            return
        menu = QMenu(self)
        local_action = menu.addAction("Load local subtitle…")
        local_supported = bool(
            getattr(getattr(self._player_port, "capabilities", None), "local_subtitles", False)
        )
        local_action.setEnabled(local_supported and self._is_seekable_mode)
        local_action.triggered.connect(lambda: self._choose_local_subtitle())
        if self._local_subtitle_file is not None:
            remove_action = menu.addAction(
                f"Remove local · {self._local_subtitle_file.display_name}"
            )
            remove_action.triggered.connect(lambda: self._remove_local_subtitle())
        capabilities = getattr(self._player_port, "capabilities", None)
        if getattr(capabilities, "subtitle_delay", False):
            delay_menu = menu.addMenu("Subtitle delay")
            for delay_ms in (-5_000, -1_000, 0, 1_000, 5_000):
                label = "0 ms" if delay_ms == 0 else f"{delay_ms:+d} ms"
                action = delay_menu.addAction(label)
                action.triggered.connect(
                    lambda _checked=False, selected_delay=delay_ms: create_owned_task(
                        self, self._set_subtitle_delay(selected_delay)
                    )
                )
        menu.addSeparator()
        off_action = menu.addAction("Subtitles off")
        off_action.triggered.connect(
            lambda _checked=False: create_owned_task(self, self._select_subtitle_track(None))
        )
        menu.addSeparator()
        try:
            tracks = await self._player_port.get_subtitle_tracks()
        except asyncio.CancelledError:
            raise
        except Exception:
            action = menu.addAction("Subtitle tracks unavailable")
            action.setEnabled(False)
            menu.popup(self.subtitle_button.mapToGlobal(self.subtitle_button.rect().bottomLeft()))
            return
        if not tracks:
            action = menu.addAction("No native subtitle tracks")
            action.setEnabled(False)
        for track in tracks:
            label = track.description or f"Track {track.id}"
            if track.active:
                label += " ✓"
            action = menu.addAction(label)
            action.triggered.connect(
                lambda _checked=False, selected_id=track.id: create_owned_task(
                    self, self._select_subtitle_track(selected_id)
                )
            )
        menu.popup(self.subtitle_button.mapToGlobal(self.subtitle_button.rect().bottomLeft()))

    async def _select_subtitle_track(self, track_id: int | None) -> None:
        if self._player_port is None:
            return
        try:
            await self._player_port.select_subtitle_track(track_id)
            self._set_status_text("● Subtitles changed")
        except asyncio.CancelledError:
            raise
        except Exception:
            self._set_status_text("● Subtitle track unavailable")

    async def _set_subtitle_delay(self, delay_ms: int) -> None:
        if self._player_port is None:
            return
        try:
            await self._player_port.set_subtitle_delay_ms(delay_ms)
            self._set_status_text(f"● Subtitle delay {delay_ms:+d} ms")
        except asyncio.CancelledError:
            raise
        except Exception:
            self._set_status_text("● Subtitle delay unavailable")

    def _show_aspect_menu(self) -> None:
        menu = QMenu(self)
        for label, value in (
            ("Default", None),
            ("1:1", "1:1"),
            ("4:3", "4:3"),
            ("5:4", "5:4"),
            ("16:9", "16:9"),
            ("16:10", "16:10"),
            ("221:100", "221:100"),
            ("4:5", "4:5"),
        ):
            action = menu.addAction(label)
            action.triggered.connect(
                lambda _checked=False, selected=value: create_owned_task(
                    self, self._set_aspect_ratio(selected)
                )
            )
        menu.popup(self.aspect_button.mapToGlobal(self.aspect_button.rect().bottomLeft()))

    async def _set_aspect_ratio(self, aspect_ratio: str | None) -> None:
        if self._player_port is None:
            return
        try:
            await self._player_port.set_aspect_ratio(aspect_ratio)
            self._set_status_text("● Aspect ratio changed")
        except asyncio.CancelledError:
            raise
        except Exception:
            self._set_status_text("● Aspect ratio unavailable")

    def _render_backend_state(self) -> None:
        """Render only the typed public player state; never expose native details."""
        if self._player_port is None:
            return
        state = getattr(self._player_port, "state", None)
        state_value = str(getattr(state, "value", "") or "").casefold()
        labels = {
            "loading": "● Loading",
            "buffering": "● Buffering",
            "recovering": "● Reconnecting",
            "playing": "● Playing",
            "paused": "● Paused",
            "stopping": "● Stopping",
            "stopped": "● Stopped",
            "ended": "● Ended",
            "error": "● Playback error",
        }
        label = labels.get(state_value)
        if label is not None:
            self._set_status_text(label)

    def _show_playback_info(self) -> None:
        """Open a user-copyable safe diagnostic panel through the existing owned-task lifecycle."""
        if self._player_port is None:
            return
        create_owned_task(self, self._open_playback_diagnostics())

    def show_playback_diagnostics(self) -> None:
        """Open the existing safe diagnostic panel from external presentation actions."""
        self._show_playback_info()

    async def _open_playback_diagnostics(self) -> None:
        """Build a sanitized runtime report and show it in an application-owned dialog."""
        if self._player_port is None:
            return
        try:
            diagnostics = await self._player_port.get_diagnostics()
        except asyncio.CancelledError:
            raise
        except Exception:
            self._set_status_text("● Playback diagnostics unavailable")
            return
        from samotech_iptv.presentation.dialogs.playback_diagnostics_dialog import (
            PlaybackDiagnosticsDialog,
        )

        provider_id = self._provider_id()
        context = PlaybackDiagnosticContext(
            application_version=APP_VERSION,
            platform=platform.platform(),
            provider_type=self._provider_types.get(provider_id),
            content_type=(
                self._active_playback_content_type.value
                if self._active_playback_content_type is not None
                else None
            ),
        )
        dialog = PlaybackDiagnosticsDialog(
            format_playback_diagnostic_report(context, diagnostics),
            self.window(),
        )
        dialog.show()
        self._active_playback_diagnostics_dialog = dialog
        self._set_status_text("● Playback diagnostics ready")

    def _set_status_text(self, text: str) -> None:
        """Update the shell status and the visible player overlay together."""
        self.status_label.setText(text)
        if hasattr(self, "overlay_status"):
            self.overlay_status.setText(text)

    def _invalidate_local_subtitle_session(self) -> None:
        """Invalidate local subtitle work whenever provider or media identity changes."""
        self._subtitle_session_token += 1
        self._local_subtitle_file = None

    def _begin_non_live_request(self) -> int:
        self._non_live_generation += 1
        return self._non_live_generation

    def _invalidate_non_live_requests(self) -> None:
        self._non_live_generation += 1
        self._active_non_live_action = None

    def _non_live_current(
        self,
        generation: int,
        provider_id: str,
        action: tuple[ContentType, str, str],
    ) -> bool:
        return (
            not self._disposed
            and generation == self._non_live_generation
            and provider_id == self._provider_id()
            and action == self._active_non_live_action
        )

    def _finish_non_live_request(
        self, generation: int, action: tuple[ContentType, str, str]
    ) -> None:
        if generation == self._non_live_generation and action == self._active_non_live_action:
            self._active_non_live_action = None

    def _begin_request(self) -> int:
        self._request_generation += 1
        self._set_loading(True)
        return self._request_generation

    def _set_loading(self, loading: bool) -> None:
        self._loading = loading
        for button in (
            self.load_button,
            self.search_button,
            self.favorite_button,
            *self._content_load_buttons.values(),
        ):
            button.setEnabled(not loading)
        if loading:
            self.channel_status.setText("Loading…")
            self._set_status_text("● Loading")

    def _schedule_load(self) -> None:
        if not self._loading:
            create_owned_task(self, self.load_channels(self._begin_request()))

    def _schedule_search(self) -> None:
        if not self._loading:
            if self._active_content_type is not ContentType.LIVE:
                self._render_content_catalogue(self._active_content_type)
                self._set_status_text("● Ready")
                return
            create_owned_task(self, self.search_channels(self._begin_request()))

    def _schedule_add_favorite(self) -> None:
        row = self.channel_list.currentIndex().row()
        if 0 <= row < self.channel_model.rowCount():
            channel = self.channel_model.channel_at(row)
            create_owned_task(self, self.add_favorite(channel))

    def _schedule_selected_channel(self, index: QModelIndex) -> None:
        row = index.row()
        if 0 <= row < self.channel_model.rowCount():
            channel = self.channel_model.channel_at(row)
            create_owned_task(self, self.play_channel(channel))

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
                self._set_status_text("● Load error")
            return
        finally:
            if request_generation == self._request_generation:
                self._set_loading(False)
        if request_generation != self._request_generation:
            return
        if response.error is not None:
            self._render_channels(())
            self.channel_status.setText("Unable to load channels")
            self._set_status_text("● Load error")
            return
        self._catalogue_channels = tuple(response.channels)
        self._search_channels_result = None
        self._render_global_search()
        self._render_active_catalogue()
        if self.selected_channel is None and response.channels:
            self.selected_channel = response.channels[0]
            self._update_channel_context()
        self.channel_status.setText(
            f"{response.total:,} channels loaded" if response.total else "No channels found"
        )
        self._set_status_text("● Ready")

    async def search_channels(self, generation: int | None = None) -> None:
        request_generation = generation if generation is not None else self._begin_request()
        query = self.search_input.text().strip()
        if not query and self._catalogue_channels:
            if request_generation == self._request_generation:
                self._search_channels_result = None
                self._render_active_catalogue()
                self.channel_status.setText(f"{self.channel_model.rowCount():,} channels loaded")
                self._set_status_text("● Ready")
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
                self._set_status_text("● Search error")
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
        self._set_status_text("● Ready")

    async def add_favorite(self, channel: ChannelDTO) -> None:
        from samotech_iptv.application.dtos import SaveFavoriteRequest

        try:
            response = await self._save_favorite.execute(
                SaveFavoriteRequest(
                    item_id=channel.id,
                    item_type="channel",
                    provider_id=channel.provider_id,
                )
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
        self._invalidate_local_subtitle_session()
        request_generation = self._request_generation
        provider_id = channel.provider_id
        self.selected_channel = channel
        self._active_playback_content_type = ContentType.LIVE
        self._set_control_availability()
        self.loading_channel = channel
        self.playback_error_channel = None
        self._update_channel_context()
        self._set_status_text("● Loading playback")
        try:
            result = await self._play_selected_channel(
                PlaybackTarget.live(channel.provider_id, channel.id, channel.stream_id)
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            if request_generation != self._request_generation or provider_id != self._provider_id():
                return
            self.loading_channel = None
            self.playback_error_channel = channel
            self._update_channel_context()
            self.channel_status.setText(
                playback_failure_message(PlaybackOutcome.FAILED, "playback exception")
            )
            self._set_status_text("● Playback error")
            self._set_control_availability()
            return
        if getattr(result, "outcome", None) is PlaybackOutcome.STALE:
            return
        if getattr(result, "outcome", None) in {
            PlaybackOutcome.FAILED,
            PlaybackOutcome.UNSUPPORTED,
        }:
            self.loading_channel = None
            self.playback_error_channel = channel
            self._update_channel_context()
            self.channel_status.setText(
                playback_failure_message(
                    getattr(result, "outcome", PlaybackOutcome.FAILED),
                    getattr(result, "error", None),
                )
            )
            self._set_status_text("● Playback error")
            self._set_control_availability()
            return
        if request_generation != self._request_generation or provider_id != self._provider_id():
            return
        self.loading_channel = None
        self.playback_error_channel = None
        self.playing_channel = channel
        self._active_playback_content_type = ContentType.LIVE
        self._set_control_availability()
        self._update_channel_context()
        self._set_status_text("● Playing")

    def _render_channels(self, channels: Sequence[ChannelDTO]) -> None:
        self._channels = list(channels)
        self.channel_model.replace_channels(self._channels)

    def closeEvent(self, event: object) -> None:  # noqa: N802
        """Invalidate non-live completions before the Qt owner is disposed."""
        self._disposed = True
        self._invalidate_local_subtitle_session()
        self._overlay_timer.stop()
        self._progress_timer.stop()
        self._invalidate_non_live_requests()
        cancel_owned_tasks(self)
        super().closeEvent(event)  # type: ignore[arg-type]

    def _toggle_play_pause(self) -> None:
        """Toggle only the pause/resume capabilities exposed by PlayerPort."""
        if self.status_label.text().endswith("Paused"):
            create_owned_task(self, self._resume_playback())
            self._set_status_text("● Playing")
            if self.overlay_status is not None:
                self.overlay_status.setText("● Playing")
        else:
            create_owned_task(self, self._pause_playback())
            self._set_status_text("● Paused")
            if self.overlay_status is not None:
                self.overlay_status.setText("● Paused")

    def _toggle_fullscreen(self) -> None:
        """Toggle real window fullscreen without changing the native VLC lifecycle."""
        window = self.window()
        if window.isFullScreen():
            window.showNormal()
            self.fullscreen_button.setText("Fullscreen")
        else:
            window.showFullScreen()
            self.fullscreen_button.setText("Exit fullscreen")
        self._show_player_overlay()
        self.fullscreen_button.setFocus(Qt.FocusReason.OtherFocusReason)
