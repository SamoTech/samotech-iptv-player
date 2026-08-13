"""Bounded MAG/Stalker handshake discovery.

This module probes only a fixed set of documented endpoint families.  It does
not crawl, scan, retain response bodies, expose credential material, or select
an endpoint based on HTTP success alone.
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from ..base.errors import NetworkError
from .protocol_profile import (
    MAGOperation,
    MAGProtocolProfile,
    StalkerClientCompatibilityProfile,
    StalkerHelperCompatibilityProfile,
    StalkerPortalPhpLegacyProfile,
    StalkerQueryProtocolProfile,
)

if TYPE_CHECKING:
    from .connection import MAGConnection, MAGProbeResponse
    from .credentials import MAGCredentials

__all__ = [
    "MAGDifferentialCase",
    "MAGDifferentialResult",
    "MAGDiscoveryCandidate",
    "MAGDiscoveryClassification",
    "MAGDiscoveryResult",
    "MAGProtocolDiscovery",
]


class MAGDiscoveryClassification(StrEnum):
    """Safe outcome categories for one bounded handshake candidate."""

    NETWORK_FAILURE = "NETWORK_FAILURE"
    HTTP_404 = "HTTP_404"
    HTTP_401 = "HTTP_401"
    HTTP_403 = "HTTP_403"
    HTTP_OTHER = "HTTP_OTHER"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"
    MALFORMED_JSON = "MALFORMED_JSON"
    JSON_WITHOUT_TOKEN = "JSON_WITHOUT_TOKEN"  # noqa: S105
    VALID_STALKER_HANDSHAKE = "VALID_STALKER_HANDSHAKE"
    UNKNOWN_PROTOCOL = "UNKNOWN_PROTOCOL"
    PROFILE_REQUIRED = "PROFILE_REQUIRED"
    PROFILE_SUCCESS = "PROFILE_SUCCESS"
    PROFILE_AUTH_ERROR = "PROFILE_AUTH_ERROR"
    LOGIN_REQUIRED = "LOGIN_REQUIRED"
    AUTH_KEY_REQUIRED = "AUTH_KEY_REQUIRED"
    STB_NOT_AUTHORIZED = "STB_NOT_AUTHORIZED"
    STB_MODEL_REJECTED = "STB_MODEL_REJECTED"
    DEVICE_ID_REQUIRED = "DEVICE_ID_REQUIRED"
    DEVICE_ID_REJECTED = "DEVICE_ID_REJECTED"
    AUTH_SUCCESS = "AUTH_SUCCESS"
    SESSION_ERROR = "SESSION_ERROR"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    CONTENT_TYPE_MISMATCH = "CONTENT_TYPE_MISMATCH"
    REDIRECTED = "REDIRECTED"
    WAF_OR_GATEWAY_SUSPECTED = "WAF_OR_GATEWAY_SUSPECTED"


@dataclass(frozen=True)
class MAGDiscoveryCandidate:
    """One fixed candidate profile in deterministic priority order."""

    name: str
    profile: MAGProtocolProfile


@dataclass(frozen=True)
class MAGDifferentialCase:
    """One fixed, evidence-labelled request variation for the differential lab."""

    test_id: str
    profile: MAGProtocolProfile
    endpoint: str
    method: str
    params: Mapping[str, str | int] = field(default_factory=dict)
    form: Mapping[str, str | int] = field(default_factory=dict)
    header_fingerprint: str = ""
    cookie_policy: str = ""
    expected_evidence: str = ""


@dataclass(frozen=True)
class MAGDifferentialResult:
    """Safe result metadata for one fixed differential request."""

    test_id: str
    profile_name: str
    endpoint: str
    method: str
    status: int | None
    content_type: str | None
    response_size: int | None
    is_json: bool
    token_present: bool
    profile_present: bool
    error_present: bool
    authorization_failure: bool
    classification: MAGDiscoveryClassification
    elapsed_seconds: float
    redirect_count: int = 0
    server: str = ""
    allow: str = ""
    www_authenticate: bool = False


@dataclass(frozen=True)
class MAGDiscoveryResult:
    """A safe discovery outcome that never contains request or response secrets."""

    candidate_name: str
    status: int | None
    content_type: str | None
    response_size: int | None
    elapsed_seconds: float
    is_json: bool
    token_present: bool
    classification: MAGDiscoveryClassification
    used_prehash: bool = False
    profile_present: bool = False
    error_present: bool = False
    authorization_failure: bool = False
    redirect_count: int = 0
    server: str = ""
    allow: str = ""
    www_authenticate: bool = False


class MAGProtocolDiscovery:
    """Probe only approved MAG/Stalker handshake endpoint candidates."""

    def __init__(self, connection: MAGConnection, credentials: MAGCredentials) -> None:
        self._connection = connection
        self._credentials = credentials

    @staticmethod
    def candidates() -> tuple[MAGDiscoveryCandidate, ...]:
        """Return the closed candidate set in explicit deterministic priority order."""
        return (
            MAGDiscoveryCandidate(
                "configured_base_server",
                StalkerQueryProtocolProfile(name="discovered_configured_base"),
            ),
            MAGDiscoveryCandidate(
                "origin_stalker_portal",
                StalkerQueryProtocolProfile(
                    name="discovered_stalker_portal",
                    handshake_endpoint="stalker_portal/server/load.php",
                    use_origin_base=True,
                ),
            ),
            MAGDiscoveryCandidate(
                "origin_stalker_portal_helper",
                StalkerHelperCompatibilityProfile(),
            ),
            MAGDiscoveryCandidate(
                "origin_stb_server",
                StalkerQueryProtocolProfile(
                    name="discovered_stb_server",
                    handshake_endpoint="stb/server/load.php",
                    use_origin_base=True,
                ),
            ),
            MAGDiscoveryCandidate(
                "origin_portal_php",
                StalkerQueryProtocolProfile(
                    name="discovered_portal_php",
                    handshake_endpoint="portal.php",
                    use_origin_base=True,
                ),
            ),
            MAGDiscoveryCandidate(
                "origin_portal_php_stalker_client",
                StalkerClientCompatibilityProfile(),
            ),
            MAGDiscoveryCandidate(
                "origin_portal_php_mac_client",
                StalkerPortalPhpLegacyProfile(),
            ),
        )

    async def probe_case(self, case: MAGDifferentialCase) -> MAGDifferentialResult:
        """Execute one caller-supplied evidence-backed request variation."""
        headers = {
            **case.profile.protocol_headers(self._credentials.portal_url),
            **case.profile.request_headers(
                self._credentials.portal_url,
                mac_address=self._credentials.mac_address,
                serial_number=self._credentials.serial_number,
                device_id=self._credentials.device_id,
                device_id2=self._credentials.device_id2,
                token=self._credentials.token,
                mag_model=self._credentials.mag_model,
            ),
        }
        if case.method.upper() == "POST":
            headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        started = time.perf_counter()
        try:
            response = await self._connection.probe(
                case.method.upper(),
                case.endpoint,
                params=case.params,
                data=case.form,
                headers=headers,
                base_url=case.profile.request_base_url(self._credentials.portal_url),
            )
        except (NetworkError, RuntimeError):
            return MAGDifferentialResult(
                test_id=case.test_id,
                profile_name=case.profile.name,
                endpoint=case.endpoint,
                method=case.method.upper(),
                status=None,
                content_type=None,
                response_size=None,
                is_json=False,
                token_present=False,
                profile_present=False,
                error_present=False,
                authorization_failure=False,
                classification=MAGDiscoveryClassification.NETWORK_FAILURE,
                elapsed_seconds=time.perf_counter() - started,
            )
        base_result = self._classify(case.test_id, response, prehash=False)
        classification = base_result.classification
        token_present = base_result.token_present
        is_json = response.payload is not None
        raw_js = response.payload.get("js") if isinstance(response.payload, Mapping) else None
        profile_present = isinstance(raw_js, Mapping) and bool(raw_js)
        error_present = isinstance(response.payload, Mapping) and bool(
            response.payload.get("error") or (isinstance(raw_js, Mapping) and raw_js.get("error"))
        )
        authorization_failure = (
            response.status in {401, 403}
            or any(
                marker in str(raw_js).casefold()
                for marker in ("unauthor", "auth", "login", "device")
            )
            if raw_js is not None
            else response.status in {401, 403}
        )
        if response.status == 405:
            classification = MAGDiscoveryClassification.METHOD_NOT_ALLOWED
        elif response.status in {301, 302, 303, 307, 308}:
            classification = MAGDiscoveryClassification.REDIRECTED
        return MAGDifferentialResult(
            test_id=case.test_id,
            profile_name=case.profile.name,
            endpoint=case.endpoint,
            method=case.method.upper(),
            status=response.status,
            content_type=response.content_type,
            response_size=response.response_size,
            is_json=is_json,
            token_present=token_present,
            profile_present=profile_present,
            error_present=error_present,
            authorization_failure=authorization_failure,
            classification=classification,
            elapsed_seconds=response.elapsed_seconds,
            redirect_count=response.redirect_count,
            server=response.server,
            allow=response.allow,
            www_authenticate=response.www_authenticate,
        )

    async def discover(self) -> tuple[tuple[MAGDiscoveryResult, ...], MAGProtocolProfile | None]:
        """Probe the fixed candidates and return safe outcomes plus one selected profile.

        At most eleven requests are made: one primary handshake per candidate and,
        only after an HTTP-200 JSON response without a token, one `prehash=false`
        retry for that same generic candidate.
        """
        results: list[MAGDiscoveryResult] = []
        selected: MAGProtocolProfile | None = None
        for candidate in self.candidates():
            primary = await self._probe(candidate, prehash=False)
            results.append(primary)
            if (
                selected is None
                and primary.classification is MAGDiscoveryClassification.VALID_STALKER_HANDSHAKE
            ):
                selected = candidate.profile
                continue
            if self._should_probe_prehash(primary) and not isinstance(
                candidate.profile,
                (
                    StalkerClientCompatibilityProfile,
                    StalkerHelperCompatibilityProfile,
                    StalkerPortalPhpLegacyProfile,
                ),
            ):
                with_prehash = await self._probe(candidate, prehash=True)
                results.append(with_prehash)
                if (
                    selected is None
                    and with_prehash.classification
                    is MAGDiscoveryClassification.VALID_STALKER_HANDSHAKE
                ):
                    selected = candidate.profile
        return tuple(results), selected

    @staticmethod
    def select_valid(
        candidates: Sequence[MAGDiscoveryCandidate], results: Sequence[MAGDiscoveryResult]
    ) -> MAGProtocolProfile | None:
        """Select the first valid primary candidate using explicit priority order."""
        results_by_name: dict[str, MAGDiscoveryResult] = {}
        for outcome in results:
            if not outcome.used_prehash:
                results_by_name[outcome.candidate_name] = outcome
        for candidate in candidates:
            result: MAGDiscoveryResult | None = results_by_name.get(candidate.name)
            if (
                result
                and result.classification is MAGDiscoveryClassification.VALID_STALKER_HANDSHAKE
            ):
                return candidate.profile
        return None

    async def _probe(
        self, candidate: MAGDiscoveryCandidate, *, prehash: bool
    ) -> MAGDiscoveryResult:
        request = candidate.profile.build_request(
            self._credentials.portal_url,
            MAGOperation.HANDSHAKE,
            params={"prehash": "false"} if prehash else None,
        )
        headers = {
            **request.headers,
            **candidate.profile.request_headers(
                self._credentials.portal_url,
                mac_address=self._credentials.mac_address,
                serial_number=self._credentials.serial_number,
                device_id=self._credentials.device_id,
                device_id2=self._credentials.device_id2,
                token="",
                mag_model=self._credentials.mag_model,
            ),
        }
        started = time.perf_counter()
        try:
            response = await self._connection.probe(
                request.method,
                request.endpoint,
                params=request.params,
                data=request.form,
                headers=headers,
                base_url=request.base_url,
            )
        except (NetworkError, RuntimeError):
            return MAGDiscoveryResult(
                candidate_name=candidate.name,
                status=None,
                content_type=None,
                response_size=None,
                elapsed_seconds=time.perf_counter() - started,
                is_json=False,
                token_present=False,
                classification=MAGDiscoveryClassification.NETWORK_FAILURE,
                used_prehash=prehash,
            )
        return self._classify(candidate.name, response, prehash=prehash)

    @staticmethod
    def _should_probe_prehash(result: MAGDiscoveryResult) -> bool:
        return (
            not result.used_prehash
            and result.status == 200
            and result.is_json
            and not result.token_present
            and result.classification is MAGDiscoveryClassification.JSON_WITHOUT_TOKEN
        )

    @staticmethod
    def _classify(
        candidate_name: str, response: MAGProbeResponse, *, prehash: bool
    ) -> MAGDiscoveryResult:
        classification: MAGDiscoveryClassification
        token_present = False
        is_json = response.payload is not None
        if response.status == 404:
            classification = MAGDiscoveryClassification.HTTP_404
        elif response.status == 401:
            classification = MAGDiscoveryClassification.HTTP_401
        elif response.status == 403:
            classification = MAGDiscoveryClassification.HTTP_403
        elif not 200 <= response.status < 300:
            classification = MAGDiscoveryClassification.HTTP_OTHER
        elif response.response_size == 0:
            classification = MAGDiscoveryClassification.EMPTY_RESPONSE
        elif response.malformed_json:
            classification = MAGDiscoveryClassification.MALFORMED_JSON
        else:
            classification, token_present = MAGProtocolDiscovery._classify_json(response.payload)
        return MAGDiscoveryResult(
            candidate_name=candidate_name,
            status=response.status,
            content_type=response.content_type,
            response_size=response.response_size,
            elapsed_seconds=response.elapsed_seconds,
            is_json=is_json,
            token_present=token_present,
            classification=classification,
            used_prehash=prehash,
            redirect_count=response.redirect_count,
            server=response.server,
            allow=response.allow,
            www_authenticate=response.www_authenticate,
        )

    @staticmethod
    def _classify_json(
        payload: object,
    ) -> tuple[MAGDiscoveryClassification, bool]:
        if not isinstance(payload, Mapping):
            return MAGDiscoveryClassification.UNKNOWN_PROTOCOL, False
        raw_js = payload.get("js")
        js = raw_js if isinstance(raw_js, Mapping) else {}
        if js.get("token") or js.get("Token") or payload.get("token"):
            return MAGDiscoveryClassification.VALID_STALKER_HANDSHAKE, True
        if isinstance(raw_js, Mapping) or "token" in payload:
            return MAGDiscoveryClassification.JSON_WITHOUT_TOKEN, False
        return MAGDiscoveryClassification.UNKNOWN_PROTOCOL, False
