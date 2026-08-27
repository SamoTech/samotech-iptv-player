# SamoTech IPTV Player — Windows Silent-Exit Forensic Audit

**Project:** SamoTech IPTV Player  
**Repository:** [`SamoTech/samotech-iptv-player`](https://github.com/SamoTech/samotech-iptv-player)  
**Audit scope:** Published v0.1.3 Windows 11 silent exit, PyInstaller execution-stage proof, corrective implementation, forensic/build validation, and exact published v0.1.4 acceptance
**Author:** **Manus AI**  
**Audit date:** 2026-08-18 (user timezone)  
**Final release commit:** `39e545e68ec4517f6a36e90730bdf29675c43fdf`
**Final release tag:** `v0.1.4`

## 1. Executive summary

The published **v0.1.3** executable failed on the reported Windows 11 Pro client by starting as a process, creating no window, loading no observable Python, Qt, or VLC runtime modules, producing no diagnostic file or Windows error event, and exiting approximately six seconds later. The original evidence is recorded in [`build/silent_exit_user_report.md`](build/silent_exit_user_report.md) and in the authoritative specification.[1]

The failure was reproduced and the root cause was **proven**, rather than inferred from the absence of a window. The frozen `desktop_entrypoint.py` script defined `main()` but lacked the executable entry-point guard `if __name__ == "__main__": main()`. PyInstaller executes the configured script as `__main__`; without that guard, Python imported the module, defined its functions, and returned exit code `0` without invoking the application. The debug-all bootloader log proves that extraction completed, Python started, the frozen script ran, and the child exited cleanly before Qt or VLC initialization.[2]

The fix was committed, rebuilt, and exercised through the complete available Windows validation path. The exact **published v0.1.4 release EXE** passed checksum and PE identity verification plus all **48/48** execution cases across the release-artifact path/PATH/launch/argument matrix on the Windows Server 2025 runner.[8] This is strong artifact-level Windows evidence, but it is not a replacement for testing on the original Windows 11 Pro client. Windows 10 and a repeat test on that real Windows 11 machine remain **NOT TESTED**.

> **Final classification:** Root cause **PROVEN**. Corrective fix **VERIFIED**. Exact published v0.1.4 artifact **ACCEPTED on the available Windows Server 2025 acceptance environment**. Real Windows 11 client acceptance and Windows 10 acceptance remain **NOT TESTED**.

## 2. Exact root cause

### 2.1 Proven cause

The exact root cause of the v0.1.3 frozen silent exit was the missing executable entry-point guard in `src/samotech_iptv/desktop_entrypoint.py`. The file contained a `main()` function, but the module did not call it when run as a script. The PyInstaller specification analyzes that file directly as the application script, so the frozen child process loaded the module under `__main__`, executed its top-level imports and definitions, and reached end-of-file. Python then returned success without creating a `QApplication`, initializing VLC, creating a main window, or writing the application startup journal.[2]

The direct reproduction independently matched the frozen behavior: executing `desktop_entrypoint.py --diagnostic --smoke-test` before the fix returned `0`, emitted no useful stderr, and created no diagnostic file. The debug-all frozen build showed `LOADER: child process started!`, `LOADER: running desktop_entrypoint.py`, Python imports, `LOADER: OK.`, and `LOADER: child process exited (return code: 0)`. The evidence therefore identifies the precise execution stage: **the bootloader and Python runtime succeeded; the application entry function was never invoked**.

### 2.2 Evidence classification

| Finding | Classification | Basis |
|---|---|---|
| v0.1.3 exited without a window or visible application error on the reported Windows 11 client | **PROVEN** | Direct client observation supplied in the specification and preserved in the user-report ledger.[1] |
| PyInstaller extraction completed in the decisive debug-all experiment | **PROVEN** | Bootloader output and normal `_MEI` cleanup were captured.[2] |
| Python started inside the frozen child process | **PROVEN** | Bootloader transitions and imported-module evidence.[2] |
| `desktop_entrypoint.py` executed as the frozen script | **PROVEN** | `LOADER: running desktop_entrypoint.py` appeared in the debug-all log.[2] |
| `main()` was not called by the pre-fix frozen script | **PROVEN** | Missing guard in source plus matching clean no-op reproduction.[2] |
| Qt and VLC were the cause of the original silent exit | **DISPROVEN for the proven failure path** | The failure occurred before either initialization stage was reached; post-fix Qt/VLC stages passed. |
| SmartScreen, Defender, or an unsigned executable caused the v0.1.3 exit | **NOT PROVEN** | The client evidence records security context, but it does not establish causality. |
| Windows 10 has the same failure | **NOT TESTED** | No Windows 10 environment was available. |
| v0.1.4 works on the original Windows 11 Pro client | **NOT TESTED** | The exact client was not available for re-test. |

## 3. Original customer evidence and prior CI discrepancy

The reported v0.1.3 asset was `SamoTech-IPTV-Player-Windows-x64-v0.1.3.exe`, 135,506,431 bytes, with SHA256 `c2c1b43308e6305b0eb1078bb2c55ba4d20b6931a13dce11b5c1fcd0bf5abf87`. On Windows 11 Pro 10.0.26200 x64, the process existed for approximately six seconds, had no HWND, showed no Python/Qt/VLC modules during observation, and exited without a matching Application Error, Windows Error Reporting, Reliability Monitor, application diagnostic, or visible `_MEI` directory.[1]

The absence of a visible `_MEI` directory was initially consistent with a one-file extraction failure, but it was not sufficient to prove that hypothesis. The controlled debug-all experiment changed the evidence classification: `_MEI` extraction and Python startup were observed directly, and the no-op exit was reproduced after the frozen script began executing. The earlier extraction hypothesis is therefore **NOT the root cause of this incident**.

Previous v0.1.3 CI checks passed because the test and build paths did not exercise the actual frozen script-entry semantics that failed in the customer run. They directly invoked Python modules, functions, or test harnesses and treated successful PyInstaller completion or a non-frozen invocation as sufficient. The missing `__main__` guard was therefore never exercised as the decisive frozen application entry point. This explains how ordinary tests could pass while a published EXE performed a clean no-op. The corrected workflow now launches the generated EXE and requires startup checkpoints, rather than considering packaging completion alone to be proof.

## 4. PyInstaller analysis and extraction-stage proof

The forensic build used the repository’s application configuration and produced four variants: OneDir, OneFile, OneFile with bootloader debugging, and OneFile with all debugging. The build workflow and downloaded evidence are retained in the repository’s `build/` forensic ledgers; the build run was `32130447534` and the execution matrix run was `32133230768`.[4] [5]

The decisive debug-all sequence was:

```text
LOADER: child process started!
LOADER: running desktop_entrypoint.py
Python imports samotech_iptv, packaged_runtime, startup_diagnostics, and PySide6-related modules
LOADER: OK.
LOADER: child process exited (return code: 0)
```

That sequence proves the following lifecycle for the pre-fix candidate:

| PyInstaller stage | Result | Interpretation |
|---|---:|---|
| Bootloader initialization | **PROVEN** | The frozen process reached the child-process stage. |
| `_MEI` temporary extraction | **PROVEN complete** | Debug output and normal cleanup demonstrated extraction. |
| Python DLL/runtime initialization | **PROVEN** | Python imports occurred inside the frozen child. |
| Frozen script execution | **PROVEN** | `desktop_entrypoint.py` was explicitly reported as running. |
| `main()` invocation | **PROVEN FALSE** | The source lacked the guard and no startup checkpoint followed. |
| Qt initialization | **NOT REACHED** | No application call was made. |
| VLC initialization | **NOT REACHED** | No application call was made. |
| Process exit | **PROVEN clean exit code 0** | Module import completion was treated as successful process completion. |
| Application diagnostic journal | **ABSENT BY DESIGN OF THE BUG** | Diagnostic construction was below the never-invoked `main()`. |

The evidence eliminates the need to attribute the original failure to a PyInstaller extraction defect. PyInstaller’s one-file extraction mechanism operated; the application script’s entry semantics were wrong. The phrase “PyInstaller issue” would have been too broad and is not used here as the root-cause label.

## 5. OneDir versus OneFile results

Before the fix, OneDir and OneFile shared the same script-entry defect because both executed the same `desktop_entrypoint.py`. The debug-all OneFile variant supplied the strongest execution-stage proof. After the fix, the OneFile, debug-bootloader, and debug-all variants reached their required startup stages across the bounded forensic path cases. The OneDir control was attempted, but the original 15-second harness bound produced timeouts before a valid stage result was captured. The timeout is a measurement limitation, not proof that the OneDir executable failed.

| Variant or artifact | Pre-fix finding | Post-fix available result | Classification |
|---|---|---|---|
| OneDir | Shared source entry-point no-op behavior was expected from the same script; later bounded runs timed out | 15-second bounded harness timed out across the OneDir cases without a valid stage capture | **NOT PROVEN to fail; measurement timeout** |
| OneFile | Clean no-op before the guard fix | `VLC_READY`, `APPLICATION_READY`, and diagnostic evidence reached in the forensic matrix | **PASS** |
| OneFile, debug bootloader | Bootloader output was available for stage attribution | All bounded cases passed after the fix | **PASS** |
| OneFile, debug-all | Directly proved extraction, Python startup, script execution, and pre-fix clean exit | All bounded cases passed after the fix | **PASS** |
| Exact production candidate | Not applicable before fix | 48/48 cases passed in run `32141055748` | **PASS** |
| Exact published v0.1.4 release asset | Not applicable before fix | 48/48 cases passed in run `32143064567` | **PASS** |

The OneDir timeout must remain visible in the final record. It was not converted into a failure and was not omitted from the evidence summary.

## 6. Python, Qt, and VLC findings

The validated production toolchain remained unchanged as required: Python 3.13 on the Windows runner, PyInstaller 6.22.1, PySide6 6.11.1, python-vlc 3.0.21203, and VLC 3.0.23. The local development environment used Python 3.12. No evidence required changing Python, PyInstaller, PySide6, python-vlc, or VLC versions, and none were changed.

The corrected application provides independent probes so that Python/Qt startup can be separated from VLC initialization. The Qt/application smoke mode reaches `MAIN_WINDOW_SHOWN` and `APPLICATION_READY`; the packaged-VLC probe reaches `VLC_READY`. The exact candidate and exact published-artifact matrices both reached the expected stage for every case. Therefore, **Qt and bundled VLC initialize correctly once `main()` is actually invoked**. They were not the cause of the original pre-fix silent exit.

The packaged runtime also validates and selects its bundled VLC runtime deterministically. It checks the frozen extraction root or explicit source-mode runtime location, verifies `libvlc.dll` and `libvlccore.dll`, configures the plugin directory, and replaces stale VLC-related environment values rather than relying on the current working directory. This is a separate hardening correction and is not promoted to the root cause of the v0.1.3 frozen no-op.

| Component | Result | Classification |
|---|---|---|
| Python frozen runtime | Loaded in debug-all and passed post-fix frozen tests | **PROVEN PASS after fix** |
| Qt initialization and main-window creation | `MAIN_WINDOW_SHOWN` and `APPLICATION_READY` reached in post-fix smoke tests | **PROVEN PASS after fix** |
| Bundled libVLC initialization | `VLC_READY` reached in post-fix packaged-VLC tests | **PROVEN PASS after fix** |
| VLC dependency inventory | Pinned `libvlc.dll`, `libvlccore.dll`, and 363 plugin DLLs validated by Windows build gates | **PROVEN PASS in runner** |
| VLC as v0.1.3 root cause | Not reached in the pre-fix failure path | **DISPROVEN for this failure path** |

## 7. Startup lifecycle after the fix

The corrected lifecycle is explicitly checkpointed and retained in the startup journal:

```text
BOOTLOADER_STARTED
  -> RUNTIME_READY / path and runtime initialization
  -> VLC_READY
  -> QT_INITIALIZED
  -> MAIN_WINDOW_SHOWN
  -> APPLICATION_READY
```

The `--packaged-vlc-test` probe verifies the VLC stage and exits successfully after `VLC_READY`. The `--qt-only-test` and `--smoke-test` paths verify that Python and Qt can initialize, that a main window is created, and that the application reaches `APPLICATION_READY` without relying on a live VLC startup path. A normal startup failure now records its phase, sanitized exception details, runtime/VLC paths, traceback, diagnostic path, and nonzero exit code, then presents a useful fail-loud error instead of silently returning success.

## 8. Exact code, configuration, and test changes

| File or area | Exact change | Purpose and verification |
|---|---|---|
| `src/samotech_iptv/desktop_entrypoint.py` | Added `if __name__ == "__main__": main()` | Invokes the application when PyInstaller runs the file as its frozen script. This is the proven root-cause fix. |
| `src/samotech_iptv/desktop_entrypoint.py` | Added `--qt-only-test`, `--packaged-vlc-test`, `--smoke-test`, and `--diagnostic` paths | Separates Python/Qt/VLC startup stages and makes exact EXE acceptance deterministic. |
| `src/samotech_iptv/desktop_entrypoint.py` and `desktop_runtime.py` | Added ordered startup checkpoints, fail-loud startup output, and preserved nonzero failure status | Prevents invisible startup failure and provides actionable phase/path information. |
| `src/samotech_iptv/startup_diagnostics.py` | Added atomic durable journal behavior, redacted traceback retention, runtime/VLC fields, environment facts, and diagnostic-path identity | Ensures diagnostics exist before Qt and survive startup failure. |
| `src/samotech_iptv/core/safe_logging.py` | Fixed `safe_label()` double-truncation of string paths | Preserves useful diagnostic path identity while retaining sanitization bounds. |
| `src/samotech_iptv/packaged_runtime.py` | Consults `VLC_RUNTIME_DIR` in source mode and replaces stale VLC environment values | Makes bundled VLC lookup deterministic from arbitrary working directories. |
| `src/samotech_iptv/__init__.py` and `version.py` | Uses authoritative `pyproject.toml` project version | Prevents stale installed metadata from misidentifying release artifacts. |
| `packaging/samotech_forensic.spec` | Added parameterized OneDir, OneFile, debug-bootloader, and debug-all forensic builds | Captures extraction and bootloader evidence without changing production defaults. |
| `scripts/build_windows_forensic.ps1` and `scripts/run_windows_forensic_matrix.ps1` | Added reproducible build and blocking execution harnesses with timeout evidence | Makes each forensic result attributable and prevents timeout misclassification. |
| `.github/workflows/windows-portable-build.yml` | Retained blocking native VLC, packaged-VLC, Qt/application, path, artifact, checksum, metadata, and upload gates | Ensures packaging completion alone is not treated as application success. |
| `.github/workflows/windows-candidate-artifact-acceptance.yml` | Added exact-candidate 48-case matrix | Proves the generated production candidate across six paths, two PATH modes, two launches, and two probes. |
| `.github/workflows/windows-release-artifact-acceptance.yml` | Added exact-published-release download, checksum/PE verification, and 48-case execution matrix | Proves the bytes users can download, not a rebuild. |
| Tests | Updated desktop-entrypoint, startup-diagnostics, packaged-runtime, version-resolution, and workflow-contract tests | Regression coverage passed in the available CI gates. |

No credentials were added. The final tracked-file credential scan passed. No force-push, force-retag, release overwrite, permission broadening, security-control suppression, or version reuse occurred.

## 9. Tests and validation performed

The original v0.1.3 evidence was reproduced through local source execution and frozen debug-all output. The corrected candidates then passed the available test and build gates. The main results are below.

| Validation | Result | Evidence |
|---|---:|---|
| Local direct pre-fix entrypoint reproduction | **PASS as reproduction** | Exit code 0, no journal, no useful stderr; matched the missing-guard mechanism.[2] |
| Pre-fix debug-all extraction/Python-stage attribution | **PASS as proof experiment** | `_MEI` extraction, Python imports, script execution, clean child exit 0.[2] |
| Forensic OneFile/debug-bootloader/debug-all fixed matrix | **PASS** | All bounded cases reached the expected VLC or application stages.[3] |
| Forensic OneDir control | **TIMEOUT / NOT PROVEN** | 15-second harness bound; no valid failure conclusion was drawn.[3] |
| Linux CI on final release commit | **PASS** | Run `32142065914`. |
| CodeQL on final release commit | **PASS** | Run `32142065833`; no unresolved findings were carried into the release. |
| Windows production candidate build | **PASS** | Run `32142065906`; all blocking gates passed. |
| Exact candidate acceptance | **48/48 PASS** | Run `32141055748`; all six paths, both PATH modes, both launches, and both probes passed. |
| Tag-triggered v0.1.4 production build/publication | **PASS** | Run `32142552074`; tag validation, build, artifact gates, and publication passed.[7] |
| Exact published v0.1.4 acceptance | **48/48 PASS** | Run `32143064567`; checksum/PE identity and all 48 execution cases passed.[8] |
| Published checksum verification | **PASS** | Downloaded release EXE matched `SHA256SUMS.txt`. |
| Tracked credential scan | **PASS** | No authorized Xtream credential appeared in tracked source, test, workflow, TOML, or Markdown files. |

The exact published matrix covered `c-drive`, `spaces`, `unicode`, `downloads-like`, `temporary`, and `arbitrary-cwd`, under normal and sanitized PATH, two launches, and both `--packaged-vlc-test` and `--smoke-test`. Every case returned exit code `0`; packaged-VLC cases reached `VLC_READY`, and smoke cases reached `APPLICATION_READY` with the required main-window checkpoint.

## 10. Windows 10 results

**Windows 10: NOT TESTED.** No Windows 10 VM or physical test environment was available. The Windows Server 2025 hosted runner validates the artifact in a controlled Windows environment but is not evidence of Windows 10 client behavior, endpoint-security policy, SmartScreen reputation, user profile, graphics stack, or filesystem conditions.

## 11. Windows 11 results

The published **v0.1.3** artifact **FAILED on the reported real Windows 11 Pro client**, as documented in the user evidence: no window, no observed Python/Qt/VLC modules, no diagnostic file, no matching Windows error event, and approximately six seconds to clean exit.[1]

The corrected **v0.1.4** artifact was **NOT TESTED on that exact real Windows 11 Pro client**. It was tested on Windows Server 2025 through the candidate and exact published-artifact acceptance matrices. Those results strongly verify the artifact’s startup behavior in the available Windows environment, but they do not permit a claim that the original customer machine has been independently revalidated.

## 12. Release artifact results

The immutable annotated tag `v0.1.4` points to commit `39e545e68ec4517f6a36e90730bdf29675c43fdf`. The tag-triggered workflow `32142552074` rebuilt the artifact and published the release without reusing an existing version tag. The published release is non-draft and non-prerelease, and previous releases v0.1.1, v0.1.2, and v0.1.3 remain preserved.[7] [9]

| Published asset property | Verified result |
|---|---|
| Asset | `SamoTech-IPTV-Player-Windows-x64-v0.1.4.exe` |
| Size | 135,509,880 bytes |
| SHA256 | `59caed3236bdbba62487b39b081ffe965137eb9002b313c2afb7d4efb7571882` |
| PE identity | PE32+ GUI x86-64 Windows executable |
| Release checksum manifest | Exact match; `sha256sum -c` returned `OK` |
| Release status | Published, non-draft, non-prerelease |
| Exact published-artifact matrix | 48/48 PASS on Windows Server 2025 |

The candidate artifact from run `32139619239` was separately exercised by the 48-case matrix in run `32141055748`, with SHA256 `9c6599f77a49add1cbc2d376bff142ec5734fbfb46af15492fb3fa283189c963`. The later published-artifact run validated the actual GitHub Release bytes rather than assuming that the candidate and release assets were identical.

## 13. Remaining limitations

The investigation has no remaining root-cause uncertainty for the reproduced frozen silent exit. The following environmental or measurement limitations remain and are intentionally not converted into claims of success:

| Limitation | Classification | Consequence |
|---|---|---|
| Original Windows 11 Pro client was not available for v0.1.4 retest | **NOT TESTED** | Real-client acceptance is not claimed. |
| Windows 10 environment unavailable | **NOT TESTED** | Windows 10 compatibility is not claimed. |
| OneDir fixed execution exceeded the 15-second forensic harness bound | **NOT PROVEN** | OneDir is not declared failed or passed on that bounded run. |
| SmartScreen/Defender behavior for the new unsigned release on a real client | **NOT TESTED** | Security-product behavior is not claimed. |
| Double-click interaction and sustained user interaction on the original machine | **NOT TESTED** | The CI matrix proves startup checkpoints, not a human session on that machine. |
| Windows runner equivalence to the user’s profile, drive, policy, and GPU stack | **NOT PROVEN** | CI success is artifact evidence, not a universal client guarantee. |

The controlled forensic matrix did include spaces, Unicode, arbitrary working directories, a D-drive case, and sanitized PATH conditions for the fixed candidates. The exact published-release matrix included the six release path cases listed above. These controlled cases reduce path and environment risk but do not replace real-client testing.

## 14. Risk assessment

The residual risk for the **specific silent-exit mechanism** is low because the missing guard is corrected, directly regression-tested, and exercised by the exact published artifact. The risk that the same clean no-op will recur through the frozen entry point is materially reduced by the explicit guard and by blocking EXE smoke tests that require startup checkpoints.

The residual **environmental** risk is moderate because the original machine was not re-tested and because the release remains unsigned. SmartScreen, endpoint-security policy, user permissions, filesystem ACLs, graphics drivers, and other machine-specific conditions could still affect a real client. The report therefore does not state that CI acceptance proves universal Windows 10 or Windows 11 behavior.

The residual **measurement** risk is limited to OneDir’s bounded timeout and to interaction beyond the deterministic startup probes. The OneDir result remains explicitly unclassified rather than being silently treated as either a failure or a pass.

## 15. Final release decision

**Release decision: v0.1.4 is ACCEPTED for publication and for the exact published-artifact Windows Server 2025 acceptance environment, with explicit real-client limitations.**

This decision is supported by all of the following: the original root cause is proven; the source fix is minimal and directly addresses that cause; startup diagnostics and fail-loud behavior are present; the candidate passed the exact 48-case matrix; the new immutable tag was created only after Linux, CodeQL, and Windows production gates passed; the tag-triggered build and publication passed; the published EXE and checksum were independently downloaded and verified; and the exact published EXE passed all 48 acceptance executions.

The decision does **not** claim Windows 10 acceptance, does **not** claim reacceptance on the original Windows 11 Pro client, does **not** claim that SmartScreen or Defender behavior has been eliminated, and does **not** convert the OneDir timeout into a success. Those items remain **NOT TESTED** or **NOT PROVEN** exactly as shown above.

## References

[1]: build/silent_exit_user_report.md "Original Windows 11 v0.1.3 client observation ledger"
[2]: build/MASTER_FORENSIC_PHASE6_FINDINGS.md "Proven PyInstaller execution-stage and missing-main-guard findings"
[3]: build/MASTER_FORENSIC_BOUNDED_EVIDENCE_SUMMARY.txt "Bounded forensic execution matrix summary"
[4]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32130447534 "Forensic candidate build workflow run"
[5]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32133230768 "Forensic candidate execution workflow run"
[6]: build/MASTER_FORENSIC_CANDIDATE_ACCEPTANCE_EVIDENCE/windows-candidate-acceptance-19eea0fcd442f07963f537fba8fd70c1761d98be/candidate-acceptance-summary.txt "Exact v0.1.4 production candidate 48-case acceptance summary"
[7]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32142552074 "Tag-triggered v0.1.4 Windows build and publication workflow run"
[8]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32143064567 "Exact published v0.1.4 release-artifact acceptance workflow run"
[9]: https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.4 "Published SamoTech IPTV Player v0.1.4 release"
[10]: ../../.github/workflows/windows-release-artifact-acceptance.yml "Exact published-artifact acceptance contract"
