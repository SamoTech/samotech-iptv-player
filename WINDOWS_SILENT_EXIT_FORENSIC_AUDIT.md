# Windows Silent-Exit Forensic Audit

**Project:** SamoTech IPTV Player  
**Repository:** [`SamoTech/samotech-iptv-player`](https://github.com/SamoTech/samotech-iptv-player)  
**Audit scope:** Windows silent-exit investigation, deterministic VLC discovery, startup diagnostics, v0.1.3 publication, and exact published-artifact verification  
**Author:** **Manus AI**  
**Audit date:** 2026-08-18 (user timezone)  
**Final tagged commit:** `ddb6cc9c7d24e5d27c356cc7c28afa93ca6659d3`  
**Final repository HEAD after post-release audit-gate cleanup:** `90dd71d`  

## Executive conclusion

The investigation **proved a source-mode VLC discovery defect**. When the application was launched from an arbitrary current working directory, `configure_bundled_runtime()` did not consult `VLC_RUNTIME_DIR`; `python-vlc` therefore fell through to its relative `ctypes.CDLL(".\\libvlc.dll")` lookup and raised a `FileNotFoundError`. This was a real deterministic-runtime defect and was fixed at the packaged-runtime layer without relying on the current working directory, installing VLC globally, or manually copying DLLs.

The investigation **did not prove that this source-mode defect caused the customer’s published v0.1.2 frozen-EXE silent exit on Windows 10**. The frozen executable uses the PyInstaller extraction directory (`_MEIPASS`) and the v0.1.2 customer report was observed on a Windows 10 environment that was not available for reproduction. The customer evidence—SmartScreen warning, “Run Anyway,” silent termination, and exit code 0—remains consistent with several possible causes, including Windows security or environment behavior, but it is not sufficient to identify the frozen-artifact root cause.

Version **v0.1.3 was rebuilt and published through the unchanged zero-touch tagged workflow**. Its exact release asset is byte-identical to the tagged workflow artifact, has a verified SHA256 checksum and PE identity, and passed the tagged Windows build’s native VLC, packaged-VLC, Qt, `VLC_READY`, `MAIN_WINDOW_SHOWN`, sanitized-PATH, artifact-audit, checksum, and upload gates. The final decision is therefore **v0.1.3 RELEASE ACCEPTED for publication, with a material limitation noted below**: the separate exact-published-artifact acceptance matrix repeatedly failed on its first C-drive case before producing a startup journal. That failed matrix is not reported as a pass, and the unresolved C-drive behavior must remain visible to maintain forensic accuracy.

## Decision summary

| Decision item | Result | Evidence and interpretation |
|---|---:|---|
| Source-mode deterministic VLC discovery | **PROVEN defect; FIXED** | `VLC_RUNTIME_DIR` was previously ignored in source mode; the corrected code selects it before relative fallback. |
| Frozen v0.1.2 Windows 10 silent-exit root cause | **NOT PROVEN** | No Windows 10 reproduction was available; the frozen path uses `_MEIPASS`, so source-mode failure is not sufficient evidence. |
| v0.1.3 source and Linux regression gates | **PASS** | Linux CI, CodeQL, quality gates, regression tests, security checks, and credential scan passed before tag creation. |
| v0.1.3 tagged Windows build | **PASS** | Run `32073501870` completed all blocking build and generated-EXE checks, including `VLC_READY` and `MAIN_WINDOW_SHOWN`. |
| v0.1.3 publication and artifact identity | **PASS** | Release `v0.1.3` is non-draft and non-prerelease; published EXE matches the tagged workflow artifact byte-for-byte. |
| v0.1.3 exact published-artifact matrix | **BLOCKED / FAIL** | Runs `32073957144`, `32074347826`, `32074479462`, `32074628592`, `32074779623`, `32074911470`, `32075754216`, `32075897689`, and `32076055559` failed on the first C-drive case before a journal was found. This is not a release-gate pass. |
| Overall release decision | **RELEASE ACCEPTED WITH LIMITATION** | Publication is accepted because the tagged artifact and build gates passed; C-drive exact-artifact behavior remains an explicit unresolved limitation requiring Windows investigation. |

## Investigation timeline and evidence

| Stage | Evidence | Finding |
|---|---|---|
| Customer observation | [`build/silent_exit_user_report.md`](build/silent_exit_user_report.md) | SmartScreen warning, “Run Anyway,” silent exit, exit code 0, and SmartScreen ADS value `Anaheim` were recorded. |
| Historical artifact status | v0.1.1 and v0.1.2 release records | v0.1.1 and v0.1.2 were preserved; no release was overwritten or force-pushed. |
| Source-mode reproduction | [`build/silent_exit_findings.md`](build/silent_exit_findings.md), [`build/silent_exit_vlc_lookup_trace.txt`](build/silent_exit_vlc_lookup_trace.txt) | The source process omitted `VLC_RUNTIME_DIR`, then `python-vlc` attempted `.\\libvlc.dll` relative to the current directory. |
| Diagnostic-mode reproduction | [`build/source_startup_diagnostic.json`](build/source_startup_diagnostic.json) | The journal retained an ordered failure record and last stage. Its `libvlc_new` result was treated as local-environment evidence, not Windows production evidence. |
| Windows build validation | Run [`32073138241`](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32073138241) | The ddb6cc9 push validation passed the new startup-diagnostic and `MAIN_WINDOW_SHOWN` checks. |
| Tagged release build | Run [`32073501870`](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32073501870) | The tagged build and publication job passed; the release was created from the intended immutable tag. |
| Published artifact identity | [`v0.1.3 release`](https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.3) and tagged-run artifact | Published and generated EXEs both measured 135,506,431 bytes and had SHA256 `c2c1b43308e6305b0eb1078bb2c55ba4d20b6931a13dce11b5c1fcd0bf5abf87`. |
| Exact published-artifact verification | Acceptance runs listed below | Checksum and PE identity passed, but the first C-drive execution did not produce a startup journal. The failure was preserved rather than converted into a warning. |

## Proven finding: source-mode VLC discovery failure

The source-mode failure is **proven** by code inspection, runtime tracing, and reproduction. The old `_bundled_vlc_root()` implementation searched only the PyInstaller extraction directory and package root. In source mode it did not consult the explicitly supported `VLC_RUNTIME_DIR`. When the application was started outside the repository or outside a directory containing `libvlc.dll`, the `python-vlc` binding reached its relative fallback and attempted to load `.\\libvlc.dll` from the current working directory. That behavior violated the production contract that the application must locate its own intended VLC runtime deterministically.

The failure was not repaired by changing the current directory, installing VLC globally, or copying DLLs manually. The corrected implementation checks `VLC_RUNTIME_DIR` first in source mode, then checks the application/package runtime roots, verifies both `libvlc.dll` and `libvlccore.dll`, configures the plugin directory, registers the Windows DLL directory, and replaces stale `PYTHON_VLC_*` and `VLC_PLUGIN_PATH` values rather than preserving them with `setdefault`. The regression suite includes an arbitrary-CWD source-mode test proving that `import vlc` succeeds when the runtime directory is supplied explicitly.

## Proven observability improvement

`src/samotech_iptv/startup_diagnostics.py` now writes an atomic JSON journal with an ordered checkpoint history. The journal records bootloader start, runtime and path initialization, VLC discovery start, `VLC_READY`, Qt initialization, `MAIN_WINDOW_SHOWN`, and `APPLICATION_READY`. On failure it retains the last successful stage, sanitized exception type and message, exit code, environment facts, and safe failure details. It uses the `SAMOTECH_STARTUP_DIAGNOSTIC_PATH` override when supplied, otherwise the stable application-data location, with a TEMP fallback when the preferred location cannot be written.

The desktop entrypoint records failures for ordinary exceptions and `SystemExit`, supports `--diagnostic`, and no longer permits a startup failure to disappear without a durable record when diagnostic mode is requested. The generated Windows executable’s blocking smoke gate checks that `VLC_READY` and `MAIN_WINDOW_SHOWN` are reached. These checks are present in the tagged build workflow and were passed by run `32073501870`.

## Frozen v0.1.2 root-cause classification

The published v0.1.2 Windows 10 silent-exit root cause is **not proven**. The source-mode defect cannot be promoted to a frozen-artifact conclusion because the frozen runtime follows a different path: PyInstaller supplies `_MEIPASS`, the runtime hook executes before the application imports `vlc`, and the bundled VLC files are located below the extracted bundle. The available Windows runner was Windows Server 2025, not the customer’s Windows 10 environment, and the sandbox has no Windows 10 VM or Wine environment capable of reproducing the customer’s exact conditions.

The customer’s SmartScreen observation is significant but not causal proof. `ADS=Anaheim` indicates that the customer’s downloaded file carried internet-origin security metadata associated with SmartScreen handling. In contrast, the CI acceptance copies had no `Zone.Identifier` stream in the captured C-drive failure. This difference means SmartScreen or endpoint-security policy remains a plausible environmental contributor, but it does not establish that SmartScreen caused the v0.1.2 exit, nor does it explain the source-mode `FileNotFoundError`.

## v0.1.3 fix set

| File or area | Change | Verification |
|---|---|---|
| `src/samotech_iptv/packaged_runtime.py` | Deterministic source-mode `VLC_RUNTIME_DIR` selection; frozen `_MEIPASS` selection; explicit DLL/plugin configuration; stale environment replacement | Focused packaged-runtime regression tests and Windows build gates passed. |
| `src/samotech_iptv/__init__.py` and `src/samotech_iptv/version.py` | Version resolution now uses the authoritative project version rather than stale installed metadata | `tests/test_version_resolution.py` passed; tagged artifact reports version 0.1.3. |
| `src/samotech_iptv/startup_diagnostics.py` | Atomic, redacted, durable startup journal with safe path selection and fallback | `tests/test_startup_diagnostics.py` passed; generated Windows diagnostics reached required stages. |
| `src/samotech_iptv/desktop_entrypoint.py` | Diagnostic-mode argument, ordered startup checkpoints, failure retention, and exit-code translation | Tagged packaged-VLC and Qt smoke gates passed. |
| `src/samotech_iptv/desktop_runtime.py` | Runtime-stage diagnostics and successful `APPLICATION_READY` recording | Tagged Qt smoke reached `MAIN_WINDOW_SHOWN` and `APPLICATION_READY`. |
| `.github/workflows/windows-portable-build.yml` | Blocking `VLC_READY`, `MAIN_WINDOW_SHOWN`, and startup-journal verification | Run `32073501870` passed the tagged build job. |
| `.github/workflows/windows-release-artifact-acceptance.yml` | Exact release download, checksum/PE identity, path/PATH matrix, and blocking startup-journal checks | Checksum and PE identity passed; exact matrix remains blocked on the first C-drive launch. |

## v0.1.3 artifact identity

The immutable release tag `v0.1.3` points to `ddb6cc9c7d24e5d27c356cc7c28afa93ca6659d3`. The published asset is `SamoTech-IPTV-Player-Windows-x64-v0.1.3.exe`, a PE32+ GUI x86-64 Windows executable, 135,506,431 bytes in size. Its SHA256 is `c2c1b43308e6305b0eb1078bb2c55ba4d20b6931a13dce11b5c1fcd0bf5abf87`, matching both `SHA256SUMS.txt` and the downloaded tagged-run artifact. The release is non-draft and non-prerelease.

For comparison, the preserved v0.1.2 artifact was recorded as 135,498,690 bytes with SHA256 beginning `39c8c43b`, and the preserved v0.1.1 artifact was recorded as 135,491,662 bytes with SHA256 beginning `f34b699c`. These earlier releases were not deleted or rewritten.

## Windows gate results

The ddb6cc9 push validations passed Linux CI run `32073138304`, CodeQL run `32073138303`, and Windows Portable EXE run `32073138241`. The tagged Windows workflow run `32073501870` passed the complete build job and its publication job, including Python/dependency setup, pinned VLC 3.0.23 acquisition and hashes, libVLC DLL validation, 363 VLC plugin DLLs, Ruff, Black, mypy, Windows non-Qt tests, native VLC lifecycle, one-file PyInstaller build, packaged-VLC smoke, Qt/application smoke, startup diagnostics, `VLC_READY`, `MAIN_WINDOW_SHOWN`, sanitized PATH, artifact contents, checksum generation, metadata, release notes, and upload/publication.

The exact published-artifact workflow passed its download, checksum, PE version, and artifact identity steps in every attempt. The matrix execution failed at `c-drive-normal-path-launch1-packaged-vlc-test` before a startup journal was found. The observed C-drive failure had an existing copied EXE of the correct 135,506,431-byte size, no stdout, no stderr, and no `Zone.Identifier` stream in the CI environment. The repeated matrix attempts were not recorded as successful acceptance: `32073957144`, `32074347826`, `32074479462`, `32074628592`, `32074779623`, `32074911470`, `32075754216`, `32075897689`, and `32076055559` all concluded failure. The later harness experiments were reverted, and the repository’s final acceptance workflow is restored to the ddb6cc9 blocking form.

## Environment limitations and remaining action

The sandbox cannot run Windows PE executables directly because it is Ubuntu Linux and has no Wine or Windows 10 virtual machine. The hosted CI runner is Windows Server 2025, which is useful for reproducible build and smoke evidence but is not equivalent to the customer’s Windows 10 machine, user profile, endpoint-security policy, GPU/driver stack, or SmartScreen reputation state.

The remaining action is therefore a targeted Windows investigation of the exact v0.1.3 release asset under the C-drive installation case, preferably on Windows 10 and Windows 11 with a standard non-administrator account and endpoint-security telemetry. The diagnostic journal must be checked both at the requested path and at the TEMP fallback location, and process creation, Windows Application Error events, Defender/SmartScreen events, and PyInstaller extraction failures should be collected. Until that evidence exists, the C-drive exact-artifact result must remain **blocked**, and the v0.1.2 frozen-artifact root cause must remain **not proven**.

## Final status

**Completed:** deterministic source-mode VLC discovery fix; startup diagnostics; regression tests; v0.1.3 rebuild; tagged Windows build; release publication; exact artifact checksum and PE verification; Linux and CodeQL gates; credential-scan and quality-gate verification; final report.

**Proven:** source-mode VLC discovery failure caused by relative `.\\libvlc.dll` lookup from the current working directory; observability gap and diagnostic retention behavior; v0.1.3 tagged build artifact identity and tagged-build gate results.

**Not proven:** the published v0.1.2 frozen-EXE silent-exit root cause on Windows 10; whether SmartScreen/Defender caused that event; whether the v0.1.3 C-drive failure is identical to the customer’s Windows 10 failure.

**Release decision:** **v0.1.3 RELEASE ACCEPTED WITH LIMITATION.** The release is published and traceable, and its tagged build passed the blocking build and smoke gates. The separate exact published-artifact C-drive matrix did not pass and is explicitly carried forward as an unresolved Windows acceptance blocker.

## References

[1]: https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.3 "SamoTech IPTV Player v0.1.3 release"

[2]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32073501870 "Tagged v0.1.3 Windows Portable EXE workflow run"

[3]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32073138241 "ddb6cc9 Windows push validation workflow run"

[4]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32073138304 "ddb6cc9 Linux CI workflow run"

[5]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32073138303 "ddb6cc9 CodeQL workflow run"

[6]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32073957144 "First exact v0.1.3 release-artifact acceptance attempt"

[7]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32076055559 "Final exact v0.1.3 release-artifact acceptance experiment"
