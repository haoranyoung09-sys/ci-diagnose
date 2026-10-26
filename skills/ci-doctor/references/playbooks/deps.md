# deps

The resolver or the lockfile failed before the suite could mean anything.

## When to follow this

The CLI category is `deps`. Signals include `ERESOLVE`, "unable to resolve dependency tree", "Conflicting peer dependency", "Could not resolve dependency", `package.json` and `package-lock.json` out of sync, "Missing: … from lock file", `ERR_PNPM_OUTDATED_LOCKFILE`, "Could not find a version that satisfies" (pip), `yarn.lock` out of date, `poetry.lock` out of date, `uv.lock needs to be updated`, and Gradle "Could not resolve all files for configuration".

Corpus: `npm-peer-eresolve`, `npm-ci-lockfile-drift`, `pnpm-outdated-lockfile`, `pip-version-unsatisfied`, `yarn-lockfile-out-of-date`, `poetry-lock-out-of-date`, `uv-lock-needs-update`, `gradle-configuration-unresolved`.

## Near misses

| What you see | What to do |
| --- | --- |
| `NODE_AUTH_TOKEN is empty` with no resolver error | `env`. Do not rewrite the lockfile. |
| A test summary after a clean install | `test`. |
| Only the words "peer dep", and the CLI is under the threshold | `unknown`. Ask for the resolver block. |
| `ERESOLVE` leading, with a stray assertion in `alternates` | Stay on `deps` for this attempt. Do not also edit the test. |
| `poetry.lock` tied with `AssertionError` (`poetry-lock-and-assertion-unknown`) | Stay `unknown`. Do not update the lockfile and the test in one attempt. |

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

只引用冲突的两侧，或 pip / Gradle 找不到的那一个模块。`poetry.lock`、`uv.lock` 不同步就提交更新后的锁文件，不要在 CI 里关掉冻结安装。`poetry-lock-and-assertion-unknown` 是打平，不要同时改锁文件和测试。一次不要顺手升级无关包。第二次仍是新的约束对就停止。
