# ci-fail-classify 0.16.0

Clone, `uses:`, and the install curl URL stay on `haoranyoung09-sys/ci-diagnose`. The Action display name stays `ci-fail-classify`. Inputs, outputs, and branding are unchanged.

This is still diagnosis only. It does not build, sign, or host the app. Compared with faultline, patchrail, failsift, ci-failure-explainer, and ci-medic, this remains the scored seven-class classifier and the offline fixture oracle.

## What the new fixtures catch

209 fixtures. Eval 209/209.

| What you see | Category | Fixture |
| --- | --- | --- |
| ImagePullBackOff | infra | `kube-image-pull-backoff-infra` |
| CrashLoopBackOff | test | `kube-crashloop-backoff-test` |
| Gradle wrapper checksum | deps | `gradle-wrapper-checksum-deps` |
| Maven wrapper checksum | deps | `maven-wrapper-checksum-deps` |
| SQLite database is locked | flake | `sqlite-database-locked-flake` |
| Postgres too many clients | infra | `postgres-too-many-clients-infra` |
| Android Gradle plugin mismatch | env | `android-gradle-plugin-mismatch-env` |
| Ansible vault password file missing | env | `ansible-vault-password-missing-env` |
| CDN error code 520 | flake | `cloudflare-520-flake` |
| Submodule has no URL | env | `git-submodule-not-initialized-env` |
| Hugging Face 429 | flake | `huggingface-rate-limit-flake` |
| Gated model | permissions | `huggingface-gated-model-permissions` |
| pixi SolvePackageNotFound | deps | `pixi-solve-not-found-deps` |
| conda PackagesNotFoundError | deps | `conda-package-not-found-deps` |
| Bazel analysis failed | test | `bazel-analysis-failed-test` |
| Bazel repository fetch failed | flake | `bazel-fetch-failed-flake` |

Terraform state lock was already `flake` (`terraform-state-lock-flake`), distinct from the provider lock (`terraform-provider-lock-deps`). A submodule username prompt was already `env`. A remote Bazel cache miss was already `infra`.

## Install

After tag `v0.16.0` is on the public mirror:

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-diagnose/v0.16.0/scripts/install.sh | bash
```

```yaml
- uses: haoranyoung09-sys/ci-diagnose@v1
```

## 中文

clone、`uses:` 和安装用的 curl 地址仍是 `haoranyoung09-sys/ci-diagnose`。Action 显示名仍是 `ci-fail-classify`。输入、输出和 branding 不变。

这仍只做诊断。和 faultline、patchrail、failsift、ci-failure-explainer、ci-medic 相比，这里仍是可以打分的七类分类器和离线 fixture。

209 条 fixture，eval 209/209。`ImagePullBackOff` 和 Postgres 连接槽用尽是 `infra`。`CrashLoopBackOff` 和 Bazel analysis 失败是 `test`。Gradle 或 Maven wrapper 校验和、pixi 或 conda 找不到包是 `deps`。SQLite 锁、CDN 520、Hugging Face 429、Bazel 仓库拉取失败是 `flake`。AGP 不匹配、Ansible vault 密码文件缺失、子模块未初始化是 `env`。受限模型是 `permissions`。Terraform state lock 本来就是 `flake`。

公开镜像有 `v0.16.0` 之后，安装命令钉这个标签。`@v1` 只在这个 commit 已经在公开镜像上时才移动。
