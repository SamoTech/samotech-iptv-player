# Fixes Applied

## Audit commit

All fixes in this report are included in commit `ed4f8a4`, pushed to `origin/main`. No authorized provider credentials were added to source, tests, reports, or committed files. The changes follow the policy of fixing only confirmed defects and preserving ordinary provider behavior.

## Security and error-boundary fixes

| Finding | Technical change | Regression evidence |
|---|---|---|
| F-HTTP-001 | `AsyncHttpClient` no longer reads or embeds HTTP error response bodies in 4xx/5xx exceptions. Error messages use the HTTP method, redacted URL, and status only; unsafe exception causes are suppressed. | `tests/test_http_session_lifecycle.py` asserts response-body canaries, query credentials, and exception causes are absent. |
| F-MAG-001 | Legacy MAG 4xx/retry errors use a safe path and static category; network logging records exception type rather than raw message; unsafe causes are suppressed. | MAG connection canary tests assert body/query tokens and portal context do not leak. |
| F-TRANSLATION-001 | Canonical and MAG error translators use static safe messages and no longer interpolate arbitrary upstream exception text. The adapter authentication fall-through was corrected to raise translated failures. | Application safe-boundary tests assert canary exception text is absent from logs and response DTOs. |
| Domain validation | URL and StreamURI invalid-input errors use `safe_label`; central URI redaction recognizes all URI schemes, including `file://`. | Domain canary tests assert credential-bearing invalid values do not appear in validation exceptions. |
| Application boundaries | Raw exception logging and `str(exc)` response messages were replaced with centralized safe diagnostics and `safe_user_message()` in provider authentication, EPG, refresh, stream resolution, favorites, and channel loading use cases. | `tests/test_safe_error_boundaries.py` covers use-case logs and DTOs. |

## Networking and provider fixes

| Finding | Technical change | Regression evidence |
|---|---|---|
| F-NET-001 | Canonical `AsyncHttpClient` does not retry POST requests. Legacy `MAGConnection` exits its retry loop after the first POST failure. GET/read retry behavior remains unchanged. | HTTP and MAG request-count tests assert one attempt and no retry sleep for POST. |
| Response bounds | Canonical successful text/JSON/bytes reads are incrementally bounded. Malformed JSON is translated to a safe client error. Legacy MAG response reads are bounded at 16 MiB. | HTTP size and malformed-JSON tests plus existing MAG body-progress tests pass. |
| F-XTREAM-001 | Xtream stream URL `kind`, username, password, stream ID, and extension segments are percent-encoded with `quote(..., safe='')`. | `tests/test_infra_xtream_request_builder.py` covers slash, query, and fragment delimiters. |
| F-MAG-002 | `_schedule_refresh()` excludes `asyncio.current_task()` from cancellation, preventing a refresh coroutine from cancelling itself while scheduling its successor. | `test_refresh_loop_reschedules_without_cancelling_current_task` passes. |

## Parser and resource-bound fixes

| Finding | Technical change | Regression evidence |
|---|---|---|
| F-M3U-001 | M3U remote reads pass a 64 MiB maximum to the shared HTTP client. Local files are read as at most 64 MiB plus one byte before UTF-8 decoding. Parser instances enforce positive configurable character and entry limits, with defaults of 50 million characters and 500,000 entries. | M3U parser tests reject oversized documents and excessive entries; source-loader and adapter suites pass. |
| XML security scanner finding | Runtime XML parsing uses `defusedxml.ElementTree.ParseError`/`fromstring`; ElementTree types are represented by a type-checking-only protocol and do not invoke standard-library parsing. | XMLTV tests pass and Bandit reports zero findings. |

## VLC lifecycle fixes

| Finding | Technical change | Regression evidence |
|---|---|---|
| F-VLC-001 | Superseded media is stopped and released before replacement. Failed media creation/play attempts clean up partial native media. Native event callbacks are detached on close using the stored event type/callback identities. | VLC adapter lifecycle tests were updated for the stop-before-replace contract and event detachment; the full focused VLC suite passes. |

These changes do not alter playback selection policy, provider protocol selection, or supported media schemes. They constrain cleanup and stale-resource behavior only.

## CI and release fix

| Finding | Technical change | Regression evidence |
|---|---|---|
| F-CI-001 | `.github/workflows/windows-portable-build.yml` now grants `contents: read` at workflow scope. Tagged publication moved to a dependent `publish-release` job with `contents: write`, after artifact validation and download by SHA. Release notes are included in the uploaded artifact. | `tests/test_windows_packaging_config.py` asserts the permission split, dependency, release action, and release-note path. |

## Verification record

The final successful command set was:

```text
.venv/bin/ruff check src/ tests/ providers/ scripts/
.venv/bin/black --check src/ tests/ providers/
.venv/bin/mypy src/
bandit -r src providers -q
pip-audit -r <direct project dependency manifest>
QT_QPA_PLATFORM=offscreen PYTHONPATH=src .venv/bin/pytest -q --cov=src --cov-report=xml <all non-presentation tests>
.venv/bin/python -m compileall -q src providers
git diff --check
```

All listed commands completed successfully at the final verification point. The Windows build and executable checks were not run because the Linux host has no PowerShell, Windows runtime, or official VLC Windows DLL tree. They remain blocking workflow gates and are reported as **NOT VERIFIED — ENVIRONMENT LIMITATION**.

## References

[1]: build/confirmed_findings.md "Evidence ledger"
[2]: ../../src/samotech_iptv/infrastructure/network/http_client.py "Canonical transport changes"
[3]: ../../providers/mag/connection.py "Legacy transport changes"
[4]: ../../src/samotech_iptv/infrastructure/parsing/m3u_source_loader.py "Bounded M3U source loading"
[5]: ../../src/samotech_iptv/infrastructure/parsing/m3u_parser.py "Bounded M3U parsing"
[6]: ../../src/samotech_iptv/infrastructure/providers/xtream_request_builder.py "Xtream path encoding"
[7]: ../../providers/mag/session.py "Refresh task fix"
[8]: ../../src/samotech_iptv/infrastructure/player/vlc_player_adapter.py "VLC lifecycle fix"
[9]: ../../.github/workflows/windows-portable-build.yml "CI permission fix"
