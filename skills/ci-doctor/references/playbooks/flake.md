# flake

A result that moved across attempts on the same commit. Quote the timeout or the "passed on rerun" line before you edit product code.

## When to follow this

The CLI category is `flake`, or you confirmed a flake signal the CLI ranked first: "suspected flake", "exceeded timeout of N", "timeout of N ms exceeded", "passed on the previous run" / "automatic rerun", "intermittent", "retry N of M".

Corpus: `jest-timeout-flake`, `registry-timeout-rerun-flake`, `playwright-timeout-flake`, `cypress-timeout-flake`.

## Near misses

| What you see | What to do |
| --- | --- |
| `AssertionError` and "Exceeded timeout of N" at the same score (`timeout-and-assertion-unknown`) | The CLI returns `unknown` with alternates `flake` and `test`. Do not pick. Ask which line repeats on a clean rerun. |
| The same assertion, same expected and received, on every attempt | Reclassify as `test`. That reclassification spends an attempt if you then edit. |
| "JavaScript heap out of memory" or "No space left on device" | That is `infra`, even if a test timed out afterwards. |
| Registry `ETIMEDOUT` that passed on the automatic rerun (`registry-timeout-rerun-flake`) | Still flake. Do not pin a new version and do not replace `npm ci` with `npm install`. |
| Only "retry N of M" or only the word "flaky", and the CLI stayed under the threshold | Stay on `unknown`. One weak word is not a fix license. |

## Recipe

1. Quote the line that moved: the timeout, the rerun, or the intermittent sentence. Include the test or step name if the log has one.
2. Name the suspected shared state in one sentence (clock, network, queue, modal, registry). Do not invent a stack trace that is not in the evidence.
3. Propose one change:
   - a deterministic wait or an event the test already exposes, or
   - a fake clock, or
   - isolating the shared state (unique temp dir, no global queue).
4. Do not raise the timeout in that same attempt. A timeout bump is a separate hypothesis, and only after the deterministic change failed.
5. If the only evidence is "passed on the automatic rerun" and there is no test name, do not edit product code. Report flake and offer one rerun as evidence, not as a fix.

## Verify

An attempt starts when you apply the change or ask for a rerun that tests this hypothesis. Reading the log does not.

- Same failure: the same test name and the same timeout or assertion line.
- New failure: a stable `AssertionError` or an `infra` host line. Stop calling it flake. The next edit, if you make one, is the next attempt.
- For a fixture, `python3 scripts/diagnose.py --fixture <id>` only checks the report. It does not prove the flake is gone.
- If the user agrees, rerun the single test more than once. One green rerun after a code change is weak. Two identical reds means the hypothesis was wrong.

## Stop

- Two attempts are recorded.
- Two reruns fail the same way. Reclassify toward `test` or `infra`, then stop if that reclassification was the second attempt.
- The only remaining idea is "raise the timeout and rewrite the test". Those are two hypotheses. Do not stack them. Stop and say so.
- You cannot name the shared state from the log. Ask for it. Do not guess a product bug.

## 中文

先引用会变动的那一行（超时、重跑、intermittent），再提出一个确定性等待、假时钟，或隔离共享状态。同一次尝试里不要同时加超时。`timeout-and-assertion-unknown` 是打平，保持 `unknown`，不要选更好改的一边。验证看测试名和同一行是否复现；连续两次相同失败就改判 `test` 或 `infra` 并停止。fixture 上重跑 CLI 只核对报告。
