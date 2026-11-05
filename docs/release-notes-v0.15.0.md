# ci-fail-classify 0.15.0

Clone, `uses:`, and the install curl URL stay on `haoranyoung09-sys/ci-diagnose`. The Action display name stays `ci-fail-classify`. Inputs, outputs, and branding are unchanged.

This is still diagnosis only. It does not build, sign, or host the app. Compared with faultline, patchrail, failsift, ci-failure-explainer, and ci-medic, this remains the scored seven-class classifier and the offline fixture oracle.

## What the new fixtures catch

193 fixtures. Eval 193/193.

| What you see | Category | Fixture |
| --- | --- | --- |
| ECR pull denied | permissions | `ecr-pull-denied-permissions` |
| CodeArtifact token denied | permissions | `codeartifact-token-denied-permissions` |
| CodeArtifact 429 | flake | `codeartifact-429-flake` |
| Artifactory 403 | permissions | `artifactory-403-permissions` |
| Artifactory 429 | flake | `artifactory-429-flake` |
| go.sum database checksum mismatch | deps | `gosum-database-mismatch-deps` |
| Go proxy context deadline | flake | `go-proxy-deadline-flake` |
| Packagist 429 | flake | `packagist-429-flake` |
| Gem version yanked | deps | `gem-version-yanked-deps` |
| Rubygems 503 | flake | `rubygems-503-flake` |
| Deno `--allow-net` | permissions | `deno-permission-prompt-permissions` |
| sparse-checkout missed a path | env | `sparse-checkout-miss-env` |
| SELinux avc denied | infra | `selinux-avc-denied-infra` |
| AppArmor denied | infra | `apparmor-denied-infra` |
| packageManager field mismatch | env | `corepack-packagemanager-mismatch-env` |
| getStaticPaths paths collide | test | `next-static-path-collision-test` |

A reusable workflow secret that was not passed was already `env` (`workflow-secret-not-passed-env`). A Go proxy 502 and a missing `go.sum` entry were already classified. Composer’s PHP platform line was already `env`. Node heap OOM was already `infra`. A concurrency cancel (`concurrency-cancel-unknown`) now names itself and stays under the threshold. A matrix job canceled because a sibling failed (`matrix-cancel-sibling-unknown`) still has no signal.

## Install

After tag `v0.15.0` is on the public mirror:

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-diagnose/v0.15.0/scripts/install.sh | bash
```

```yaml
- uses: haoranyoung09-sys/ci-diagnose@v1
```

## 中文

clone、`uses:` 和安装用的 curl 地址仍是 `haoranyoung09-sys/ci-diagnose`。Action 显示名仍是 `ci-fail-classify`。输入、输出和 branding 不变。

这仍只做诊断。和 faultline、patchrail、failsift、ci-failure-explainer、ci-medic 相比，这里仍是可以打分的七类分类器和离线 fixture。

193 条 fixture，eval 193/193。ECR 或 CodeArtifact 拒绝、Artifactory 403、Deno `--allow-net` 是 `permissions`。这些主机的 429、Packagist 429、Go proxy deadline、Rubygems 503 是 `flake`。sumdb 校验不符和被 yank 的 gem 是 `deps`。sparse-checkout 漏路径和 `packageManager` 不一致是 `env`。SELinux 和 AppArmor 是 `infra`。`getStaticPaths` 路径冲突是 `test`。并发组取消会点名自己，但仍低于阈值；matrix 兄弟任务取消仍然没有信号。

公开镜像有 `v0.15.0` 之后，安装命令钉这个标签。`@v1` 只在这个 commit 已经在公开镜像上时才移动。
