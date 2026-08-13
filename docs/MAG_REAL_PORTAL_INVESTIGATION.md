# MAG Real-Portal Investigation

**Date:** 2026-08-13

**Repository:** `SamoTech/samotech-iptv-player`
**Status:** **UNRESOLVED — no real token-bearing handshake**

This report records the final evidence-backed phase after the original bounded endpoint set had already been exhausted. It does not claim production MAG support from local fixtures, HTTP 200, application startup, or VLC initialization.

## 1. Exact tests executed

| Test | Purpose | Result |
|---|---|---|
| Existing full suite `pytest -q` | Regression coverage across the repository | PASS |
| `tests/providers/mag/test_auth_state_machine.py` | Handshake-only, optional `get_profile`, explicit POST `do_auth`, missing login, missing key, policy markers, explicit identity fields | PASS |
| `tests/providers/mag/test_differential_lab.py` | Fixed local T01–T06 differential matrix | PASS |
| `tests/providers/mag/test_middleware_lab.py` | Source-derived classic middleware handshake → genres → ordered list → command → `create_link` | PASS |
| Authorized T01 | GUI GET handshake | HTTP 404 |
| Authorized T02 | GUI POST handshake | HTTP 404 |
| Authorized T03 | Helper GET, empty token, `prehash=false` | HTTP 404 |
| Authorized T04 | Helper GET, empty token, `prehash=0` | HTTP 404 |
| Authorized T05 | GUI POST, `prehash=false` | HTTP 404 |
| Authorized T06 | Helper POST, `prehash=0` | HTTP 404 |
| Authorized MODEL-01 | Exactly one explicit `MAG254` helper request | HTTP 404 |

No arbitrary paths, ports, Host headers, proxies, SSRF, WAF bypass, brute force, or credential guessing were used.

## 2. Source evidence behind every new request variant

The new request variants are justified by the current public `kidpoleon/stalkerhek` source and the archived `erkexzcx/stalkerhek` source. The current source constructs a GET handshake with `type=stb`, `action=handshake`, `token`, and `JsHttpRequest=1-xml`; it sends MAG-style headers/cookies and supports an explicit model field. It constructs `do_auth` as an `application/x-www-form-urlencoded` POST with login, password, optional device IDs, and `JsHttpRequest=1-xml`. It also calls `get_profile` with optional `hd`, `sn`, `stb_type`, device IDs, and `auth_second_step`. [1] [2]

The archived source independently documents a GET handshake using `prehash=0` and `token`, and a credential-bearing `do_auth` request. [2] The supplied client references provide the helper and GUI fingerprints already present in the repository. These sources justify a finite method/form/prehash differential matrix, not a general endpoint scanner.

## 3. Real response classifications

| Test | Endpoint family | Method | Content-Type | Bytes | JSON | Token | Profile | Error field | Classification |
|---|---|---:|---|---:|---|---|---|---|---|
| T01 | `portal.php` GUI | GET | `text/javascript` | 0 | No | No | No | No | `HTTP_404` |
| T02 | `portal.php` GUI | POST | `text/javascript` | 0 | No | No | No | No | `HTTP_404` |
| T03 | `stalker_portal/server/load.php` helper | GET | `text/html` | 146 | No | No | No | No | `HTTP_404` |
| T04 | `stalker_portal/server/load.php` helper | GET | `text/html` | 146 | No | No | No | No | `HTTP_404` |
| T05 | `portal.php` GUI | POST | `text/javascript` | 0 | No | No | No | No | `HTTP_404` |
| T06 | `stalker_portal/server/load.php` helper | POST | `text/html` | 146 | No | No | No | No | `HTTP_404` |
| MODEL-01 | `stalker_portal/server/load.php` helper, explicit model | GET | `text/html` | 146 | No | No | No | No | `HTTP_404` |

No machine-readable response was returned, so no policy classification such as `STB_NOT_AUTHORIZED`, `STB_MODEL_REJECTED`, `LOGIN_REQUIRED`, `DEVICE_ID_REQUIRED`, or `AUTH_KEY_REQUIRED` is asserted.

## 4. Authentication state transition

The real portal state transition was:

```text
DISCOVERY
  → HANDSHAKE ATTEMPTS T01–T06 and MODEL-01
  → NO TOKEN_RECEIVED
  → SESSION_VALIDATED NOT REACHED
  → CATALOGUE NOT REACHED
```

The implemented state machine supports the following explicit paths when the portal returns machine-readable success/policy data:

```text
HANDSHAKE → TOKEN_RECEIVED → SESSION_VALIDATED
HANDSHAKE → TOKEN_RECEIVED → GET_PROFILE → SESSION_VALIDATED
HANDSHAKE → TOKEN_RECEIVED → GET_PROFILE → DO_AUTH → SESSION_VALIDATED
HANDSHAKE → TOKEN_RECEIVED → DO_AUTH → SESSION_VALIDATED
```

No path is selected automatically from a bare HTTP status.

## 5. Whether a token was received

**No.** None of T01–T06 or MODEL-01 returned JSON or a token. No token was fabricated, cached, logged, or reused. The application’s strict token gate correctly stopped authentication.

## 6. Whether `get_profile` was required

**Not determinable for the real portal.** The portal did not produce a handshake token, so `get_profile` could not be reached legitimately. The implementation now supports an explicit `profile_required`/`profile_second_step` configuration and sends minimal `type=stb`, `action=get_profile`, `JsHttpRequest=1-xml` first, adding only explicitly supplied identity fields.

The deterministic tests prove the stage locally; they do not prove that the real portal requires it.

## 7. Whether `do_auth` was required

**Not determinable for the real portal.** No handshake token was received, so no real `do_auth` request was sent. The implementation supports `mag_auth_mode=mac_plus_login` explicitly, mapping configured login/password to form-encoded POST fields without placing the password in the URL or logs. Missing credentials classify as `LOGIN_REQUIRED`.

## 8. Whether model identity mattered

**Not determinable for the real portal.** The no-model helper request returned HTTP 404. Exactly one explicit `MAG254` helper request, justified by the new source evidence, also returned HTTP 404 with the same safe metadata. No model spraying was performed. The runtime leaves the model **UNKNOWN** unless `mag_model` is explicitly configured and never infers it from User-Agent.

## 9. Whether device identity mattered

**Not determinable for the real portal.** No machine-readable response required or rejected serial/device fields. The implementation accepts explicit `serial_number`, `device_id`, `device_id2`, and `signature` values, sends them only when supplied, and never generates or derives them.

## 10. Whether authorization-key mode mattered

**Not determinable for the real portal.** No policy response required an authorization key. The implementation exposes explicit `mag_auth_mode=authorization_key` and `authorization_key` fields. An absent key fails as `AUTH_KEY_REQUIRED`; a transport algorithm is not invented.

## 11. Real category count

**Unavailable.** The real portal never established a session, so `get_genres` was not called. Local source-derived lab: one deterministic live genre.

## 12. Real channel count

**Unavailable.** The real portal never returned ordered-list records. Local source-derived lab: three deterministic live channels across helper page 1 and page 2.

## 13. Rejected channel count

**Unavailable for the real portal.** No real records were received. The local catalogue retains safe aggregate received/accepted/rejected counts and rejects records lacking ID, name, or command.

## 14. `create_link` result

**Not reached for the real portal.** No real channel command was received. The local laboratory passes actual command retention and profile-owned `type=itv`, `action=create_link`, `cmd`, `JsHttpRequest=1-xml` handling.

## 15. Real stream result

**Not reached.** No real stream URL was returned. The resolver accepts only URLs with `http`, `https`, `rtsp`, or `rtmp` schemes and never logs them.

## 16. Windows playback result

**Not tested for MAG.** Existing user-provided Windows evidence confirms M3U/Xtream playback and VLC/libVLC availability. MAG stopped before real stream resolution, so video, audio, stop/play, switching, dead-stream recovery, and MAG-specific VLC diagnosis were correctly not attempted.

## 17. Final root cause

**UNRESOLVED: routing/deployment/provider-side policy boundary.** Every evidence-backed differential request returned an Nginx-style HTTP 404: GUI cases returned zero-byte `text/javascript`; helper cases returned 146-byte `text/html`. No response contained JSON, an error field, a token, a profile, or an authorization marker. Therefore the evidence does not distinguish disabled classic routing, reverse-proxy/rewrite behavior, middleware-family/version mismatch, gateway filtering, MAC registration/new-STB status, login/key policy, or model policy.

A bare 404 is deliberately not classified as STB-not-authorized. The result also does not prove the portal is incompatible with all Stalker/Ministra implementations.

## 18. Exact remaining blocker

The exact blocker is **absence of a machine-readable handshake response from every evidence-backed request form tested**. The next justified action is provider-side confirmation of the registered/active status and configured authorization mode for the supplied device identity, followed by one corresponding explicitly selected Windows attempt. No new endpoint or protocol profile should be added until that fact or a new machine-readable response is available.

## Security status

No credential, MAC, token, cookie, Authorization value, device identity, raw response body, or stream URL is present in this report. No fake identity, token, authorization key, password guess, brute force, WAF bypass, or arbitrary scanning was performed.

## References

[1]: https://github.com/kidpoleon/stalkerhek/blob/main/stalker/authentication.go "Current stalkerhek authentication source"
[2]: https://github.com/erkexzcx/stalkerhek/blob/master/stalker/authentication.go "Archived stalkerhek authentication source"
[3]: https://github.com/kidpoleon/stalkerhek/blob/main/stalker/portal_meta.go "Current stalkerhek get_profile metadata source"
[4]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-installation-guide/faq/how-to-organize-the-access-to-the-portal-by-login-and-password "Infomir login/password and authorization-key access"
[5]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-installation-guide/configuration-file "Infomir Ministra configuration reference"
