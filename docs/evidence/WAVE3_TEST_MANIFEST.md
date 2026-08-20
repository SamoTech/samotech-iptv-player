# Wave 3 Test and Evidence Manifest

## Deterministic and Static Gates

| Gate | Result | Evidence |
|---|---|---|
| Typed account-expiration model | PASS | `tests/test_domain_provider_runtime_records.py` |
| Xtream trial/account translation | PASS | `tests/test_infra_xtream_domain_translator.py` |
| Four-state capability truth model | PASS | `tests/test_application_load_provider_capabilities.py` |
| Provider summary state distinctions | PASS | `tests/test_presentation_provider_management.py` with offscreen Qt |
| Focused Wave 3 total | PASS — 32 tests | Account, translator, capability, and provider-management selections |
| Non-presentation regression corpus | PASS | `pytest -q` excluding `test_presentation*.py`; 72 existing aiohttp deprecation warnings only |
| Ruff | PASS | Repository-wide `src tests providers scripts` |
| Black | PASS | Repository-wide `src tests providers` |
| MyPy | PASS | 221 source files |
| Bandit | PASS | No high/medium findings; parser/comment and historic `nosec` warnings only |
| Dependency audit | PASS | No known vulnerabilities; project package itself is not on PyPI and cannot be audited |
| Diff / protected boundary scan | PASS | No README, version, workflow, tag, release, or credential-bearing diff detected |

## Runtime and Platform Evidence

| Evidence requirement | Result | Exact boundary |
|---|---|---|
| Public HLS VOD real libVLC probe | ENVIRONMENTAL BLOCKER | Linux sandbox has no libVLC library/executable/runtime directory; adapter initialization fails before media open |
| Authorized Xtream/MAG real media chain | BLOCKED_EXTERNAL | No newly authorized provider fixture; historic provider acceptance remains blocked |
| Full monolithic local pytest | ENVIRONMENTAL BLOCKER | PySide6 collection segmentation fault while importing `test_presentation_smart_import_dialog.py`, despite `QT_QPA_PLATFORM=offscreen` |
| Isolated provider-management Qt test | PASS | Four focused offscreen tests passed |
| Windows package/runtime evidence | Historical PASS | Run 32330586667 validates current published build path; Wave 3 code requires a new post-push Windows validation run |
| macOS/Android/iOS/Web | NOT VERIFIED | No corresponding target or runtime exists in this repository |

## Integrity Rule

No blocked runtime item was converted into a pass or warning. No raw credentials, tokens, authorization headers, cookies, private playlist data, or stream URL output is included in this manifest.

## References

[1]: `docs/evidence/WAVE3_RUNTIME_PROBE_LOG.md` — controlled HLS blocker.  
[2]: `docs/evidence/WAVE3_CAPABILITY_MATRIX.md` — current status matrix.  
[3]: `PHASE25_REAL_PROVIDER_PLAYBACK_AUDIT.md` and `PHASE26_REAL_PLAYBACK_ACCEPTANCE_HARNESS.md` — historical provider-evidence limits.  
[4]: [Windows Portable EXE workflow run 32330586667](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32330586667) — historical package/lifecycle validation.
