# Stability and Concurrency Audit

## Result

**Stability: PASS for the Linux-verifiable application and test scope.** The audit traced asyncio task ownership, qasync shutdown, provider session refresh, HTTP retries, SQLite worker operations, VLC media generations, native event callbacks, timers, and stale UI requests. Confirmed lifecycle defects were fixed and regression-tested. The Windows native VLC and packaged-executable portions remain **NOT VERIFIED — ENVIRONMENT LIMITATION**.

## Async and task ownership

Presentation tasks are created through `presentation/task_owner.py`. Owners track tasks, cancel them on close or destruction, consume task results, and provide an application-wide shutdown function. PlayerShell invalidates request generations and subtitle session tokens when provider/media identity changes. Results from stale operations are discarded instead of overwriting current UI state. Timers are stopped during close. Desktop runtime awaits the close callback before the qasync loop exits.

Dialogs use the same owned-task mechanism for refresh, health, favorite, and library operations. Synchronous health checks and local subtitle inspection run through worker threads. Cancellation is explicitly re-raised in async boundaries rather than swallowed as a generic error.

## Provider and HTTP concurrency

The shared HTTP session has explicit open/close ownership and cancellation-safe request handling. GET/read operations may retry according to the configured policy; POST operations now fail after the first attempt in both canonical and legacy transport. This avoids replaying ambiguous provider mutations. Response reads are bounded and connection contexts are exited on every response path.

`MAGSession` stores token state in memory and maintains a refresh task. The confirmed defect was self-cancellation: refresh completion called `_schedule_refresh`, which could cancel the currently running `_refresh_loop`. The fix excludes `asyncio.current_task()` from cancellation and keeps cancellation for an older distinct task. The new test verifies a refresh loop produces a live successor task. Session close cancels and awaits the refresh task.

The provider runtime cache closes invalidated instances asynchronously and continues shutdown when one provider close fails. This is intentional best-effort shutdown behavior; it prevents one broken provider from preventing other providers, the player, or HTTP resources from closing. Shutdown diagnostics are safe and do not expose provider payloads.

## VLC lifecycle

The VLC adapter uses media generations and session tokens to reject stale callbacks. The audit confirmed and fixed three cleanup paths: replacing an existing media now stops and releases the superseded media, failed media creation/play attempts release any partially created media, and native event subscriptions detach during close. Release and stop paths are idempotent and isolate native backend exceptions.

Focused lifecycle tests cover recording, stop, recovery, close, event detachment, stale callbacks, and release expectations. No confirmed double-release or use-after-release remained after the fix. Native VLC behavior itself is covered by repository probes and the Windows workflow, but cannot be executed on this Linux host.

## Qt/qasync behavior

The main window and PlayerShell remain thin presentation orchestration layers. Provider calls are awaited in owned tasks rather than performed synchronously in widget callbacks. Long-running local inspection and health checks are moved to `asyncio.to_thread`. Close invalidates state, stops timers, cancels owned UI tasks, and composition shutdown awaits all owners before closing providers, player, and HTTP.

The excluded Windows presentation test modules are not silently treated as passing. Their collection caused a fatal native Qt access violation in the prior audit environment; CI deliberately selects the non-presentation corpus. This is a test-harness/platform limitation and a release validation item, not an application stability pass.

## SQLite concurrency

Each SQLite operation uses a fresh connection in a worker thread. The connection context manager commits on success, rolls back on `BaseException`, and closes in `finally`. SQL is parameterized. XMLTV binding replacement is transactionally atomic. This avoids sharing SQLite connections across asyncio worker threads. The trade-off is serialized database work through SQLite locking rather than a persistent connection pool, which is suitable for the desktop workload.

## Confirmed stability findings

| Finding | Root cause | Fix and evidence |
|---|---|---|
| F-NET-001 | POST retries could replay ambiguous operations. | Canonical and legacy no-retry branches; request-count tests pass. |
| F-MAG-002 | Refresh scheduler cancelled its own task. | Current-task exclusion; refresh lifecycle test passes. |
| F-VLC-001 | Superseded media and native subscriptions were not fully cleaned. | Stop/release and event-detach paths; VLC suite passes. |
| F-M3U-001 | Oversized input could cause unbounded parse work. | Source, character, and entry bounds; parser tests pass. |

## Residual risks

Concurrent calls to a single live provider can still be initiated by separate application operations, but no confirmed data race or unsafe mutation was demonstrated after tracing the cache, session, and adapter boundaries. Future work may serialize authentication and token refresh with an explicit per-session lock if protocol-specific concurrency evidence emerges. That change was not made because the audit policy permits only confirmed defects.

## References

[1]: src/samotech_iptv/presentation/task_owner.py "Presentation task ownership"
[2]: src/samotech_iptv/presentation/player_shell.py "PlayerShell task, timer, and close lifecycle"
[3]: src/samotech_iptv/desktop_runtime.py "qasync runtime owner"
[4]: src/samotech_iptv/desktop_composition.py "Application shutdown order"
[5]: src/samotech_iptv/infrastructure/player/vlc_player_adapter.py "VLC lifecycle implementation"
[6]: tests/test_infra_vlc_player_adapter.py "VLC lifecycle regression tests"
[7]: providers/mag/session.py "MAG token refresh lifecycle"
[8]: tests/providers/mag/test_auth_state_machine.py "MAG session state tests"
[9]: src/samotech_iptv/infrastructure/database/sqlite_connection.py "SQLite commit/rollback/close contract"
[10]: tests/test_infra_sqlite_connection_lifecycle.py "SQLite lifecycle tests"
