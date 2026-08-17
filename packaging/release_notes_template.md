# SamoTech IPTV Player v{{VERSION}}

## Windows Portable Edition

Download the portable Windows x64 executable:

`{{ARTIFACT}}`

## SHA256

```text
{{SHA256}}  {{ARTIFACT}}
```

## What's Included

- Windows x64 portable EXE
- Python runtime
- PySide6/Qt runtime
- `python-vlc`
- bundled libVLC/VLC `{{VLC}}` runtime
- required VLC plugins and application resources

## Installation

No installation is required. Download the EXE and run it. Verify the SHA256 checksum before execution.

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
