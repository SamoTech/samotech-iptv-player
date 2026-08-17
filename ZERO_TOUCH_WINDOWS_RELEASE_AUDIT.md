# SamoTech IPTV Player — Zero-Touch Windows Release Audit

**Audit date:** 2026-08-17 UTC+03:00
**Repository:** [SamoTech/samotech-iptv-player][1]
**Previous release:** `v0.1.0`, classified by the previous audit as **A — FIRST GITHUB RELEASE VERIFIED**, with manual post-publication release-note augmentation.
**New release:** [`v0.1.1`][2]
**Tagged build commit:** `5ba5938e3d398b27147732496591f0f2a49f7c45`
**Tagged workflow run:** [`32019974720`][3]
**Final status:** **A — ZERO-TOUCH RELEASE VERIFIED**

This report is the single authoritative record for the zero-touch Windows distribution acceptance. Every result is classified as **IMPLEMENTED**, **VERIFIED**, **PARTIAL**, **BLOCKED**, **DEFERRED**, or **NOT EXECUTED**. No provider credentials, tokens, cookies, MAC addresses, private URLs, authorization headers, or raw provider payloads are reproduced.

## 1. Executive Summary

**VERIFIED.** The previous manual release-note limitation was removed. A new semantic patch release, `v0.1.1`, was created from the current `origin/main`, pushed normally, built by the blocking Windows workflow, validated as an actual portable executable, checksummed, uploaded, and published as a GitHub Release. The release body was generated inside the tagged workflow from current version, artifact, checksum, workflow, build, toolchain, validation, and project-status metadata. No post-publication release edit was performed.

The published release contains exactly the versioned Windows x64 EXE and `SHA256SUMS.txt`. The downloaded EXE is a PE32+ Windows x86-64 GUI executable, has embedded `FileVersion=0.1.1` and `ProductVersion=0.1.1`, and has the following independently verified SHA256:

```text
f34b699cabd07efb409ebb96e3138a6990ac8d12d76dca0ee0127143e19417f5
```

## 2. Previous v0.1.0 Findings

**VERIFIED.** The previous audit established that the build, Windows validation, checksum, Actions artifact upload, and GitHub Release publication were automated, but GitHub’s default generated changelog did not contain the required portable-EXE user-facing summary. The release body was therefore manually augmented after publication. The previous workflow used `generate_release_notes: true` without a generated `body_path` containing the build-specific release summary.[1]

The new phase specifically addressed that limitation without changing provider protocols, IPTV architecture, VLC packaging, or adding an installer, ARM64 build, auto-update system, or real-provider test.

## 3. Initial Repository State

**VERIFIED.** Before implementation, `git fetch origin main` completed successfully. The repository was on branch `main`, HEAD was `038db7ad4d76247334631940b2e52391951ecf06`, `origin/main` matched it, ahead/behind was `0 0`, and the worktree was clean. The only existing local release tag was `v0.1.0`; the only existing GitHub Release was `v0.1.0`.

The implementation was then committed in logical steps and pushed normally. No force-push, tag deletion, history rewrite, or unrelated provider/playback change was used.

## 4. Release Pipeline Audit

**IMPLEMENTED; VERIFIED.** The release chain now follows:

```text
pyproject.toml version
        ↓
annotated v0.1.1 tag
        ↓
Windows GitHub Actions run
        ↓
version/tag validation
        ↓
Windows build and blocking tests
        ↓
actual EXE validation
        ↓
artifact name and SHA256
        ↓
dynamic release metadata
        ↓
generated release body via body_path
        ↓
GitHub Release and assets
```

The workflow retains the existing blocking gates and adds only release-specific validation and metadata generation. The release action was updated to the maintained `softprops/action-gh-release@v3`; the official action documentation supports loading generated notes through `body_path` and requires `contents: write` permission.[5]

| Pipeline requirement | Evidence | Classification |
|---|---|---|
| Tag trigger `v*.*.*` | Existing workflow tag trigger | **VERIFIED** |
| `contents: write` | Workflow permissions | **VERIFIED** |
| Tag/application version check | New blocking PowerShell step | **VERIFIED** |
| Dynamic body generation | `scripts/generate_release_notes.py` and template | **VERIFIED** |
| Release body publication | `body_path: dist/release/release-notes.md` | **VERIFIED** |
| Release assets | Versioned EXE and `SHA256SUMS.txt` | **VERIFIED** |
| Blocking quality and packaging gates | No critical `continue-on-error` | **VERIFIED** |

## 5. Root Cause of Manual Notes

**VERIFIED.** The root cause was a **missing user-facing release summary in the release-body handling**, not a packaging or checksum defect. The old workflow asked GitHub to generate release notes from repository changes. GitHub generated a historical changelog, but it had no build-time input containing the current EXE filename, SHA256, size, CI validation outcome, toolchain versions, or current limitations. The previous acceptance consequently used a manual `gh release edit` operation after publication.

The workflow had no authoritative release template, no metadata-driven body generator, and no regression test rejecting stale or missing release fields. The new implementation closes all three gaps.

## 6. Release Notes Architecture

**IMPLEMENTED; VERIFIED.** The architecture has four layers. `packaging/release_notes_template.md` is the structure and contains placeholders only. The tagged workflow creates `build/release-metadata.txt` from current job values after the EXE and checksum exist. `PROJECT_STATUS.md` supplies the marked authoritative limitation block. `scripts/generate_release_notes.py` validates and renders these inputs into `dist/release/release-notes.md`, which is passed to the release action with `body_path`.

The generator fails closed when metadata is missing, the tag does not match the application version, the artifact is not an EXE, the checksum is malformed, the artifact size is invalid, the limitations markers are absent, or the template contains stale hard-coded version/hash material. This prevents a release from silently publishing an incomplete or stale body.

## 7. Implementation

**IMPLEMENTED.** The implementation consists of the following bounded changes:

| Change | Purpose | Classification |
|---|---|---|
| `scripts/generate_release_notes.py` | Parse, validate, and render current release metadata | **IMPLEMENTED** |
| `packaging/release_notes_template.md` | Authoritative release-body structure with placeholders | **IMPLEMENTED** |
| Workflow metadata step | Captures commit, tag, artifact, hash, size, timestamp, toolchain, and validation data | **IMPLEMENTED** |
| Workflow tag check | Fails when `vX.Y.Z` does not equal `pyproject.toml` version | **IMPLEMENTED** |
| `softprops/action-gh-release@v3` with `body_path` | Publishes the generated body without manual editing | **IMPLEMENTED** |
| `src/samotech_iptv/version.py` | Resolves version from authoritative `pyproject.toml`, source or packaged | **IMPLEMENTED** |
| `core/constants.py` and PyInstaller spec | Uses and bundles the authoritative version source | **IMPLEMENTED** |
| `pyproject.toml` | Advances the next semantic patch version to `0.1.1` | **IMPLEMENTED** |

Provider architecture, MAG, Xtream, M3U, qasync, shared libVLC, PlayerPort, ResolvedPlayback, and Live EOF recovery were not redesigned.

## 8. Test Coverage

**VERIFIED.** New deterministic tests cover release-note substitution for version, EXE filename, SHA256, commit, workflow, size, limitations, and build metadata. They also verify rejection of stale hard-coded version/hash content, missing metadata, mismatched tag/version, and missing authoritative limitation markers. A version-consistency test confirms that application constants resolve to the `pyproject.toml` version.

The focused suite passed with **15 tests**. The existing Windows packaging configuration tests were updated to require the tag validation step, generator step, `body_path`, maintained release action, and build timestamp metadata.

## 9. Version Handling

**VERIFIED.** The authoritative application version is `0.1.1` in `pyproject.toml`.[4] The correct next version was the semantic patch release `v0.1.1`, because the current published release was `v0.1.0` and this phase adds release-engineering fixes without a provider or product feature change.

The annotated tag `v0.1.1` resolves to commit `5ba5938e3d398b27147732496591f0f2a49f7c45`. The tagged Windows workflow logged application version `0.1.1`, and its blocking tag check passed.

## 10. Windows Build

**VERIFIED.** Tagged workflow run `32019974720` completed successfully on `windows-latest` in approximately 4 minutes 20 seconds. The run executed the pinned dependency installation, Python 3.13 setup, VLC acquisition, tag/version validation, VLC verification, Ruff, Black, mypy, the Windows non-presentation pytest corpus, native VLC lifecycle, PyInstaller build, both generated-EXE smoke modes, sanitized PATH validation, artifact audit, versioned naming, metadata generation, release-note generation, artifact upload, and GitHub Release publication.[3]

The release artifact is:

```text
SamoTech-IPTV-Player-Windows-x64-v0.1.1.exe
```

The published EXE size is **135,491,662 bytes**.

## 11. EXE Validation

**VERIFIED.** The tagged workflow executed the actual generated executable using:

```text
--packaged-vlc-test
--smoke-test
```

Both passed. The packaged-VLC mode exercised safe synthetic media against the bundled VLC runtime. The Qt smoke mode initialized the packaged application, processed events, and shut down successfully. The downloaded release asset has the same SHA256 as the generated artifact recorded by the tagged workflow, proving the published bytes are the validated build output.

## 12. VLC Validation

**VERIFIED.** Native VLC lifecycle validation passed against the pinned VLC 3.0.23 runtime. The generated EXE packaged-VLC test also passed. VLC was acquired and verified using the pinned ZIP SHA256 `992d19dbd0b8a7cde9167d2f7780b1ef6f92acc8a71acfa736101a21f35181e1`.

This is synthetic-media and native lifecycle validation. It does not claim real IPTV-provider playback acceptance.

## 13. Qt Validation

**VERIFIED for the generated executable.** The generated executable’s Qt/application smoke test passed in the tagged Windows workflow. The existing presentation-test collection access violation remains excluded from the Windows non-Qt test corpus, while the executable-level Qt smoke test remains blocking.

## 14. Clean Environment

**VERIFIED.** The Windows workflow copied the generated EXE into a temporary directory containing spaces and non-ASCII characters, sanitized PATH to system directories, and ran both smoke modes. The runner logged that VLC and `libvlc.dll` were not available through PATH before sanitization, while both executable tests still passed. The workflow therefore verifies runtime-relative packaged discovery rather than dependence on a system VLC installation or developer working directory.

## 15. User-Like Download Test

**VERIFIED by byte-equivalent release validation; PARTIAL for direct local execution.** The EXE and checksum were downloaded from the actual GitHub Release into an isolated directory. The EXE was confirmed as `PE32+ executable (GUI) x86-64, for MS Windows`, and its SHA256 exactly matched the workflow-generated and GitHub asset digest.

The tagged Windows job executed the same bytes outside the repository from a temporary Unicode/space-containing path with sanitized PATH. Direct execution of the downloaded Windows file inside this Linux sandbox was **NOT EXECUTED** because no Windows host or Wine layer was available (`wine=unavailable`). The exact hash equivalence means the published release asset is the same binary that passed the Windows outside-repository execution gate.

## 16. Artifact Audit

**VERIFIED.** The blocking artifact audit passed on the tagged generated EXE. The audit scanned for credentials, private keys, token-shaped material, credential-bearing URLs, Python source/bytecode, and development leftovers. No failure was reported.

## 17. SHA256

**VERIFIED.** The workflow generated and published:

```text
f34b699cabd07efb409ebb96e3138a6990ac8d12d76dca0ee0127143e19417f5  SamoTech-IPTV-Player-Windows-x64-v0.1.1.exe
```

The file is 135,491,662 bytes. Independent hashing of the downloaded release asset produced the same SHA256.

## 18. GitHub Artifact

**VERIFIED.** The successful tagged run uploaded the Actions artifact:

```text
windows-portable-5ba5938e3d398b27147732496591f0f2a49f7c45
```

GitHub reported the artifact container size as **135,031,803 bytes**, created at `2026-08-17T10:28:06Z`, and `expired=false`. It contains the generated release EXE, `SHA256SUMS.txt`, and build metadata.

## 19. GitHub Release

**VERIFIED.** Exactly one new published release exists for `v0.1.1`; the prior `v0.1.0` release remains intact. The new release is not a draft and is not a prerelease.

| Release field | Result |
|---|---|
| Name/title | `v0.1.1` |
| Tag | `v0.1.1` |
| Tag-resolved commit | `5ba5938e3d398b27147732496591f0f2a49f7c45` |
| Workflow head SHA | `5ba5938e3d398b27147732496591f0f2a49f7c45` |
| Draft | `false` |
| Prerelease | `false` |
| Published | `2026-08-17T10:28:18Z` |
| Release URL | https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.1 |

## 20. Release Notes

**VERIFIED.** The published release body contains the dynamically generated current version, versioned EXE filename, SHA256, commit, workflow URL, Windows x64 architecture, portable distribution explanation, no-Python requirement, no-VLC-installation requirement, actual validation summary, known limitations, build timestamp, Python, PyInstaller, PySide6, `python-vlc`, and VLC versions.

The body begins with `# SamoTech IPTV Player v0.1.1`, includes the exact current artifact hash, and contains no stale `v0.1.0` artifact or hash. The published body is the generated `body_path` output; it was not manually edited after publication.

## 21. Zero-Manual-Intervention Evidence

**VERIFIED.** The tagged workflow log shows `Generate automated release notes` completing with `release-notes generated: dist\release\release-notes.md` before upload and publication. The release body contains values generated at the same run, including run ID `32019974720`, tagged commit `5ba5938e3d398b27147732496591f0f2a49f7c45`, build timestamp `2026-08-17T10:27:59Z`, artifact size, and hash.

No manual `gh release edit` operation was performed for `v0.1.1`. No manual EXE upload, manual checksum generation, or manual release-body modification was performed. The only developer actions for the release were committing the implementation/documentation changes, pushing `main`, creating the annotated tag, and pushing the tag.

## 22. Security

**VERIFIED.** The downloaded release body and checksum contain no credentials, passwords, tokens, cookies, MAC addresses, authorization headers, private URLs, or developer-local paths. The saved v0.1.1 workflow log contains no scanned credential or secret patterns. Ephemeral GitHub-hosted runner paths appear in raw CI diagnostics, but they are not included in the release body, checksum, metadata fields, or artifact.

Tracked repository scans found no authorized Xtream credentials. No real provider credentials or real provider streams were used for this release acceptance.

## 23. SmartScreen/Code Signing Status

**DEFERRED.** The generated EXE is not code-signed. The workflow and packaging configuration contain no certificate, Authenticode, `signtool`, or SmartScreen bypass step. The Linux sandbox had no `osslsigncode`, Windows SmartScreen, or Windows shell available for direct reputation-warning inspection. The release makes no code-signing claim and does not attempt to bypass Windows security.

## 24. Regression Results

**VERIFIED.** The focused generator and packaging regression suite passed with 15 tests. The full non-presentation regression corpus also passed locally. The tagged Windows workflow passed its blocking non-presentation pytest corpus. Ruff, Black, and mypy passed locally and in the tagged Windows workflow.

The known Qt presentation-test collection access violation remains a documented environment limitation. It was not hidden by weakening assertions or changing provider/product behavior.

## 25. Documentation

**IMPLEMENTED.** The following documentation was updated only where justified:

| File | Update |
|---|---|
| `README.md` | Documents generated release bodies, zero-touch tag flow, versioned artifacts, checksum publication, and Windows x64 scope |
| `CHANGELOG.md` | Records the dynamic release generator, tag/version validation, maintained release action, and v0.1.1 acceptance target |
| `PROJECT_STATUS.md` | Sets the current package version to `0.1.1` and provides the marked authoritative limitation block consumed by the generator |
| `ZERO_TOUCH_WINDOWS_RELEASE_AUDIT.md` | This evidence-backed final report |

No provider, playback, installer, ARM64, auto-update, or SmartScreen-bypass documentation was added.

## 26. Git History

**VERIFIED.** Logical commits were used:

| Commit | Purpose |
|---|---|
| `1f231fd` | `ci: automate portable release notes` |
| `ad296a5` | `test: validate release metadata generation` |
| `5ba5938` | `docs: document zero-touch windows releases` |

The annotated tag `v0.1.1` points to the final pre-tag commit `5ba5938e3d398b27147732496591f0f2a49f7c45`. No force-push or history rewrite was used.

## 27. Push Verification

**VERIFIED.** The implementation, tests, and documentation were pushed normally to `origin/main` before the tag was created. The tag was pushed normally and triggered the successful workflow. The tagged run and published release both identify the same commit SHA.

## 28. Known Limitations

**PARTIAL / DEFERRED as labeled.** Windows presentation-test collection remains blocked by the known Qt access violation and is excluded from the Windows non-Qt corpus. Direct execution of the downloaded Windows binary inside this Linux sandbox was not possible because no Windows or Wine runtime was available; exact SHA256 equivalence plus the tagged Windows outside-repository execution gate provides the release validation bridge.

The distribution is Windows x64 portable EXE only. The release does not claim universal IPTV compatibility, real-provider acceptance, MAG VOD/Series acceptance, subtitle certification, ARM64 support, installer support, auto-update support, Microsoft Store support, or code signing.

## 29. Deferred Items

**DEFERRED.** Certificate acquisition and Authenticode signing, SmartScreen reputation measurement on a real Windows desktop, ARM64 packaging, installer formats, auto-update, Microsoft Store distribution, broad codec/enterprise-environment testing, authorized-provider runtime acceptance, populated real Xtream acceptance, and production subtitle interoperability remain separate phases.

## 30. Final Acceptance Matrix

| Acceptance item | Result | Classification |
|---|---|---|
| Current `origin/main` audited | HEAD synchronized and clean before implementation | **VERIFIED** |
| Previous v0.1.0 limitation identified | Default notes lacked build-specific user summary | **VERIFIED** |
| Dynamic release mechanism implemented | Template, generator, metadata, body_path | **IMPLEMENTED** |
| Deterministic regression tests added | 15 focused tests passed | **VERIFIED** |
| Version source verified | `pyproject.toml` = `0.1.1` | **VERIFIED** |
| Annotated v0.1.1 tag created and pushed | Normal tag push | **VERIFIED** |
| Windows workflow triggered | Run `32019974720` | **VERIFIED** |
| Dependency installation passed | Tagged Windows job | **VERIFIED** |
| Ruff passed | Local and Windows job | **VERIFIED** |
| Black passed | Local and Windows job | **VERIFIED** |
| mypy passed | Local and Windows job | **VERIFIED** |
| pytest passed | Non-presentation corpus | **VERIFIED** |
| Native VLC lifecycle passed | Tagged Windows job | **VERIFIED** |
| PyInstaller build passed | Tagged Windows job | **VERIFIED** |
| Packaged VLC test passed | Generated EXE | **VERIFIED** |
| Qt smoke passed | Generated EXE | **VERIFIED** |
| Sanitized PATH and Unicode path passed | Generated EXE outside repository | **VERIFIED** |
| Artifact audit passed | Tagged Windows job | **VERIFIED** |
| Versioned artifact name correct | `...-v0.1.1.exe` | **VERIFIED** |
| SHA256 generated | `SHA256SUMS.txt` | **VERIFIED** |
| Build metadata generated | Safe current metadata | **VERIFIED** |
| Automated release body generated | `body_path` source created by workflow | **VERIFIED** |
| GitHub Actions artifact uploaded | Artifact present and unexpired | **VERIFIED** |
| GitHub Release published | Exactly one new `v0.1.1` release | **VERIFIED** |
| EXE attached | Versioned EXE asset uploaded | **VERIFIED** |
| SHA256 attached | `SHA256SUMS.txt` uploaded | **VERIFIED** |
| Release notes require no manual modification | No post-publication edit; dynamic body matches run | **VERIFIED** |
| Downloaded EXE hash independently verified | `sha256sum -c` returned `OK` | **VERIFIED** |
| Downloaded EXE direct local run | No Windows/Wine runtime in sandbox | **NOT EXECUTED** |
| Downloaded EXE byte-equivalent Windows run | Same hash as Windows-tested generated EXE | **VERIFIED** |
| No Python/VLC required in validated path | Sanitized PATH Windows smoke passed | **VERIFIED** |
| No credentials exposed | Release outputs and logs scanned | **VERIFIED** |
| No developer paths in release outputs | Body and checksum clean | **VERIFIED** |
| SmartScreen/code signing | No signing infrastructure | **DEFERRED** |
| Final repository clean and synchronized | To be checked after this report commit | **NOT EXECUTED** |

## 31. Final Status

**A — ZERO-TOUCH RELEASE VERIFIED.** A new release was published successfully; the complete release body was generated automatically from current build metadata and authoritative project-status limitations; no manual post-publication modification was required; the actual release EXE was downloaded; the checksum was independently verified; and the published bytes match the EXE validated by the tagged Windows workflow outside the repository.

This classification does not claim code signing, SmartScreen reputation, real-provider IPTV acceptance, universal compatibility, ARM64, installer, auto-update, or other deferred capabilities. Those boundaries are explicitly recorded above.

## References

[1]: https://github.com/SamoTech/samotech-iptv-player/blob/main/WINDOWS_PORTABLE_EXE_BUILD_AUDIT.md "Previous v0.1.0 release audit"

[2]: https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.1 "Published v0.1.1 GitHub Release"

[3]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32019974720 "Successful v0.1.1 tagged Windows workflow run"

[4]: https://github.com/SamoTech/samotech-iptv-player/blob/main/pyproject.toml "Authoritative application version"

[5]: https://github.com/softprops/action-gh-release "Official softprops/action-gh-release documentation"

[6]: https://github.com/SamoTech/samotech-iptv-player/releases/download/v0.1.1/SHA256SUMS.txt "Published v0.1.1 checksum asset"

[7]: https://github.com/SamoTech/samotech-iptv-player/blob/main/PROJECT_STATUS.md "Authoritative project status and release limitations"

[8]: https://github.com/SamoTech/samotech-iptv-player/blob/v0.1.1/.github/workflows/windows-portable-build.yml "Tagged v0.1.1 release workflow"
