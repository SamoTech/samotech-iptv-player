# Playback Protocol Matrix — Wave 3

**Rule:** A protocol/container/codec is not marked verified merely because an adapter can create a URL or libVLC advertises general support.

| Transport / source | Container / manifest | Current executable boundary | Codec / audio evidence | State | Required evidence before promotion |
|---|---|---|---|---|---|
| HTTP(S) M3U channel | Unknown until input open | `ResolvedPlayback(URL)` to libVLC | Unprobed | DOCUMENTED | Sanitized open, decoded-frame, and audio-init proof |
| HTTP(S) HLS | `.m3u8`, segment format unknown | libVLC URL handoff | H.264/H.265/AAC/subtitles unprobed | NOT_VERIFIED | Manifest fetch, media segment read, decoded video frame, audio initialization |
| HTTP(S) MPEG-TS | `.ts` | libVLC URL handoff | Codec/audio unprobed | NOT_VERIFIED | Demux/frame/audio runtime evidence |
| HTTP(S) MP4/fMP4 | `.mp4`/fragmented media possible | libVLC URL handoff | Codec/audio unprobed | NOT_VERIFIED | Container/decode/audio runtime evidence |
| Xtream live/VOD/series | Provider extension | URL-shaped handoff after control-plane resolution | Extension is not codec evidence | NOT_VERIFIED | Authorized provider, sanitized full-chain evidence |
| MAG create_link | Portal-returned HTTP(S) URL | URL boundary narrows to HTTP(S) | Portal session/media headers unproven | BLOCKED_EXTERNAL | Authorized portal trace plus safe metadata evidence |
| RTSP/RTMP/RTP/UDP/SRT | Any | URI may be classified below the player boundary | Not executable at current `URL` contract | UNSUPPORTED | Explicit typed transport contract and controlled platform acceptance |

## Runtime Telemetry Contract

Future runtime probes may record only safe metadata: transport family, manifest/container classification when reliably observable, bounded backend event sequence, player state, media generation, relative timing, whether a decoded frame/audio initialization was observed, and bounded non-sensitive error class. They must not record credentials, tokenized URLs, raw headers, cookies, authorization values, provider payloads, or artwork URLs.

## References

[1]: `docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md` — existing HTTP(S) handoff and transport limitations.  
[2]: `docs/evidence/WAVE3_CAPABILITY_MATRIX.md` — consolidated provider/platform evidence levels.  
[3]: `src/samotech_iptv/application/dtos/playback.py` — resolved-playback and ephemeral transport metadata.
