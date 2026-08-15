# MAG/Stalker Protocol

## Scope

The MAG provider is implemented behind the application provider boundary. The Qt layer calls application use cases; the MAG adapter owns domain translation, credential-store integration, session state, and controlled re-authentication; the legacy provider owns protocol requests, response parsing, catalogue access, and stream-link resolution.

## Protocol profiles

The repository contains five explicit, evidence-based handshake profiles.
 Middleware-family compatibility is documented separately in `docs/MAG_MIDDLEWARE_COMPATIBILITY.md`; these profiles are request contracts, not claims about a particular Ministra/Stalker release.

| Profile | Status | Behavior |
|---|---|---|
| `legacy` | **IMPLEMENTED and TESTED** | Bare `/server/load.php` handshake relative to the configured portal base, using the existing MAG User-Agent and device identity headers. This remains the default. |
| `stalker_query` | **IMPLEMENTED and SIMULATED** | Observed Stalker client variant using `type=stb`, `action=handshake`, empty `token`, `JsHttpRequest=1-xml`, X-User-Agent, and Referer headers. It remains available as an explicit profile. |
| `stalker_gui_compatibility` | **IMPLEMENTED and SIMULATED** | Models the observed GUI `portal.php` request exactly: origin-relative `portal.php`, MAG200 User-Agent, `type=stb`, `action=handshake`, `JsHttpRequest=1-xml`, and private raw `mac`, `stb_lang`, London-timezone cookies. Its live ordered-list flow starts at `p=0`. It intentionally omits the helper-only empty `token` parameter, X-User-Agent, Referer, and browser-style headers. |
| `stalker_helper_compatibility` | **IMPLEMENTED and SIMULATED** | Models the observed helper `stalker_portal/server/load.php` request: origin-relative helper path, empty `token`, MAG200 User-Agent, optional model-dependent MAG250-style X-User-Agent only when an explicit model is configured, `/stalker_portal/c/index.html` Referer, observed safe browser-style headers, and private percent-encoded `mac`, `stb_lang`, Paris-timezone cookies. Its live ordered-list flow starts at `p=1`. It deliberately excludes the helper's unverified random-token/prehash retry and never fabricates device IDs, serials, or models. |
| `stalker_portal_php_legacy` | **IMPLEMENTED and FIXTURE-TESTED; REAL PORTAL REJECTED THE HANDSHAKE** | Models the newly supplied concrete client: origin-relative `portal.php` handshake, ordered `action=handshake`, `type=stb`, empty `token`, `JsHttpRequest=1-xml`, `Authorization: MAC`, raw `mac` cookie, browser User-Agent, `/c/` Referer, JSON/text Accept, and `X-Requested-With`. After a token it validates `/portal.php` account info, reads genres from `/server/load.php`, reads channels from `/portal.php`, and retains usable `cmds[].url` values without inventing `create_link` or fallback URLs. |
| `auto` | **IMPLEMENTED and TESTED against local fixtures** | Runs a closed, deterministic discovery set: configured-base `server/load.php`, generic origin `stalker_portal/server/load.php`, exact helper origin `stalker_portal/server/load.php`, origin `stb/server/load.php`, generic origin `portal.php`, exact GUI origin `portal.php`, and the concrete origin `portal.php` MAC-client profile. Only generic candidates may add one `prehash=false` retry after an HTTP-200 JSON response without a token; the exact GUI, helper, and concrete MAC-client profiles never send that retry. The first structurally valid token-bearing response is selected and reused for the normal session. |

Compatibility profiles can be selected explicitly by their documented profile names or selected by `auto` only after a structurally valid token-bearing discovery response.
 Discovery retains only candidate name, status, content type, response size, elapsed time, JSON/token flags, and classification. It neither stores a token nor treats HTTP 200 as authentication. The existence or selection of a profile does not imply universal portal compatibility. Official Infomir documentation confirms that portal routing, STB model restrictions, and authorization modes are configurable; it does not identify the supplied portal's middleware family. See `docs/MAG_MIDDLEWARE_COMPATIBILITY.md` for the source-derived local lab and version matrix.

## Authentication contract

The authentication state machine is explicit and non-inferential: `DISCOVERY → HANDSHAKE → TOKEN_RECEIVED → ACCOUNT_INFO? → PROFILE_REQUIRED? → GET_PROFILE → DO_AUTH? → SESSION_VALIDATED → CATALOGUE`.
 The selected configuration may choose `mac_only`, `mac_plus_login`, or `authorization_key`; no mode is inferred from HTTP status or profile shape. The optional `profile_second_step`/`profile_required` flag enables `get_profile`, and the login mode uses form-encoded POST `do_auth` only when explicitly configured. Missing authorization keys fail as `AUTH_KEY_REQUIRED`; an authorization-key transport is not invented.

A fixed differential probe API now supports only source-backed request cases with safe IDs and metadata. It does not scan paths or retain raw bodies. The current local and authorized matrix covers GUI GET/POST, helper GET `prehash=false`, helper GET `prehash=0`, GUI POST `prehash=false`, and helper POST `prehash=0`.

A successful handshake must return a JSON object containing `js.token`, source-observed `js.Token`, or a top-level `token`. `js.token_TTL` is accepted when present; otherwise the legacy default TTL is used. Empty bodies, malformed JSON, HTTP 4xx responses, missing tokens, and explicit session-error envelopes fail safely.
 Discovery classifies network failure, 401, 403, 404, other HTTP status, empty response, malformed JSON, JSON without token, valid Stalker handshake, profile/policy markers, method-not-allowed, redirected responses, and unknown protocol before normal authentication can proceed. A 404 is never labeled STB-not-authorized without machine-readable policy evidence. The adapter never invents a token and never proceeds through authenticated operations without a valid session.

## Session lifecycle

A valid session is reused. When a catalogue response explicitly reports a session error, the adapter marks the session expired, performs at most one controlled re-authentication, and retries the operation once. Authentication failures remain application-facing failures, not successful empty catalogues. The application currently has only a MAC-based credential path; official login/password and authorization-key modes are documented as provider-side options, but are not silently selected or implemented without portal evidence.

The legacy MAG provider owns its `aiohttp` session and connector. It keeps those resources open only for a successfully authenticated active provider instance. If bounded discovery or authentication fails after opening the connection, it closes the session and connector before propagating the original failure. Explicit provider shutdown also closes those resources. Cleanup is best effort and must not replace an authentication failure or weaken authentication guards.

## Current real-portal status

The supplied real portal remains **UNRESOLVED** for compatibility. After the dedicated `stalker_portal_php_legacy` implementation, the new authorized `PORTAL-PHP-01` handshake was tested directly and returned HTTP 404 `text/javascript`, zero bytes, `Server: nginx`, zero redirects, no `Allow` header, no `WWW-Authenticate` header, no JSON, and no token. Account info, genres, channels, stream resolution, and playback were not reached. GUI GET/POST and GUI POST-prehash returned HTTP 404 `text/javascript` zero-byte responses; helper GET prehash=false/0 and helper POST prehash=0 returned HTTP 404 `text/html` 146-byte responses. No test returned a profile, an error field, or an authorization policy marker. One earlier explicit MAG254 helper request also returned HTTP 404 `text/html` 146 bytes. The most recent bounded authorized validation completed the six-candidate closed set:
 `configured_base_server`, `origin_stalker_portal`, `origin_stalker_portal_helper`, and `origin_stb_server` each returned HTTP 404; generic `origin_portal_php` returned HTTP 200 with an empty `text/javascript` response; and exact `origin_portal_php_stalker_client` returned HTTP 404 with an empty `text/javascript` response. A subsequent one-candidate revalidation of the GUI profile after correcting its observed raw MAC-cookie representation also returned HTTP 404 with an empty `text/javascript` response. A new single-candidate helper revalidation after removing the unverified implicit model identity returned HTTP 404 with `text/html`, 146 bytes, no JSON, and no token; no model header was sent. Safe metadata showed `Server: nginx` with no redirect on the real server paths, while the local source-derived classic route returns JSON 401 without credentials. This proves a deployment/routing/response-boundary difference but does not identify the middleware family or authorization policy. No candidate returned JSON or a session token, so authentication, genres, ordered-list channels, stream resolution, and playback were not reached. The prior real Windows run also confirmed that the owned HTTP session and connector close on authentication failure with no unclosed-resource warning. The new profile has deterministic local full-stack coverage and a safe sandbox real-portal rejection result. A fresh Windows run included the new `origin_portal_php_mac_client` candidate, but every candidate failed earlier with `NETWORK_FAILURE` and Windows `WinError 121`; no HTTP response was obtained. A Windows cross-client transport matrix is now required before interpreting protocol compatibility. This does not establish production MAG compatibility.

## Security

Diagnostics include only safe endpoint paths, methods, statuses, content types, response sizes, elapsed timing, redirect counts, selected response headers (`Server`, `Allow`, and `WWW-Authenticate` presence), and classifications. MAC addresses, passwords, tokens, cookies, Authorization headers, credential-bearing URLs, payloads, and resolved stream URLs are not logged.

## Catalogue response-boundary diagnostics

Catalogue requests now emit three safe, aggregate-only response-boundary records. `CATALOGUE_HTTP_RESPONSE` is written after response headers arrive and records the attempt, active total timeout, HTTP status, content type, declared content length, transfer encoding, and elapsed time. `CATALOGUE_BODY_COMPLETE` is written only after the complete body has been collected and records the received byte count, chunk count, first and last body-byte timing, and body elapsed time.

If body collection does not complete, `CATALOGUE_BODY_INCOMPLETE` records only the same safe response metadata when available, aggregate received bytes and chunk count, first-body-byte timing, last-chunk age, body elapsed time, and one classification: `TIMEOUT`, `PAYLOAD_ERROR`, or `NETWORK_ERROR`. A pre-response failure uses explicit `<none>` placeholders for unavailable response metadata; a partial body is never parsed or accepted as a catalogue.

This instrumentation retains the existing configured timeout object, retry count, retry delays, request construction, endpoints, authentication state machine, response acceptance rules, and provider/session lifecycle. It replaces `response.read()` with ordered aggregate chunk collection so incomplete-body progress is observable while successful JSON decoding receives the same complete byte sequence. The diagnostics are evidence collection only: they do not prove a provider is slow, a response is truncated, or Windows lifecycle behavior is correct without repeated authorized runtime measurements.

## References

[1]: https://wiki.infomir.eu/eng/ministra-tv-platform/changelog/stalker-middleware-4-8 "Infomir Stalker Middleware changelog"
[2]: https://github.com/Cyogenus/IPTV-MAC-STALKER-PLAYER-BY-MY-1/blob/main/stalker.py "Secondary open-source Stalker client reference"
[3]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-installation-guide/ministra-tv-platform-installation "Infomir Ministra installation and STB authorization documentation"
[4]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-installation-guide/configuration-file "Infomir Ministra configuration file"
[5]: https://github.com/lloesche/stalker_portal "Open-source Middleware Stalker tree"
[6]: https://github.com/iptvhakr/stalker_portal "Open-source Stalker Middleware 5.1.1 tree"
