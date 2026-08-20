# Wave 3 Capability Matrix

**Purpose:** Record the current evidence boundary before Wave 3 implementation.  
**Classification rule:** `VERIFIED` requires evidence at the stated boundary; `DOCUMENTED` describes implementation/source documentation only; `NOT_VERIFIED` has no qualifying runtime evidence; `UNSUPPORTED` is outside the executable contract; `BLOCKED_EXTERNAL` requires an authorized provider or platform unavailable to this task.

| Provider/source | Media protocol / container | Video / audio / subtitles | Backend | Platform | Evidence level | Status | Evidence and limitation |
|---|---|---|---|---|---:|---|---|
| M3U local/remote | Playlist parse only | Metadata only | Parser | Linux/Windows source path | 1 | VERIFIED | Bounded source loading/parsing tests; this is not decoded media. |
| M3U | HTTP(S) handoff | Extension or metadata hints only | libVLC | Windows package / local source | 3 | DOCUMENTED | HTTP(S) `ResolvedPlayback` reaches the backend; no current per-stream decoded-frame evidence. |
| M3U HLS | `.m3u8`; segment/container unknown until backend probes | Codec/audio/subtitle unknown | libVLC | Windows | 3 | DOCUMENTED | Existing architecture delegates HLS to libVLC; manifest parse is not playback evidence. A controlled Linux public-fixture probe was blocked before open because no libVLC runtime exists. |
| M3U MPEG-TS | HTTP(S) TS possible | Codec/audio unknown | libVLC | Windows | 3 | DOCUMENTED | No Wave 3 decoded-frame/audio evidence. |
| M3U RTSP/RTP/UDP/SRT/RTMP | Classifiable URI schemes | Unknown | None at executable boundary | All | 0 | UNSUPPORTED | Current provider-to-player `URL` accepts HTTP(S) only. |
| Xtream | Control API / `player_api.php` | N/A | Xtream adapter | Local/Windows | 2 | VERIFIED | Deterministic API, translation, resolution, and subpath regression coverage. |
| Xtream Live | HTTP(S) `/live/...` URL handoff | Provider extension only; codec/audio unprobed | libVLC | Windows | 3 | DOCUMENTED | URL path construction exists; real authorization/provider playback remains blocked. |
| Xtream VOD / episode | HTTP(S) `/movie` or `/series` URL handoff | Provider extension only; codec/audio unprobed | libVLC | Windows | 3 | DOCUMENTED | Deterministic resolution and player lifecycle tests only. |
| MAG/Stalker | Handshake/session/categories/EPG/`create_link` | N/A | MAG adapter | Local | 2 | VERIFIED | Controlled protocol/profile/session tests. |
| MAG Live | HTTP(S) handoff after `create_link` | Unknown; portal headers/cookies may be required | libVLC | Windows | 2 | BLOCKED_EXTERNAL | No authorized portal/media-session trace demonstrates media-plane continuity. |
| MAG VOD / Series / catch-up | Provider-specific | Unknown | None advertised | All | 0 | UNSUPPORTED | Existing capability boundary intentionally does not claim these modes. |
| HTTP(S) generic stream | Backend open | Container/codec backend-owned | libVLC | Windows package | 3 | VERIFIED | Windows portable workflow verifies native VLC lifecycle, packaged media surface/smoke, and lifecycle package gates; it is not provider-specific playback evidence. |
| HLS master/media playlist | HLS/fMP4 or TS segments possible | Unknown until decoder opens | libVLC | Windows | 3 | NOT_VERIFIED | No documented Level 4 frame and Level 5 audio evidence in current Wave 3 inventory. |
| MPEG-TS | TS demux possible | H.264/H.265/MPEG-2/AAC/etc. not independently detected | libVLC | Windows | 3 | NOT_VERIFIED | No sanitized decoded-frame/PAT/PMT/audio-init evidence. |
| MP4/fMP4 | Progressive/fragmented possible | Codec/audio unknown | libVLC | Windows | 3 | NOT_VERIFIED | URL extension is not accepted as codec/playback proof. |
| Audio tracks | Native enumeration/selection | Descriptions only | libVLC | Linux/Windows contract | 1 | VERIFIED | Adapter unit tests demonstrate typed track contract; no real audio initialization claim. |
| Subtitle tracks | Native enumeration/selection; SRT/ASS/SSA/VTT local attachment | Native or local subtitle | libVLC | Linux/Windows contract | 1 | VERIFIED | Contract and focused regression evidence; real multiplexed-subtitle acceptance not established. |
| Buffering/liveness/recovery | Native events and media-time heartbeat | N/A | libVLC | Contract / Windows package | 1 | VERIFIED | Deterministic bounded recovery, typed live-stall, and non-live END tests. |
| Channel switching | Generation/session-scoped stop/open/play | N/A | libVLC | Contract / Windows package | 1 | VERIFIED | Deterministic stale-generation and switching lifecycle coverage. |
| VOD / series controls | Play/seek/resume/history/episode navigation | N/A | libVLC | Contract | 1 | VERIFIED | Deterministic application/UI contract evidence only. |
| EPG | Xtream/MAG/XMLTV canonical data | N/A | UI/catalogue | Local | 1 | VERIFIED | Parser/DTO/presentation coverage; remote provider load remains source-specific. |
| Catch-up | Archive/timeshift | N/A | None | All | 0 | UNSUPPORTED | No explicit provider capability and no provider-neutral archive contract. |
| Diagnostics | Safe player state/liveness/recovery identifiers | No media codec/frame metrics | libVLC | Contract | 1 | VERIFIED | Safe diagnostics exist; full Wave 3 media diagnostics are incomplete. |
| Windows | Packaged EXE / native VLC lifecycle | No real authorized provider content | libVLC package | Windows | 3 | VERIFIED | Workflow run 32330586667 passed build, package, lifecycle, smoke, sanitized PATH, and artifact gates. |
| Linux | Offscreen Qt / deterministic player probe | Native provider playback unavailable | libVLC contract | Linux | 1 | VERIFIED | Deterministic/offscreen evidence; not native stream acceptance. |
| macOS / Android / iOS / Web | Not present in this repository | N/A | N/A | Respective platform | 0 | NOT_VERIFIED | No source, build, or runtime target in the current project. |

## Evidence Boundaries

No row above promotes a parsed manifest, stream URL, backend opening, test double, or package smoke result to decoded-frame, audio-initialization, sustained-playback, or real-provider evidence. Real provider acceptance remains dependent on a valid authorized source and sanitized runtime capture.

## References

[1]: `WAVE3_REPOSITORY_FORENSIC.md` — Wave 3 baseline and missing-evidence inventory.  
[2]: `docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md` — provider/media architecture and boundaries.  
[3]: `PHASE25_REAL_PROVIDER_PLAYBACK_AUDIT.md` and `PHASE26_REAL_PLAYBACK_ACCEPTANCE_HARNESS.md` — provider and controlled-harness evidence limits.  
[4]: [Windows Portable EXE workflow run 32330586667](https://github.com/SamoTech/samotech-iptv-player/actions/runs/32330586667) — package/lifecycle/smoke validation.
[5]: `docs/evidence/WAVE3_RUNTIME_PROBE_LOG.md` — controlled public-fixture runtime blocker.
