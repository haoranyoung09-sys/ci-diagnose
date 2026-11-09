# 分类 v0

[English](taxonomy.md)

七个类别。id 是契约：`flake`、`env`、`test`、`deps`、`permissions`、`infra`、`unknown`。诊断命令按 [`scripts/diagnose.py`](../scripts/diagnose.py) 里的信号打分。某一类得分至少为 6 且领先时胜出。低于阈值则是 `unknown`。两类在阈值上打平，也是 `unknown`。

置信度：`high`（≥ 0.80）、`medium`（≥ 0.60）、`low`。`unknown` 故意是 low。这些都不是“可以合并”。

日志可以是步骤原文，也可以是 `gh run view --log-failed` 的行（job、step、时间戳）。匹配前会去掉前缀。

## flake

失败会自己挪位置：超时后重跑通过、被标成间歇性的测试、某一次编号重试变绿。

**信号：** “suspected flake”、“exceeded timeout of N”、“timeout of N ms exceeded”、“passed on the previous run” 或 “passed on the automatic rerun”、“intermittent”、“retry N of M”、checkout 的 “SSL certificate problem” / “server certificate verification failed” / “unable to get local issuer certificate” / “The TLS connection was non-properly terminated”、“failed to download the external dataset”、“external host timed out”、“health check failed” / “health check timed out” / “service container … failed to start”、Helm “timeout waiting for … InProgress”。和 `AssertionError` 打平时仍是 `unknown`（`timeout-and-assertion-unknown`、`checkout-tls-and-assertion-unknown`、`dataset-and-assertion-unknown`）。

**不是这类：** 稳定的断言（`test`）、运行器内存耗尽（`infra`）、注册表 DNS 或 egress 失败（`infra`）、包不存在的 404（`deps`）。

**Fixture：** [`jest-timeout-flake`](../fixtures/gha/jest-timeout-flake)、[`registry-timeout-rerun-flake`](../fixtures/gha/registry-timeout-rerun-flake)、[`playwright-timeout-flake`](../fixtures/gha/playwright-timeout-flake)、[`cypress-timeout-flake`](../fixtures/gha/cypress-timeout-flake)、[`matrix-shard-flake`](../fixtures/gha/matrix-shard-flake)、[`docker-rate-limit-flake`](../fixtures/gha/docker-rate-limit-flake)、[`checkout-tls-verify-flake`](../fixtures/gha/checkout-tls-verify-flake)、[`external-dataset-host-flake`](../fixtures/gha/external-dataset-host-flake)、[`checkout-tls-hook-cascade-flake`](../fixtures/gha/checkout-tls-hook-cascade-flake)、[`service-healthcheck-timeout-flake`](../fixtures/gha/service-healthcheck-timeout-flake)、[`helm-healthcheck-timeout-flake`](../fixtures/gha/helm-healthcheck-timeout-flake)、[`external-host-chronic-flake`](../fixtures/gha/external-host-chronic-flake)。只有 hook、没有 checkout 错误仍低于阈值（`checkout-hook-only-unknown`）。健康检查和 `AssertionError` 打平仍是 `unknown`（`healthcheck-and-assertion-unknown`）。外部主机每次都失败仍是 `flake`，应改用镜像或仓库内文件，而不是反复重跑同一个 URL。只有 `toomanyrequests`、Cypress “Timed out retrying after”、Git LFS 速率限制也是 `flake`。速率限制和 `pull access denied` 打平仍是 `unknown`（`registry-rate-and-auth-unknown`）。只有 “retry N of M” 的分片仍是 `unknown`（`shard-retry-only-unknown`）。

**最小下一步：** 先引用重跑或超时那一行。优先改成确定性等待，而不是只把超时调大。重跑一次是证据，不是修复。

## env

作业死在一个缺失的名字上：环境变量、action 输入，或从未提供的 secret。报告里不能出现值。

**信号：** “Required environment variable NAME is not set”、“Input required and not supplied”、“NAME is empty”、“secret NAME was not provided”。

**不是这类：** `GITHUB_TOKEN` 的 403（`permissions`）、peer 冲突（`deps`）。

**Fixture：** [`missing-database-url`](../fixtures/gha/missing-database-url)、[`missing-node-auth-token`](../fixtures/gha/missing-node-auth-token)、[`unset-api-base-url`](../fixtures/gha/unset-api-base-url)、[`secret-signing-key-missing`](../fixtures/gha/secret-signing-key-missing)、[`aws-region-undefined`](../fixtures/gha/aws-region-undefined)、[`compose-db-url-unset`](../fixtures/gha/compose-db-url-unset)、[`node-engine-mismatch-env`](../fixtures/gha/node-engine-mismatch-env)、[`setup-python-version-missing-env`](../fixtures/gha/setup-python-version-missing-env)、[`composite-action-path-missing-env`](../fixtures/gha/composite-action-path-missing-env)。和 “does not have permission” 打平时仍是 `unknown`（`empty-token-and-permission-unknown`、`oidc-role-and-empty-arn-unknown`）。

**最小下一步：** 在 job 或该 job 使用的 Actions environment 上提供这个名字。不要编造值，也不要打印值。

## test

测试套件已经跑起来，某个期望失败了。Jest 的 `FAIL`、pytest 的 `FAILED`、`AssertionError`、expected 对 received。

**信号：** `AssertionError`、`expect(received)`、`FAIL path`、`go test` 的 `--- FAIL:`、`Expected:`、`Tests: N failed`、`FAILED path`、`Test Suites: N failed`、PHPUnit 的 “Failed asserting that”、RSpec 的 `Failure/Error:`、cargo 的 `test result: FAILED`。

**不是这类：** 另一次尝试通过的超时（`flake`）、`npm ci` 拒绝锁文件（`deps`）。

**Fixture：** [`npm-test-assertion`](../fixtures/gha/npm-test-assertion)、[`pytest-assertion`](../fixtures/gha/pytest-assertion)、[`go-test-want-got`](../fixtures/gha/go-test-want-got)、[`maven-surefire-assertion`](../fixtures/gha/maven-surefire-assertion)、[`phpunit-assert-failed`](../fixtures/gha/phpunit-assert-failed)、[`rspec-failure-error`](../fixtures/gha/rspec-failure-error)、[`cargo-test-result-failed`](../fixtures/gha/cargo-test-result-failed)、[`gradle-test-assertion`](../fixtures/gha/gradle-test-assertion)、[`multi-job-one-step-failed`](../fixtures/gha/multi-job-one-step-failed)。多 job 日志只给失败的 job 打分。

**最小下一步：** 改失败所指的产品代码或断言。不要删测试来换绿。

## deps

安装或解析失败。peer 冲突、`ERESOLVE`、`npm ci` 拒绝不同步的锁文件。

**信号：** `ERESOLVE`、“unable to resolve dependency tree”、“Conflicting peer dependency”、“Could not resolve dependency”、`package.json` 与 `package-lock.json` 不同步、“Missing: … from lock file”、`ERR_PNPM_OUTDATED_LOCKFILE`、pip 的 “Could not find a version that satisfies”、`yarn.lock` / `poetry.lock` / `uv.lock` 过期、Gradle “Could not resolve all files for configuration”、Bundler “add the updated Gemfile.lock” / “could not find compatible versions”、`missing go.sum entry` / “verifying module: checksum mismatch”、`Cargo.lock needs to be updated` / “failed to select a version”。

**不是这类：** 发布前缺少 `NODE_AUTH_TOKEN`（`env`）、干净安装之后才失败的测试（`test`）。

**Fixture：** [`npm-peer-eresolve`](../fixtures/gha/npm-peer-eresolve)、[`npm-ci-lockfile-drift`](../fixtures/gha/npm-ci-lockfile-drift)、[`pnpm-outdated-lockfile`](../fixtures/gha/pnpm-outdated-lockfile)、[`pip-version-unsatisfied`](../fixtures/gha/pip-version-unsatisfied)、[`yarn-lockfile-out-of-date`](../fixtures/gha/yarn-lockfile-out-of-date)、[`poetry-lock-out-of-date`](../fixtures/gha/poetry-lock-out-of-date)、[`uv-lock-needs-update`](../fixtures/gha/uv-lock-needs-update)、[`gradle-configuration-unresolved`](../fixtures/gha/gradle-configuration-unresolved)、[`bundler-lockfile-out-of-date`](../fixtures/gha/bundler-lockfile-out-of-date)、[`go-sum-checksum-mismatch`](../fixtures/gha/go-sum-checksum-mismatch)、[`cargo-lock-needs-update`](../fixtures/gha/cargo-lock-needs-update)、[`maven-dependencies-unresolved-deps`](../fixtures/gha/maven-dependencies-unresolved-deps)、[`swiftpm-package-unresolved-deps`](../fixtures/gha/swiftpm-package-unresolved-deps)、[`cocoapods-pod-conflict-deps`](../fixtures/gha/cocoapods-pod-conflict-deps)、[`nuget-package-not-found-deps`](../fixtures/gha/nuget-package-not-found-deps)。和 `AssertionError` 打平时仍是 `unknown`（`poetry-lock-and-assertion-unknown`）。缓存 `EACCES` 加锁文件仍是 `unknown`（`cache-eacces-and-lockfile-unknown`）。损坏的 `actions/cache` 恢复压过锁文件（`actions-cache-restore-corrupt`，`infra`）。`pnpm-lock.yaml` “not up to date” 是 deps（`pnpm-lock-not-up-to-date-deps`）。`continue-on-error` 步骤不会盖住后面的锁文件错误（`continue-on-error-lockfile-deps`）。

**最小下一步：** 对齐证据里的版本，或提交更新后的锁文件。不要先用 `--force` 或 `--legacy-peer-deps`。不要把 CI 里的 `npm ci` 换成 `npm install` 当作修复。

## permissions

token、角色或 `permissions:` 拒绝了某个 API。常见形态是 HTTP 403、“Resource not accessible by integration”，或 `git` 拒绝 `github-actions[bot]`。

**信号：** “Resource not accessible by integration”、“Permission to … denied”、“requested URL returned error: 403”、`HttpError` 403、“does not have permission”、“not granted contents:” / `issues:` / `pull-requests:` / `id-token:`。单独一行 “Refusing to force-push” 低于阈值（`force-push-refusal-only-unknown`）。

**不是这类：** 构建脚本里与 GitHub API 无关的文件系统 `EACCES`（看清路径后多半是 `infra` 或 `env`）、secret 的值缺失（`env`）。

**Fixture：** [`gha-token-integration-403`](../fixtures/gha/gha-token-integration-403)、[`git-push-permission-denied`](../fixtures/gha/git-push-permission-denied)、[`id-token-permission-denied`](../fixtures/gha/id-token-permission-denied)、[`bare-http-403`](../fixtures/gha/bare-http-403)、[`oidc-assume-role-denied`](../fixtures/gha/oidc-assume-role-denied)、[`registry-pull-auth-denied`](../fixtures/gha/registry-pull-auth-denied)。`pull access denied` 是 permissions。没有认证行的 `no such host` 是 `infra`。两行一起仍是 `unknown`（`registry-auth-and-egress-unknown`）。

**最小下一步：** 指出最窄的缺失 scope。不要改用个人访问令牌。不要 force-push。

## infra

宿主倒下了。堆内存耗尽、运行器磁盘满、进程被杀死、运行器关闭。断言不是缺陷。

**信号：** “JavaScript heap out of memory”、“Reached heap limit”、`OOMKilled`、“No space left on device”、“disk quota exceeded”、“runner process was killed”、“Cannot connect to the Docker daemon”、注册表拉取的 `dial tcp: lookup` / “no such host” / “network is unreachable” / “TLS handshake timeout” / “i/o timeout” / “egress blocked”、DNS 的 `getaddrinfo` / “Temporary failure in name resolution” / “Could not resolve host”、`Failed to restore cache`。单独的缓存 `EACCES` 仍低于阈值。和 “does not have permission” 打平的内存耗尽仍是 `unknown`（`oom-and-permission-unknown`）。egress 被阻断且 `remote: permission to … denied` 仍是 `unknown`（`egress-and-permission-unknown`）。

**不是这类：** 重跑通过的测试超时（`flake`）、checkout 证书校验失败（`flake`）、没有 DNS 或 egress 行的 `pull access denied`（`permissions`）、`npm` 解析错误（`deps`）。

**Fixture：** [`node-heap-oom`](../fixtures/gha/node-heap-oom)、[`runner-disk-full`](../fixtures/gha/runner-disk-full)、[`generic-oom-without-heap`](../fixtures/gha/generic-oom-without-heap)、[`runner-killed-exit-137`](../fixtures/gha/runner-killed-exit-137)、[`docker-build-disk-full`](../fixtures/gha/docker-build-disk-full)、[`docker-daemon-unavailable`](../fixtures/gha/docker-daemon-unavailable)、[`mcr-pull-egress-blocked`](../fixtures/gha/mcr-pull-egress-blocked)、[`ghcr-pull-io-timeout`](../fixtures/gha/ghcr-pull-io-timeout)、[`dns-name-resolution-infra`](../fixtures/gha/dns-name-resolution-infra)、[`actions-cache-restore-corrupt`](../fixtures/gha/actions-cache-restore-corrupt)、[`kernel-oom-killed-infra`](../fixtures/gha/kernel-oom-killed-infra)、[`self-hosted-runner-offline-infra`](../fixtures/gha/self-hosted-runner-offline-infra)、[`windows-filename-too-long-infra`](../fixtures/gha/windows-filename-too-long-infra)、[`runner-arch-mismatch-infra`](../fixtures/gha/runner-arch-mismatch-infra)、[`docker-layer-cache-missing-infra`](../fixtures/gha/docker-layer-cache-missing-infra)。单独一行 `Killed` 是 infra。“failed to compute cache key” 不是 pytest。

**最小下一步：** 只改一处资源（堆上限、更少产物、更大的 runner）。关闭之后重跑一次是合理的。第二次还是同样的宿主失败，就停止。

## unknown

日志没有足够强的 v0 信号，或两类打平。这是合法答案。

**信号：** 几乎只有一行 “Process completed with exit code 1”，或一行取消且没有其他信号。低于阈值的弱命中仍然是 `unknown`。两类得分相同且都达到 6，也是 `unknown`。`canceled-step-unknown` 故意不命中 v0 的任何规则。

**不是这类：** 用来藏一个猜测的桶。不要在报告里发明第八个类别。不要把文件系统 `EACCES` 当成 `permissions`，也不要把低于阈值的 force-push 拒绝当成可以 force-push。

**Fixture：** [`bare-exit-unknown`](../fixtures/gha/bare-exit-unknown)、[`canceled-step-unknown`](../fixtures/gha/canceled-step-unknown)、[`timeout-and-assertion-unknown`](../fixtures/gha/timeout-and-assertion-unknown)、[`empty-token-and-permission-unknown`](../fixtures/gha/empty-token-and-permission-unknown)、[`force-push-refusal-only-unknown`](../fixtures/gha/force-push-refusal-only-unknown)、[`cache-eacces-unknown`](../fixtures/gha/cache-eacces-unknown)、[`concurrency-cancel-unknown`](../fixtures/gha/concurrency-cancel-unknown)、[`poetry-lock-and-assertion-unknown`](../fixtures/gha/poetry-lock-and-assertion-unknown)、[`oom-and-permission-unknown`](../fixtures/gha/oom-and-permission-unknown)、[`oidc-role-and-empty-arn-unknown`](../fixtures/gha/oidc-role-and-empty-arn-unknown)、[`shard-retry-only-unknown`](../fixtures/gha/shard-retry-only-unknown)、[`checkout-tls-and-assertion-unknown`](../fixtures/gha/checkout-tls-and-assertion-unknown)、[`dataset-and-assertion-unknown`](../fixtures/gha/dataset-and-assertion-unknown)、[`egress-and-permission-unknown`](../fixtures/gha/egress-and-permission-unknown)、[`checkout-hook-only-unknown`](../fixtures/gha/checkout-hook-only-unknown)、[`multi-job-green-noise-unknown`](../fixtures/gha/multi-job-green-noise-unknown)、[`registry-auth-and-egress-unknown`](../fixtures/gha/registry-auth-and-egress-unknown)、[`healthcheck-and-assertion-unknown`](../fixtures/gha/healthcheck-and-assertion-unknown)、[`cache-eacces-and-lockfile-unknown`](../fixtures/gha/cache-eacces-and-lockfile-unknown)。

**最小下一步：** 要失败步骤的名字，以及退出码上面的那些行。在等到之前不要顺手重构。

## 0.13.0 新增

作业 “exceeded the maximum execution time” 是 `infra`（`job-max-execution-time-infra`）。步骤 “has timed out after N minutes” 是 `flake`（`step-timeout-minutes-flake`）。这两类和 `AssertionError` 打平仍是 `unknown`（`job-timeout-and-assertion-unknown`）。只有 exit code 137 是 `infra`（`bare-exit-137-infra`）。“no runners available” 是 `infra`（`no-runners-available-infra`）。Playwright 找不到浏览器可执行文件是 `deps`（`playwright-browser-missing-deps`）；浏览器下载失败是 `flake`（`playwright-browser-download-flake`、`cypress-binary-download-flake`）。Terraform provider lock 不一致是 `deps`（`terraform-provider-lock-deps`），不是 state lock。`ERR_PNPM_TARBALL_INTEGRITY` 是 `deps`（`pnpm-tarball-integrity-deps`）。LFS 配额是 `permissions`（`git-lfs-budget-exceeded-permissions`）。没有速率也没有配额的 git-lfs smudge 失败是 `env`（`git-lfs-smudge-failed-env`）。因为另一个 matrix 单元失败而被取消、且没有断言，保持 `unknown`（`matrix-cancel-sibling-unknown`）。

## 0.14.0 新增

Docker 构建上下文超过限制是 `infra`（`docker-build-context-too-large-infra`）。BuildKit `cache export failed` 是 `infra`（`buildx-cache-export-failed-infra`）。Helm 升级或 collector 抓取出现 `context deadline exceeded` 是 `flake`（`helm-upgrade-deadline-flake`、`otel-collector-scrape-timeout-flake`）。NuGet 401 是 `permissions`（`nuget-feed-unauthorized-permissions`）。NuGet 503 是 `flake`（`nuget-feed-503-flake`），不是缺包。crates.io 429 是 `flake`（`cargo-crates-io-rate-limit-flake`）。被 yank 的 crate 是 `deps`（`cargo-crate-yanked-deps`）。找不到 Xcode DerivedData 是 `env`（`xcode-derived-data-missing-env`）。`vm.max_map_count` 过低是 `infra`（`elasticsearch-vm-max-map-count-infra`）。Redis `LOADING` 是 `flake`（`redis-loading-not-ready-flake`）。缺少 Codecov token 是 `env`（`codecov-token-missing-env`）。覆盖率上传超时是 `flake`（`codecov-upload-timeout-flake`）。Codecov `401 Invalid token` 是 `permissions`（`codecov-token-rejected-permissions`）。Windows `PathTooLongException` 是 `infra`（`windows-path-too-long-infra`）。`com.apple.quarantine` 是 `permissions`（`macos-quarantine-blocked-permissions`）。System Integrity Protection 是 `infra`（`macos-sip-blocked-infra`）。只有 Dependabot 这一个词、没有解析行，保持 `unknown`（`dependabot-word-only-unknown`）。

## 0.15.0 新增

`not authorized to perform` 或 `AccessDeniedException` 是 `permissions`（`ecr-pull-denied-permissions`、`codeartifact-token-denied-permissions`）。CodeArtifact 429 是 `flake`（`codeartifact-429-flake`）。Artifactory 403 是 `permissions`（`artifactory-403-permissions`）。Artifactory 429 是 `flake`（`artifactory-429-flake`）。`go.sum database checksum mismatch` 是 `deps`（`gosum-database-mismatch-deps`）。Go proxy 的 context deadline 是 `flake`（`go-proxy-deadline-flake`）。Packagist 429 是 `flake`（`packagist-429-flake`）。被 yank 的 gem 是 `deps`（`gem-version-yanked-deps`）。Rubygems 503 是 `flake`（`rubygems-503-flake`）。Deno `--allow-net` 是 `permissions`（`deno-permission-prompt-permissions`）。sparse-checkout 漏路径是 `env`（`sparse-checkout-miss-env`）。SELinux `avc: denied` 和 AppArmor `DENIED` 是 `infra`（`selinux-avc-denied-infra`、`apparmor-denied-infra`）。`packageManager` 字段不一致是 `env`（`corepack-packagemanager-mismatch-env`）。`getStaticPaths` 路径冲突是 `test`（`next-static-path-collision-test`）。并发组取消会点名自己，但仍低于阈值（`concurrency-cancel-unknown`）。因为另一个 matrix 单元失败而取消、没有信号，仍是 `unknown`（`matrix-cancel-sibling-unknown`）。

## 0.16.0 新增

`ImagePullBackOff` 是 `infra`（`kube-image-pull-backoff-infra`）。`CrashLoopBackOff` 是 `test`（`kube-crashloop-backoff-test`）。Gradle 或 Maven wrapper 校验和不符是 `deps`（`gradle-wrapper-checksum-deps`、`maven-wrapper-checksum-deps`）。SQLite `database is locked` 是 `flake`（`sqlite-database-locked-flake`）。Postgres `too many clients already` 是 `infra`（`postgres-too-many-clients-infra`）。Android Gradle plugin 和 Gradle 不兼容是 `env`（`android-gradle-plugin-mismatch-env`）。找不到 Ansible vault 密码文件是 `env`（`ansible-vault-password-missing-env`）。CDN 520 是 `flake`（`cloudflare-520-flake`）。子模块没有 URL 是 `env`（`git-submodule-not-initialized-env`）。Hugging Face 429 是 `flake`（`huggingface-rate-limit-flake`）。受限模型是 `permissions`（`huggingface-gated-model-permissions`）。`SolvePackageNotFound` 和 `PackagesNotFoundError` 是 `deps`（`pixi-solve-not-found-deps`、`conda-package-not-found-deps`）。Bazel analysis 失败是 `test`（`bazel-analysis-failed-test`）。Bazel 仓库拉取失败是 `flake`（`bazel-fetch-failed-flake`）。Terraform state lock 本来就是 `flake`（`terraform-state-lock-flake`）。

## 0.17.0 新增

连不上 Podman 是 `infra`（`podman-socket-unavailable-infra`）。端口已被占用是 `infra`（`testcontainers-port-conflict-infra`）。Kafka broker 还没就绪是 `flake`（`kafka-broker-not-ready-flake`）。MongoDB 认证失败是 `permissions`（`mongodb-auth-failed-permissions`）。MongoDB 拒绝连接是 `flake`（`mongodb-connection-refused-flake`）。缺少 `SENTRY_AUTH_TOKEN` 是 `env`（`sentry-token-missing-env`）。质量门失败是 `test`（`sonar-quality-gate-failed-test`）。`sonar.token` 被拒绝是 `permissions`（`sonar-token-rejected-permissions`）。缺少 Coveralls repo token 是 `env`（`coveralls-token-missing-env`）。发布要求 provenance 是 `permissions`（`npm-provenance-required-permissions`）。GitHub Packages 403 是 `permissions`（`github-packages-publish-403-permissions`）。包版本被取消发布是 `deps`（`github-packages-unpublished-deps`）。mypy 缓存损坏是 `infra`（`mypy-cache-corrupt-infra`）。Prettier 检查失败是 `test`（`prettier-check-drift-test`）。远程缓存拒绝 token 是 `permissions`（`turbo-remote-unauthorized-permissions`）。远程缓存连不上是 `infra`（`nx-remote-cache-unreachable-infra`）。Earthly 或 Dagger 引擎断开是 `infra`（`earthly-daemon-unavailable-infra`、`dagger-engine-disconnect-infra`）。

## 0.18.0 新增

Slack webhook `404 no_service` 是 `env`（`slack-webhook-404-env`）。Slack `ratelimited` 是 `flake`（`slack-rate-limit-flake`）。缺少 `DD_API_KEY` 或 `NEW_RELIC_LICENSE_KEY` 是 `env`（`datadog-api-key-missing-env`、`newrelic-license-missing-env`）。Pulumi 栈被锁是 `flake`（`pulumi-stack-locked-flake`）。Pulumi 未登录是 `env`（`pulumi-login-missing-env`）。Workers 部署未授权是 `permissions`（`cloudflare-workers-auth-permissions`），不是 CDN 520。缺少 Vercel token 是 `env`（`vercel-token-missing-env`）。`next build` 失败或 Netlify building site 阶段失败是 `test`（`vercel-build-failed-test`、`netlify-build-failed-test`）。Netlify 认证失败是 `permissions`（`netlify-auth-failed-permissions`）。数据库迁移版本 dirty 是 `env`（`laravel-migrate-dirty-env`）。Django 迁移冲突是 `test`（`django-migrate-conflict-test`）。Prisma drift 是 `env`（`prisma-migrate-drift-env`）。Prisma `P1001` 是 `flake`（`prisma-p1001-flake`）。GraphQL schema 合并不了是 `test`（`graphql-schema-conflict-test`）。缺少 Chromatic 或 Percy token 是 `env`（`visual-snapshot-token-missing-env`）。`wasm-ld` 失败是 `test`（`wasm-link-failed-test`）。

## 如何扩展

先加 fixture，再加信号，然后改本文件和 [`skills/ci-doctor/references/taxonomy.md`](../skills/ci-doctor/references/taxonomy.md)。重命名 id 是分类版本变更，不是顺手一改。见 [CONTRIBUTING.md](../CONTRIBUTING.md)。
