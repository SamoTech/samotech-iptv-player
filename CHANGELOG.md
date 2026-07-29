# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial repository scaffold with Clean Architecture skeleton
- Core primitives: `Result[T, E]` monad, typed `EventBus`
- Domain entities: Channel, Playlist, EPGEntry, Recording, Credential, UserProfile
- Domain value objects: `StreamURL`, `MACAddress`, `ChannelID`
- Abstract repository interfaces for all domain aggregates
- CI/CD pipeline (lint + typecheck + test + build)
- Pre-commit hooks (Black, Ruff, mypy)
- Plugin SDK host skeleton
