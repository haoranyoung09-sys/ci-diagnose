# GitHub Action

[English](action.md)

根目录的 `action.yml` 是 composite action。它在 runner 上执行 `python3 scripts/action_entry.py`。不安装 npm 包，不用 Docker 镜像，也不调用 LLM。

步骤把 markdown 写到 `$GITHUB_STEP_SUMMARY`，并设置输出：`category`、`confidence`、`confidence-level`、`advisory`、`next-step`、`evidence`。`advisory` 恒为 `true`。类别是 `flake`、`env`、`test`、`deps`、`permissions`、`infra`、`unknown` 之一。

## 日志从哪来

只传一种来源。

| 输入 | 网络 | 何时用 |
| --- | --- | --- |
| `log-path` | 不访问 | 你用 `tee` 存下了失败命令的输出。同一个 job 里、包括 `if: failure()`，都可以。 |
| `fixture` | 不访问 | 演示或自测。id 是这个 action 自带的 `fixtures/gha` 目录名。 |
| `run-id` | GitHub API，需要 `actions: read` | **已经结束**的 workflow run。`workflow_run` 应该用这个。 |

三个都不传时，action 用 `github.run_id` 去拉日志。正在跑的 job 还没有日志包，API 返回 404。步骤会写成 `category: unknown`，并说明改用 `workflow_run` 或 `log-path`。这种情况不会发 pull request 评论。

下载日志时，API 会重定向到 blob 存储。跳到别的主机时会**去掉** `Authorization`。token 不会被打印。

压缩包里既有失败 job 又有成功 job 时，只给失败的文件打分。

## Pull request 评论

`comment` 默认 `false`。设成 `true` 会发一条评论，或更新已有的、正文里带 `<!-- ci-doctor -->` 的那一条。需要 `pull-requests: write`，以及 pull request 编号（`pull-request`，或事件里自带的编号）。评论正文和 job summary 相同。它不是合并批准。

来自 fork 的 pull request 常常不能把 `pull-requests: write` 给 `GITHUB_TOKEN`。那里请保持 `comment` 关闭。

## 在 GitHub 上要手动做的事

这个仓库自己不会把 Action 发到 Marketplace。

- 把这个 commit 同步到公开镜像。
- 给该 commit 打不可移动的标签 `v0.7.0`，并把移动标签 `v1` 指到同一 commit。`uses: haoranyoung09-sys/ci-diagnose@v1` 跟随 `v1`。
- 为 `v0.7.0` 建一个 GitHub Release。Marketplace 的勾选在那个发布表单上。正文用 [release-notes-v0.7.0.md](release-notes-v0.7.0.md)。
- 示例工作流自己写了 `permissions`。仓库默认 token 若是只读，请保留这些块。拉日志要 `actions: read`。发评论要 `pull-requests: write`。

示例在 [examples/workflows](../examples/workflows)。自测是 [`.github/workflows/action.yml`](../.github/workflows/action.yml)，用 `uses: ./` 跑一条 fixture 和一份保存的日志，不调用 GitHub API。

`.github/workflows/triage-comment.yml` 仍然关闭（`if: false`）。要评论时用本 action 的 `comment: true`。
