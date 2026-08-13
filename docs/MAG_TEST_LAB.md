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
| Bounded endpoint discovery | **SIMULATED and TESTED** for the four approved candidate families, safe classification, deterministic priority, conditional `prehash=false`, and reuse of the selected endpoint family for authenticated live-channel loading. |
| HTTP resource lifecycle | **SIMULATED and TESTED** for retained successful-session reuse, discovery/authentication failure cleanup, repeated failure cleanup, provider shutdown, and absence of `ResourceWarning` from the deterministic failure path. |

The fixture uses fake identities and local loopback URLs only. No real account or provider payload is committed.

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

## Real portal distinction

Passing a fixture profile proves only that the application handles that modeled protocol response. It does not prove compatibility with a production portal. The supplied real portal remains unresolved because it returned 404 for the configured application path and 200 empty `text/javascript` for the root path.


## Stalker client compatibility profile

The lab additionally covers the bounded `stalker_client_compatibility` profile through the adapter, protocol profile, HTTP transport, fixture portal, parser, and canonical translator. It verifies the observed `portal.php` request fingerprint, strict JSON-token gate, private cookie/authentication transition, TTL handling, live genres, ordered-list channels, loaded-channel command `create_link`, stream-command extraction, lifecycle cleanup, and sensitive-value redaction. This remains **SIMULATED and TESTED**; it is not evidence of real portal authentication, channels, stream resolution, or VLC playback.
