# Roadmap

## Current project status

The repository scaffold and the core recovery are complete. The recovered core is installable, has a single configuration boundary, uses domain-oriented provider ports, includes a tested MAG/Stalker adapter, and passes the configured test, type, and lint checks.

> **Current phase:** Phase 2 — Domain completion and M3U parsing.  
> **Completed milestone:** Core recovery and MAG provider integration.  
> **Next product milestone:** A tested M3U parser and complete domain/value-object coverage.

| Phase | Scope | Status |
|---:|---|---|
| **Recovery** | Packaging repair; configuration composition; canonical provider ports; MAG adapter/credential/session ownership; integration coverage; strict quality gate; truthful documentation | **Completed** |
| **1** | Repository scaffold, baseline architecture, CI configuration, module placeholders | **Completed** |
| **2** | Complete domain entities and value objects; M3U parser; parser and domain unit tests | **Current** |
| **3** | VLC/player adapter, SQLite repositories, dependency-injection composition root, and basic window | Planned |
| **4** | Channel browser UI, search, favorites, and watch history | Planned |
| **5** | Xtream Codes and Stalker provider clients; playlist manager UI | Partially advanced by the recovered MAG/Stalker core; application integration remains planned |
| **6** | XMLTV EPG parser and EPG grid view | Planned |
| **7** | Stream recording through the player adapter and recording UI | Planned |
| **8** | Plugin SDK, example provider plugin, and plugin loader | Planned |
| **9** | Theme engine, dark/light styles, and settings UI | Planned |
| **10** | Auto-updater, crash reporting, picture-in-picture, subtitle/audio management | Planned |
| **11** | Performance pass, memory profiling, and large-playlist stress testing | Planned |
| **12** | PyInstaller packaging, Windows installer, and release automation | Planned |

## Ordering rationale

The project will not start desktop UI work until the domain, application ports, provider adapters, and persistence/player composition have stable contracts. Phase 2 therefore focuses on deterministic parsing and domain behavior; it is the appropriate next increment after the core-recovery milestone.

Each phase must add or update focused tests and pass the full quality gate before it is marked complete.
