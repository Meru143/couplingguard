# Contributing to couplingguard

Thanks for your interest in improving couplingguard.

## Local development setup

```bash
git clone https://github.com/Meru143/couplingguard.git
cd couplingguard
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
make dev
```

## Running checks

```bash
make lint          # ruff
make type-check    # mypy --strict
make test          # pytest with coverage
make all           # all three
```

Tests must keep coverage at >= 85% and `mypy --strict` must pass.

## Commit messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/).
`python-semantic-release` reads commit messages to decide version bumps:

- `feat:` — new feature (minor bump)
- `fix:` — bug fix (patch bump)
- `docs:` — documentation only
- `chore:` / `refactor:` / `test:` — no version bump
- `BREAKING CHANGE:` in body / `!` after type — major bump

Example:
```
feat: add fail_threshold input to action.yml

Adds a configurable threshold above which the action exits 1, so teams
can enforce a coupling budget in CI without mandatory failure for all repos.
```

## Pull requests

1. Open an issue first for non-trivial features.
2. Branch off `main`.
3. Make sure `make all` passes.
4. Update `CHANGELOG.md` under `## [Unreleased]`.
5. Open the PR — couplingguard will comment on its own PR ;)

## Reporting security issues

See [SECURITY.md](SECURITY.md).
