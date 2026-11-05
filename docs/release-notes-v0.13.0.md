# ci-fail-classify 0.13.0

The GitHub rename stays deferred. Clone, `uses:`, and the install curl URL stay on `haoranyoung09-sys/ci-diagnose`. The Action display name stays `ci-fail-classify`. Inputs, outputs, and branding are unchanged.

This is still diagnosis only. It does not build, sign, or host the app. Compared with faultline, patchrail, failsift, ci-failure-explainer, and ci-medic, this remains the scored seven-class classifier and the offline fixture oracle.

## What the new fixtures catch

159 fixtures. Eval 159/159.

| What you see | Category | Fixture |
| --- | --- | --- |
| Job exceeded its maximum execution time | infra | `job-max-execution-time-infra` |
| Step timed out after N minutes | flake | `step-timeout-minutes-flake` |
| Only exit code 137 | infra | `bare-exit-137-infra` |
| Job time limit and an assertion, same score | unknown | `job-timeout-and-assertion-unknown` |
| No runners available for the labels | infra | `no-runners-available-infra` |
| Playwright browser executable missing | deps | `playwright-browser-missing-deps` |
| Playwright browser download failed | flake | `playwright-browser-download-flake` |
| Terraform provider lock does not match | deps | `terraform-provider-lock-deps` |
| `ERR_PNPM_TARBALL_INTEGRITY` | deps | `pnpm-tarball-integrity-deps` |
| Cypress app could not be downloaded | flake | `cypress-binary-download-flake` |
| Repository exceeded its LFS budget | permissions | `git-lfs-budget-exceeded-permissions` |
| git-lfs smudge filter failed | env | `git-lfs-smudge-failed-env` |
| Canceled because another matrix cell failed | unknown | `matrix-cancel-sibling-unknown` |

A heap line, a bare `Killed`, or a runner shutdown still explains exit 137. The new rule does not add a second signal on those logs.

## Install

After tag `v0.13.0` is on the public mirror:

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-diagnose/v0.13.0/scripts/install.sh | bash
```

```yaml
- uses: haoranyoung09-sys/ci-diagnose@v1
```

## 中文

GitHub 改名先不做。clone、`uses:` 和安装用的 curl 地址仍是 `haoranyoung09-sys/ci-diagnose`。Action 显示名仍是 `ci-fail-classify`。输入、输出和 branding 不变。

这仍只做诊断，不构建、不签名、不托管应用。和 faultline、patchrail、failsift、ci-failure-explainer、ci-medic 相比，这里仍是可以打分的七类分类器和离线 fixture。

159 条 fixture，eval 159/159。作业超过 maximum execution time、只有 exit code 137、no runners available 是 `infra`。步骤 “timed out after N minutes”、Cypress 或 Playwright 浏览器下载失败是 `flake`。Playwright 缺浏览器、Terraform provider lock、`ERR_PNPM_TARBALL_INTEGRITY` 是 `deps`。LFS 配额是 `permissions`。没有速率也没有配额的 git-lfs smudge 失败是 `env`。作业时限和断言打平，或因为另一个 matrix 单元失败而被取消，保持 `unknown`。已经写了堆内存、`Killed` 或 runner 关闭的日志，不会再为 exit 137 加第二条信号。

公开镜像有 `v0.13.0` 之后，安装命令钉这个标签。`@v1` 只在这个 commit 已经在公开镜像上时才移动。
