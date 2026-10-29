# Changelog

## 0.9.0 — 2026-10-29

Maven, SwiftPM, CocoaPods, and NuGet resolution failures are `deps`. Cargo registry network errors are `flake`; a rustc type error that cargo could not compile is `test`. Terraform state lock is `flake`; missing cloud credentials are `env`. kubectl rollout timeout is `flake`; RBAC `is forbidden` is `permissions`. A GitHub secondary rate limit is `flake`; Bad credentials are `permissions`. `java.lang.OutOfMemoryError` and Python `MemoryError` are `infra`. `Missing required environment variable NAME` is `env`.

102 fixtures. Eval 102/102. Taxonomy ids unchanged.

Action inputs, outputs, and branding are unchanged from 0.7.0, so `@v1` stays compatible. Notes: [docs/release-notes-v0.9.0.md](docs/release-notes-v0.9.0.md).

## 0.8.0 — 2026-10-28

More of the failures that used to land on `unknown`: a bare kernel `Killed` (exit 137), Node `engines` and missing setup-python/setup-node versions, a missing composite `action.yml`, a self-hosted runner that lost communication, `Filename too long`, an arm64 image on an amd64 host, a missing Docker build layer, bare `toomanyrequests`, Cypress "timed out retrying", and a Git LFS rate limit. `pnpm-lock.yaml` "not up to date" stays `deps`. A `continue-on-error` step no longer hides the later lockfile error. A pull rate limit tied with `pull access denied` stays `unknown`.

87 fixtures. Eval 87/87. Taxonomy ids unchanged.

The GitHub Action inputs, outputs, and branding from 0.7.0 are unchanged, so `@v1` stays compatible. Move the `v1` tag only when you publish this release. Notes: [docs/release-notes-v0.8.0.md](docs/release-notes-v0.8.0.md).

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
