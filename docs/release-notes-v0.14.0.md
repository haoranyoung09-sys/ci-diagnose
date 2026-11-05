# ci-fail-classify 0.14.0

Clone, `uses:`, and the install curl URL stay on `haoranyoung09-sys/ci-diagnose`. The Action display name stays `ci-fail-classify`. Inputs, outputs, and branding are unchanged.

This is still diagnosis only. It does not build, sign, or host the app. Compared with faultline, patchrail, failsift, ci-failure-explainer, and ci-medic, this remains the scored seven-class classifier and the offline fixture oracle.

## What the new fixtures catch

177 fixtures. Eval 177/177.

| What you see | Category | Fixture |
| --- | --- | --- |
| Build context is larger than the limit | infra | `docker-build-context-too-large-infra` |
| BuildKit cache export failed | infra | `buildx-cache-export-failed-infra` |
| Helm upgrade context deadline exceeded | flake | `helm-upgrade-deadline-flake` |
| Collector scrape context deadline exceeded | flake | `otel-collector-scrape-timeout-flake` |
| NuGet feed 401 | permissions | `nuget-feed-unauthorized-permissions` |
| NuGet service index 503 | flake | `nuget-feed-503-flake` |
| crates.io 429 | flake | `cargo-crates-io-rate-limit-flake` |
| Crate version is yanked | deps | `cargo-crate-yanked-deps` |
| DerivedData does not exist | env | `xcode-derived-data-missing-env` |
| `vm.max_map_count` is too low | infra | `elasticsearch-vm-max-map-count-infra` |
| Redis is still loading | flake | `redis-loading-not-ready-flake` |
| Codecov token is missing | env | `codecov-token-missing-env` |
| Coverage upload timed out | flake | `codecov-upload-timeout-flake` |
| Codecov 401 Invalid token | permissions | `codecov-token-rejected-permissions` |
| Windows path is too long | infra | `windows-path-too-long-infra` |
| `com.apple.quarantine` | permissions | `macos-quarantine-blocked-permissions` |
| System Integrity Protection | infra | `macos-sip-blocked-infra` |
| Only the word Dependabot | unknown | `dependabot-word-only-unknown` |

Node heap and exit 137 were already classified. A service-container health check and "timed out waiting for the condition" were already flake. `Filename too long` was already infra; the new Windows line is `PathTooLongException`.

## Install

After tag `v0.14.0` is on the public mirror:

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-diagnose/v0.14.0/scripts/install.sh | bash
```

```yaml
- uses: haoranyoung09-sys/ci-diagnose@v1
```

## 中文

clone、`uses:` 和安装用的 curl 地址仍是 `haoranyoung09-sys/ci-diagnose`。Action 显示名仍是 `ci-fail-classify`。输入、输出和 branding 不变。

这仍只做诊断。和 faultline、patchrail、failsift、ci-failure-explainer、ci-medic 相比，这里仍是可以打分的七类分类器和离线 fixture。

177 条 fixture，eval 177/177。构建上下文过大、BuildKit 缓存导出失败、`vm.max_map_count`、Windows 路径过长、System Integrity Protection 是 `infra`。Helm 或 collector 的 deadline、NuGet 503、crates.io 429、Redis 仍在加载、覆盖率上传超时是 `flake`。被 yank 的 crate 是 `deps`。DerivedData 缺失和 Codecov token 缺失是 `env`。NuGet 401、Codecov 401、`com.apple.quarantine` 是 `permissions`。只有 Dependabot 这一个词、没有解析行，保持 `unknown`。

公开镜像有 `v0.14.0` 之后，安装命令钉这个标签。`@v1` 只在这个 commit 已经在公开镜像上时才移动。
