# CI Doctor — roadmap

**Date:** 2026-10-26 (Asia/Shanghai)
**Owner:** Young
**Goal:** Long-cycle OSS product: an agent skill and a small toolset that triage CI failures, a fixture corpus that compounds, and room to grow a family brand.

**Bootstrap status:** this tree has the installable skill, taxonomy v0, the synthetic GitHub Actions corpus, bilingual docs, and the smoke workflow. `scripts/diagnose.py` classifies a fixture or a saved log offline, and it can fetch a public failed run with `gh run view --log-failed` when `gh` is installed and logged in. Without `gh`, that path exits with a short message. `make eval` scores the corpus offline. Playbooks under `skills/ci-doctor/references/playbooks/` carry a recipe, a verification, and a stop for each category. `.github/workflows/triage-comment.yml` is an experimental comment sketch and is disabled. A real comment bot, extra CI hosts, and the Dependabot sibling are later phases.

## Positioning

**One line:** Pull a failed CI run, classify the root cause, propose a minimal fix, and verify — a portable skill pack with a public redacted fixture corpus.

**Not this:** generic AI pull-request review, a flaky-test SaaS, or another Actions marketplace bot.

## Why this can earn stars (long cycle)

- Universal weekly pain for every active repo.
- Embedded playbooks exist (for example microsoft/vscode `.github/skills/fix-ci-failures`) but there is no dominant standalone skill pack.
- The fixture corpus and the taxonomy are a compounding asset for demos, evals, and docs.
- Natural expansion stays on the same brand: a Dependabot explainer, more CI hosts, a pull-request comment bot.

## Two-year roadmap

### Year 0–3 months — MVP

- Installable Agent Skill (`skills/ci-doctor/SKILL.md`) for Claude Code, Cursor, and Codex-style hosts.
- GitHub Actions first: fetch failed run logs via `gh` (documented recipes; graceful without auth).
- Cause taxonomy v0: `flake` | `env` | `test` | `deps` | `permissions` | `infra` | `unknown`.
- Redacted public fixtures under `fixtures/` with expected labels. The bootstrap set is synthetic and lives in `fixtures/gha/`.
- CLI: offline `doctor diagnose <log>`, implemented as `python3 scripts/diagnose.py`.
- Guardrails: stop after two failed fix attempts; never force-push; never print secrets.
- Bilingual README (English + 中文).
- MIT license, CONTRIBUTING, Code of Conduct.

### Months 3–9

- A GitHub Action that posts a triage summary on a failed `workflow_run`.
- Grow the corpus toward 50–100 fixtures and add golden evals (skill versus a baseline).
- A Dependabot/Renovate “safe-merge explainer” as a sibling skill. That sibling is the one that may talk about merge safety. This skill does not.
- A better log redaction pipeline.

### Months 9–24

- GitLab CI and CircleCI adapters.
- A narrow flaky-reproduction assistant, not a flakiness platform.
- Optional org mode: pin a skill version, and check CI for skill drift.
- Community fixture contributions and taxonomy versioning.

## MVP success criteria

1. A fresh clone can follow the README, diagnose one fixture offline, and get a structured report (category, evidence quotes, suggested next steps).
2. With `gh` auth, a public failed Actions run can be triaged from a URL or run id by the documented recipe. Without auth, the path fails closed onto a saved log.
3. The skill description triggers on “CI failed”, “Actions is red”, and “fix the build”.
4. At least 10 fixtures carry labels, and the taxonomy is documented.
5. The English and Chinese READMEs agree.

## Repo layout

```text
README.md
README.zh-CN.md
LICENSE
CONTRIBUTING.md
CODE_OF_CONDUCT.md
ROADMAP.md
docs/
  taxonomy.md
  taxonomy.zh-CN.md
  hosts.md
  hosts.zh-CN.md
skills/
  ci-doctor/
    SKILL.md
    references/
      taxonomy.md
      playbooks/
fixtures/
  README.md
  gha/
    <case-id>/
      meta.json
      log.txt
scripts/
  diagnose.py
.github/
  workflows/
    smoke.yml
```

## Naming

Working name: **ci-doctor**. The brand family can be “CI Doctor”. Check for unrelated “cidoctor” products before publishing under another name.

## Constraints

- Privacy first. Fixtures are redacted. The skill refuses to echo tokens or secret values.
- Advisory tone. Reports carry a confidence level. “Safe to merge” belongs to a later sibling, not to this skill.
- Prefer a small MVP: GitHub Actions, fixtures, and the skill. More hosts wait.
