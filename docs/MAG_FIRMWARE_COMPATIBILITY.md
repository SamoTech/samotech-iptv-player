# MAG Firmware and Middleware Compatibility

## Status legend

**IMPLEMENTED** means code exists. **TESTED** means deterministic repository tests exercise it. **SIMULATED** means a local fixture exercises the request/response shape. **NOT VERIFIED** means the relevant real hardware, portal, or playback boundary has not been exercised successfully. **UNSUPPORTED** means the current adapter intentionally does not expose that capability.

## Evidence boundary

Infomir maintains firmware and Stalker Middleware documentation and versioned changelogs. The changelog records version-specific fixes involving authentication, access tokens, loading, and playback; it does not establish that every MAG hardware family uses one identical public handshake. [1]

Open-source clients provide useful secondary evidence for observed request variants, including `type=stb`, `action=handshake`, `token`, `JsHttpRequest`, MAG-style headers, and Referer values. These are reverse-engineered implementation references, not universal official specifications. [2]

The official Ministra configuration reference documents `/stalker_portal/` as a classic portal base and separately documents administrative/API facilities. It also documents configurable STB model restrictions and authorization modes. Infomir documents login/password authorization that binds an STB MAC after first authorization, authorization-with-key behavior, and `default_stb_status = 0` for closing access to new STBs. These are **OFFICIAL INFOMIR BEHAVIOR**, not evidence that the supplied portal uses any one policy. Its REST API v1 Basic-authentication contract is an operator administration interface, not documented evidence to replace the classic MAG client session protocol. The already tested `/stalker_portal/` family remains the only classic family supported by this official evidence; the middleware-family investigation did not identify another production candidate or a new protocol family. [3] [4] [5]

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

The `legacy` profile preserves the existing provider behavior. The `stalker_query`, `stalker_gui_compatibility`, and `stalker_helper_compatibility` profiles model distinct observed request contracts. The canonical MAG path uses a bounded auto-discovery mode that probes six documented candidate families and selects one only after a structurally valid token-bearing response; it never infers arbitrary paths, authentication modes, model identities, or compatibility from a URL, device identity, or HTTP 200 alone. The optional `mag_model` field is empty unless explicitly configured; model-dependent X-User-Agent is not generated from a profile default. Middleware-family findings and the source-derived local lab are recorded in `docs/MAG_MIDDLEWARE_COMPATIBILITY.md`.

## Real-world acceptance gap

The supplied portal remains **UNRESOLVED**. Real connectivity was verified, but the six-candidate set and one new no-model helper revalidation did not produce a JSON token response. The result is not classified as bad MAC, STB rejection, login-required, or auth-key-required because the portal returned routing/response-boundary data without a machine-readable policy error. A real Windows application run has established that libVLC loads and its plugins are discovered; MAG did not reach stream resolution, so MAG video/audio, recovery, rapid switching, and UI responsiveness remain **NOT VERIFIED**.

## References

[1]: https://wiki.infomir.eu/eng/ministra-tv-platform/changelog/stalker-middleware-4-8 "Infomir Stalker Middleware changelog"
[2]: https://github.com/lloesche/stalker_portal/blob/master/server/load.php "Archived open-source Stalker Portal dispatcher"
[3]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-installation-guide/configuration-file "Infomir Ministra configuration reference"
[4]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-setup-guide/rest-api-v1 "Infomir Ministra REST API v1"
[5]: https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-installation-guide/faq/how-to-organize-the-access-to-the-portal-by-login-and-password "Infomir STB login/password and authorization-key access"


## Secondary client-fingerprint profiles

`stalker_gui_compatibility` and `stalker_helper_compatibility` are **IMPLEMENTED and SIMULATED** from secondary reverse-engineered client references. They use distinct approved endpoint families and do not create firmware or middleware-version support claims. The profiles intentionally exclude fabricated device identities and the helper reference’s unverified 404 random-token/prehash sequence. A real token-bearing handshake remains required to establish compatibility for any particular firmware or portal. The local source-derived middleware laboratory proves only the SamoTech application contract against deterministic local data.
