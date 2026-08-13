# MAG Transport-Layer Investigation

## Executive conclusion

> **The latest Windows run fails before HTTP at the TCP transport boundary.** It resolves the portal hostname, but every bounded discovery connection ends with Windows `WinError 121` (“The semaphore timeout period has expired”). No HTTP status, content type, response bytes, or server headers were received in that run.

This result is materially different from the earlier authorized HTTP 404 evidence. The 404 cases prove that an HTTP response can be obtained from at least one network path; the latest Windows run proves that the actual Windows path used for the application did not complete TCP/HTTP connectivity at that time. No production MAG authentication semantics were changed in response to the timeout.

## Layer-by-layer result

| Layer | Evidence | Result |
|---|---|---|
| DNS | Windows log resolves the hostname to an IPv4 address | **PASS** |
| TCP connect from Windows | Repeated `WinError 121` from the Windows Proactor connect completion | **FAIL / FIRST PROVEN FAILURE** |
| HTTP from that Windows run | No status or response headers for any candidate | **NOT REACHED** |
| Historical HTTP routing | Earlier authorized cases returned 404 or empty 200 from another path | **OBSERVED ON A DIFFERENT RUN/PATH** |
| Request fingerprint | New portal.php MAC profile was present in Windows discovery, but no request reached HTTP | **NOT EVALUATED BY THIS RUN** |
| Handshake/token | No machine-readable response and no token | **NOT REACHED** |
| Session/catalogue/stream/playback | No authenticated continuation | **NOT REACHED** |

The application correctly closed its HTTP session after bounded discovery and translated the failure to `AuthenticationError`; it did not treat the timeout as authorization rejection or as an empty catalogue.

## Windows execution evidence

The updated Windows application included all seven bounded candidates, including `origin_portal_php_mac_client`. Each candidate was classified as `NETWORK_FAILURE`, with approximately 21 seconds elapsed per attempt. The complete LOAD_CHANNELS operation took approximately 148 seconds and returned zero records. The first concrete error was repeated `OSError: [WinError 121]` from the Windows asyncio Proactor during TCP connection completion.

A subsequent Windows-native matrix confirmed the same boundary independently. The posted matrix used a different MAC identity from the original authorized test credential; because all probes failed before HTTP, this does not affect the TCP conclusion but must not be used as evidence about the original device’s authorization or protocol behavior.
 PowerShell `Invoke-WebRequest` timed out without an HTTP status, WinHTTP timed out without an HTTP status, and the raw TCP probe explicitly failed during TCP connect with `TimeoutException: TCP connect timeout`. The companion script did not execute curl; its result was a placeholder instructing a separate curl run. Therefore the Windows evidence proves TCP connect failure and absence of an HTTP response, but does not yet include an independent curl result.

The long duration is explained by independent per-candidate timeout behavior: the same unreachable destination was attempted for each bounded candidate. This is a user-experience characteristic of the failure path, not evidence that any candidate reached the portal or that a new protocol permutation is required.

## Safe sandbox transport matrix

A standalone matrix was run outside production MAG code using the same concrete portal.php handshake request internally. It retained only safe metadata. PowerShell was unavailable in the Linux sandbox.

| Transport | Connection result | Status | Content type | Bytes | Redirects | Server | Allow | WWW-Authenticate |
|---|---|---:|---|---:|---:|---|---|---|
| Python requests, hostname | HTTP response | 404 | `text/javascript` | 0 | 0 | `nginx` | absent | absent |
| Python requests, IP with Host | HTTP response | 404 | `text/javascript` | 0 | 0 | `nginx` | absent | absent |
| Python aiohttp, hostname | HTTP response | 404 | `text/javascript` | 0 | 0 | `nginx` | absent | absent |
| Python aiohttp, IP with Host | HTTP response | 404 | `text/javascript` | 0 | 0 | `nginx` | absent | absent |
| `curl` | HTTP response | 404 | `text/javascript` | 0 | not retained | `nginx` | absent | absent |
| Raw TCP, hostname | TCP connected, no HTTP response before read timeout | — | — | — | — | — | — | — |
| Raw TCP, IP with Host | TCP connected, no HTTP response before read timeout | — | — | — | — | — | — | — |
| HTTPS requests | TLS/HTTP not completed before timeout | — | — | — | — | — | — | — |
| PowerShell `Invoke-WebRequest` | Not run in sandbox | — | — | — | — | — | — | — |

The raw TCP discrepancy is recorded explicitly. It shows that a TCP socket can be opened from the sandbox but does not receive the HTTP response that requests, aiohttp, and curl receive. It is not a justification to modify MAG protocol semantics; it indicates that the transport path or HTTP handling must be compared using the actual Windows tools.

## Production transport audit

The production connection uses an `aiohttp.ClientSession` with an `aiohttp.ClientTimeout(total=30)` default, an `aiohttp.TCPConnector`, profile-owned request paths and headers, and bounded retry behavior for normal authenticated operations. Discovery probes use the session directly, read only the response body needed for safe classification, and do not retry or retain raw bodies. The Windows timeout occurred before a response was available, so the parser, token gate, profile state machine, and catalogue code were not implicated by this evidence.

The current discovery loop attempts the fixed candidates sequentially. A transport failure therefore repeats the same unreachable destination for each candidate. No fail-fast production change was made because the required Windows cross-client comparison is not yet complete and such a change would improve latency only; it would not make the portal reachable.

## External-source comparison

The user-specified `Abanoub20130019/IPTV-MAC-address-APP` repository was inspected at shallow clone commit `a09b5096386b3b7030266c487f4e9fcc889c73f8`. Its `stalker_raw.py` uses the older helper-style `/stalker_portal/server/load.php` route, QtEmbedded MAG headers, helper Referer and model headers, and helper-style account/genre/ordered-list/create-link calls. It also generates serial/device identities when absent and retries a 404 with random token/prehash values. Those latter behaviors are explicitly excluded by the SamoTech task constraints and were not copied or executed. [1]

The user-specified `Ftvubuctxrzyfif/mac-stalker-iptv-player` repository was inspected at shallow clone commit `2cd935d2b92163d9d7d91faf5687aa01cf9288bc`. The inspected API file is an M3U/database playlist importer and contains no concrete MAG handshake, bearer-token, or portal-routing implementation. [2]

The supplied concrete portal.php client contract remains the direct source for the dedicated SamoTech profile: origin `/portal.php`, browser request headers, MAC Authorization and raw MAC cookie before the token, Bearer Authorization after a token, account info on portal.php, genres on server/load.php, channels on portal.php, and direct `cmds[].url` handling. The latest Windows run did not reach a point where any of those HTTP request details could be compared against a real server response.

## Required Windows diagnostic

The repository now contains two standalone diagnostic helpers outside the production MAG provider:

- `tools/mag_transport_probe.py` runs requests, aiohttp, curl, raw TCP, hostname/IP Host-preservation, and bounded HTTPS checks where available.
- `tools/mag_transport_probe.ps1` runs Windows `Invoke-WebRequest`, WinHTTP, raw TCP, and records curl availability without printing response bodies or credentials.

Run the PowerShell helper on the same Windows machine and network as the application with the authorized values supplied through environment variables. Redact the hostname, address, MAC, cookies, and command line before sharing the output. The raw TCP, PowerShell, and WinHTTP portions of that Windows comparison are now complete and all fail before HTTP. The only remaining client check is to execute curl.exe separately without printing its command line or response body. If curl also times out, fix route/firewall/ISP/proxy/reachability before changing MAG protocol code. If curl receives HTTP 404, the 404 routing result is reproducible from Windows and protocol investigation can continue. If curl receives JSON/token while the application receives no response, then the aiohttp/qasync transport path becomes the focused engineering target.

## Current root cause and blocker

The latest Windows evidence establishes **network/TCP failure as the first failing layer for that run**. It does not establish the portal’s authorization policy or disprove the new handshake profile, because no HTTP request reached the server. The historical 404 result remains a separate HTTP-layer observation from a different successful transport path.

The blocker is therefore **Windows-to-portal reachability or transport-path inconsistency**, followed by the unresolved real HTTP handshake. Until the Windows matrix proves an HTTP response from the same machine, no further MAG endpoint, token, model, serial, device-ID, prehash, or authentication-state changes are justified.

## References

[1]: https://github.com/Abanoub20130019/IPTV-MAC-address-APP "Abanoub20130019 IPTV-MAC-address-APP"
[2]: https://github.com/Ftvubuctxrzyfif/mac-stalker-iptv-player "Ftvubuctxrzyfif mac-stalker-iptv-player"
[3]: https://github.com/SamoTech/samotech-iptv-player/blob/main/providers/mag/connection.py "SamoTech MAG connection implementation"
