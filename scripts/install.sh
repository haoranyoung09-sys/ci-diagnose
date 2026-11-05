#!/usr/bin/env bash
# Install CI Doctor (MIT). Review this file before you pipe it to a shell.
# It does not read tokens. It refuses to replace an existing install
# unless you pass --force.
#
# From a checkout:
#   bash scripts/install.sh --user --cli
#   bash scripts/install.sh --project
# After tag v0.16.0 is on GitHub:
#   curl -fsSL https://raw.githubusercontent.com/haoranyoung09-sys/ci-diagnose/v0.16.0/scripts/install.sh | bash
# Pin another ref with CI_DIAGNOSE_REF (default v0.16.0). The Action stays uses: ...@v1.

set -euo pipefail

REF="${CI_DIAGNOSE_REF:-v0.16.0}"
REPO_URL="https://github.com/haoranyoung09-sys/ci-diagnose"
MODE="user"
WITH_CLI=0
FORCE=0
WITH_CLAUDE=0

usage() {
  cat <<'EOF'
Usage: install.sh [--user | --project] [--cli] [--claude] [--force]

  --user      Install the skill for this account (default).
              Cursor and Codex: ~/.agents/skills/ci-doctor
  --project   Install into ./.agents/skills/ci-doctor from the current directory.
  --cli       Also install ~/.local/bin/diagnose (a wrapper around diagnose.py).
  --claude    Also link ~/.claude/skills/ci-doctor. Skip this if you use Cursor,
              which already reads ~/.agents/skills and would load the skill twice.
  --force     Replace an existing link, directory, or diagnose wrapper.

From a git checkout the script links that checkout. Piped from curl, it
downloads the public tag archive into ~/.local/share/ci-fail-classify.
Set CI_DIAGNOSE_REF to choose the tag (default v0.16.0).
Public checkout: https://github.com/haoranyoung09-sys/ci-diagnose
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --user) MODE="user" ;;
    --project) MODE="project" ;;
    --cli) WITH_CLI=1 ;;
    --claude) WITH_CLAUDE=1 ;;
    --force) FORCE=1 ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "ci-fail-classify: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

need_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "ci-fail-classify: python3 is not on PATH. Install Python 3.9 or newer and retry." >&2
    exit 1
  fi
  if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)'; then
    echo "ci-fail-classify: python3 is older than 3.9, or it refused to run. Need Python 3.9 or newer." >&2
    exit 1
  fi
}

script_root() {
  local source_path="${BASH_SOURCE[0]:-}"
  if [[ -z "$source_path" || ! -f "$source_path" ]]; then
    return 1
  fi
  local root
  root="$(cd "$(dirname "$source_path")/.." && pwd)"
  if [[ -f "$root/skills/ci-doctor/SKILL.md" && -f "$root/scripts/diagnose.py" ]]; then
    printf '%s\n' "$root"
    return 0
  fi
  return 1
}

fetch_release() {
  local dest="$1"
  local parent tmp archive url
  parent="$(dirname "$dest")"
  mkdir -p "$parent"
  if [[ -e "$dest" && "$FORCE" != 1 ]]; then
    echo "ci-fail-classify: $dest already exists. Re-run with --force to replace that checkout." >&2
    exit 1
  fi
  tmp="$(mktemp -d)"
  archive="$tmp/ci-fail-classify.tar.gz"
  url="${REPO_URL}/archive/refs/tags/${REF}.tar.gz"
  echo "ci-fail-classify: downloading ${url}"
  if ! curl -fsSL "$url" -o "$archive"; then
    echo "ci-fail-classify: could not download tag ${REF}." >&2
    echo "ci-fail-classify: from a git checkout run: bash scripts/install.sh --user" >&2
    rm -rf "$tmp"
    exit 1
  fi
  tar -xzf "$archive" -C "$tmp"
  local extracted
  extracted="$(find "$tmp" -mindepth 1 -maxdepth 1 -type d \( -name 'ci-fail-classify-*' -o -name 'ci-diagnose-*' \) | head -n 1)"
  if [[ -z "$extracted" || ! -f "$extracted/scripts/diagnose.py" ]]; then
    echo "ci-fail-classify: the archive did not contain scripts/diagnose.py" >&2
    rm -rf "$tmp"
    exit 1
  fi
  if [[ -e "$dest" ]]; then
    rm -rf "$dest"
  fi
  mv "$extracted" "$dest"
  rm -rf "$tmp"
  echo "ci-fail-classify: checkout $dest"
}

place_link() {
  local dest="$1"
  local src="$2"
  mkdir -p "$(dirname "$dest")"
  if [[ -L "$dest" ]]; then
    local current
    current="$(readlink "$dest")"
    if [[ "$current" == "$src" ]]; then
      echo "ci-fail-classify: skill already at $dest"
      echo "ci-fail-classify: source $src"
      return 0
    fi
    if [[ "$FORCE" != 1 ]]; then
      echo "ci-fail-classify: $dest already points at $current" >&2
      echo "ci-fail-classify: re-run with --force to replace that link." >&2
      exit 1
    fi
  elif [[ -e "$dest" ]]; then
    if [[ "$FORCE" != 1 ]]; then
      echo "ci-fail-classify: $dest exists and is not a symlink." >&2
      echo "ci-fail-classify: re-run with --force to replace it." >&2
      exit 1
    fi
    rm -rf "$dest"
  fi
  ln -sfn "$src" "$dest"
  echo "ci-fail-classify: skill $dest"
  echo "ci-fail-classify: source $src"
}

install_cli() {
  local root="$1"
  local bindir="${HOME}/.local/bin"
  local wrapper="${bindir}/diagnose"
  mkdir -p "$bindir"
  local quoted body
  quoted="$(printf '%q' "$root")"
  body="$(printf '#!/bin/sh\nexec python3 %s/scripts/diagnose.py "$@"\n' "$quoted")"
  if [[ -f "$wrapper" && "$FORCE" != 1 ]]; then
    if [[ "$(cat "$wrapper"; printf x)" == "${body}x" ]]; then
      echo "ci-fail-classify: cli already at $wrapper"
      return 0
    fi
    echo "ci-fail-classify: $wrapper already exists. Re-run with --force to replace it." >&2
    exit 1
  fi
  printf '%s' "$body" >"$wrapper"
  chmod 755 "$wrapper"
  echo "ci-fail-classify: cli $wrapper"
  case ":${PATH}:" in
    *":${bindir}:"*) ;;
    *)
      echo "ci-fail-classify: ${bindir} is not on PATH. Add it, or call ${wrapper} by path."
      ;;
  esac
}

need_python

ROOT=""
if ROOT="$(script_root)"; then
  echo "ci-fail-classify: using checkout $ROOT"
else
  ROOT="${HOME}/.local/share/ci-fail-classify"
  fetch_release "$ROOT"
fi

SKILL_SRC="${ROOT}/skills/ci-doctor"
if [[ ! -f "${SKILL_SRC}/SKILL.md" ]]; then
  echo "ci-fail-classify: missing ${SKILL_SRC}/SKILL.md" >&2
  exit 1
fi

if [[ "$MODE" == "project" ]]; then
  place_link "${PWD}/.agents/skills/ci-doctor" "$SKILL_SRC"
else
  place_link "${HOME}/.agents/skills/ci-doctor" "$SKILL_SRC"
fi

if [[ "$WITH_CLAUDE" == 1 ]]; then
  echo "ci-fail-classify: Claude Code only. Cursor also reads this path and would load the skill twice."
  place_link "${HOME}/.claude/skills/ci-doctor" "$SKILL_SRC"
fi

if [[ "$WITH_CLI" == 1 ]]; then
  install_cli "$ROOT"
fi

echo "ci-fail-classify: python $(python3 -V 2>&1 | awk '{print $2}')"
echo "ci-fail-classify: done"
