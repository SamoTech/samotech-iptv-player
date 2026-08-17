from __future__ import annotations

import asyncio
import logging
import sys
from typing import TYPE_CHECKING

import pytest
from scripts import audit_windows_artifact

from samotech_iptv.core.diagnostics import DiagnosticTrace, log_exception
from samotech_iptv.core.safe_logging import (
    safe_label,
    sanitize_exception,
    sanitize_headers,
    sanitize_mapping,
    sanitize_url,
)
from samotech_iptv.infrastructure.parsing.m3u_source_loader import (
    M3USourceError,
    M3USourceLoader,
)

if TYPE_CHECKING:
    from pathlib import Path

_CANARIES = {
    "password": "SAMOSAFE_" + "PASSWORD_9f3a7c",
    "token": "SAMOSAFE_" + "TOKEN_8b2d91",
    "cookie": "SAMOSAFE_" + "COOKIE_4c7e22",
    "username": "SAMOSAFE_" + "USERNAME_7d1e44",
}


class _FailingHttpClient:
    async def get_text(self, _url: str, **_: object) -> str:
        raise RuntimeError(
            f"request failed url=https://{_CANARIES['username']}:{_CANARIES['password']}"
            f"@provider.example/live?username={_CANARIES['username']}"
            f"&password={_CANARIES['password']}&token={_CANARIES['token']}"
        )


@pytest.mark.parametrize(
    "value",
    [
        f"https://{_CANARIES['username']}:{_CANARIES['password']}"
        f"@provider.example/live?token={_CANARIES['token']}",
        f"authorization=Bearer {_CANARIES['token']} cookie={_CANARIES['cookie']}",
        {
            "username": _CANARIES["username"],
            "password": _CANARIES["password"],
            "token": _CANARIES["token"],
        },
    ],
)
def test_sensitive_values_are_absent_from_central_redaction(value: object) -> None:
    rendered = str(value)
    safe = (
        sanitize_mapping(value)
        if isinstance(value, dict)
        else (
            sanitize_url(value)
            if isinstance(value, str) and value.startswith("http")
            else safe_label(value)
        )
    )
    safe_text = str(safe)
    for canary in _CANARIES.values():
        assert canary not in safe_text
    assert rendered != safe_text or isinstance(value, dict)


def test_headers_and_nested_mapping_retain_safe_shape_without_secrets() -> None:
    headers = sanitize_headers(
        {
            "User-Agent": "SamoTech-Test",
            "Authorization": f"Bearer {_CANARIES['token']}",
            "Cookie": f"session={_CANARIES['cookie']}",
            "X-Provider": {"username": _CANARIES["username"], "status": "ok"},
        }
    )
    assert headers["User-Agent"] == "SamoTech-Test"
    assert headers["Authorization"] == "<REDACTED>"
    assert headers["Cookie"] == "<REDACTED>"
    assert headers["X-Provider"]["username"] == "<REDACTED>"  # type: ignore[index]
    assert headers["X-Provider"]["status"] == "ok"  # type: ignore[index]
    assert all(canary not in str(headers) for canary in _CANARIES.values())


def test_exception_and_diagnostic_trace_capture_are_secret_free(
    caplog: pytest.LogCaptureFixture,
) -> None:
    error = ValueError(
        f"invalid URL https://{_CANARIES['username']}:{_CANARIES['password']}"
        f"@provider.example/live?token={_CANARIES['token']}"
    )
    with caplog.at_level(logging.DEBUG, logger="samotech_iptv.diagnostics"):
        log_exception(
            logging.getLogger("samotech_iptv.diagnostics"),
            "provider request failed",
            error,
            headers={
                "Authorization": f"Bearer {_CANARIES['token']}",
                "Cookie": _CANARIES["cookie"],
            },
            response={
                "username": _CANARIES["username"],
                "password": _CANARIES["password"],
                "status": "error",
            },
        )
        trace = DiagnosticTrace("LOAD_CHANNELS", "provider-safe", "Xtream")
        with pytest.raises(ValueError):
            with trace.stage(
                "HTTP request",
                url=f"https://provider.example/live?password={_CANARIES['password']}",
                response={"token": _CANARIES["token"], "status": "error"},
            ):
                raise error

    output = caplog.text
    assert "diagnostic_exception" in output
    assert "STAGE FAIL" in output
    assert all(canary not in output for canary in _CANARIES.values())


def test_m3u_credential_bearing_source_never_reaches_captured_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    source = (
        f"https://provider.example/list.m3u?username={_CANARIES['username']}"
        f"&password={_CANARIES['password']}&token={_CANARIES['token']}"
    )
    loader = M3USourceLoader(_FailingHttpClient())  # type: ignore[arg-type]
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(M3USourceError):
            asyncio.run(loader.load(source))

    output = caplog.text
    assert "provider.example" in output
    assert all(canary not in output for canary in _CANARIES.values())


@pytest.mark.asyncio
async def test_local_m3u_path_is_not_logged(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    path = tmp_path / f"playlist-{_CANARIES['password']}.m3u"
    path.write_text("#EXTM3U\n", encoding="utf-8")
    loader = M3USourceLoader(_FailingHttpClient())  # type: ignore[arg-type]
    with caplog.at_level(logging.DEBUG):
        await loader.load(str(path))
    assert _CANARIES["password"] not in caplog.text
    assert "source_kind=local_file" in caplog.text


def test_artifact_audit_never_prints_matched_secret_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    artifact = tmp_path / "sample.exe"
    artifact.write_bytes(f"Bearer {_CANARIES['token']}_ABC123456789".encode())
    monkeypatch.setattr(sys, "argv", ["audit_windows_artifact.py", "--exe", str(artifact)])

    assert audit_windows_artifact.main() == 1
    output = capsys.readouterr().out
    assert output.strip() == "artifact_audit=FAIL"
    assert _CANARIES["token"] not in output
    assert "secret_findings=" not in output
    assert "finding_count=" not in output


def test_sanitize_exception_returns_type_and_safe_summary() -> None:
    safe = sanitize_exception(RuntimeError(f"password={_CANARIES['password']}"))
    assert safe.startswith("RuntimeError:")
    assert _CANARIES["password"] not in safe
