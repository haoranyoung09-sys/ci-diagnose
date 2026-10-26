# env

A name was missing. The value must stay out of the report, the workflow file, and the chat.

## When to follow this

The CLI category is `env`. Typical lines: "Required environment variable NAME is not set", "Environment variable NAME is undefined", "Input required and not supplied", "NAME is empty", "secret NAME was not provided".

Corpus: `missing-database-url`, `missing-node-auth-token`, `unset-api-base-url`, `secret-signing-key-missing`, `aws-region-undefined`, `compose-db-url-unset`.

## Near misses

| What you see | What to do |
| --- | --- |
| "NAME is empty" and "does not have permission" together (`empty-token-and-permission-unknown`) | Tie. Stay `unknown`. Do not invent a token value and do not grant `write-all`. |
| GitHub returned 403 or "Resource not accessible by integration" | `permissions`. The name exists; the grant does not. |
| `ERESOLVE` or a lockfile out of date | `deps`. An empty `NODE_AUTH_TOKEN` is env only when that empty-name line is the winning signal, as in `missing-node-auth-token`. |
| The log prints a value after `password=` or `Authorization:` | Do not repeat it. The CLI redacts common shapes. Quote the variable name only. |

## Recipe

1. Quote the line that names the missing variable, input, or secret. Copy the name exactly. Do not copy a value, even if one is present.
2. Say where that name has to live:
   - job `env:` for a non-secret configuration name (`API_BASE_URL`, `AWS_REGION`), or
   - the GitHub Actions environment the job already sets with `environment:`, for a secret (`DATABASE_URL`, `SIGNING_KEY`).
3. Check one trap before you declare the secret missing: a repository secret is invisible to a job that uses a different `environment:`. Say which of the two you are assuming, and ask if the log does not name the environment.
4. Do not invent a placeholder. Do not add `echo "$NAME"` to prove it is set. Do not commit a value.
5. One name per attempt. If the log names two, fix the one in the evidence line you quoted, then verify.

## Verify

- Re-run the single failed job after that name exists. That rerun is attempt 1 if you asked for it to test this hypothesis.
- Same failure: the same name is still reported missing.
- New failure: a different name, or a 403, or a resolver error. Report the new category. Editing for the new name is attempt 2.
- Success for this hypothesis: the job gets past the step that cited the name. Do not call the whole workflow safe to merge.
- Fixture check: `python3 scripts/diagnose.py --fixture <id>` confirms the label only.

## Stop

- Two distinct missing names have each had an attempt, and one is still missing.
- You cannot place the name without a value the user will not provide. Report the name and stop.
- The next error is a 403 or a lockfile conflict. Do not keep editing `env:` blocks. Hand off to that playbook, and stop if you are already on attempt 2.

## 中文

只引用变量或输入的名字，不引用值。仓库级 secret 对另一个 `environment:` 不可见，先核对 job 用的环境再判断缺失。`empty-token-and-permission-unknown` 是 `env` 和 `permissions` 打平，不要填一个假 token，也不要开 `write-all`。一次只补一个名字。下一个错误如果是 403 或锁文件，就换对应 playbook；已经是第二次尝试则停止。
