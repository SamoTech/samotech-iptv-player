# Wave 4 Validation Manifest

**Scope:** Pre-version-increment validation of the public-testing implementation.
**Captured before:** any `0.1.6` version, tag, release, or published artifact action.

| Gate | Result | Evidence and interpretation |
|---|---|---|
| New safe diagnostic-report unit tests | PASS | Report shows only allow-listed values, redacts sensitive assignment text, and marks unmeasured values `NOT_AVAILABLE`. |
| libVLC adapter regressions | PASS | Typed snapshot exposes state/protocol/timing/recovery without source URL or query data. |
| Manual provider dialogs | PASS | M3U, Xtream, and MAG registration paths use generated non-secret IDs and source-specific fields. |
| Smart Import presentation tests | PASS | Protocol-specific fields are visible only for the detected selection; Xtream input remains masked and locally handled. |
| All presentation test files in isolated Qt processes | PASS | Every `test_presentation*.py` file passed when launched independently with `QT_QPA_PLATFORM=offscreen`. |
| Combined local pytest | BLOCKED_ENVIRONMENT | Exit 139 during PySide6/shiboken collection/import of `test_presentation_smart_import_dialog.py`. This is the pre-existing Linux Qt collection constraint; it is not converted to a warning or skipped. |
| Complete non-presentation corpus | PASS | All test files outside the `test_presentation*.py` group passed; existing aiohttp bare-function deprecation warnings remained. |
| 10,000-item performance probe | PASS | Existing deterministic probe confirmed 10,000 live channels, EPG entries, movies, and series; 1,000 categories; no provider search or resolver calls during render. |
| Ruff | PASS | `src`, `tests`, `providers`, and `scripts` clean. |
| Black | PASS | 382 files unchanged. |
| MyPy | PASS | 224 source files, no issues. |
| Bandit production-code scan | PASS | No high/medium findings in `src`, `providers`, and `scripts`. Historic comment/`nosec` warnings remained. |
| Bandit including tests | INFORMATIONAL | Test assertions trigger historic low-severity B101 findings; no high/medium result was reported. |
| Dependency audit | SCOPED BLOCKER | The repository build requirement now pins `wheel>=0.46.2`, remediating the project-controlled Wheel finding. The sandbox global environment still reports `pypdf` and `xhtml2pdf`, neither declared by this project. |
| Secret indicators / credential-bearing diff | PASS | No added credential-bearing URLs, private-key markers, or token/authorization/cookie assignments. Generic password field names and synthetic test values are expected false-positive indicator filenames only. |
| Protected-boundary diff | PASS | No README change, no application-version change, no CI/CodeQL workflow change, and no release/tag mutation. |

## Local Validation Limits

The Linux sandbox has no libVLC runtime, so it cannot prove decoded IPTV frames/audio or Windows window-manager behavior. The hosted Windows portable workflow remains the mandatory platform gate for startup, bundled VLC, packaged Qt, path/CWD matrix, generated EXE smoke, debug-launcher smoke, artifact audit, checksum, and metadata.
