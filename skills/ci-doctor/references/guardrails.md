# Guardrails

These apply to every triage, including fixtures.

1. **Attempt budget.** At most two fix attempts. Reading, classifying, and quoting the log is not an attempt. An attempt starts when you apply a change or ask for a rerun that tests one hypothesis. After the second miss, stop and report what is still unknown.
2. **No force-push.** Never `git push --force`, `--force-with-lease`, or a history rewrite on a branch the user did not explicitly ask to rewrite. Never amend a commit that has been pushed unless the user asks.
3. **Secrets stay out of the transcript.** Do not echo tokens, `Authorization` headers, `.npmrc` credentials, private keys, or environment values. Quote the variable name only. Prefer `scripts/diagnose.py`, which redacts common shapes before printing evidence. Redaction is best-effort; still read the evidence before you repeat it.
4. **Advisory only.** Give a category, a confidence level (`high`, `medium`, `low`), and next steps. Do not say a change is safe to merge. That claim belongs to a later sibling skill, not this one.
5. **Least privilege.** Do not widen `permissions:` to `write-all`, do not mint a personal access token, and do not ask the user to paste a token into the chat.
6. **No private logs in the corpus.** Do not copy a real run into `fixtures/`. Fixtures are synthetic, or already public and redacted. Every synthetic log says it is not a real workflow run.
7. **One hypothesis at a time.** Do not stack a dependency bump, a timeout increase, and a permission change in the same attempt.
8. **`gh` fails closed.** Prefer `scripts/diagnose.py --run-url` or `--run-id`. It runs `gh run view --log-failed`, redacts the log before scoring, and exits with a short message when `gh` is missing or not logged in. If you see that message, switch to a saved log. Do not run `gh auth login`. Do not read `GH_TOKEN` in order to print it. `--dry-run` does not fetch.
9. **Ties stay unknown.** If the report is `unknown` and `alternates` lists two categories, do not pick the one that is easier to patch. Ask for one distinguishing line, or follow the unknown playbook. A phrase under the score threshold (a bare "Refusing to force-push", a filesystem `EACCES` with no GitHub 403) is not a category win.
