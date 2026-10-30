# Progress

[中文说明](#中文)

Weekly public changelog for CI Doctor. Copy the template, fill one week, and keep the row honest. Numbers come from this repo: count directories under `fixtures/gha`, then run `make eval`. That command does not call `gh`. A report is advisory. It is not a merge decision.

Do not invent star counts, download numbers, or badges.

## Template

```text
Date: YYYY-MM-DD
Fixtures: <count>
Eval: <matched>/<count> (<accuracy>)
Version: <skill version, optional>
Improvement: <one sentence>
Next: <one sentence>
```

## 2026-10-26

Date: 2026-10-26

Fixtures: 50

Eval: 50/50 (1.000)

Improvement: The synthetic GitHub Actions corpus now includes Docker, Poetry, uv, Gradle, matrix shards, concurrency cancellation, and OIDC near-misses, and the diagnose CLI masks more token shapes before it quotes evidence.

Next: Add another near-miss only when `make eval` stays perfect. Leave `.github/workflows/triage-comment.yml` disabled (`if: false`).

## 2026-10-26 — checkout, egress, datasets

Date: 2026-10-26

Fixtures: 57

Eval: 57/57 (1.000)

Improvement: Checkout TLS certificate failures and flaky external dataset hosts now classify as flake, and blocked MCR or GHCR pulls classify as infra. Ties with an assertion or a git permission denial stay unknown.

Next: Leave `.github/workflows/triage-comment.yml` disabled (`if: false`). Add another near-miss only when `make eval` stays perfect.

## 2026-10-26 — feature guide and edge logs

Date: 2026-10-26

Fixtures: 63

Eval: 63/63 (1.000)

Version: 0.5.0

Improvement: The READMEs now explain the seven categories, when to skip the skill, and how playbooks map to checkout TLS, registry auth versus egress, and external dataset hosts. The classifier ignores a green job in a multi-job log, treats a post-checkout hook as a cascade of the checkout failure, and keeps registry authentication denial distinct from a blocked pull.

Next: Leave `.github/workflows/triage-comment.yml` disabled (`if: false`). Add another near-miss only when `make eval` stays perfect.

## 2026-10-27

Date: 2026-10-27

Fixtures: 73

Eval: 73/73 (1.000)

Version: 0.6.0

Improvement: Service and Helm health-check timeouts classify as flake, Bundler, go.sum, and Cargo.lock join the deps corpus, DNS name resolution classifies as infra, and a corrupt actions/cache restore outranks a following lockfile line. A chronic external host stays flake, with the playbook pointing at a mirror or a vendored file instead of another rerun. Health-check-plus-assertion and cache-EACCES-plus-lockfile stay unknown.

Next: Leave `.github/workflows/triage-comment.yml` disabled (`if: false`). Add another near-miss only when `make eval` stays perfect.

## 2026-10-28

Date: 2026-10-28

Fixtures: 73

Eval: 73/73 (1.000)

Version: 0.7.0

Improvement: A composite GitHub Action writes the category, confidence, evidence, and one next step to the job summary. Log-path and fixture stay offline. A completed run is downloaded with actions: read. Pull request comments stay off unless comment is true. The moving v1 tag is documented and not created from this repo.

Next: Leave `.github/workflows/triage-comment.yml` disabled (`if: false`). Publish the Action only after the public mirror has this commit and the v0.7.0 / v1 tags.

## 2026-10-28 — 0.8.0

Date: 2026-10-28

Fixtures: 87

Eval: 87/87 (1.000)

Version: 0.8.0

Improvement: Bare OOM kills, runtime version misses, self-hosted runner loss, path and architecture mismatches, pull and Git LFS rate limits, and Cypress retry timeouts now classify. continue-on-error noise no longer hides a later lockfile error. Action inputs and outputs are unchanged.

Next: Leave `.github/workflows/triage-comment.yml` disabled (`if: false`). Move the public `v1` tag only when this commit is on the mirror.

## 2026-10-29

Date: 2026-10-29

Fixtures: 102

Eval: 102/102 (1.000)

Version: 0.9.0

Improvement: Maven, SwiftPM, CocoaPods, NuGet, Cargo network versus compile, Terraform lock versus credentials, kubectl timeout versus RBAC, GitHub secondary rate limit versus bad credentials, and Java or Python out-of-memory lines now classify. Action inputs and outputs are unchanged.

Next: Leave `.github/workflows/triage-comment.yml` disabled (`if: false`). Move the public `v1` tag only when this commit is on the mirror.

## 2026-10-30

Date: 2026-10-30

Fixtures: 117

Eval: 117/117 (1.000)

Version: 0.10.0

Improvement: Bazel cache, Nix, apt, Homebrew, Deno, Go proxy, Rust linker OOM, Composer PHP, Google ADC, AWS token rejection, connection reset, and a reusable workflow secret that was not passed now classify. The Nix word flake is not a rerun. Action inputs and outputs are unchanged.

Next: Leave `.github/workflows/triage-comment.yml` disabled (`if: false`). Move the public `v1` tag only when this commit is on the mirror.

## 中文

每周公开记录。复制上面的模板，填一周。数字以本仓库为准：数 `fixtures/gha` 下的目录，再跑 `make eval`。该命令不调用 `gh`。报告只供参考，不是合并结论。不要编造 star 数或徽章。
