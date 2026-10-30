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
| Service container or Helm "health check timed out" / "failed to start" (`service-healthcheck-timeout-flake`, `helm-healthcheck-timeout-flake`) | Flake. One rerun is the check. Do not edit the app assertion and do not raise the health timeout in that attempt. |
| That health-check line tied with `AssertionError` (`healthcheck-and-assertion-unknown`) | Stay `unknown`. |
| External dataset host that failed on every recent attempt (`external-host-chronic-flake`) | Still `flake`. Do not spend both attempts on reruns. Mirror, cache, or use a file the repo already vendors. |
| Bare `toomanyrequests` or "pull rate limit" (`docker-pull-rate-limit-flake`) | Flake. Do not change the image tag. If the same log also says `pull access denied` (`registry-rate-and-auth-unknown`), stay `unknown`. |
| Cypress "Timed out retrying after Nms" (`cypress-retry-timeout-flake`) | Flake. One rerun. Do not raise the Cypress timeout in that attempt. |
| Git LFS "rate limit exceeded" while smudging (`git-lfs-rate-limit-flake`) | Flake. One rerun. Do not delete the LFS pointer. |
| Cargo "unable to update registry" or "spurious network error" (`cargo-registry-network-flake`) | Flake. Not a `Cargo.lock` edit. One rerun. |
| "Error acquiring the state lock" (`terraform-state-lock-flake`) | Flake. One rerun after the holder finishes. Do not force-unlock in that attempt. |
| "timed out waiting for the condition" (`kubectl-rollout-timeout-flake`) | Flake. One rerun. Do not widen RBAC in that attempt. |
| "exceeded a secondary rate limit" (`github-secondary-rate-limit-flake`) | Flake. Wait and rerun once. Not a new token. |
| `proxy.golang.org` returned 502 (`go-proxy-502-flake`) | Flake. One rerun. Do not edit `go.sum` for a 502. |
| `read ECONNRESET` and no assertion (`econnreset-flake`) | Flake. One rerun. If `AssertionError` is also present (`econnreset-and-assertion-unknown`), stay `unknown`. |

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
9. Service or Helm health check (`service-healthcheck-timeout-flake`, `helm-healthcheck-timeout-flake`): quote the service or the InProgress object. One rerun is the hypothesis. Do not change the chart and the test in that attempt.
10. Chronic external host (`external-host-chronic-flake`): if the log says the same URL failed on every attempt, the one change is a mirror, a cache, or a file already in the repo. A second rerun of the same URL is not a new hypothesis. Stop after you have named that path.

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

先引用会变动的那一行（超时、重跑、intermittent、矩阵分片、checkout 证书校验、外部数据集主机）。`checkout-tls-verify-flake` 只重跑一次，不要关掉 `sslVerify`。证书失败之后 hook 跑不起来（`checkout-tls-hook-cascade-flake`）仍是 flake，不要去修 hook。只有 hook、没有 checkout 行（`checkout-hook-only-unknown`）低于阈值，保持 `unknown`。服务或 Helm 健康检查超时（`service-healthcheck-timeout-flake`、`helm-healthcheck-timeout-flake`）只重跑一次，不要同时改测试。和 `AssertionError` 打平（`healthcheck-and-assertion-unknown`）保持 `unknown`。外部主机每次都失败（`external-host-chronic-flake`）仍是 flake，但不要把两次尝试都花在重跑同一个 URL 上，改用镜像、缓存或仓库里已有的文件。只有 `toomanyrequests`（`docker-pull-rate-limit-flake`）不要改镜像标签；若同时有 `pull access denied`（`registry-rate-and-auth-unknown`）保持 `unknown`。Cypress “Timed out retrying after”（`cypress-retry-timeout-flake`）只重跑一次。Git LFS 速率限制（`git-lfs-rate-limit-flake`）也只重跑一次。Cargo 仓库网络错误、Terraform state lock、kubectl rollout 超时、GitHub secondary rate limit 都只重跑一次，不要 force-unlock，也不要换 token。同一条证书错误再出现，就停下来问是不是自定义 CA。`external-dataset-host-flake` 引用主机名，不要在同一次尝试里改断言或换数据集。和 `AssertionError` 打平（`checkout-tls-and-assertion-unknown`、`dataset-and-assertion-unknown`）保持 `unknown`。`matrix-shard-flake` 只改共享状态，不要改每一个 matrix cell。只有 `retry N of M`（`shard-retry-only-unknown`）低于阈值，保持 `unknown`。Docker Hub `toomanyrequests` 且重跑已通过时，不要在同一次尝试里更换基础镜像。注册表 `no such host` 或 `egress blocked` 是 `infra`，不是这类。连续两次相同失败就改判并停止。
