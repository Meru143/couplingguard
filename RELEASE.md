# Release checklist

Every release of couplingguard follows this flow. Steps marked **automated**
happen via GitHub Actions; the rest are manual.

## Pre-flight (one-time per environment)

These only need to happen once, ever, on a clean machine or fork:

- [ ] PyPI account exists at https://pypi.org and has 2FA enabled
- [ ] PyPI Trusted Publisher registered at
      https://pypi.org/manage/account/publishing/ — fields:
      - Project name: `couplingguard`
      - Owner: `Meru143`
      - Repository: `couplingguard`
      - Workflow: `release.yml`
      - Environment: `pypi`
- [ ] GitHub repo has the `pypi` environment configured under
      **Settings → Environments → pypi** with:
      - Required reviewer: yourself
      - Deployment branch/tag rule: ref type **Tag**, pattern `v*.*.*`
- [ ] Repo is public (Marketplace requires public)

## Per-release flow

### 1. Prepare

- [ ] Pull main locally and make sure it's clean:
      `git checkout main && git pull && git status`
- [ ] Run the full local quality gate:
      `ruff check src/ tests/ && mypy src/ --strict && pytest`
- [ ] Confirm `[Unreleased]` section in `CHANGELOG.md` lists every shipping
      change (semantic-release writes from commit messages, but this is a
      human-readable mirror)
- [ ] Skim the diff since the previous tag:
      `git log --oneline $(git describe --tags --abbrev=0)..HEAD`

### 2. Smoke-test with a release candidate (optional but recommended)

- [ ] Tag and push the rc:
      ```bash
      git tag v0.X.Y-rc1
      git push origin v0.X.Y-rc1
      ```
- [ ] Watch the **Release** workflow at
      https://github.com/Meru143/couplingguard/actions
- [ ] When the job pauses for review, click **Review deployments → Approve and deploy**
- [ ] Confirm the wheel landed at
      https://pypi.org/project/couplingguard/#history
- [ ] Pip-install the rc into a clean venv and run `couplingguard --help`
      to verify the entry point works
- [ ] Yank the rc from PyPI after the real release ships, if you want a clean
      version list: PyPI project page → Manage → yank release

### 3. Cut the real release

- [ ] Tag and push the release:
      ```bash
      git tag v0.X.Y
      git push origin v0.X.Y
      ```
- [ ] Approve the deployment in the Actions tab
- [ ] **Automated**: workflow builds wheel + sdist, runs semantic-release
      (which writes a GitHub Release + CHANGELOG entry), publishes to PyPI
      via Trusted Publishing OIDC, force-updates the `v1` major-version tag
- [ ] Verify outputs:
      - PyPI: https://pypi.org/project/couplingguard/
      - GitHub Releases: https://github.com/Meru143/couplingguard/releases
      - The `v1` tag now points at the new commit (`git ls-remote --tags origin`)

### 4. Publish to GitHub Marketplace (first release only)

- [ ] Open the new release page on GitHub
- [ ] Click **Publish this Action to the GitHub Marketplace**
- [ ] Accept the Marketplace developer terms
- [ ] Pick **two categories**: *Code quality* and *Continuous integration*
- [ ] Add featured tags: `code-quality`, `pull-request`, `git`, `coupling`,
      `static-analysis`
- [ ] Submit; the listing usually goes live within a few minutes at
      https://github.com/marketplace/actions/couplingguard

For subsequent releases, the Marketplace listing updates automatically
when the `v1` major-version tag moves.

### 5. Announce (optional)

- [ ] Tweet / toot the release with a screenshot of the PR comment
- [ ] Post in r/Python, r/programming, HN (Show HN)
- [ ] Add a "What's new in v0.X.Y" line to your blog
- [ ] DM a few platform-engineer friends to try it on a real PR

### 6. Post-release housekeeping

- [ ] Open a new `## [Unreleased]` section in `CHANGELOG.md` for the next
      release
- [ ] Triage any Marketplace install issues that come in within the first
      48 hours
- [ ] If a hotfix is needed: branch from the tag (`git checkout -b
      hotfix/v0.X.Z v0.X.Y`), fix, tag `v0.X.Z`, push, repeat steps 3-4

## Rollback plan

If a release ships broken:

1. **Yank the bad version from PyPI**: project page → Manage → Yank release.
   This keeps pip from auto-resolving to it but doesn't break existing
   installs.
2. **Move the `v1` tag back to the previous good commit**:
   ```bash
   git tag -f v1 <previous-good-sha>
   git push -f origin v1
   ```
   Users of `@v1` instantly get the previous version on next run.
3. **Cut a fixed patch** following the per-release flow above.
4. Open a GitHub Discussion or Issue explaining what happened, what users
   should do, and the ETA on the fix.
