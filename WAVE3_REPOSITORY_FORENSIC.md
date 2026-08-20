# Wave 3 Repository Forensic Audit

**Specification reviewed:** `pasted_content.txt`, Wave 3 Full IPTV Media Player Engine  
**Repository baseline:** `452e03a0ccfd2e5a93145b4a4495180274eb3d5f` (`HEAD == origin/main` before this forensic artifact)  
**Application version:** `0.1.5`  
**Latest existing tag:** `v0.1.5`  
**Forensic disposition:** **No implementation change made in this phase.**

## 1. Repository State

The repository is a Python/PySide6 desktop application, not a Flutter or web application. Its current media engine is a single `python-vlc` / libVLC backend. The pre-existing worktree was clean before the Wave 3 checklist artifact was created; this audit adds documentation and planning artifacts only.

The version, tags, release state, README badge block, GitHub Actions configuration, and existing published `v0.1.5` release are protected boundaries for this work. No release, tag, version increment, badge edit, asset replacement, or CI-permission change is authorized by the specification.

## 2. Actual Playback Architecture

The source repository supports the following verified dependency direction:

```text
M3U / Xtream / MAG provider adapter
  → provider-resolution and capability interfaces
  → PlaybackResource
  → ResolvedPlayback (ephemeral URL + transport metadata)
  → PlayerPort
  → VlcPlayerAdapter
  → libVLC Media / MediaPlayer
  → Qt-owned native video surface
```

`PlaybackResource` is a non-URL logical identity. `ResolvedPlayback` carries the final URL and optional ephemeral transport metadata. `PlayerPort` is the current backend contract, and `VlcPlayerAdapter` is the sole production backend. The player uses one libVLC instance/player lifecycle, media generation tokens, typed public state, bounded recovery, and a native Qt video surface. This already matches the specification’s requirement to preserve lifecycle control and avoid direct UI-to-VLC calls.

The repository does **not** contain production `media_kit`, Flutter, hls.js/MSE, MPV, multi-engine selection, `BackendSelector`, `CapabilityResolver`, or a named `PlaybackSession` implementation. The closest current equivalents are provider-resolution capability interfaces, `PlaybackStateMachine`, `PlayerPort`, `VlcPlayerAdapter`, and the composition helper. Introducing a second playback architecture would violate the supplied non-negotiable architecture rule.

## 3. Provider, Account, and Catalogue Baseline

| Area | Current repository state | Evidence classification |
|---|---|---|
| M3U/M3U8 | Local/file/HTTP(S) source loading, bounded parsing, channel catalogue, HTTP(S) stream handoff | Implemented at deterministic boundary |
| Xtream | Authentication/control API, account/server data, live/VOD/series/categories/details/short EPG, URL-based resolution | Partially implemented; real provider acceptance blocked historically |
| MAG/Stalker | Profile/session/handshake/live/categories/EPG/search/`create_link` control plane | Partially implemented and provider-specific |
| Account information | Typed `AccountInfo` includes status, expiration datetime, connections, and safe message | Partially implemented; no full Wave 3 expiration domain model |
| Provider capabilities | Explicit feature enum and capability-gated resolution | Implemented at declared boundary; no four-state evidence model yet |
| VOD / Series | Existing Xtream movie and episode resolution/playback paths | Deterministically tested; real provider acceptance not established |
| EPG | Existing Xtream/MAG/XMLTV parsing and presentation paths | Deterministic/local evidence only |
| Catch-up | Capability vocabulary exists; no advertised/executable implementation | Not implemented by design |

## 4. Media and Runtime Baseline

`VlcPlayerAdapter` exposes play, stop, restart, position/duration, absolute/fractional seek, volume, mute, audio-track enumeration/selection, subtitle-track enumeration/selection, local subtitles, subtitle delay, aspect ratio, recording, native video attachment, and typed player state. It subscribes to libVLC events where available and uses generation/session-scoped bounded recovery for live EOF, stopped, error, buffering timeout, start timeout, and liveness stalls.

The present runtime contract remains HTTP(S)-executable at the provider-to-player boundary. The domain can classify additional schemes, but the URL value object and `ResolvedPlayback` handoff do not claim RTSP, RTP, UDP, SRT, RTMP, or RTMPS playback. The repository also does not independently demux, decode, or probe codecs; libVLC owns that work. URL extension, successful HTTP response, manifest parsing, backend start, and real decoded frames remain distinct evidence levels.

## 5. Existing Evidence and Historic Reports

The current repository already contains substantial reports and tests, including Player 3 architecture/runtime/real-provider documentation, protocol/playback architecture, the VLC remediation audit, Phase 24 UI/UX audit, Phase 25 provider validation audit, and Phase 26 local real-playback harness audit.

The requested exact Wave 3 document names `PLAYBACK_BACKEND_DECISION.md`, `PLAYBACK_PROTOCOL_MATRIX.md`, a feature parity matrix, migration status, AI team status, and evidence manifest were not present at the requested paths. Existing equivalent/adjacent evidence is `docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md`, `docs/PLAYER_3_ARCHITECTURE.md`, `docs/PLAYER_3_RUNTIME_VALIDATION.md`, `docs/PLAYER_3_REAL_PROVIDER_ACCEPTANCE.md`, and the historic audits. Wave 3 must add its own distinct evidence artifacts rather than relabeling historical files.

## 6. Critical Gaps Before a Wave 3 Acceptance Claim

| Required Wave 3 item | Current disposition |
|---|---|
| Capability matrix with evidence-level statuses | Missing as a dedicated Wave 3 artifact |
| Typed subscription/expiration domain beyond `expires_at` | Partial; missing status, timezone, remaining-time semantics |
| Four-state provider-capability truth model | Missing; current enum is feature-only |
| Backend decision record and codec registry | Missing as dedicated evidence artifacts |
| Runtime diagnostics for container/codec/frames/audio initialization | Partial; no evidence of all required runtime fields |
| Actual HLS/MPEG-TS/MP4 decoded frame and audio proof | Not established in current forensic evidence |
| Real authorized IPTV provider full-chain acceptance | Blocked by prior provider/WAF evidence; no new authorized source supplied |
| Platform matrix beyond Windows build evidence / local Linux probes | Not verified across all requested platforms |
| Catch-up/archive | Not implemented; no explicit provider capability evidence |

## 7. Architectural Decision for the Next Phase

The smallest mature architecture already present is **the existing shared libVLC backend**. Wave 3 should extend its typed evidence, account/capability models, diagnostics, and controlled runtime harnesses through the existing `PlaybackResource → ResolvedPlayback → PlayerPort → VlcPlayerAdapter` route. It must not add an unproven alternate media engine, custom codec pipeline, browser engine, direct VLC calls from UI code, proxy, or competing recovery mechanism.

## 8. Forensic Conclusion

The repository is already a lifecycle-controlled desktop media-player architecture at contract and deterministic-test boundaries, not merely a URL launcher. It is not yet evidence-qualified as a **full Wave 3 media player** because decoded-video, audio-initialization, sustained-playback, and real authorized-provider evidence are absent or historically blocked. The next action is therefore to build a conservative evidence matrix and gap map before considering any implementation change.

## References

[1]: `src/samotech_iptv/application/dtos/playback.py` — playback resource and resolved-playback boundary.  
[2]: `src/samotech_iptv/application/ports/player_port.py` — sole player contract.  
[3]: `src/samotech_iptv/infrastructure/player/vlc_player_adapter.py` — shared libVLC backend, lifecycle, recovery, and native output.  
[4]: `docs/PROTOCOL_PLAYBACK_ARCHITECTURE.md` — current provider/media architecture and known limitations.  
[5]: `PLAYER_3_FINAL_AUDIT.md` — historical implementation and evidence limitations.  
[6]: `PHASE25_REAL_PROVIDER_PLAYBACK_AUDIT.md` and `PHASE26_REAL_PLAYBACK_ACCEPTANCE_HARNESS.md` — prior authorized-provider and local-harness evidence boundaries.
