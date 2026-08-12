# Pull Request Exception Template

> **Normal workflow:** This repository develops directly on `main`. Do not open a pull request unless a maintainer has explicitly requested an exception. The standard workflow is documented in [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Summary

Briefly explain the approved exception and the change.

## Related issue or approval

Link the issue, maintainer instruction, or other explicit reason a pull request was requested.

## Change type

- [ ] Bug fix
- [ ] Feature
- [ ] Refactor
- [ ] Documentation
- [ ] CI/CD

## Required checklist

- [ ] Tests added or updated where behavior changed.
- [ ] `black --check src tests` passes.
- [ ] `ruff check src tests` passes.
- [ ] `mypy src` passes.
- [ ] `pytest -q` passes.
- [ ] `git diff --check` passes.
- [ ] Documentation and current support claims were updated where applicable.
- [ ] No credentials, MAC identifiers, tokens, sensitive URLs, or generated local artifacts are included.
