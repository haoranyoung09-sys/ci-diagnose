# unknown

No v0 signal was strong enough, or two categories tied. Say that plainly. `unknown` is a result, not a failure of the skill.

## When to follow this

The CLI category is `unknown`. That happens when nothing reaches the score threshold (6), or when two categories tie at or above it. Confidence stays low. Do not round it up.

Corpus:

| Fixture | Why it is unknown |
| --- | --- |
| `bare-exit-unknown` | Exit code 1 and a below-threshold exit phrase. |
| `canceled-step-unknown` | Canceled before any step log. No v0 signal. |
| `timeout-and-assertion-unknown` | Tie: `AssertionError` and "Exceeded timeout of N". Alternates `flake` and `test`. |
| `empty-token-and-permission-unknown` | Tie: `NODE_AUTH_TOKEN is empty` and "does not have permission". Alternates `env` and `permissions`. |
| `force-push-refusal-only-unknown` | "Refusing to force-push" is below the threshold. It is a guardrail, not a win. |
| `cache-eacces-unknown` | `EACCES` on a runner cache path. Not a GitHub token 403. |
| `concurrency-cancel-unknown` | Concurrency group canceled the run. No v0 signal. |
| `poetry-lock-and-assertion-unknown` | Tie: poetry lockfile and `AssertionError`. Alternates `deps` and `test`. |
| `oom-and-permission-unknown` | Tie: "out of memory" and "does not have permission". Alternates `infra` and `permissions`. |
| `oidc-role-and-empty-arn-unknown` | Tie: `AWS_ROLE_ARN is empty` and "does not have permission". Alternates `env` and `permissions`. |
| `shard-retry-only-unknown` | Only "retry N of M" on a matrix shard. Under the threshold. |
| `checkout-tls-and-assertion-unknown` | Tie: checkout certificate verification and `AssertionError`. Alternates `flake` and `test`. |
| `dataset-and-assertion-unknown` | Tie: external dataset download and `AssertionError`. Alternates `flake` and `test`. |
| `egress-and-permission-unknown` | Tie: registry egress blocked and `remote: permission to … denied`. Alternates `infra` and `permissions`. |
| `registry-auth-and-egress-unknown` | Tie: registry authentication denied and egress blocked. Alternates `infra` and `permissions`. |
| `checkout-hook-only-unknown` | A hook cannot run, and the log has no checkout or certificate line. Under the threshold. |
| `multi-job-green-noise-unknown` | The only taxonomy phrase is on a job that succeeded. The failed job has no signal. |

## Near misses

Do not rescue a tie by picking the alternate you know how to edit. Do not promote `force-push-refusal-only-unknown` into `permissions` and then force-push. Do not promote `cache-eacces-unknown` into `permissions` and grant `contents: write`.

If `truncated: true`, you do not have the tail of the log. Ask for the failed step, not the whole multi-megabyte file.

## Recipe

1. State the category `unknown`, the confidence, and why: "tie between A and B" or "no signal reached 6".
2. Quote at most the evidence lines the CLI printed. If the evidence is only the last line, say that it is a fallback, not a classification.
3. Ask for one missing piece, matched to the fixture shape:
   - **Bare exit or cancel:** the failed step name and the 30 lines above the exit or cancel.
   - **Tie:** one rerun, or the lines that show which signal is stable. Do not edit either side yet.
   - **Force-push line only:** the git 403 or the "not granted contents:" line, if it exists. Do not push.
   - **`EACCES` on a path:** whether that path is a GitHub API or a local directory. Do not grant a token scope for a local directory.
   - **Concurrency cancel:** whether a newer run on the same group was the one that should finish. Do not rerun in a loop.
   - **Shard retry only:** the suspected-flake or "passed on rerun" line, if it exists. Do not edit the matrix yet.
   - **Checkout TLS or a dataset host tied with an assertion:** which line repeats on a clean rerun. Do not disable certificate verification and do not edit the assertion yet.
   - **Egress tied with a git permission denial:** which failure remains if the other step is skipped. Do not open the network and grant a scope together.
4. Do not propose a drive-by refactor, a dependency bump, or a permission widening while you wait.

## Verify

There is nothing to verify until a classifiable log exists. Do not spend a fix attempt on a guess. `attempt: 0 of 2` is the honest report.

A fixture re-run confirms the label is still `unknown`. It is not a verification of a fix.

## Stop

Stop immediately after you have asked for the missing lines. A guessed category does not count as progress and does not unlock an attempt.

If the user later pastes the missing lines, start the workflow again from classify. The attempt counter starts only when a hypothesis is tested.

## 中文

`unknown` 是合法结论。打平（超时对断言、空 token 对 permission、poetry 锁文件对断言、内存耗尽对 permission、空角色 ARN 对 permission、checkout 证书校验对断言、外部数据集对断言、egress 对 git permission）不要选更好改的一类。并发组取消（`concurrency-cancel-unknown`）只要更新的那一次运行是否才是该完成的，不要循环重跑。矩阵分片只有 `retry N of M` 时不要改矩阵。force-push 拒绝低于阈值。缓存路径 `EACCES` 不是 GitHub 403。在分类清楚之前不要改代码，尝试次数保持 0。
