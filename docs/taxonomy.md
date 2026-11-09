# Taxonomy v0

[中文](taxonomy.zh-CN.md)

Seven categories. The id is the contract: `flake`, `env`, `test`, `deps`, `permissions`, `infra`, `unknown`. The diagnose CLI scores signals in [`scripts/diagnose.py`](../scripts/diagnose.py). A category wins when its score is at least 6 and it leads. Below that threshold the result is `unknown`. A tie between two categories at or above the threshold is also `unknown`.

Confidence is `high` (≥ 0.80), `medium` (≥ 0.60), or `low`. `unknown` is low on purpose. None of these mean safe to merge.

Logs may be raw step output or `gh run view --log-failed` lines (`job`, `step`, timestamp). Prefixes are stripped before matching.

## flake

A failure that moved when nothing else did: a timeout that passed on rerun, a test marked intermittent, a numbered retry that sometimes goes green.

**Signals:** "suspected flake", "exceeded timeout of N", "timeout of N ms exceeded", "passed on the previous run" or "passed on the automatic rerun", "intermittent", "retry N of M", checkout "SSL certificate problem" / "server certificate verification failed" / "unable to get local issuer certificate" / "The TLS connection was non-properly terminated", "failed to download the external dataset", "external host timed out", "health check failed" / "health check timed out" / "service container … failed to start", Helm "timeout waiting for … InProgress". A tie with an `AssertionError` stays `unknown` (`timeout-and-assertion-unknown`, `checkout-tls-and-assertion-unknown`, `dataset-and-assertion-unknown`).

**Not this:** a stable assertion (`test`), a runner that ran out of memory (`infra`), a registry DNS or egress failure (`infra`), a registry 404 for a missing package (`deps`).

**Fixtures:** [`jest-timeout-flake`](../fixtures/gha/jest-timeout-flake), [`registry-timeout-rerun-flake`](../fixtures/gha/registry-timeout-rerun-flake), [`playwright-timeout-flake`](../fixtures/gha/playwright-timeout-flake), [`cypress-timeout-flake`](../fixtures/gha/cypress-timeout-flake), [`matrix-shard-flake`](../fixtures/gha/matrix-shard-flake), [`docker-rate-limit-flake`](../fixtures/gha/docker-rate-limit-flake), [`checkout-tls-verify-flake`](../fixtures/gha/checkout-tls-verify-flake), [`external-dataset-host-flake`](../fixtures/gha/external-dataset-host-flake), [`checkout-tls-hook-cascade-flake`](../fixtures/gha/checkout-tls-hook-cascade-flake), [`service-healthcheck-timeout-flake`](../fixtures/gha/service-healthcheck-timeout-flake), [`helm-healthcheck-timeout-flake`](../fixtures/gha/helm-healthcheck-timeout-flake), [`external-host-chronic-flake`](../fixtures/gha/external-host-chronic-flake). A hook line with no checkout error stays under the threshold (`checkout-hook-only-unknown`). A health check tied with `AssertionError` stays `unknown` (`healthcheck-and-assertion-unknown`). A chronic external host stays `flake`; mirror or vendor the file instead of rerunning the same URL. Bare `toomanyrequests` (`docker-pull-rate-limit-flake`), Cypress "Timed out retrying after" (`cypress-retry-timeout-flake`), and a Git LFS rate limit (`git-lfs-rate-limit-flake`) are flake. Rate limit tied with `pull access denied` stays `unknown` (`registry-rate-and-auth-unknown`). A shard that only says "retry N of M" stays `unknown` (`shard-retry-only-unknown`).

**Minimal next step:** quote the rerun or timeout line. Prefer a deterministic wait over bumping the timeout as the only edit. One rerun is evidence, not a fix.

## env

The job died because a name was missing: an environment variable, an action input, or a secret that was never provided. The value must not appear in the report.

**Signals:** "Required environment variable NAME is not set", "Input required and not supplied", "NAME is empty", "secret NAME was not provided".

**Not this:** a 403 from `GITHUB_TOKEN` (`permissions`), a peer conflict (`deps`).

**Fixtures:** [`missing-database-url`](../fixtures/gha/missing-database-url), [`missing-node-auth-token`](../fixtures/gha/missing-node-auth-token), [`unset-api-base-url`](../fixtures/gha/unset-api-base-url), [`secret-signing-key-missing`](../fixtures/gha/secret-signing-key-missing), [`aws-region-undefined`](../fixtures/gha/aws-region-undefined), [`compose-db-url-unset`](../fixtures/gha/compose-db-url-unset), [`node-engine-mismatch-env`](../fixtures/gha/node-engine-mismatch-env), [`setup-python-version-missing-env`](../fixtures/gha/setup-python-version-missing-env), [`composite-action-path-missing-env`](../fixtures/gha/composite-action-path-missing-env). A tie with "does not have permission" stays `unknown` (`empty-token-and-permission-unknown`, `oidc-role-and-empty-arn-unknown`).

**Minimal next step:** supply that name on the job or the Actions environment that the job uses. Do not invent a value and do not print one.

## test

The suite started and an expectation failed. Jest `FAIL`, pytest `FAILED`, `AssertionError`, expected versus received.

**Signals:** `AssertionError`, `expect(received)`, a `FAIL path` line, `--- FAIL:` from `go test`, `Expected:`, `Tests: N failed`, `FAILED path`, `Test Suites: N failed`, PHPUnit "Failed asserting that", RSpec `Failure/Error:`, cargo `test result: FAILED`.

**Not this:** a timeout that passed on another attempt (`flake`), `npm ci` refusing a lockfile (`deps`).

**Fixtures:** [`npm-test-assertion`](../fixtures/gha/npm-test-assertion), [`pytest-assertion`](../fixtures/gha/pytest-assertion), [`go-test-want-got`](../fixtures/gha/go-test-want-got), [`maven-surefire-assertion`](../fixtures/gha/maven-surefire-assertion), [`phpunit-assert-failed`](../fixtures/gha/phpunit-assert-failed), [`rspec-failure-error`](../fixtures/gha/rspec-failure-error), [`cargo-test-result-failed`](../fixtures/gha/cargo-test-result-failed), [`gradle-test-assertion`](../fixtures/gha/gradle-test-assertion), [`multi-job-one-step-failed`](../fixtures/gha/multi-job-one-step-failed). In a multi-job log, only the failed job is scored.

**Minimal next step:** change the product code or the assertion the failure points at. Do not delete the test to go green.

## deps

The install or resolver failed. Peer conflicts, `ERESOLVE`, `npm ci` refusing an out-of-sync lockfile.

**Signals:** `ERESOLVE`, "unable to resolve dependency tree", "Conflicting peer dependency", "Could not resolve dependency", `package.json` and `package-lock.json` out of sync, "Missing: … from lock file", `ERR_PNPM_OUTDATED_LOCKFILE`, pip "Could not find a version that satisfies", `yarn.lock` / `poetry.lock` / `uv.lock` out of date, Gradle "Could not resolve all files for configuration", Bundler "add the updated Gemfile.lock" / "could not find compatible versions", `missing go.sum entry` / "verifying module: checksum mismatch", `Cargo.lock needs to be updated` / "failed to select a version".

**Not this:** a missing `NODE_AUTH_TOKEN` before publish (`env`), a test that fails after a clean install (`test`).

**Fixtures:** [`npm-peer-eresolve`](../fixtures/gha/npm-peer-eresolve), [`npm-ci-lockfile-drift`](../fixtures/gha/npm-ci-lockfile-drift), [`pnpm-outdated-lockfile`](../fixtures/gha/pnpm-outdated-lockfile), [`pip-version-unsatisfied`](../fixtures/gha/pip-version-unsatisfied), [`yarn-lockfile-out-of-date`](../fixtures/gha/yarn-lockfile-out-of-date), [`poetry-lock-out-of-date`](../fixtures/gha/poetry-lock-out-of-date), [`uv-lock-needs-update`](../fixtures/gha/uv-lock-needs-update), [`gradle-configuration-unresolved`](../fixtures/gha/gradle-configuration-unresolved), [`bundler-lockfile-out-of-date`](../fixtures/gha/bundler-lockfile-out-of-date), [`go-sum-checksum-mismatch`](../fixtures/gha/go-sum-checksum-mismatch), [`cargo-lock-needs-update`](../fixtures/gha/cargo-lock-needs-update). A tie with `AssertionError` stays `unknown` (`poetry-lock-and-assertion-unknown`). Cache `EACCES` tied with a lockfile stays `unknown` (`cache-eacces-and-lockfile-unknown`). A corrupt `actions/cache` restore outranks the lockfile (`actions-cache-restore-corrupt`, `infra`). `pnpm-lock.yaml` "not up to date" is deps (`pnpm-lock-not-up-to-date-deps`). A `continue-on-error` step does not hide a later lockfile error (`continue-on-error-lockfile-deps`).

**Minimal next step:** align the versions in the evidence, or commit an updated lockfile. Do not lead with `--force` or `--legacy-peer-deps`. Do not replace `npm ci` with `npm install` in CI as the fix.

## permissions

The token, role, or `permissions:` block refused an API. Typical shape: HTTP 403, "Resource not accessible by integration", or `git` denying `github-actions[bot]`.

**Signals:** "Resource not accessible by integration", "Permission to … denied", "requested URL returned error: 403", `HttpError` 403, "does not have permission", "not granted contents:" / `issues:` / `pull-requests:` / `id-token:`. A lone "Refusing to force-push" stays under the threshold (`force-push-refusal-only-unknown`).

**Not this:** a filesystem `EACCES` inside a build script with no GitHub API involved (often `infra` or `env` once the path is known), a missing secret value (`env`).

**Fixtures:** [`gha-token-integration-403`](../fixtures/gha/gha-token-integration-403), [`git-push-permission-denied`](../fixtures/gha/git-push-permission-denied), [`id-token-permission-denied`](../fixtures/gha/id-token-permission-denied), [`bare-http-403`](../fixtures/gha/bare-http-403), [`oidc-assume-role-denied`](../fixtures/gha/oidc-assume-role-denied), [`registry-pull-auth-denied`](../fixtures/gha/registry-pull-auth-denied). `pull access denied` is permissions. `no such host` without an auth line is `infra`. Both together stay `unknown` (`registry-auth-and-egress-unknown`).

**Minimal next step:** name the narrowest missing scope. Do not switch the job to a personal access token. Do not force-push.

## infra

The host fell over. Heap OOM, runner disk full, process killed, runner shutdown. The assertion is not the bug.

**Signals:** "JavaScript heap out of memory", "Reached heap limit", `OOMKilled`, "No space left on device", "disk quota exceeded", "runner process was killed", "Cannot connect to the Docker daemon", registry pull `dial tcp: lookup` / "no such host" / "network is unreachable" / "TLS handshake timeout" / "i/o timeout" / "egress blocked", DNS `getaddrinfo` / "Temporary failure in name resolution" / "Could not resolve host", `Failed to restore cache`. A bare cache `EACCES` stays under the threshold. An "out of memory" line tied with "does not have permission" stays `unknown` (`oom-and-permission-unknown`). Egress blocked tied with `remote: permission to … denied` stays `unknown` (`egress-and-permission-unknown`).

**Not this:** a test timeout that passed on rerun (`flake`), checkout certificate verification (`flake`), `pull access denied` with no DNS or egress line (`permissions`), an `npm` resolver error (`deps`).

**Fixtures:** [`node-heap-oom`](../fixtures/gha/node-heap-oom), [`runner-disk-full`](../fixtures/gha/runner-disk-full), [`generic-oom-without-heap`](../fixtures/gha/generic-oom-without-heap), [`runner-killed-exit-137`](../fixtures/gha/runner-killed-exit-137), [`docker-build-disk-full`](../fixtures/gha/docker-build-disk-full), [`docker-daemon-unavailable`](../fixtures/gha/docker-daemon-unavailable), [`mcr-pull-egress-blocked`](../fixtures/gha/mcr-pull-egress-blocked), [`ghcr-pull-io-timeout`](../fixtures/gha/ghcr-pull-io-timeout), [`dns-name-resolution-infra`](../fixtures/gha/dns-name-resolution-infra), [`actions-cache-restore-corrupt`](../fixtures/gha/actions-cache-restore-corrupt), [`kernel-oom-killed-infra`](../fixtures/gha/kernel-oom-killed-infra), [`self-hosted-runner-offline-infra`](../fixtures/gha/self-hosted-runner-offline-infra), [`windows-filename-too-long-infra`](../fixtures/gha/windows-filename-too-long-infra), [`runner-arch-mismatch-infra`](../fixtures/gha/runner-arch-mismatch-infra), [`docker-layer-cache-missing-infra`](../fixtures/gha/docker-layer-cache-missing-infra). A line that is only `Killed` is infra. "failed to compute cache key" is not a pytest line.

**Minimal next step:** one resource change (heap cap, fewer artifacts, larger runner). One rerun after a shutdown is reasonable. A second identical host failure stops the loop.

## unknown

The log does not carry a v0 signal strong enough to pick a category, or two categories tie. This is a valid answer.

**Signals:** a bare "Process completed with exit code 1", or a cancel line with no other signal. A weak hit that stays under the score threshold is still `unknown`. Two categories at the same score at or above 6 are also `unknown`. `canceled-step-unknown` matches nothing in v0 on purpose.

**Not this:** a place to hide a guess. Do not invent an eighth category in the report. Do not treat a filesystem `EACCES` as `permissions`, and do not treat a below-threshold force-push refusal as permission to force-push.

**Fixtures:** [`bare-exit-unknown`](../fixtures/gha/bare-exit-unknown), [`canceled-step-unknown`](../fixtures/gha/canceled-step-unknown), [`timeout-and-assertion-unknown`](../fixtures/gha/timeout-and-assertion-unknown), [`empty-token-and-permission-unknown`](../fixtures/gha/empty-token-and-permission-unknown), [`force-push-refusal-only-unknown`](../fixtures/gha/force-push-refusal-only-unknown), [`cache-eacces-unknown`](../fixtures/gha/cache-eacces-unknown), [`concurrency-cancel-unknown`](../fixtures/gha/concurrency-cancel-unknown), [`poetry-lock-and-assertion-unknown`](../fixtures/gha/poetry-lock-and-assertion-unknown), [`oom-and-permission-unknown`](../fixtures/gha/oom-and-permission-unknown), [`oidc-role-and-empty-arn-unknown`](../fixtures/gha/oidc-role-and-empty-arn-unknown), [`shard-retry-only-unknown`](../fixtures/gha/shard-retry-only-unknown), [`checkout-tls-and-assertion-unknown`](../fixtures/gha/checkout-tls-and-assertion-unknown), [`dataset-and-assertion-unknown`](../fixtures/gha/dataset-and-assertion-unknown), [`egress-and-permission-unknown`](../fixtures/gha/egress-and-permission-unknown), [`checkout-hook-only-unknown`](../fixtures/gha/checkout-hook-only-unknown), [`multi-job-green-noise-unknown`](../fixtures/gha/multi-job-green-noise-unknown), [`registry-auth-and-egress-unknown`](../fixtures/gha/registry-auth-and-egress-unknown), [`healthcheck-and-assertion-unknown`](../fixtures/gha/healthcheck-and-assertion-unknown), [`cache-eacces-and-lockfile-unknown`](../fixtures/gha/cache-eacces-and-lockfile-unknown).

**Minimal next step:** ask for the failed step name and the lines above the exit. Do not refactor while you wait.

## Added in 0.13.0

A job line "exceeded the maximum execution time" is `infra` (`job-max-execution-time-infra`). A step line "has timed out after N minutes" is `flake` (`step-timeout-minutes-flake`). Those two tied with `AssertionError` stay `unknown` (`job-timeout-and-assertion-unknown`). Exit code 137 with no other host phrase is `infra` (`bare-exit-137-infra`). "no runners available" is `infra` (`no-runners-available-infra`). A missing Playwright browser executable is `deps` (`playwright-browser-missing-deps`); a failed browser download is `flake` (`playwright-browser-download-flake`, `cypress-binary-download-flake`). A Terraform provider lock mismatch is `deps` (`terraform-provider-lock-deps`), not a state lock. `ERR_PNPM_TARBALL_INTEGRITY` is `deps` (`pnpm-tarball-integrity-deps`). An LFS budget line is `permissions` (`git-lfs-budget-exceeded-permissions`). A git-lfs smudge failure with no rate limit and no budget line is `env` (`git-lfs-smudge-failed-env`). A matrix job canceled because a sibling failed, with no assertion, stays `unknown` (`matrix-cancel-sibling-unknown`).

## Added in 0.14.0

A Docker build context that is larger than the limit is `infra` (`docker-build-context-too-large-infra`). BuildKit `cache export failed` is `infra` (`buildx-cache-export-failed-infra`). `context deadline exceeded` on a Helm upgrade or a collector scrape is `flake` (`helm-upgrade-deadline-flake`, `otel-collector-scrape-timeout-flake`). A NuGet 401 is `permissions` (`nuget-feed-unauthorized-permissions`). A NuGet 503 is `flake` (`nuget-feed-503-flake`), not a missing package. crates.io `429 Too Many Requests` is `flake` (`cargo-crates-io-rate-limit-flake`). A yanked crate version is `deps` (`cargo-crate-yanked-deps`). Missing Xcode DerivedData is `env` (`xcode-derived-data-missing-env`). `vm.max_map_count` too low is `infra` (`elasticsearch-vm-max-map-count-infra`). Redis `LOADING` is `flake` (`redis-loading-not-ready-flake`). A missing Codecov token is `env` (`codecov-token-missing-env`). A coverage upload timeout is `flake` (`codecov-upload-timeout-flake`). Codecov `401 Invalid token` is `permissions` (`codecov-token-rejected-permissions`). Windows `PathTooLongException` is `infra` (`windows-path-too-long-infra`). `com.apple.quarantine` is `permissions` (`macos-quarantine-blocked-permissions`). System Integrity Protection is `infra` (`macos-sip-blocked-infra`). The word Dependabot with no resolver line stays `unknown` (`dependabot-word-only-unknown`).

## Added in 0.15.0

`not authorized to perform` or `AccessDeniedException` is `permissions` (`ecr-pull-denied-permissions`, `codeartifact-token-denied-permissions`). CodeArtifact `429` is `flake` (`codeartifact-429-flake`). Artifactory `403` is `permissions` (`artifactory-403-permissions`). Artifactory `429` is `flake` (`artifactory-429-flake`). A `go.sum database checksum mismatch` is `deps` (`gosum-database-mismatch-deps`). A Go proxy context deadline is `flake` (`go-proxy-deadline-flake`). Packagist `429` is `flake` (`packagist-429-flake`). A yanked gem is `deps` (`gem-version-yanked-deps`). Rubygems `503` is `flake` (`rubygems-503-flake`). Deno `--allow-net` is `permissions` (`deno-permission-prompt-permissions`). `sparse-checkout` missing a path is `env` (`sparse-checkout-miss-env`). SELinux `avc: denied` and AppArmor `DENIED` are `infra` (`selinux-avc-denied-infra`, `apparmor-denied-infra`). A `packageManager` field mismatch is `env` (`corepack-packagemanager-mismatch-env`). Conflicting `getStaticPaths` is `test` (`next-static-path-collision-test`). A concurrency cancel names itself and stays under the threshold (`concurrency-cancel-unknown`). A matrix cancel because a sibling failed stays with no signal (`matrix-cancel-sibling-unknown`).

## Added in 0.16.0

`ImagePullBackOff` is `infra` (`kube-image-pull-backoff-infra`). `CrashLoopBackOff` is `test` (`kube-crashloop-backoff-test`). A Gradle or Maven wrapper checksum mismatch is `deps` (`gradle-wrapper-checksum-deps`, `maven-wrapper-checksum-deps`). SQLite `database is locked` is `flake` (`sqlite-database-locked-flake`). Postgres `too many clients already` is `infra` (`postgres-too-many-clients-infra`). An Android Gradle plugin that is not compatible with Gradle is `env` (`android-gradle-plugin-mismatch-env`). A missing Ansible vault password file is `env` (`ansible-vault-password-missing-env`). CDN error code 520 is `flake` (`cloudflare-520-flake`). A submodule with no URL is `env` (`git-submodule-not-initialized-env`). A Hugging Face 429 is `flake` (`huggingface-rate-limit-flake`). A gated model is `permissions` (`huggingface-gated-model-permissions`). `SolvePackageNotFound` and `PackagesNotFoundError` are `deps` (`pixi-solve-not-found-deps`, `conda-package-not-found-deps`). Bazel analysis failure is `test` (`bazel-analysis-failed-test`). A Bazel repository fetch failure is `flake` (`bazel-fetch-failed-flake`). Terraform state lock was already `flake` (`terraform-state-lock-flake`).

## Added in 0.17.0

`cannot connect to Podman` is `infra` (`podman-socket-unavailable-infra`). `port is already allocated` is `infra` (`testcontainers-port-conflict-infra`). A Kafka broker that is not available is `flake` (`kafka-broker-not-ready-flake`). MongoDB authentication failed is `permissions` (`mongodb-auth-failed-permissions`). A MongoDB connection refusal is `flake` (`mongodb-connection-refused-flake`). A missing `SENTRY_AUTH_TOKEN` is `env` (`sentry-token-missing-env`). A failed quality gate is `test` (`sonar-quality-gate-failed-test`). A rejected `sonar.token` is `permissions` (`sonar-token-rejected-permissions`). A missing Coveralls repo token is `env` (`coveralls-token-missing-env`). Publish that requires provenance is `permissions` (`npm-provenance-required-permissions`). GitHub Packages 403 is `permissions` (`github-packages-publish-403-permissions`). An unpublished package version is `deps` (`github-packages-unpublished-deps`). A corrupt mypy cache is `infra` (`mypy-cache-corrupt-infra`). A Prettier check failure is `test` (`prettier-check-drift-test`). A remote cache unauthorized line is `permissions` (`turbo-remote-unauthorized-permissions`). A remote cache that could not be reached is `infra` (`nx-remote-cache-unreachable-infra`). An Earthly or Dagger engine disconnect is `infra` (`earthly-daemon-unavailable-infra`, `dagger-engine-disconnect-infra`).

## Added in 0.18.0

A Slack webhook `404 no_service` is `env` (`slack-webhook-404-env`). Slack `ratelimited` is `flake` (`slack-rate-limit-flake`). A missing `DD_API_KEY` or `NEW_RELIC_LICENSE_KEY` is `env` (`datadog-api-key-missing-env`, `newrelic-license-missing-env`). A locked Pulumi stack is `flake` (`pulumi-stack-locked-flake`). Pulumi not logged in is `env` (`pulumi-login-missing-env`). Workers deploy not authorized is `permissions` (`cloudflare-workers-auth-permissions`), distinct from CDN 520. A missing Vercel token is `env` (`vercel-token-missing-env`). A failed `next build` or Netlify building-site stage is `test` (`vercel-build-failed-test`, `netlify-build-failed-test`). Netlify authentication failed is `permissions` (`netlify-auth-failed-permissions`). A dirty database version is `env` (`laravel-migrate-dirty-env`). Conflicting Django migrations are `test` (`django-migrate-conflict-test`). Prisma drift is `env` (`prisma-migrate-drift-env`). Prisma `P1001` is `flake` (`prisma-p1001-flake`). An unmerged GraphQL schema is `test` (`graphql-schema-conflict-test`). A missing Chromatic or Percy token is `env` (`visual-snapshot-token-missing-env`). `wasm-ld` failure is `test` (`wasm-link-failed-test`).

## How to extend it

Add a fixture first, then a signal, then a sentence in this file and in [`skills/ci-doctor/references/taxonomy.md`](../skills/ci-doctor/references/taxonomy.md). Renaming an id is a taxonomy version change, not a drive-by edit. See [CONTRIBUTING.md](../CONTRIBUTING.md).
