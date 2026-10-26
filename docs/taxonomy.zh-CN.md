# 分类 v0

[English](taxonomy.md)

七个类别。id 是契约：`flake`、`env`、`test`、`deps`、`permissions`、`infra`、`unknown`。诊断命令按 [`scripts/diagnose.py`](../scripts/diagnose.py) 里的信号打分。某一类得分至少为 6 且领先时胜出。低于阈值则是 `unknown`。两类在阈值上打平，也是 `unknown`。

置信度：`high`（≥ 0.80）、`medium`（≥ 0.60）、`low`。`unknown` 故意是 low。这些都不是“可以合并”。

日志可以是步骤原文，也可以是 `gh run view --log-failed` 的行（job、step、时间戳）。匹配前会去掉前缀。

## flake

失败会自己挪位置：超时后重跑通过、被标成间歇性的测试、某一次编号重试变绿。

**信号：** “suspected flake”、“exceeded timeout of N”、“timeout of N ms exceeded”、“passed on the previous run” 或 “passed on the automatic rerun”、“intermittent”、“retry N of M”、checkout 的 “SSL certificate problem” / “server certificate verification failed” / “unable to get local issuer certificate” / “The TLS connection was non-properly terminated”、“failed to download the external dataset”、“external host timed out”。和 `AssertionError` 打平时仍是 `unknown`（`timeout-and-assertion-unknown`、`checkout-tls-and-assertion-unknown`、`dataset-and-assertion-unknown`）。

**不是这类：** 稳定的断言（`test`）、运行器内存耗尽（`infra`）、注册表 DNS 或 egress 失败（`infra`）、包不存在的 404（`deps`）。

**Fixture：** [`jest-timeout-flake`](../fixtures/gha/jest-timeout-flake)、[`registry-timeout-rerun-flake`](../fixtures/gha/registry-timeout-rerun-flake)、[`playwright-timeout-flake`](../fixtures/gha/playwright-timeout-flake)、[`cypress-timeout-flake`](../fixtures/gha/cypress-timeout-flake)、[`matrix-shard-flake`](../fixtures/gha/matrix-shard-flake)、[`docker-rate-limit-flake`](../fixtures/gha/docker-rate-limit-flake)、[`checkout-tls-verify-flake`](../fixtures/gha/checkout-tls-verify-flake)、[`external-dataset-host-flake`](../fixtures/gha/external-dataset-host-flake)、[`checkout-tls-hook-cascade-flake`](../fixtures/gha/checkout-tls-hook-cascade-flake)。只有 hook、没有 checkout 错误仍低于阈值（`checkout-hook-only-unknown`）。只有 “retry N of M” 的分片仍是 `unknown`（`shard-retry-only-unknown`）。

**最小下一步：** 先引用重跑或超时那一行。优先改成确定性等待，而不是只把超时调大。重跑一次是证据，不是修复。

## env

作业死在一个缺失的名字上：环境变量、action 输入，或从未提供的 secret。报告里不能出现值。

**信号：** “Required environment variable NAME is not set”、“Input required and not supplied”、“NAME is empty”、“secret NAME was not provided”。

**不是这类：** `GITHUB_TOKEN` 的 403（`permissions`）、peer 冲突（`deps`）。

**Fixture：** [`missing-database-url`](../fixtures/gha/missing-database-url)、[`missing-node-auth-token`](../fixtures/gha/missing-node-auth-token)、[`unset-api-base-url`](../fixtures/gha/unset-api-base-url)、[`secret-signing-key-missing`](../fixtures/gha/secret-signing-key-missing)、[`aws-region-undefined`](../fixtures/gha/aws-region-undefined)、[`compose-db-url-unset`](../fixtures/gha/compose-db-url-unset)。和 “does not have permission” 打平时仍是 `unknown`（`empty-token-and-permission-unknown`、`oidc-role-and-empty-arn-unknown`）。

**最小下一步：** 在 job 或该 job 使用的 Actions environment 上提供这个名字。不要编造值，也不要打印值。

## test

测试套件已经跑起来，某个期望失败了。Jest 的 `FAIL`、pytest 的 `FAILED`、`AssertionError`、expected 对 received。

**信号：** `AssertionError`、`expect(received)`、`FAIL path`、`go test` 的 `--- FAIL:`、`Expected:`、`Tests: N failed`、`FAILED path`、`Test Suites: N failed`、PHPUnit 的 “Failed asserting that”、RSpec 的 `Failure/Error:`、cargo 的 `test result: FAILED`。

**不是这类：** 另一次尝试通过的超时（`flake`）、`npm ci` 拒绝锁文件（`deps`）。

**Fixture：** [`npm-test-assertion`](../fixtures/gha/npm-test-assertion)、[`pytest-assertion`](../fixtures/gha/pytest-assertion)、[`go-test-want-got`](../fixtures/gha/go-test-want-got)、[`maven-surefire-assertion`](../fixtures/gha/maven-surefire-assertion)、[`phpunit-assert-failed`](../fixtures/gha/phpunit-assert-failed)、[`rspec-failure-error`](../fixtures/gha/rspec-failure-error)、[`cargo-test-result-failed`](../fixtures/gha/cargo-test-result-failed)、[`gradle-test-assertion`](../fixtures/gha/gradle-test-assertion)、[`multi-job-one-step-failed`](../fixtures/gha/multi-job-one-step-failed)。多 job 日志只给失败的 job 打分。

**最小下一步：** 改失败所指的产品代码或断言。不要删测试来换绿。

## deps

安装或解析失败。peer 冲突、`ERESOLVE`、`npm ci` 拒绝不同步的锁文件。

**信号：** `ERESOLVE`、“unable to resolve dependency tree”、“Conflicting peer dependency”、“Could not resolve dependency”、`package.json` 与 `package-lock.json` 不同步、“Missing: … from lock file”、`ERR_PNPM_OUTDATED_LOCKFILE`、pip 的 “Could not find a version that satisfies”、`yarn.lock` / `poetry.lock` / `uv.lock` 过期、Gradle “Could not resolve all files for configuration”。

**不是这类：** 发布前缺少 `NODE_AUTH_TOKEN`（`env`）、干净安装之后才失败的测试（`test`）。

**Fixture：** [`npm-peer-eresolve`](../fixtures/gha/npm-peer-eresolve)、[`npm-ci-lockfile-drift`](../fixtures/gha/npm-ci-lockfile-drift)、[`pnpm-outdated-lockfile`](../fixtures/gha/pnpm-outdated-lockfile)、[`pip-version-unsatisfied`](../fixtures/gha/pip-version-unsatisfied)、[`yarn-lockfile-out-of-date`](../fixtures/gha/yarn-lockfile-out-of-date)、[`poetry-lock-out-of-date`](../fixtures/gha/poetry-lock-out-of-date)、[`uv-lock-needs-update`](../fixtures/gha/uv-lock-needs-update)、[`gradle-configuration-unresolved`](../fixtures/gha/gradle-configuration-unresolved)。和 `AssertionError` 打平时仍是 `unknown`（`poetry-lock-and-assertion-unknown`）。

**最小下一步：** 对齐证据里的版本，或提交更新后的锁文件。不要先用 `--force` 或 `--legacy-peer-deps`。不要把 CI 里的 `npm ci` 换成 `npm install` 当作修复。

## permissions

token、角色或 `permissions:` 拒绝了某个 API。常见形态是 HTTP 403、“Resource not accessible by integration”，或 `git` 拒绝 `github-actions[bot]`。

**信号：** “Resource not accessible by integration”、“Permission to … denied”、“requested URL returned error: 403”、`HttpError` 403、“does not have permission”、“not granted contents:” / `issues:` / `pull-requests:` / `id-token:`。单独一行 “Refusing to force-push” 低于阈值（`force-push-refusal-only-unknown`）。

**不是这类：** 构建脚本里与 GitHub API 无关的文件系统 `EACCES`（看清路径后多半是 `infra` 或 `env`）、secret 的值缺失（`env`）。

**Fixture：** [`gha-token-integration-403`](../fixtures/gha/gha-token-integration-403)、[`git-push-permission-denied`](../fixtures/gha/git-push-permission-denied)、[`id-token-permission-denied`](../fixtures/gha/id-token-permission-denied)、[`bare-http-403`](../fixtures/gha/bare-http-403)、[`oidc-assume-role-denied`](../fixtures/gha/oidc-assume-role-denied)、[`registry-pull-auth-denied`](../fixtures/gha/registry-pull-auth-denied)。`pull access denied` 是 permissions。没有认证行的 `no such host` 是 `infra`。两行一起仍是 `unknown`（`registry-auth-and-egress-unknown`）。

**最小下一步：** 指出最窄的缺失 scope。不要改用个人访问令牌。不要 force-push。

## infra

宿主倒下了。堆内存耗尽、运行器磁盘满、进程被杀死、运行器关闭。断言不是缺陷。

**信号：** “JavaScript heap out of memory”、“Reached heap limit”、`OOMKilled`、“No space left on device”、“disk quota exceeded”、“runner process was killed”、“Cannot connect to the Docker daemon”、注册表拉取的 `dial tcp: lookup` / “no such host” / “network is unreachable” / “TLS handshake timeout” / “i/o timeout” / “egress blocked”。和 “does not have permission” 打平的内存耗尽仍是 `unknown`（`oom-and-permission-unknown`）。egress 被阻断且 `remote: permission to … denied` 仍是 `unknown`（`egress-and-permission-unknown`）。

**不是这类：** 重跑通过的测试超时（`flake`）、checkout 证书校验失败（`flake`）、没有 DNS 或 egress 行的 `pull access denied`（`permissions`）、`npm` 解析错误（`deps`）。

**Fixture：** [`node-heap-oom`](../fixtures/gha/node-heap-oom)、[`runner-disk-full`](../fixtures/gha/runner-disk-full)、[`generic-oom-without-heap`](../fixtures/gha/generic-oom-without-heap)、[`runner-killed-exit-137`](../fixtures/gha/runner-killed-exit-137)、[`docker-build-disk-full`](../fixtures/gha/docker-build-disk-full)、[`docker-daemon-unavailable`](../fixtures/gha/docker-daemon-unavailable)、[`mcr-pull-egress-blocked`](../fixtures/gha/mcr-pull-egress-blocked)、[`ghcr-pull-io-timeout`](../fixtures/gha/ghcr-pull-io-timeout)。

**最小下一步：** 只改一处资源（堆上限、更少产物、更大的 runner）。关闭之后重跑一次是合理的。第二次还是同样的宿主失败，就停止。

## unknown

日志没有足够强的 v0 信号，或两类打平。这是合法答案。

**信号：** 几乎只有一行 “Process completed with exit code 1”，或一行取消且没有其他信号。低于阈值的弱命中仍然是 `unknown`。两类得分相同且都达到 6，也是 `unknown`。`canceled-step-unknown` 故意不命中 v0 的任何规则。

**不是这类：** 用来藏一个猜测的桶。不要在报告里发明第八个类别。不要把文件系统 `EACCES` 当成 `permissions`，也不要把低于阈值的 force-push 拒绝当成可以 force-push。

**Fixture：** [`bare-exit-unknown`](../fixtures/gha/bare-exit-unknown)、[`canceled-step-unknown`](../fixtures/gha/canceled-step-unknown)、[`timeout-and-assertion-unknown`](../fixtures/gha/timeout-and-assertion-unknown)、[`empty-token-and-permission-unknown`](../fixtures/gha/empty-token-and-permission-unknown)、[`force-push-refusal-only-unknown`](../fixtures/gha/force-push-refusal-only-unknown)、[`cache-eacces-unknown`](../fixtures/gha/cache-eacces-unknown)、[`concurrency-cancel-unknown`](../fixtures/gha/concurrency-cancel-unknown)、[`poetry-lock-and-assertion-unknown`](../fixtures/gha/poetry-lock-and-assertion-unknown)、[`oom-and-permission-unknown`](../fixtures/gha/oom-and-permission-unknown)、[`oidc-role-and-empty-arn-unknown`](../fixtures/gha/oidc-role-and-empty-arn-unknown)、[`shard-retry-only-unknown`](../fixtures/gha/shard-retry-only-unknown)、[`checkout-tls-and-assertion-unknown`](../fixtures/gha/checkout-tls-and-assertion-unknown)、[`dataset-and-assertion-unknown`](../fixtures/gha/dataset-and-assertion-unknown)、[`egress-and-permission-unknown`](../fixtures/gha/egress-and-permission-unknown)、[`checkout-hook-only-unknown`](../fixtures/gha/checkout-hook-only-unknown)、[`multi-job-green-noise-unknown`](../fixtures/gha/multi-job-green-noise-unknown)、[`registry-auth-and-egress-unknown`](../fixtures/gha/registry-auth-and-egress-unknown)。

**最小下一步：** 要失败步骤的名字，以及退出码上面的那些行。在等到之前不要顺手重构。

## 如何扩展

先加 fixture，再加信号，然后改本文件和 [`skills/ci-doctor/references/taxonomy.md`](../skills/ci-doctor/references/taxonomy.md)。重命名 id 是分类版本变更，不是顺手一改。见 [CONTRIBUTING.md](../CONTRIBUTING.md)。
