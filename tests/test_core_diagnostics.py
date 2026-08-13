from __future__ import annotations

import logging

import pytest

from samotech_iptv.core.diagnostics import DiagnosticTrace, redact_url


def test_debug_trace_emits_stages_timing_and_summary(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG, logger="samotech_iptv.diagnostics"):
        trace = DiagnosticTrace("LOAD_CHANNELS", "news", "XtreamProviderAdapter")
        trace.start()
        with trace.stage("HTTP request", status=200, records=187):
            pass
        trace.result("PASS", records_received=187, records_translated=187)

    output = caplog.text
    assert "[IPTV] PROVIDER OPERATION" in output
    assert "HTTP request: PASS" in output
    assert "0." in output
    assert "OPERATION RESULT" in output
    assert "records_received=187" in output


def test_debug_trace_suppresses_verbose_output_when_disabled(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO, logger="samotech_iptv.diagnostics"):
        trace = DiagnosticTrace("LOAD_CHANNELS", "news", "XtreamProviderAdapter")
        trace.start()
        with trace.stage("HTTP request", status=200):
            pass
        trace.result("PASS", records_received=1)

    assert "[IPTV] PROVIDER OPERATION" not in caplog.text
    assert "OPERATION RESULT" not in caplog.text


def test_debug_trace_logs_full_traceback_and_safe_error(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG, logger="samotech_iptv.diagnostics"):
        trace = DiagnosticTrace("LOAD_CHANNELS", "news", "XtreamProviderAdapter")
        with pytest.raises(ValueError):
            with trace.stage("Domain translation", record=123, field="logo_url"):
                raise ValueError("Invalid URL http://user:password@example.test/path?token=secret")

    assert "Domain translation: FAIL" in caplog.text
    assert "ValueError" in caplog.text
    assert "Traceback (most recent call last)" in caplog.text
    assert "password" not in caplog.text
    assert "token=secret" not in caplog.text
    assert "http://example.test/path" in caplog.text


def test_redact_url_removes_userinfo_and_query() -> None:
    assert redact_url("http://user:password@example.test:8080/path?token=secret") == (
        "http://example.test:8080/path"
    )


def test_safe_exception_text_redacts_bare_credentials() -> None:
    from samotech_iptv.core.diagnostics import safe_label

    safe = safe_label("username=user password=secret token=abc")
    assert safe == "username=<REDACTED> password=<REDACTED> token=<REDACTED>"
