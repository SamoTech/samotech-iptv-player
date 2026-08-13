"""
MAGProvider — top-level facade registered as "mag".
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from ..base.errors import AuthError
from ..base.provider import BaseProvider
from ..registry import register
from .catalogue import MAGCatalogue
from .connection import MAGConnection
from .constants import DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT_S
from .credentials import MAGCredentials
from .discovery import MAGProtocolDiscovery
from .profile import MAGProfile
from .protocol_profile import (
    LegacyMAGProtocolProfile,
    MAGProtocolProfile,
    StalkerQueryProtocolProfile,
)
from .session import MAGSession
from .stream import MAGStream

log = logging.getLogger(__name__)


@register("mag")
class MAGProvider(BaseProvider):
    """
    Stalker / MAG middleware provider.

    Required config keys
    --------------------
    portal_url : str
    mac_address : str

    Optional config keys
    --------------------
    serial_number, device_id, device_id2 : str
    timeout_s : float          (default 30)
    max_retries : int          (default 3)
    dev_mode : bool            (default False)
    use_keyring : bool         (default False)
    protocol_profile : str     (`legacy`, `stalker_query`, or bounded `auto`)
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)

        if config.get("use_keyring"):
            creds = MAGCredentials.from_keyring(config["portal_url"])
        else:
            creds = MAGCredentials(
                portal_url=config["portal_url"],
                mac_address=config["mac_address"],
                serial_number=config.get("serial_number", ""),
                device_id=config.get("device_id", ""),
                device_id2=config.get("device_id2", ""),
            )

        self._connection = MAGConnection(
            portal_url=config["portal_url"],
            timeout_s=float(config.get("timeout_s", DEFAULT_TIMEOUT_S)),
            max_retries=int(config.get("max_retries", DEFAULT_MAX_RETRIES)),
            dev_mode=bool(config.get("dev_mode", False)),
        )
        profile_name = str(config.get("protocol_profile", "legacy")).casefold()
        protocol_profile: MAGProtocolProfile
        self._auto_discover = profile_name == "auto"
        if profile_name in {"legacy", "auto"}:
            protocol_profile = LegacyMAGProtocolProfile()
        elif profile_name == "stalker_query":
            protocol_profile = StalkerQueryProtocolProfile()
        else:
            raise ValueError(f"Unsupported MAG protocol profile: {profile_name!r}")
        self._session = MAGSession(self._connection, creds, profile=protocol_profile)
        self._profile_mgr = MAGProfile(self._connection, self._session)
        self._catalogue = MAGCatalogue(self._connection, self._session)
        self._stream = MAGStream(self._connection, self._session)

    async def connect(self) -> None:
        """Open a reusable session, releasing it if discovery or authentication fails."""
        await self._connection.open()
        try:
            if self._auto_discover:
                results, profile = await MAGProtocolDiscovery(
                    self._connection, self._session.credentials
                ).discover()
                for result in results:
                    log.info(
                        "[IPTV] PROVIDER=MAG OPERATION=DISCOVERY CANDIDATE=%s "
                        "HTTP_STATUS=%s CONTENT_TYPE=%s RESPONSE_BYTES=%s JSON=%s "
                        "TOKEN_PRESENT=%s CLASSIFICATION=%s ELAPSED=%.3fs",
                        result.candidate_name,
                        result.status if result.status is not None else "<none>",
                        result.content_type or "<missing>",
                        result.response_size if result.response_size is not None else "<none>",
                        result.is_json,
                        result.token_present,
                        result.classification,
                        result.elapsed_seconds,
                    )
                if profile is None:
                    raise AuthError("MAG protocol discovery did not establish a valid handshake")
                self._session.select_profile(profile)
            await self._session.authenticate()
        except asyncio.CancelledError:
            await self._close_after_failed_connect()
            raise
        except Exception:
            await self._close_after_failed_connect()
            raise
        log.info("MAG provider session connected")

    async def _close_after_failed_connect(self) -> None:
        """Best-effort cleanup that preserves the original authentication failure."""
        try:
            await self._session.close()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.warning("MAG session cleanup failed after authentication failure", exc_info=True)
        finally:
            try:
                await self._connection.close()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.warning(
                    "MAG connection cleanup failed after authentication failure",
                    exc_info=True,
                )

    async def close(self) -> None:
        await self._session.close()
        await self._connection.close()
        log.info("MAG provider session disconnected")

    async def authenticate(self) -> None:
        await self._session.authenticate()

    async def refresh_token(self) -> None:
        await self._session.refresh()

    async def get_profile(self) -> dict[str, Any]:
        return await self._profile_mgr.get_profile()

    @property
    def supports_live_categories(self) -> bool:
        """Whether the selected authenticated profile supports live genre browsing."""
        return self._session.profile.uses_ordered_live_catalogue

    @property
    def live_catalogue_stats(self) -> dict[str, int]:
        """Return safe aggregate live-catalogue counts from the current provider session."""
        return self._catalogue.live_catalogue_stats

    async def get_live_categories(self) -> list[dict[str, Any]]:
        """Return profile-supported live genre records."""
        return await self._catalogue.get_live_categories()

    async def get_channels(self) -> list[dict[str, Any]]:
        return await self._catalogue.get_channels()

    async def get_vod(self, page: int = 0, category_id: int | None = None) -> list[dict[str, Any]]:
        return await self._catalogue.get_vod(page=page, category_id=category_id)

    async def get_series(
        self, page: int = 0, category_id: int | None = None
    ) -> list[dict[str, Any]]:
        return await self._catalogue.get_series(page=page, category_id=category_id)

    async def get_epg(
        self,
        channel_ids: list[int] | None = None,
        period: int = 3,
    ) -> dict[int, list[dict[str, Any]]]:
        return await self._catalogue.get_epg(channel_ids=channel_ids, period=period)

    async def get_stream_url(self, stream_id: int, stream_type: str = "live") -> str:
        command = await self._catalogue.live_command(stream_id) if stream_type == "live" else None
        return await self._stream.get_stream_url(
            stream_id=stream_id,
            stream_type=stream_type,
            channel_command=command,
        )
