# ci-fail-classify 0.12.1

Rename. The public project is `ci-fail-classify`. It was `ci-diagnose`. The skill directory is still `ci-doctor`. This release does not add a category and does not change the Action inputs or outputs.

## Redirect

On GitHub, rename `haoranyoung09-sys/ci-diagnose` to `haoranyoung09-sys/ci-fail-classify` if that repository still uses the old name. GitHub will redirect the old URL. Origin keeps its current slug; this agent could not rename it.

Clone:

```bash
git clone https://github.com/haoranyoung09-sys/ci-fail-classify.git
cd ci-fail-classify
```

Action (unchanged contract, new repository name):

```yaml
- uses: haoranyoung09-sys/ci-fail-classify@v1
  with:
    run-id: ${{ github.event.workflow_run.id }}
```

Install, pinned to this tag:

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-fail-classify/v0.12.1/scripts/install.sh | bash
```

From a checkout: `bash scripts/install.sh --user --cli`. The script still refuses to replace an existing install unless you pass `--force`.

## What stayed the same

Seven categories. Offline `make eval` (146/146). Advisory only. English playbooks with a short 中文 note. No CI server: it does not build, sign, or host the app.

Compared with other failure-triage tools, this one is the scored classifier and the fixture oracle. Compared with a CI platform, it only classifies a log you already have.

## Action

`action.yml` name is `ci-fail-classify`. Inputs, outputs, and branding are the same as 0.7.0 through 0.12.0. Log-path and fixture stay offline. A completed run still needs `actions: read`. `comment` still defaults to false.

## Tags

- `v0.12.1` — this release. Do not move it. The curl install pins this tag.
- `v1` — move this tag to this commit on `ci-fail-classify` when you want `@v1` to install 0.12.1. Do not move it before the public mirror contains the commit.
