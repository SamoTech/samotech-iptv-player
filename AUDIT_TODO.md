# Complete Forensic Repository Audit Todo List

Source specification: `/home/ubuntu/upload/pasted_content.txt`, read completely through line 1066.

| Order | Task | Dependency | Required evidence | Status |
|---:|---|---|---|---|
| 1 | Sync `main`; record commit, status, OS, Python, dependencies, tools, tree, and file classifications | None | `AUDIT_BASELINE.md` plus raw baseline captures | Complete |
| 2 | Audit architecture, dependency direction, boundaries, coupling, dead code, and global state | 1 | `ARCHITECTURE_AUDIT.md`, dependency/call graph | In progress |
| 3 | Trace canonical `src/samotech_iptv` versus legacy `providers` implementations and packaging/execution paths | 1, 2 | Import graph, packaged-file analysis, migration classification | Pending |
| 4 | Trace every MAG credential path through storage, handshake, requests, stream resolution, logging, exceptions, diagnostics, and shutdown | 2, 3 | Security flow map, findings, regression tests | Pending |
| 5 | Audit HTTP exceptions and response-body leakage; remove unsafe raw bodies if confirmed | 2, 4 | Network source review, failing-before/fixed-after tests | Pending |
| 6 | Review every relevant domain and application file/function for correctness, security, concurrency, lifecycle, and type safety | 1, 2 | Layer findings and tests | Pending |
| 7 | Audit networking, Xtream, MAG/Stalker, M3U, XMLTV, retries, redirects, response limits, and cancellation | 3–6 | Protocol and network findings | Pending |
| 8 | Deeply audit VLC/player state, callbacks, tasks, recovery, release, shutdown, and thread affinity | 2, 6, 7 | Lifecycle trace and race/concurrency tests | Pending |
| 9 | Audit Qt/qasync UI thread use, dialogs, workers, timers, callbacks, close, and shutdown | 2, 6, 8 | Presentation findings and tests | Pending |
| 10 | Audit SQLite, migrations, transactions, connections, corruption, keyring, plugins, and sensitive persistence | 3–6 | Storage/security findings and tests | Pending |
| 11 | Run dedicated security/dependency/secret tooling: Ruff, MyPy, Bandit, pip-audit, pytest, coverage, CodeQL, and existing scans | 1–10 | Exact commands/results and explicit limitations | Pending |
| 12 | Audit `pyproject.toml`, requirements, lock state, GitHub Actions, PyInstaller, VLC, Qt, reproducibility, and least privilege | 1, 3, 11 | `BUILD_RELEASE_AUDIT.md` evidence | Pending |
| 13 | Review every test module for coverage quality, false positives, mocks, security, Windows, concurrency, and provider gaps; run full suite | 1–12 | `TEST_AUDIT.md`, test totals, coverage | Pending |
| 14 | Classify every confirmed issue by severity and priority; do not fix preferences or unconfirmed concerns | 2–13 | Finding ledger with file/symbol/root cause/impact/evidence | Pending |
| 15 | Apply smallest safe fixes for confirmed issues only, preserving public behavior and legacy compatibility where required | 14 | Code diff and root-cause explanation | Pending |
| 16 | Add/update regression tests; run targeted tests, then full suite and static analysis | 15 | Before/after verification evidence | Pending |
| 17 | Re-audit canonical/legacy providers, MAG credentials, HTTP leakage, logs, diagnostics, VLC, async tasks, switching, packaging, security, and tests | 16 | Re-audit search and finding disposition | Pending |
| 18 | Run final complete validation, coverage, security/dependency scans, clean build, smoke test, packaging test, and artifact checks | 16, 17 | Exact command outputs and explicit blocked states | Pending |
| 19 | Write `FULL_CODE_AUDIT.md`, `SECURITY_AUDIT.md`, `ARCHITECTURE_AUDIT.md`, `STABILITY_CONCURRENCY_AUDIT.md`, `TEST_AUDIT.md`, `BUILD_RELEASE_AUDIT.md`, `FIXES_APPLIED.md`, and `FINAL_AUDIT_REPORT.md` | 14–18 | Eight required reports | Pending |
| 20 | Commit justified changes, push without force/empty commits, verify remote/clean state, and deliver final audit | 19 | Final SHA, clean repository, final report | Pending |

## Fixed audit rules

1. Do not delete `providers/` until import, packaging, execution, security, and test evidence proves it is safe.
2. Do not treat sanitized logging as sufficient if an unsafe exception or plaintext persistence path exists upstream.
3. Do not include actual credentials, provider payloads, tokens, cookies, private URLs, or authorized identifiers in reports, tests, commits, or logs.
4. Do not suppress CodeQL, Ruff, MyPy, Bandit, or dependency findings merely to obtain green CI.
5. Do not claim a command passed unless it completed successfully; classify environment failures as **NOT VERIFIED — ENVIRONMENT LIMITATION**.
6. Do not perform unrelated refactoring or change public behavior without a confirmed technical reason.
