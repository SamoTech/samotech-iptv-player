# MAG/Stalker Protocol

## Scope

The MAG provider is implemented behind the application provider boundary. The Qt layer calls application use cases; the MAG adapter owns domain translation, credential-store integration, session state, and controlled re-authentication; the legacy provider owns protocol requests, response parsing, catalogue access, and stream-link resolution.

## Protocol profiles

The repository contains three explicit, evidence-based handshake profiles:

| Profile | Status | Behavior |
|---|---|---|
| `legacy` | **IMPLEMENTED and TESTED** | Bare `/server/load.php` handshake relative to the configured portal base, using the existing MAG User-Agent and device identity headers. This remains the default. |
| `stalker_query` | **IMPLEMENTED and SIMULATED** | Observed Stalker client variant using `type=stb`, `action=handshake`, empty `token`, `JsHttpRequest=1-xml`, X-User-Agent, and Referer headers. It remains available as an explicit profile. |
| `stalker_client_compatibility` | **IMPLEMENTED and SIMULATED** | Uses the secondary reference's materially different `portal.php` client fingerprint: the exact MAG200 User-Agent, MAG250 X-User-Agent, `/stalker_portal/c/index.html` Referer, and private `mac`, `stb_lang`, and timezone cookies. It also uses `get_genres` plus `get_ordered_list(genre, p)` and a loaded channel command for `create_link`. It never fabricates device IDs or tokens. |
| `auto` | **IMPLEMENTED and TESTED against local fixtures** | Runs a closed, deterministic discovery set: configured-base `server/load.php`, origin `stalker_portal/server/load.php`, origin `stb/server/load.php`, generic origin `portal.php`, and the materially different client-fingerprint request at that same approved `portal.php` path. The generic candidates may add one `prehash=false` retry only after an HTTP-200 JSON response without a token. The compatibility candidate never sends the unverified random-token/prehash variant. The first structurally valid token-bearing response is selected and reused for the normal session. |

Discovery retains only candidate name, status, content type, response size, elapsed time, JSON/token flags, and classification. It neither stores a token nor treats HTTP 200 as authentication. The existence or selection of a profile does not imply universal portal compatibility. Firmware, middleware, portal base path, and provider-specific behavior must be established by authorized evidence.

## Authentication contract

A successful handshake must return a JSON object containing either `js.token` or a top-level `token`. `js.token_TTL` is accepted when present; otherwise the legacy default TTL is used. Empty bodies, malformed JSON, HTTP 4xx responses, missing tokens, and explicit session-error envelopes fail safely. Discovery classifies network failure, 401, 403, 404, other HTTP status, empty response, malformed JSON, JSON without token, valid Stalker handshake, and unknown protocol before normal authentication can proceed. The adapter never invents a token and never proceeds through authenticated operations without a valid session.

## Session lifecycle

A valid session is reused. When a catalogue response explicitly reports a session error, the adapter marks the session expired, performs at most one controlled re-authentication, and retries the operation once. Authentication failures remain application-facing failures, not successful empty catalogues.

The legacy MAG provider owns its `aiohttp` session and connector. It keeps those resources open only for a successfully authenticated active provider instance. If bounded discovery or authentication fails after opening the connection, it closes the session and connector before propagating the original failure. Explicit provider shutdown also closes those resources. Cleanup is best effort and must not replace an authentication failure or weaken authentication guards.

## Current real-portal status

The supplied real portal remains **UNRESOLVED** for compatibility. Previous approved generic requests produced three HTTP-404 classifications and one HTTP-200 empty-response classification; no candidate produced a JSON session token. The new compatibility request uses the same already-approved `portal.php` path with a materially different client fingerprint, but has not yet been run against the real Windows portal. A supplied Windows run of the failure-safe revision exercised the earlier sequence twice and logged HTTP-session closure before each authentication failure, with no unclosed-session or unclosed-connector warning in the supplied log. This confirms cleanup of the observed failure path, not portal compatibility or playback.

## Security

Diagnostics include only safe endpoint paths, methods, statuses, content types, response sizes, elapsed timing, and classifications. MAC addresses, passwords, tokens, cookies, Authorization headers, credential-bearing URLs, payloads, and resolved stream URLs are not logged.

## References

[1]: https://wiki.infomir.eu/eng/ministra-tv-platform/changelog/stalker-middleware-4-8 "Infomir Stalker Middleware changelog"
[2]: https://github.com/Cyogenus/IPTV-MAC-STALKER-PLAYER-BY-MY-1/blob/main/stalker.py "Secondary open-source Stalker client reference"
