# CI Doctor

[English](README.md)

拉取一次失败的 CI，归类根因，给出最小修复，并说明如何验证。这个仓库是可安装的 Agent Skill，加上一份公开、已脱敏的 fixture 语料。第一个宿主是 GitHub Actions。

`diagnose` 命令行是确定性的启发式规则，不是模型。它是离线路径，也是 fixture 的冒烟测试基准。置信度低时，skill 可以不同意分类结果，但必须明说。报告只供参考，不是合并结论。

## 安装 skill

Skill 源文件是 [`skills/ci-doctor/SKILL.md`](skills/ci-doctor/SKILL.md)。本仓库把它链接到 [`.agents/skills/ci-doctor`](.agents/skills/ci-doctor)，Cursor 和 Codex 打开仓库时就能发现它。

| 宿主 | 项目内路径 | 用户级路径 |
| --- | --- | --- |
| Cursor | `.agents/skills/` 或 `.cursor/skills/` | `~/.agents/skills/` 或 `~/.cursor/skills/` |
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |

Cursor 也会读取 `.claude/skills/` 和 `.codex/skills/`。装一处即可。在别的仓库里使用时，链接这个目录，不要复制，除非你想固定一份快照：

```bash
mkdir -p .agents/skills
ln -sfn /absolute/path/to/ci-doctor/skills/ci-doctor .agents/skills/ci-doctor
```

Claude Code：

```bash
mkdir -p .claude/skills
ln -sfn /absolute/path/to/ci-doctor/skills/ci-doctor .claude/skills/ci-doctor
```

各宿主的说明见 [docs/hosts.zh-CN.md](docs/hosts.zh-CN.md)。

## 离线诊断一条 fixture

需要 Python 3.9 或更高版本。不安装依赖，也不需要 token。

```bash
python3 scripts/diagnose.py --fixture npm-test-assertion
python3 scripts/diagnose.py fixtures/gha/npm-test-assertion/log.txt
python3 scripts/diagnose.py --fixtures-dir fixtures/gha
python3 scripts/diagnose.py --self-check
```

`--fixtures-dir` 会分类 `fixtures/gha` 下的每条案例，打印报告（类别、置信度、证据行、下一步），并在分类与 `meta.json` 的 `label` 不一致时以非零状态退出。这就是冒烟测试的判定。`make test` 跑标准库边界测试（空日志、2MB 上限、打码、坏掉的 fixture、重叠信号、`gh` 失败路径）。`make eval` 对同一语料打分，打印准确率和混淆矩阵，不调用 `gh`。`make smoke` 会跑自检、边界测试、fixture 全量和 `make eval`。

`.github/workflows/triage-comment.yml` 是只读失败评论的实验草稿。job 被关掉（`if: false`），工作流只有 `contents: read`，文件里没有 token。

超过 2MB 的日志会在该上限内的换行处截断后再打分，报告里会标出 `truncated`。文件剩余部分不会读入内存。

单条 fixture 的报告形如：

```text
ci-doctor 0.1.0
id: npm-test-assertion
log: fixtures/gha/npm-test-assertion/log.txt
category: test
confidence: 0.93 (high)
advisory: classification only; not a merge decision
expected_label: test
label_match: yes
signals: expect(received) mismatch; FAIL path line; expected vs received
prefix_stripped: removed gh job/step/timestamp prefixes

evidence:
  L7    FAIL src/api/health.test.ts
  L12   Expected: 200

next_steps:
  1. Open the failing test named in the evidence and compare expected vs received. ...
```

命令行输出的字段名是英文。类别 id 也保持英文：`flake`、`env`、`test`、`deps`、`permissions`、`infra`、`unknown`。中文含义见 [docs/taxonomy.zh-CN.md](docs/taxonomy.zh-CN.md)。

`--format json` 打印同一组字段，并带上 `scores` 和 `label_match`。退出码：`0` 报告正常，`1` fixture 标签不一致或自检失败，`2` 参数错误、fixture 元数据不合法，或 `gh` 未安装 / 未登录。

日志可以是步骤原文，也可以是 `gh run view --log-failed` 的输出。匹配前会去掉 job、step 和时间戳前缀。常见 token 形态会在打印证据前被打码。打码不是完整的秘密扫描，复述证据前请再看一眼。

## 用 gh 分诊 GitHub Actions

同一条命令在 `gh` 已安装且已登录时拉取公开的失败运行。它执行 `gh run view RUN_ID --repo OWNER/REPO --log-failed`，先打码再打分。URL 里浏览器的 `/job/` 数字不会传给 `gh`。

```bash
python3 scripts/diagnose.py --run-url 'https://github.com/OWNER/REPO/actions/runs/RUN_ID'
python3 scripts/diagnose.py --run-id RUN_ID --repo OWNER/REPO
python3 scripts/diagnose.py --run-url 'https://github.com/OWNER/REPO/actions/runs/RUN_ID' --dry-run
```

`--dry-run` 只打印这条 `gh` 命令，不访问网络。`python3 scripts/diagnose.py --self-check` 在不需要登录的情况下检查 URL 解析、dry-run 命令、拉取日志的打码，以及未安装或未登录时的提示。

`gh` 未安装或未登录时，命令以状态 2 退出，只有一段短说明，没有堆栈。把日志存下来，改用上面的文件路径。不要把 token 贴进 shell 或对话。

若要自己保存文件，等价步骤是：

```bash
gh run list --repo OWNER/REPO --status failure --limit 10
gh run view RUN_ID --repo OWNER/REPO --log-failed > /tmp/ci-doctor-run.log
python3 scripts/diagnose.py /tmp/ci-doctor-run.log
```

只看一个 job 时，用 `gh run view --json jobs` 里的 `databaseId`，不要用浏览器 URL 末尾的数字。给 agent 的完整步骤在 [`skills/ci-doctor/references/github-actions.md`](skills/ci-doctor/references/github-actions.md)。

## 隐私与护栏

- Fixture 是合成的，日志里写明了这一点。它们不是从私有运行复制来的。
- 不要回显 token、私钥或 secret 的值。只引用变量名。
- 两次修复尝试失败后停止。第二次没对上就停，不要把猜测放得更宽。
- 不要 force-push，也不要改写已经发布的历史，除非操作者明确要求。
- 不要为了变绿把 `permissions:` 放宽成 `write-all`，也不要用个人 token 换掉 `GITHUB_TOKEN`。
- 置信度分 `high`、`medium`、`low`。不要说某个改动可以安全合并。
- 超过 2 MB 的日志会被截断，报告里 `truncated` 为 true。

## 分类

`flake` 偶发失败 · `env` 环境变量 · `test` 测试断言 · `deps` 依赖 · `permissions` 权限 · `infra` 宿主资源 · `unknown` 证据不足

定义、信号和对应 fixture：[docs/taxonomy.zh-CN.md](docs/taxonomy.zh-CN.md)。语料索引：[fixtures/README.md](fixtures/README.md)。

## 目录

```text
skills/ci-doctor/     agent skill、playbook、gh 步骤
scripts/diagnose.py   分类、打码，以及用 gh 拉取日志
fixtures/gha/         合成的 GitHub Actions 失败
docs/                 分类说明与宿主安装
```

后续宿主、失败评论机器人，以及 Dependabot 旁路 skill，记在 [ROADMAP.md](ROADMAP.md)。

## 许可证

[MIT](LICENSE)。贡献请遵循 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。
