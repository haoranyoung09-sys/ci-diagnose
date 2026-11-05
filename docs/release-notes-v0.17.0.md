# ci-fail-classify 0.17.0

Clone, `uses:`, and the install curl URL stay on `haoranyoung09-sys/ci-diagnose`. The Action display name stays `ci-fail-classify`. Inputs, outputs, and branding are unchanged.

This is still diagnosis only. It does not build, sign, or host the app. Compared with faultline, patchrail, failsift, ci-failure-explainer, and ci-medic, this remains the scored seven-class classifier and the offline fixture oracle.

## What the new fixtures catch

227 fixtures. Eval 227/227.

| What you see | Category | Fixture |
| --- | --- | --- |
| Cannot connect to Podman | infra | `podman-socket-unavailable-infra` |
| Host port is already allocated | infra | `testcontainers-port-conflict-infra` |
| Kafka broker is not ready | flake | `kafka-broker-not-ready-flake` |
| MongoDB authentication failed | permissions | `mongodb-auth-failed-permissions` |
| MongoDB connection refused | flake | `mongodb-connection-refused-flake` |
| SENTRY_AUTH_TOKEN is unset | env | `sentry-token-missing-env` |
| Quality gate failed | test | `sonar-quality-gate-failed-test` |
| sonar.token was rejected | permissions | `sonar-token-rejected-permissions` |
| Coveralls repo token missing | env | `coveralls-token-missing-env` |
| Publish requires provenance | permissions | `npm-provenance-required-permissions` |
| GitHub Packages publish 403 | permissions | `github-packages-publish-403-permissions` |
| Package version was unpublished | deps | `github-packages-unpublished-deps` |
| mypy cache is corrupt | infra | `mypy-cache-corrupt-infra` |
| Prettier check found drift | test | `prettier-check-drift-test` |
| Remote cache unauthorized | permissions | `turbo-remote-unauthorized-permissions` |
| Remote cache could not be reached | infra | `nx-remote-cache-unreachable-infra` |
| Earthly daemon is not responding | infra | `earthly-daemon-unavailable-infra` |
| Dagger failed to connect to the engine | infra | `dagger-engine-disconnect-infra` |

The Docker daemon line was already `infra`. Ruff parse failure was already `test`. A Slack webhook line was left out of this slice.

## Install

After tag `v0.17.0` is on the public mirror:

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-diagnose/v0.17.0/scripts/install.sh | bash
```

```yaml
- uses: haoranyoung09-sys/ci-diagnose@v1
```

## 中文

clone、`uses:` 和安装用的 curl 地址仍是 `haoranyoung09-sys/ci-diagnose`。Action 显示名仍是 `ci-fail-classify`。输入、输出和 branding 不变。

这仍只做诊断。和 faultline、patchrail、failsift、ci-failure-explainer、ci-medic 相比，这里仍是可以打分的七类分类器和离线 fixture。

227 条 fixture，eval 227/227。Podman socket、端口占用、mypy 缓存损坏、远程缓存连不上、Earthly 或 Dagger 引擎断开是 `infra`。Kafka 未就绪和 MongoDB 拒绝连接是 `flake`。MongoDB 认证失败、Sonar token 被拒绝、npm provenance、GitHub Packages 403、远程缓存拒绝 token 是 `permissions`。包版本被取消发布是 `deps`。质量门失败和 Prettier 检查失败是 `test`。缺少 Sentry 或 Coveralls token 是 `env`。Docker daemon 那一行本来就是 `infra`。

公开镜像有 `v0.17.0` 之后，安装命令钉这个标签。`@v1` 只在这个 commit 已经在公开镜像上时才移动。
