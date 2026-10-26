# CI Doctor

[中文](README.zh-CN.md)

Pull a failed CI run, classify the root cause, propose a minimal fix, and verify it. This repository is the portable skill and the public redacted fixture corpus. The first host is GitHub Actions.

The diagnose CLI is a deterministic heuristic, not a model. It is the offline path and the smoke oracle for the fixtures. The skill may disagree when confidence is low; it has to say so. A report is advisory. It is not a merge decision.

## Install the skill

The skill source is [`skills/ci-doctor/SKILL.md`](skills/ci-doctor/SKILL.md). This checkout also links it at [`.agents/skills/ci-doctor`](.agents/skills/ci-doctor) so Cursor and Codex discover it from the repo.

| Host | Project path | User path |
| --- | --- | --- |
| Cursor | `.agents/skills/` or `.cursor/skills/` | `~/.agents/skills/` or `~/.cursor/skills/` |
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |

Cursor also reads `.claude/skills/` and `.codex/skills/`. One install path is enough. To use the skill from another repo, link this directory (do not copy it unless you want a frozen snapshot):

```bash
mkdir -p .agents/skills
ln -sfn /absolute/path/to/ci-doctor/skills/ci-doctor .agents/skills/ci-doctor
```

Claude Code:

```bash
mkdir -p .claude/skills
ln -sfn /absolute/path/to/ci-doctor/skills/ci-doctor .claude/skills/ci-doctor
```

Host details: [docs/hosts.md](docs/hosts.md).

## Diagnose a fixture offline

Python 3.9 or newer. No packages and no token.

```bash
python3 scripts/diagnose.py --fixture npm-test-assertion
python3 scripts/diagnose.py fixtures/gha/npm-test-assertion/log.txt
python3 scripts/diagnose.py --fixtures-dir fixtures/gha
python3 scripts/diagnose.py --self-check
```

`--fixtures-dir` classifies every case under `fixtures/gha`, prints a report (category, confidence, evidence lines, next steps), and exits non-zero if a label does not match `meta.json`. That is the smoke oracle. `make test` runs the stdlib edge-case tests (empty logs, the 2MB cap, redaction, bad fixtures, ambiguous signals, `gh` failure modes). `make eval` scores the same corpus and prints accuracy plus a confusion matrix. It does not call `gh`. `make smoke` runs the self-check, the edge tests, the fixture pass, and `make eval`.

`.github/workflows/triage-comment.yml` is an experimental sketch of a read-only failure comment. The job is disabled (`if: false`), the workflow has `contents: read` only, and it stores no token.

A log larger than 2MB is cut on a newline under that cap before scoring, and the report says `truncated`. The rest of the file is not loaded.

A single fixture looks like this:

```text
ci-doctor 0.1.0
id: npm-test-assertion
log: fixtures/gha/npm-test-assertion/log.txt
category: test
confidence: 0.93 (high)
advisory: classification only; not a merge decision
expected_label: test
label_match: yes
signals: expect(received) mismatch; FAIL path line; expected vs received; Jest tests failed summary; test suite failed summary
prefix_stripped: removed gh job/step/timestamp prefixes

evidence:
  L7    FAIL src/api/health.test.ts
  L12   Expected: 200

next_steps:
  1. Open the failing test named in the evidence and compare expected vs received. ...
```

`--format json` prints the same fields, including `scores` and `label_match`. Exit codes: `0` report ok, `1` a fixture label mismatched or the self-check failed, `2` bad arguments, an invalid fixture, or `gh` missing / not logged in.

The CLI accepts a raw step log or `gh run view --log-failed` output. Job, step, and timestamp prefixes are stripped before matching, and common token shapes are redacted before evidence is printed. Redaction is best-effort. Read the evidence before you repeat it.

## Triage a GitHub Actions run with gh

The same CLI fetches a public failed run when `gh` is installed and logged in. It runs `gh run view RUN_ID --repo OWNER/REPO --log-failed`, redacts the text, then scores it. A browser `/job/` number in the URL is not passed to `gh`.

```bash
python3 scripts/diagnose.py --run-url 'https://github.com/OWNER/REPO/actions/runs/RUN_ID'
python3 scripts/diagnose.py --run-id RUN_ID --repo OWNER/REPO
python3 scripts/diagnose.py --run-url 'https://github.com/OWNER/REPO/actions/runs/RUN_ID' --dry-run
```

`--dry-run` prints that `gh` command and does not call the network. `python3 scripts/diagnose.py --self-check` covers URL parsing, the dry-run command, redaction of a fetched log, and the missing-or-logged-out messages without auth.

If `gh` is missing or not logged in, the command exits 2 with a short message and no traceback. Save the log and use the file path above. Do not paste a token into the shell or the chat.

Manual equivalent, if you want the file yourself:

```bash
gh run list --repo OWNER/REPO --status failure --limit 10
gh run view RUN_ID --repo OWNER/REPO --log-failed > /tmp/ci-doctor-run.log
python3 scripts/diagnose.py /tmp/ci-doctor-run.log
```

One job needs the API `databaseId` from `gh run view --json jobs`, not the trailing number in the browser URL. The agent recipe is [`skills/ci-doctor/references/github-actions.md`](skills/ci-doctor/references/github-actions.md).

## Privacy and guardrails

- Fixtures are synthetic and say so in the log. They are not copied from a private run.
- Do not echo tokens, private keys, or secret values. Quote the variable name only.
- Stop after two failed fix attempts. A second miss is a stop, not a wider guess.
- Never force-push, and never rewrite published history unless the operator asked.
- Do not widen `permissions:` to `write-all` or replace `GITHUB_TOKEN` with a personal token to get a green job.
- Confidence is `high`, `medium`, or `low`. Do not say a change is safe to merge.
- Logs over 2 MB are truncated and the report sets `truncated` to true.

## Taxonomy

`flake` · `env` · `test` · `deps` · `permissions` · `infra` · `unknown`

Definitions, signals, and the fixture that demonstrates each one: [docs/taxonomy.md](docs/taxonomy.md). The corpus index is [fixtures/README.md](fixtures/README.md).

## Layout

```text
skills/ci-doctor/     agent skill, playbooks, gh recipe
scripts/diagnose.py   classifier, redaction, and live gh fetch
fixtures/gha/         synthetic GitHub Actions failures
docs/                 taxonomy and host install notes
```

Later hosts, a workflow comment bot, and a Dependabot sibling are tracked in [ROADMAP.md](ROADMAP.md).

## License

[MIT](LICENSE). Contributions follow [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
