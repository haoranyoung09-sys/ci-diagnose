# GitHub Actions logs

The diagnose CLI fetches a failed run when `gh` is installed and logged in. It redacts the log before scoring and printing. A browser job number in the URL is ignored: the command is always `gh run view RUN_ID --repo OWNER/REPO --log-failed`.

## Live path

```bash
python3 scripts/diagnose.py --run-url 'https://github.com/OWNER/REPO/actions/runs/RUN_ID'
python3 scripts/diagnose.py --run-id RUN_ID --repo OWNER/REPO
```

See the `gh` command without calling `gh` or the network:

```bash
python3 scripts/diagnose.py --run-url 'https://github.com/OWNER/REPO/actions/runs/RUN_ID' --dry-run
```

If `gh` is missing or not logged in, the CLI exits with a short message and no traceback. Switch to a saved log:

```bash
python3 scripts/diagnose.py /path/to/saved.log
```

Do not run `gh auth login` from the agent. Do not ask for a token. Do not print `GH_TOKEN`.

## Manual fallback

The same flags, if you need the file yourself:

```bash
gh auth status >/dev/null 2>&1 || {
  printf '%s\n' "gh is not authenticated."
  printf '%s\n' "Save the failed log and run: python3 scripts/diagnose.py <saved-log>"
  exit 0
}

gh run list --repo OWNER/REPO --status failure --limit 10
gh run view RUN_ID --repo OWNER/REPO --log-failed > /tmp/ci-doctor-RUN_ID.log
python3 scripts/diagnose.py /tmp/ci-doctor-RUN_ID.log
```

One job, using the API id rather than the number at the end of a browser URL:

```bash
gh run view RUN_ID --repo OWNER/REPO --json jobs --jq '.jobs[] | {name, conclusion, databaseId}'
gh run view --job DATABASE_ID --repo OWNER/REPO --log-failed > /tmp/ci-doctor-job.log
python3 scripts/diagnose.py /tmp/ci-doctor-job.log
```

Write logs under `/tmp`. Do not commit them. Share the diagnose report, not the raw log. The CLI strips the `job<TAB>step<TAB>timestamp` prefix and truncates input past 2 MB (`truncated: true`).

## After the report

Open `references/playbooks/<category>.md` and follow Recipe, then Verify, then Stop. Re-run failed jobs with `gh run rerun RUN_ID --repo OWNER/REPO --failed` only when the user wants a verification and the hypothesis is already a single change. A rerun with no change does not fix a `test`, `deps`, `env`, or `permissions` failure. One rerun is a reasonable check for `infra` after a runner shutdown, and it is evidence rather than a fix for `flake`.
