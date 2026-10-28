# GitHub Action

[中文](action.zh-CN.md)

`action.yml` is a composite action. It runs `python3 scripts/action_entry.py` on the runner. No npm install, no Docker image, no LLM.

The step writes a markdown report to `$GITHUB_STEP_SUMMARY` and sets outputs: `category`, `confidence`, `confidence-level`, `advisory`, `next-step`, `evidence`. `advisory` is always `true`. The category is one of `flake`, `env`, `test`, `deps`, `permissions`, `infra`, `unknown`.

## How a run gets its log

Pass one source.

| Input | Network | When to use it |
| --- | --- | --- |
| `log-path` | no | You saved the failing command with `tee`. Works in the same job, including `if: failure()`. |
| `fixture` | no | Demo or the self-test. The id is a directory under `fixtures/gha` inside this action. |
| `run-id` | GitHub API, `actions: read` | A **completed** workflow run. This is the right input for `workflow_run`. |

If you pass none of them, the action uses `github.run_id` and calls the logs API. A job that is still running has no log archive. The API returns 404. The step then writes `category: unknown` and tells you to use `workflow_run` or `log-path`. It does not post a pull request comment in that case.

Downloading logs follows the API redirect to blob storage and **drops** the `Authorization` header on that hop. The token is not printed.

When the zip contains both a failed job and a successful job, only the failed job files are scored.

## Pull request comment

`comment` defaults to `false`. Set `comment: true` to create one comment, or update the existing comment that contains `<!-- ci-doctor -->`. That call needs `pull-requests: write` and a pull request number (`pull-request`, or the workflow event). The comment is the same markdown as the job summary. It is not a merge approval.

Fork pull requests often cannot grant `pull-requests: write` to `GITHUB_TOKEN`. Leave `comment` off there.

## What you set on GitHub

This repository does not publish the Action by itself.

- Push this commit to the public mirror.
- Tag that commit `v0.7.0` (immutable) and move the tag `v1` to the same commit. `uses: haoranyoung09-sys/ci-diagnose@v1` tracks `v1`.
- Open a GitHub Release for `v0.7.0`. The Marketplace checkbox is on that release form. Paste [release-notes-v0.7.0.md](release-notes-v0.7.0.md).
- The example workflows set `permissions` themselves. If the repository's default token is read-only, keep those blocks. Log download needs `actions: read`. Comments need `pull-requests: write`.

Examples: [examples/workflows](../examples/workflows). The self-test is [`.github/workflows/action.yml`](../.github/workflows/action.yml). It runs `uses: ./` on a fixture and a saved log. It does not call the GitHub API.

`.github/workflows/triage-comment.yml` is still disabled (`if: false`). The supported comment path is `comment: true` on this action.
