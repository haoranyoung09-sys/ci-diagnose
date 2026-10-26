# flake

A result that moved across attempts on the same commit. Quote the timeout or the "passed on rerun" line before you edit product code.

## When to follow this

The CLI category is `flake`, or you confirmed a flake signal the CLI ranked first: "suspected flake", "exceeded timeout of N", "timeout of N ms exceeded", "passed on the previous run" / "automatic rerun", "intermittent", "retry N of M", checkout "SSL certificate problem" / "server certificate verification failed" / "unable to get local issuer certificate" / "The TLS connection was non-properly terminated", or "failed to download the external dataset" / "external host timed out".

Corpus: `jest-timeout-flake`, `registry-timeout-rerun-flake`, `playwright-timeout-flake`, `cypress-timeout-flake`, `matrix-shard-flake`, `docker-rate-limit-flake`, `checkout-tls-verify-flake`, `external-dataset-host-flake`.

## Near misses

| What you see | What to do |
| --- | --- |
| `AssertionError` and "Exceeded timeout of N" at the same score (`timeout-and-assertion-unknown`) | The CLI returns `unknown` with alternates `flake` and `test`. Do not pick. Ask which line repeats on a clean rerun. |
| The same assertion, same expected and received, on every attempt | Reclassify as `test`. That reclassification spends an attempt if you then edit. |
| "JavaScript heap out of memory" or "No space left on device" | That is `infra`, even if a test timed out afterwards. |
| Registry `ETIMEDOUT` that passed on the automatic rerun (`registry-timeout-rerun-flake`) | Still flake. Do not pin a new version and do not replace `npm ci` with `npm install`. |
| Only "retry N of M" or only the word "flaky", and the CLI stayed under the threshold (`shard-retry-only-unknown`) | Stay on `unknown`. A matrix shard number alone is not a fix license. |
| Matrix shard with "suspected flake" or "passed on the previous run" (`matrix-shard-flake`) | Flake. Quote the shard. Do not edit every matrix cell. |
| Docker Hub `toomanyrequests` that passed on the automatic rerun (`docker-rate-limit-flake`) | Flake. Do not pin a new base image in that attempt. |
| `actions/checkout` "SSL certificate problem", "server certificate verification failed", or "unable to get local issuer certificate" (`checkout-tls-verify-flake`) | Flake. One rerun is the check. Do not set `sslVerify: false`, do not change the ref, and do not rewrite git config in that attempt. If the same certificate line repeats, stop and ask whether the runner needs a custom CA. |
| "failed to download the external dataset" or "external host timed out" (`external-dataset-host-flake`) | Flake. Quote the host. Do not vendor a new dataset and do not edit the assertion in that attempt. |
| Checkout TLS or a dataset-host line tied with `AssertionError` (`checkout-tls-and-assertion-unknown`, `dataset-and-assertion-unknown`) | Stay on `unknown`. Do not pick the easier side. |
| `dial tcp: lookup`, "no such host", "egress blocked", or "TLS handshake timeout" on a registry pull | That is `infra` (`mcr-pull-egress-blocked`, `ghcr-pull-io-timeout`), not a checkout flake. |
| Checkout TLS failed and a later hook says it cannot run (`checkout-tls-hook-cascade-flake`) | Still flake. The hook is a cascade. Do not debug the hook script and do not disable `sslVerify`. |
| Only "cannot run … hook", no checkout or certificate line (`checkout-hook-only-unknown`) | Below the threshold. Stay `unknown`. Do not invent a TLS failure. |

## Recipe

1. Quote the line that moved: the timeout, the rerun, or the intermittent sentence. Include the test or step name if the log has one.
2. Name the suspected shared state in one sentence (clock, network, queue, modal, registry). Do not invent a stack trace that is not in the evidence.
3. Propose one change:
   - a deterministic wait or an event the test already exposes, or
   - a fake clock, or
   - isolating the shared state (unique temp dir, no global queue).
4. Do not raise the timeout in that same attempt. A timeout bump is a separate hypothesis, and only after the deterministic change failed.
5. If the only evidence is "passed on the automatic rerun" and there is no test name, do not edit product code. Report flake and offer one rerun as evidence, not as a fix.
6. Checkout TLS (`checkout-tls-verify-flake`): the one hypothesis is a single rerun of that checkout step. Do not disable certificate verification to make it pass.
7. External dataset or host (`external-dataset-host-flake`): name the host from the log. The one hypothesis is a rerun, or a fixture the repo already vendors. Do not add a new network retry loop and a new pin in the same attempt.
8. Checkout cascade (`checkout-tls-hook-cascade-flake`): quote the certificate line, then the hook line, and say the hook did not run because checkout did not finish. One rerun of checkout is the hypothesis.

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

先引用会变动的那一行（超时、重跑、intermittent、矩阵分片、checkout 证书校验、外部数据集主机）。`checkout-tls-verify-flake` 只重跑一次，不要关掉 `sslVerify`。证书失败之后 hook 跑不起来（`checkout-tls-hook-cascade-flake`）仍是 flake，不要去修 hook。只有 hook、没有 checkout 行（`checkout-hook-only-unknown`）低于阈值，保持 `unknown`。同一条证书错误再出现，就停下来问是不是自定义 CA。`external-dataset-host-flake` 引用主机名，不要在同一次尝试里改断言或换数据集。和 `AssertionError` 打平（`checkout-tls-and-assertion-unknown`、`dataset-and-assertion-unknown`）保持 `unknown`。`matrix-shard-flake` 只改共享状态，不要改每一个 matrix cell。只有 `retry N of M`（`shard-retry-only-unknown`）低于阈值，保持 `unknown`。Docker Hub `toomanyrequests` 且重跑已通过时，不要在同一次尝试里更换基础镜像。注册表 `no such host` 或 `egress blocked` 是 `infra`，不是这类。连续两次相同失败就改判并停止。
