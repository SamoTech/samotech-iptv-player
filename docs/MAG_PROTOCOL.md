# MAG/Stalker Protocol

## Scope

The MAG provider is implemented behind the application provider boundary. The Qt layer calls application use cases; the MAG adapter owns domain translation, credential-store integration, session state, and controlled re-authentication; the legacy provider owns protocol requests, response parsing, catalogue access, and stream-link resolution.

## Protocol profiles

The repository contains four explicit, evidence-based handshake profiles. Middleware-family compatibility is documented separately in `docs/MAG_MIDDLEWARE_COMPATIBILITY.md`; these profiles are request contracts, not claims about a particular Ministra/Stalker release.

| Profile | Status | Behavior |
|---|---|---|
| `legacy` | **IMPLEMENTED and TESTED** | Bare `/server/load.php` handshake relative to the configured portal base, using the existing MAG User-Agent and device identity headers. This remains the default. |
| `stalker_query` | **IMPLEMENTED and SIMULATED** | Observed Stalker client variant using `type=stb`, `action=handshake`, empty `token`, `JsHttpRequest=1-xml`, X-User-Agent, and Referer headers. It remains available as an explicit profile. |
| `stalker_gui_compatibility` | **IMPLEMENTED and SIMULATED** | Models the observed GUI `portal.php` request exactly: origin-relative `portal.php`, MAG200 User-Agent, `type=stb`, `action=handshake`, `JsHttpRequest=1-xml`, and private raw `mac`, `stb_lang`, London-timezone cookies. Its live ordered-list flow starts at `p=0`. It intentionally omits the helper-only empty `token` parameter, X-User-Agent, Referer, and browser-style headers. |
| `stalker_helper_compatibility` | **IMPLEMENTED and SIMULATED** | Models the observed helper `stalker_portal/server/load.php` request exactly: origin-relative helper path, empty `token`, MAG200 User-Agent, MAG250 X-User-Agent, `/stalker_portal/c/index.html` Referer, observed safe browser-style headers, and private percent-encoded `mac`, `stb_lang`, Paris-timezone cookies. Its live ordered-list flow starts at `p=1`. It deliberately excludes the helper's unverified random-token/prehash retry and never fabricates device IDs or tokens. |
| `auto` | **IMPLEMENTED and TESTED against local fixtures** | Runs a closed, deterministic discovery set: configured-base `server/load.php`, generic origin `stalker_portal/server/load.php`, exact helper origin `stalker_portal/server/load.php`, origin `stb/server/load.php`, generic origin `portal.php`, and exact GUI origin `portal.php`. The generic candidates may add one `prehash=false` retry only after an HTTP-200 JSON response without a token. The exact GUI/helper candidates never send the unverified random-token/prehash variant. The first structurally valid token-bearing response is selected and reused for the normal session. |

Both compatibility profiles can be selected explicitly by their documented profile names or selected by `auto` only after a structurally valid token-bearing discovery response. Discovery retains only candidate name, status, content type, response size, elapsed time, JSON/token flags, and classification. It neither stores a token nor treats HTTP 200 as authentication. The existence or selection of a profile does not imply universal portal compatibility. Official Infomir documentation confirms that portal routing, STB model restrictions, and authorization modes are configurable; it does not identify the supplied portal's middleware family. See `docs/MAG_MIDDLEWARE_COMPATIBILITY.md` for the source-derived local lab and version matrix.

## Authentication contract

A successful handshake must return a JSON object containing either `js.token` or a top-level `token`. `js.token_TTL` is accepted when present; otherwise the legacy default TTL is used. Empty bodies, malformed JSON, HTTP 4xx responses, missing tokens, and explicit session-error envelopes fail safely. Discovery classifies network failure, 401, 403, 404, other HTTP status, empty response, malformed JSON, JSON without token, valid Stalker handshake, and unknown protocol before normal authentication can proceed. The adapter never invents a token and never proceeds through authenticated operations without a valid session.

## Session lifecycle

A valid session is reused. When a catalogue response explicitly reports a session error, the adapter marks the session expired, performs at most one controlled re-authentication, and retries the operation once. Authentication failures remain application-facing failures, not successful empty catalogues.

The legacy MAG provider owns its `aiohttp` session and connector. It keeps those resources open only for a successfully authenticated active provider instance. If bounded discovery or authentication fails after opening the connection, it closes the session and connector before propagating the original failure. Explicit provider shutdown also closes those resources. Cleanup is best effort and must not replace an authentication failure or weaken authentication guards.

## Current real-portal status

The supplied real portal remains **UNRESOLVED** for compatibility. The most recent bounded authorized validation completed the six-candidate closed set: `configured_base_server`, `origin_stalker_portal`, `origin_stalker_portal_helper`, and `origin_stb_server` each returned HTTP 404; generic `origin_portal_php` returned HTTP 200 with an empty `text/javascript` response; and exact `origin_portal_php_stalker_client` returned HTTP 404 with an empty `text/javascript` response. A subsequent one-candidate revalidation of the GUI profile after correcting its observed raw MAC-cookie representation also returned HTTP 404 with an empty `text/javascript` response. No candidate returned JSON or a session token, so authentication, genres, ordered-list channels, stream resolution, and playback were not reached. The prior real Windows run also confirmed that the owned HTTP session and connector close on authentication failure with no unclosed-resource warning. This documents cleanup only; it does not establish production MAG compatibility.

## Security

Diagnostics include only safe endpoint paths, methods, statuses, content types, response sizes, elapsed timing, and classifications. MAC addresses, passwords, tokens, cookies, Authorization headers, credential-bearing URLs, payloads, and resolved stream URLs are not logged.

## References

[1]: https://wiki.infomir.eu/eng/ministra-tv-platform/changelog/stalker-middleware-4-8 "Infomir Stalker Middleware changelog"
[2]: https://github.com/Cyogenus/IPTV-MAC-STALKER-PLAYER-BY-MY-1/blob/main/stalker.py "Secondary open-source Stalker client reference"
[3]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-installation-guide/ministra-tv-platform-installation "Infomir Ministra installation and STB authorization documentation"
[4]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-installation-guide/configuration-file "Infomir Ministra configuration file"
[5]: https://github.com/lloesche/stalker_portal "Open-source Middleware Stalker tree"
[6]: https://github.com/iptvhakr/stalker_portal "Open-source Stalker Middleware 5.1.1 tree"
