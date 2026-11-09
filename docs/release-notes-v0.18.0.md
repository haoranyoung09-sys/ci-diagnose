# ci-fail-classify 0.18.0

Clone, `uses:`, and the install curl URL stay on `haoranyoung09-sys/ci-diagnose`. The Action display name stays `ci-fail-classify`. Inputs, outputs, and branding are unchanged.

This is still diagnosis only. It does not build, sign, or host the app. Compared with faultline, patchrail, failsift, ci-failure-explainer, and ci-medic, this remains the scored seven-class classifier and the offline fixture oracle.

## What the new fixtures catch

245 fixtures. Eval 245/245.

| What you see | Category | Fixture |
| --- | --- | --- |
| Slack webhook 404 no_service | env | `slack-webhook-404-env` |
| Slack API ratelimited | flake | `slack-rate-limit-flake` |
| DD_API_KEY is not set | env | `datadog-api-key-missing-env` |
| NEW_RELIC_LICENSE_KEY was not provided | env | `newrelic-license-missing-env` |
| Pulumi stack is locked | flake | `pulumi-stack-locked-flake` |
| Pulumi is not logged in | env | `pulumi-login-missing-env` |
| Workers deploy was not authorized | permissions | `cloudflare-workers-auth-permissions` |
| VERCEL_TOKEN is missing | env | `vercel-token-missing-env` |
| next build exited 1 | test | `vercel-build-failed-test` |
| Netlify authentication failed | permissions | `netlify-auth-failed-permissions` |
| Netlify building site failed | test | `netlify-build-failed-test` |
| Dirty database version | env | `laravel-migrate-dirty-env` |
| Conflicting Django migrations | test | `django-migrate-conflict-test` |
| Prisma schema drift | env | `prisma-migrate-drift-env` |
| Prisma P1001 | flake | `prisma-p1001-flake` |
| GraphQL schema could not be merged | test | `graphql-schema-conflict-test` |
| Chromatic or Percy token missing | env | `visual-snapshot-token-missing-env` |
| wasm-ld failed | test | `wasm-link-failed-test` |

CDN error 520 was already `flake`. A JavaScript heap OOM, including a Storybook or Heroku slug compile that only prints that line, was already `infra`. A `FAIL path` line from Pint was already `test`.

## Install

After tag `v0.18.0` is on the public mirror:

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-diagnose/v0.18.0/scripts/install.sh | bash
```

```yaml
- uses: haoranyoung09-sys/ci-diagnose@v1
```

## 中文

clone、`uses:` 和安装用的 curl 地址仍是 `haoranyoung09-sys/ci-diagnose`。Action 显示名仍是 `ci-fail-classify`。输入、输出和 branding 不变。

这仍只做诊断。和 faultline、patchrail、failsift、ci-failure-explainer、ci-medic 相比，这里仍是可以打分的七类分类器和离线 fixture。

245 条 fixture，eval 245/245。Slack webhook 404、缺少 Datadog 或 New Relic key、Pulumi 未登录、缺少 Vercel token、迁移 dirty、Prisma drift、缺少 Chromatic 或 Percy token 是 `env`。Slack 速率限制、Pulumi 栈锁、Prisma P1001 是 `flake`。Workers 部署未授权和 Netlify 认证失败是 `permissions`。站点构建失败、Django 迁移冲突、GraphQL schema 合并不了、`wasm-ld` 失败是 `test`。CDN 520 本来就是 `flake`。只有堆内存耗尽那一行的 Storybook 或 Heroku 编译本来就是 `infra`。

公开镜像有 `v0.18.0` 之后，安装命令钉这个标签。`@v1` 只在这个 commit 已经在公开镜像上时才移动。
