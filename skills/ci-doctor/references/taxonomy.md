# Taxonomy v0 (skill reference)

Ids: `flake`, `env`, `test`, `deps`, `permissions`, `infra`, `unknown`.

The CLI in `scripts/diagnose.py` is the smoke oracle. It scores the signals below, picks the leader when the score is at least 6, and returns `unknown` under that threshold or on a tie. If you edit a signal here, edit the rule and [docs/taxonomy.md](../../../docs/taxonomy.md) in the same change. When the full repo is not on disk, this file is enough to classify by hand.

Confidence from the CLI: `high` (≥ 0.80), `medium` (≥ 0.60), `low`. Repeat that level. Do not round it up to a merge decision.

| id | Pick it when | Do not pick it when | Fixture |
| --- | --- | --- | --- |
| `flake` | Timeout, "timeout of N ms exceeded", "suspected flake", passed on rerun, intermittent, retry N of M | The assertion fails the same way every time, or it ties with `AssertionError` | `jest-timeout-flake`, `registry-timeout-rerun-flake`, `playwright-timeout-flake`, `cypress-timeout-flake` |
| `env` | A named variable, action input, or secret name is unset or empty | The token is present and GitHub returned 403, or the empty name ties with "does not have permission" | `missing-database-url`, `missing-node-auth-token`, `unset-api-base-url`, `secret-signing-key-missing`, `aws-region-undefined` |
| `test` | `FAIL` / `FAILED`, `--- FAIL:`, `AssertionError`, PHPUnit "Failed asserting that", RSpec `Failure/Error:`, cargo `test result: FAILED` | The suite never started, a timeout that passed on rerun, or a tie with that timeout | `npm-test-assertion`, `pytest-assertion`, `go-test-want-got`, `maven-surefire-assertion`, `phpunit-assert-failed`, `rspec-failure-error`, `cargo-test-result-failed` |
| `deps` | `ERESOLVE`, peer conflict, npm or pnpm or yarn lockfile out of date, pip "Could not find a version that satisfies" | `NODE_AUTH_TOKEN` is simply empty | `npm-peer-eresolve`, `npm-ci-lockfile-drift`, `pnpm-outdated-lockfile`, `pip-version-unsatisfied`, `yarn-lockfile-out-of-date` |
| `permissions` | Integration 403, `HttpError` 403, `permissions:` or `id-token:` not granted, remote rejected the push | A secret value was never provided, a filesystem `EACCES`, or only "Refusing to force-push" | `gha-token-integration-403`, `git-push-permission-denied`, `id-token-permission-denied`, `bare-http-403` |
| `infra` | Heap OOM, generic "out of memory", disk full, runner killed | A flaky timeout that passed on rerun, or `EACCES` on a cache directory with no host line | `node-heap-oom`, `runner-disk-full`, `generic-oom-without-heap`, `runner-killed-exit-137` |
| `unknown` | No signal clears the threshold, a bare cancel, or two categories tie | You want the report to sound decisive | `bare-exit-unknown`, `canceled-step-unknown`, `timeout-and-assertion-unknown`, `empty-token-and-permission-unknown`, `force-push-refusal-only-unknown`, `cache-eacces-unknown` |

If `alternates` is non-empty or confidence is not `high`, say which other category was close and which lines you used. Stay inside this list.
