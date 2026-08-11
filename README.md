# SamoTech IPTV Player

> **Project status: core architecture recovery complete; desktop client not yet implemented.**

SamoTech IPTV Player is an in-progress, open-source IPTV project. This revision provides a **tested Python core** with Clean Architecture boundaries, configuration composition, provider registration, and a MAG/Stalker provider adapter. It does **not** yet include a runnable PySide6/WinUI desktop application, VLC playback integration, database persistence, or an end-user playlist-management interface.

[![CI](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/ci.yml/badge.svg)](https://github.com/SamoTech/samotech-iptv-player/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)

## Capability status

| Status | Capability | Notes |
|---|---|---|
| **Implemented** | Core, domain, application, and infrastructure boundaries | Application provider ports are domain-oriented; infrastructure adapters translate external protocol data into domain entities and value objects. |
| **Implemented** | Provider registry and explicit factory registration | Adapters are registered by the composition root rather than import-time global state. |
| **Implemented** | MAG/Stalker provider core | Authentication, channel catalogue loading, local channel search, EPG loading, stream URL resolution, error translation, and session refresh are covered by unit and integration tests using test-only providers. |
| **Implemented** | Configuration composition | `ConfigurationProvider` owns `IPTV_*` environment parsing with explicit override → environment → default precedence. |
| **Implemented** | Extended M3U parsing | `M3UParser` translates `#EXTINF` metadata and HTTP(S) stream URLs into canonical `Channel` and `Stream` entities with deterministic IDs and malformed-input errors. |
| **Implemented** | VOD catalogue validation | `Movie` and `Series` enforce nonblank identity/title metadata, nonblank supplied categories, positive years, and ratings between 0.0 and 10.0. |
| **Implemented** | User-library validation | `Favorite` and `History` reject blank identifiers and unsupported item types; history also rejects negative playback values and positions beyond a known duration. |
| **Implemented** | Stream metadata validation | `Stream` rejects blank containers/codecs and non-positive supplied bitrates while preserving optional codec and bitrate metadata. |
| **Implemented** | Catalogue grouping and provider validation | `Category` and `Playlist` reject blank identifiers and names; supplied category parents must be nonblank. `Provider` also rejects a blank factory discriminator. |
| **Implemented** | Programme-record validation | `Channel` rejects blank supplied category/EPG references, while `Episode` and `EPGEntry` enforce required identity/title metadata and safe numeric or temporal boundaries. |
| **Implemented** | Value-object validation | Identifier, credential, and URL value objects have focused validation, redaction, and immutable value-semantics coverage. URLs require complete whitespace-free HTTP(S) authorities. |
| **Implemented** | Credential/session separation | A MAG connection identity is distinct from the short-lived runtime session token. Tokens are not stored in provider metadata. |
| **Partially implemented** | Secure credential storage | A keyring-backed credential-store adapter exists. Its deployment and platform integration remain to be exercised by the future application composition root. |
| **Planned** | M3U/Xtream application adapters and playlist management | Legacy/provider scaffolding exists, but these are not yet integrated through the canonical application provider contract. |
| **Planned** | Playback, persistence, desktop UI, EPG grid, recording, plugins, settings, updater, packaging | See [ROADMAP.md](ROADMAP.md). |

## Architecture

The project follows Clean Architecture. Dependencies point inward; the domain does not depend on provider protocols, UI frameworks, HTTP clients, or persistence libraries.

```text
Presentation (planned) → Application → Domain
                         ↑
              Infrastructure adapters
                         ↑
              MAG/Stalker protocol

Core supports all layers.
```

The provider boundary is domain-oriented. For example, MAG protocol records are translated into `Channel`, `EPGEntry`, and `URL` domain objects before application use cases map them to presentation-facing DTOs. See [ARCHITECTURE.md](ARCHITECTURE.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the broader design.

## Verified developer setup

The project currently supports development and core verification—not launching a desktop player.

```bash
# Clone and enter the repository
git clone https://github.com/SamoTech/samotech-iptv-player.git
cd samotech-iptv-player

# Create an isolated environment and install all development tooling
python -m venv .venv
. .venv/bin/activate                    # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e '.[dev]'

# Run the full quality gate
ruff check src tests
mypy src
pytest -q
```

A clean normal installation is also supported with `pip install .`. Python **3.12 or newer** is required; CI verifies Python 3.13.

## Configuration

`ConfigurationProvider` is the single process-environment composition boundary. Explicit constructor overrides take precedence over `IPTV_*` variables, which take precedence over defaults.

| Variable | Default | Purpose |
|---|---:|---|
| `IPTV_DEBUG` | `false` | Enable debug configuration. |
| `IPTV_LOG_LEVEL` | `INFO` | Logging level. |
| `IPTV_DATA_DIR` | `~/.samotech_iptv` | Future application data directory. |
| `IPTV_CONNECT_TIMEOUT` | `10.0` | TCP connection timeout in seconds. |
| `IPTV_READ_TIMEOUT` | `30.0` | Read timeout in seconds. |
| `IPTV_MAX_RETRIES` | `3` | HTTP retry attempts. |
| `IPTV_TLS_VERIFY` | `true` | TLS certificate verification. |
| `IPTV_BUFFER_MB` | `16` | Future player buffer size. |
| `IPTV_HW_DECODE` | `true` | Future hardware-decoding preference. |

## MAG provider integration

The MAG/Stalker adapter requires a registered portal URL and a MAG connection identity. At the application boundary, the credential username represents the authorized MAC address; the generic password is stored through the credential-store contract but is not sent by the current MAG handshake protocol. Short-lived portal tokens stay within the live adapter/session and are never copied to provider metadata or logs.

Do not commit portals, authorized MAC addresses, credentials, or session tokens. Use only test data in local test fixtures.

## Project phases

The initial scaffold, core recovery, and **Phase 2 domain/parser completion** are complete: an extended M3U parser plus validated catalogue, library, stream, programme-record, and value-object contracts are delivered with focused tests. M3U provider-adapter integration remains deliberately deferred to future provider-management work. The desktop player and UI remain later phases, after the provider/application core is extended. See [ROADMAP.md](ROADMAP.md) for the complete sequence.

## Contributing and security

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting changes. Report vulnerabilities according to [SECURITY.md](SECURITY.md); do not open public issues containing sensitive IPTV credentials or tokens.

## License

MIT — see [LICENSE](LICENSE).
