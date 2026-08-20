# SamoTech IPTV Player v{{VERSION}}

## Windows Portable Edition

Download the portable Windows x64 executable:

`{{ARTIFACT}}`

> **This is a public testing release.** The project has been validated extensively at the architecture, application, security, deterministic-test, and Windows packaging levels. Real IPTV compatibility depends on provider implementation, stream format, headers/session behavior, codecs, and network conditions. Commercial IPTV compatibility is not universally certified. Test using your own legitimate IPTV source.

## SHA256

```text
{{SHA256}}  {{ARTIFACT}}
```

## What's Included

- Windows x64 portable EXE
- Optional `SamoTech-Debug.bat` local diagnostic launcher
- Python runtime
- PySide6/Qt runtime
- `python-vlc`
- bundled libVLC/VLC `{{VLC}}` runtime
- required VLC plugins and application resources

## Installation

No installation is required. Download the EXE and run it. Verify the SHA256 checksum before execution.

## Real-World Testing and Diagnostics

Add one legitimate source using **Providers → Add IPTV Provider**. M3U/M3U8 supports a local file or playlist URL. Xtream uses server URL, username, and password. MAG/Stalker remains limited to the existing portal and device-identity flow. Playback diagnostics are available from **Player Controls → Info**; use **Copy Diagnostic Report** when reporting an issue. The optional `SamoTech-Debug.bat` launcher keeps a local console open for sanitized lifecycle events while normal users can continue launching the EXE directly.

Do not post passwords, tokens, cookies, authorization headers, MAC addresses, private playlist URLs, or credential-bearing URLs. No credentials are collected by SamoTech.

## Requirements

Windows x64. No separate Python installation is required. No separate VLC installation is required. No repository checkout or developer PATH is required for the validated portable path.

## Validation

The tagged GitHub Actions workflow completed all blocking Windows release gates before generating this release body:

`{{VALIDATION_SUMMARY}}`

- Workflow: [{{WORKFLOW_RUN}}]({{WORKFLOW_URL}})
- Tagged commit: `{{COMMIT}}`
- Generated artifact size: `{{SIZE_BYTES}}` bytes

## Known Limitations

{{KNOWN_LIMITATIONS}}

Real-world provider compatibility is still being validated. Use your own legitimate IPTV source. This release does not claim universal M3U, Xtream, MAG, codec, stream-format, or commercial-provider compatibility.

## Build Information

| Field | Value |
|---|---|
| Application version | `{{VERSION}}` |
| Release tag | `{{RELEASE_TAG}}` |
| Build timestamp (UTC) | `{{BUILD_TIMESTAMP_UTC}}` |
| Architecture | `{{ARCHITECTURE}}` |
| Python | `{{PYTHON}}` |
| PyInstaller | `{{PYINSTALLER}}` |
| PySide6 | `{{PYSIDE6}}` |
| python-vlc | `{{PYTHON_VLC}}` |
| VLC | `{{VLC}}` |
