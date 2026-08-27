# IPTV CONTINUATION / MAG PROTOCOL REPORT

## 1. Work Completed

The completed VLC/MAG/category reliability work was preserved and committed directly to `main`. The only new implementation change in this continuation was an evidence-backed diagnostic improvement in the legacy MAG HTTP connection layer. It now records, without sensitive values, the MAG endpoint path, HTTP method, status, content type, response byte count, and a specific `EMPTY_SESSION_RESPONSE` or `MALFORMED_JSON` classification. Empty responses terminate immediately as an empty-session failure instead of being misreported only as generic malformed JSON.

Deterministic tests were added for successful JSON responses, empty responses, malformed JSON responses, payload non-leakage, and redacted endpoint diagnostics. No MAG protocol compatibility hack was added because the real evidence did not prove a single safe correction.

## 2. Existing Work Preserved

| Area | Preserved state |
|---|---|
| M3U | Real source retrieval, 21,786-channel parsing/translation, 0 rejected records, and stream resolution remain unchanged. |
| Xtream | Real authentication, 187 categories, 14,204 translated channels, 0 rejected records, optional-logo resilience, and stream resolution remain unchanged. |
| VLC | Serialized playback operations, bounded retry, automatic software fallback, buffering configuration, event diagnostics, and production composition wiring remain unchanged. |
| MAG | Adapter-owned session states, secure credential restoration, session reuse, controlled re-authentication, authentication guards, and typed unsupported-category handling remain unchanged. |
| Diagnostics | Existing redaction behavior was preserved and extended at the legacy HTTP response boundary. |

## 3. MAG Investigation

| Item | Evidence |
|---|---|
| Portal reachability | DNS resolved, TCP connected, and the portal landing request returned HTTP 200. |
| Handshake endpoint | The installed legacy provider requests `GET /server/load.php` relative to the configured portal base. With the supplied portal base ending in `/c/`, the application request resolved to `/c/server/load.php`. |
| HTTP status | The real application-path retest returned HTTP 404. A separate root-path probe returned HTTP 200. |
| Content type | The root-path probe returned `text/javascript;charset=UTF-8`; the response body was empty. The application-path 404 response was `text/html`. |
| Response size | Root-path response: 0 bytes. Application-path 404 response: 146 bytes. |
| Expected response | A JSON object containing a token in `js.token` or a top-level `token`; optional `js.token_TTL` controls the session lifetime. |
| Actual response | The configured `/c/server/load.php` application path returned HTTP 404. The root `/server/load.php` variant returned HTTP 200 with an empty non-JSON body. Standard query/header variants did not yield a JSON token response. |
| First failing boundary | Real MAG authentication, at the legacy HTTP/protocol response boundary, before session creation. |
| Root cause | The evidence proves a portal/base-path or portal-variant compatibility mismatch, but does not prove whether the portal requires another base path, a different Stalker variant, or intentionally rejects this client. The current evidence is insufficient for a safe protocol correction. |

The installed legacy implementation uses the MAG-style User-Agent, `X-User-Mac`, optional serial/device headers, and bearer authorization only when a prior token exists. Its handshake parser expects JSON and extracts `js.token` or top-level `token`, with optional `js.token_TTL`. External implementation references describe a common Stalker variant using `type=stb`, `action=handshake`, `token=`, and `JsHttpRequest=1-xml`, plus MAG-specific headers. Those variants were probed against the supplied portal, but none produced a JSON session response. The portal’s behavior therefore remains unresolved rather than being “fixed” by guesswork.

## 4. MAG Fix

The evidence-backed fix was **diagnostic only**. The legacy connection now reads the response once, records safe metadata, classifies empty bodies as `EMPTY_SESSION_RESPONSE`, classifies non-empty non-JSON bodies as `MALFORMED_JSON`, and never logs the response payload, full URL, credentials, cookies, headers, token, or resolved stream URL. The adapter’s authentication guard was not removed, and protocol details remain owned by the legacy MAG connection/session implementation.

## 5. MAG Real Test

| Stage | Result |
|---|---|
| Authentication | **FAIL**. The actual application path returned HTTP 404; the root-path variant returned HTTP 200 with an empty non-JSON response. |
| Session | **FAIL** because no token was established. |
| Categories | **NOT VERIFIED** after authentication failure. The adapter’s unsupported-category behavior remains deterministically tested. |
| Channels | **NOT VERIFIED** after authentication failure. |
| Stream resolution | **NOT VERIFIED** after authentication failure. |
| Playback | **ENVIRONMENT NOT VERIFIED**; no native libVLC runtime is available in the sandbox. |

The real retest produced a safe diagnostic equivalent to:

```text
[IPTV] PROVIDER=MAG OPERATION=HTTP_REQUEST STAGE=AUTHENTICATION METHOD=GET PATH=/c/server/load.php HTTP_STATUS=404 CONTENT_TYPE=text/html RESPONSE_BYTES=146 RESULT=FAIL ERROR=HTTP_STATUS
```

No credential, MAC identity, authorization header, cookie, token, or resolved stream URL appeared in the diagnostic marker.

## 6. Regression

| Area | Result |
|---|---|
| M3U | **PASS** for real source retrieval, parsing, translation, record counts, and stream resolution; Windows UI and real VLC playback remain unverified. |
| Xtream | **PASS** for real authentication, 187 categories, 14,204 channels, 0 rejected records, and stream resolution; real VLC playback remains unverified. |
| VLC | **PASS** for deterministic reliability tests; real playback remains environment-limited because native libVLC is absent. |
| MAG | **PASS** for deterministic lifecycle and redaction tests; **FAIL** for real authentication at the observed portal response boundary. |

## 7. Automated Tests

| Check | Result |
|---|---|
| pytest | **PASS**. Full repository suite: 584 tests. |
| Focused MAG tests | **PASS**. Legacy connection, session, adapter lifecycle, integration, and category tests passed; the expanded connection suite includes successful JSON, empty response, malformed response, and redaction checks. |
| Black | **PASS**. |
| Ruff | **PASS** across `src`, `providers`, and `tests`. |
| mypy | Repository-wide baseline remains failing with 38 errors across 18 unrelated files. No diagnostics were reported for the modified implementation files. |
| git diff --check | **PASS** before commit. |

## 8. Security

| Check | Result |
|---|---|
| Credential leakage | **PASS**. No passwords or usernames were written to diagnostics or reports. |
| MAC leakage | **PASS**. The supplied device identity was not written to code, tests, reports, or diagnostics. |
| Token leakage | **PASS**. Response payloads and token values are not logged. |
| Cookie leakage | **PASS**. Cookies are not logged. |
| Stream URL leakage | **PASS**. Resolved stream URLs are not logged or included in reports. |

## 9. Git

| Item | Result |
|---|---|
| Branch | `main` |
| Commit | `90d91796159cc21d7d8f1e00509eeac4284b5dbd` |
| Commit message | `fix: harden vlc playback and mag session diagnostics` |
| Pushed | **YES**, directly to `origin/main`. |
| HEAD | `90d91796159cc21d7d8f1e00509eeac4284b5dbd` |
| origin/main | `90d91796159cc21d7d8f1e00509eeac4284b5dbd` |
| Remote verified | **YES** after `git fetch origin`; HEAD equals origin/main. |
| Working tree | Clean at the time of push and verification. |

## 10. Remaining Work

### VERIFIED

The completed reliability implementation is committed and published. Real M3U and Xtream live workflows through channel translation and stream resolution remain verified. MAG portal reachability and the exact first authentication failure are verified. Safe MAG response diagnostics and deterministic regression coverage are verified.

### PENDING

A Windows/libVLC run remains pending for real M3U playback, real Xtream playback, H264 decoder fallback, dead-stream behavior, rapid switching, stop-to-play transitions, and UI responsiveness. A MAG retest remains pending if the portal owner supplies the correct Stalker/Ministra base path or protocol variant.

### FAILED

The supplied real MAG portal did not establish a session through the configured application path. The application correctly refused unauthenticated category, channel, and stream operations.

### ENVIRONMENT LIMITATION

The sandbox has the Python VLC binding but no native libVLC runtime or Windows Qt desktop session. Real playback cannot be claimed from this environment.

### NOT TESTED

Real MAG session reuse after successful portal authentication, real session expiration/re-authentication, MAG channel loading, MAG stream resolution, MAG playback, and Windows PowerShell debug output were not tested because authentication failed first or the required desktop runtime was unavailable.

## 11. NEXT PHASE

The core live IPTV path is **partially verified**:

| Provider path | Assessment |
|---|---|
| M3U → channels → stream resolution → VLC | Channels and stream resolution are verified; real VLC playback is pending Windows/libVLC validation. |
| Xtream → channels → stream resolution → VLC | Channels and stream resolution are verified; real VLC playback is pending Windows/libVLC validation. |
| MAG → authentication → channels → stream resolution → VLC | Authentication currently fails at the portal/base-path protocol boundary; downstream stages are not verified. |

The next bounded roadmap phase should be a Windows acceptance run for M3U/Xtream/VLC and, separately, a portal-owner-assisted MAG endpoint/base-path confirmation. VOD, Series, DASH, RTMP, and Ministra feature development should not begin until the live-path acceptance gaps are closed.

## References

[1]: https://github.com/Jitendraunatti/Stalker-Portal/blob/main/config.php "Stalker Portal implementation reference"
[2]: https://github.com/Cyogenus/IPTV-MAC-STALKER-PLAYER-BY-MY-1/blob/main/stalker.py "Stalker client implementation reference"
[3]: https://wiki.infomir.eu/eng/ministra-tv-platform/changelog/stalker-middleware-4-8 "Infomir Stalker Middleware changelog"
