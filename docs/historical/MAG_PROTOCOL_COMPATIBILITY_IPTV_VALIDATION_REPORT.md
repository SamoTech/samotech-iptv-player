# MAG PROTOCOL COMPATIBILITY / IPTV VALIDATION REPORT

## 1. Work Completed

Implemented a deterministic MAG/Stalker protocol compatibility lab without changing the working M3U or Xtream paths. The lab uses an in-process `aiohttp` protocol fixture and drives the real MAG adapter, legacy provider, HTTP connection, session parser, catalogue/stream layers, domain translation, and application category capability boundary.

Added two explicit protocol profiles: the default `legacy` profile preserves the existing bare handshake behavior, while the opt-in `stalker_query` profile models a documented-by-secondary-implementation handshake variant using `type=stb`, `action=handshake`, empty `token`, `JsHttpRequest=1-xml`, X-User-Agent, and Referer headers. No profile is automatically selected for an unknown real portal.

Added explicit MAG category capability behavior and explicit session-error classification in catalogue responses so controlled re-authentication can operate on a real protocol-shaped error envelope. Added deterministic coverage for successful and failed handshakes, TTL, empty/malformed/status responses, missing tokens, session expiry/re-authentication, channels, stream resolution, unsupported categories, profile request construction, and diagnostic safety.

Added the requested MAG protocol, firmware compatibility, research, and test-lab documentation, and updated README, ROADMAP, and CHANGELOG. No VOD, Series, DASH, RTMP, or Ministra feature work was started.

## 2. MAG Research

### Official Infomir findings

Infomir’s Stalker Middleware 4.8 changelog documents version-specific fixes involving authentication, access tokens, loading, and playback. This supports treating firmware and middleware behavior as version-sensitive rather than assuming a single universal MAG protocol. [1]

### Firmware findings

The repository does not have an authorized hardware trace for MAG250, MAG254, MAG256, MAG322, MAG324, MAG325, MAG420, MAG424, MAG520, or MAG524. Their production compatibility is therefore **NOT VERIFIED**. A fixture passing for one protocol shape must not be interpreted as proof for any hardware family.

### Middleware findings

The evidence supports separate compatibility families for legacy bare handshakes and newer Stalker-style query/header requests. The exact middleware generation, firmware generation, and portal base path for the supplied real portal remain unknown.

### Open-source references

Secondary open-source Stalker clients commonly construct `/server/load.php` requests with `type=stb`, `action=handshake`, an empty `token`, `JsHttpRequest=1-xml`, MAG-style User-Agent, X-User-Agent, Referer, and device identity headers. This is reverse-engineered implementation behavior, not an official universal specification. [2] [3]

### Known protocol variants

The lab models two evidence-backed request families: a legacy bare `/server/load.php` request and an opt-in Stalker-query request. Portal-specific base-path behavior is intentionally not guessed or inferred from HTTP 200 alone.

## 3. MAG Compatibility Architecture

### Protocol profile design

`MAGProtocolProfile` owns handshake endpoint/query/header construction. `LegacyMAGProtocolProfile` is the default. `StalkerQueryProtocolProfile` is opt-in and deterministic. The legacy provider/session owns protocol execution and response parsing; the MAG adapter continues to own application/domain translation, credential-store integration, session state, and controlled re-authentication.

### Files changed

The protocol implementation changed `providers/mag/protocol_profile.py`, `providers/mag/session.py`, `providers/mag/provider.py`, and `providers/mag/catalogue.py`. The adapter’s typed unsupported-category method is in `src/samotech_iptv/infrastructure/providers/mag_adapter.py`. The local protocol fixture is `tests/providers/mag/test_compatibility_lab.py`. Documentation is in `docs/MAG_PROTOCOL.md`, `docs/MAG_FIRMWARE_COMPATIBILITY.md`, `docs/MAG_TEST_LAB.md`, and `docs/MAG_RESEARCH_NOTES.md`.

### Application boundary

The tested boundary is:

```text
MAG adapter → legacy MAG provider → MAG session/catalogue/stream → MAGConnection/aiohttp → local fixture portal → parser → domain translation → application capability handling
```

The MAG authentication guard remains active. The adapter never invents a token and never proceeds with authenticated operations after authentication failure.

### HTTP boundary

The fixture uses a real local HTTP server on an ephemeral loopback port. It returns controlled status codes, content types, bodies, JSON envelopes, session-error envelopes, and stream-link responses. No real credentials or production payloads are present in the fixture.

## 4. MAG Test Lab

### Environment

The lab runs under Python 3.12 with the repository’s existing `aiohttp` HTTP abstraction and pytest configuration. It does not emulate MAG hardware; it emulates protocol-server behavior.

### Docker/local fixture

A deterministic in-process local `aiohttp` fixture was used instead of Docker. This keeps the lab self-contained and exercises the production HTTP boundary without introducing an external service dependency.

### Profiles implemented

| Profile | Status |
|---|---|
| Successful legacy-style authentication | **SIMULATED / TESTED** |
| Successful newer-style authentication | **SIMULATED / TESTED** |
| HTTP 200 empty body | **SIMULATED / TESTED** |
| HTTP 200 malformed JSON | **SIMULATED / TESTED** |
| HTTP 401 | **SIMULATED / TESTED** |
| HTTP 403 | **SIMULATED / TESTED** |
| HTTP 404 | **SIMULATED / TESTED** |
| Valid JSON missing token | **SIMULATED / TESTED** |
| Valid token plus TTL | **SIMULATED / TESTED** |
| Expired session | **SIMULATED / TESTED** |
| Successful re-authentication | **SIMULATED / TESTED through the same controlled re-auth path** |
| Unsupported categories | **SIMULATED / TESTED** |
| Successful categories | **SIMULATED route only; NOT VERIFIED by the current MAG adapter**, which intentionally reports category browsing as unsupported |
| Successful channels | **SIMULATED / TESTED** |
| Stream resolution | **SIMULATED / TESTED** |

### Profiles tested

The compatibility-lab file contains 12 collected tests, including nine authentication cases, live channels/stream/unsupported-category application-boundary coverage, controlled session re-authentication, and explicit completeness of the 15 named scenarios. The full repository collection is 599 tests.

## 5. MAG Results

| Stage | Result |
|---|---|
| Authentication | **PASS in both modeled legacy and Stalker-query fixtures; real supplied portal remains UNRESOLVED** |
| Session | **PASS in fixtures** for token establishment, reuse, TTL-compatible state, expiry detection, and one controlled re-authentication. |
| Categories | **UNSUPPORTED** for the current MAG adapter by design. The local fixture includes a successful-category route for protocol completeness, but the current application capability intentionally does not expose MAG category browsing. |
| Channels | **PASS in the local fixture** through provider response parsing and canonical channel translation. |
| Stream resolution | **PASS in the local fixture** through the legacy stream-link protocol and URL validation. |
| Re-authentication | **PASS in the local fixture** with one controlled re-authentication after an explicit session-error envelope. |

These fixture results are **SIMULATED**, not production-portal support claims.

## 6. Real MAG Portal

| Item | Result |
|---|---|
| Reachability | **PASS** for DNS, TCP, and HTTP reachability. |
| Application path | **FAIL** at the configured `/c/server/load.php` path: HTTP 404, `text/html`, 146 bytes. |
| Root path | **UNRESOLVED** protocol response: HTTP 200, `text/javascript;charset=UTF-8`, 0 bytes. |
| Protocol variant | **UNRESOLVED**. Standard query/header variants tested did not produce a JSON token response. |
| Authentication | **FAIL** for the supplied portal at the application boundary; no token was established. |
| Conclusion | **REAL PORTAL COMPATIBILITY UNRESOLVED**. No speculative path or profile selection was added, no token was faked, and the authentication guard was not bypassed. |

This single portal result does not establish that MAG/Stalker support is globally broken, nor does it establish complete production support.

## 7. M3U

| Check | Result |
|---|---|
| Channels | **PASS** from prior real validation: 21,786 received and translated, 0 rejected. |
| Stream resolution | **PASS** from prior real validation. |
| Windows UI | **NOT VERIFIED** in the sandbox. |
| VLC | **ENVIRONMENT LIMITATION / NOT VERIFIED** because native libVLC was unavailable. |

No M3U code path was modified in this compatibility-lab increment.

## 8. Xtream

| Check | Result |
|---|---|
| Categories | **PASS** from prior real validation: 187 live categories. |
| Channels | **PASS** from prior real validation: 14,204 received and translated. |
| Rejected | **0**. |
| Stream resolution | **PASS** from prior real validation. |
| Windows UI | **NOT VERIFIED** in the sandbox. |
| VLC | **ENVIRONMENT LIMITATION / NOT VERIFIED** because native libVLC was unavailable. |

No Xtream code path was modified in this compatibility-lab increment.

## 9. VLC

| Check | Result |
|---|---|
| Automated | **PASS** for serialized operations, bounded retry, hardware-to-software fallback, caching, event diagnostics, and lifecycle behavior. |
| Real | **NOT VERIFIED**; the sandbox has the Python binding but no usable native libVLC runtime. |
| Windows pending | Actual video/audio, H264 problematic stream, software fallback, dead stream, bounded retry, rapid switching, stop-to-play, and UI responsiveness. |
| Fallback | **SIMULATED / TESTED** in deterministic adapter tests; real decoder fallback is pending Windows/libVLC validation. |
| Dead stream | **SIMULATED / TESTED** in deterministic adapter tests; real VLC behavior is pending. |
| Rapid switching | **SIMULATED / TESTED** for serialized adapter operations; real UI/player switching is pending. |

## 10. Security

| Check | Result |
|---|---|
| Credential leakage | **PASS**. Fake identities only in committed fixtures; no supplied credential values in code, tests, reports, or diagnostics. |
| MAC leakage | **PASS**. No supplied device identity was committed or logged. |
| Token leakage | **PASS**. Fixture tokens are test-local and not emitted by diagnostics; production response payloads are not logged. |
| Cookie leakage | **PASS**. Cookies are not included in diagnostics. |
| Stream URL leakage | **PASS** for production diagnostics and reports. Fixture assertions use loopback URLs only. |

## 11. Quality

| Check | Result |
|---|---|
| pytest | **PASS**. Full collected suite: 599 tests; full run passed. |
| Black | **PASS** across `src`, `providers`, and `tests`. |
| Ruff | **PASS** across `src`, `providers`, and `tests`. |
| mypy | Repository baseline remains **FAIL** with 38 errors across 18 unrelated files; no new diagnostics were reported for the modified MAG/profile files. |
| diff-check | **PASS**. |

## 12. Git

| Item | Result |
|---|---|
| Branch | `main` |
| Commit | `b4f36f57a620c8e894dbf57e0962cebe49166356` |
| Pushed | **YES**, directly to `origin/main`. |
| HEAD | `b4f36f57a620c8e894dbf57e0962cebe49166356` |
| origin/main | `b4f36f57a620c8e894dbf57e0962cebe49166356` |
| Verified | **YES** after fetch; HEAD equals origin/main. |
| Working tree | Clean after push verification. |

## 13. Remaining Roadmap

### VERIFIED

The deterministic MAG compatibility lab, profile construction, session lifecycle, controlled re-authentication, unsupported-category handling, channel translation, stream resolution, and security behavior are verified through local protocol fixtures. Prior real M3U and Xtream channel/stream-resolution baselines remain verified. The reliability implementation is published on `main`.

### PENDING

Real Windows/libVLC acceptance for M3U and Xtream playback remains pending. The user must run the PowerShell debug session and test actual video/audio, H264 fallback, dead-stream handling, rapid switching, stop-to-play, and UI responsiveness. An authorized MAG portal trace or provider-confirmed base path/profile is also pending.

### FAILED

The supplied real MAG portal fails authentication through the configured application path and does not provide a JSON token through the root/standard variants tested. This is a portal compatibility failure for that supplied case, not a global MAG support conclusion.

### UNRESOLVED

The exact real-portal base path, Stalker/Ministra generation, firmware/client expectation, and provider-specific handshake contract remain unresolved.

### ENVIRONMENT LIMITATION

The sandbox cannot provide real native libVLC playback or Windows Qt acceptance.

### NEXT BOUNDED PHASE

Run the Windows acceptance matrix for M3U and Xtream first. Separately obtain an authorized MAG portal/profile trace before selecting or extending a production profile. Do not begin VOD, Series, DASH, RTMP, or Ministra feature development until the live-path acceptance gaps are closed.

## References

[1]: https://wiki.infomir.eu/eng/ministra-tv-platform/changelog/stalker-middleware-4-8 "Infomir Stalker Middleware changelog"
[2]: https://github.com/Cyogenus/IPTV-MAC-STALKER-PLAYER-BY-MY-1/blob/main/stalker.py "Secondary open-source Stalker client reference"
[3]: https://github.com/Jitendraunatti/Stalker-Portal/blob/main/config.php "Secondary open-source portal implementation reference"
