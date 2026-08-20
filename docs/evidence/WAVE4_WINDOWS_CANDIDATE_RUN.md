# Wave 4 Windows Candidate Validation

**Candidate commit:** `fb41e6bb6aa8aafadd7390b4d2226b8386cf459f`
**Workflow:** [Windows Portable EXE run 32334691869](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32334691869)
**Result:** **PASS** — completed in 4 minutes 28 seconds.

The unchanged-version candidate passed installation, pinned VLC verification, Ruff, Black, MyPy, the Windows non-Qt corpus, native bundled-libVLC lifecycle validation, one-file EXE build, generated packaged-VLC and Qt smoke tests, the new optional sanitized debug-launcher smoke test, sanitized PATH and working-directory validation, artifact contents audit, EXE checksum generation, build metadata, and artifact upload. The tag-only version/release and automated-release-note steps were intentionally skipped because this was a main-branch candidate run rather than a release tag.

The hosted result provides packaging and startup/runtime evidence for the exact public-testing implementation. It does not assert decoded IPTV media, commercial-provider compatibility, multi-monitor behavior, or real user source credentials; those remain public-testing evidence gaps rather than successful compatibility claims.
