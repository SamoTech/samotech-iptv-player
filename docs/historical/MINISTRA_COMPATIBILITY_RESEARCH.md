# Ministra Compatibility Research Notes — Historical Evidence

> **Historical scope:** These notes informed the 2026-08-11 Ministra assessment and do not indicate an implemented client. Ministra remains **Planned** pending an authorized sanitized portal fixture and approved device identity. See [PROJECT_STATUS.md](../../PROJECT_STATUS.md) and [MINISTRA_COMPATIBILITY_ASSESSMENT.md](MINISTRA_COMPATIBILITY_ASSESSMENT.md).


## Official platform framing

Infomir documents that **Stalker Middleware was renamed to the Ministra TV platform**. The platform documentation still links changelogs under both names, so compatibility must treat historical Stalker and Ministra deployments as a related but version-variable platform family rather than assuming a single, stable client protocol.[1]

## Administrative REST API is not the player API

The official REST API v1 documentation describes an **administrative** REST surface. It supports Basic HTTP authentication and resources for STB/account management, messages/events, IPTV channel administration, subscriptions, tariffs, and service packages.[2] This API is not a safe substitute for a subscriber playback integration because it manages portal resources and can change account/device state.

The documented STB and account resources are MAC-address aware, and the account fields include `stb_mac`, `stb_sn`, and `stb_type`.[2] Device identity is therefore an architecture-level input for a Ministra client—not merely a credential string.

## Device-facing compatibility risks

The official changelog records repeated changes in device authorization, access-token handling, authorization keys, temporary playback URLs, EPG/archive behavior, secure-link support, and strict STB type checks.[3] This supports isolating the device-facing portal protocol behind a **separate Ministra provider** instead of treating it as interchangeable with Xtream's credential URL construction.

Public client integrations commonly describe a device-facing sequence of portal-specific handshake, token acquisition, profile loading, catalogue/EPG retrieval, and temporary playback-link resolution. These sources are implementation references only; production support must be validated against an authorized test portal and must not depend on administration credentials.[4]

## Sources

[1] [Infomir — Ministra TV platform](https://wiki.infomir.eu/eng/ministra-tv-platform)

[2] [Infomir — REST API v1](https://wiki.infomir.eu/eng/ministra-tv-platform/ministra-setup-guide/rest-api-v1)

[3] [Infomir — Stalker Middleware 4.8 changelog](https://wiki.infomir.eu/eng/ministra-tv-platform/changelog/stalker-middleware-4-8)

[4] [Stalker provider implementation reference](https://github.com/DimitarCC/iptv-m3u-reader/blob/main/src/StalkerProvider.py)
