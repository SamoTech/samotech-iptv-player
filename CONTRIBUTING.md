# Contributing

SamoTech IPTV Player is an extensible, provider-agnostic IPTV desktop-player foundation. Contributions must preserve its Clean Architecture boundaries, credential-safe provider model, libVLC-only player policy, PySide6/Qt-only desktop policy, and evidence-based documentation standards.

## Before changing code

Read [PROJECT_STATUS.md](PROJECT_STATUS.md), [ARCHITECTURE.md](ARCHITECTURE.md), [ROADMAP.md](ROADMAP.md), [PRODUCT_GAP_ANALYSIS.md](docs/historical/PRODUCT_GAP_ANALYSIS.md), and [SECURITY.md](SECURITY.md). The current product status is authoritative in `PROJECT_STATUS.md`; historical reports and old phase notes are not substitutes for checking the source and tests.

Do not infer provider capability from a protocol name, an enum value, or an abstract port. Verify the adapter implementation and its tests before claiming support.

## Setup

```bash
git clone https://github.com/SamoTech/samotech-iptv-player.git
cd samotech-iptv-player
python -m venv .venv
. .venv/bin/activate             # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -e '.[dev]'
```

Python 3.12 or newer is required. CI validates Python 3.13.

## Required development workflow

`main` is the active development branch. The project uses a permanent direct-to-main workflow:

```text
Inspect → Implement → Test → Quality gate → Commit → Push origin/main → Verify remote → Continue
```

Do **not** create a feature branch or pull request unless explicitly requested. Do **not** commit known failures. Use logical, conventional commit prefixes such as `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, or `chore:`.

Before every commit, run:

```bash
black --check src tests
ruff check src tests
mypy src
pytest -q
git diff --check
```

The repository CI also checks `providers/` and runs coverage on Python 3.13. Local changes must at minimum satisfy the project quality gate above.

## Architecture rules

The required dependency direction is:

```text
Presentation → Application → Domain
                    ↑
         Infrastructure implements application ports
```

- The domain must not import provider clients, Qt, libVLC, SQLite, `aiohttp`, keyring, or other infrastructure/UI libraries.
- The application must depend on abstract ports, domain records, and core utilities—not infrastructure or presentation concrete implementations.
- Infrastructure adapters own protocol DTOs, HTTP, persistence, keyring, libVLC, sessions, and translations to canonical records.
- Presentation must invoke application use cases; it must not access provider credentials, provider sessions, raw protocol DTOs, or concrete infrastructure adapters.
- Keep providers, playlist/manifests, stream transports, and player backends conceptually separate. See [ARCHITECTURE.md](ARCHITECTURE.md).

## Player and UI policy

- **libVLC through `python-vlc` is the sole supported player and recording backend.** Do not introduce an alternate player backend without an explicit product decision.
- **PySide6/Qt is the sole supported desktop UI toolkit.** Use the existing qasync integration for asynchronous UI behavior.

## Provider and protocol work

Each provider capability must be independently executable and tested before being documented as implemented. A new provider adapter should:

1. Own provider-specific credentials, device identity, session state, protocol DTOs, and HTTP behavior inside infrastructure.
2. Translate provider records into canonical domain entities/value objects before crossing into application code.
3. Advertise only capabilities it actually implements.
4. Add authorized, sanitized fixtures or fake-backed contract tests as appropriate.
5. Avoid using administrative APIs, portal scanning, unknown device identities, or subscription bypass behavior.

Ministra has a separate decision gate. Do not begin a Ministra client without the authorized fixture and approved device identity described in [MINISTRA_COMPATIBILITY_ASSESSMENT.md](docs/historical/MINISTRA_COMPATIBILITY_ASSESSMENT.md).

## Security and test data

Never commit or log:

- provider usernames or passwords;
- MAG MAC addresses or device identifiers;
- session tokens or cookies;
- tokenized/credential-bearing source URLs;
- resolved playback URLs that may include authorization material;
- real portal payloads or local recording paths.

Use fake credentials, fake portal hosts, fake device identities, and fake playback URLs in tests. Preserve the separation between keyring-held secrets and SQLite-held non-secret metadata. See [SECURITY.md](SECURITY.md).

## Documentation changes

Documentation must be technically accurate, internally consistent, and explicit about limitations. Use these document roles:

| Document | Responsibility |
|---|---|
| `PROJECT_STATUS.md` | Authoritative current state and support matrices. |
| `README.md` | Product and contributor overview. |
| `ROADMAP.md` | Milestones and future direction. |
| `PRODUCT_GAP_ANALYSIS.md` | Prioritized gaps. |
| `ARCHITECTURE.md` | Current boundaries and terminology. |
| Historical reports/assessments | Date/commit-scoped evidence, not current status. |

Update documentation whenever a public capability, limitation, lifecycle, or security boundary changes. Do not copy historical phase claims forward without verifying the implementation.

## Commit examples

```text
feat: add desktop composition root
fix: prevent tokenized M3U source metadata leak
test: cover registered M3U stream resolution
docs: rebaseline provider capability matrix
refactor: isolate provider lifecycle composition
```

## Reporting defects

Use the repository issue templates for ordinary bugs and feature requests. Do not include secrets, real provider data, account details, device identities, or resolved playback URLs in public reports. Follow [SECURITY.md](SECURITY.md) for vulnerability reporting.
