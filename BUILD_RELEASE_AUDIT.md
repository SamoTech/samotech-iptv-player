# Build and Release Audit

## Result

**Packaging: CONDITIONAL. CI/CD: PASS.** The repository’s packaging configuration, runtime hook, Windows scripts, version metadata, checksum generation, artifact naming, release notes, acceptance workflow, and permissions were inspected. Linux-side syntax and configuration checks pass. The actual Windows portable executable and bundled VLC runtime could not be built or launched on this Linux host, so those steps are explicitly **NOT VERIFIED — ENVIRONMENT LIMITATION**.

## Dependencies

Runtime dependencies are limited to aiohttp, defusedxml, keyring, python-vlc, PySide6, and qasync. Development dependencies include pytest, pytest-asyncio, pytest-cov, aioresponses, Black, MyPy, Ruff, types-defusedxml, and pinned PyInstaller. Windows packaging requirements pin the packaging-critical versions of PyInstaller, PySide6, python-vlc, qasync, aiohttp, defusedxml, and keyring. No `uv.lock` is retained; the project’s baseline notes that the lock file is regenerated automatically and is removed before commits as required.

The direct project dependency manifest was scanned with pip-audit and returned no known vulnerabilities. The global system environment scan reported unrelated vulnerabilities in `pypdf`, `wheel`, and `xhtml2pdf`; these packages are not declared runtime dependencies of this project. The build-system requirement `wheel>=0.46.2` was considered as a hardening opportunity, but no blind dependency upgrade was applied because the direct manifest audit was clean and CI resolves current build tooling. This distinction is recorded rather than conflating global environment findings with application dependencies.

## PyInstaller and VLC packaging

`samotech-iptv-player.spec` requires `VLC_RUNTIME_DIR`, verifies `libvlc.dll`, `libvlccore.dll`, and the plugins directory, bundles VLC DLLs/plugins plus optional locale and Lua resources, collects legacy provider submodules, and installs a runtime hook that configures the bundled runtime. The spec emits version metadata from the package version and builds a one-file Windows x64 executable with development-only modules excluded.

The Windows build script removes stale `dist` and PyInstaller work directories, preserves the downloaded VLC runtime under a dedicated build path, invokes PyInstaller with `--clean --noconfirm`, and verifies the expected executable exists. The VLC preparation script downloads the official archive, verifies the pinned SHA256, expands it, checks for the complete runtime tree, and records the root path.

The Linux host verified Python syntax compilation of the spec and inspected the runtime/resource contracts. No Windows VLC DLLs, PowerShell, Wine, or Windows runner were available, so the actual build and executable smoke tests are not claimed as passed.

## CI/CD audit

The CI workflow installs Python 3.13, Qt offscreen support, development dependencies, Ruff, Black, MyPy, security regression tests, the full non-presentation suite, and coverage. CodeQL runs security-extended Python analysis with read-only contents and security-events write permissions.

The principal confirmed CI finding was excessive release authority: the Windows build workflow originally granted `contents: write` at workflow scope, including pull requests and ordinary main builds. The fix changes the workflow scope to `contents: read` and moves release publication into a dependent `publish-release` job with `contents: write`. The publish job runs only for version tags, downloads the exact validated artifact by SHA, and publishes the executable, checksum, and generated release notes. Configuration tests assert this contract.

## Artifact and release validation

The Windows workflow validates tag/version alignment, official VLC checksum, VLC DLL/plugin presence, Ruff, Black, MyPy, non-Qt tests, native VLC lifecycle, packaged-VLC smoke, Qt/application smoke, sanitized PATH startup, generated artifact contents, SHA256SUMS, build metadata, and automated release notes. The separate acceptance workflow downloads the exact release asset and verifies checksum, PE version metadata, path/environment matrix, first and second launch, packaged VLC, and Qt smoke.

## Verification table

| Check | Local result |
|---|---|
| PyInstaller spec Python syntax | PASS |
| Packaging/workflow contract tests | PASS |
| Direct dependency pip-audit | PASS |
| Windows PowerShell build | NOT VERIFIED — ENVIRONMENT LIMITATION |
| Official Windows VLC download/extraction | NOT VERIFIED — ENVIRONMENT LIMITATION |
| Windows native VLC probe | NOT VERIFIED — ENVIRONMENT LIMITATION |
| Generated EXE smoke tests | NOT VERIFIED — ENVIRONMENT LIMITATION |
| Sanitized Windows PATH matrix | NOT VERIFIED — ENVIRONMENT LIMITATION |
| Published release acceptance matrix | NOT VERIFIED — ENVIRONMENT LIMITATION |

## References

[1]: pyproject.toml "Project and dependency declarations"
[2]: packaging/windows-build-requirements.txt "Pinned Windows packaging dependencies"
[3]: samotech-iptv-player.spec "PyInstaller specification"
[4]: packaging/samotech_runtime_hook.py "Bundled VLC runtime hook"
[5]: scripts/build_windows.ps1 "Windows build script"
[6]: scripts/prepare_windows_vlc.ps1 "Pinned VLC preparation script"
[7]: .github/workflows/ci.yml "Continuous integration workflow"
[8]: .github/workflows/codeql.yml "CodeQL workflow"
[9]: .github/workflows/windows-portable-build.yml "Windows build and release workflow"
[10]: .github/workflows/windows-release-artifact-acceptance.yml "Release artifact acceptance workflow"
[11]: tests/test_windows_packaging_config.py "Packaging and workflow contract tests"
