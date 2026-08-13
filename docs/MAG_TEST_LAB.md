# MAG/Stalker Compatibility Test Lab

## Environment

The lab uses an in-process `aiohttp` protocol fixture on an ephemeral loopback port. It does not emulate MAG hardware. The fixture is a deterministic protocol server, and tests drive the real legacy MAG provider, HTTP connection, session parser, catalogue and stream helpers, MAG adapter, and application category use-case boundary.

## Profiles implemented

The lab declares these 15 scenarios:

| Profile | Classification |
|---|---|
| Legacy successful authentication | **SIMULATED and TESTED** |
| Stalker query successful authentication | **SIMULATED and TESTED** |
| HTTP 200 empty body | **SIMULATED and TESTED** |
| HTTP 200 malformed JSON | **SIMULATED and TESTED** |
| HTTP 401 | **SIMULATED and TESTED** |
| HTTP 403 | **SIMULATED and TESTED** |
| HTTP 404 | **SIMULATED and TESTED** |
| Valid JSON missing token | **SIMULATED and TESTED** |
| Valid token plus TTL | **SIMULATED and TESTED** |
| Expired session | **SIMULATED and TESTED** through explicit JSON session-error handling and one controlled re-authentication |
| Successful re-authentication | **SIMULATED** as a named scenario and covered by the same re-authentication path |
| Unsupported categories | **SIMULATED and TESTED** through the typed MAG capability result |
| Successful categories | **SIMULATED route only; NOT VERIFIED by the current MAG adapter**, which intentionally reports category browsing as unsupported |
| Successful channels | **SIMULATED and TESTED** |
| Stream resolution | **SIMULATED and TESTED** |
| Bounded endpoint discovery | **SIMULATED and TESTED** for the six approved candidate families, safe classification, deterministic priority, conditional `prehash=false`, and reuse of the selected endpoint family for authenticated live-channel loading. |
| HTTP resource lifecycle | **SIMULATED and TESTED** for retained successful-session reuse, discovery/authentication failure cleanup, repeated failure cleanup, provider shutdown, and absence of `ResourceWarning` from the deterministic failure path. |

The fixture uses fake identities and local loopback URLs only. No real account or provider payload is committed. Helper-profile tests that assert the source-observed model-dependent X-User-Agent supply `mag_model` explicitly; the production credential bridge defaults to MODEL UNKNOWN and never fabricates MAG250/MAG254.

The deterministic state-machine coverage includes: handshake-only; handshake plus `get_profile`; handshake plus `get_profile` plus explicit POST `do_auth`; missing login/password; missing authorization key; model rejection; device-ID requirement; explicit identity pass-through; and existing session-expiry/re-authentication behavior. Policy markers are normalized safely and are never inferred from a bare HTTP 404.

## Boundaries exercised

The principal tests execute:

```text
MAG adapter
  → legacy MAG provider
  → MAG session / catalogue / stream protocol layer
  → MAGConnection and aiohttp
  → local fixture portal
  → response parser
  → canonical domain translation
  → application category capability handling
```

Authentication tests verify token extraction, TTL-compatible success, empty/malformed/status failures, and safe failure states. Discovery tests verify that the candidate list is finite, every result retains safe metadata only, HTTP success alone is insufficient, and the selected endpoint family is reused by normal session and live-channel operations. Resource-lifecycle tests verify that the legacy provider closes its owned aiohttp resources after failed discovery/authentication, does not accumulate sessions across repeated failures, keeps a successful session reusable until explicit provider close, and does not emit a `ResourceWarning` in the fixture failure path. Live-path tests verify channel translation, stream-link resolution, and typed unsupported-category behavior. Expiry tests verify one controlled re-authentication and session reuse rather than authentication on every operation.

## Differential request lab

`tests/providers/mag/test_differential_lab.py` defines exactly six fixed source-backed cases: T01 GUI GET handshake; T02 GUI POST handshake; T03 helper GET with empty token and `prehash=false`; T04 helper GET with empty token and `prehash=0`; T05 GUI POST with `prehash=false`; and T06 helper POST with `prehash=0`. Each case retains only test ID, profile, endpoint, method, safe response metadata, JSON/token/profile/error flags, and classification. It is not a generic scanner.

## Real portal distinction

Passing a fixture profile proves only that the application handles that modeled protocol response. It does not prove compatibility with a production portal. The supplied real portal remains unresolved because the bounded six-candidate set returned four HTTP 404 responses, one HTTP 200 empty `text/javascript` response, and one HTTP 404 GUI fingerprint response. A corrected GUI-cookie revalidation also returned HTTP 404. The new T01–T06 differential matrix returned HTTP 404 for every case; GUI cases were `text/javascript` with zero bytes and helper cases were `text/html` with 146 bytes. One explicit MAG254 helper request also returned HTTP 404. No JSON, token, profile, or machine-readable policy marker was returned.


## Source-derived middleware laboratory

`tests/providers/mag/test_middleware_lab.py` provides a deterministic **SOURCE-DERIVED / SIMULATED** classic middleware server based on the readable open-source dispatcher contract: `/stalker_portal/server/load.php` receives `type` and `action`, authenticated requests carry Bearer authorization plus token/MAC cookies, and live catalogue calls use `get_genres`, page-one/page-two `get_ordered_list`, and command-based `create_link`. The test drives the real MAG provider through the adapter boundary and proves handshake, TTL, token transport, genres, pagination, channel translation, and stream resolution against local test data. It does not emulate hardware or establish production support.

## Stalker client compatibility profiles

`stalker_gui_compatibility` and `stalker_helper_compatibility` are **IMPLEMENTED and SIMULATED** from secondary reverse-engineered client references. They remain evidence-based request profiles, not middleware-version claims. The GUI profile uses the origin-relative `portal.php` family and page-zero live pagination; the helper profile uses origin-relative `stalker_portal/server/load.php` and page-one live pagination. Model-dependent X-User-Agent is emitted only when `mag_model` is explicitly supplied; absent that field, the model is UNKNOWN. Both exclude fabricated device identities and the helper source’s unverified 404 random-token/prehash sequence. A real token-bearing handshake remains required to establish compatibility for any particular firmware or portal.
