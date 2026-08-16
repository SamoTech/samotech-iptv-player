# Player 2 Runtime Validation

## Execution context

Validation was executed in the Linux sandbox on **2026-08-16** with `QT_QPA_PLATFORM=offscreen` for Qt tests. The repository uses Python 3.12, PySide6, qasync, python-vlc, pytest, Ruff, Black, and mypy. The supported media backend remains libVLC.

## Quality-gate matrix

| Gate | Command or evidence | Result |
| --- | --- | --- |
| Full deterministic suite | `QT_QPA_PLATFORM=offscreen uv run pytest -q --cov=src/samotech_iptv --cov-report=term-missing --cov-report=json` | **PASS**; 328 tests passed; aggregate coverage 71% |
| Black | `uv run black --check src tests` | **PASS**; 328 files unchanged after formatting the new probe |
| Ruff | `uv run ruff check src tests` | **PASS** |
| mypy | `uv run mypy src` | **PASS**; no issues in 212 source files |
| Diff whitespace | `git diff --check` | **PASS** |
| PlayerShell native probe | `QT_QPA_PLATFORM=offscreen uv run python tests/player_shell_native_probe.py` | **PASS**; stale identity, provider invalidation, keyboard, controls, and artwork checks passed |
| PlayerShell performance | `QT_QPA_PLATFORM=offscreen uv run python tests/player_shell_performance_probe.py` | **PASS**; 10,000, 50,000, and 100,000 catalogue checkpoints completed |
| Windows-only VLC probe on Linux | `QT_QPA_PLATFORM=offscreen uv run python tests/vlc_native_lifecycle_probe.py` | **SKIP** with `native_vlc_lifecycle=SKIP reason=windows_required` |
| Local track-shape probe on Linux | `uv run python tests/vlc_track_shape_probe.py` | **BLOCKED**; python-vlc imported, but the sandbox has no loadable native `libvlc_new` function |
| Populated authorized provider | No real populated provider execution in this environment | **NOT EXECUTED** |

## Control and state evidence

The adapter tests cover valid state transitions, stale and duplicate event handling, position/duration reads, millisecond and fractional seek validation, volume and mute, typed audio and subtitle track parsing, native selection, subtitle disable, restart, and aspect-ratio validation. The PlayerShell probe verifies that Movie mode enables seek controls and formats `0:30 / 2:00`, relative seek dispatches through the application-level player double, and Live mode displays `LIVE` while disabling the seek slider.

The native VLC probe remains intentionally provider-free and local-media-only. Its Windows path now checks all required lifecycle, position, seek, volume, mute, track, subtitle, and aspect-ratio method names before inspecting local-media track descriptions. On Linux the probe exits successfully only as an explicit platform skip; no Linux result is presented as Windows evidence.

## History and resume evidence

Application tests verify provider-scoped records, derived watched percentage, lifecycle timestamps, completion normalization, and the rule that Live unknown-duration history is never completed. SQLite tests verify backward-compatible schema initialization and round-trip of provider identity, position, duration, percentage, completion, and timestamps. Playback tests verify that a matching incomplete Movie record restores its stored position, while Live playback does not invoke resume.

## Performance checkpoints

The standalone probe completed local model replacement, selection, category filtering, search, no-match search, and clear-search checks through 100,000 items. The observed 100,000-item values were approximately 12.34 ms for model replacement, 0.105 ms for selection, 19.001 ms for category filtering, 93.222 ms for search, 94.506 ms for no-match search, and 5.099 ms for clear search. These are local offscreen probe observations, not a claim of network or production-provider performance.

## Security review

The changed-file scan found no exact matches for the previously supplied provider hostname, username, or password. Credential and token key matches were limited to existing safe application terminology, tests, audit text, or dependency metadata; no new secret-bearing value was added. URL literals in changed tests and audits are synthetic fixtures or documentation references. The UI path continues to avoid raw provider URLs, credentials, and tokens.

## Platform and acceptance limitations

Windows validation is **NOT EXECUTED** from this Linux environment. The Windows-only native VLC probe is a deliberate skip, not a pass claim. Real populated authorized-provider validation is **NOT EXECUTED**. The prior provider architecture, MAG transport, M3U/Xtream adapters, shared VLC lifecycle, qasync ownership, and Live EOF recovery policy were not replaced or silently widened during Player 2 work.
