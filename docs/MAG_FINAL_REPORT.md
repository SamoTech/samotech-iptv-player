# MAG/Stalker Compatibility Final Report

> **REAL PORTAL STILL BLOCKED**

**Repository:** `SamoTech/samotech-iptv-player`  
**Branch:** `main`  
**Implementation commit:** `b2507590062db485acfcb3162e37a5a28e65b299`
**Assessment:** The dedicated profile is implemented and regression-clean. The authorized portal still did not return a machine-readable handshake response, so real end-to-end MAG functionality is not established.

## A. Files changed

The implementation commit `b250759` changed the MAG connection, constants, discovery, protocol profiles, provider, session, catalogue, stream resolver, and MAG regression tests. It adds the concrete `stalker_portal_php_legacy` profile and a full-stack deterministic hybrid fixture. The documentation update records the new authorized result.

| Area | Files |
|---|---|
| Protocol and transport | `providers/mag/connection.py`, `providers/mag/constants.py`, `providers/mag/protocol_profile.py` |
| Credentials and provider wiring | `providers/mag/credentials.py`, `providers/mag/provider.py`, `src/samotech_iptv/infrastructure/providers/mag_credential.py` |
| Discovery, session, and catalogue | `providers/mag/discovery.py`, `providers/mag/session.py`, `providers/mag/catalogue.py`, `providers/mag/stream.py` |
| Regression tests | `tests/providers/mag/test_discovery.py`, `tests/providers/mag/test_connection.py`, `tests/providers/mag/test_protocol_profile.py`, `tests/providers/mag/test_portal_php_legacy_lab.py` |
| Documentation | `docs/MAG_PROTOCOL.md`, `docs/MAG_REAL_PORTAL_INVESTIGATION.md`, `docs/MAG_FINAL_REPORT.md` |

No M3U, Xtream, or VLC implementation was modified.

## B. Authentication changes

The authentication state machine now models the explicit sequence `DISCOVERY → HANDSHAKE → TOKEN_RECEIVED → ACCOUNT_INFO? → PROFILE_REQUIRED? → GET_PROFILE → DO_AUTH? → SESSION_VALIDATED → CATALOGUE`.
 It supports explicitly selected `mac_only`, `mac_plus_login`, and `authorization_key` modes. Optional profile-stage fields include `hd` and `auth_second_step`; form-encoded POST transport is used only when the selected profile and stage require it.

Stage failures invalidate the in-memory token and expiry state transactionally. Authentication success is not declared until the complete configured post-handshake sequence succeeds. Missing authorization keys remain explicit `AUTH_KEY_REQUIRED` failures, and no authorization-key transport algorithm is fabricated.

## C. Protocol/profile changes

The protocol request model now carries method and form data separately from query parameters. Profile-selected GET versus POST transport is honored by the connection and discovery layers. The configured application path is preserved when joining endpoint paths, so a configured portal base with an application prefix remains distinct from an origin-base profile. The new `stalker_portal_php_legacy` profile uses origin `/portal.php` for handshake, account info, and channels, `/server/load.php` for genres, MAC Authorization before the token, Bearer Authorization afterward, the raw MAC cookie, browser headers, and `/c/` Referer.

The parser accepts the source-observed `js.Token` spelling in addition to `js.token` and a top-level `token`. The hybrid catalogue reads direct `cmds[].url` values and validates their schemes without invoking `create_link` or inventing a fallback URL. The helper profile supports optional explicit `profile_hd`/model configuration without inventing a model or device identity. Discovery remains bounded and evidence-backed; it does not scan arbitrary paths, retry random prehash values, fabricate tokens, or generate device identities. Safe response diagnostics now include redirect count, `Server`, `Allow`, and the presence of `WWW-Authenticate` without retaining raw bodies, credentials, or portal hosts.

## D. Real portal tests performed

The authorized validation included the fixed T01–T06 differential matrix and a direct `PORTAL-PHP-01` request using the newly supplied concrete client fingerprint. The direct profile test used origin `/portal.php`, GET, the four handshake query fields, MAC Authorization, raw MAC cookie, browser User-Agent, `/c/` Referer, JSON/text Accept, and `X-Requested-With`. The earlier evidence-backed MODEL-01 explicit-model helper request remains in the investigation record.

| Test | Profile | Method | Status | Content-Type | Bytes | Redirects | Server | Allow | WWW-Authenticate | JSON | Token | Classification |
|---|---|---:|---:|---|---:|---:|---|---|---|---|---|---|
| T01 | `stalker_gui_compatibility` | GET | 404 | `text/javascript` | 0 | 0 | `nginx` | No | No | No | No | `HTTP_404` |
| T02 | `stalker_gui_compatibility` | POST | 404 | `text/javascript` | 0 | 0 | `nginx` | No | No | No | No | `HTTP_404` |
| T03 | `stalker_helper_compatibility` | GET | 404 | `text/html` | 146 | 0 | `nginx` | No | No | No | No | `HTTP_404` |
| T04 | `stalker_helper_compatibility` | GET | 404 | `text/html` | 146 | 0 | `nginx` | No | No | No | No | `HTTP_404` |
| T05 | `stalker_gui_compatibility` | POST | 404 | `text/javascript` | 0 | 0 | `nginx` | No | No | No | No | `HTTP_404` |
| T06 | `stalker_helper_compatibility` | POST | 404 | `text/html` | 146 | 0 | `nginx` | No | No | No | No | `HTTP_404` |
| PORTAL-PHP-01 | `stalker_portal_php_legacy` | GET | 404 | `text/javascript` | 0 | 0 | `nginx` | No | No | No | No | `HTTP_404` |

All current requests reached the first HTTP response boundary and stopped there. No response included JSON, a token, a profile, an error field, or a machine-readable authorization marker. A bare 404 is not classified as `STB_NOT_AUTHORIZED`.

## E. First successful boundary

There was **no successful real-portal boundary**. The new concrete portal.php handshake also ended with HTTP 404 before `TOKEN_RECEIVED`. Consequently, account info, `SESSION_VALIDATED`, genres, channels, direct command extraction, stream resolution, and playback were not reached.

## F. Real category count

**Unavailable.** No real token or authenticated session was established, so live genres were not requested.

## G. Real channel count

**Unavailable.** No real genres or ordered-list channel records were received.

## H. Real rejected channel count

**Unavailable.** No real channel records were received, so no real acceptance or rejection count exists.

## I. `create_link` result

**Not reached.** No real channel command was received. The new profile is designed to use a real `cmds[].url` directly when returned; it does not call `create_link` for that contract.

## J. Real stream result

**Not reached.** No real stream URL was resolved. No stream URL was logged or retained.

## K. VLC result

**Not run for MAG.** The authorized sandbox validation stopped at handshake, before stream resolution. The fresh Windows run included the new discovery candidate but failed earlier at TCP connection with repeated `WinError 121`; no HTTP response or stream was obtained. VLC/libVLC code was not changed, and no MAG-specific playback claim is made.

## L. Regression/CI status

The complete local quality gate passed after implementation. The implementation commit was pushed directly to `main` and synchronized with `origin/main`; the documentation update will be pushed with the final report revision.

| Check | Result |
|---|---|
| `black --check src tests providers` | PASS |
| `ruff check src tests providers` | PASS |
| `MYPYPATH=/tmp/mypy_stubs mypy src` | PASS |
| `PYTHONPATH=src:. pytest -q` | PASS |
| `git diff --check` | PASS |
| `HEAD == origin/main` | PASS |
| Working tree | CLEAN |

The full suite completed successfully; only existing `aiohttp` deprecation warnings were reported.

## M. Remaining blocker

The latest Windows run establishes a transport-layer blocker before HTTP: DNS resolved, but TCP connection completion repeatedly failed with `WinError 121`, so no handshake request was observed from that machine. A subsequent Windows-native matrix independently confirmed that PowerShell and WinHTTP timed out without HTTP status, while the raw TCP probe failed during TCP connect. That posted matrix used a different MAC identity from the original authorized test credential; because it failed before HTTP, it is transport evidence only and cannot establish authorization behavior for the original device. The Windows companion did not execute curl, so one independent Windows-client check remains.
 Separate sandbox requests/aiohttp/curl runs reached HTTP and reproduced the earlier Nginx-style 404 boundary. This network-path difference must be resolved before interpreting the portal’s protocol or authorization behavior. The 404 evidence still does not distinguish disabled or rewritten routes, middleware-family/version mismatch, gateway filtering, device registration state, or provider-side authorization policy. It is not sufficient evidence to claim that the device is unauthorized, and it does not prove incompatibility with every Stalker/Ministra deployment.

The raw TCP, PowerShell, and WinHTTP portions of the Windows matrix now all fail before HTTP. Execute the remaining curl.exe check separately without printing its command line or body. If curl also times out, fix reachability/firewall/proxy/ISP conditions before changing MAG code. If curl receives HTTP 404, continue routing/protocol analysis from that Windows path. Until a valid real token is returned, the correct status remains **REAL PORTAL STILL BLOCKED**. No further endpoint permutations, random-token/prehash retries, fabricated identities, VOD/Series/DASH/RTMP work, or VLC changes are justified.

## References

[1]: https://github.com/kidpoleon/stalkerhek/blob/main/stalker/authentication.go "Current stalkerhek authentication source"

[2]: https://github.com/erkexzcx/stalkerhek/blob/master/stalker/authentication.go "Archived stalkerhek authentication source"

[3]: https://github.com/kidpoleon/stalkerhek/blob/main/stalker/portal_meta.go "Current stalkerhek get_profile metadata source"

[4]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-installation-guide/configuration-file "Infomir Ministra configuration reference"
