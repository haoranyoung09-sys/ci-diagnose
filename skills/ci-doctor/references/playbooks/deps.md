# deps

The resolver or the lockfile failed before the suite could mean anything.

## When to follow this

The CLI category is `deps`. Signals include `ERESOLVE`, "unable to resolve dependency tree", "Conflicting peer dependency", "Could not resolve dependency", `package.json` and `package-lock.json` out of sync, "Missing: … from lock file", `ERR_PNPM_OUTDATED_LOCKFILE`, "Could not find a version that satisfies" (pip), `yarn.lock` / `poetry.lock` / `uv.lock` out of date, Gradle "Could not resolve all files for configuration", Bundler "add the updated Gemfile.lock" / "could not find compatible versions", `missing go.sum entry` / "verifying module: checksum mismatch", and `Cargo.lock needs to be updated` / "failed to select a version".

Corpus: `npm-peer-eresolve`, `npm-ci-lockfile-drift`, `pnpm-outdated-lockfile`, `pip-version-unsatisfied`, `yarn-lockfile-out-of-date`, `poetry-lock-out-of-date`, `uv-lock-needs-update`, `gradle-configuration-unresolved`, `bundler-lockfile-out-of-date`, `go-sum-checksum-mismatch`, `cargo-lock-needs-update`.

## Near misses

| What you see | What to do |
| --- | --- |
| `NODE_AUTH_TOKEN is empty` with no resolver error | `env`. Do not rewrite the lockfile. |
| A test summary after a clean install | `test`. |
| Only the words "peer dep", and the CLI is under the threshold | `unknown`. Ask for the resolver block. |
| `ERESOLVE` leading, with a stray assertion in `alternates` | Stay on `deps` for this attempt. Do not also edit the test. |
| `poetry.lock` tied with `AssertionError` (`poetry-lock-and-assertion-unknown`) | Stay `unknown`. Do not update the lockfile and the test in one attempt. |
| Cache `EACCES` and a lockfile line together (`cache-eacces-and-lockfile-unknown`) | Stay `unknown`. Do not chmod the cache and rewrite the lockfile in one attempt. |
| `Failed to restore cache` above a lockfile complaint (`actions-cache-restore-corrupt`) | That is `infra`. Do not start with the lockfile. |
| `pnpm-lock.yaml` is "not up to date" (`pnpm-lock-not-up-to-date-deps`) | Deps. Commit the lockfile. Do not drop `--frozen-lockfile`. |
| "Suspected flake" only inside a `continue-on-error` step, then a lockfile error (`continue-on-error-lockfile-deps`) | Deps. Ignore that step. Do not chase the flake. |
| Maven "Could not resolve dependencies for project" (`maven-dependencies-unresolved-deps`) | Deps. Quote the missing artifact. Do not skip tests. |
| SwiftPM "Could not resolve package dependencies" or CocoaPods "compatible versions for pod" (`swiftpm-package-unresolved-deps`, `cocoapods-pod-conflict-deps`) | Deps. Align that one requirement. |
| NuGet `NU1102` (`nuget-package-not-found-deps`) | Deps. The version is not in the feed named in the log. |

## Recipe

1. Quote the two constraints, not a whole tree. Examples: the root package and the peer; the `package.json` range and the lockfile entry; the pip requirement that could not be satisfied; the `yarn.lock` path the log names.
2. Pick one of these, matching the evidence:
   - **Peer / `ERESOLVE`:** choose one range that satisfies the peer named in the log. Do not start with `--force` or `--legacy-peer-deps`.
   - **`npm ci` out of sync:** update `package-lock.json` and commit it. npm's hint to run `npm install` is how you refresh the lockfile locally. It is not a reason to replace `npm ci` in the workflow.
   - **pnpm:** commit an updated `pnpm-lock.yaml`. Do not drop `--frozen-lockfile` in CI to hide the drift.
   - **yarn:** commit an updated `yarn.lock`. Do not delete the lockfile. Do not switch the job to `npm install`.
   - **pip:** name the requirement that has no matching distribution. Change that pin, or the index the log already uses. Do not `pip install --upgrade` the world.
   - **poetry:** commit an updated `poetry.lock`. Do not delete it to hide the drift.
   - **uv:** commit an updated `uv.lock`. Do not drop `--frozen` in CI.
   - **Gradle:** quote the configuration (`:app:compileClasspath`) and the missing module. Do not `--refresh-dependencies` the whole build as the only change.
   - **Bundler:** commit an updated `Gemfile.lock`. Do not drop `--deployment` in CI to hide the drift (`bundler-lockfile-out-of-date`).
   - **Go:** add the missing `go.sum` entry with `go mod download` or `go mod tidy` locally and commit `go.sum`. Do not pass `-mod=mod` in CI to skip the checksum (`go-sum-checksum-mismatch`).
   - **Cargo:** commit an updated `Cargo.lock`. Do not drop `--locked` in CI (`cargo-lock-needs-update`).
3. Do not bump unrelated packages in the same attempt.

## Verify

- Re-run the install job once. That is attempt 1.
- Same failure: the same two constraints, or the same missing distribution.
- New failure: a different pair of constraints. Show both pairs. Editing for the new pair is attempt 2.
- The suite has not started yet. Do not "verify" by editing a test.
- Fixture check only confirms the saved log's label.

## Stop

- A conflict you cannot satisfy without an upstream release. Report the two constraints and stop.
- Two resolver failures with different constraints. Do not open a third bump.
- You are about to add `--force`, `--legacy-peer-deps`, or a deleted lockfile. Those hide the drift. Stop and say which constraint is still open.

## 中文

只引用冲突的两侧，或 pip / Gradle / Bundler / Cargo 找不到的那一个模块。`poetry.lock`、`uv.lock`、`Gemfile.lock`、`Cargo.lock` 不同步就提交更新后的锁文件，不要在 CI 里关掉冻结安装。`go.sum` 缺条目或校验和不匹配时提交补齐后的 `go.sum`，不要在 CI 里用 `-mod=mod` 跳过。`poetry-lock-and-assertion-unknown` 是打平，不要同时改锁文件和测试。缓存 `EACCES` 加锁文件（`cache-eacces-and-lockfile-unknown`）也是打平。`Failed to restore cache`（`actions-cache-restore-corrupt`）是 `infra`，不要先改锁文件。Maven、SwiftPM、CocoaPods、NuGet 解析失败是 deps，引用缺的那一个模块。`poetry-lock-and-assertion-unknown` 是打平，不要同时改锁文件和测试。一次不要顺手升级无关包。第二次仍是新的约束对就停止。
