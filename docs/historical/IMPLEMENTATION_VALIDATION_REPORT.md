# IPTV Playback and MAG Lifecycle Reliability

## Executive summary

The requested reliability work is complete. VLC playback now serializes channel operations, applies configurable live-stream buffering, supports automatic hardware-to-software decoder fallback, retries startup within a bounded limit, and emits redacted lifecycle diagnostics. MAG/Stalker operations now establish and reuse authenticated sessions automatically, rehydrate credentials before authenticated operations, and perform one controlled re-authentication when a session expires. Category browsing for providers that do not support it is represented as a typed non-fatal result rather than an application failure.

The existing Xtream loading path was not refactored. No credential, MAC address, token, or resolved playback URL is written to the new diagnostics.

## Implementation changes

| Area | Implementation | Files |
|---|---|---|
| VLC concurrency | Added an `asyncio.Lock` around play, stop, pause, and resume operations so rapid channel changes cannot race libVLC state transitions. Blocking libVLC calls continue to run via `asyncio.to_thread`, keeping the Qt/qasync event loop responsive. | `src/samotech_iptv/infrastructure/player/vlc_player_adapter.py` |
| VLC resilience | Added bounded startup retries. In `auto` mode, a failed first attempt retries with `:avcodec-hw=none`; software mode always disables hardware decoding, while hardware mode preserves the normal libVLC decoder selection. | `src/samotech_iptv/infrastructure/player/vlc_player_adapter.py` |
| VLC buffering | Added configurable `network_caching_ms`, with media-level `:network-caching` configuration. The production factory maps the existing `PlayerConfig.buffer_size_mb` setting to a conservative millisecond cache value and passes the hardware-decode preference into the adapter. | `src/samotech_iptv/infrastructure/player/composition.py`, `src/samotech_iptv/desktop_composition.py` |
| VLC diagnostics | Added defensive subscriptions for available libVLC opening, buffering, playing, error, end, and stopped events. Diagnostics use `[IPTV]` labels and redact stream URLs to host-only or safe labels. | `src/samotech_iptv/infrastructure/player/vlc_player_adapter.py` |
| MAG session lifecycle | Added explicit session states: `no_session`, `authenticating`, `authenticated`, `authentication_failed`, and `session_expired`. Authentication is restored from the credential store before authenticated operations, and the active session is reused until invalidated. | `src/samotech_iptv/infrastructure/providers/mag_adapter.py` |
| MAG re-authentication | Added a single retry path for translated authentication/session-expiry errors. Failed authentication clears volatile state and is surfaced through the existing provider error boundary. | `src/samotech_iptv/infrastructure/providers/mag_adapter.py` |
| MAG protocol alignment | Verified against the installed legacy provider: `connect()` opens the HTTP session and then calls `session.authenticate()`, which performs `GET /server/load.php` with bearer/MAC/device headers and stores the response token and TTL. The adapter continues to delegate protocol details to this legacy implementation rather than duplicating the handshake. | `providers/mag/provider.py`, `providers/mag/connection.py`, `providers/mag/session.py`, `src/samotech_iptv/infrastructure/providers/mag_adapter.py` |
| Category capability handling | Added typed `unsupported` category results and retained generic failure handling for real provider errors. Provider-specific details do not cross the application/presentation boundary. | `src/samotech_iptv/application/dtos/categories.py`, `src/samotech_iptv/application/use_cases/load_categories.py` |

## Legacy MAG handshake verification

The inspected legacy implementation confirms the intended lifecycle sequence:

1. `MAGProvider.connect()` calls `MAGConnection.open()`.
2. `MAGConnection.open()` creates an `aiohttp.ClientSession` with the configured user agent, timeout, and TLS policy.
3. `MAGProvider.connect()` then calls `MAGSession.authenticate()`.
4. Authentication requests `/server/load.php` with `Authorization: Bearer ...` when a token exists, `X-User-Mac`, and optional serial/device headers.
5. The response token is read from `js.token` or the top-level `token`, and the optional `js.token_TTL` controls expiry.
6. Channel and stream operations remain delegated to the legacy catalogue and stream services.

The adapter therefore establishes sessions through the actual provider implementation and does not invent an alternate handshake.

## Validation

| Check | Result |
|---|---|
| Black formatting | Passed; 270 files unchanged by the final check. |
| Ruff lint | Passed. |
| Full pytest suite | Passed; 584 tests collected and completed successfully. Four pre-existing aiohttp deprecation warnings remain. |
| Focused VLC/MAG/category regression tests | Passed; 33 focused tests. |
| `git diff --check` | Passed with no whitespace errors. |
| Mypy | The modified implementation files have no remaining mypy diagnostics. Repository-wide mypy still reports 38 pre-existing errors across 18 other files, primarily unused Qt import suppressions and missing/untyped third-party module handling. |

## Changed files

The final working tree contains intended changes in the two reliability implementations, production composition, category DTO/use case, and their regression tests:

`src/samotech_iptv/application/dtos/categories.py`, `src/samotech_iptv/application/use_cases/load_categories.py`, `src/samotech_iptv/desktop_composition.py`, `src/samotech_iptv/infrastructure/player/composition.py`, `src/samotech_iptv/infrastructure/player/vlc_player_adapter.py`, `src/samotech_iptv/infrastructure/providers/mag_adapter.py`, `tests/test_application_load_categories.py`, `tests/test_desktop_composition.py`, `tests/test_infra_b2_mag_adapter.py`, `tests/test_infra_player_composition.py`, and `tests/test_infra_vlc_player_adapter.py`.

## Remaining verification note

The automated suite verifies adapter behavior and production composition, but it cannot validate every installed operating-system libVLC decoder, portal firmware variation, or physical Qt video surface. A final manual smoke test should exercise rapid channel switching, a deliberately unavailable stream, a stream that requires software decoding, MAG registration followed by channel loading, and a session-expiry/re-authentication cycle while observing only redacted `[IPTV]` diagnostics.
