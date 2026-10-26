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

## 中文

每周公开记录。复制上面的模板，填一周。数字以本仓库为准：数 `fixtures/gha` 下的目录，再跑 `make eval`。该命令不调用 `gh`。报告只供参考，不是合并结论。不要编造 star 数或徽章。
