# Contributing

Thanks for improving CI Doctor. The useful unit of work is a redacted fixture, a sharper taxonomy signal, or a smaller playbook. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) first.

## Development loop

Python 3.9+ is enough. The diagnose CLI uses the standard library only.

```bash
python3 scripts/diagnose.py --self-check
python3 scripts/diagnose.py --fixtures-dir fixtures/gha
make test
make eval
make smoke
```

`make test` runs the stdlib edge-case tests in `tests/`. `make eval` scores every fixture label and prints a confusion matrix. It does not use the network or `gh`. `make smoke` runs the self-check, `make test`, the human-readable fixture pass, and `make eval`. It exits non-zero when a fixture's `meta.json` label disagrees with the classifier. That disagreement is the bug to fix, not something to silence.

## Add a fixture

1. Create `fixtures/gha/<id>/` with `meta.json` and `log.txt`.
2. `<id>` is lowercase kebab-case and matches `meta.json`'s `id`.
3. Set `label` to one of `flake`, `env`, `test`, `deps`, `permissions`, `infra`, `unknown`.
4. Set `source` to `synthetic` (invented) or `redacted-public` (already public, and scrubbed). Set `redacted` to `true` and `host` to `github-actions`.
5. Write `notes` that say why this label is right, and why a neighbor label is wrong.
6. Synthetic logs must contain the phrase `synthetic redacted fixture` and `not a real workflow run`.
7. Do not paste a real private log, a token, a connection string, or a cookie. The loader rejects common secret shapes.
8. Run `make smoke`. If the label you believe is correct does not match, adjust the patterns in `scripts/diagnose.py` and the signal list in [docs/taxonomy.md](docs/taxonomy.md) and [skills/ci-doctor/references/taxonomy.md](skills/ci-doctor/references/taxonomy.md). Do not weaken a rule so far that another fixture flips.

If two categories are honestly tied, label the fixture `unknown` and say so in `notes`.

## Change the taxonomy

Category ids are the public contract. Do not rename or remove one without a note in [ROADMAP.md](ROADMAP.md) and a migration line in the taxonomy doc. Adding a category is a later change; v0 is the seven ids above.

## Change the skill

The agent-facing instructions live in `skills/ci-doctor/`. Keep `SKILL.md` short and put long playbooks under `references/`. The frontmatter `description` is what makes the skill trigger on "CI failed", "Actions is red", and "fix the build". If you edit it, keep those triggers, and keep it under 1024 characters.

Guardrails are not optional copy: no force-push, no printed secrets, stop after two fix attempts, and never call a change safe to merge.

## Pull requests

- Run `make smoke` before you ask for review. That is the check this repo expects: self-check, `make test`, every fixture label, and `make eval`.
- Keep the diff to the fixture, the signal, and the docs that name them.
- If you change an English doc that has a 中文 twin (`README`, `docs/taxonomy`, `docs/hosts`), update both.
- Do not commit real logs, tokens, or connection strings. Synthetic fixtures must say they are synthetic.
- The diagnose CLI stays on the Python standard library. Do not add a dependency to make a fixture pass.

## Privacy

Fixtures in this repo are synthetic. Do not add a log from a private repository, even if you think you redacted it. If you discover a secret already in the tree, do not open a public issue that repeats the value. Contact the maintainers privately.

## Reporting other problems

Bug reports are welcome with the fixture id or a redacted log snippet, the command you ran, and the report you got. Please do not include tokens in the snippet.

## 中文

开发循环只要 Python 3.9+ 的标准库：

```bash
python3 scripts/diagnose.py --self-check
make test
make eval
make smoke
```

`make eval` 不访问网络，也不调用 `gh`。fixture 的 `label` 必须是 `flake`、`env`、`test`、`deps`、`permissions`、`infra`、`unknown` 之一。合成日志必须包含 `synthetic redacted fixture` 和 `not a real workflow run`。不要贴私有日志或 token。

改了英文文档，就要一起改中文孪生文件：`README` / `README.zh-CN`、`docs/taxonomy` / `docs/taxonomy.zh-CN`、`docs/hosts` / `docs/hosts.zh-CN`。功能说明在 README 的 Features / 功能。类别 id 保持英文。

护栏不能改松：不要 force-push，不要打印 secret，两次修复失败就停，不要说可以安全合并。
