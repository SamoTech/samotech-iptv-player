"""Deterministic, local parsing and normalization for universal IPTV input."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, TypedDict
from urllib.parse import parse_qs, urlsplit

if TYPE_CHECKING:
    from collections.abc import Mapping


class _XtreamFields(TypedDict):
    server_url: str | None
    playlist_url: str | None
    username: str | None
    password: str | None
    epg_url: str | None
    output_format: str | None
    additional_parameters: dict[str, str]


class _M3UFields(TypedDict):
    playlist_url: str | None
    server_url: str | None


class _MAGFields(TypedDict):
    portal_url: str | None
    mac_address: str | None


__all__ = [
    "DetectedProviderInput",
    "ImportProtocol",
    "detect_provider_input",
    "mask_mac",
    "mask_password",
    "suggest_provider_id",
]


class ImportProtocol(StrEnum):
    """Protocols understood by the Smart Import boundary."""

    XTREAM = "xtream"
    M3U = "m3u"
    MAG = "mag"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DetectedProviderInput:
    """Safe normalized detection result; secret fields are never included in repr output."""

    protocol: ImportProtocol
    server_url: str | None = None
    portal_url: str | None = None
    playlist_url: str | None = None
    username: str | None = field(default=None, repr=False)
    password: str | None = field(default=None, repr=False)
    mac_address: str | None = field(default=None, repr=False)
    epg_url: str | None = None
    output_format: str | None = None
    additional_parameters: Mapping[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    missing_required_fields: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    candidates: tuple[ImportProtocol, ...] = ()

    @property
    def is_complete(self) -> bool:
        """Return whether the detected protocol has all required registration fields."""
        return self.protocol in {
            ImportProtocol.XTREAM,
            ImportProtocol.M3U,
            ImportProtocol.MAG,
        } and not (self.missing_required_fields)


_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_MAC_RE = re.compile(r"(?<![0-9A-Fa-f])(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}(?![0-9A-Fa-f])")
_LABEL_RE = re.compile(
    r"(?im)^\s*(server|server url|username|user|password|pass|portal|mag portal|mac|mac address|"
    r"xtream url|m3u url|playlist url|epg|epg url|output|output format)\s*[:=]\s*(.*?)\s*$"
)


def mask_password(value: str | None) -> str:
    """Return a fixed safe mask for a non-empty password."""
    return "••••••••" if value else "Not detected"


def mask_mac(value: str | None) -> str:
    """Mask all but the last MAC octet for a human-readable preview."""
    if not value:
        return "Not detected"
    parts = value.split(":")
    return "••:" * 5 + parts[-1].upper()


def suggest_provider_id(result: DetectedProviderInput) -> str:
    """Build a deterministic non-secret provider ID from protocol and safe host data."""
    raw = result.server_url or result.portal_url or result.playlist_url or result.protocol.value
    host = urlsplit(raw).hostname or raw
    host = re.sub(r"[^a-z0-9]+", "-", host.casefold()).strip("-") or "provider"
    suffix = ""
    if result.protocol is ImportProtocol.XTREAM and result.username:
        suffix = "-" + re.sub(r"[^a-z0-9]+", "-", result.username.casefold()).strip("-")[:24]
    elif result.protocol is ImportProtocol.MAG and result.mac_address:
        suffix = "-" + result.mac_address.replace(":", "")[-6:].casefold()
    return f"{result.protocol.value}-{host}{suffix}".strip("-")[:64]


def detect_provider_input(text: str) -> DetectedProviderInput:
    """Parse, detect, normalize, and validate one arbitrary local text block."""
    source = text.strip()
    if not source:
        return DetectedProviderInput(
            protocol=ImportProtocol.UNKNOWN,
            confidence=0.0,
            missing_required_fields=("provider format",),
            warnings=("Paste provider information to begin detection.",),
        )

    labels = _labels(source)
    urls = [_clean_url(url) for url in _URL_RE.findall(source)]
    mac = _extract_mac(source) or _clean_value(labels.get("mac") or labels.get("mac address"))
    explicit = _explicit_protocol(source)
    xtream = _xtream_fields(source, labels, urls)
    mag = _mag_fields(source, labels, urls, mac)
    m3u = _m3u_fields(source, labels, urls)

    scores = {
        ImportProtocol.XTREAM: _xtream_score(source, labels, urls, explicit),
        ImportProtocol.M3U: _m3u_score(source, labels, urls, explicit),
        ImportProtocol.MAG: _mag_score(source, labels, urls, mac, explicit),
    }
    active = sorted(
        ((score, protocol) for protocol, score in scores.items() if score > 0),
        reverse=True,
    )
    if not active:
        return DetectedProviderInput(
            protocol=ImportProtocol.UNKNOWN,
            confidence=0.0,
            warnings=("No supported IPTV format was detected.",),
        )

    top_score, top_protocol = active[0]
    close = tuple(protocol for score, protocol in active if score >= max(1, top_score - 25))
    if len(close) > 1 and not explicit:
        return DetectedProviderInput(
            protocol=ImportProtocol.AMBIGUOUS,
            confidence=min(0.99, top_score / 100),
            warnings=("More than one provider format is possible. Select a protocol.",),
            candidates=close,
        )

    if top_protocol is ImportProtocol.XTREAM:
        return _complete_xtream(xtream, top_score)
    if top_protocol is ImportProtocol.M3U:
        return _complete_m3u(m3u, top_score)
    return _complete_mag(mag, top_score)


def _labels(text: str) -> dict[str, str]:
    return {
        key.casefold(): cleaned
        for key, value in _LABEL_RE.findall(text)
        if value.strip()
        if (cleaned := _clean_value(value)) is not None
    }


def _explicit_protocol(text: str) -> ImportProtocol | None:
    lowered = text.casefold()
    mag_marker = re.search(r"(?im)^\s*(mag|stalker|portal|mag portal)\s*[:=]", lowered)
    xtream_marker = re.search(r"(?im)^\s*(xtream|xtream url|xtream codes?)\s*[:=]", lowered)
    m3u_marker = re.search(r"(?im)^\s*(m3u|m3u url|playlist|playlist url)\s*[:=]", lowered)
    explicit = [
        protocol
        for marker, protocol in (
            (mag_marker, ImportProtocol.MAG),
            (xtream_marker, ImportProtocol.XTREAM),
            (m3u_marker, ImportProtocol.M3U),
        )
        if marker
    ]
    return explicit[0] if len(explicit) == 1 else None


def _xtream_fields(text: str, labels: dict[str, str], urls: list[str]) -> _XtreamFields:
    candidate = _clean_url(labels.get("xtream url") or "")
    if not candidate:
        candidate = next((url for url in urls if _is_xtream_url(url)), "")
    server = (
        _server_from_url(candidate)
        if candidate
        else _server_from_url(_clean_url(labels.get("server") or labels.get("server url") or ""))
    )
    username = _clean_value(labels.get("username") or labels.get("user"))
    password = _clean_value(labels.get("password") or labels.get("pass"))
    params: dict[str, str] = {}
    if candidate:
        params = _query_params(candidate)
        parsed_candidate = urlsplit(candidate)
        username = username or parsed_candidate.username or params.get("username")
        password = password or parsed_candidate.password or params.get("password")
    epg_url = next((url for url in urls if "xmltv" in url.casefold()), None)
    return _XtreamFields(
        server_url=server or None,
        playlist_url=candidate or (urls[0] if urls and _is_xtream_url(urls[0]) else None),
        username=username or None,
        password=password or None,
        epg_url=epg_url,
        output_format=params.get("output"),
        additional_parameters=params,
    )


def _m3u_fields(text: str, labels: dict[str, str], urls: list[str]) -> _M3UFields:
    explicit_url = labels.get("m3u url") or labels.get("playlist url")
    playlist = _clean_url(explicit_url or "") or next(
        (url for url in urls if _is_m3u_url(url)), None
    )
    return _M3UFields(
        playlist_url=playlist,
        server_url=_server_from_url(playlist) if playlist else None,
    )


def _mag_fields(text: str, labels: dict[str, str], urls: list[str], mac: str | None) -> _MAGFields:
    portal: str | None = _clean_url(labels.get("portal") or labels.get("mag portal") or "")
    portal = portal or next((url for url in urls if "/c" in urlsplit(url).path.casefold()), None)
    return _MAGFields(portal_url=portal, mac_address=mac)


def _xtream_score(
    text: str, labels: dict[str, str], urls: list[str], explicit: ImportProtocol | None
) -> int:
    score = 0
    if explicit is ImportProtocol.XTREAM:
        score += 80
    if any(_is_xtream_url(url) for url in urls):
        score += 70
    if labels.get("server") or labels.get("server url"):
        score += 20
    if labels.get("username") or labels.get("password"):
        score += 15
    if "get.php" in text.casefold() or "player_api.php" in text.casefold():
        score += 30
    return min(score, 100)


def _m3u_score(
    text: str, labels: dict[str, str], urls: list[str], explicit: ImportProtocol | None
) -> int:
    score = 0
    if explicit is ImportProtocol.M3U:
        score += 80
    if "#extm3u" in text.casefold() or "#extinf" in text.casefold():
        score += 90
    if any(_is_m3u_url(url) for url in urls):
        score += 65
    if labels.get("m3u url") or labels.get("playlist url"):
        score += 30
    return min(score, 100)


def _mag_score(
    text: str,
    labels: dict[str, str],
    urls: list[str],
    mac: str | None,
    explicit: ImportProtocol | None,
) -> int:
    score = 0
    if explicit is ImportProtocol.MAG:
        score += 80
    if mac:
        score += 55
    if labels.get("portal") or labels.get("mag portal"):
        score += 35
    if any("/c" in urlsplit(url).path.casefold() for url in urls):
        score += 45
    if "stalker" in text.casefold():
        score += 20
    return min(score, 100)


def _complete_xtream(fields: _XtreamFields, score: int) -> DetectedProviderInput:
    missing = tuple(
        name
        for name, value in (
            ("server URL", fields.get("server_url")),
            ("username", fields.get("username")),
            ("password", fields.get("password")),
        )
        if not value
    )
    return DetectedProviderInput(
        protocol=ImportProtocol.XTREAM,
        server_url=fields.get("server_url"),
        playlist_url=fields.get("playlist_url"),
        username=fields.get("username"),
        password=fields.get("password"),
        epg_url=fields.get("epg_url"),
        output_format=fields.get("output_format"),
        additional_parameters=fields.get("additional_parameters", {}),
        confidence=min(0.99, score / 100),
        missing_required_fields=missing,
        warnings=("Password is required.",) if "password" in missing else (),
    )


def _complete_m3u(fields: _M3UFields, score: int) -> DetectedProviderInput:
    missing = () if fields.get("playlist_url") else ("playlist URL",)
    return DetectedProviderInput(
        protocol=ImportProtocol.M3U,
        server_url=fields.get("server_url"),
        playlist_url=fields.get("playlist_url"),
        confidence=min(0.99, score / 100),
        missing_required_fields=missing,
        warnings=("Playlist URL or M3U content is required.",) if missing else (),
    )


def _complete_mag(fields: _MAGFields, score: int) -> DetectedProviderInput:
    missing = tuple(
        name
        for name, value in (
            ("portal URL", fields.get("portal_url")),
            ("MAC address", fields.get("mac_address")),
        )
        if not value
    )
    return DetectedProviderInput(
        protocol=ImportProtocol.MAG,
        portal_url=fields.get("portal_url"),
        mac_address=fields.get("mac_address"),
        confidence=min(0.99, score / 100),
        missing_required_fields=missing,
        warnings=("Provide the missing portal URL or MAC address.",) if missing else (),
    )


def _extract_mac(text: str) -> str | None:
    match = _MAC_RE.search(text)
    return match.group(0).upper() if match else None


def _is_xtream_url(url: str) -> bool:
    parsed = urlsplit(url)
    query = _query_params(url)
    path = parsed.path.casefold()
    return (
        "get.php" in path
        or "player_api.php" in path
        or parsed.username is not None
        or {"username", "password"}.issubset(query)
    )


def _is_m3u_url(url: str) -> bool:
    path = urlsplit(url).path.casefold()
    return path.endswith((".m3u", ".m3u8", "/playlist")) or "playlist" in path


def _server_from_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlsplit(url)
    if not parsed.scheme or not parsed.hostname:
        return None
    hostname = parsed.hostname
    if parsed.port is not None:
        hostname = f"{hostname}:{parsed.port}"
    return f"{parsed.scheme}://{hostname}".rstrip("/")


def _query_params(url: str) -> dict[str, str]:
    try:
        return {
            key.casefold(): values[-1].strip()
            for key, values in parse_qs(urlsplit(url).query).items()
            if values
        }
    except ValueError:
        return {}


def _clean_url(value: str) -> str:
    return value.strip().rstrip(",;.)]>")


def _clean_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().strip("\"'")
    return cleaned or None
