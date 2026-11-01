# Changelog

## 0.12.1 — 2026-11-01

Public name is `ci-fail-classify` (formerly `ci-diagnose`). Clone URLs, Action `uses:` examples, and the install curl URL point at `https://github.com/haoranyoung09-sys/ci-fail-classify`. The Action marketplace name is `ci-fail-classify`. Inputs and outputs are unchanged, so `@v1` stays the same contract. The skill directory remains `ci-doctor`.

The READMEs say how this differs from other failure-triage tools and from a full CI platform: a scored seven-class taxonomy, an offline fixture oracle, an agent skill, bilingual playbooks, and an advisory report. It does not build or host the app.

146 fixtures. Eval 146/146. Notes: [docs/release-notes-v0.12.1.md](docs/release-notes-v0.12.1.md).

## 0.12.0 — 2026-11-01

The install one-liner now pins `v0.12.0`. The Action stays `uses: haoranyoung09-sys/ci-fail-classify@v1`. [docs/architecture.md](docs/architecture.md) says what the Action, CLI, and skill each do. This is still diagnosis only.

Apple signing material missing or expired, match git username or decrypt failure, a missing Android keystore or SDK, and a bundletool JDK mismatch are `env`. An unauthorized adb device and Apple notarization 401 are `permissions`. No adb device, and a simulator that will not boot, are `infra`. A notarization timeout is `flake`. A fastlane expected/got line and a Metro syntax error are `test`.

146 fixtures. Eval 146/146. Taxonomy ids unchanged.

Action inputs, outputs, and branding are unchanged. Notes: [docs/release-notes-v0.12.0.md](docs/release-notes-v0.12.0.md).

## 0.11.0 — 2026-11-01

`bash scripts/install.sh --user --cli` links the skill for Cursor and Codex and can install a `diagnose` wrapper. It does not replace an existing install unless `--force` is set. The curl one-liner uses tag `v0.11.0` on the public mirror and does not send a token.

Yarn Berry's immutable install, Yarn PnP, pip hash mismatch, Coursier, pub version solving, a frozen Bun lockfile, and a missing image tag are `deps`. Poetry or uv asking for another Python, and an artifact path or name that matches nothing, are `env`. A bare PyPI 503 is `flake`. An image pull 401 is `permissions`. Ruff failing to parse a file is `test`.

131 fixtures. Eval 131/131. Taxonomy ids unchanged.

Action inputs, outputs, and branding are unchanged, so `@v1` stays compatible. Notes: [docs/release-notes-v0.11.0.md](docs/release-notes-v0.11.0.md).

## 0.10.0 — 2026-10-30

Bazel remote cache, Nix store hash mismatch, apt mirror 404, a Homebrew bottle download, and a Rust linker that cannot allocate are `infra`. A missing Nix flake output and a stale Deno lockfile are `deps` (the Nix word flake is not a rerun). apt `NO_PUBKEY`, missing Google ADC, a Composer PHP platform requirement, and a reusable workflow secret that was not passed are `env`. An invalid AWS security token is `permissions`. A Go module proxy 502 and a bare `ECONNRESET` are `flake`. `ECONNRESET` tied with `AssertionError` stays `unknown`. Linker OOM outranks `could not compile`.

117 fixtures. Eval 117/117. Taxonomy ids unchanged.

Action inputs, outputs, and branding are unchanged, so `@v1` stays compatible. Notes: [docs/release-notes-v0.10.0.md](docs/release-notes-v0.10.0.md).

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
