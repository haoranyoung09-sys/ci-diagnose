# deps

The resolver or the lockfile failed before the suite could mean anything.

## When to follow this

The CLI category is `deps`. Signals include `ERESOLVE`, "unable to resolve dependency tree", "Conflicting peer dependency", "Could not resolve dependency", `package.json` and `package-lock.json` out of sync, "Missing: … from lock file", `ERR_PNPM_OUTDATED_LOCKFILE`, "Could not find a version that satisfies" (pip), and `yarn.lock` out of date.

Corpus: `npm-peer-eresolve`, `npm-ci-lockfile-drift`, `pnpm-outdated-lockfile`, `pip-version-unsatisfied`, `yarn-lockfile-out-of-date`.

## Near misses

| What you see | What to do |
| --- | --- |
| `NODE_AUTH_TOKEN is empty` with no resolver error | `env`. Do not rewrite the lockfile. |
| A test summary after a clean install | `test`. |
| Only the words "peer dep", and the CLI is under the threshold | `unknown`. Ask for the resolver block. |
| `ERESOLVE` leading, with a stray assertion in `alternates` | Stay on `deps` for this attempt. Do not also edit the test. |

## Recipe

1. Quote the two constraints, not a whole tree. Examples: the root package and the peer; the `package.json` range and the lockfile entry; the pip requirement that could not be satisfied; the `yarn.lock` path the log names.
2. Pick one of these, matching the evidence:
   - **Peer / `ERESOLVE`:** choose one range that satisfies the peer named in the log. Do not start with `--force` or `--legacy-peer-deps`.
   - **`npm ci` out of sync:** update `package-lock.json` and commit it. npm's hint to run `npm install` is how you refresh the lockfile locally. It is not a reason to replace `npm ci` in the workflow.
   - **pnpm:** commit an updated `pnpm-lock.yaml`. Do not drop `--frozen-lockfile` in CI to hide the drift.
   - **yarn:** commit an updated `yarn.lock`. Do not delete the lockfile. Do not switch the job to `npm install`.
   - **pip:** name the requirement that has no matching distribution. Change that pin, or the index the log already uses. Do not `pip install --upgrade` the world.
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

只引用冲突的两侧，或 pip 找不到的那一个要求。锁文件不同步就更新并提交对应的 lock 文件，不要把 CI 里的 `npm ci` / 冻结安装改成宽松安装。一次不要顺手升级无关包。安装步骤重跑后如果换了一对新约束，展示两对；这是第二次就停止。上游发版才能解开时，报告约束并停止。
