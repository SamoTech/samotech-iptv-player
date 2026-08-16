# Player 3 Reference Findings

## Sources consulted

1. [EStalker GitHub repository](https://github.com/kiddac/EStalker) — public repository describing an Enigma2 Ministra/Stalker IPTV player. The repository presents provider-specific catalogue, account, and playback workflow code, but its Enigma2 architecture is not SamoTech’s architecture.
2. [XStreamity GitHub repository](https://github.com/kiddac/XStreamity) — public README states that it is an Enigma2 plugin for official Xtream Codes playlists and that users supply their own playlist details.
3. [Fermata Xtream API discussion](https://github.com/AndreyPavlenko/Fermata/discussions/434) — public discussion includes examples of `player_api.php` action usage, including `get_series_info`, and community discussion of VOD formats, track metadata, and catch-up uncertainty. It is community material, not an authoritative provider contract.

## Engineering conclusions

The references support high-level patterns only: provider-specific authentication/session handling, catalogue/category navigation, metadata-aware VOD/Series presentation, provider-owned stream resolution, and careful handling of server variation. They do not prove universal MAG/Stalker non-live support, Xtream pagination, catch-up URL formats, audio/subtitle availability, or production compatibility for SamoTech’s providers.

SamoTech will retain its own provider ports, canonical domain records, `PlaybackTarget`/`ResolvedPlayback` handoff, PlayerPort/libVLC boundary, qasync ownership, and security rules. No source code, credentials, branding, UI assets, or implementation text is copied from the reference projects.

The low-level Xtream action surface observed in the current repository is limited to authentication/base info, live/VOD/Series categories and listings, `get_vod_info`, `get_series_info`, `get_short_epg`, and provider-owned stream URL construction. The current repository does not expose server-side pagination, generic non-live search, catch-up resolution, or a dedicated track/catch-up provider capability contract. Those items remain partial, provider-dependent, or blocked unless implementation evidence is added.
