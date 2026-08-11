"""Account / subscriber profile retrieval for the MAG provider."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING

from .constants import ENDPOINT_PROFILE

if TYPE_CHECKING:
    from .connection import MAGConnection
    from .session import MAGSession

log = logging.getLogger(__name__)


class MAGProfile:
    def __init__(self, connection: MAGConnection, session: MAGSession) -> None:
        self._conn = connection
        self._sess = session

    async def get_profile(self) -> dict[str, object]:
        """Return a validated profile record from the MAG ``js`` envelope."""
        log.info("Fetching account profile")
        data = await self._conn.get(ENDPOINT_PROFILE, headers=self._sess.get_headers())
        if not isinstance(data, Mapping):
            return {}
        raw_profile = data.get("js", {})
        profile: dict[str, object] = (
            {str(key): value for key, value in raw_profile.items()}
            if isinstance(raw_profile, Mapping)
            else {}
        )
        log.debug("Profile keys: %s", list(profile.keys()))
        return profile
