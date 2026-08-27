# Windows Portable EXE Beta Failure Forensic Audit

**Repository:** [SamoTech/samotech-iptv-player][1]
**Audit date:** 2026-08-17
**Author:** **Manus AI**
**Audited branch:** `main`
**Audited CI/package commit:** `9e4e49b4f720d9deff2b7c639be3190b0227c927`
**Documentation follow-up commit:** `e3ade5dbe6b97d4315927ed5962c992876f614b6`

> **Final status: D — ROOT CAUSE NOT YET PROVEN.** The exact published `v0.1.1` customer EXE was downloaded, checksum-verified, structurally inspected, and executed successfully on a hosted Windows runner in an expanded 48-execution matrix. No application defect, trust block, or beta-machine-specific failure was reproduced, and no speculative production fix or replacement release was created. The beta report therefore remains an unresolved production incident despite strong independent artifact acceptance evidence.

## 1. Incident summary

The authoritative specification states that a beta tester reported that the Windows Portable EXE downloaded directly from the published GitHub Release did not work on the tester’s Windows machine. The specification classifies this as release-blocking and explicitly prohibits assuming either that the tester was wrong or that GitHub Actions success proves customer compatibility.[1]

The investigation preserved the prior security remediation and existing provider, player, VLC, Qt, qasync, and zero-touch release architecture. It first recorded the repository baseline, then downloaded and inspected the exact release asset before any rebuild. A blocking manual acceptance workflow was added so the exact published artifact—not merely a freshly built workspace artifact—could be exercised on Windows.

## 2. Beta tester report

The available authoritative input contains the claim that the release EXE did not work, but it does not include the tester’s Windows version, exact symptom, screenshot, stdout/stderr, Windows Event Viewer record, Defender/SmartScreen message, crash dump, process exit code, working directory, profile state, or reproduction steps. A search of the repository’s GitHub Issues and pull requests returned no public incident record containing additional beta evidence.

Accordingly, the report is treated as a real production incident, but the observable failure class cannot be selected from the supplied evidence. The absence of a detailed beta report is an explicit blocker rather than evidence that the tester was mistaken.

## 3. Exact affected release

The affected customer-facing release is `v0.1.1`, published on 2026-08-17T10:28:18Z. It is a non-draft, non-prerelease GitHub Release with the asset `SamoTech-IPTV-Player-Windows-x64-v0.1.1.exe` and the companion `SHA256SUMS.txt`.[2]

The annotated tag `v0.1.1` points to commit `5ba5938e3d398b27147732496591f0f2a49f7c45`, whose subject is `docs: document zero-touch windows releases`. The release asset is therefore treated as the authoritative customer artifact for this audit, not as a rebuild candidate.

## 4. Download source

The EXE and checksum were downloaded directly from the published release using the GitHub repository’s release asset endpoint. The exact EXE URL was:

`https://github.com/SamoTech/samotech-iptv-player/releases/download/v0.1.1/SamoTech-IPTV-Player-Windows-x64-v0.1.1.exe`

The local forensic copies are retained under `build/beta_release_artifact/` for reproducible inspection. No release asset was manually replaced, overwritten, or republished.

## 5. SHA256

The release metadata reports an EXE size of **135,491,662 bytes**. The downloaded file produced SHA256:

```text
f34b699cabd07efb409ebb96e3138a6990ac8d12d76dca0ee0127143e19417f5
```

The exact same digest appears in the downloaded `SHA256SUMS.txt`. Checksum verification therefore passed before Windows execution. The independent hosted Windows acceptance workflow repeated the hash calculation and reported the same digest.[3]

## 6. Environment

The local forensic inspection ran on Ubuntu 24.04.4 LTS, Linux 6.1.102, x86_64. The sandbox has no `wine` or `wine64`, so it cannot execute the PE directly. Local execution claims are therefore limited to source-level tests, native Linux probes where supported, and static artifact inspection.

The actual customer artifact was executed by GitHub Actions on a hosted Windows runner. The expanded acceptance run recorded Microsoft Windows Server 2025, version 10.0.26100, runner image `windows-2025-vs2026`, image version `20260810.198.2`, and architecture Windows x64.[4]

## 7. Reproduction steps

The investigation followed the required order. First, repository state, tag, release, workflow, PyInstaller spec, runtime hook, VLC contract, Qt packaging, entry point, and resource-resolution code were inspected. Second, the exact `v0.1.1` EXE and checksum asset were downloaded. Third, PE metadata, embedded PyInstaller archive contents, Qt files, VLC files, Python extensions, and runtime data were inspected. No rebuild preceded these steps.

A new workflow was then added at `.github/workflows/windows-release-artifact-acceptance.yml`. It downloads the exact release asset by tag, verifies SHA256 and FileVersion/ProductVersion, copies the exact EXE into multiple locations, sanitizes PATH, changes the working directory independently of the EXE location, and executes both `--packaged-vlc-test` and `--smoke-test` with first and second launches.

## 8. Reproduction result

The exact published `v0.1.1` EXE passed the initial eight-execution hosted Windows acceptance run `32028411385`. After expanding the gate, the same exact release asset passed **48/48 executions** in run `32028755849`.[4]

Every tested execution returned exit code `0`. Packaged VLC smoke and Qt/application smoke both passed for each location, PATH mode, and launch number. No crash, timeout, nonzero exit, missing-DLL message, missing-platform-plugin message, or startup failure was observed in the available hosted Windows environment.

This is strong evidence that the artifact is launchable under the tested Windows runner conditions. It is not evidence that the beta tester’s specific machine had the same conditions or that the original report was invalid.

## 9. Failure classification

No classification from categories A–Q can be confirmed. In particular, the investigation did not reproduce an EXE launch failure, post-launch crash, missing window, silent exit, SmartScreen/Defender block, missing DLL, VLC initialization failure, Qt platform failure, path failure, permission failure, architecture mismatch, or corrupted asset.

The appropriate evidence-based classification is **Q — other/unresolved incident due to missing beta-environment evidence**, with the root cause status required by the specification set to **D — ROOT CAUSE NOT YET PROVEN**. The exact artifact’s independent Windows acceptance pass prevents classifying the release as definitively broken, but it does not explain the beta observation.

## 10. Root cause

No root cause has been proven. The available evidence establishes that the published file is intact, is a PE32+ x86-64 GUI executable, contains a PyInstaller archive, contains Qt and VLC payloads, and launches successfully in the hosted Windows matrix. It does not identify what occurred on the beta tester’s machine.

Potential distinctions—application startup failure, trust/reputation block, antivirus interference, user-profile or permission difference, GPU/driver issue, locale/path difference, or a transient/corrupted local download—remain hypotheses only. They are not promoted to conclusions because the required machine-specific evidence is absent.

## 11. Evidence

The principal evidence is summarized below.

| Evidence | Result | Interpretation |
|---|---|---|
| Exact GitHub release download | PASS | The customer asset was inspected before rebuild |
| Published checksum comparison | PASS | Downloaded EXE matches `SHA256SUMS.txt` |
| PE format | PASS | PE32+ x86-64 Windows GUI executable |
| FileVersion/ProductVersion | PASS | Both are `0.1.1` |
| PyInstaller archive | PASS | Embedded archive present and inspectable |
| Qt platform payload | PASS | `PySide6\\plugins\\platforms\\qwindows.dll` present |
| VLC payload | PASS | `libvlc.dll`, `libvlccore.dll`, and VLC plugin tree present |
| Exact artifact Windows execution | PASS | 48/48 smoke executions exit 0 |
| Code signing | NOT PRESENT | PE Security Directory is absent; no Authenticode signature was found |
| Beta-machine reproduction | BLOCKED | No tester environment or failure trace supplied |
| SmartScreen/Defender result | BLOCKED | No user-facing trust/security message supplied |

The raw structural inspection, PE metadata, archive listing, and hosted Windows logs are retained under `build/beta_release_artifact/` and are not release assets.

## 12. CI-vs-real-user difference

The original tagged build workflow `32019974720` passed its generated-artifact checks and published `v0.1.1`. Those checks included the Windows non-Qt corpus, native VLC lifecycle, generated EXE packaged-VLC smoke, generated EXE Qt smoke, sanitized-PATH validation, artifact audit, checksum generation, and release publication.[5]

The new independent gate differs in one decisive way: it downloads and runs the actual GitHub Release asset. It also expands the path/PATH/launch matrix. Even with those improvements, the hosted runner remains different from an unknown beta machine in Windows version, user profile, permissions, antivirus/Defender state, SmartScreen reputation state, GPU and display drivers, locale/code page, TEMP location, username/path, installed runtime components, and network policy. Because the beta values for these fields are unavailable, the smallest explanatory difference cannot be identified.

## 13. Packaging analysis

The PyInstaller spec requires `VLC_RUNTIME_DIR`, validates `libvlc.dll`, `libvlccore.dll`, and the `plugins` directory, packages VLC binaries under `vlc`, packages the VLC plugin tree under `vlc/plugins`, includes optional VLC `lua` and `locale` data, includes `pyproject.toml`, registers `packaged_runtime` as a hidden import, collects provider submodules, and installs `packaging/samotech_runtime_hook.py` as a runtime hook.[6]

The EXE archive contains `desktop_entrypoint`, `pyproject.toml`, PyInstaller runtime hooks, Python 3.13 DLLs, PySide6 native modules, Qt DLLs, Qt plugins, and the VLC tree. The strings inspection found no obvious `/home/`, `/workspace/`, runner-user, or source-tree development path. The runtime code resolves the frozen root through `sys._MEIPASS` and does not use the current working directory to locate the bundled VLC root.

No packaging defect was proven. Consequently, the spec and application packaging were not changed speculatively.

## 14. VLC analysis

The exact archive contains top-level `libvlc.dll` and `libvlccore.dll` entries as well as the packaged `vlc\\libvlc.dll` and `vlc\\libvlccore.dll` entries, plus the VLC plugin tree and locale/lua data. The source runtime hook calls `configure_bundled_runtime()` before importing `vlc`. The packaged runtime looks for `sys._MEIPASS\\vlc`, keeps the Windows DLL directory handle alive, sets `PYTHON_VLC_LIB_PATH`, `PYTHON_VLC_MODULE_PATH`, and `VLC_PLUGIN_PATH`, and verifies that the plugin directory exists.[6]

The exact release artifact passed `--packaged-vlc-test` in all 24 combinations of the expanded matrix, including sanitized PATH and arbitrary CWD. That is native evidence that the bundled VLC runtime initializes in the tested runner environment. The local Linux VLC lifecycle probe correctly reported `SKIP: windows_required`; no unsupported Linux claim was made.

## 15. Qt analysis

The exact archive contains `PySide6\\Qt6Core.dll`, `Qt6Gui.dll`, `Qt6Network.dll`, `Qt6Widgets.dll`, the PySide6 extension modules, the PySide6 runtime DLLs, and `PySide6\\plugins\\platforms\\qwindows.dll`. The PE archive therefore contains the expected Windows Qt platform plugin rather than relying on a separately installed Qt distribution.

The exact release artifact passed `--smoke-test` in all 24 combinations of the expanded matrix. This initializes the production desktop graph, creates the Qt application, shows the main window, processes a Qt turn, and closes the composed desktop object. It does not constitute full manual GUI interaction through provider, catalogue, player, fullscreen, or stop controls.

## 16. Windows security analysis

The PE metadata parser reported that the Security Directory is absent. This establishes that the published EXE does not contain an embedded Authenticode signature. It does **not** establish that SmartScreen or Defender blocked the beta tester’s execution.

No SmartScreen dialog, Defender event, quarantine record, Windows Event Viewer entry, or user-facing security message was provided. The hosted acceptance runner’s successful execution does not test the reputation state of an unsigned binary on a clean consumer machine. Code signing and SmartScreen reputation remain commercial-distribution limitations, not confirmed causes of this incident.

The release workflow was not weakened: no Defender-disable instruction was added, no security gate was made non-blocking, and the new workflow has `contents: read` permission only.

## 17. Confirmed defect

No confirmed application defect exists in the evidence set. The exact artifact’s checksum, PE identity, bundled runtime contents, packaged VLC smoke, Qt smoke, path handling, sanitized PATH, arbitrary CWD, first launch, and second launch all passed on the available hosted Windows runner.

The confirmed engineering gap is different: the prior release process validated a generated workspace artifact but did not independently run the exact downloaded GitHub Release asset in a dedicated blocking workflow. That gap has now been corrected. It is a prevention/process defect, not proof that the v0.1.1 application itself was defective on the beta machine.

## 18. Fix

No production application fix was made because no application root cause was reproduced. This is deliberate compliance with the specification’s “fix only proven defects” rule. Existing provider protocols, PlayerShell, PlayerPort, ResolvedPlayback, shared libVLC lifecycle, qasync, Smart Import, and the completed safe-logging remediation remain unchanged.

The implemented CI fix is a blocking exact-release acceptance workflow. It downloads the published asset, verifies identity, and executes the artifact under an expanded Windows matrix. The workflow was added in commit `373a23ed27573d0edf492d3b0cc54163f8286833` and expanded in `9e4e49b4f720d9deff2b7c639be3190b0227c927`.

## 19. Regression test

`tests/test_windows_packaging_config.py` now asserts that the exact-release workflow is artifact-focused and blocking. It verifies the release download, checksum, PE version checks, packaged VLC smoke, Qt smoke, C-drive/temporary/Unicode/Downloads-like/arbitrary-CWD paths, normal and sanitized PATH, first and second launches, and absence of `continue-on-error` in the acceptance workflow.

The focused workflow regression file passed **6/6** tests after formatting. The full non-presentation pytest corpus also passed locally with coverage XML generation. The native PlayerShell probe passed **17/17** checks, and the performance probe passed at 10K, 50K, and 100K catalogue sizes.

## 20. Prevention gate

The permanent gate is `.github/workflows/windows-release-artifact-acceptance.yml`. It is manually dispatched with a release tag and runs on `windows-latest`. It downloads the exact named EXE and checksum from GitHub Releases, fails on missing assets or checksum mismatch, checks FileVersion and ProductVersion against the tag, and fails on any nonzero process exit or timeout.

The gate runs both packaged VLC and Qt/application smoke paths in six locations, two PATH modes, and two launches. It is not allowed to continue after a failed check. The main CI workflow also remains blocking for lint, format, type checking, security regression tests, and the non-presentation test corpus.

## 21. Windows acceptance matrix

The completed expanded matrix is:

| Dimension | Cases | Result |
|---|---|---|
| Location | C-drive root, spaces, Unicode, Downloads-like, TEMP, arbitrary CWD | 6/6 cases passed |
| PATH | Normal PATH, sanitized system-only PATH | 2/2 modes passed |
| Launch | First launch, second launch | 2/2 launches passed |
| Smoke | Packaged VLC, Qt/application | 2/2 smoke paths passed |
| Total executions | 6 × 2 × 2 × 2 | **48/48 exit code 0** |

The actual asset was copied and executed from each test location. The arbitrary-CWD case launched the EXE while the working directory was the Windows system directory, testing that resource resolution is not CWD-dependent.

The matrix does not include a separately provisioned standard non-admin account, a clean consumer Windows image without developer tools, a clean user profile, a network drive, a real GPU/driver variation, or an actual beta machine. Those remain blockers for full real-user equivalence.

## 22. Security validation

The existing centralized safe-logging remediation was preserved. Local security tests passed, Ruff passed, Black passed, mypy passed, and the latest CodeQL workflows for the CI acceptance commits completed successfully: CodeQL run `32028756816` for `9e4e49b` concluded success.[7]

The earlier authenticated GitHub Security evidence showed alerts #1–#10, all titled “Clear-text logging of sensitive information,” closed as fixed. The current Code Scanning REST inventory request returned HTTP 403 (`Resource not accessible by integration`) in this sandbox, so no new alert count is manufactured. The latest CodeQL workflow conclusion is recorded; the API limitation remains explicit.

A protected-credential scan over tracked non-test files passed. The corrected sensitive-marker scan found no synthetic canary marker outside the intentional security test source. No credentials, provider URLs, tokens, cookies, or passwords were added by this Windows investigation.

## 23. Performance impact

The CI-only acceptance changes have no application runtime performance impact. The existing native performance probe passed at 10K, 50K, and 100K catalogue sizes. The new workflow adds Windows execution time because it deliberately runs the exact customer artifact 48 times, but that is an acceptance-cost increase, not a production performance regression.

The expanded gate is intentionally conservative: a portable release must prove startup, packaged VLC, Qt initialization, path independence, sanitized-PATH independence, repeat launch, and exit-code behavior before it can be considered accepted.

## 24. Release decision

No new release was published. The existing `v0.1.1` release remains unchanged and is documented as the release associated with the unresolved beta report. The specification forbids silently overwriting the existing release and forbids creating a new release before the failure mechanism is understood.

The acceptance workflow and its regression coverage were pushed to `main`, but they do not constitute a production application fix. A patch release is not justified on the present evidence because no application defect was confirmed. If beta-machine evidence later proves a defect affecting `v0.1.1`, the appropriate patch must be built and published through the existing zero-touch tag workflow only after the complete build/test/Windows-acceptance/checksum/audit chain passes.

## 25. Remaining blockers

The principal blocker is the missing beta-machine evidence. The investigation needs the tester’s exact Windows version/build, architecture, user privilege, exact download source and hash, path from which the EXE was launched, process behavior, screenshots or messages, Windows Event Viewer records, Defender/SmartScreen result, antivirus/quarantine state, display/GPU details, locale/code page, TEMP path, and whether the tester used first or repeat launch.

Full commercial acceptance also remains blocked for manual GUI flows through provider screen, Smart Import, provider list, search, live catalogue, player, fullscreen, stop, and exit. Authorized populated-provider acceptance must not be claimed without authorized data. SmartScreen reputation, code signing, ARM64, and consumer AV behavior are also not established by the hosted runner.

## 26. Deferred items

A safe beta diagnostic mode was not added. The failure was not shown to be silent, and adding a new diagnostic path without a confirmed need would violate the no-speculation rule. The existing central `safe_logging` utility remains the only approved redaction mechanism if diagnostics are later required.

Network-drive execution, a separately provisioned standard non-admin account, a clean consumer profile, no-developer-tool image, GPU/driver variation, and live-provider GUI acceptance are deferred until the required environment or authorized fixtures are available. No provider protocol or packaging redesign is deferred as a hidden workaround.

## 27. Commit history

The relevant commits are:

| Commit | Change | Classification |
|---|---|---|
| `5ba5938e3d398b27147732496591f0f2a49f7c45` | v0.1.1 release tag commit | Existing release baseline |
| `1dd4488781a7ea569f8a50ef2fb80560fb7362f2` | Prior corrected CI/security evidence baseline | Existing work preserved |
| `373a23ed27573d0edf492d3b0cc54163f8286833` | Add exact published release artifact acceptance workflow | CI/prevention only |
| `9e4e49b4f720d9deff2b7c639be3190b0227c927` | Expand exact-release acceptance matrix and regression coverage | CI/prevention only |
| `e3ade5dbe6b97d4315927ed5962c992876f614b6` | Keep the prior security audit’s canary scan wording consistent | Documentation only |

No force-push, history rewrite, empty commit, manual release replacement, or provider/protocol change occurred.

## 28. Workflow runs

| Workflow | Run | Commit | Result |
|---|---:|---|---|
| Windows Portable EXE, tagged v0.1.1 | `32019974720` | `5ba5938e` | Success; generated artifact and release publication gates passed |
| Exact release acceptance, initial matrix | `32028411385` | `373a23e` | Success; exact v0.1.1 asset, 8 executions |
| Exact release acceptance, expanded matrix | `32028755849` | `9e4e49b` | Success; exact v0.1.1 asset, 48/48 executions |
| CI | `32028756685` | `9e4e49b` | Success |
| CodeQL | `32028756816` | `9e4e49b` | Success |

The historical CI failure `32025891263` is preserved as evidence of a separate Ubuntu Qt collection segmentation fault at `tests/test_presentation_smart_import_dialog.py`. The workflow correction excludes only the already-proven fatal presentation corpus from the Ubuntu broad gate; the blocking security gate remains active.

## 29. Artifact verification

The final traceability chain for the tested customer artifact is:

```text
Git tag v0.1.1
  → commit 5ba5938e3d398b27147732496591f0f2a49f7c45
  → GitHub Windows release workflow 32019974720
  → GitHub Release asset SamoTech-IPTV-Player-Windows-x64-v0.1.1.exe
  → SHA256 f34b699cabd07efb409ebb96e3138a6990ac8d12d76dca0ee0127143e19417f5
  → independent exact-release acceptance workflow 32028755849
  → FileVersion/ProductVersion 0.1.1
  → 48/48 Windows smoke executions exit code 0
```

Static PE inspection identified PE32+ x86-64, Windows GUI subsystem, PyInstaller bootloader strings, PySide6 Qt DLLs and `qwindows.dll`, Python 3.13 DLLs, libVLC/libVLCcore, and the VLC plugin/runtime tree. The PE Security Directory was absent, so code signing is not present in the artifact. No manual asset replacement occurred.

## 30. Final status

**D — ROOT CAUSE NOT YET PROVEN.**

The exact published EXE is intact and independently launchable in the available hosted Windows environment. The new blocking gate materially improves prevention by testing the actual release asset rather than only a workspace-generated artifact. The prior security remediation remains preserved, and current local/CI/CodeQL checks are strong.

However, the required customer incident is not closed because the beta tester’s actual failure was not reproduced and the machine-specific evidence needed to distinguish application failure from trust blocking, antivirus interference, environment differences, or a transient/corrupted download was not available. The honest remaining action is to obtain that evidence and rerun the exact artifact on the affected or equivalent environment. Until then, the release must not be represented as universally Windows-compatible, SmartScreen-compatible, fully GUI-accepted, or root-cause-fixed.

## References

[1]: https://github.com/SamoTech/samotech-iptv-player "SamoTech IPTV Player repository"
[2]: https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.1 "SamoTech IPTV Player v0.1.1 GitHub Release"
[3]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32028411385 "Initial exact-release Windows acceptance run"
[4]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32028755849 "Expanded exact-release Windows acceptance run"
[5]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32019974720 "Tagged v0.1.1 Windows Portable EXE workflow run"
[6]: https://github.com/SamoTech/samotech-iptv-player/blob/9e4e49b4f720d9deff2b7c639be3190b0227c927/samotech-iptv-player.spec "PyInstaller packaging specification"
[7]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32028756816 "CodeQL workflow run for the expanded acceptance-gate commit"
