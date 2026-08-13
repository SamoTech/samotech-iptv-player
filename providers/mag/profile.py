"""Account / subscriber profile retrieval for the MAG provider."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING

from .protocol_profile import MAGOperation

if TYPE_CHECKING:
    from .connection import MAGConnection
    from .session import MAGSession

log = logging.getLogger(__name__)


class MAGProfile:
    def __init__(self, connection: MAGConnection, session: MAGSession) -> None:
        # The connection remains constructor-injected for legacy compatibility;
        # profile-owned requests are issued through the session.
        self._conn = connection
        self._sess = session

    async def get_profile(self) -> dict[str, object]:
        """Return a validated account profile through the selected protocol family."""
        log.info("Fetching MAG account profile")
        data = await self._sess.request(MAGOperation.ACCOUNT_INFO)
        if not isinstance(data, Mapping):
            return {}
        raw_profile = data.get("js", {})
        profile: dict[str, object] = (
            {str(key): value for key, value in raw_profile.items()}
            if isinstance(raw_profile, Mapping)
            else {}
        )
        log.debug("MAG account profile keys: %s", list(profile.keys()))
        return profile
