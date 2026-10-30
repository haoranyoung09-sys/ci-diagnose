# CI Doctor

[English](README.md)

CI 挂了，或者 GitHub Actions 是红的？给日志归类，引用打码后的证据，提出一处最小修复，并说明如何验证。只供参考，不是合并结论。

## 快速开始：加到工作流

不用安装，也不调用 LLM。名为 `CI` 的工作流变红并结束后，这个 job 拉取该次运行的日志（`actions: read`），把类别写进 job summary。

```yaml
name: CI Doctor
"on":
  workflow_run:
    workflows: ["CI"]
    types: [completed]
permissions:
  actions: read
  contents: read
jobs:
  triage:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - uses: haoranyoung09-sys/ci-diagnose@v1
        with:
          run-id: ${{ github.event.workflow_run.id }}
```

同一个 job、并且你已经把日志存下来时用下面这段。`if: failure()` 拉不到当前这次运行的日志，因为 job 还没结束。

```yaml
- uses: haoranyoung09-sys/ci-diagnose@v1
  if: failure()
  with:
    log-path: ci.log
```

`comment` 默认关闭。取舍、权限和 `v1` 标签见 [docs/action.zh-CN.md](docs/action.zh-CN.md)。

下面两张图由 [`scripts/render_demo.py`](scripts/render_demo.py) 根据 `npm-ci-lockfile-drift` 的真实报告生成，不是 github.com 的录屏。

![npm-ci-lockfile-drift 的终端分类](docs/demo-terminal.svg)

![同一份报告的 job summary 字段](docs/demo-summary.svg)

## 30 秒演示

Python 3.9 或更高。不安装依赖，不需要 token，也不访问网络。

```bash
git clone https://github.com/haoranyoung09-sys/ci-diagnose.git
cd ci-diagnose
python3 scripts/diagnose.py --fixture npm-ci-lockfile-drift
make eval
```

这条 fixture 会打印一份 `deps` 报告，对应 `npm ci` 的锁文件不同步。`make eval` 打印 `fixtures/gha` 的准确率和混淆矩阵，不调用 `gh`。

每周记录：[docs/PROGRESS.md](docs/PROGRESS.md)。

适合在这些时候用：workflow run failed、检查变红、要做 Actions triage、找一个 agent skill。第一个宿主是 GitHub Actions。这个仓库是 skill，加上一份公开的合成 fixture 语料。

`diagnose` 命令行是确定性的启发式规则，不是模型。它是离线路径，也是 fixture 的冒烟测试基准。置信度低时，skill 可以不同意分类结果，但必须明说。

## 功能

<a id="features"></a>

CI Doctor 给失败的 GitHub Actions 日志归类，引用打码后的证据，并指出一步下一步。它不合并，也不判断某个改动可以安全落地。[`action.yml`](action.yml) 里的 GitHub Action 调用同一个分类器。说明见 [docs/action.zh-CN.md](docs/action.zh-CN.md)。

### 它分类什么

七个 id。某一类得分至少为 6 且领先时胜出。两类在 6 分上打平，结果是 `unknown`。打分时不读 `meta.json`。

| id | 含义 | Actions 里常见的样子 |
| --- | --- | --- |
| `flake` | 结果会变，或 checkout、注册表、数据集的短暂失败 | 证书校验失败；外部数据集主机超时；hook 失败只是因为 checkout 没完成 |
| `env` | 某个具名变量、action 输入或 secret 从未设置 | `DATABASE_URL` 未设置 |
| `test` | 测试已经跑起来，某个期望失败 | Jest `FAIL`、`AssertionError` |
| `deps` | 解析器或锁文件不一致 | `npm ci` 锁文件不同步 |
| `permissions` | token 或镜像仓库登录被拒绝 | `GITHUB_TOKEN` 403；`pull access denied` |
| `infra` | 运行器、磁盘或网络路径失败 | 磁盘满；MCR `no such host`；Docker daemon 不在 |
| `unknown` | 没有信号过线，或两类打平 | 只有退出码；checkout TLS 和断言打平；egress 和仓库认证打平 |

每个信号的定义和 fixture：[docs/taxonomy.zh-CN.md](docs/taxonomy.zh-CN.md)。语料索引：[fixtures/README.md](fixtures/README.md)。类别 id 保持英文。

### 它怎么工作

1. 读日志，到 2MB 停止。空日志是 `unknown`。截断点之后的信号不计分，报告会标 `truncated`。
2. 去掉 `gh` 的 job、step 和时间戳前缀。先打码常见 token，再打分。打码不是完整扫描。
3. 日志里有多个 job、且只有一部分失败时，只给失败的 job 打分。绿 job 上的一句话不能获胜（`multi-job-one-step-failed`）。失败 job 本身没有信号时，结果保持 `unknown`（`multi-job-green-noise-unknown`）。
4. 打开该类别的 playbook，只跟一条配方。打平不是去选更好改的那一类。
5. `make eval` 离线核对每条 fixture 的标签，不调用 `gh`。

### 什么时候用

- GitHub Actions 的 job 是红的，你手头有日志、运行 URL 或 fixture id。
- 你要一个类别、支撑它的行，以及一种验证方式。
- 你在用这份语料核对 skill。

### 什么时候不用

- 用来批准合并，或说某个改动可以安全落地。
- Dependabot 或 Renovate 的版本更新。那个旁路 skill 还不在这个仓库里。
- GitLab CI、CircleCI，或 GitHub Actions 以外的宿主。
- 一条私有日志，不贴 secret 就讲不清楚。请改存一份打码后的文件。
- 评论工作流。[`.github/workflows/triage-comment.yml`](.github/workflows/triage-comment.yml) 是关掉的（`if: false`）。

### Playbook 和真实的 Actions 失败

| 日志里有什么 | 类别 | Fixture |
| --- | --- | --- |
| Checkout 出现 `SSL certificate problem` 或 `server certificate verification failed` | `flake` | `checkout-tls-verify-flake` |
| 这次 checkout 失败之后，hook 跑不起来 | `flake` | `checkout-tls-hook-cascade-flake` |
| hook 跑不起来，日志里没有 checkout 错误 | `unknown` | `checkout-hook-only-unknown` |
| 外部数据集主机超时 | `flake` | `external-dataset-host-flake` |
| `mcr.microsoft.com` 或 `ghcr.io`：`no such host`、`egress blocked`、`i/o timeout` | `infra` | `mcr-pull-egress-blocked`、`ghcr-pull-io-timeout` |
| `pull access denied` 或 `unauthorized: authentication required` | `permissions` | `registry-pull-auth-denied` |
| 同一次拉取里既有 egress 阻断，又有仓库认证拒绝 | `unknown` | `registry-auth-and-egress-unknown` |
| 多个 job，只有一个失败 | 失败的那个 job | `multi-job-one-step-failed` |
| Postgres/Redis 服务或 Helm 健康检查超时 | `flake` | `service-healthcheck-timeout-flake`、`helm-healthcheck-timeout-flake` |
| 这次健康检查和 `AssertionError` 打平 | `unknown` | `healthcheck-and-assertion-unknown` |
| 外部主机最近每次尝试都失败 | `flake`（改用镜像或仓库内文件，不要把同一个 URL 重跑两次） | `external-host-chronic-flake` |
| `Gemfile.lock`、`go.sum` 或 `Cargo.lock` 过期 | `deps` | `bundler-lockfile-out-of-date`、`go-sum-checksum-mismatch`、`cargo-lock-needs-update` |
| `getaddrinfo` / “Temporary failure in name resolution” | `infra` | `dns-name-resolution-infra` |
| `actions/cache` 恢复失败，随后锁文件报错 | `infra` | `actions-cache-restore-corrupt` |
| 缓存 `EACCES` 和锁文件行同时出现 | `unknown` | `cache-eacces-and-lockfile-unknown` |
| 内核 `Killed` 且退出码 137、自托管 runner 失联、`Filename too long`、arm64 镜像跑在 amd64 上、Docker 层缺失 | `infra` | `kernel-oom-killed-infra`、`self-hosted-runner-offline-infra`、`windows-filename-too-long-infra`、`runner-arch-mismatch-infra`、`docker-layer-cache-missing-infra` |
| Node `engines` 不符、镜像上没有要求的 Python/Node、找不到 `action.yml` | `env` | `node-engine-mismatch-env`、`setup-python-version-missing-env`、`composite-action-path-missing-env` |
| 只有 `toomanyrequests`、Cypress “timed out retrying”、Git LFS 速率限制 | `flake` | `docker-pull-rate-limit-flake`、`cypress-retry-timeout-flake`、`git-lfs-rate-limit-flake` |
| `pnpm-lock.yaml` 不是最新，或 `continue-on-error` 之后锁文件失败 | `deps` | `pnpm-lock-not-up-to-date-deps`、`continue-on-error-lockfile-deps` |
| 拉取速率限制和 `pull access denied` 同时出现 | `unknown` | `registry-rate-and-auth-unknown` |
| Maven、SwiftPM、CocoaPods 或 NuGet 解析不到包 | `deps` | `maven-dependencies-unresolved-deps`、`swiftpm-package-unresolved-deps`、`cocoapods-pod-conflict-deps`、`nuget-package-not-found-deps` |
| Cargo 连不上 crates-io；rustc 拒绝编译 | `flake` / `test` | `cargo-registry-network-flake`、`cargo-type-mismatch-test` |
| Terraform 拿不到 state lock，或没有云凭证 | `flake` / `env` | `terraform-state-lock-flake`、`terraform-credentials-missing-env` |
| kubectl 等待超时，或 RBAC 拒绝 | `flake` / `permissions` | `kubectl-rollout-timeout-flake`、`kubectl-rbac-forbidden-permissions` |
| GitHub secondary rate limit，或 Bad credentials | `flake` / `permissions` | `github-secondary-rate-limit-flake`、`github-bad-credentials-permissions` |
| Java `OutOfMemoryError` 或 Python `MemoryError` | `infra` | `java-heap-oom-infra`、`python-memory-error-infra` |
| 缺少 App Store Connect 的密钥名字 | `env` | `app-store-connect-key-missing-env` |
| Bazel 远程缓存不可用、Nix store 哈希不符、apt 镜像 404、Homebrew bottle 下载失败、Rust 链接器内存耗尽 | `infra` | `bazel-remote-cache-unavailable-infra`、`nix-nar-hash-mismatch-infra`、`apt-mirror-404-infra`、`homebrew-bottle-download-infra`、`rust-linker-oom-infra` |
| Nix flake 没有对应输出、Deno 锁文件过期 | `deps` | `nix-flake-output-missing-deps`、`deno-lockfile-out-of-date-deps` |
| apt 缺少 `NO_PUBKEY`、Google ADC 没有凭证、Composer 要求更高 PHP、可复用工作流没传入 secret | `env` | `apt-pubkey-missing-env`、`gcp-adc-missing-env`、`composer-php-platform-env`、`workflow-secret-not-passed-env` |
| AWS 拒绝了 security token | `permissions` | `aws-invalid-token-permissions` |
| Go module proxy 返回 502，或只有 `ECONNRESET` | `flake` | `go-proxy-502-flake`、`econnreset-flake` |
| `ECONNRESET` 和 `AssertionError` 打平 | `unknown` | `econnreset-and-assertion-unknown` |

Playbook 在 [`skills/ci-doctor/references/playbooks/`](skills/ci-doctor/references/playbooks/)。每一份都有配方、验证、停止条件，和一段简短中文。

### 离线演示和 eval

上面的 [30 秒演示](#30-秒演示) 是支持的离线路径。不装包，不要 token，不访问网络。

`python3 scripts/diagnose.py --fixture npm-ci-lockfile-drift` 打印一份 `deps` 报告。`make eval` 打印 `fixtures/gha` 的准确率和混淆矩阵。`make test` 覆盖空日志、2MB 截断、打码和含糊信号。`make smoke` 跑自检、测试、全部 fixture 和 `make eval`。

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
action.yml            composite GitHub Action
examples/workflows/   可复制的工作流
skills/ci-doctor/     agent skill、playbook、gh 步骤
scripts/diagnose.py   分类、打码，以及用 gh 拉取日志
fixtures/gha/         合成的 GitHub Actions 失败
docs/                 分类说明、宿主安装、Action 说明、每周进展
```

后续宿主、失败评论机器人，以及 Dependabot 旁路 skill，记在 [ROADMAP.md](ROADMAP.md)。

## 许可证

[MIT](LICENSE)。贡献请遵循 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。
