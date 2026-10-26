# Taxonomy v0

[中文](taxonomy.zh-CN.md)

Seven categories. The id is the contract: `flake`, `env`, `test`, `deps`, `permissions`, `infra`, `unknown`. The diagnose CLI scores signals in [`scripts/diagnose.py`](../scripts/diagnose.py). A category wins when its score is at least 6 and it leads. Below that threshold the result is `unknown`. A tie between two categories at or above the threshold is also `unknown`.

Confidence is `high` (≥ 0.80), `medium` (≥ 0.60), or `low`. `unknown` is low on purpose. None of these mean safe to merge.

Logs may be raw step output or `gh run view --log-failed` lines (`job`, `step`, timestamp). Prefixes are stripped before matching.

## flake

A failure that moved when nothing else did: a timeout that passed on rerun, a test marked intermittent, a numbered retry that sometimes goes green.

**Signals:** "suspected flake", "exceeded timeout of N", "timeout of N ms exceeded", "passed on the previous run" or "passed on the automatic rerun", "intermittent", "retry N of M", checkout "SSL certificate problem" / "server certificate verification failed" / "unable to get local issuer certificate" / "The TLS connection was non-properly terminated", "failed to download the external dataset", "external host timed out". A tie with an `AssertionError` stays `unknown` (`timeout-and-assertion-unknown`, `checkout-tls-and-assertion-unknown`, `dataset-and-assertion-unknown`).

**Not this:** a stable assertion (`test`), a runner that ran out of memory (`infra`), a registry DNS or egress failure (`infra`), a registry 404 for a missing package (`deps`).

**Fixtures:** [`jest-timeout-flake`](../fixtures/gha/jest-timeout-flake), [`registry-timeout-rerun-flake`](../fixtures/gha/registry-timeout-rerun-flake), [`playwright-timeout-flake`](../fixtures/gha/playwright-timeout-flake), [`cypress-timeout-flake`](../fixtures/gha/cypress-timeout-flake), [`matrix-shard-flake`](../fixtures/gha/matrix-shard-flake), [`docker-rate-limit-flake`](../fixtures/gha/docker-rate-limit-flake), [`checkout-tls-verify-flake`](../fixtures/gha/checkout-tls-verify-flake), [`external-dataset-host-flake`](../fixtures/gha/external-dataset-host-flake), [`checkout-tls-hook-cascade-flake`](../fixtures/gha/checkout-tls-hook-cascade-flake). A hook line with no checkout error stays under the threshold (`checkout-hook-only-unknown`). A shard that only says "retry N of M" stays `unknown` (`shard-retry-only-unknown`).

**Minimal next step:** quote the rerun or timeout line. Prefer a deterministic wait over bumping the timeout as the only edit. One rerun is evidence, not a fix.

## env

The job died because a name was missing: an environment variable, an action input, or a secret that was never provided. The value must not appear in the report.

**Signals:** "Required environment variable NAME is not set", "Input required and not supplied", "NAME is empty", "secret NAME was not provided".

**Not this:** a 403 from `GITHUB_TOKEN` (`permissions`), a peer conflict (`deps`).

**Fixtures:** [`missing-database-url`](../fixtures/gha/missing-database-url), [`missing-node-auth-token`](../fixtures/gha/missing-node-auth-token), [`unset-api-base-url`](../fixtures/gha/unset-api-base-url), [`secret-signing-key-missing`](../fixtures/gha/secret-signing-key-missing), [`aws-region-undefined`](../fixtures/gha/aws-region-undefined), [`compose-db-url-unset`](../fixtures/gha/compose-db-url-unset). A tie with "does not have permission" stays `unknown` (`empty-token-and-permission-unknown`, `oidc-role-and-empty-arn-unknown`).

**Minimal next step:** supply that name on the job or the Actions environment that the job uses. Do not invent a value and do not print one.

## test

The suite started and an expectation failed. Jest `FAIL`, pytest `FAILED`, `AssertionError`, expected versus received.

**Signals:** `AssertionError`, `expect(received)`, a `FAIL path` line, `--- FAIL:` from `go test`, `Expected:`, `Tests: N failed`, `FAILED path`, `Test Suites: N failed`, PHPUnit "Failed asserting that", RSpec `Failure/Error:`, cargo `test result: FAILED`.

**Not this:** a timeout that passed on another attempt (`flake`), `npm ci` refusing a lockfile (`deps`).

**Fixtures:** [`npm-test-assertion`](../fixtures/gha/npm-test-assertion), [`pytest-assertion`](../fixtures/gha/pytest-assertion), [`go-test-want-got`](../fixtures/gha/go-test-want-got), [`maven-surefire-assertion`](../fixtures/gha/maven-surefire-assertion), [`phpunit-assert-failed`](../fixtures/gha/phpunit-assert-failed), [`rspec-failure-error`](../fixtures/gha/rspec-failure-error), [`cargo-test-result-failed`](../fixtures/gha/cargo-test-result-failed), [`gradle-test-assertion`](../fixtures/gha/gradle-test-assertion), [`multi-job-one-step-failed`](../fixtures/gha/multi-job-one-step-failed). In a multi-job log, only the failed job is scored.

**Minimal next step:** change the product code or the assertion the failure points at. Do not delete the test to go green.

## deps

The install or resolver failed. Peer conflicts, `ERESOLVE`, `npm ci` refusing an out-of-sync lockfile.

**Signals:** `ERESOLVE`, "unable to resolve dependency tree", "Conflicting peer dependency", "Could not resolve dependency", `package.json` and `package-lock.json` out of sync, "Missing: … from lock file", `ERR_PNPM_OUTDATED_LOCKFILE`, pip "Could not find a version that satisfies", `yarn.lock` / `poetry.lock` / `uv.lock` out of date, Gradle "Could not resolve all files for configuration".

**Not this:** a missing `NODE_AUTH_TOKEN` before publish (`env`), a test that fails after a clean install (`test`).

**Fixtures:** [`npm-peer-eresolve`](../fixtures/gha/npm-peer-eresolve), [`npm-ci-lockfile-drift`](../fixtures/gha/npm-ci-lockfile-drift), [`pnpm-outdated-lockfile`](../fixtures/gha/pnpm-outdated-lockfile), [`pip-version-unsatisfied`](../fixtures/gha/pip-version-unsatisfied), [`yarn-lockfile-out-of-date`](../fixtures/gha/yarn-lockfile-out-of-date), [`poetry-lock-out-of-date`](../fixtures/gha/poetry-lock-out-of-date), [`uv-lock-needs-update`](../fixtures/gha/uv-lock-needs-update), [`gradle-configuration-unresolved`](../fixtures/gha/gradle-configuration-unresolved). A tie with `AssertionError` stays `unknown` (`poetry-lock-and-assertion-unknown`).

**Minimal next step:** align the versions in the evidence, or commit an updated lockfile. Do not lead with `--force` or `--legacy-peer-deps`. Do not replace `npm ci` with `npm install` in CI as the fix.

## permissions

The token, role, or `permissions:` block refused an API. Typical shape: HTTP 403, "Resource not accessible by integration", or `git` denying `github-actions[bot]`.

**Signals:** "Resource not accessible by integration", "Permission to … denied", "requested URL returned error: 403", `HttpError` 403, "does not have permission", "not granted contents:" / `issues:` / `pull-requests:` / `id-token:`. A lone "Refusing to force-push" stays under the threshold (`force-push-refusal-only-unknown`).

**Not this:** a filesystem `EACCES` inside a build script with no GitHub API involved (often `infra` or `env` once the path is known), a missing secret value (`env`).

**Fixtures:** [`gha-token-integration-403`](../fixtures/gha/gha-token-integration-403), [`git-push-permission-denied`](../fixtures/gha/git-push-permission-denied), [`id-token-permission-denied`](../fixtures/gha/id-token-permission-denied), [`bare-http-403`](../fixtures/gha/bare-http-403), [`oidc-assume-role-denied`](../fixtures/gha/oidc-assume-role-denied), [`registry-pull-auth-denied`](../fixtures/gha/registry-pull-auth-denied). `pull access denied` is permissions. `no such host` without an auth line is `infra`. Both together stay `unknown` (`registry-auth-and-egress-unknown`).

**Minimal next step:** name the narrowest missing scope. Do not switch the job to a personal access token. Do not force-push.

## infra

The host fell over. Heap OOM, runner disk full, process killed, runner shutdown. The assertion is not the bug.

**Signals:** "JavaScript heap out of memory", "Reached heap limit", `OOMKilled`, "No space left on device", "disk quota exceeded", "runner process was killed", "Cannot connect to the Docker daemon", registry pull `dial tcp: lookup` / "no such host" / "network is unreachable" / "TLS handshake timeout" / "i/o timeout" / "egress blocked". An "out of memory" line tied with "does not have permission" stays `unknown` (`oom-and-permission-unknown`). Egress blocked tied with `remote: permission to … denied` stays `unknown` (`egress-and-permission-unknown`).

**Not this:** a test timeout that passed on rerun (`flake`), checkout certificate verification (`flake`), `pull access denied` with no DNS or egress line (`permissions`), an `npm` resolver error (`deps`).

**Fixtures:** [`node-heap-oom`](../fixtures/gha/node-heap-oom), [`runner-disk-full`](../fixtures/gha/runner-disk-full), [`generic-oom-without-heap`](../fixtures/gha/generic-oom-without-heap), [`runner-killed-exit-137`](../fixtures/gha/runner-killed-exit-137), [`docker-build-disk-full`](../fixtures/gha/docker-build-disk-full), [`docker-daemon-unavailable`](../fixtures/gha/docker-daemon-unavailable), [`mcr-pull-egress-blocked`](../fixtures/gha/mcr-pull-egress-blocked), [`ghcr-pull-io-timeout`](../fixtures/gha/ghcr-pull-io-timeout).

**Minimal next step:** one resource change (heap cap, fewer artifacts, larger runner). One rerun after a shutdown is reasonable. A second identical host failure stops the loop.

## unknown

The log does not carry a v0 signal strong enough to pick a category, or two categories tie. This is a valid answer.

**Signals:** a bare "Process completed with exit code 1", or a cancel line with no other signal. A weak hit that stays under the score threshold is still `unknown`. Two categories at the same score at or above 6 are also `unknown`. `canceled-step-unknown` matches nothing in v0 on purpose.

**Not this:** a place to hide a guess. Do not invent an eighth category in the report. Do not treat a filesystem `EACCES` as `permissions`, and do not treat a below-threshold force-push refusal as permission to force-push.

**Fixtures:** [`bare-exit-unknown`](../fixtures/gha/bare-exit-unknown), [`canceled-step-unknown`](../fixtures/gha/canceled-step-unknown), [`timeout-and-assertion-unknown`](../fixtures/gha/timeout-and-assertion-unknown), [`empty-token-and-permission-unknown`](../fixtures/gha/empty-token-and-permission-unknown), [`force-push-refusal-only-unknown`](../fixtures/gha/force-push-refusal-only-unknown), [`cache-eacces-unknown`](../fixtures/gha/cache-eacces-unknown), [`concurrency-cancel-unknown`](../fixtures/gha/concurrency-cancel-unknown), [`poetry-lock-and-assertion-unknown`](../fixtures/gha/poetry-lock-and-assertion-unknown), [`oom-and-permission-unknown`](../fixtures/gha/oom-and-permission-unknown), [`oidc-role-and-empty-arn-unknown`](../fixtures/gha/oidc-role-and-empty-arn-unknown), [`shard-retry-only-unknown`](../fixtures/gha/shard-retry-only-unknown), [`checkout-tls-and-assertion-unknown`](../fixtures/gha/checkout-tls-and-assertion-unknown), [`dataset-and-assertion-unknown`](../fixtures/gha/dataset-and-assertion-unknown), [`egress-and-permission-unknown`](../fixtures/gha/egress-and-permission-unknown), [`checkout-hook-only-unknown`](../fixtures/gha/checkout-hook-only-unknown), [`multi-job-green-noise-unknown`](../fixtures/gha/multi-job-green-noise-unknown), [`registry-auth-and-egress-unknown`](../fixtures/gha/registry-auth-and-egress-unknown).

**Minimal next step:** ask for the failed step name and the lines above the exit. Do not refactor while you wait.

## How to extend it

Add a fixture first, then a signal, then a sentence in this file and in [`skills/ci-doctor/references/taxonomy.md`](../skills/ci-doctor/references/taxonomy.md). Renaming an id is a taxonomy version change, not a drive-by edit. See [CONTRIBUTING.md](../CONTRIBUTING.md).
