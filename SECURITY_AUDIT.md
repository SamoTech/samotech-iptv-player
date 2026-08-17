# Security Audit

## Scope and conclusion

This audit covered credential flow, logging, diagnostics, exception translation, URL construction, HTTP behavior, provider sessions, XML parsing, local-file access, SQLite persistence, dynamic imports, subprocess usage, DLL/resource loading, dependencies, and CI permissions. The audited commit is `ed4f8a4`.

**Security result: PASS for the audited Linux-verifiable scope, with Windows artifact execution remaining not verified due to the host environment.** No authorized test credentials are present in the repository. Bandit completed with zero findings after seven narrowly justified annotations for MAG state markers and empty pre-authentication fields. `pip-audit` against the direct project dependency manifest reported no known vulnerabilities. The initial global-environment scan reported unrelated packages not declared by the project; those were not treated as application findings.

## Credential flow

The authoritative flow is `Credential` domain value object → credential-store port → OS keyring adapter → provider adapter/session. Provider metadata and SQLite repositories do not persist passwords, MAC addresses, session tokens, cookies, or authorization headers. MAG session tokens exist only in memory and are cleared on invalidation and shutdown. `repr()` methods for canonical and legacy credential objects redact password/token material and sanitize portal URLs.

The audit searched username, password, MAC, authorization, token, cookie, serial, device ID, and model fields across source, tests, diagnostics, exception construction, repositories, and packaging. The dual canonical/legacy provider structure is a migration boundary, not a second plaintext persistence mechanism: the canonical adapter translates keyring credentials into an ephemeral legacy configuration object, and the legacy runtime is closed through the provider cache.

## Confirmed security findings

| Finding | Risk | Root cause | Remediation |
|---|---|---|---|
| F-HTTP-001 | High / P0 | Canonical HTTP 4xx/5xx exceptions included raw body and raw URL. | Exceptions now contain method, sanitized URL, and status only; response-body canaries and query-credential canaries pass. |
| F-MAG-001 | High / P0 | Legacy MAG transport exposed unsafe URL/message context in exceptions and logs. | Safe path and static categories are used; network logs retain exception type only; canary tests pass. |
| F-TRANSLATION-001 | High / P0 | Error translators copied arbitrary upstream exception strings into domain errors. | Static safe user messages and suppressed exception causes prevent normal-path disclosure. |
| F-XTREAM-001 | Medium / P1 | Xtream credentials and IDs were raw path segments. | Each segment is percent-encoded; delimiter injection regression passes. |
| F-M3U-001 | Medium / P1 | Oversized remote/local M3U content could be retained and expanded without bounds. | 64 MiB source bound plus parser character and entry limits. |
| F-CI-001 | High / P0 | Build workflow had write permission in all contexts. | Build job is read-only; only dependent tagged publication job has write access. |

## HTTP and logging controls

`AsyncHttpClient` redacts URL userinfo and query values before logging or exception construction. Response bodies are not read for HTTP error exceptions. Successful text, bytes, and JSON responses are read incrementally through a hard byte limit. Malformed JSON becomes `HTTP response was not valid JSON` without raw decoder text. Timeout and connection exceptions use sanitized URLs and suppress unsafe causes. Application use cases use centralized `log_exception()` and `safe_user_message()` rather than interpolating arbitrary exception text.

The redaction utility recognizes generic URI schemes, not only HTTP. This is important for `file://`, `rtmp://`, `rtsp://`, and other credential-bearing URI forms. URL and stream-URI validation errors use safe labels instead of echoing raw invalid input.

## XML, URL, and file boundaries

XMLTV and DASH parsing use defusedxml. XMLTV rejects unsafe/malformed documents, bounds input to ten million characters and ten thousand mapped entries, and does not invoke standard-library parsing on untrusted data. M3U local sources are opened as bounded bytes and decoded as UTF-8; remote sources use the shared HTTP client with a 64 MiB limit. Local subtitle selection is restricted to a user-selected file path and validated through the dedicated subtitle inspector; no arbitrary shell execution occurs.

URL values are validated as supported absolute URLs. Xtream query parameters use standard URL encoding. Playback path segments are percent-encoded. MAG stream resolution accepts only `http`, `https`, `rtsp`, and `rtmp` schemes and logs only the scheme. Provider commands and response fields are not written to the history or SQLite schemas.

## Static and dependency security verification

The final security commands were:

```text
bandit -r src providers -q
pip-audit -r <direct project dependency manifest>
.venv/bin/ruff check src/ tests/ providers/ scripts/
.venv/bin/mypy src/
QT_QPA_PLATFORM=offscreen PYTHONPATH=src .venv/bin/pytest -q --cov=src <all non-presentation tests>
```

Bandit finished with zero findings. Its earlier B405 warning on `xml.etree.ElementTree` was eliminated by importing `ParseError` from defusedxml and using a type-checking-only structural protocol. Earlier B105/B106 findings were verified as non-secret classification markers or empty pre-authentication/session-clear values; each is annotated with a specific reason rather than globally suppressing security checks. Direct-manifest pip-audit returned “No known vulnerabilities found.”

## CI supply-chain posture

The top-level Windows workflow now has `contents: read`. Build and validation steps cannot publish releases. The `publish-release` job runs only after the validated artifact job succeeds, downloads the exact artifact by workflow SHA, and alone has `contents: write`. The release workflow pins the official VLC archive checksum and verifies the presence of `libvlc.dll`, `libvlccore.dll`, and plugins before PyInstaller packaging.

## Residual limitations

The Linux host cannot execute the Windows portable EXE, native Windows VLC probe, sanitized Windows PATH matrix, or published-artifact acceptance workflow. These are explicitly **NOT VERIFIED — ENVIRONMENT LIMITATION**, not security passes. The next tagged GitHub Actions run must be reviewed for artifact contents, release metadata, and no-secret bundling.

## References

[1]: src/samotech_iptv/core/safe_logging.py "Central redaction utilities"
[2]: src/samotech_iptv/core/diagnostics.py "Diagnostic capture and safe exception logging"
[3]: src/samotech_iptv/infrastructure/network/http_client.py "Bounded HTTP client"
[4]: src/samotech_iptv/infrastructure/parsing/xmltv_parser.py "Defused and bounded XMLTV parser"
[5]: src/samotech_iptv/infrastructure/parsing/m3u_source_loader.py "Bounded M3U source loader"
[6]: src/samotech_iptv/infrastructure/providers/xtream_request_builder.py "Encoded Xtream URL builder"
[7]: .github/workflows/windows-portable-build.yml "Least-privilege Windows workflow"
[8]: tests/test_safe_error_boundaries.py "Safe exception-boundary tests"
[9]: tests/test_http_session_lifecycle.py "HTTP disclosure and response-bound tests"
[10]: tests/providers/mag/test_connection.py "Legacy MAG disclosure and retry tests"
