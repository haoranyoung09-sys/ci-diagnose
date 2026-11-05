# 宿主安装说明

[English](hosts.md)

Skill 是一个带 `SKILL.md` 和 `references/` 的目录。本仓库里的规范位置是 [`skills/ci-doctor/`](../skills/ci-doctor/)。[`.agents/skills/ci-doctor`](../.agents/skills/ci-doctor) 是相对符号链接，Cursor 和 Codex 把本仓库当作工作区时会加载它。

它分类什么、什么时候不要用、playbook 如何对应 checkout TLS、注册表 egress 和外部数据集：见 [README.zh-CN.md](../README.zh-CN.md#features)。English: [README.md](../README.md#features).

Frontmatter 遵循 Agent Skills 规范：`name` 为 `ci-doctor`（与目录名一致），`description` 说明它做什么、何时使用，并包含 “CI failed”、“GitHub Actions is red” 和 “fix the build”。

## 一条命令

在本仓库的检出里：

```bash
bash scripts/install.sh --user --cli
```

`--user` 是默认。它把 `~/.agents/skills/ci-doctor` 符号链接到检出里的 `skills/ci-doctor`，并打印两边的路径。`--cli` 额外写入 `~/.local/bin/diagnose`，那个包装脚本执行 `python3 scripts/diagnose.py`。`--project` 在当前目录链接 `./.agents/skills/ci-doctor`。已有的链接或目录不会被替换，除非加上 `--force`。Python 低于 3.9 时脚本会停下。

Action 引用保持 `uses: haoranyoung09-sys/ci-diagnose@v1`。安装脚本钉在当前发行标签上。公开镜像发布 `v0.17.0` 之后：

```bash
curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-diagnose/v0.17.0/scripts/install.sh | bash
```

这种形式把标签压缩包下载到 `~/.local/share/ci-fail-classify`。不发送 token。`--claude` 还会链接 `~/.claude/skills/ci-doctor`。装了 Cursor 就不要加它，否则 skill 会被加载两次。

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
