# Fixture corpus

Synthetic, redacted GitHub Actions failures for taxonomy v0. Nothing here is a customer log. Every `log.txt` says it is a synthetic redacted fixture and not a real workflow run.

```bash
python3 scripts/diagnose.py --fixtures-dir fixtures/gha
```

The loader checks `meta.json`, rejects secret-like strings, and fails the smoke run when the classifier disagrees with `label`.

## meta.json

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | yes | Kebab-case, same as the directory name |
| `label` | yes | One of `flake`, `env`, `test`, `deps`, `permissions`, `infra`, `unknown` |
| `notes` | yes | Why this label, and why a neighbor is wrong |
| `source` | yes | `synthetic` or `redacted-public` |
| `redacted` | yes | Must be `true` |
| `host` | yes under `gha/` | `github-actions` |

`label` is ground truth for the smoke test. The classifier does not read it while scoring.

## Cases

| id | label | What the log is |
| --- | --- | --- |
| `npm-test-assertion` | test | Jest expected 200, received 503. `gh --log-failed` prefixes included. |
| `pytest-assertion` | test | pytest `AssertionError` on an invoice total. |
| `missing-database-url` | env | `DATABASE_URL` unset. No connection string. |
| `missing-node-auth-token` | env | `NODE_AUTH_TOKEN` empty. No token value. |
| `gha-token-integration-403` | permissions | Issue comment API: resource not accessible by integration. |
| `git-push-permission-denied` | permissions | `github-actions[bot]` push denied, HTTP 403. |
| `npm-peer-eresolve` | deps | react 18 root versus a react 17 peer. |
| `npm-ci-lockfile-drift` | deps | `npm ci` lockfile out of sync on `left-pad`. |
| `jest-timeout-flake` | flake | 5000 ms timeout; passed on the previous attempt. |
| `registry-timeout-rerun-flake` | flake | Registry connect timed out; passed on automatic rerun. |
| `node-heap-oom` | infra | V8 heap limit, runner killed, exit 137. |
| `runner-disk-full` | infra | Artifact upload, no space left on device. |
| `bare-exit-unknown` | unknown | Exit code 1 and no taxonomy signal. |
| `go-test-want-got` | test | `go test` `--- FAIL`, got 503 want 200. |
| `maven-surefire-assertion` | test | Surefire `AssertionError`, expected 200 was 503. |
| `unset-api-base-url` | env | `API_BASE_URL` unset. No endpoint printed. |
| `pnpm-outdated-lockfile` | deps | `ERR_PNPM_OUTDATED_LOCKFILE` on a frozen install. |
| `id-token-permission-denied` | permissions | Job not granted `id-token: write`. No credential. |
| `playwright-timeout-flake` | flake | 30000 ms timeout; passed on the previous attempt. |
| `canceled-step-unknown` | unknown | Canceled before any step log. No v0 signal at all. |
| `phpunit-assert-failed` | test | PHPUnit "Failed asserting that". Suite started. |
| `rspec-failure-error` | test | RSpec `Failure/Error` with expected 200, got 503. |
| `cargo-test-result-failed` | test | `test result: FAILED` from cargo. |
| `pip-version-unsatisfied` | deps | pip could not satisfy `example-lib==9.9.9`. |
| `yarn-lockfile-out-of-date` | deps | `yarn.lock` out of date on a frozen install. |
| `secret-signing-key-missing` | env | `SIGNING_KEY` was not provided. No value. |
| `aws-region-undefined` | env | `AWS_REGION` undefined. No access key. |
| `bare-http-403` | permissions | One `HttpError: 403` and no scope name. |
| `generic-oom-without-heap` | infra | "out of memory" without a V8 heap line. |
| `runner-killed-exit-137` | infra | Runner process killed, exit 137. |
| `cypress-timeout-flake` | flake | 4000 ms timeout; passed on the previous run. |
| `timeout-and-assertion-unknown` | unknown | Tie: `AssertionError` and "Exceeded timeout of 5000". |
| `empty-token-and-permission-unknown` | unknown | Tie: empty `NODE_AUTH_TOKEN` and "does not have permission". |
| `force-push-refusal-only-unknown` | unknown | "Refusing to force-push" stays under the score threshold. |
| `cache-eacces-unknown` | unknown | `EACCES` on a runner cache path. Not a GitHub 403. |
| `poetry-lock-out-of-date` | deps | `poetry.lock` out of date with `pyproject.toml`. |
| `uv-lock-needs-update` | deps | `uv.lock` needs an update on a frozen install. |
| `gradle-configuration-unresolved` | deps | Gradle could not resolve `:app:compileClasspath`. |
| `gradle-test-assertion` | test | Gradle `:app:test` `AssertionError`. |
| `docker-build-disk-full` | infra | `docker build` ran out of disk. |
| `docker-daemon-unavailable` | infra | Cannot connect to the Docker daemon. |
| `compose-db-url-unset` | env | Compose `db` failed because `DATABASE_URL` is unset. |
| `matrix-shard-flake` | flake | Matrix shard 3 of 8 passed on the previous run. |
| `docker-rate-limit-flake` | flake | Docker Hub `toomanyrequests`, passed on rerun. |
| `concurrency-cancel-unknown` | unknown | Concurrency group canceled the run. No v0 signal. |
| `oidc-assume-role-denied` | permissions | Not granted `id-token: write`. No static cloud key. |
| `oidc-role-and-empty-arn-unknown` | unknown | Tie: empty `AWS_ROLE_ARN` and "does not have permission". |
| `poetry-lock-and-assertion-unknown` | unknown | Tie: poetry lockfile and `AssertionError`. |
| `oom-and-permission-unknown` | unknown | Tie: "out of memory" and "does not have permission". |
| `shard-retry-only-unknown` | unknown | Matrix shard only says `retry 2 of 4`. Under the threshold. |
| `checkout-tls-verify-flake` | flake | `actions/checkout` SSL certificate verification failed. |
| `checkout-tls-and-assertion-unknown` | unknown | Tie: checkout certificate verification and `AssertionError`. |
| `external-dataset-host-flake` | flake | External dataset host timed out. No assertion. |
| `dataset-and-assertion-unknown` | unknown | Tie: external dataset download and `AssertionError`. |
| `mcr-pull-egress-blocked` | infra | `mcr.microsoft.com` pull: DNS lookup failed, egress blocked. |
| `ghcr-pull-io-timeout` | infra | `ghcr.io` pull: TLS handshake timeout and `i/o timeout`. |
| `egress-and-permission-unknown` | unknown | Tie: registry egress blocked and a git permission denial. |
| `checkout-tls-hook-cascade-flake` | flake | Checkout TLS failed, then the post-checkout hook could not run. |
| `checkout-hook-only-unknown` | unknown | Hook missing, no checkout or certificate line. Under the threshold. |
| `multi-job-one-step-failed` | test | Green job mentions a flake. Only the test job failed. |
| `multi-job-green-noise-unknown` | unknown | The only taxonomy phrase is on the green job. |
| `registry-pull-auth-denied` | permissions | Image pull access denied. Not an egress block. |
| `registry-auth-and-egress-unknown` | unknown | Tie: registry auth denied and egress blocked. |
| `service-healthcheck-timeout-flake` | flake | Postgres service container health check timed out. |
| `helm-healthcheck-timeout-flake` | flake | Helm health check timed out on InProgress. |
| `healthcheck-and-assertion-unknown` | unknown | Tie: health check timeout and `AssertionError`. |
| `external-host-chronic-flake` | flake | External dataset host failed on every attempt. Still flake. |
| `bundler-lockfile-out-of-date` | deps | `Gemfile.lock` stale under `bundle install --deployment`. |
| `go-sum-checksum-mismatch` | deps | Missing `go.sum` entry and a checksum mismatch. |
| `cargo-lock-needs-update` | deps | `Cargo.lock` needs an update under `--locked`. |
| `dns-name-resolution-infra` | infra | `getaddrinfo` temporary failure in name resolution. |
| `actions-cache-restore-corrupt` | infra | Cache restore failed; lockfile noise is downstream. |
| `cache-eacces-and-lockfile-unknown` | unknown | Tie: cache `EACCES` and a lockfile mismatch. |

Add a case by the steps in [CONTRIBUTING.md](../CONTRIBUTING.md).
