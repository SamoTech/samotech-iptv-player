# Security Policy

## Supported version

| Version | Supported |
|---|---|
| Latest commit on `main` | Yes |

The current verified product state is maintained in [PROJECT_STATUS.md](PROJECT_STATUS.md). This policy describes the repository’s current security boundaries; it does not claim a packaged production release or a formal security-service-level agreement.

## Reporting a vulnerability

Please **do not** open a public issue containing a vulnerability, provider credential, MAC/device identity, token, playback URL, portal payload, or account data.

Report a vulnerability to the project maintainer through the repository’s configured private contact channel. Include a concise description, safe reproduction steps using redacted or synthetic data, potential impact, and an optional proposed mitigation. Do not attach real IPTV account information or live provider captures.

## Sensitive data model

| Data | Why it is sensitive | Required handling |
|---|---|---|
| Provider username/password | Grants or may grant account access. | Store and retrieve through the OS keyring only; never commit, log, display, or persist in SQLite provider metadata. |
| MAG MAC address/device identity | Can identify and authorize a subscriber device. | Treat as a credential-bound sensitive identifier; do not store in provider metadata or user-facing summaries. |
| Session token/cookie | Runtime authorization material. | Keep private and volatile inside the provider adapter; never persist or expose through application DTOs/UI. |
| Tokenized or credential-bearing M3U URL | Query, fragment, or user-info may grant source access. | Store full source only through the secure credential boundary; persist a sanitized identifier source only. |
| Resolved playback URL | May contain provider credentials or temporary authorization. | Pass only from provider resolution to the player; do not log, persist, or display it. |
| Provider payload/portal fixture | Can contain account, device, channel, token, or URL material. | Use authorized, sanitized test fixtures only; do not commit real payloads. |
| Local recording path | May expose personal filesystem information. | Keep out of logs and generic UI feedback. |

## Current security boundaries

### Credentials and provider metadata

`KeyringCredentialStore` implements the application credential-store port through the operating-system keyring. Provider metadata is separately persisted with SQLite and is restricted to non-secret fields such as provider ID, provider type, sanitized base URL, activation, capabilities, and whether an M3U source is secure. It must not contain credentials, MAC identifiers, tokens, resolved links, or provider error text.

### Provider sessions and protocol DTOs

Provider adapters own their provider-specific sessions. The MAG/Stalker adapter keeps a session token in private runtime state. Xtream builds authenticated requests from credentials retrieved inside infrastructure. Application and presentation layers receive canonical domain records or safe DTOs rather than raw provider payloads, credentials, tokens, or live session objects.

### Presentation and logging

Qt dialogs show safe provider summaries and generic failures where detailed errors could expose sensitive infrastructure information. Logs must not include passwords, MAC addresses, tokens, tokenized URLs, resolved playback URLs, or local recording paths. Tests must use fake credentials, fake portal hosts, fake device identities, and fake media URLs.

### Parsing and input safety

- Canonical `URL` and `StreamURI` value objects validate the URL/URI forms they represent.
- XMLTV parsing uses `defusedxml` with document and entry limits plus explicit source-channel mappings.
- M3U loading restricts sources to local/file/HTTP(S) paths and protects sensitive remote source strings.
- The repository does not use `eval()`, `exec()`, or `pickle` for provider input processing.

### Trusted local plugins

The plugin SDK supports explicitly selected, trusted local Python files only. Plugin code is **not sandboxed** and has the operating-system permissions of the application process. The loader validates plugin identity, API version, and provider namespace, and activates registrations transactionally, but it does not provide a permission system, code signing, automatic discovery, remote download, marketplace, or updater. Enable only plugins whose source and author you trust. See [docs/PLUGIN_SDK.md](docs/PLUGIN_SDK.md).

## Development requirements

- Never commit secrets, tokens, private portal details, real device identities, or generated local data.
- Never use unknown device identities, scan portals, bypass subscriptions, or invoke administrative account/device APIs for a player feature.
- Preserve the domain → application → infrastructure/presentation dependency boundaries.
- Run the quality gate before every commit:

```bash
black --check src tests
ruff check src tests
mypy src
pytest -q
git diff --check
```

- Follow the direct-to-`main` workflow documented in [CONTRIBUTING.md](CONTRIBUTING.md).

## Related documents

- [PROJECT_STATUS.md](PROJECT_STATUS.md) — current support claims and known limitations.
- [ARCHITECTURE.md](ARCHITECTURE.md) — security-relevant dependency and data-flow boundaries.
- [docs/m3u_secure_source_design.md](docs/m3u_secure_source_design.md) — tokenized M3U source handling.
- [docs/PLUGIN_SDK.md](docs/PLUGIN_SDK.md) — trusted local plugin security model.
- [MINISTRA_COMPATIBILITY_ASSESSMENT.md](MINISTRA_COMPATIBILITY_ASSESSMENT.md) — Ministra implementation decision gate.
