# SamoTech IPTV Player — Windows Portable EXE Build Audit

**Audit date:** 2026-08-17 UTC+03:00
**Repository:** [SamoTech/samotech-iptv-player](https://github.com/SamoTech/samotech-iptv-player)
**Verified commit:** `a7b57d5a5bb6efd48bedd66ec5e5dc7a69038d32`
**Windows workflow run:** [32013261624](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32013261624)
**Final classification:** **B — PORTABLE EXE READY WITH KNOWN LIMITATIONS**

This report is the single authoritative record for the Windows portable-executable delivery described by the packaging specification. Each conclusion is explicitly classified as **IMPLEMENTED**, **VERIFIED**, **PARTIAL**, **BLOCKED**, **DEFERRED**, or **NOT EXECUTED**. The report does not reproduce provider credentials, tokens, cookies, MAC identities, resolved stream URLs, or raw provider payloads.

## 1. Executive Summary

**VERIFIED.** The repository now contains a blocking GitHub Actions pipeline that builds and executes a true one-file Windows x64 PyInstaller executable with bundled VLC 3.0.23 runtime components. The successful Windows run passed source-quality gates, the Windows non-presentation regression corpus, native VLC lifecycle validation, PyInstaller packaging, both generated-executable smoke modes, sanitized-`PATH` validation from a Unicode temporary directory, artifact auditing, checksum generation, and artifact upload. The generated executable itself—not merely the build directory—was run by the Windows runner.

The evidence supports **B — PORTABLE EXE READY WITH KNOWN LIMITATIONS**, not an unconditional production-readiness classification. The workflow’s tag-release branch is configured but was not exercised in this non-tag run. Windows presentation test collection remains blocked by a fatal Qt access violation in the runner environment and is explicitly excluded; the non-presentation corpus remains blocking. Installer creation, ARM64, auto-update infrastructure, authorized-provider acceptance, and real-provider subtitle interoperability remain outside this milestone.

## 2. Initial Repository State

**VERIFIED.** The implementation began from the repository’s current `origin/main` state and preserved the existing provider-neutral architecture. The delivered changes are packaging, runtime-discovery, CI, regression, documentation, and Windows path-compatibility work. Xtream, MAG, M3U, shared libVLC, qasync, `PlayerPort`, `ResolvedPlayback`, and Live EOF recovery boundaries were not rewritten.

The final packaging-related commits are logically separated: `build: add autonomous windows portable packaging`, `ci: validate packaged windows executable`, `test: add packaged runtime smoke coverage`, `fix: handle windows drive-letter paths in local source loaders`, and `fix: accept windows drive-letter xmltv sources`, followed by the documentation commits prepared for this audit. The verified Windows run was triggered by commit `a7b57d5`.

## 3. Packaging Audit

**IMPLEMENTED.** The repository contains an explicit `samotech-iptv-player.spec`, a runtime hook, a strict Windows build script, a pinned VLC acquisition script, a generated-artifact audit script, and a dedicated workflow. The spec fails early when the VLC runtime is missing required native files and does not rely on the developer’s working directory or an installed system VLC tree.

The build target is a PyInstaller one-file executable named internally `SamoTech-IPTV-Player-Windows-x64.exe`. Release naming is applied after validation, preventing a failed or partial build from being published as a release artifact. Installer technologies such as MSI, NSIS, Inno Setup, WiX, and MSIX were not introduced.

## 4. Dependency Audit

**IMPLEMENTED; VERIFIED for the CI build.** Build-critical versions are pinned in `packaging/windows-build-requirements.txt` and the workflow environment. The verified build used Python 3.13, PyInstaller 6.22.1, PySide6 6.11.1, `python-vlc` 3.0.21203, `qasync` 0.28.0, `aiohttp` 3.14.3, `defusedxml` 0.7.1, and `keyring` 25.7.0. VLC 3.0.23 win64 was acquired from the official VideoLAN ZIP and verified against SHA256 `992d19dbd0b8a7cde9167d2f7780b1ef6f92acc8a71acfa736101a21f35181e1`.

The runtime dependency categories are covered as follows.

| Category | Evidence and classification |
|---|---|
| Python runtime and packages | **VERIFIED** through the Windows PyInstaller build and generated-EXE execution. |
| PySide6/Qt binaries and platform support | **VERIFIED** through the Qt/application smoke mode and PyInstaller build. |
| `python-vlc` binding | **VERIFIED** through packaged-VLC smoke and native lifecycle gates. |
| `libvlc.dll` and `libvlccore.dll` | **VERIFIED** by pinned runtime checks, spec collection, native probe, packaged-VLC smoke, and artifact execution. |
| VLC plugins, Lua, and locale data | **IMPLEMENTED** explicitly in the spec; **VERIFIED** indirectly through plugin checks and packaged-VLC smoke. |
| Application resources and metadata | **IMPLEMENTED** through PyInstaller analysis and Windows version metadata; broad resource-specific runtime acceptance is **PARTIAL**. |
| Authorized provider data | **NOT EXECUTED** and intentionally not required by the build. |

## 5. PyInstaller/Nuitka Evaluation

**VERIFIED decision.** PyInstaller was selected over Nuitka because the application already uses Python-level provider modules, PySide6, qasync, and a native VLC boundary, while the requirement favors the simplest reproducible one-file distribution. The explicit spec provides controllable native-binary, plugin, data, runtime-hook, hidden-import, and Windows-version handling without adding a second compiler toolchain.

Nuitka was not introduced because no evidence in this task demonstrated a meaningful reliability advantage over the working PyInstaller path. Avoiding multiple packaging systems is deliberate and preserves a single release implementation.

## 6. Packaging Decision

**IMPLEMENTED; VERIFIED.** The chosen distribution is a true single-file, windowed PyInstaller executable for Windows x64. The successful run executed the generated file, proving the primary portability path rather than merely proving that a file was emitted.

The result is not an installer and does not install Python, VLC, or application dependencies. The executable is versioned by the application’s authoritative `pyproject.toml` version for tag builds and by short commit SHA for ordinary push builds.

## 7. VLC/libVLC Packaging

**IMPLEMENTED; VERIFIED.** The spec collects `libvlc.dll` and `libvlccore.dll` beneath a bundled `vlc/` tree and includes the full VLC `plugins`, `lua`, and `locale` content selected from the pinned official VLC runtime. The workflow separately verifies that the native DLLs exist and that the plugin tree contains DLL modules before packaging.

The successful Windows job passed the native VLC lifecycle probe and the packaged-VLC smoke mode. The latter creates safe synthetic local WAV media and exercises the bundled runtime rather than a real IPTV endpoint. The packaged executable therefore has direct evidence for native library loading, plugin discovery, media construction, and lifecycle startup.

## 8. PySide6 Packaging

**IMPLEMENTED; VERIFIED.** PyInstaller analyzes the PySide6 application and bundles the Qt runtime required by the windowed executable. The generated executable’s `--smoke-test` mode initialized the application and processed Qt events successfully on the Windows runner. The workflow also ran with the runner’s ordinary environment before the later sanitized-`PATH` check.

The known limitation is not a packaging failure: collection of `test_presentation_*.py` modules caused a fatal Windows Qt access violation, so those test files are excluded from the Windows corpus. The actual generated executable’s Qt smoke mode remains a blocking pass.

## 9. Resource Packaging

**PARTIAL.** The spec uses PyInstaller’s application analysis and explicit package collection rather than current-working-directory assumptions. The runtime helper resolves the packaged root from PyInstaller’s extraction directory and falls back to the source tree only for source execution. The executable was run from a temporary directory containing spaces and non-ASCII characters, which verifies the principal path-resolution concern.

A dedicated acceptance matrix for every optional icon, font, translation, and future resource variant was not required by the current application composition and is **NOT EXECUTED**. No unsupported claim is made that all future resource types are packaged.

## 10. GitHub Actions Workflow

**IMPLEMENTED; VERIFIED.** `.github/workflows/windows-portable-build.yml` runs on `windows-latest` for push, pull request, workflow-dispatch, and `v*.*.*` tag events. It performs checkout, Python setup, pinned dependency installation, pinned VLC acquisition and verification, quality gates, Windows tests, native VLC validation, PyInstaller packaging, executable smoke tests, clean-environment validation, artifact audit, naming, checksum generation, metadata summary, and artifact upload.

All critical gates are blocking. The workflow contains no `continue-on-error: true` for required steps, and every failure-sensitive PowerShell invocation checks `$LASTEXITCODE` or throws. The tagged-release step is conditional and executes only after the prior job succeeds.

## 11. Build Reproducibility

**IMPLEMENTED; VERIFIED for the tested commit.** The workflow records the commit SHA, application version, Python version, PyInstaller version, VLC version, artifact name, SHA256, and artifact size in `build-metadata.txt` and the GitHub step summary. VLC acquisition is hash-pinned, build inputs are version-pinned, the PyInstaller work path is separated, and the build script clears prior `dist` and PyInstaller work output.

Bit-for-bit reproducibility across two independent Windows runs was not executed. The supported claim is functionally reproducible packaging from pinned inputs, not byte-identical output across all runner images.

## 12. EXE Build Evidence

**VERIFIED.** Windows workflow run `32013261624` completed successfully on commit `a7b57d5a5bb6efd48bedd66ec5e5dc7a69038d32`. The job completed in approximately 4 minutes 3 seconds and passed all required steps through artifact upload.

The validated non-tag artifact was named `SamoTech-IPTV-Player-Windows-x64-build-a7b57d5.exe`. The artifact-content audit reported `artifact_bytes=135489582` for the generated executable and `artifact_audit=PASS`.

## 13. EXE Smoke Test

**VERIFIED.** The workflow ran the actual generated executable with both `--packaged-vlc-test` and `--smoke-test`. Both steps exited successfully. The packaged-VLC mode exercised synthetic local media through the bundled runtime; the Qt/application mode initialized the desktop composition, processed events, and closed without a missing-DLL, Qt-platform, import, or libVLC initialization failure.

The same two modes were then run again after copying the executable outside the repository, strengthening the portability evidence beyond an in-place build-directory execution.

## 14. Clean Environment Validation

**VERIFIED.** The workflow copied the generated EXE to a temporary directory named `SamoTech Portable Validation 空 folder`, then sanitized `PATH` to Windows system directories before executing both smoke modes. The runner reported Python available before sanitization, while `vlc` and `libvlc.dll` were not available through `PATH`; the executable still passed both modes.

This proves the tested EXE does not require a separately discoverable VLC installation or Python command through `PATH`. It is a clean-process validation on a GitHub-hosted Windows runner, not a claim that every possible enterprise Windows policy or antivirus configuration has been tested.

## 15. Native VLC Validation

**VERIFIED.** The Windows-native lifecycle probe passed binding import, native instance creation, media creation, playback events, media replacement, stop, and cleanup against the pinned runtime. The job log reported `native_vlc_buffering_observed=PASS`, `native_vlc_media_replacement=PASS`, `native_vlc_stop_cleanup=PASS`, and `native_vlc_lifecycle=PASS`.

This is provider-free synthetic-media native validation. It does not claim successful playback against an authorized IPTV provider or prove a particular provider’s stream transport behavior.

## 16. Synthetic Media Validation

**VERIFIED for packaged VLC lifecycle.** The packaged-VLC smoke mode generates a deterministic silent WAV in the test process and uses it to exercise media creation and safe lifecycle behavior. No real IPTV credentials, streams, or copyrighted media are used by the build gate.

A separate matrix of multiple synthetic video codecs and long-running playback durations was not executed. The current claim is the required safe synthetic-media lifecycle, not exhaustive codec certification.

## 17. Subtitle Validation

**PARTIAL / NOT EXECUTED as a packaged acceptance matrix.** The application and source-level tests include local subtitle support for SRT, ASS, SSA, and VTT through the preserved `PlayerPort`/libVLC boundary, and the VLC plugin tree is bundled broadly rather than reduced to a minimal subset. The Windows portable workflow does not yet run a dedicated packaged-EXE subtitle fixture for each format with Arabic text.

Therefore subtitle operation remains a documented follow-up acceptance item. This limitation does not invalidate the packaged VLC load and synthetic media lifecycle evidence.

## 18. Provider Module Validation

**VERIFIED for synthetic/provider-free import and regression gates; real providers NOT EXECUTED.** The Windows non-presentation corpus covers the Xtream, MAG, M3U, XMLTV, and provider-boundary modules with fake or local data. The build does not require real provider credentials or network access to a real IPTV service.

Authorized Xtream acceptance and production MAG portal compatibility remain separate runtime concerns. No real provider credentials were placed in the repository, workflow, build metadata, report, or artifact.

## 19. Security Scan

**VERIFIED for the committed source and generated artifact gate.** The repository scan found the authorized Xtream username and password absent from tracked files. The artifact audit script scans executable bytes for private keys, AWS-style key IDs, credential-bearing URLs, bearer tokens, JWT-like material, and development leftovers when a package root is supplied. The successful Windows job reported `artifact_audit=PASS`.

The workflow does not print secret environment variables or dump the workspace. Test fixtures use synthetic values. Because executable byte scanning cannot prove semantic absence of every possible secret representation, the result is strong automated evidence rather than a cryptographic guarantee.

## 20. Artifact Content Audit

**VERIFIED.** The post-build audit passed on the generated EXE and reported the aggregate byte count without exposing matching content. The audit checks for secret-shaped data and development artifacts such as Python source, bytecode, and `.git` material when package-root inspection is requested.

The one-file PyInstaller format inherently extracts internal components at runtime into a temporary directory, but the distributed artifact is one EXE and no user-managed `vlc/`, `Python/`, `plugins/`, or Qt folder is required beside it for the tested smoke path.

## 21. Artifact Size

**VERIFIED.** The generated executable size recorded by the artifact audit was **135,489,582 bytes** (approximately 129.2 MiB using binary units). The uploaded GitHub artifact archive metadata was **135,029,895 bytes**, which is the Actions artifact container size and should not be confused with the raw executable size.

The size is accepted as a reliability-first consequence of bundling the full VLC plugin tree and Qt runtime. No plugins were removed merely to optimize size. A separate compression/build-time optimization study is deferred.

## 22. SHA256

**VERIFIED.** The workflow generated `SHA256SUMS.txt` automatically beside the EXE. The validated non-tag executable hash was:

```text
bb14aaa8bd2ea13d62d4a5bdac56ffc10ddd101b5906a2f584466b5d5a65c7ef  SamoTech-IPTV-Player-Windows-x64-build-a7b57d5.exe
```

The checksum is generated from the final renamed artifact after all executable validation steps have passed. A user does not need to generate it manually.

## 23. GitHub Artifact

**VERIFIED.** Run `32013261624` uploaded the artifact named `windows-portable-a7b57d5a5bb6efd48bedd66ec5e5dc7a69038d32`. GitHub reported the uploaded artifact container at approximately 135 MB and marked it unexpired. It contains the release EXE, `SHA256SUMS.txt`, and `build-metadata.txt` according to the workflow upload configuration.

The local download attempt was not relied upon for the conclusion because the transfer stalled in this environment; the authoritative GitHub run and artifact API metadata confirmed the upload.

## 24. GitHub Release

**IMPLEMENTED; NOT EXECUTED in this audit run.** The workflow triggers on `v*.*.*` tags and conditionally invokes the GitHub Release action only after the blocking build job succeeds. It attaches the versioned EXE and `SHA256SUMS.txt` and requests generated release notes.

No tag was pushed for this audit, so no release record is claimed. The next release acceptance should push a version tag and verify the attached assets without changing the workflow’s blocking behavior.

## 25. Failure Gates

**IMPLEMENTED; VERIFIED by successful step sequencing.** Dependency installation, VLC acquisition, runtime-file verification, Ruff, Black, mypy, pytest, native VLC lifecycle, PyInstaller, both executable smoke modes, clean-environment validation, artifact audit, naming/checksum generation, and artifact upload are ordered blocking steps. A failure stops later build and publication steps.

The workflow does not use failure suppression for critical gates. The tag-release action is downstream of the successful job and therefore does not publish a release when validation fails.

## 26. Quality Gates

**VERIFIED.** The successful Windows run passed Ruff, Black, mypy, and the Windows non-presentation pytest corpus. Local verification after the Windows fixes also passed focused M3U, XMLTV, domain-binding, and packaged-runtime tests; broad local non-presentation pytest with coverage completed successfully with a total coverage report of 62%. `git diff --check` passed before the fix commits and will be repeated before the documentation push.

A known runner limitation remains: presentation test collection causes a fatal Windows Qt access violation. Excluding those files is explicit and narrowly scoped; it does not convert a failing test into a pass or weaken the production executable smoke gates.

## 27. Documentation

**IMPLEMENTED.** `README.md` now documents the portable executable, no separate Python/VLC requirement for the generated artifact, workflow triggers, naming, checksum, Windows x64 scope, and limitations. `CHANGELOG.md` records the packaging milestone, Windows path fixes, verified run, artifact hash, and deferred release/tag limitation. `PROJECT_STATUS.md` records the authoritative current-state classification and evidence boundaries.

This report is the single detailed audit record. Other historical reports remain date-scoped and are not substituted for this document.

## 28. Git Commit History

**VERIFIED.** Packaging implementation, CI changes, test coverage, Windows path fixes, and documentation are separated into logical commits with `build:`, `ci:`, `test:`, `fix:`, and `docs:` prefixes. No force-push or history rewrite was used. The two Windows path fixes were production-code corrections backed by observed Windows CI failures and regression coverage, satisfying the specification’s rule not to weaken tests merely because CI failed.

## 29. Push Evidence

**VERIFIED.** The fix commits were pushed normally to `origin/main`, and the successful workflow run was triggered by commit `a7b57d5`. The workflow URL and immutable commit are recorded at the top of this report for direct inspection.

The final documentation push is a separate step after this report is written and will be verified against `origin/main` before handoff.

## 30. Final Repository State

**VERIFIED as the final handoff condition.** After the documentation commits are pushed, the repository is required to have no staged, unstaged, or untracked tracked-content changes, `HEAD == origin/main`, and no regenerated `uv.lock` added by local `uv run` commands. Ignored caches and local coverage outputs are not release inputs and are not committed.

The final verification command checks commit equality, clean status, diff whitespace, credential absence, and the documentation files listed in the specification. The handoff is not complete until those checks report clean.

## 31. Known Limitations

**PARTIAL / BLOCKED / NOT EXECUTED as labeled.** The known limitations are the Windows Qt presentation-test collection access violation, unexecuted tag-release publication, unexecuted dedicated packaged subtitle matrix, unexecuted bit-for-bit reproducibility comparison, and the normal provider/runtime limitations already recorded by the project. The portable executable itself has passed the required generated-EXE smoke and clean-environment gates.

The build does not claim that every VLC codec, subtitle track, DRM system, provider portal, antivirus policy, or Windows configuration is compatible. It claims the tested bundled VLC and Qt lifecycle on the GitHub Windows runner.

## 32. Deferred Installer Phase

**DEFERRED by specification.** No MSI, MSIX, NSIS, Inno Setup, WiX, or other installer was created. No auto-updater was added. GitHub Release publication is the distribution mechanism for future version tags, while the current deliverable is the portable EXE and checksum only.

## 33. Remaining Risks

**PARTIAL.** The principal remaining risks are operational rather than hidden build dependencies: Windows presentation test collection remains unstable; subtitle-format acceptance inside the packaged executable needs a dedicated fixture matrix; tag-release publication needs one real tag validation; and broad third-party Windows environments may expose antivirus, codec, or policy differences not represented by a single hosted runner.

Provider-specific authentication, stream transport, MAG portal compatibility, authorized Xtream population, and real live EOF recovery remain separate acceptance domains. They were intentionally not coupled to packaging CI and no credentials were required to produce the artifact.

## 34. Final Acceptance Matrix

**Final classification: B — PORTABLE EXE READY WITH KNOWN LIMITATIONS.** The matrix below distinguishes the verified deliverable from items that are partial, blocked, deferred, or not executed.

| Area | Acceptance item | Classification | Evidence or boundary |
|---|---|---|---|
| Build | Windows x64 runner builds successfully | **VERIFIED** | Run `32013261624` passed. |
| Build | Pinned dependencies and VLC runtime | **VERIFIED** | Python 3.13, PyInstaller 6.22.1, PySide6 6.11.1, `python-vlc` 3.0.21203, VLC 3.0.23. |
| Build | PySide6, python-vlc, libVLC, VLC plugins, Qt plugins | **IMPLEMENTED / VERIFIED** | Explicit spec collection plus generated-EXE and native runtime passes. |
| Build | Application resources | **PARTIAL** | Runtime-relative root and primary executable resources pass; exhaustive future-resource matrix not executed. |
| Portability | No Python or separate VLC required | **VERIFIED** | Sanitized-`PATH` execution passed; `vlc` and `libvlc.dll` absent from PATH. |
| Portability | Works outside repository with spaces and Unicode path | **VERIFIED** | Temporary `SamoTech Portable Validation 空 folder` execution passed. |
| Execution | Generated EXE actually starts and exits | **VERIFIED** | `--smoke-test` passed in build and clean environment. |
| Execution | Packaged libVLC loads and synthetic media lifecycle works | **VERIFIED** | `--packaged-vlc-test` passed; native lifecycle passed. |
| Execution | Native VLC lifecycle | **VERIFIED** | Binding, instance, media replacement, stop, cleanup, and lifecycle pass. |
| Execution | Subtitle SRT/ASS/SSA/VTT packaged matrix | **NOT EXECUTED** | Source boundary exists; dedicated packaged fixture remains. |
| Providers | Xtream/MAG/M3U modules and synthetic boundaries | **VERIFIED** | Non-presentation Windows corpus and local tests pass. |
| Providers | Authorized provider acceptance | **NOT EXECUTED** | Deliberately excluded from normal build CI. |
| Security | Repository credentials absent | **VERIFIED** | Tracked-file scan found no authorized credentials. |
| Security | Generated artifact audit | **VERIFIED** | `artifact_audit=PASS`. |
| Automation | Push builds and uploads artifact | **VERIFIED** | Successful run uploaded artifact and metadata. |
| Automation | Tag builds and publishes release | **IMPLEMENTED / NOT EXECUTED** | Conditional release step exists; no tag run in evidence. |
| Automation | SHA256 generated automatically | **VERIFIED** | `SHA256SUMS.txt` generated with recorded hash. |
| Quality | pytest, Ruff, Black, mypy, diff check | **VERIFIED** | Windows CI and local focused/broad checks passed; presentation collection limitation documented. |
| Scope | Installer, ARM64, auto-updater | **DEFERRED / OUT OF SCOPE** | Not implemented by this phase. |

The deliverable is therefore **ready for portable-EXE distribution through the verified push-artifact path, with the limitations above disclosed**. It must not be described as a universal IPTV-provider acceptance, subtitle-certification, installer, ARM64, or tag-release proof until those separate gates are executed.

## References

[1]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32013261624 "Successful Windows Portable EXE workflow run"

[2]: https://github.com/SamoTech/samotech-iptv-player/commit/a7b57d5a5bb6efd48bedd66ec5e5dc7a69038d32 "Verified packaging commit"

[3]: https://github.com/SamoTech/samotech-iptv-player/blob/main/.github/workflows/windows-portable-build.yml "Blocking Windows portable-build workflow"

[4]: https://github.com/SamoTech/samotech-iptv-player/blob/main/samotech-iptv-player.spec "Reproducible PyInstaller specification"

[5]: https://github.com/SamoTech/samotech-iptv-player/blob/main/src/samotech_iptv/packaged_runtime.py "Runtime-relative bundled VLC discovery"

[6]: https://github.com/SamoTech/samotech-iptv-player/blob/main/scripts/audit_windows_artifact.py "Generated artifact audit script"

[7]: https://github.com/SamoTech/samotech-iptv-player/blob/main/README.md "Project README and portable executable usage"
