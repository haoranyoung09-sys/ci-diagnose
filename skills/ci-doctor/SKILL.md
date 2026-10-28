---
name: ci-doctor
description: >-
  Triage a failed CI run for GitHub Actions: classify the root cause
  (flake, env, test, deps, permissions, infra, or unknown), quote redacted
  evidence, propose a minimal fix, and say how to verify it. Use when CI
  failed, GitHub Actions is red, a workflow run failed, checks are failing,
  the build is broken, checkout fails certificate verification, a registry
  or MCR pull is blocked, an external dataset host flakes, or the user asks
  to fix the build, diagnose a failing check, explain a red Actions job, or
  triage a fixture log. Also use it when a later hook fails because
  checkout failed, a registry pull is authentication-denied rather than
  blocked, or only one job in a multi-job log failed. Also use it for a
  service or Helm health-check timeout, a chronic external dataset host,
  Bundler, Cargo.lock, or go.sum drift, DNS name resolution, or an
  actions/cache restore failure. Do not use it to approve a merge, to
  review Dependabot, or on a CI host other than GitHub Actions.
license: MIT
compatibility: >-
  Offline diagnosis needs Python 3.9+ with the standard library only. A
  GitHub Actions run URL is fetched with gh run view --log-failed when gh
  is installed and logged in. Without gh, pass a saved log. --dry-run
  prints the gh command and does not call the network. The GitHub
  Action is composite, runs python3 on the runner, and does not call an LLM.
metadata:
  author: ci-doctor
  version: "0.8.0"
  taxonomy: v0
---

# CI Doctor

Advisory triage for a failed GitHub Actions run. Classify, quote evidence, propose one minimal fix, and say how to verify it. Do not merge. Do not force-push.

If the user writes in Chinese, write the final report in Chinese. Keep category ids in English.

## When to use this skill

- CI failed, GitHub Actions is red, or the user pasted a log, a run URL, or a fixture id.
- Checkout certificate verification failed, or a later hook failed only because checkout did not finish (`checkout-tls-verify-flake`, `checkout-tls-hook-cascade-flake`).
- A registry or MCR pull was blocked (`infra`) or the registry denied authentication (`permissions`). If both lines are present, stay on `unknown`.
- An external dataset host timed out. If the log says the same URL failed on every attempt, prefer a mirror or a vendored file over another rerun.
- A service container or Helm health check timed out, and there is no assertion. If both are present, stay on `unknown`.
- Bundler `Gemfile.lock`, `go.sum`, or `Cargo.lock` failed before the tests. `getaddrinfo` / name resolution with no auth line. `actions/cache` failed to restore, even if a lockfile line follows. Cache `EACCES` plus a lockfile line stays `unknown`.
- A multi-job log where only one job failed. Run the CLI. Do not classify a phrase that appears only on a green job.
- Node or Python on the runner does not match the workflow, a self-hosted runner is offline, a pull is rate-limited, the image arch does not match the host, or Git LFS hit a rate limit. A `continue-on-error` step is not the failure if a later lockfile line is.
- The user wants the result in a GitHub Actions job summary. The composite action is `action.yml` at the repo root. It does not call an LLM. Leave `comment` off unless they set it. Same-job `if: failure()` needs `log-path`; a finished run uses `workflow_run` and `run-id`.

## When not to use this skill

- The user wants a merge decision or "safe to merge". Refuse.
- Dependabot, Renovate, GitLab CI, or CircleCI. Say this skill does not cover that, and do not invent a category.
- The log is empty, or `truncated: true` and the failed step is past the 2MB cut. Ask for the failed step. Do not guess from the kept prefix.
- The category is `unknown` or `alternates` is non-empty. Do not pick the easier side. A hook line with no checkout error (`checkout-hook-only-unknown`) is not a TLS flake.

Human feature intro, in English and 中文: repository `README.md` and `README.zh-CN.md`, section Features. Taxonomy and playbooks in this directory stay in English; category ids stay English in a Chinese report.

## Guardrails

Follow [references/guardrails.md](references/guardrails.md) on every run.

- At most two fix attempts. Reading the log is not an attempt. An attempt is a change you apply or a rerun that tests one hypothesis.
- Never force-push, never `git push --force`, never `--force-with-lease`, and never amend a pushed commit unless the user explicitly asks.
- Never print secrets. Quote variable names only. Prefer the diagnose CLI; it redacts common token shapes before printing evidence. Redaction is best-effort — read the evidence before you repeat it.
- Confidence is `high`, `medium`, or `low`. Do not say a change is safe to merge.
- Do not widen `permissions:` to `write-all`, do not mint a PAT, and do not ask the user to paste a token.
- Do not copy a real run into `fixtures/`.

## Resolve the CLI

Use the first one that exists:

1. `scripts/diagnose.py` at the workspace root, when this repo is the workspace.
2. Walk parents of this `SKILL.md` until you find `scripts/diagnose.py`. That walk hits the checkout root both from `skills/ci-doctor/` and from the `.agents/skills/ci-doctor` symlink.
3. If neither exists, classify by hand from [references/taxonomy.md](references/taxonomy.md) and say the CLI was not on disk.

Commands, from a checkout:

```bash
python3 scripts/diagnose.py --fixture <id>
python3 scripts/diagnose.py --fixtures-dir fixtures/gha
python3 scripts/diagnose.py <path-to-log>
python3 scripts/diagnose.py --run-url 'https://github.com/OWNER/REPO/actions/runs/RUN_ID'
python3 scripts/diagnose.py --run-id RUN_ID --repo OWNER/REPO
python3 scripts/diagnose.py --run-url 'https://github.com/OWNER/REPO/actions/runs/RUN_ID' --dry-run
python3 scripts/diagnose.py --self-check
```

The CLI does not read `meta.json` labels while scoring. On a fixture, `label_match` compares the score with the corpus label after the fact.

## Workflow

1. **Get the log.**
   - Fixture id or `log.txt` in this repo: pass `--fixture` or the path.
   - A file the user points at: pass that path.
   - An Actions URL or run id: run `scripts/diagnose.py --run-url` or `--run-id` with `--repo`, as in [references/github-actions.md](references/github-actions.md). The CLI redacts the log before it scores. If it reports that `gh` is missing or not logged in, stop and ask for a saved log. Do not run `gh auth login`. Do not print `GH_TOKEN`. `--dry-run` shows the `gh` command with no network.
2. **Classify.** Run the CLI. Read [references/taxonomy.md](references/taxonomy.md). Trust a `high` result that names one category. If the category is `unknown`, confidence is below `high`, or `alternates` is non-empty, inspect the evidence and either confirm `unknown` or name one taxonomy category plus the extra lines you used. Do not invent a category.
3. **Playbook.** Open `references/playbooks/<category>.md` and follow its **Recipe**. One hypothesis. Quote at most six redacted lines with their line numbers from the report. If `alternates` is non-empty, name that near miss from the playbook before you edit. A tie (`unknown` plus two alternates) is not permission to pick the easier category.
4. **Verify.** Follow that playbook's **Verify** section. Say what would count as the same failure and what would count as a new one. Re-running the diagnose CLI on a fixture only checks the report. Apply a code change only when the user asked to fix it. Record `attempt: 1 of 2` or `2 of 2` once a change or a hypothesis-testing rerun has happened.
5. **Stop.** Follow the playbook's **Stop** section. After two failed verifications, stop. Summarize both attempts, the confidence, and what a human should look at. Do not loop. Do not stack a second hypothesis into the same attempt.

## Report shape

Use this shape even when you classified by hand:

```text
category: <id>
confidence: <0.00-1.00> (<high|medium|low>)
advisory: classification only; not a merge decision
evidence:
  L<n>  <redacted line>
next_steps:
  1. ...
attempt: <0-2> of 2
```

`attempt: 0 of 2` when you have only diagnosed and not yet tested a fix.

## Repo map

- `scripts/diagnose.py` — classifier, redaction, and live `gh run view --log-failed`
- `fixtures/gha/` — synthetic corpus
- `docs/taxonomy.md` — human-facing taxonomy, when the full repo is present
- `references/` — what you need if only this skill directory was installed
