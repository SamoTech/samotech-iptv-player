# SamoTech IPTV Player — First Automated GitHub Release Acceptance Audit

**Audit date:** 2026-08-17 UTC+03:00
**Repository:** [SamoTech/samotech-iptv-player](https://github.com/SamoTech/samotech-iptv-player)
**Tagged release:** [`v0.1.0`](https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.0)
**Tagged build commit:** `d1ab67325a59c6f86089dbe309e99ba7386dc24b`
**Workflow run:** [32016330754](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32016330754)
**Final status:** **A — FIRST GITHUB RELEASE VERIFIED**

This report is the single authoritative record for the first automated release acceptance. Every result is classified as **IMPLEMENTED**, **VERIFIED**, **PARTIAL**, **BLOCKED**, **DEFERRED**, or **NOT EXECUTED**. The report does not reproduce provider credentials, tokens, cookies, MAC addresses, private stream URLs, or raw provider payloads.

## 1. Initial Repository State

**VERIFIED.** Before release work, `git fetch origin main` completed successfully. The repository was on branch `main`, with HEAD `d1ab673` (`docs: finalize portable exe audit wording`), a clean worktree, and `git rev-list --left-right --count HEAD...origin/main` reporting `0 0`. The pre-tag HEAD and `origin/main` resolved to `d1ab67325a59c6f86089dbe309e99ba7386dc24b`.

No production code, packaging code, provider behavior, VLC packaging, installer, or auto-update system was changed for the release acceptance. The existing portable build was preserved.

## 2. Existing Release State

**VERIFIED.** Before creating the tag, GitHub reported no releases for the repository. This was confirmed through the repository release listing rather than assumed from local state. After the tagged workflow completed, the repository contained exactly one published release: `v0.1.0`.

## 3. Existing Tag State

**VERIFIED.** Before tag creation, neither a local `v0.1.0` tag nor an origin tag reference for `v0.1.0` existed. The authoritative application version was `0.1.0`, so the correct first release tag was `v0.1.0`. The created tag is annotated: tag object `71d7c0bc4f1e03c1b8922d4e6edad4a3901909cb`, resolving to commit `d1ab67325a59c6f86089dbe309e99ba7386dc24b`.

## 4. Workflow Audit

**IMPLEMENTED; VERIFIED.** The current `.github/workflows/windows-portable-build.yml` satisfies the release requirements:

| Requirement | Evidence | Classification |
|---|---|---|
| Tag trigger `v*.*.*` | `on.push.tags: ["v*.*.*"]` | **VERIFIED** |
| Write permission | `permissions: contents: write` | **VERIFIED** |
| Required release action | `softprops/action-gh-release@v2` | **VERIFIED** |
| Release gate ordering | Release step is after all build, test, smoke, audit, checksum, and upload steps | **VERIFIED** |
| Release assets | `dist/release/*.exe` and `dist/release/SHA256SUMS.txt` | **VERIFIED** |
| Generated release notes | `generate_release_notes: true` | **VERIFIED** |
| Blocking gates | No critical `continue-on-error` or failure suppression | **VERIFIED** |

The workflow continues to use the existing portable build; no competing release workflow was created.

## 5. Application Version

**VERIFIED.** `pyproject.toml` is the authoritative version source and declares:

```text
version = "0.1.0"
```

The tagged Windows job logged `Application version: 0.1.0`. No duplicate manually maintained application version was invented.

## 6. Release Tag

**VERIFIED.** The release tag is `v0.1.0`, derived directly from the authoritative application version. It was created as an annotated tag and pushed normally to origin. No duplicate tag was created, no existing tag was overwritten, and no force-push or history rewrite was used.

## 7. Tag Push Evidence

**VERIFIED.** The tag push returned:

```text
[new tag] v0.1.0 -> v0.1.0
```

The tag triggered workflow run `32016330754` with event `push`, branch/ref `v0.1.0`, and head SHA `d1ab67325a59c6f86089dbe309e99ba7386dc24b`.

## 8. GitHub Actions Run

**VERIFIED.** The tag-triggered workflow completed successfully:

| Field | Result |
|---|---|
| Run | `32016330754` |
| Job | `95346482024` |
| Event | `push` |
| Ref | `v0.1.0` |
| Head SHA | `d1ab67325a59c6f86089dbe309e99ba7386dc24b` |
| Duration | approximately 4 minutes 8 seconds |
| Conclusion | `success` |

The workflow sequence passed dependency installation, VLC acquisition and verification, Ruff, Black, mypy, pytest, native VLC lifecycle, PyInstaller, both generated-EXE smoke modes, sanitized-`PATH` validation, artifact audit, versioned naming, checksum generation, metadata, artifact upload, and release publication.

## 9. Windows Build Evidence

**VERIFIED.** The Windows runner built the tagged commit with Python 3.13, PyInstaller 6.22.1, PySide6 6.11.1, `python-vlc` 3.0.21203, and the pinned VLC 3.0.23 win64 runtime. VLC acquisition was verified against SHA256 `992d19dbd0b8a7cde9167d2f7780b1ef6f92acc8a71acfa736101a21f35181e1`.

The generated artifact was named using the required tagged-release form:

```text
SamoTech-IPTV-Player-Windows-x64-v0.1.0.exe
```

The generated EXE size reported by the artifact audit and GitHub Release asset metadata is **135,490,319 bytes**.

## 10. EXE Validation

**VERIFIED.** The actual executable generated by the tagged commit was executed, not merely checked for existence. The workflow passed both:

```text
--packaged-vlc-test
--smoke-test
```

The packaged-VLC test exercised the bundled runtime with safe synthetic media. The Qt/application smoke mode initialized the packaged application, processed Qt events, and exited successfully. The same modes passed again from outside the repository during sanitized-environment validation.

## 11. VLC Validation

**VERIFIED.** The Windows native VLC lifecycle probe passed against the pinned bundled runtime. The job reported successful native binding/instance/media lifecycle, media replacement, stop, cleanup, and final lifecycle status. The packaged-VLC smoke mode also passed against the runtime that was included in the generated executable.

This is provider-free synthetic-media validation. It does not claim live playback against an authorized IPTV provider.

## 12. Qt Validation

**VERIFIED for the generated executable.** The tagged workflow’s generated-EXE Qt/application smoke test passed. No missing Qt platform plugin, Python import, or application initialization failure occurred.

A separate test-collection limitation remains documented: importing `tests/test_presentation_smart_import_dialog.py` during the full Linux pre-release pytest collection caused a fatal Qt access violation. The Windows workflow intentionally excludes `test_presentation_*.py` from its non-Qt corpus while keeping the generated executable’s Qt smoke test blocking.

## 13. Clean Environment Validation

**VERIFIED.** The workflow copied the tagged executable into a temporary directory containing spaces and non-ASCII characters, then sanitized `PATH` to Windows system directories before running both executable smoke modes. The runner logged:

```text
where_python_available_before_sanitize=True
where_vlc_available_before_sanitize=False
where_libvlc_available_before_sanitize=False
```

Both smoke modes passed after sanitization. This verifies the tested EXE does not depend on a separately discoverable VLC installation or Python command through `PATH`.

## 14. Artifact Audit

**VERIFIED.** The generated-artifact audit reported:

```text
artifact_bytes=135490319
artifact_audit=PASS
```

The audit scans executable bytes for secret-shaped material and development leftovers. No credentials, private keys, credential-bearing URLs, bearer tokens, JWT-like material, Python source/bytecode, or repository artifacts were reported by the blocking audit.

## 15. SHA256

**VERIFIED.** The tagged workflow generated `SHA256SUMS.txt` with this entry:

```text
89c271df0ff3fbc79051fd8eaf3a71697eb0c63a9d87c42abebe4306769e4ae6  SamoTech-IPTV-Player-Windows-x64-v0.1.0.exe
```

The same SHA256 was reported in the tagged Windows job metadata and by the GitHub Release asset digest.

## 16. GitHub Artifact

**VERIFIED.** The successful tagged run uploaded the Actions artifact:

```text
windows-portable-d1ab67325a59c6f86089dbe309e99ba7386dc24b
```

GitHub reported the artifact container size as **135,030,640 bytes**, created at `2026-08-17T09:43:26Z`, and `expired=false`. The workflow configuration includes the versioned EXE, `SHA256SUMS.txt`, and `build-metadata.txt` in the uploaded artifact.

## 17. GitHub Release

**VERIFIED.** Exactly one release exists for the new version, and it is the published `v0.1.0` release:

| Field | Result |
|---|---|
| Release name | `v0.1.0` |
| Tag | `v0.1.0` |
| Draft | `false` |
| Prerelease | `false` |
| Published | `2026-08-17T09:43:34Z` |
| Release URL | https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.0 |
| Tag-resolved commit | `d1ab67325a59c6f86089dbe309e99ba7386dc24b` |

The release action executed only after the required build and artifact gates passed. No failed or partial release was published.

## 18. Release Assets

**VERIFIED.** The release contains exactly the required two assets, both in `uploaded` state:

| Asset | Size | GitHub asset digest |
|---|---:|---|
| `SamoTech-IPTV-Player-Windows-x64-v0.1.0.exe` | 135,490,319 bytes | `sha256:89c271df0ff3fbc79051fd8eaf3a71697eb0c63a9d87c42abebe4306769e4ae6` |
| `SHA256SUMS.txt` | 111 bytes | `sha256:8ae0c15c5e652eab2e2f40751410944e4684c0e3644c578131c0add6fd17c207` |

The EXE asset URL is https://github.com/SamoTech/samotech-iptv-player/releases/download/v0.1.0/SamoTech-IPTV-Player-Windows-x64-v0.1.0.exe. The checksum asset URL is https://github.com/SamoTech/samotech-iptv-player/releases/download/v0.1.0/SHA256SUMS.txt.

## 19. Release Notes

**VERIFIED with a documented repair.** The release action generated GitHub’s changelog section successfully. The generated notes initially described historical changes but did not include the required portable-EXE user-facing summary, so the release body was augmented without changing assets, code, packaging, or workflow gates. The final release notes describe Windows x64 Portable EXE distribution, no separate Python installation, no separate VLC installation, the portable artifact, and known limitations.

The final notes explicitly avoid claims of universal IPTV compatibility, MAG VOD/Series support, real-provider acceptance, subtitle certification, ARM64 support, installer support, Microsoft Store distribution, or auto-update support. A release-note augmentation was necessary; therefore the result is **VERIFIED** for content but **PARTIAL** against a strict zero-manual-intervention interpretation of release-note authoring.

## 20. Independent Checksum Verification

**VERIFIED.** Both release assets were downloaded from the published GitHub Release. The downloaded EXE was 135,490,319 bytes. Independent local hashing produced:

```text
89c271df0ff3fbc79051fd8eaf3a71697eb0c63a9d87c42abebe4306769e4ae6
```

Running `sha256sum -c SHA256SUMS.txt` from the downloaded asset directory returned:

```text
SamoTech-IPTV-Player-Windows-x64-v0.1.0.exe: OK
```

The published checksum, the independently calculated local hash, and GitHub’s EXE asset digest match exactly.

## 21. Security Review

**VERIFIED.** The generated artifact audit passed. The repository’s tracked-content credential scan found no authorized Xtream username or password. The release notes and release metadata contain no provider credentials, tokens, cookies, MAC addresses, private stream URLs, or other private acceptance data.

The release did not use a real provider, real IPTV stream, or authorized credentials as a build dependency. Existing credential boundaries and provider architecture were preserved.

## 22. Failure and Repair Evidence

**PARTIAL; no production-code repair was required.** The full Linux pre-release pytest command exited with code 139 during collection of `tests/test_presentation_smart_import_dialog.py`, demonstrating the existing Qt access-violation limitation. No production code was modified to conceal or bypass that failure. The independent non-presentation pytest corpus was then run successfully, matching the established Windows workflow exclusion.

One local checksum command initially failed because it was run from the repository root while `SHA256SUMS.txt` contained a relative basename. The verification was corrected by running `sha256sum -c` from the downloaded asset directory; it then returned `OK`. This was a command-location error, not a release defect.

The release action itself did not fail. The only release-content repair was augmenting generated release notes with the required portable-EXE summary after confirming that the assets and workflow result were correct.

## 23. Final Repository State

**VERIFIED.** Before tagging, HEAD and `origin/main` were synchronized at `d1ab67325a59c6f86089dbe309e99ba7386dc24b`, and the worktree was clean. The annotated tag was pushed without modifying the tagged commit. After the report commit was pushed, the final handoff verification reported matching HEAD and `origin/main`, a clean worktree, passing `git diff --check`, and no authorized credentials in tracked content. Temporary downloaded release assets and build logs remain outside tracked content.

## 24. Final Acceptance Matrix

| Acceptance item | Result | Classification |
|---|---|---|
| Current main verified before release | Branch `main`, ahead/behind `0 0`, clean | **VERIFIED** |
| Working tree clean before tag | No status entries | **VERIFIED** |
| Application version verified | `0.1.0` from `pyproject.toml` | **VERIFIED** |
| Correct version tag created | Annotated `v0.1.0` | **VERIFIED** |
| Tag pushed normally | `v0.1.0 -> v0.1.0` | **VERIFIED** |
| GitHub Actions triggered | Run `32016330754` | **VERIFIED** |
| Windows runner completed | Job success in about 4m8s | **VERIFIED** |
| Portable EXE built | Versioned EXE emitted | **VERIFIED** |
| Actual EXE validated | Packaged-VLC and Qt smoke passed | **VERIFIED** |
| Native VLC validation passed | Lifecycle probe passed | **VERIFIED** |
| Qt smoke passed | Generated EXE smoke passed | **VERIFIED** |
| Sanitized PATH validation passed | Unicode temporary path, no VLC on PATH | **VERIFIED** |
| Artifact audit passed | `artifact_audit=PASS` | **VERIFIED** |
| SHA256 generated | `SHA256SUMS.txt` uploaded | **VERIFIED** |
| GitHub Actions artifact uploaded | Artifact present and unexpired | **VERIFIED** |
| GitHub Release created | Exactly one published `v0.1.0` release | **VERIFIED** |
| Release EXE attached | Correct versioned filename | **VERIFIED** |
| Release SHA256 attached | `SHA256SUMS.txt` present | **VERIFIED** |
| SHA256 independently verified | Downloaded EXE hash matched checksum | **VERIFIED** |
| Release notes generated | Generated changelog preserved | **VERIFIED** |
| Required portable summary in notes | Added after publication | **VERIFIED / PARTIAL automation** |
| Release contains no secrets | Notes and metadata clean | **VERIFIED** |
| Final repository clean after report | Post-report verification returned clean | **VERIFIED** |
| HEAD synchronized after report commit | Post-report verification returned matching HEAD/origin/main | **VERIFIED** |

## 25. Known Limitations

**PARTIAL / BLOCKED / DEFERRED as labeled.** The full Linux pytest collection remains blocked by the known Qt access violation in `test_presentation_smart_import_dialog.py`; the Windows release workflow excludes presentation test modules while retaining blocking generated-EXE Qt smoke validation. Release-note content required a post-publication augmentation because the action-generated notes did not include the portable distribution summary. A strict zero-manual-intervention claim therefore applies to build, validation, checksum, asset upload, and release publication, but not to the final notes augmentation performed in this acceptance.

This release does not certify universal IPTV provider compatibility, real-provider acceptance, MAG VOD/Series, subtitle-format interoperability, ARM64, installers, auto-update, Microsoft Store distribution, or long-running codec compatibility. These remain deferred, out of scope, or not executed.

## 26. Final Status

**A — FIRST GITHUB RELEASE VERIFIED.** The authoritative version tag `v0.1.0` triggered the Windows workflow, the tagged Windows runner built and executed the actual portable EXE, native VLC and Qt validation passed, the sanitized-`PATH` test passed, the artifact was audited and checksummed, GitHub Actions uploaded the artifact, GitHub published exactly one release, both release assets are present, and the checksum was independently verified from the downloaded release assets.

The status is **A** under the specification’s explicit rule: a tagged workflow completed successfully and the GitHub Release contains the verified portable EXE and checksum. This classification does not expand the release’s documented scope or erase the known Qt collection and release-note automation limitations.

## References

[1]: https://github.com/SamoTech/samotech-iptv-player/actions/runs/32016330754 "Successful v0.1.0 tagged Windows workflow run"

[2]: https://github.com/SamoTech/samotech-iptv-player/releases/tag/v0.1.0 "Published v0.1.0 GitHub Release"

[3]: https://github.com/SamoTech/samotech-iptv-player/blob/main/.github/workflows/windows-portable-build.yml "Windows portable-build and release workflow"

[4]: https://github.com/SamoTech/samotech-iptv-player/blob/main/pyproject.toml "Authoritative application version"

[5]: https://github.com/SamoTech/samotech-iptv-player/blob/main/scripts/audit_windows_artifact.py "Generated artifact audit script"

[6]: https://github.com/SamoTech/samotech-iptv-player/releases/download/v0.1.0/SHA256SUMS.txt "Published v0.1.0 checksum asset"
