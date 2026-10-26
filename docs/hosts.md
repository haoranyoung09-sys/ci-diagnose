# Host install notes

[中文](hosts.zh-CN.md)

The skill is a directory with `SKILL.md` plus `references/`. Canonical source in this repo: [`skills/ci-doctor/`](../skills/ci-doctor/). A relative symlink at [`.agents/skills/ci-doctor`](../.agents/skills/ci-doctor) makes Cursor and Codex load it when this repo is the workspace.

Frontmatter follows the Agent Skills spec: `name` is `ci-doctor` (it matches the directory), and `description` says what the skill does and when to use it, including “CI failed”, “GitHub Actions is red”, and “fix the build”.

## Cursor

Loaded from `.agents/skills/`, `.cursor/skills/`, `~/.agents/skills/`, and `~/.cursor/skills/`. For compatibility, Cursor also loads `.claude/skills/`, `.codex/skills/`, and the matching home directories. Install once.

User-wide, for every repo on this machine:

```bash
mkdir -p ~/.agents/skills
ln -sfn /absolute/path/to/ci-doctor/skills/ci-doctor ~/.agents/skills/ci-doctor
```

`~/.cursor/skills/` is not copied to Cloud Agents by itself. A cloud run sees project skills that are in the repo. The `.agents/skills` link in this checkout covers that.

## Codex

Codex reads `.agents/skills` from the working directory up through the repo root, plus `~/.agents/skills` and `/etc/codex/skills`. Symlinked skill directories are followed. The same `~/.agents/skills` link used for Cursor is the user-level install.

## Claude Code

Claude Code reads `.claude/skills/` in the project and `~/.claude/skills/` for the user. This repo does not also link `.claude/skills/`, because Cursor would then load the skill a second time through its compatibility path.

```bash
mkdir -p ~/.claude/skills
ln -sfn /absolute/path/to/ci-doctor/skills/ci-doctor ~/.claude/skills/ci-doctor
```

## Finding the CLI

The classifier stays at [`scripts/diagnose.py`](../scripts/diagnose.py). From the directory that contains `SKILL.md`, walk parents until `scripts/diagnose.py` exists. That finds the checkout root from `skills/ci-doctor/` and from the `.agents/skills/ci-doctor` symlink. A fixed `../../` is wrong for one of those two paths.

If the skill folder was copied alone into another project, the walk will not find the script. Classify from [`skills/ci-doctor/references/taxonomy.md`](../skills/ci-doctor/references/taxonomy.md) and say the CLI was not on disk, or call the script by absolute path in the ci-doctor checkout.

Copying the skill directory freezes it. Prefer a symlink so playbook edits travel with the repo.
