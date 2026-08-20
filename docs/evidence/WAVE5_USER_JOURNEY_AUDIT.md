# Wave 5 User-Journey Audit

## Method

The audit followed the requested first-run route using the current source, deterministic native PlayerShell probe, dialog contracts, prior large-data evidence, and packaged Windows evidence. It deliberately does not treat a unit-test double, parsed playlist, or packaged startup as proof of commercial-provider playback.

## Findings

| Journey area | Evidence-based result | Severity | Decision |
|---|---|---:|---|
| Launch and onboarding | Home page directs a new user to manage providers and does not fabricate available media before a provider is selected. | None | Preserve. |
| Add source | M3U accepts local file/URL; Xtream uses server/username/masked password; MAG retains only implemented portal/device inputs; Smart Import is protocol-specific. | None | Preserve. |
| Live/VOD/series loading | Explicit load actions, local category/filter/sort behavior, stale-request protection, and loading-state button disablement are present. | None | Preserve. |
| Empty states | Home, live, search, content, library, artwork, and provider states are generally actionable. | P2 | Improve only legacy Favorites/History/EPG dialogs where raw opaque identifiers or generic prompts create avoidable friction. |
| Playback errors | `PlayerShell` distinguishes loading, buffering, recovery, stopped, ended, and generic playback error, but a failed playback has no direct retry action. | **P1** | Add a disabled-until-needed Retry control that reuses the existing typed playback target path. |
| Playback controls | Live seeking/restart is disabled; movie/episode seek, resume persistence, episode navigation, audio, subtitles, aspect ratio, volume, mute, fullscreen, and diagnostics are context-aware. | None | Preserve. |
| Fullscreen/focus | Qt toggling, Escape exit, `F`, mouse-overlay visibility, and stateful fullscreen label are implemented. Taskbar, multi-monitor, and restoration behavior require Windows/user validation. | Requires Windows validation | Do not claim more. |
| Keyboard | Space, `F`, `M`, seek keys, Enter, and list arrows are supported without intercepting focused line edits/combo boxes. | None | Preserve. |
| Search | Uses case-folded local search and current loaded content. No network request occurs for global filtering. Existing 10k probe covers responsive local rendering. | None | Preserve. |
| EPG | The legacy EPG dialog asks normal users to type provider/channel IDs and has broad `Unable to load EPG` copy. | **P1** | Use the active shell selection as safe context and provide actionable no-selection/error messaging. |
| Favorites | The legacy Favorites dialog renders opaque record/provider/item IDs and asks for a manually typed favorite ID to remove an item. | P2 | Render user-oriented safe summaries and remove the selected stored record without exposing internal IDs. |
| History | The legacy History dialog renders raw database-like IDs and ISO data as its primary text. | P2 | Render safe type/progress/completion/watch-time summaries, never opaque identifiers. |
| Settings | Only theme is configurable. General, Playback, Network, Diagnostics, and Privacy are explanatory sections and explicitly avoid fake switches. | None | Preserve. |
| Diagnostics | The report is allow-listed/redacted, marks missing values `NOT_AVAILABLE`, and does not retain secrets. Copy is supported; closing is the correct non-persistent clear operation. | None | Preserve. |
| Debug launcher | Existing v0.1.6 Windows workflow and release acceptance verify arbitrary CWD, spaces, PATH variants, packaged EXE resolution, clean exit, and safe output. | None | Preserve. |
| Provider/media boundary | PlayerShell and VLC adapter consume typed playback contracts; no provider protocol code is present in them. | None | Preserve. |
| Capability truth | Provider capabilities use explicit truth states; player controls do not claim codec/container success in advance of runtime evidence. | None | Preserve. |

## Implementation Scope

The audit justifies one P1 playback recovery affordance, one P1 EPG context/error improvement, and two contained P2 legacy-library usability improvements. It does not justify a new backend, provider protocol work, codec support claim, broad UI redesign, proxy, unbounded search rewrite, installer, or release.
