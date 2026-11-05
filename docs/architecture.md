# How the pieces fit

[中文](#中文)

CI Doctor diagnoses a failed GitHub Actions log. It does not run builds, store artifacts, or replace your CI. fastlane.ci tried to be a CI server and was retired; the useful lesson is to keep the layers small and the config readable.

## Three surfaces

| Surface | What it is | What it is not |
| --- | --- | --- |
| Action | `action.yml`. A workflow step. Writes the job summary and outputs. `uses: …@v1` is the stable contract. | A CI product. Inputs and outputs do not change inside `@v1`. |
| CLI | `scripts/diagnose.py`, and the `diagnose` wrapper from `scripts/install.sh`. Offline. | A daemon. It scores one log and exits. |
| Skill | `skills/ci-doctor/`. Tells an agent to run the CLI, then follow one playbook. | A second classifier. If the CLI and the skill disagree, the report says so. |

The Action display name is `ci-fail-classify`. The public GitHub path is still [`haoranyoung09-sys/ci-diagnose`](https://github.com/haoranyoung09-sys/ci-diagnose). Install and the Action snippet are the two ways in. The install script is pinned to a release tag (`v0.16.0` for this release). The Action tag `@v1` moves only when a release keeps the same inputs and outputs. The skill directory stays `ci-doctor`.

## What talks to what

```text
workflow step  ->  action_entry.py  ->  diagnose.py  ->  job summary
agent          ->  SKILL.md         ->  diagnose.py  ->  one playbook
you            ->  diagnose.py or diagnose
fixtures/gha   ->  make eval        ->  the same diagnose.py
```

`scripts/action_entry.py` is the Action adapter. It accepts a saved log, a fixture id, or a completed run id. It does not call an LLM. `scripts/diagnose.py` is the only scorer. The skill does not reimplement the rules.

A new CI host, if one is ever added, would be another adapter that still calls `diagnose.py`. Do not fold host-specific HTTP into the scorer.

## Fixture oracle

Each case under `fixtures/gha/<id>/` has `meta.json` and `log.txt`. The label is the expected category. `make eval` runs the classifier without reading that label while scoring, then counts mismatches. A change that flips a label is a failed eval, not a silent retune.

Categories stay `flake`, `env`, `test`, `deps`, `permissions`, `infra`, and `unknown`. Ties at the decision threshold are `unknown` on purpose.

## 中文

CI Doctor 只诊断失败的 GitHub Actions 日志。它不构建、不存产物、也不替换你的 CI。fastlane.ci 曾经想做成 CI 服务器，后来停了。能学的是把层次留小、配置让人读得懂。

三个表面：Action（`action.yml`，`@v1` 是稳定契约）、命令行（`scripts/diagnose.py`）、skill（`skills/ci-doctor/`，让 agent 去跑命令行再跟一份 playbook）。Action 显示名是 `ci-fail-classify`。公开 GitHub 路径仍是 `haoranyoung09-sys/ci-diagnose`。安装脚本钉在发行标签上（这一版是 `v0.16.0`）。skill 目录仍是 `ci-doctor`。`@v1` 只在输入和输出保持不变时才移动。

`scripts/action_entry.py` 是 Action 适配器，只把日志交给 `diagnose.py`。不调用模型。`make eval` 用 `fixtures/gha` 做离线对照。类别仍然只有 `flake`、`env`、`test`、`deps`、`permissions`、`infra`、`unknown`。
