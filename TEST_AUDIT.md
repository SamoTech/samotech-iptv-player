# Test Audit

## Result

**Testing: PASS for the executed non-presentation corpus; CONDITIONAL for native Windows and presentation-specific validation.** The audit reviewed unit, integration, provider, parser, security, storage, VLC, packaging-configuration, and workflow-configuration tests. The final full non-presentation run completed successfully with coverage XML generation.

## Test corpus and executed verification

The repository’s tests cover domain invariants, application use cases, canonical and legacy providers, HTTP sessions, M3U/XMLTV parsers, SQLite repositories, keyring behavior, VLC lifecycle, task ownership, packaging configuration, release-note generation, and sensitive logging. The final command selected every `tests/test_*.py` file except `test_presentation_*.py`, with `QT_QPA_PLATFORM=offscreen`, coverage enabled, and `PYTHONPATH=src`.

| Verification | Result |
|---|---|
| Ruff over source, tests, providers, scripts | PASS |
| Black format check | PASS; 367 files unchanged |
| MyPy over source | PASS; 220 source files checked |
| Bandit over `src providers` | PASS; zero findings |
| Direct-manifest pip-audit | PASS; no known vulnerabilities |
| Full non-presentation pytest | PASS; completed at 100% with no failures |
| Coverage XML generation | PASS; `coverage.xml` written |
| Python compileall over source and providers | PASS |
| `git diff --check` before commit | PASS |

## Regression coverage added or updated

The security boundary tests use unique canary values to prove that response bodies, query credentials, application exception messages, invalid URL values, and stream-URI values are absent from logs, exceptions, and response DTOs. HTTP lifecycle tests cover successful bounded text/bytes reads, malformed JSON translation, error-body non-disclosure, query redaction, and POST no-retry attempt counts.

Legacy MAG tests cover 4xx/5xx non-disclosure, bounded body behavior, timeout classification, POST no-retry semantics, and refresh/session behavior. M3U tests cover document character limits and entry limits. Xtream request-builder tests cover path-segment encoding for slash, query, and fragment delimiters. VLC tests were updated for explicit stop-before-replace behavior and event detachment. Packaging tests assert that the workflow’s build job is read-only and the dependent publish job is the only write-scoped job.

## Test-quality observations

The test suite generally uses deterministic fakes and local aiohttp servers rather than live provider credentials. Sensitive values are synthetic canaries. Provider protocol variations are tested through explicit mocked payloads and state transitions. SQLite tests verify both normal operation and rollback/connection closure. Native VLC tests use fakes for deterministic adapter lifecycle and separate probes for actual native behavior.

The primary test gap is platform-specific execution. Presentation modules that exercise full native Qt had a proven fatal collection issue in the prior environment and remain excluded from CI. The Windows workflow runs the non-Qt corpus and separate native VLC/application probes on a Windows runner, but those jobs were not executable on this Linux host. This limitation is documented instead of converted into a pass.

## Findings and disposition

No false-positive regression was accepted as proof of a fix. Where a test could not be made to fail before the fix without destabilizing the shared fixture, the test asserts the post-fix contract directly and the defect was independently traced to the pre-fix code path. Full verification was rerun after the final XMLTV typing and Bandit cleanup changes.

The remaining recommended testing action is to run the tagged Windows portable workflow and the release-artifact acceptance workflow, then retain their logs and generated SHA256 metadata alongside the release record.

## References

[1]: tests/test_safe_error_boundaries.py "Application and domain safety canaries"
[2]: tests/test_http_session_lifecycle.py "HTTP lifecycle and bounded response tests"
[3]: tests/providers/mag/test_connection.py "MAG transport regression tests"
[4]: tests/providers/mag/test_auth_state_machine.py "MAG authentication and refresh tests"
[5]: tests/test_infra_b2_m3u_parser.py "M3U parser tests"
[6]: tests/test_infra_vlc_player_adapter.py "VLC adapter lifecycle tests"
[7]: tests/test_infra_sqlite_connection_lifecycle.py "SQLite lifecycle tests"
[8]: tests/test_windows_packaging_config.py "Packaging and workflow contract tests"
[9]: .github/workflows/ci.yml "CI test selection and gates"
[10]: .github/workflows/windows-portable-build.yml "Windows native and packaged validation gates"
