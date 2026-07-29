# SamoTech IPTV Player

> A modern, open-source IPTV desktop player for Windows — built with Python, PySide6, and VLC.

[![CI](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/ci.yml/badge.svg)](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)

## Features

- 🎬 M3U / M3U8 / Xtream Codes / Stalker Portal playlist support
- 📅 XMLTV EPG with live grid timeline
- ⭐ Favorites, watch history, full-text channel search
- 🎙️ Stream recording via libVLC
- 🔌 Plugin SDK for custom providers, metadata, and themes
- 🌙 Dark / Light theme engine with QSS
- 🔒 Credentials stored in Windows Credential Manager (never in plaintext)
- ⚡ Auto-updater via GitHub Releases

## Architecture

Clean Architecture (Robert C. Martin) with strict Dependency Rule enforcement.
See [ARCHITECTURE.md](ARCHITECTURE.md) for the full blueprint.

```
[Presentation] → [Application] → [Domain]
      ↓                ↓
[Infrastructure] implements [Application Ports]
[Core] used by all layers
[Plugins] extend via SDK interfaces
```

## Quick Start

```powershell
# Install uv (if not already installed)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone and set up
git clone https://github.com/SamoTech/samotech-iptv-player.git
cd samotech-iptv-player
./scripts/install_dev.ps1

# Run
uv run python -m samotech_iptv.presentation.app
```

## Development

```powershell
./scripts/run_tests.ps1          # Run full test suite
./scripts/build.ps1              # PyInstaller Windows build
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the phased delivery plan.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md) for the vulnerability disclosure policy.

## License

MIT — see [LICENSE](LICENSE).
