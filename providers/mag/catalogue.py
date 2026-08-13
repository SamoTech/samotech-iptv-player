"""Catalogue retrieval helpers for the MAG provider."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING

from ..base.errors import AuthError, ProviderError
from .protocol_profile import MAGOperation

if TYPE_CHECKING:
    from .connection import MAGConnection
    from .session import MAGSession

log = logging.getLogger(__name__)

# Safety guard only: the profile-priority fix selects the correct finite contract.
MAX_ORDERED_LIVE_PAGES_PER_GENRE = 1000

type MagRecord = dict[str, object]


class MAGCatalogue:
    """Load MAG catalogue records through the selected protocol profile."""

    def __init__(self, connection: MAGConnection, session: MAGSession) -> None:
        self._conn = connection
        self._sess = session
        self._live_commands: dict[str, str] = {}
        self._last_live_stats = {"received": 0, "accepted": 0, "rejected": 0}
        self._last_category_count: int | None = None

    @property
    def live_catalogue_stats(self) -> dict[str, int]:
        """Return safe aggregate counts without retaining raw portal payloads."""
        return dict(self._last_live_stats)

    async def get_live_categories(self) -> list[MagRecord]:
        """Return live genre records only for profiles that explicitly support them."""
        if not (
            self._sess.profile.uses_ordered_live_catalogue
            or self._sess.profile.uses_direct_live_catalogue
        ):
            raise ProviderError("Provider does not support category browsing")
        endpoint = self._sess.profile.operation_endpoint(MAGOperation.LIVE_GENRES)
        log.info(
            "[IPTV] PROVIDER=MAG CATALOGUE STAGE=categories REQUEST ENDPOINT=%s",
            endpoint,
        )
        data = await self._sess.request(MAGOperation.LIVE_GENRES)
        self._log_response_shape("categories", data)
        categories = self._records_from_js_list(data)
        self._last_category_count = len(categories)
        log.info(
            "[IPTV] PROVIDER=MAG CATALOGUE STAGE=categories RESPONSE JSON=True RECORDS=%d",
            len(categories),
        )
        log.info("[IPTV] PROVIDER=MAG CATALOGUE PARSED categories=%d", len(categories))
        return categories

    async def get_channels(self) -> list[MagRecord]:
        """Return live records through legacy or observed ordered-list behavior."""
        endpoint = self._sess.profile.operation_endpoint(
            MAGOperation.LIVE_ORDERED_LIST
            if self._sess.profile.uses_ordered_live_catalogue
            else MAGOperation.CHANNELS
        )
        log.info(
            "[IPTV] PROVIDER=MAG CATALOGUE STAGE=channels REQUEST ENDPOINT=%s",
            endpoint,
        )
        if not self._sess.profile.uses_ordered_live_catalogue:
            data = await self._sess.request(MAGOperation.CHANNELS)
            self._log_response_shape("channels", data)
            items = (
                self._records_from_direct_response(data)
                if self._sess.profile.uses_direct_channel_urls
                else self._records_from_response(data)
            )
            if not self._sess.profile.uses_direct_channel_urls:
                self._last_live_stats = {
                    "received": len(items),
                    "accepted": len(items),
                    "rejected": 0,
                }
                log.info(
                    "[IPTV] PROVIDER=MAG CATALOGUE STAGE=channels RESPONSE JSON=True RECORDS=%d",
                    len(items),
                )
                log.info("[IPTV] PROVIDER=MAG CATALOGUE PARSED channels=%d", len(items))
                self._log_channel_sample(items)
                self._log_catalogue_complete(len(items))
                return items
            accepted_records: list[MagRecord] = []
            rejected = 0
            for item in items:
                channel_id = str(item.get("id") or "").strip()
                name = str(item.get("name") or item.get("title") or "").strip()
                command = self._direct_command(item)
                if not channel_id or not name or not command:
                    rejected += 1
                    continue
                self._live_commands[channel_id] = command
                accepted_records.append(item)
            self._last_live_stats = {
                "received": len(items),
                "accepted": len(accepted_records),
                "rejected": rejected,
            }
            log.info(
                "[IPTV] PROVIDER=MAG CATALOGUE STAGE=channels RESPONSE JSON=True "
                "RECEIVED=%d ACCEPTED=%d REJECTED=%d",
                len(items),
                len(accepted_records),
                rejected,
            )
            log.info(
                "[IPTV] PROVIDER=MAG CATALOGUE PARSED channels=%d",
                len(accepted_records),
            )
            self._log_channel_sample(accepted_records)
            self._log_catalogue_complete(len(accepted_records))
            return accepted_records
        return await self._ordered_live_channels()

    async def _ordered_live_channels(self) -> list[MagRecord]:
        genres = await self.get_live_categories()
        received = accepted = rejected = 0
        self._live_commands.clear()
        records: list[MagRecord] = []
        seen: set[str] = set()
        for genre in genres:
            genre_id = str(genre.get("id") or "").strip()
            if not genre_id:
                rejected += 1
                continue
            page = self._sess.profile.ordered_live_start_page
            fetched_for_genre = 0
            pages_for_genre = 0
            page_fingerprints: set[bytes] = set()
            while True:
                if pages_for_genre >= MAX_ORDERED_LIVE_PAGES_PER_GENRE:
                    raise ProviderError("MAG ordered-list pagination exceeded the safety limit")
                data = await self._sess.request(
                    MAGOperation.LIVE_ORDERED_LIST,
                    params={"genre": genre_id, "p": page},
                )
                pages_for_genre += 1
                self._log_response_shape("ordered", data)
                if not isinstance(data, Mapping):
                    raise ProviderError("MAG ordered-list response was not a JSON object")
                raw_envelope = data.get("js")
                if not isinstance(raw_envelope, Mapping) or "data" not in raw_envelope:
                    raise ProviderError("MAG ordered-list response missing js.data")
                if not isinstance(raw_envelope["data"], list):
                    raise ProviderError("MAG ordered-list response data was not a list")
                envelope = raw_envelope
                if envelope.get("error"):
                    raise AuthError("MAG catalogue response indicated an expired session")
                page_records = self._records(envelope.get("data", []))
                fingerprint = self._page_fingerprint(page_records)
                if page_records and fingerprint in page_fingerprints:
                    raise ProviderError("MAG ordered-list pagination repeated a non-empty page")
                page_fingerprints.add(fingerprint)
                fetched_for_genre += len(page_records)
                received += len(page_records)
                for record in page_records:
                    channel_id = str(record.get("id") or "").strip()
                    name = str(record.get("name") or record.get("title") or "").strip()
                    command = record.get("cmd")
                    if (
                        not channel_id
                        or not name
                        or not isinstance(command, str)
                        or not command.strip()
                    ):
                        rejected += 1
                        continue
                    if channel_id in seen:
                        continue
                    seen.add(channel_id)
                    self._live_commands[channel_id] = command
                    records.append(record)
                    accepted += 1
                total_items = self._as_nonnegative_int(
                    envelope.get("total_items"), len(page_records)
                )
                log.debug(
                    "[IPTV] PROVIDER=MAG ORDERED PAGE GENRE=<redacted> PAGE=%d "
                    "RECORDS=%d TOTAL_ITEMS=%d",
                    page,
                    len(page_records),
                    total_items,
                )
                if not page_records or fetched_for_genre >= total_items:
                    break
                page += 1
        self._last_live_stats = {"received": received, "accepted": accepted, "rejected": rejected}
        log.info(
            "[IPTV] PROVIDER=MAG CATALOGUE STAGE=channels RESPONSE JSON=True "
            "RECEIVED=%d ACCEPTED=%d REJECTED=%d",
            received,
            accepted,
            rejected,
        )
        log.info("[IPTV] PROVIDER=MAG CATALOGUE PARSED channels=%d", accepted)
        self._log_channel_sample(records)
        self._log_catalogue_complete(accepted)
        return records

    def _log_response_shape(self, stage: str, data: object) -> None:
        """Log response structure without logging values or response bodies."""
        top_type = type(data).__name__
        top_keys = sorted(str(key) for key in data.keys()) if isinstance(data, Mapping) else []
        raw_js = data.get("js") if isinstance(data, Mapping) else None
        js_type = type(raw_js).__name__
        js_keys = sorted(str(key) for key in raw_js.keys()) if isinstance(raw_js, Mapping) else []
        raw_data = raw_js.get("data") if isinstance(raw_js, Mapping) else None
        data_type = type(raw_data).__name__
        data_count = len(raw_data) if isinstance(raw_data, list) else None
        sample = raw_data[0] if isinstance(raw_data, list) and raw_data else None
        sample_keys = (
            sorted(str(key) for key in sample.keys()) if isinstance(sample, Mapping) else []
        )
        sample_types = (
            ",".join(f"{key}:{type(sample[key]).__name__}" for key in sample_keys)
            if isinstance(sample, Mapping)
            else ""
        )
        sample_commands = sample.get("cmds") if isinstance(sample, Mapping) else None
        cmds_url_present = (
            isinstance(sample_commands, list)
            and bool(sample_commands)
            and isinstance(sample_commands[0], Mapping)
            and isinstance(sample_commands[0].get("url"), str)
        )
        log.debug(
            "[IPTV] PROVIDER=MAG CATALOGUE SHAPE stage=%s top_type=%s top_keys=%s "
            "js_type=%s js_keys=%s data_type=%s data_count=%s sample_keys=%s "
            "sample_types=%s id_present=%s name_present=%s cmd_present=%s "
            "cmds_present=%s cmds_url_present=%s logo_present=%s genre_present=%s",
            stage,
            top_type,
            ",".join(top_keys),
            js_type,
            ",".join(js_keys),
            data_type,
            data_count if data_count is not None else "<none>",
            ",".join(sample_keys),
            sample_types,
            isinstance(sample, Mapping) and bool(str(sample.get("id") or "").strip()),
            isinstance(sample, Mapping)
            and bool(str(sample.get("name") or sample.get("title") or "").strip()),
            isinstance(sample, Mapping) and "cmd" in sample,
            isinstance(sample, Mapping) and "cmds" in sample,
            cmds_url_present,
            isinstance(sample, Mapping) and bool(sample.get("logo") or sample.get("logo_small")),
            isinstance(sample, Mapping)
            and bool(sample.get("tv_genre_id") or sample.get("category_id") or sample.get("genre")),
        )

    def _log_channel_sample(self, records: list[MagRecord]) -> None:
        """Log channel field presence without exposing record values."""
        if not records:
            return
        sample = records[0]
        commands = sample.get("cmds")
        direct_command = (
            isinstance(commands, list)
            and bool(commands)
            and isinstance(commands[0], Mapping)
            and isinstance(commands[0].get("url"), str)
            and bool(commands[0]["url"].strip())
        )
        log.info(
            "[IPTV] PROVIDER=MAG CHANNEL SAMPLE ID_PRESENT=%s NAME_PRESENT=%s "
            "CMDS_PRESENT=%s USABLE_CMDS_URL=%s",
            bool(str(sample.get("id") or "").strip()),
            bool(str(sample.get("name") or sample.get("title") or "").strip()),
            isinstance(commands, list),
            direct_command,
        )

    async def live_command(self, channel_id: int) -> str | None:
        """Return a private loaded command, refreshing only if a compatible profile needs it."""
        key = str(channel_id)
        command = self._live_commands.get(key)
        if command is not None:
            return command
        if (
            self._sess.profile.uses_channel_command_for_live_link
            or self._sess.profile.uses_direct_channel_urls
        ):
            await self.get_channels()
            return self._live_commands.get(key)
        return None

    async def get_vod(self, page: int = 0, category_id: int | None = None) -> list[MagRecord]:
        params: dict[str, str | int] = {"p": page, "items_num": 100, "sortby": "added"}
        if category_id is not None:
            params["category"] = category_id
        return self._records_from_response(
            await self._sess.request(MAGOperation.VOD, params=params)
        )

    async def get_series(self, page: int = 0, category_id: int | None = None) -> list[MagRecord]:
        params: dict[str, str | int] = {"p": page, "items_num": 100, "sortby": "added"}
        if category_id is not None:
            params["category"] = category_id
        return self._records_from_response(
            await self._sess.request(MAGOperation.SERIES, params=params)
        )

    async def get_epg(
        self, channel_ids: list[int] | None = None, period: int = 3
    ) -> dict[int, list[MagRecord]]:
        params: dict[str, str | int] = {"period": period}
        if channel_ids:
            params["ch_id"] = ",".join(str(channel_id) for channel_id in channel_ids)
        raw = self._js_payload(await self._sess.request(MAGOperation.EPG, params=params))
        result: dict[int, list[MagRecord]] = {}
        for raw_channel_id, programmes in raw.items():
            try:
                result[int(str(raw_channel_id))] = self._records(programmes)
            except ValueError:
                continue
        return result

    def _log_catalogue_complete(self, channel_count: int) -> None:
        """Log aggregate catalogue counts without retaining sensitive payloads."""
        category_count = (
            str(self._last_category_count) if self._last_category_count is not None else "<unknown>"
        )
        log.info(
            "[IPTV] PROVIDER=MAG CATALOGUE COMPLETE CATEGORIES=%s CHANNELS=%d",
            category_count,
            channel_count,
        )

    @staticmethod
    def _records_from_response(data: object) -> list[MagRecord]:
        payload = MAGCatalogue._js_payload(data)
        if payload.get("error"):
            raise AuthError("MAG catalogue response indicated an expired session")
        return MAGCatalogue._records(payload.get("data", []))

    @staticmethod
    def _records_from_js_list(data: object) -> list[MagRecord]:
        if not isinstance(data, Mapping) or "js" not in data:
            raise ProviderError("MAG catalogue response missing js category data")
        raw_records = data["js"]
        if not isinstance(raw_records, list):
            raise ProviderError("MAG catalogue category data was not a list")
        return MAGCatalogue._records(raw_records)

    @staticmethod
    def _records_from_direct_response(data: object) -> list[MagRecord]:
        if not isinstance(data, Mapping):
            raise ProviderError("MAG channel response was not a JSON object")
        raw_js = data.get("js")
        if not isinstance(raw_js, Mapping) or "data" not in raw_js:
            raise ProviderError("MAG channel response missing js.data")
        if not isinstance(raw_js["data"], list):
            raise ProviderError("MAG channel response data was not a list")
        return MAGCatalogue._records(raw_js["data"])

    @staticmethod
    def _js_payload(data: object) -> Mapping[str, object]:
        if not isinstance(data, Mapping):
            return {}
        payload = data.get("js", {})
        return payload if isinstance(payload, Mapping) else {}

    @staticmethod
    def _page_fingerprint(records: list[MagRecord]) -> bytes:
        """Fingerprint stable record shape without retaining commands or URLs."""
        shape = tuple(
            (
                str(record.get("id") or ""),
                str(record.get("name") or record.get("title") or ""),
                isinstance(record.get("cmd"), str),
                isinstance(record.get("cmds"), list),
            )
            for record in records
        )
        return hashlib.sha256(repr(shape).encode("utf-8")).digest()

    @staticmethod
    def _direct_command(record: MagRecord) -> str | None:
        """Extract a supplied ``cmds[].url`` without rewriting or logging it."""
        raw_commands = record.get("cmds")
        if not isinstance(raw_commands, list) or not raw_commands:
            return None
        first = raw_commands[0]
        if not isinstance(first, Mapping):
            return None
        raw_url = first.get("url")
        if not isinstance(raw_url, str) or not raw_url.strip():
            return None
        return raw_url.strip()

    @staticmethod
    def _records(value: object) -> list[MagRecord]:
        if not isinstance(value, list):
            return []
        return [dict(record) for record in value if isinstance(record, Mapping)]

    @staticmethod
    def _as_nonnegative_int(value: object, fallback: int) -> int:
        try:
            return max(int(str(value)), 0)
        except (TypeError, ValueError):
            return fallback
