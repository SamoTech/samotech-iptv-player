# MAG Real-Portal Investigation

**Date:** 2026-08-13

**Repository:** `SamoTech/samotech-iptv-player`
**Status:** **UNRESOLVED — no real token-bearing handshake**

This report records the final evidence-backed phase after the original bounded endpoint set had already been exhausted. It includes the post-commit revalidation using configured-path preservation and safe response-header metadata. It does not claim production MAG support from local fixtures, HTTP 200, application startup, or VLC initialization.

## 1. Exact tests executed

| Test | Purpose | Result |
|---|---|---|
| Existing full suite `pytest -q` | Regression coverage across the repository | PASS |
| `tests/providers/mag/test_auth_state_machine.py` | Handshake-only, optional `get_profile`, explicit POST `do_auth`, missing login, missing key, policy markers, explicit identity fields | PASS |
| `tests/providers/mag/test_differential_lab.py` | Fixed local T01–T06 differential matrix | PASS |
| `tests/providers/mag/test_middleware_lab.py` | Source-derived classic middleware handshake → genres → ordered list → command → `create_link` | PASS |
| `tests/providers/mag/test_portal_php_legacy_lab.py` | Concrete portal.php MAC handshake → account info → genres → direct channels → `cmds[].url` stream resolution | PASS |
| Complete quality gate | `black --check`, `ruff check`, `mypy`, `pytest -q`, and `git diff --check` | PASS |
| Authorized T01 | GUI GET handshake | HTTP 404 |
| Authorized T02 | GUI POST handshake | HTTP 404 |
| Authorized T03 | Helper GET, empty token, `prehash=false` | HTTP 404 |
| Authorized T04 | Helper GET, empty token, `prehash=0` | HTTP 404 |
| Authorized T05 | GUI POST, `prehash=false` | HTTP 404 |
| Authorized T06 | Helper POST, `prehash=0` | HTTP 404 |
| Authorized MODEL-01 | Exactly one explicit `MAG254` helper request | HTTP 404 |
| Authorized PORTAL-PHP-01 | New concrete origin portal.php MAC-client handshake | HTTP 404 |

No arbitrary paths, ports, Host headers, proxies, SSRF, WAF bypass, brute force, or credential guessing were used.

## 2. Source evidence behind every new request variant

The new request variants are justified by the current public `kidpoleon/stalkerhek` source, the archived `erkexzcx/stalkerhek` source, and the newly supplied independently implemented client contract. The supplied client adds a concrete browser-style origin `portal.php` handshake with MAC Authorization and a raw MAC cookie, followed after a token by account info on `portal.php`, genres on `server/load.php`, and channels on `portal.php`; channel records may provide direct `cmds[].url` values.
 The current source constructs a GET handshake with `type=stb`, `action=handshake`, `token`, and `JsHttpRequest=1-xml`; it sends MAG-style headers/cookies and supports an explicit model field. It constructs `do_auth` as an `application/x-www-form-urlencoded` POST with login, password, optional device IDs, and `JsHttpRequest=1-xml`. It also calls `get_profile` with optional `hd`, `sn`, `stb_type`, device IDs, and `auth_second_step`. [1] [2]

The archived source independently documents a GET handshake using `prehash=0` and `token`, and a credential-bearing `do_auth` request. [2] The supplied client references provide the helper and GUI fingerprints already present in the repository. These sources justify a finite method/form/prehash differential matrix, not a general endpoint scanner.

## 3. Real response classifications

| Test | Endpoint family | Method | Content-Type | Bytes | Redirects | Server | Allow | WWW-Authenticate | JSON | Token | Profile | Error field | Classification |
|---|---|---:|---|---:|---:|---|---|---|---|---|---|---|---|
| T01 | `portal.php` GUI | GET | `text/javascript` | 0 | 0 | `nginx` | No | No | No | No | No | No | `HTTP_404` |
| T02 | `portal.php` GUI | POST | `text/javascript` | 0 | 0 | `nginx` | No | No | No | No | No | No | `HTTP_404` |
| T03 | `stalker_portal/server/load.php` helper | GET | `text/html` | 146 | 0 | `nginx` | No | No | No | No | No | No | `HTTP_404` |
| T04 | `stalker_portal/server/load.php` helper | GET | `text/html` | 146 | 0 | `nginx` | No | No | No | No | No | No | `HTTP_404` |
| T05 | `portal.php` GUI | POST | `text/javascript` | 0 | 0 | `nginx` | No | No | No | No | No | No | `HTTP_404` |
| T06 | `stalker_portal/server/load.php` helper | POST | `text/html` | 146 | 0 | `nginx` | No | No | No | No | No | No | `HTTP_404` |
| MODEL-01 | `stalker_portal/server/load.php` helper, explicit model | GET | `text/html` | 146 | 0 | `nginx` | No | No | No | No | No | No | `HTTP_404` |
| PORTAL-PHP-01 | `portal.php` concrete MAC client | GET | `text/javascript` | 0 | 0 | `nginx` | No | No | No | No | No | No | `HTTP_404` |

No machine-readable response was returned, so no policy classification such as `STB_NOT_AUTHORIZED`, `STB_MODEL_REJECTED`, `LOGIN_REQUIRED`, `DEVICE_ID_REQUIRED`, or `AUTH_KEY_REQUIRED` is asserted.

## 4. Authentication state transition

The combined authorized evidence set has the following state transition:

```text
DISCOVERY
  → HANDSHAKE ATTEMPTS T01–T06, MODEL-01, and PORTAL-PHP-01
  → NO TOKEN_RECEIVED
  → SESSION_VALIDATED NOT REACHED
  → CATALOGUE NOT REACHED
```

The post-commit T01–T06 rerun used the corrected configured-base URL behavior for helper requests. The new PORTAL-PHP-01 direct profile test also produced HTTP 404 with `text/javascript`, zero bytes, `Server: nginx`, zero redirects, no `Allow`, no `WWW-Authenticate`, no JSON, and no token, so no continuation request was made.

The implemented state machine supports the following explicit paths when the portal returns machine-readable success/policy data:

```text
HANDSHAKE → TOKEN_RECEIVED → SESSION_VALIDATED
HANDSHAKE → TOKEN_RECEIVED → ACCOUNT_INFO → SESSION_VALIDATED
HANDSHAKE → TOKEN_RECEIVED → GET_PROFILE → SESSION_VALIDATED
HANDSHAKE → TOKEN_RECEIVED → GET_PROFILE → DO_AUTH → SESSION_VALIDATED
HANDSHAKE → TOKEN_RECEIVED → DO_AUTH → SESSION_VALIDATED
```

No path is selected automatically from a bare HTTP status.

## 5. Whether a token was received

**No.** None of the post-commit T01–T06 rerun, MODEL-01, or PORTAL-PHP-01 returned JSON or a token.
 No token was fabricated, cached, logged, or reused. The application’s strict token gate correctly stopped authentication.

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

**Unavailable.** The real portal never established a session, so `get_genres` was not called. The new local portal.php lab reaches one deterministic live genre after account info.

## 12. Real channel count

**Unavailable.** The real portal never returned direct channel records. The new local portal.php lab receives three records, accepts two, and rejects one missing a usable command.

## 13. Rejected channel count

**Unavailable for the real portal.** No real records were received. The local direct-catalogue path retains safe aggregate received/accepted/rejected counts and rejects records lacking ID, name, or direct command.

## 14. `create_link` result

**Not reached for the real portal.** No real channel command was received. The local portal.php laboratory passes direct `cmds[].url` retention and stream extraction; the existing laboratory separately covers profile-owned `create_link`.

## 15. Real stream result

**Not reached.** No real stream URL was returned. The resolver accepts only URLs with `http`, `https`, `rtsp`, or `rtmp` schemes and never logs them.

## 16. Windows playback result

**Not tested for MAG.** Existing user-provided Windows evidence confirms M3U/Xtream playback and VLC/libVLC availability. The fresh Windows run included the new discovery candidate but stopped at TCP connection with repeated `WinError 121`, before any HTTP response or stream resolution; video, audio, stop/play, switching, dead-stream recovery, and MAG-specific VLC diagnosis remain unverified.

## 17. Final root cause

**UNRESOLVED: Windows transport path first; historical HTTP routing second.** The fresh Windows run failed before HTTP with repeated TCP `WinError 121`. Separately, every post-commit evidence-backed differential request from the successful HTTP path, including the new concrete portal.php MAC-client handshake, returned an Nginx-style HTTP 404 or empty response: GUI cases returned zero-byte `text/javascript`; helper cases returned 146-byte `text/html`; PORTAL-PHP-01 returned zero-byte `text/javascript`; all had zero redirects, no `Allow` header, and no `WWW-Authenticate` header.
 No response contained JSON, an error field, a token, a profile, or an authorization marker. Therefore the evidence does not distinguish disabled classic routing, reverse-proxy/rewrite behavior, middleware-family/version mismatch, gateway filtering, MAC registration/new-STB status, login/key policy, or model policy.

A bare 404 is deliberately not classified as STB-not-authorized. The result also does not prove the portal is incompatible with all Stalker/Ministra implementations.

## 18. Exact remaining blocker

The latest Windows blocker is **TCP transport failure before any HTTP response**, while the historical sandbox/authorized HTTP blocker is absence of a machine-readable handshake response from the tested request forms, including the newly supplied portal.php MAC Authorization contract.
 The next justified action is to run `tools/mag_transport_probe.ps1` on the same Windows machine and network using raw TCP, PowerShell, WinHTTP, and curl. Resolve reachability if those tools time out; only if they receive HTTP should provider-side route/authorization confirmation and further protocol analysis proceed. No new endpoint or protocol profile should be added until a new machine-readable response is available.

## Security status

No credential, MAC, token, cookie, Authorization value, device identity, raw response body, or stream URL is present in this report. Only safe response metadata was retained: case ID, profile, method, status, content type, byte count, redirect count, selected header presence/value, JSON/token flags, and classification. No fake identity, token, authorization key, password guess, brute force, WAF bypass, or arbitrary scanning was performed.

## References

[1]: https://github.com/kidpoleon/stalkerhek/blob/main/stalker/authentication.go "Current stalkerhek authentication source"
[2]: https://github.com/erkexzcx/stalkerhek/blob/master/stalker/authentication.go "Archived stalkerhek authentication source"
[3]: https://github.com/kidpoleon/stalkerhek/blob/main/stalker/portal_meta.go "Current stalkerhek get_profile metadata source"
[4]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-installation-guide/faq/how-to-organize-the-access-to-the-portal-by-login-and-password "Infomir login/password and authorization-key access"
[5]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-installation-guide/configuration-file "Infomir Ministra configuration reference"
