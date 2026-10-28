# ci-diagnose 0.7.0

Drop CI Doctor into a workflow. The Action classifies a failed GitHub Actions log and writes the result to the job summary. Advisory only. Not a merge decision. No LLM.

## Use it

After the workflow named `CI` fails:

```yaml
name: CI Doctor
"on":
  workflow_run:
    workflows: ["CI"]
    types: [completed]
permissions:
  actions: read
  contents: read
jobs:
  triage:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - uses: haoranyoung09-sys/ci-diagnose@v1
        with:
          run-id: ${{ github.event.workflow_run.id }}
```

Same job, when the failing command was saved:

```yaml
- uses: haoranyoung09-sys/ci-diagnose@v1
  if: failure()
  with:
    log-path: ci.log
```

`if: failure()` cannot download this run's logs. The job has not finished, so the logs API returns 404. `log-path` stays on disk. `workflow_run` downloads the completed run (`actions: read`).

Outputs: `category`, `confidence`, `confidence-level`, `advisory`, `next-step`, `evidence`.

Pull request comments are off. Set `comment: true` and grant `pull-requests: write` to post or update one comment. The marker is `<!-- ci-doctor -->`.

## Tags

- `v0.7.0` — this release. Do not move it.
- `v1` — moving tag. Point it at this commit so `uses: haoranyoung09-sys/ci-diagnose@v1` installs this Action. Move `v1` again only when a later release stays compatible with these inputs.

## Publish

On the GitHub Release form, tick **Publish this Action to the GitHub Marketplace**. The public mirror has to contain this commit before the tag exists.

## Corpus

Skill metadata 0.7.0. Taxonomy ids are unchanged. `make eval` is 73/73.
