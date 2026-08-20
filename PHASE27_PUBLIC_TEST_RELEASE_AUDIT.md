# SamoTech IPTV Player v0.1.6 — Public Test Release Audit

**Release:** [`v0.1.6`](https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.6)
**Release commit:** `a1fd6cdf9eec4b8ee7439768494c869a31cb9440`
**Release workflow:** [Windows Portable EXE 32335400337](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32335400337) — **PASS**
**Published-artifact acceptance:** [Windows Release Artifact Acceptance 32335760310](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32335760310) — **PASS**

## 1. Final Status

> **Classification: RELEASED — PUBLIC TESTING.** The v0.1.6 Windows portable release passed deterministic application, security, packaged-runtime, checksum, and hosted Windows acceptance gates. It remains a public-testing release, not a universal IPTV compatibility certification.

The release was created after the application version was incremented only in the legitimate current-version sources. The historical `v0.1.5` tag, release, assets, and evidence were preserved. The protected README badge block has the unchanged baseline SHA-256 `d6310d733baae10823f9a84f2bb7ad157706930d993f4b26d78eb534d7da810d`.

| Dimension | Final result |
|---|---|
| Windows portable package | **PASS** |
| Bundled VLC and Qt startup | **PASS** |
| Optional sanitized debug launcher | **PASS** |
| Published EXE checksum and PE identity | **PASS** |
| Published artifact launch/path matrix | **PASS** |
| Real decoded IPTV media in Linux | **NOT AVAILABLE** — no local libVLC runtime |
| Authorized commercial-provider playback | **NOT VERIFIED** — no newly authorized provider fixture supplied |
| Universal provider/codec compatibility | **NOT CLAIMED** |

## 2. Completed Tasks

| Task | Completed result |
|---|---|
| Forensic baseline and protection | Recorded release history, Wave 3 boundaries, source architecture, Windows workflow gates, and the byte-exact README badge hash in `docs/evidence/WAVE4_PROTECTED_BOUNDARY_REPORT.md`. |
| Feedback investigation | Classified M3U setup, provider IDs, settings, dialog ownership, theme behavior, large playlists, fullscreen, screenshots, and real-provider requests in `docs/evidence/WAVE4_USER_FEEDBACK_INVESTIGATION.md`. |
| Simple source setup | M3U retains local-file/URL setup. Xtream and MAG now derive bounded non-secret internal IDs from their server/portal origin, eliminating unnecessary manual ID fields. Smart Import displays only fields relevant to the selected detected protocol. |
| Diagnostics | Added typed local playback diagnostics, bounded timing/recovery information, a safe copyable report, and `NOT_AVAILABLE` values instead of invented codec/container/frame claims. URLs, credentials, headers, tokens, cookies, and MAC identities are excluded. |
| User feedback path | Updated the bug-report template with source/content/first-frame/audio/buffering/switching evidence requests and explicit instructions never to publish secrets. |
| Window/settings improvements | Routine source dialogs are transient MainWindow-owned dialogs. The in-shell settings page now presents General, Playback, Appearance, Network, Diagnostics, and Privacy sections without fictitious configuration controls. |
| Debug launcher | Added `SamoTech-Debug.bat`, which launches the EXE with existing sanitized diagnostic mode, emits only local safe lifecycle output, and keeps normal EXE launch unchanged. |
| Documentation | Added `docs/PUBLIC_TESTING_GUIDE.md` and public-testing release-note language covering installation, source setup, fullscreen, diagnostics, privacy, and safe reporting. No mock or stale screenshot was added. |
| Large data | Reused the deterministic Phase 27 probe and passed the 10,000-item catalogue/EPG/VOD/series and 1,000-category workload without provider search/resolver work during rendering. |

## 3. Verification Results

| Gate | Result | Evidence |
|---|---|---|
| Focused diagnostics/provider/dialog/documentation tests | **PASS** | New and modified suites passed; Smart Import and all presentation modules were run in isolated Qt processes. |
| Complete non-presentation corpus | **PASS** | Existing `aiohttp` bare-function deprecation warnings remained. |
| Full local pytest collection | **BLOCKED_ENVIRONMENT** | Exit 139 in PySide6/shiboken collection/import of `test_presentation_smart_import_dialog.py`; each presentation file passed separately. No test was silently skipped. |
| Ruff, Black, MyPy | **PASS** | Ruff clean; Black reported 383 unchanged files; MyPy reported no issues across 224 source files. |
| Bandit production scan | **PASS** | No high/medium findings in `src`, `providers`, and `scripts`; historic scoped comment/`nosec` warnings remained. |
| Dependency audit | **SCOPED BLOCKER** | The project-controlled Wheel finding was remediated by requiring `wheel>=0.46.2`. Remaining sandbox-global `pypdf` and `xhtml2pdf` findings are not project dependencies. |
| Secret / protected-boundary checks | **PASS** | No added credential-bearing URL, private-key marker, or token/authorization/cookie assignment; README badge digest unchanged; CI/CodeQL permissions unchanged. |
| Windows candidate run | **PASS** | [Run 32334691869](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32334691869) validated the exact feature commit before version increment. |
| Windows version-matched run | **PASS** | [Run 32335111267](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32335111267) validated v0.1.6 before tagging. |
| Tagged release run | **PASS** | Tag/version matching, native VLC, EXE build, packaged smoke, Qt smoke, debug launcher, sanitized PATH/CWD matrix, artifact audit, checksum, metadata, and publication passed. |
| Independent release download | **PASS** | `SHA256SUMS.txt` verified both the EXE and debug launcher. The EXE was identified as a Windows x86-64 GUI PE. |
| Published release acceptance | **PASS** | Hosted release-artifact run passed checksum, PE metadata, bundled-VLC smoke, Qt smoke, normal/sanitized PATH, C drive/temp/spaces/Unicode/Downloads-like paths, arbitrary CWD, and repeat launch matrix. |

## 4. Release Identity and Published Assets

| Item | Published value |
|---|---|
| Tag | `v0.1.6` annotated tag `36e2e7c8d0719deeccc0dbe7a870062d18799f9a` |
| Tag target | `a1fd6cdf9eec4b8ee7439768494c869a31cb9440` |
| Release state | Published, non-draft, non-prerelease |
| EXE | `SamoTech-IPTV-Player-Windows-x64-v0.1.6.exe` — 135,532,351 bytes |
| EXE SHA-256 | `46352200290c712435b787ab731db409cb3fcb03a4de460179d106c1ee1e3854` |
| Debug launcher | `SamoTech-Debug.bat` — 1,062 bytes |
| Debug launcher SHA-256 | `9f3fa790b2f8bb4fb22f8c8542a1aa1248dba72273bbfa5dee0a698c7179b94e` |
| Checksum manifest | `SHA256SUMS.txt` — verifies both published assets |

## 5. Changes Made

The functional changes remain inside the existing Python, PySide6, and libVLC architecture. `PlayerPort` receives a non-abstract safe diagnostic snapshot method, and the sole `VlcPlayerAdapter` produces only local, typed, redacted lifecycle information. The player shell renders the report using a separate dialog; no provider URL, raw stream manifest, network header, token, password, cookie, or device identity is forwarded to this UI.

The release pipeline now packages and checksums the optional debug launcher beside the EXE, smoke-tests it on the Windows runner, and publishes it only after the existing blocking package gates. No CI permission change, workflow-scope reduction, release workaround, second player, playback proxy, codec implementation, or provider-specific claim was introduced.

## 6. Blocked Items and Exact Reasons

| ID | Status | Exact reason |
|---|---|---|
| B-01 | **BLOCKED_ENVIRONMENT** | The Linux sandbox lacks `libvlc.so`, `libvlccore.so`, and a VLC executable. It cannot prove decoded HLS/MPEG-TS/MP4 frames or audio. |
| B-02 | **BLOCKED_ENVIRONMENT** | Monolithic local pytest still exits 139 during PySide6/shiboken collection. Every presentation file passed in a separate process, and Windows non-Qt plus generated-EXE Qt smoke gates passed. |
| B-03 | **BLOCKED_EXTERNAL** | No new authorized real M3U, Xtream, or MAG fixture was supplied for actual provider/catalogue/media acceptance. |
| B-04 | **NOT VERIFIED** | No safe runtime evidence establishes commercial provider headers, session/cookie refresh, temporary link behavior, codec coverage, multi-monitor behavior, or decoded media continuity. |
| B-05 | **SCOPED ENVIRONMENT FINDING** | `pip-audit` still reports global `pypdf` and `xhtml2pdf` packages not declared in the repository. The project-controlled Wheel finding was remediated. |

## 7. Remaining Actions

Public testers should use their own legitimate source and submit the copied safe diagnostic report with source type, content type, catalogue/open/frame/audio/buffering/switching observations. The next engineering milestone should prioritize reproducible evidence from those reports, then add provider-owned ephemeral transport/session handling only when the existing boundary demonstrates a specific need.

The Linux Qt collection fault should be isolated in a dedicated test-environment task. It must not be treated as proof that presentation tests are unnecessary. Real provider acceptance, non-HTTP transport support, advanced MAG flows, catch-up, VOD/series claims, cross-platform clients, multi-monitor behavior, and broad codec certification remain separate evidence-driven milestones.

## References

[1]: [Windows candidate validation run 32334691869](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32334691869)
[2]: [Windows v0.1.6 validation run 32335111267](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32335111267)
[3]: [Tagged v0.1.6 release workflow 32335400337](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32335400337)
[4]: [Published v0.1.6 artifact acceptance 32335760310](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32335760310)
[5]: [`WAVE4_VALIDATION_MANIFEST.md`](docs/evidence/WAVE4_VALIDATION_MANIFEST.md)
[6]: [`PUBLIC_TESTING_GUIDE.md`](docs/PUBLIC_TESTING_GUIDE.md)
