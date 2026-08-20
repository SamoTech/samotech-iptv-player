# Playback Backend Decision — Wave 3

**Decision:** Retain **one shared `VlcPlayerAdapter` backed by libVLC** as the only production media engine.

## Decision Inputs

The existing application already uses a provider-neutral resolved-playback boundary, serializes lifecycle operations through `PlayerPort`, owns Qt native video output in the presentation layer, provides typed playback state, implements bounded live recovery, and has Windows packaged-VLC validation. A second engine, alternate process, custom decoder, Flutter/media-kit path, browser engine, or UI-owned VLC control would duplicate lifecycle/recovery ownership and violate the supplied architecture restrictions.

| Candidate | Decision | Evidence boundary |
|---|---|---|
| Existing libVLC backend | **Selected** | Current source, deterministic adapter tests, and Windows package/smoke evidence |
| Custom Python media stack | Rejected | No existing lifecycle/codec/runtime evidence; would violate scope |
| Flutter/media_kit | Rejected | Repository is Python/PySide6; no Flutter target or code path |
| Web HLS player / hls.js | Rejected | No browser target; would add a second app/media architecture |
| MPV / external VLC process | Rejected | Competing backend and process-control model; no accepted evidence |
| FFmpeg transcode/proxy | Rejected | Adds prohibited backend/proxy scope and does not solve provider authorization evidence |

## Contract

The backend contract remains:

```text
Provider resolver → PlaybackResource → ResolvedPlayback → PlayerPort → VlcPlayerAdapter → libVLC → Qt native surface
```

The UI must request application use cases and render typed state. It must not construct stream URLs, directly invoke libVLC, infer headers/cookies, or create a parallel recovery/session owner.

## Acceptance Boundary

This decision is architectural, not a universal codec or provider claim. Each transport/container/codec combination requires independent evidence before it is marked verified. The backend remains eligible for controlled runtime probing through the existing adapter and local harness only.

## References

[1]: `WAVE3_REPOSITORY_FORENSIC.md` — Wave 3 forensic baseline.  
[2]: `docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md` — current provider-to-player and libVLC contract.  
[3]: `src/samotech_iptv/application/ports/player_port.py` — player interface.  
[4]: `src/samotech_iptv/infrastructure/player/vlc_player_adapter.py` — sole backend implementation.
