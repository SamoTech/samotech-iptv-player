# Player 3 Runtime Validation

**Date:** 2026-08-16  
**Environment:** Linux 6.1.102 x86_64, Python 3.12.3, `QT_QPA_PLATFORM=offscreen`  
**Status:** Deterministic and Linux/offscreen validation complete; Windows and populated-provider acceptance not executed.

## Evidence matrix

| Area | Command or evidence | Result | Classification |
|---|---|---|---|
| Separated full deterministic verification | Non-Qt corpus plus isolated PlayerShell/lifecycle/concurrency invocations | 850 collected tests passed across the compatible groups | PASS |
| VOD/Series concurrency cases | `uv run pytest -q tests/xtream_vod_series_concurrency_cases.py` | 7 passed | PASS |
| VOD/Series concurrency integration | `uv run pytest -q tests/test_xtream_vod_series_concurrency.py` | 1 passed | PASS |
| PlayerShell performance | `uv run python tests/player_shell_performance_probe.py` | 39,753 live; 5,000 content; required sizes 0–100,000 | PASS |
| Performance regression test | `uv run pytest -q tests/test_presentation_01_player_shell_performance.py` | 1 passed | PASS |
| Linux PlayerShell native probe | `uv run python tests/player_shell_native_probe.py` | Exit code 0 | PASS / LIMITED |
| VLC native lifecycle probe | `uv run python tests/vlc_native_lifecycle_probe.py` | `native_vlc_lifecycle=SKIP reason=windows_required` | SKIP / WINDOWS-ONLY |
| Changed-file security scan | Saved deterministic scanner plus `git diff --check` | No known provider literals; no quoted source/doc secret assignments; diff clean | PASS |
| Windows native validation | Not runnable in current environment | Linux host | NOT EXECUTED |
| Populated authorized Xtream | Controlled procedure exists but was not run | No real-provider claim | NOT EXECUTED |
| MAG VOD/Series/Episodes | No compatible authorized portal trace | Non-live contract unproven | NOT EXECUTED |

## Performance evidence

The deterministic probe exercised 39,753 live records, 5,000 Movie/Series/Episode-style content records, and dynamic catalogue sizes of 0, 1, 10, 100, 500, 1,000, 5,000, 10,000, 17,431, 39,753, 50,000, and 100,000. The observed summary was:

| Measure | Result |
|---|---:|
| Initial 39,753-record replacement | 0.421 ms |
| Selection latency | 0.052 ms |
| Empty replacement | 0.189 ms |
| Search-result replacement | 3.599 ms |
| Content-model replacement | 0.036 ms |
| Common search | 3.554 ms |
| Rare search | 2.752 ms |
| No-match search | 2.707 ms |
| Repeated search | 3.287 ms |
| Clear search | 0.022 ms |

These are deterministic local-model measurements, not network, provider, or native decoder benchmarks.

## Qt concurrency note

Qt-heavy modules passed when invoked in compatible isolated groups. A combined offscreen invocation can segfault during cross-module Qt teardown even though the individual modules pass. The Player 3 audit therefore reports the isolated evidence and names the teardown limitation rather than claiming a single aggregate invocation succeeded. The separated verification total is 850 passed tests across the compatible groups.

## Security and privacy evidence

The changed-file security scan checked known authorized-provider literals, credential-bearing URLs, quoted bearer assignments, and quoted secret assignments in changed source and documentation. It reported zero known provider literals, zero literal secret assignments in source/docs, and passed `git diff --check`. Synthetic test fixtures were not treated as provider evidence and no raw provider payloads, tokens, cookies, resolved URLs, or credentials were recorded.

## Acceptance limitations

The environment is Linux and has no `vlc` binary in `PATH`. The Windows-only VLC lifecycle probe correctly reports `SKIP reason=windows_required`. The authorized Xtream procedure in [PLAYER_3_REAL_PROVIDER_ACCEPTANCE.md](PLAYER_3_REAL_PROVIDER_ACCEPTANCE.md) was prepared but not executed. The real-provider result is therefore **NOT EXECUTED**, not PASS or FAIL. MAG VOD/Series/Episodes remain **NOT EXECUTED** because the authorized portal has not established a compatible non-live contract. Catch-up/archive remains **NOT IMPLEMENTED** because no current provider advertises `ProviderCapability.CATCHUP`.

## References

1. [PLAYER_3_FINAL_AUDIT.md](../historical/PLAYER_3_FINAL_AUDIT.md) — complete delivery audit.
2. [PLAYER_3_REAL_PROVIDER_ACCEPTANCE.md](PLAYER_3_REAL_PROVIDER_ACCEPTANCE.md) — controlled acceptance procedure.
3. [PROJECT_STATUS.md](../../PROJECT_STATUS.md) — authoritative current-state matrix.
4. [tests/player_shell_performance_probe.py](../../tests/player_shell_performance_probe.py) — performance evidence source.
