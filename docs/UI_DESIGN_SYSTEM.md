# SamoTech IPTV Player UI Design System

**Status:** Active presentation guidance for the current PySide6 desktop shell.

This design system keeps SamoTech IPTV Player visually coherent without coupling presentation code to provider protocols, credentials, or libVLC internals. It applies to the PlayerShell, MainWindow, dialogs, player overlay, and state messaging. It is intentionally conservative: the current increment does not add a bespoke icon pack or unlicensed artwork.

## Visual hierarchy

| Level | Use | Current token or rule |
|---|---|---|
| Product identity | Brand and application context | `brand` 18px bold; compact eyebrow uses uppercase 10px muted text |
| Page heading | Current workspace title | `pageTitle` 22px bold; hero title 28px emphasized |
| Section label | Navigation and grouping | `sectionKicker`, uppercase, 10px bold with letter spacing |
| Supporting copy | Scope, limitations, and instructions | `pageSubtitle`, 13–14px muted text with word wrap |
| Status | Playback/provider/result feedback | Short, generic text using semantic status colors; never raw URLs, credentials, tokens, or provider payloads |
| Content detail | Selected Movie/Series/Episode metadata | Word-wrapped detail text beside bounded artwork placeholder |

## Spacing and shape

The canonical spacing scale is `xs=4`, `sm=8`, `md=12`, `lg=16`, `xl=24`, and `xxl=32` pixels. New layouts should use these tokens rather than local numeric spacing. Standard radii are `sm=6`, `md=10`, and `lg=14` pixels. Dialogs may set a minimum width when readable form content requires it, but width should remain content-driven rather than fixed unnecessarily.

## Color semantics

| Semantic role | Token | Meaning |
|---|---|---|
| Background | `COLORS.background` | Application canvas |
| Surface | `COLORS.surface` / `surface_elevated` | Panels, cards, dialogs, and controls |
| Primary | `COLORS.primary` / `primary_hover` | Main navigation or commit action |
| Muted | `COLORS.text_muted` | Supporting copy and secondary context |
| Disabled | `COLORS.text_disabled` | Temporarily unavailable actions |
| Success | `COLORS.success` | Confirmed healthy/active state |
| Warning | `COLORS.warning` | Caution or incomplete state |
| Danger | `COLORS.danger` | Destructive action or failure emphasis |
| Video | `COLORS.video` | Native playback viewport |

Color is never the sole carrier of meaning. State text, accessible names, and enabled/disabled behavior accompany semantic color treatment.

## Action hierarchy

Primary actions commit or start the current workflow, such as **Load channels**, **Load movies**, **Open series**, **Save provider**, and **Save Theme**. Secondary actions inspect, filter, navigate, or refresh, such as **Search**, **Categories**, **Check Session Status**, and **Refresh History**. Destructive actions change or remove persisted state and use explicit wording, danger styling where available, and a confirmation boundary in production flows. Cancel/back actions remain text-labelled and should follow the platform’s ordinary focus order.

## Dialog rules

Dialogs state their purpose in the title, keep provider credentials and MAC identities out of summaries, provide a short explanation before sensitive entry, and show generic safe status text after an operation. Form fields must have visible labels or equivalent context. Buttons are individually labelled; any destructive operation must have a clear confirmation step in the real application. Focus order and default-button behavior are part of the acceptance tests, not assumptions.

## Empty, loading, and error states

Every data surface distinguishes no data from an operation in progress and from an operation failure. Empty states explain what the user can do next. Loading states disable only the affected operation and retain a path to recovery. Error states use generic, actionable language and never include raw provider response bodies, private URLs, credentials, MAC addresses, tokens, cookies, or diagnostic dumps.

## Focus and keyboard behavior

Major controls expose accessible names and useful tooltips. List surfaces support selection and Enter/double-click activation where appropriate. Player shortcuts remain limited to evidence-backed behavior (`Space`, `F`, `Escape`, and supported volume/mute handling); no new shortcut is added solely for visual polish. Focus must remain visible through the shared Qt focus styling, and icon-only or compact controls must preserve a tooltip and accessible name.

## Icon strategy

The repository currently contains no bespoke icon family; `resources/icons` is only a placeholder. This increment keeps visible text labels and existing compact sidebar glyphs rather than introducing random symbols or unlicensed assets. If future iconography is needed, use Qt/platform-safe standard icons or a reviewed bundled/licensed family, preserve visible labels for discoverability, and provide a tooltip plus accessible name for every icon-only control.

## Provider and playback honesty

Presentation labels must describe the executable capability exposed by the selected provider. The UI may hide unsupported Movies, Series, EPG, or other pages through capability gating, but it must not turn deterministic fixtures, URL resolution, libVLC startup, or HTTP success into claims of real provider compatibility or decoded playback. Playback state labels reflect typed evidence from the player boundary and do not infer first-frame, audio, subtitle, or codec success without corresponding evidence.
