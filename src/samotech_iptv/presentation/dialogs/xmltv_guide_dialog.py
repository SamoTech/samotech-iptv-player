"""Qt dialog for local XMLTV source configuration and manual guide refresh."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)

from samotech_iptv.application.dtos import (
    ConfigureXMLTVBindingRequest,
    RefreshXMLTVGuideRequest,
    XMLTVChannelMappingRequest,
)
from samotech_iptv.presentation.task_owner import create_owned_task
from samotech_iptv.presentation.theme.dialogs import apply_form_dialog_style

if TYPE_CHECKING:
    from samotech_iptv.application.use_cases.configure_xmltv_binding import ConfigureXMLTVBinding
    from samotech_iptv.application.use_cases.refresh_xmltv_guide import RefreshXMLTVGuide

__all__ = ["XMLTVGuideDialog"]

_CONFIGURE_ERROR = "Unable to save XMLTV guide configuration"
_REFRESH_ERROR = "Unable to refresh XMLTV guide"


class XMLTVGuideDialog(QDialog):
    """Configure a local XMLTV binding and render bounded, non-secret schedule rows."""

    def __init__(
        self,
        configure_binding: ConfigureXMLTVBinding,
        refresh_guide: RefreshXMLTVGuide,
    ) -> None:
        super().__init__()
        self._configure_binding = configure_binding
        self._refresh_guide = refresh_guide
        self.setWindowTitle("XMLTV Guide")
        self.provider_id_input = QLineEdit()
        self.source_input = QLineEdit()
        self.mapping_input = QLineEdit()
        self.mapping_input.setPlaceholderText("source-channel=canonical-channel, ...")
        self.configure_button = QPushButton("Save Local XMLTV Configuration")
        self.configure_button.setObjectName("primary")
        self.configure_button.setAccessibleName("Save local XMLTV configuration")
        self.configure_button.clicked.connect(self._schedule_configure)
        self.refresh_button = QPushButton("Refresh Guide")
        self.refresh_button.setAccessibleName("Refresh local XMLTV guide")
        self.refresh_button.clicked.connect(self._schedule_refresh)
        self.status_label = QLabel()
        self.entries_list = QListWidget()

        form = QFormLayout()
        form.addRow("Provider ID", self.provider_id_input)
        form.addRow("Local XMLTV file", self.source_input)
        form.addRow("Channel mappings", self.mapping_input)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.configure_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.entries_list)
        apply_form_dialog_style(self)

    async def configure(self) -> None:
        """Persist one explicit local XMLTV source binding with generic feedback."""
        request = self._configuration_request()
        if request is None:
            self.status_label.setText(_CONFIGURE_ERROR)
            return
        response = await self._configure_binding.execute(request)
        self.status_label.setText(
            "Local XMLTV guide configuration saved" if response.success else _CONFIGURE_ERROR
        )

    async def refresh(self) -> None:
        """Refresh the configured source and display only safe schedule details."""
        self.entries_list.clear()
        response = await self._refresh_guide.execute(
            RefreshXMLTVGuideRequest(provider_id=self.provider_id_input.text().strip())
        )
        if response.error is not None:
            self.status_label.setText(_REFRESH_ERROR)
            return
        for entry in response.entries:
            self.entries_list.addItem(f"{entry.start} — {entry.end} — {entry.title}")
        self.status_label.setText(
            "No XMLTV entries found"
            if not response.entries
            else f"Loaded {len(response.entries)} entries"
        )

    def _configuration_request(self) -> ConfigureXMLTVBindingRequest | None:
        mappings: list[XMLTVChannelMappingRequest] = []
        for raw_mapping in self.mapping_input.text().split(","):
            source_channel_id, separator, channel_id = raw_mapping.partition("=")
            if not separator or not source_channel_id.strip() or not channel_id.strip():
                return None
            mappings.append(
                XMLTVChannelMappingRequest(
                    source_channel_id=source_channel_id.strip(),
                    channel_id=channel_id.strip(),
                )
            )
        provider_id = self.provider_id_input.text().strip()
        source = self.source_input.text().strip()
        if not provider_id or not source or not mappings:
            return None
        return ConfigureXMLTVBindingRequest(
            provider_id=provider_id,
            source=source,
            mappings=tuple(mappings),
        )

    def _schedule_configure(self) -> None:
        """Queue configuration on the Qt-aware event loop."""

        create_owned_task(self, self.configure())

    def _schedule_refresh(self) -> None:
        """Queue manual refresh on the Qt-aware event loop."""

        create_owned_task(self, self.refresh())
