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
4. Do not propose a drive-by refactor, a dependency bump, or a permission widening while you wait.

## Verify

There is nothing to verify until a classifiable log exists. Do not spend a fix attempt on a guess. `attempt: 0 of 2` is the honest report.

A fixture re-run confirms the label is still `unknown`. It is not a verification of a fix.

## Stop

Stop immediately after you have asked for the missing lines. A guessed category does not count as progress and does not unlock an attempt.

If the user later pastes the missing lines, start the workflow again from classify. The attempt counter starts only when a hypothesis is tested.

## 中文

`unknown` 是合法结论。打平（超时对断言、空 token 对 permission）不要选更好改的一类。只有 “Refusing to force-push” 时不要 force-push，也不要升格成 `permissions`。缓存路径上的 `EACCES` 不是 GitHub 403，不要授予 `contents: write`。取消或裸退出只要失败步骤名和退出前的日志。在此之前不要改代码，尝试次数保持 0。日志被截断时只要失败的那一个步骤。
