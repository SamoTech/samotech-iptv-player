# MAG Firmware and Middleware Compatibility

## Status legend

**IMPLEMENTED** means code exists. **TESTED** means deterministic repository tests exercise it. **SIMULATED** means a local fixture exercises the request/response shape. **NOT VERIFIED** means real hardware, Windows, libVLC, or a production portal was not available. **UNSUPPORTED** means the current adapter intentionally does not expose that capability.

## Evidence boundary

Infomir maintains firmware and Stalker Middleware documentation and versioned changelogs. The changelog records version-specific fixes involving authentication, access tokens, loading, and playback; it does not establish that every MAG hardware family uses one identical public handshake. [1]

Open-source clients provide useful secondary evidence for observed request variants, including `type=stb`, `action=handshake`, `token`, `JsHttpRequest`, MAG-style headers, and Referer values. These are reverse-engineered implementation references, not universal official specifications. [2]

## Hardware-family assessment

| Family | Firmware/middleware compatibility | Repository status |
|---|---|---|
| MAG250 / MAG254 | Requires portal-specific and firmware-specific validation. | **NOT VERIFIED** against physical hardware. |
| MAG256 | Requires separate middleware and firmware validation. | **NOT VERIFIED**. |
| MAG322 / MAG324 / MAG325 | Requires separate device identity and portal compatibility evidence. | **NOT VERIFIED**. |
| MAG420 / MAG424 | Requires separate 4K-era firmware and middleware validation. | **NOT VERIFIED**. |
| MAG520 / MAG524 | Requires separate newer firmware/API validation. | **NOT VERIFIED**. |

The compatibility lab deliberately does not infer support for a hardware family from a passing local fixture. A model-specific profile should be added only when an authorized device/portal trace or official provider documentation establishes the request and response contract.

## Current profiles

The `legacy` profile is the default and preserves the existing provider behavior. The `stalker_query` profile is an opt-in simulation of a commonly observed Stalker client request variant. Neither profile is automatically inferred from a portal URL or device identity.

## Real-world acceptance gap

The supplied portal remains **UNRESOLVED**. Real connectivity was verified, but authentication did not produce a JSON token response. A Windows/libVLC run is also required for actual audio/video, H264 fallback, dead-stream recovery, rapid switching, and UI responsiveness.

## References

[1]: https://wiki.infomir.eu/eng/ministra-tv-platform/changelog/stalker-middleware-4-8 "Infomir Stalker Middleware changelog"
[2]: https://github.com/Cyogenus/IPTV-MAC-STALKER-PLAYER-BY-MY-1/blob/main/stalker.py "Secondary open-source Stalker client reference"
