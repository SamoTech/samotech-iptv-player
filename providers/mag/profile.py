"""Account / subscriber profile retrieval for the MAG provider."""
from __future__ import annotations

import logging
from typing import Any

from .constants import ENDPOINT_PROFILE
from .connection import MAGConnection
from .session import MAGSession

log = logging.getLogger(__name__)


class MAGProfile:
    def __init__(self, connection: MAGConnection, session: MAGSession) -> None:
        self._conn = connection
        self._sess = session

    async def get_profile(self) -> dict[str, Any]:
        log.info("Fetching account profile")
        data = await self._conn.get(ENDPOINT_PROFILE, headers=self._sess.get_headers())
        profile: dict[str, Any] = data.get("js") or {}
        log.debug("Profile keys: %s", list(profile.keys()))
        return profile
