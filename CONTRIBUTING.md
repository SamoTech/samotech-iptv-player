# Contributing

Thank you for your interest in contributing to SamoTech IPTV Player!

## Setup

```powershell
git clone https://github.com/SamoTech/samotech-iptv-player.git
cd samotech-iptv-player
./scripts/install_dev.ps1
```

## Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes, add tests
4. Run `./scripts/run_tests.ps1` — all tests must pass
5. Run `pre-commit run --all-files`
6. Open a Pull Request against `main`

## Code Style

- **Formatter**: Black (`black src/ tests/`)
- **Linter**: Ruff (`ruff check src/ tests/`)
- **Type checker**: mypy (`mypy src/`)
- All three must pass with zero errors.

## Commit Convention

```
feat: add Xtream Codes authentication
fix: handle empty M3U playlist gracefully
test: add EPG matcher edge cases
docs: update plugin SDK guide
```

## Pull Request Guidelines

- One feature / fix per PR
- Reference the related issue: `Closes #123`
- Include tests for all new code
- Update docs if public API changes

## Issue Reports

Use the GitHub Issue Templates (bug report / feature request).
