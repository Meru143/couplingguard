# couplingguard

Detect file coupling risk in pull requests from git co-change history. Zero-config GitHub Action with optional GitLab CI support, CODEOWNERS-aware reviewer suggestions, delta comments on re-push, and a self-hosted trend dashboard.

## Install

```yaml
name: Coupling Guard
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  coupling:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: Meru143/couplingguard@v1
        with:
          github_token: ${{ github.token }}
```

Full documentation is generated in Phase 19.
