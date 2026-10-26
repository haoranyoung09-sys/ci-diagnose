# permissions

GitHub refused the token. Quote the API or the ref, and the missing scope if the log names one.

## When to follow this

The CLI category is `permissions`. Signals include "Resource not accessible by integration", "Permission to … denied", "requested URL returned error: 403", `HttpError` 403, "does not have permission", "not granted" plus `contents:` / `issues:` / `pull-requests:` / `id-token:`, "insufficient permissions".

Corpus: `gha-token-integration-403`, `git-push-permission-denied`, `id-token-permission-denied`, `bare-http-403`, `oidc-assume-role-denied`.

`bare-http-403` is a weak win: one 403 and no scope name. Say the confidence is not high and ask which API and which `permissions:` key. Do not grant a scope you cannot name.

## Near misses

| What you see | What to do |
| --- | --- |
| "does not have permission" tied with "NAME is empty" (`empty-token-and-permission-unknown`) | Stay `unknown`. Do not grant permissions and do not paste a token. |
| Only "Refusing to force-push", score under the threshold (`force-push-refusal-only-unknown`) | Stay `unknown`. That line is a guardrail, not a category win, and not a suggestion to force-push. |
| `EACCES` on a runner path such as `_temp` or a cache dir (`cache-eacces-unknown`) | Not this category. There is no GitHub API 403. Follow `unknown` until a path or identity is clear. |
| "secret NAME was not provided" | `env`. The value was never supplied. Do not widen `permissions:`. |
| `id-token: write` in the log | Quote it as a scope. Do not redact the word `write`. The CLI leaves `id-token: write` intact on purpose. |
| OIDC assume-role failed and the log names `id-token: write` (`oidc-assume-role-denied`) | Quote the role ARN and that scope. Do not print a web identity token and do not add a long-lived cloud key. |
| Empty role name tied with "does not have permission" (`oidc-role-and-empty-arn-unknown`) | Stay `unknown`. Do not invent the ARN. |

## Recipe

1. Quote the API, git ref, or cloud role ARN, and the scope if present (`contents: write`, `issues: write`, `pull-requests: write`, `id-token: write`). For OIDC, the fix is that scope plus the cloud trust policy, not a static key.
2. Suggest the narrowest `permissions:` key that covers that call. One key.
3. If the log has a 403 and no key (`bare-http-403`), name the HTTP line and ask which API it was. Do not guess `packages: write` or `contents: write` without a noun in the evidence.
4. Do not switch the job to a personal access token. Do not ask the user to paste a token.
5. Do not force-push. A line that says the job refused to force-push is a guardrail. Never `git push --force` or `--force-with-lease`.
6. If the repository forbids `GITHUB_TOKEN` writes, say so and stop. You cannot fix that from a workflow edit.

## Verify

- Re-run the job after the workflow change. That rerun is attempt 1.
- Same failure: the same API and the same 403 text.
- New failure: a 403 from a different API. That is a new finding. It is not a cue to grant `write-all`. A second workflow edit is attempt 2.
- Do not verify by printing `GITHUB_TOKEN` or `GH_TOKEN`.
- Fixture check only re-scores the saved log.

## Stop

- Two permission misses, including two different APIs.
- A policy you cannot change from the workflow file.
- The only next step you can think of is `permissions: write-all`, a PAT, or a force-push. Refuse that step and stop.
- The CLI category was `unknown` because of a tie or a below-threshold force-push line. Do not spend an attempt anyway.

## 中文

引用 API、ref 或云角色 ARN，以及日志里点名的最窄 scope。OIDC（`oidc-assume-role-denied`）要的是 `id-token: write` 和信任策略，不是长期密钥，也不要打印 web identity token。`oidc-role-and-empty-arn-unknown` 与 `empty-token-and-permission-unknown` 都是打平。只有一行 `HttpError: 403` 时先问 API。禁止 force-push，不要授予 `write-all`。两次 403 或组织策略改不了，就停止。
