# Full Code Audit

## Repository and audit basis

This report records the completed forensic audit of `SamoTech/samotech-iptv-player` on branch `main`. The audited fix commit is `ed4f8a4` (`security: harden provider boundaries and release workflow`), based on the prior baseline commit `65e4ff8eab40cf770799a5e2139f8497778362cc`. The audit followed the required **AUDIT → TRACE → VERIFY → CLASSIFY → FIX → TEST → RE-AUDIT → REPORT** sequence. The baseline, dependency-ordered work list, import topology, legacy-provider trace, and finding ledger are retained in [`AUDIT_BASELINE.md`](AUDIT_BASELINE.md), [`AUDIT_TODO.md`](AUDIT_TODO.md), and the ignored working evidence under `build/`.

The implementation is a Python 3.12 desktop application using PySide6, qasync, aiohttp, python-vlc, SQLite, and OS keyring storage. The source tree contains the canonical `src/samotech_iptv` package and a deliberately retained compatibility package under `providers/`. The latter remains required at runtime because `mag_adapter.py` lazily imports `providers.mag.provider.MAGProvider`; both trees are intentionally included in packaging.

## Executive outcome

The repository has a sound hexagonal/ports-and-adapters architecture, strong credential boundaries, comprehensive focused regression coverage, and passing Linux quality gates. The audit confirmed and fixed security-data disclosure, unsafe retry, unbounded playlist, Xtream path-construction, MAG refresh-task, VLC lifecycle, and CI privilege findings. The principal remaining limitation is environmental: the Windows PyInstaller/VLC artifact cannot be built or executed on this Linux audit host because no Windows runner, PowerShell, or official Windows VLC runtime is available. Those gates remain blocking in GitHub Actions and are therefore reported as **not verified locally**, not as passed.

| Area | Result | Evidence and disposition |
|---|---|---|
| Architecture | PASS | AST graph covered 243 modules; zero cycles and zero forbidden layer edges. Legacy MAG dependency is documented and packaged intentionally. |
| Domain/application | PASS | Value-object validation, safe DTO boundaries, stale-operation guards, and static error translation were reviewed and tested. |
| Security | PASS with scanner caveat | Bandit completed with zero findings after verified false-positive annotations; direct-manifest pip-audit reported no known vulnerabilities; secret canary tests pass. |
| Networking | PASS | Redirect and session behavior were traced, response bodies are bounded, POST is not retried, and exceptions contain safe URL/status information only. |
| Providers | PASS | Xtream, M3U, canonical MAG, and legacy MAG compatibility paths were traced with malformed-response and lifecycle tests. |
| M3U/XMLTV | PASS | M3U now has byte, character, and entry limits. XMLTV uses defusedxml with bounded parsing and no XXE path. |
| VLC | PASS | Superseded media is stopped and released, failed media is cleaned up, and native event subscriptions detach on close. |
| UI/qasync | PASS | Owned tasks, generation guards, off-thread blocking work, timer shutdown, and awaited application shutdown were verified. |
| Database | PASS | Short-lived SQLite connections commit/rollback deterministically, close on all paths, and persist no credentials. |
| Testing | PASS | Full non-presentation suite and coverage run completed successfully. Windows presentation tests remain excluded because native Qt collection crashes are documented. |
| Packaging | CONDITIONAL | Spec syntax, resource declarations, version metadata, and workflow gates were reviewed; actual Windows artifact execution is not locally verifiable. |
| CI/CD | PASS | Build permissions are read-only; only the dependent tagged publication job has `contents: write`. |

## Architecture and dependency trace

The application follows a one-way dependency direction: domain value objects and entities are independent of infrastructure; application use cases depend on ports; infrastructure implements ports and integrates HTTP, keyring, SQLite, VLC, and provider protocols; presentation composes use cases and owns UI tasks. The AST import graph found no circular imports and no forbidden reverse-layer edges. Provider-specific behavior is contained in provider adapters and translators rather than generic domain code.

The canonical provider implementation is under `src/samotech_iptv/infrastructure/providers`. The top-level `providers/` package is legacy compatibility code used by the canonical MAG adapter through a lazy import. It is not dead code and was not deleted. The PyInstaller spec collects both package families. This is an intentionally incomplete migration boundary, but it is explicit, tested, and isolated at `mag_adapter._ensure_provider()`.

## Credential and data-flow audit

Xtream username/password values are held in an ephemeral `Credential` value object, persisted through the credential-store port, and not serialized into SQLite metadata. MAG MAC and credential material follow the same boundary into the keyring-backed store; session tokens remain in memory and are not persisted. Legacy `MAGCredentials` and canonical credential representations redact secrets in `repr()`. Provider metadata stores only provider ID, type, sanitized base URL, active status, capabilities, and source-security status.

The audit searched logs, exception construction, diagnostic capture, response DTOs, URL validation, provider representations, SQLite schemas, and packaging metadata. Confirmed raw response-body and exception-text leakage paths were removed. Regression tests use canaries to prove that response bodies, query credentials, application exception payloads, and invalid credential-bearing URLs do not cross normal error boundaries.

## Networking and provider audit

The canonical HTTP client owns the shared aiohttp session and requires explicit open/close lifecycle. It preserves cancellation, applies timeout configuration, uses sanitized URLs in logs and exceptions, bounds successful response bodies, and converts malformed JSON into a safe `HttpClientError`. HTTP 4xx responses are not retried. POST requests are now never retried, preventing ambiguous provider mutations from being replayed. GET/read operations retain configured retry behavior.

Xtream API query parameters are encoded with `urlencode`. Playback URL path segments are now encoded with `quote(..., safe="")`, protecting credentials and stream identifiers from path, query, and fragment delimiter injection while preserving ordinary URLs. M3U remote and local source reads are bounded, and M3U parser expansion is bounded by configurable character and entry limits. XMLTV uses `defusedxml.ElementTree.fromstring`, rejects unsafe or malformed documents, and limits document characters and mapped entries.

Legacy MAG transport was reviewed for session ownership, bounded incremental body reads, safe status/error classification, retry behavior, and shutdown. POST requests fail after the first attempt. MAG refresh scheduling no longer cancels its own running task. Native MAG stream URL validation permits only supported media schemes and logs scheme metadata rather than the URL.

## Player and presentation audit

`VlcPlayerAdapter` uses media generations and session tokens to suppress stale callbacks. The audit confirmed cleanup for superseded media, failed media creation/play attempts, native event subscription detachment, idempotent stop/release, and task cancellation. The Qt shell uses `create_owned_task` for asynchronous work, invalidates request generations when content changes, stops timers during close, and cancels owned tasks before Qt disposal. Blocking health checks and local subtitle inspection are moved to worker threads. The qasync runtime and desktop composition await task-owner, provider-cache, player, and HTTP shutdown in deterministic order.

The player state machine and native event callbacks were verified against focused lifecycle tests covering stop, recovery, recording, stale events, close, and release. The audit found no confirmed use-after-release or event-subscription leak after the fixes.

## SQLite and persistence audit

Each repository opens a short-lived connection in a worker thread, uses parameterized SQL, commits successful operations, rolls back exceptions, and closes the connection in `finally`. XMLTV mapping replacement is performed in one transaction with foreign keys enabled. Migrations add only expected non-secret columns. Input reconstruction failures become safe `StorageError` messages. SQLite schemas contain no password, MAC, token, cookie, authorization, or stream-URL credential fields.

The storage lifecycle suite verifies connection closure and rollback. The remaining design trade-off is per-operation connection creation rather than a pooled writer; this is appropriate for a desktop workload and avoids cross-thread connection ownership.

## Confirmed findings and fixes

| Finding | Severity / priority | Root cause | Fix and verification |
|---|---:|---|---|
| F-HTTP-001 | High / P0 | HTTP errors retained raw body and raw URL. | Static safe exceptions, sanitized URL, suppressed unsafe cause; canary tests pass. |
| F-MAG-001 | High / P0 | Legacy MAG error paths propagated unsafe URL/message content. | Safe path, static categories, type-only network logging; canary tests pass. |
| F-TRANSLATION-001 | High / P0 | Translators interpolated arbitrary upstream exception text. | Static domain messages and `from None`; application boundary tests pass. |
| F-NET-001 | Medium / P1 | POST operations were eligible for retries. | POST no-retry in canonical and legacy transports; attempt-count tests pass. |
| F-M3U-001 | Medium / P1 | Playlist reads and parser expansion were unbounded. | 64 MiB source bound, 50M-character parser bound, 500k-entry bound; parser tests pass. |
| F-XTREAM-001 | Medium / P1 | Credential and stream path segments were interpolated raw. | Percent-encode every segment; delimiter regression test passes. |
| F-MAG-002 | Medium / P1 | Refresh completion could cancel its own task. | Current-task exclusion; refresh successor test passes. |
| F-VLC-001 | Medium / P1 | Superseded media and native event subscriptions could remain attached. | Stop/release transition and event detach; VLC suite passes. |
| F-CI-001 | High / P0 | Windows build job had release write permission. | Read-only build job plus dependent write-scoped publish job; workflow tests pass. |

## Verification record

The following commands completed successfully at commit `ed4f8a4`:

```text
.venv/bin/ruff check src/ tests/ providers/ scripts/
.venv/bin/black --check src/ tests/ providers/
.venv/bin/mypy src/
bandit -r src providers -q
pip-audit -r <direct project dependency manifest>
QT_QPA_PLATFORM=offscreen PYTHONPATH=src .venv/bin/pytest -q --cov=src --cov-report=xml <all test_*.py excluding test_presentation_*.py>
.venv/bin/python -m compileall -q src providers
 git diff --check
```

The final non-presentation test run completed at 100% with no failures and wrote `coverage.xml`. The focused regression suites also passed after each affected fix. The authorized fixture credentials were scanned and were absent from the repository and committed files.

## Limitations and remaining actions

The actual Windows build, bundled VLC native lifecycle probe, packaged executable smoke test, sanitized-PATH execution, and release-artifact acceptance matrix are **NOT VERIFIED — ENVIRONMENT LIMITATION** on this Linux host. The GitHub workflow contains blocking gates for those tests and should be run on the next tagged build or manually through the acceptance workflow. Windows presentation test modules remain excluded from CI because their collection caused a proven fatal native Qt access violation; this is documented as a platform-specific test-harness limitation rather than silently reported as a pass.

## References

[1]: AUDIT_BASELINE.md "Audit baseline"
[2]: AUDIT_TODO.md "Dependency-ordered audit work list"
[3]: ../../src/samotech_iptv/infrastructure/network/http_client.py "Canonical HTTP client"
[4]: ../../providers/mag/connection.py "Legacy MAG transport"
[5]: ../../src/samotech_iptv/infrastructure/player/vlc_player_adapter.py "VLC player adapter"
[6]: ../../src/samotech_iptv/desktop_composition.py "Desktop resource composition and shutdown"
[7]: ../../.github/workflows/windows-portable-build.yml "Windows build and release workflow"
[8]: ../../tests/test_http_session_lifecycle.py "HTTP lifecycle and disclosure regression tests"
[9]: ../../tests/providers/mag/test_connection.py "MAG transport regression tests"
[10]: ../../tests/test_safe_error_boundaries.py "Application and domain disclosure regression tests"
