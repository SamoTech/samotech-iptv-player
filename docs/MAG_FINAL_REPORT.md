# MAG/Stalker Compatibility Final Report

> **REAL PORTAL STILL BLOCKED**

**Repository:** `SamoTech/samotech-iptv-player`  
**Branch:** `main`  
**Final synchronized commit:** `6b330a89b688009ce4569ff2c8b634858b4cf2d6`  
**Assessment:** The implementation is regression-clean and the bounded authorized validation is complete, but the real portal did not return a machine-readable handshake response. Real end-to-end MAG functionality is therefore not established.

## A. Files changed

The implementation commit `d54c7df` changed the MAG connection, credentials, discovery, protocol-profile, provider, session, application credential bridge, and MAG regression tests. The documentation commit `6b330a8` updated `docs/MAG_PROTOCOL.md`, `docs/MAG_REAL_PORTAL_INVESTIGATION.md`, and this final report.

| Area | Files |
|---|---|
| Protocol and transport | `providers/mag/connection.py`, `providers/mag/protocol_profile.py` |
| Credentials and provider wiring | `providers/mag/credentials.py`, `providers/mag/provider.py`, `src/samotech_iptv/infrastructure/providers/mag_credential.py` |
| Discovery and session state | `providers/mag/discovery.py`, `providers/mag/session.py` |
| Regression tests | `tests/providers/mag/test_auth_state_machine.py`, `tests/providers/mag/test_connection.py`, `tests/providers/mag/test_protocol_profile.py` |
| Documentation | `docs/MAG_PROTOCOL.md`, `docs/MAG_REAL_PORTAL_INVESTIGATION.md`, `docs/MAG_FINAL_REPORT.md` |

No M3U, Xtream, or VLC implementation was modified.

## B. Authentication changes

The authentication state machine now models the explicit sequence `DISCOVERY → HANDSHAKE → TOKEN_RECEIVED → PROFILE_REQUIRED? → GET_PROFILE → DO_AUTH? → SESSION_VALIDATED → CATALOGUE`. It supports explicitly selected `mac_only`, `mac_plus_login`, and `authorization_key` modes. Optional profile-stage fields include `hd` and `auth_second_step`; form-encoded POST transport is used only when the selected profile and stage require it.

Stage failures invalidate the in-memory token and expiry state transactionally. Authentication success is not declared until the complete configured post-handshake sequence succeeds. Missing authorization keys remain explicit `AUTH_KEY_REQUIRED` failures, and no authorization-key transport algorithm is fabricated.

## C. Protocol/profile changes

The protocol request model now carries method and form data separately from query parameters. Profile-selected GET versus POST transport is honored by the connection and discovery layers. The configured application path is preserved when joining endpoint paths, so a configured portal base with an application prefix remains distinct from an origin-base profile.

The parser accepts the source-observed `js.Token` spelling in addition to `js.token` and a top-level `token`. The helper profile supports optional explicit `profile_hd`/model configuration without inventing a model or device identity. Discovery remains bounded and evidence-backed; it does not scan arbitrary paths, retry random prehash values, fabricate tokens, or generate device identities. Safe response diagnostics now include redirect count, `Server`, `Allow`, and the presence of `WWW-Authenticate` without retaining raw bodies or credentials.

## D. Real portal tests performed

The authorized validation reran the fixed T01–T06 differential matrix after the URL-preserving change. The six tests were GUI GET, GUI POST, helper GET with `prehash=false`, helper GET with `prehash=0`, GUI POST with `prehash=false`, and helper POST with `prehash=0`. An earlier evidence-backed MODEL-01 explicit-model helper request is also retained in the investigation record.

| Test | Profile | Method | Status | Content-Type | Bytes | Redirects | Server | Allow | WWW-Authenticate | JSON | Token | Classification |
|---|---|---:|---:|---|---:|---:|---|---|---|---|---|---|
| T01 | `stalker_gui_compatibility` | GET | 404 | `text/javascript` | 0 | 0 | `nginx` | No | No | No | No | `HTTP_404` |
| T02 | `stalker_gui_compatibility` | POST | 404 | `text/javascript` | 0 | 0 | `nginx` | No | No | No | No | `HTTP_404` |
| T03 | `stalker_helper_compatibility` | GET | 404 | `text/html` | 146 | 0 | `nginx` | No | No | No | No | `HTTP_404` |
| T04 | `stalker_helper_compatibility` | GET | 404 | `text/html` | 146 | 0 | `nginx` | No | No | No | No | `HTTP_404` |
| T05 | `stalker_gui_compatibility` | POST | 404 | `text/javascript` | 0 | 0 | `nginx` | No | No | No | No | `HTTP_404` |
| T06 | `stalker_helper_compatibility` | POST | 404 | `text/html` | 146 | 0 | `nginx` | No | No | No | No | `HTTP_404` |

All six current requests reached the first HTTP response boundary and stopped there. No response included JSON, a token, a profile, an error field, or a machine-readable authorization marker. A bare 404 is not classified as `STB_NOT_AUTHORIZED`.

## E. First successful boundary

There was **no successful real-portal boundary**. The first attempted boundary was the handshake response, and every current case ended with HTTP 404 before `TOKEN_RECEIVED`. Consequently, `SESSION_VALIDATED` was not reached.

## F. Real category count

**Unavailable.** No real token or authenticated session was established, so live genres were not requested.

## G. Real channel count

**Unavailable.** No real genres or ordered-list channel records were received.

## H. Real rejected channel count

**Unavailable.** No real channel records were received, so no real acceptance or rejection count exists.

## I. `create_link` result

**Not reached.** No real channel command was received, so the live `create_link` operation was not called.

## J. Real stream result

**Not reached.** No real stream URL was resolved. No stream URL was logged or retained.

## K. VLC result

**Not run for MAG.** The real portal stopped at handshake, before stream resolution. VLC/libVLC code was not changed, and no MAG-specific playback claim is made.

## L. Regression/CI status

The complete local quality gate passed after implementation and documentation changes. The repository is synchronized directly on `main` with no uncommitted changes.

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

The remaining blocker is the absence of a machine-readable handshake response from every evidence-backed request form tested. The observed Nginx-style 404 boundary does not distinguish disabled or rewritten routes, middleware-family/version mismatch, gateway filtering, device registration state, or provider-side authorization policy. It is not sufficient evidence to claim that the device is unauthorized, and it does not prove incompatibility with every Stalker/Ministra deployment.

The next evidence requirement is provider-side confirmation of the active portal route and the registered device's authorization mode, followed by one corresponding explicitly selected Windows validation. Until a valid real token is returned, the correct status remains **REAL PORTAL STILL BLOCKED**. No further endpoint permutations, random-token/prehash retries, fabricated identities, VOD/Series/DASH/RTMP work, or VLC changes are justified.

## References

[1]: https://github.com/kidpoleon/stalkerhek/blob/main/stalker/authentication.go "Current stalkerhek authentication source"

[2]: https://github.com/erkexzcx/stalkerhek/blob/master/stalker/authentication.go "Archived stalkerhek authentication source"

[3]: https://github.com/kidpoleon/stalkerhek/blob/main/stalker/portal_meta.go "Current stalkerhek get_profile metadata source"

[4]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-installation-guide/configuration-file "Infomir Ministra configuration reference"
