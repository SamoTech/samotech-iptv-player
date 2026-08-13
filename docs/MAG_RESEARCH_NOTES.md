# MAG Protocol Research Notes

## Official and secondary evidence

Infomir's Stalker Middleware 4.8 changelog documents middleware-version-specific behavior and fixes, including handshake/access-token behavior, authorization, loading, and playback changes. It supports treating firmware and middleware compatibility as version-sensitive rather than universal.

Secondary open-source Stalker clients commonly construct a request to `/server/load.php` with `type=stb`, `action=handshake`, an empty `token`, and `JsHttpRequest=1-xml`, together with MAG-style User-Agent, X-User-Agent, Referer, and device identity headers. This is reverse-engineered implementation behavior, not an official universal specification.

## Repository comparison

The installed legacy client currently requests `/server/load.php` relative to the configured portal base, uses the MAG200 stbapp User-Agent, sends X-User-Mac and optional device headers, and expects JSON containing `js.token` or a top-level token, with optional `js.token_TTL`. The real supplied portal returned HTTP 404 for the configured `/c/server/load.php` application path and HTTP 200 with an empty `text/javascript` body for the root `/server/load.php` variant. Standard query/header variants tested against the portal did not return a JSON session token.

## Design consequence

The compatibility lab will model both a legacy bare handshake and a newer query-parameter handshake as deterministic fixture profiles. It will not silently select a new production profile or alter the real portal behavior without stronger evidence. The fixture lab will exercise the existing MAG provider through its real HTTP connection, session parser, catalogue translator, stream resolver, and application adapter boundary.

## References

1. https://wiki.infomir.eu/eng/ministra-tv-platform/changelog/stalker-middleware-4-8 — Infomir Stalker Middleware 4.8 changelog.
2. https://github.com/Cyogenus/IPTV-MAC-STALKER-PLAYER-BY-MY-1/blob/main/stalker.py — secondary open-source Stalker client reference.
3. https://github.com/Jitendraunatti/Stalker-Portal/blob/main/config.php — secondary open-source portal implementation reference.
