# Changelog

## 0.7.0 — 2026-10-28

Composite GitHub Action at the repository root (`action.yml`). A workflow can classify a saved log, a shipped fixture, or a completed run's logs. The step writes `$GITHUB_STEP_SUMMARY` and outputs `category`, `confidence`, `confidence-level`, `advisory`, `next-step`, and `evidence`. No LLM.

`comment` stays off unless the workflow sets `comment: true`. That path posts or updates one pull request comment with the workflow `GITHUB_TOKEN`.

Same-job `if: failure()` cannot download the current run's log archive, because the job is still in progress. Pass `log-path`, or use `workflow_run` with `run-id`.

Skill metadata is 0.7.0. Taxonomy ids are unchanged. The fixture eval is still 73/73.

The moving tag `v1` should point at this release. `v0.7.0` should stay on this commit. Publishing to the Marketplace is a checkbox on the GitHub Release. See [docs/release-notes-v0.7.0.md](docs/release-notes-v0.7.0.md).

## 0.6.0 — 2026-10-27

Service and Helm health-check timeouts, Bundler, `go.sum`, `Cargo.lock`, DNS name resolution, and `actions/cache` restore. 73 fixtures, eval 73/73.

## 0.5.0 — 2026-10-26

Feature guide in both READMEs. Multi-job scoring ignores a green job. Checkout hook cascades stay `flake`. Registry authentication denial is separate from egress.

## 0.4.0 — 2026-10-26

Checkout TLS, external dataset hosts, and blocked registry pulls. 57 fixtures.

## 0.3.0 — 2026-10-26

Corpus of 50 fixtures, broader redaction, playbooks for the new cases.
