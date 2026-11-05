# ci-fail-classify 0.12.1

The Action display name became `ci-fail-classify`. The skill directory stayed `ci-doctor`. This release did not add a category and did not change the Action inputs or outputs.

0.13.0 defers the GitHub rename. Clone and `uses:` stay `haoranyoung09-sys/ci-diagnose`.

Clone:

```bash
git clone https://github.com/haoranyoung09-sys/ci-diagnose.git
cd ci-diagnose
```

Action (unchanged contract, new repository name):

```yaml
- uses: haoranyoung09-sys/ci-diagnose@v1
  with:
    run-id: ${{ github.event.workflow_run.id }}
```

Install, pinned to this tag:

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-diagnose/v0.12.1/scripts/install.sh | bash
```

From a checkout: `bash scripts/install.sh --user --cli`. The script still refuses to replace an existing install unless you pass `--force`.

## What stayed the same

Seven categories. Offline `make eval` (146/146). Advisory only. English playbooks with a short 中文 note. No CI server: it does not build, sign, or host the app.

Compared with other failure-triage tools, this one is the scored classifier and the fixture oracle. Compared with a CI platform, it only classifies a log you already have.

## Action

`action.yml` name is `ci-fail-classify`. Inputs, outputs, and branding are the same as 0.7.0 through 0.12.0. Log-path and fixture stay offline. A completed run still needs `actions: read`. `comment` still defaults to false.

## Tags

- `v0.12.1` — this release. Do not move it. The curl install pins this tag.
- `v1` — move this tag to this commit on `haoranyoung09-sys/ci-diagnose` when you want `@v1` to install 0.12.1. Do not move it before the public mirror contains the commit. 0.13.0 defers the GitHub rename.
