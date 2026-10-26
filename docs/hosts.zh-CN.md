# 宿主安装说明

[English](hosts.md)

Skill 是一个带 `SKILL.md` 和 `references/` 的目录。本仓库里的规范位置是 [`skills/ci-doctor/`](../skills/ci-doctor/)。[`.agents/skills/ci-doctor`](../.agents/skills/ci-doctor) 是相对符号链接，Cursor 和 Codex 把本仓库当作工作区时会加载它。

Frontmatter 遵循 Agent Skills 规范：`name` 为 `ci-doctor`（与目录名一致），`description` 说明它做什么、何时使用，并包含 “CI failed”、“GitHub Actions is red” 和 “fix the build”。

## Cursor

从 `.agents/skills/`、`.cursor/skills/`、`~/.agents/skills/` 和 `~/.cursor/skills/` 加载。为了兼容，Cursor 也会读 `.claude/skills/`、`.codex/skills/` 以及对应的用户目录。装一次即可。

本机所有仓库可用的用户级安装：

```bash
mkdir -p ~/.agents/skills
ln -sfn /absolute/path/to/ci-doctor/skills/ci-doctor ~/.agents/skills/ci-doctor
```

仅放在 `~/.cursor/skills/` 的 skill 不会自动进 Cloud Agent。云端运行看到的是仓库里的项目 skill。本仓库的 `.agents/skills` 链接覆盖这一点。

## Codex

Codex 从当前工作目录向上直到仓库根读取 `.agents/skills`，另外还有 `~/.agents/skills` 和 `/etc/codex/skills`。符号链接的 skill 目录会被跟随。给 Cursor 用的同一条 `~/.agents/skills` 链接就是 Codex 的用户级安装。

## Claude Code

Claude Code 读项目里的 `.claude/skills/` 和用户级的 `~/.claude/skills/`。本仓库不再链接 `.claude/skills/`，否则 Cursor 会从兼容路径把同一个 skill 再加载一次。

```bash
mkdir -p ~/.claude/skills
ln -sfn /absolute/path/to/ci-doctor/skills/ci-doctor ~/.claude/skills/ci-doctor
```

## 找到命令行

分类器在 [`scripts/diagnose.py`](../scripts/diagnose.py)。从包含 `SKILL.md` 的目录向上找，直到出现 `scripts/diagnose.py`。从 `skills/ci-doctor/` 和从 `.agents/skills/ci-doctor` 符号链接出发都能找到仓库根。固定的 `../../` 对其中一条路径是错的。

如果 skill 目录被单独复制到别的项目，向上找不会遇到脚本。那时按 [`skills/ci-doctor/references/taxonomy.md`](../skills/ci-doctor/references/taxonomy.md) 手工分类，并说明命令行不在磁盘上，或者用 ci-doctor 检出里的绝对路径调用脚本。

复制 skill 目录会把它冻住。优先用符号链接，这样 playbook 的修改会跟着仓库走。
