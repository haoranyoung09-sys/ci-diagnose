#!/usr/bin/env python3
"""CI failure triage for the ci-doctor corpus and for live GitHub Actions runs.

Heuristic classifier for the v0 taxonomy (flake, env, test, deps,
permissions, infra, unknown). Stdlib only. Evidence is redacted before
it is scored and printed. Category ids are smoke-tested against fixtures/gha;
keep them aligned with docs/taxonomy.md and skills/ci-doctor/references/.

A live run uses `gh run view --log-failed`. If `gh` is missing or not
logged in, the command exits with a short message and no traceback.

Exit codes:
  0  report produced; every fixture label matched when a corpus was checked
  1  self-check failed, or a fixture label did not match
  2  usage error, missing path, invalid fixture metadata, or gh unavailable
"""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path

VERSION = "0.1.0"
CATEGORIES = (
    "flake",
    "env",
    "test",
    "deps",
    "permissions",
    "infra",
    "unknown",
)
MIN_SCORE = 6
MAX_EVIDENCE = 6
# Heaviest lines kept per category while scoring. The printed report still
# shows at most MAX_EVIDENCE. 32 is enough to preserve the top 6 for every
# fixture without storing a hit for every matching line of a huge log.
EVIDENCE_POOL = 32
MAX_BYTES = 2_000_000
_STDERR_CAP = 256_000
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIXTURES = REPO_ROOT / "fixtures" / "gha"
SYNTHETIC_MARKERS = (
    "synthetic redacted fixture",
    "not a real workflow run",
)
HOST_BY_DIR = {"gha": "github-actions"}
ALLOWED_SOURCES = {"synthetic", "redacted-public"}

_ANSI = re.compile(r"\x1b\[[0-9;]*m")
# gh run view --log-failed lines look like:
#   <job>\t<step>\t2026-10-26T01:14:22.1038427Z message
# Require the timestamp so a tab-separated test line (Go's FAIL\tpackage\t0.02s)
# is not treated as a job/step prefix.
_GH_PREFIX = re.compile(
    r"^(?:[^\t\n]+\t[^\t\n]+\t)?"
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\s+"
)
# job \t step \t 2026-10-26T01:14:22.1038427Z message
_GH_JOB = re.compile(
    r"^([^\t\n]+)\t[^\t\n]+\t\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
)
_FAILED_STEP = re.compile(
    r"##\[error\]|process completed with exit code (?!0\b)\d+|\bexit code (?:[1-9]\d*)\b",
    re.IGNORECASE,
)

_SECRET_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*", re.IGNORECASE),
        "[REDACTED_PRIVATE_KEY]",
    ),
    (
        re.compile(r"-----END [A-Z0-9 ]*PRIVATE KEY-----.*", re.IGNORECASE),
        "[REDACTED_PRIVATE_KEY]",
    ),
    (
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{8,}\b"),
        "[REDACTED_GITHUB_TOKEN]",
    ),
    (
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{8,}\b"),
        "[REDACTED_GITHUB_TOKEN]",
    ),
    (re.compile(r"\bglpat-[A-Za-z0-9_\-]{8,}\b"), "[REDACTED_GITLAB_TOKEN]"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "[REDACTED_SLACK_TOKEN]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_ACCESS_KEY]"),
    (
        re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_\-]{10,}\b"),
        "[REDACTED_API_KEY]",
    ),
    (
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
        ),
        "[REDACTED_JWT]",
    ),
    (
        re.compile(r"(?i)(https?://[^/\s:]+:)[^@\s/]+@"),
        r"\1[REDACTED]@",
    ),
    (
        re.compile(r"(?i)(authorization\s*:\s*bearer\s+)\S+"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(?i)(authorization\s*:\s*basic\s+)\S+"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"\bASIA[0-9A-Z]{16}\b"),
        "[REDACTED_AWS_ACCESS_KEY]",
    ),
    (
        re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{16,}\b"),
        "[REDACTED_API_KEY]",
    ),
    (
        re.compile(r"\bAIza[0-9A-Za-z\-_]{20,}\b"),
        "[REDACTED_API_KEY]",
    ),
    (
        re.compile(r"\bnpm_[A-Za-z0-9]{36}\b"),
        "[REDACTED_NPM_TOKEN]",
    ),
    (
        re.compile(r"\bpypi-[A-Za-z0-9_\-]{16,}\b"),
        "[REDACTED_PYPI_TOKEN]",
    ),
    (
        re.compile(r"\bdckr_pat_[A-Za-z0-9_\-]{16,}\b"),
        "[REDACTED_DOCKER_TOKEN]",
    ),
    (
        re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
        "[REDACTED_HF_TOKEN]",
    ),
    (
        re.compile(
            r"https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+"
        ),
        "[REDACTED_SLACK_WEBHOOK]",
    ),
    (
        re.compile(
            r"(?i)(?<![A-Za-z0-9])(bearer\s+)(?!\[REDACTED\])"
            r"[A-Za-z0-9\-._~+/]{20,}"
        ),
        r"\1[REDACTED]",
    ),
    (
        re.compile(
            r"(?i)\b((?:aws_secret_access_key|aws_session_token|npm_token|"
            r"auth_token|_?authtoken|api[_-]?key|refresh_token|client_secret|"
            r"secret_key|token|password|passwd|secret)"
            r"\s*[=:]\s*)(?!\[REDACTED\])(?!(?:read|write|none)\b)\S+"
        ),
        r"\1[REDACTED]",
    ),
)

_FORBIDDEN_IN_CORPUS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{8,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{8,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bASIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(
        r"(?i)\b(?:password|aws_secret_access_key|aws_session_token|"
        r"api[_-]?key|client_secret|refresh_token|secret_key)\s*=\s*\S+"
    ),
    re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bnpm_[A-Za-z0-9]{36}\b"),
    re.compile(r"\bdckr_pat_[A-Za-z0-9_\-]{16,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
)


@dataclass(frozen=True)
class Rule:
    category: str
    weight: int
    pattern: str
    signal: str
    flags: int = re.IGNORECASE

    def compile(self) -> re.Pattern[str]:
        return re.compile(self.pattern, self.flags)


RULES: tuple[Rule, ...] = (
    Rule(
        "permissions",
        9,
        r"resource not accessible by integration",
        "integration token cannot access the resource",
    ),
    Rule(
        "permissions",
        8,
        r"remote:\s*permission to .+ denied",
        "remote rejected the push for this token",
    ),
    Rule(
        "permissions",
        7,
        r"requested url returned error:\s*403",
        "remote returned HTTP 403",
    ),
    Rule(
        "permissions",
        7,
        r"does not have permission",
        "actor does not have permission",
    ),
    Rule(
        "permissions",
        7,
        r"not granted .*(?:permission|contents:|pull-requests:|issues:|id-token:)",
        "workflow permissions block the job",
    ),
    Rule("permissions", 6, r"\bhttp(?:error)?\b.*\b403\b", "HTTP 403"),
    Rule("permissions", 6, r"insufficient permissions", "insufficient permissions"),
    Rule(
        "permissions",
        8,
        r"unauthorized: authentication required|pull access denied|requested access to the resource is denied",
        "registry authentication was denied",
    ),
    Rule(
        "permissions",
        5,
        r"refusing to (?:force-push|allow)",
        "token refused a force-push or broader grant",
    ),
    Rule(
        "env",
        9,
        r"required environment variable .+ is not set",
        "required environment variable is unset",
    ),
    Rule(
        "env",
        8,
        r"environment variable .+ (?:is )?(?:not set|unset|missing|undefined)",
        "environment variable missing",
    ),
    Rule(
        "env",
        8,
        r"input required and not supplied",
        "action input was not supplied",
    ),
    Rule(
        "env",
        7,
        r"\b[A-Z][A-Z0-9_]{2,} is empty\b",
        "named variable is empty",
        flags=0,
    ),
    Rule(
        "env",
        6,
        r"secret .+ (?:not found|was not provided|is not set)",
        "secret was not provided",
    ),
    Rule("deps", 9, r"\bERESOLVE\b", "ERESOLVE"),
    Rule(
        "deps",
        8,
        r"unable to resolve dependency tree",
        "dependency tree could not be resolved",
    ),
    Rule("deps", 8, r"conflicting peer dependency", "conflicting peer dependency"),
    Rule(
        "deps",
        8,
        r"could not resolve dependency",
        "dependency could not be resolved",
    ),
    Rule(
        "deps",
        9,
        r"package\.json and package-lock\.json",
        "package.json and lockfile disagree",
    ),
    Rule(
        "deps",
        8,
        r"missing: .+ from lock file",
        "package missing from the lockfile",
    ),
    Rule("deps", 5, r"peer dep", "peer dependency conflict"),
    Rule(
        "deps",
        9,
        r"err_pnpm_outdated_lockfile|pnpm-lock\.yaml.+(?:out of date|outdated)",
        "pnpm lockfile is out of date",
    ),
    Rule(
        "deps",
        8,
        r"could not find a version that satisfies",
        "pip could not satisfy a version",
    ),
    Rule(
        "deps",
        8,
        r"yarn\.lock.+(?:out of date|needs to be updated)",
        "yarn lockfile is out of date",
    ),
    Rule(
        "deps",
        8,
        r"poetry\.lock.+(?:out of date|not consistent)|since poetry\.lock was last generated",
        "poetry lockfile is out of date",
    ),
    Rule(
        "deps",
        8,
        r"uv\.lock needs to be updated",
        "uv lockfile needs an update",
    ),
    Rule(
        "deps",
        8,
        r"could not resolve all (?:files|artifacts|dependencies) for configuration",
        "Gradle could not resolve a configuration",
    ),
    Rule(
        "deps",
        8,
        r"updated gemfile\.lock to version control|bundler could not find compatible versions|gemfile\.lock.+(?:out of date|does not match)",
        "Bundler lockfile is out of date",
    ),
    Rule(
        "deps",
        8,
        r"missing go\.sum entry|verifying module: checksum mismatch",
        "go.sum entry is missing or mismatched",
    ),
    Rule(
        "deps",
        8,
        r"cargo\.lock needs to be updated|failed to select a version for the requirement",
        "Cargo lockfile could not select a version",
    ),
    Rule("flake", 9, r"suspected flake", "suspected flake"),
    Rule("flake", 8, r"exceeded timeout of \d+", "test exceeded its timeout"),
    Rule(
        "flake",
        8,
        r"timeout of \d+\s*m?s exceeded",
        "runner timed out waiting for the test",
    ),
    Rule(
        "flake",
        7,
        r"passed on (?:the |a )?(?:previous run|automatic rerun|rerun|retry)",
        "passed on a rerun",
    ),
    Rule("flake", 6, r"\bintermittent\b", "intermittent failure"),
    Rule("flake", 5, r"retry \d+ of \d+", "failed on a numbered retry"),
    Rule("flake", 6, r"\bflak(?:e|y|iness)\b", "flake or flaky wording"),
    Rule(
        "flake",
        8,
        r"ssl certificate problem|server certificate verification failed|unable to get local issuer certificate|tls connection was non-properly terminated",
        "checkout TLS certificate verification failed",
    ),
    Rule(
        "flake",
        8,
        r"failed to (?:download|fetch) (?:the )?(?:external )?dataset|external host (?:timed out|timeout|connection reset)",
        "external dataset or host dependency failed",
    ),
    Rule(
        "flake",
        8,
        r"health ?check (?:failed|timed out)|service container \S+ failed to start|timed out waiting for \S+ to become healthy|timeout waiting for [^:\n]{0,80}inprogress",
        "service health check timed out",
    ),
    Rule(
        "flake",
        5,
        r"cannot run \S*hooks?\b|hook failed because checkout",
        "downstream hook did not run after checkout",
    ),
    Rule("test", 8, r"\bAssertionError\b", "AssertionError"),
    Rule("test", 7, r"expect\(received\)", "expect(received) mismatch"),
    Rule("test", 6, r"^\s*FAIL\s+\S", "FAIL path line"),
    Rule("test", 5, r"^\s*Expected:\s*\S", "expected vs received"),
    Rule("test", 5, r"^\s*Tests:\s+.*\bfailed\b", "Jest tests failed summary"),
    Rule("test", 7, r"^\s*FAILED\s+(?!asserting\b)\S", "pytest FAILED line"),
    Rule("test", 7, r"^\s*--- FAIL:", "Go test FAIL"),
    Rule("test", 5, r"\btest suites?:.*\bfailed\b", "test suite failed summary"),
    Rule("test", 7, r"failed asserting that", "PHPUnit assertion failed"),
    Rule("test", 7, r"^\s*Failure/Error:", "RSpec failure"),
    Rule("test", 7, r"test result:\s*FAILED", "cargo test result FAILED"),
    Rule(
        "infra",
        9,
        r"javascript heap out of memory",
        "JavaScript heap out of memory",
    ),
    Rule("infra", 8, r"reached heap limit", "V8 reached the heap limit"),
    Rule("infra", 9, r"\bOOMKilled\b", "OOMKilled"),
    Rule("infra", 9, r"no space left on device", "no space left on device"),
    Rule("infra", 8, r"disk quota exceeded", "runner disk quota exceeded"),
    Rule("infra", 7, r"out of memory", "out of memory"),
    Rule(
        "infra",
        6,
        r"runner (?:process|has received).*(?:killed|shutdown)",
        "runner process killed or shut down",
    ),
    Rule(
        "infra",
        7,
        r"cannot connect to the docker daemon",
        "Docker daemon is not reachable",
    ),
    Rule(
        "infra",
        8,
        r"dial tcp: lookup|no such host|network is unreachable|tls handshake timeout|egress blocked|\bi/o timeout\b",
        "registry pull or egress blocked",
    ),
    Rule(
        "infra",
        8,
        r"temporary failure in name resolution|getaddrinfo|name or service not known|could not resolve host",
        "DNS name resolution failed",
    ),
    Rule(
        "infra",
        12,
        r"failed to restore cache(?: entry)?|cache restore failed",
        "actions cache restore failed",
    ),
    Rule(
        "infra",
        5,
        r"\bEACCES: permission denied\b",
        "cache path EACCES",
    ),
    Rule(
        "unknown",
        1,
        r"process completed with exit code",
        "process exited without a taxonomy signal",
    ),
)

COMPILED: tuple[tuple[Rule, re.Pattern[str]], ...] = tuple(
    (rule, rule.compile()) for rule in RULES
)

NEXT_STEPS: dict[str, tuple[str, ...]] = {
    "test": (
        "Open the failing test named in the evidence and compare expected vs received. Change the product code or the assertion, whichever the failure shows is wrong.",
        "Reproduce with the same command the job ran, then re-run that job. Do not delete or skip the test to force a green build.",
        "A second failure with a different assertion is a new hypothesis. Stop after two unsuccessful fix attempts.",
    ),
    "env": (
        "Treat the variable name in the evidence as the defect. Supply it through the job env or the right GitHub Actions environment. Do not invent a value and do not print the value.",
        "Check whether the secret is defined on the workflow environment named in the job. Repo-level secrets are not visible to every environment.",
        "Re-run the single failed job after the name is present. Stop if the next error names a different variable.",
    ),
    "deps": (
        "Align the versions quoted in the evidence, or regenerate the lockfile and commit it. Do not start with --force or --legacy-peer-deps.",
        "If npm ci reports that package.json and the lockfile are out of sync, update the lockfile. Do not replace npm ci with npm install in CI as the fix.",
        "Re-run the install job once. If the resolver reports a new conflict, stop and show both constraints.",
    ),
    "permissions": (
        "Name the missing permissions: scope from the evidence and suggest the narrowest grant that covers that API. Do not switch the job to a personal access token.",
        "Do not force-push, and do not widen permissions on a retry loop.",
        "Re-run the job after the workflow change. A 403 from a different API is a new finding, not a cue to grant write-all.",
    ),
    "flake": (
        "Quote the timeout, rerun, checkout TLS, or external-dataset line before changing product logic. A pass on rerun is a flake signal, not a fix.",
        "Prefer a deterministic wait or isolating shared state over raising the timeout as the only edit.",
        "After a code change, rerun the test more than once if the user agrees. If it fails the same way every time, reclassify toward test or infra. Stop after two attempts.",
    ),
    "infra": (
        "Quote the host signal (heap, disk, runner killed, registry egress). Do not edit the assertion or the image tag to absorb an out-of-memory, disk-full, or blocked-pull failure.",
        "Suggest one resource change: a smaller build, fewer artifacts, a heap cap, or a larger runner class.",
        "One rerun is reasonable after a runner shutdown. A second identical host failure means report infra and stop.",
    ),
    "unknown": (
        "No v0 taxonomy signal was strong enough. Say that plainly and quote the last error line.",
        "Ask for the failed step name and the log lines above the exit code. Do not guess a category to sound decisive.",
        "Do not propose a drive-by refactor. Stop until there is a classifiable log.",
    ),
}


class CorpusError(Exception):
    """A fixture on disk is missing, unsafe, or internally inconsistent."""


class GhError(Exception):
    """A live GitHub fetch cannot continue. The message is safe to print."""


@dataclass
class Hit:
    line_no: int
    text: str
    category: str
    weight: int
    signal: str


@dataclass
class Classification:
    category: str
    confidence: float
    confidence_level: str
    evidence: list[dict[str, object]]
    next_steps: list[str]
    scores: dict[str, int]
    signals: list[str]
    alternates: list[str]
    truncated: bool
    prefix_stripped: bool


def redact(text: str) -> str:
    """Best-effort line-oriented redaction. Not a complete secret scanner."""
    for pattern, repl in _SECRET_RULES:
        text = pattern.sub(repl, text)
    return text


def normalize_line(line: str) -> str:
    line = _ANSI.sub("", line.rstrip("\n\r"))
    return _GH_PREFIX.sub("", line).rstrip()


def _job_name(raw: str) -> str | None:
    """GitHub job name from a `gh run view --log-failed` line, if present."""
    match = _GH_JOB.match(_ANSI.sub("", raw.rstrip("\n\r")))
    if match is None:
        return None
    return match.group(1)


def _failed_jobs(text: str) -> frozenset[str] | None:
    """Failed job names when the log mixes failed and successful jobs.

    Returns None when every line should be scored: no job prefixes, a single
    job, or every job failed. A successful job's signals must not outrank the
    step that actually failed.
    """
    seen: dict[str, bool] = {}
    for raw in text.splitlines():
        name = _job_name(raw)
        if name is None:
            continue
        failed = _FAILED_STEP.search(normalize_line(raw)) is not None
        seen[name] = seen.get(name, False) or failed
    if len(seen) < 2:
        return None
    failed_names = frozenset(name for name, failed in seen.items() if failed)
    if not failed_names or len(failed_names) == len(seen):
        return None
    return failed_names


def confidence_level(confidence: float) -> str:
    if confidence >= 0.8:
        return "high"
    if confidence >= 0.6:
        return "medium"
    return "low"


def _as_float(value: float) -> float:
    return float(f"{value:.2f}")


def _prepare(text: str) -> tuple[str, bool]:
    """Cap an in-memory log at MAX_BYTES. Prefer read_log_text for files."""
    if len(text) <= MAX_BYTES and text.isascii():
        return text, False
    raw = text.encode("utf-8", errors="replace")
    if len(raw) <= MAX_BYTES:
        return text, False
    raw = raw[:MAX_BYTES]
    newline = raw.rfind(b"\n")
    if newline >= 0:
        raw = raw[:newline]
    return raw.decode("utf-8", errors="replace"), True


def _read_capped(stream: io.BufferedIOBase, limit: int) -> tuple[bytes, bool]:
    """Read at most `limit` bytes. One extra byte records that more existed."""
    chunks: list[bytes] = []
    remaining = limit
    while remaining > 0:
        block = stream.read(min(65536, remaining))
        if not block:
            return b"".join(chunks), False
        chunks.append(block)
        remaining -= len(block)
    extra = stream.read(1)
    return b"".join(chunks), bool(extra)


def _decode_capped(raw: bytes, truncated: bool) -> str:
    if truncated:
        newline = raw.rfind(b"\n")
        if newline >= 0:
            raw = raw[:newline]
    return raw.decode("utf-8", errors="replace")


def read_log_text(path: Path) -> tuple[str, bool]:
    """Stream a log up to MAX_BYTES. The rest of a huge file is not read."""
    with path.open("rb") as handle:
        raw, truncated = _read_capped(handle, MAX_BYTES)
    return _decode_capped(raw, truncated), truncated


def _consider_hit(pool: list[Hit], hit: Hit) -> None:
    """Keep the strongest EVIDENCE_POOL lines. The same line keeps the heavier hit."""
    for index, current in enumerate(pool):
        if current.line_no == hit.line_no:
            if hit.weight > current.weight:
                pool[index] = hit
            return
    if len(pool) < EVIDENCE_POOL:
        pool.append(hit)
        return
    worst_index = 0
    worst_key = (pool[0].weight, -pool[0].line_no)
    for index, current in enumerate(pool):
        key = (current.weight, -current.line_no)
        if key < worst_key:
            worst_key = key
            worst_index = index
    if (hit.weight, -hit.line_no) > worst_key:
        pool[worst_index] = hit


def _signals_in_rule_order(matched: list[bool], category: str | None) -> list[str]:
    """Signals follow COMPILED order, which is the order reports already show."""
    signals: list[str] = []
    for index, (rule, _pattern) in enumerate(COMPILED):
        if not matched[index]:
            continue
        if category is not None and rule.category != category:
            continue
        if rule.signal not in signals:
            signals.append(rule.signal)
    return signals


def _select_evidence(hits: list[Hit], category: str) -> list[Hit]:
    chosen = [hit for hit in hits if hit.category == category]
    if not chosen:
        chosen = list(hits)
    best: dict[int, Hit] = {}
    for hit in chosen:
        current = best.get(hit.line_no)
        if current is None or hit.weight > current.weight:
            best[hit.line_no] = hit
    ranked = sorted(best.values(), key=lambda hit: (-hit.weight, hit.line_no))
    top = ranked[:MAX_EVIDENCE]
    return sorted(top, key=lambda hit: hit.line_no)


def _tie_cache_eacces_with_lockfile(
    scores: dict[str, int], matched: list[bool]
) -> None:
    """Keep a bare cache EACCES under the threshold.

    The same EACCES line plus a lockfile hit would otherwise be reported as
    deps and hide the cache failure. Match the infra score to deps so the
    two tie. A stronger infra hit, such as a corrupt cache restore, is left
    as the leader.
    """
    eacces = any(
        matched[index] and rule.signal == "cache path EACCES"
        for index, (rule, _pattern) in enumerate(COMPILED)
    )
    if eacces and scores["deps"] >= MIN_SCORE and scores["infra"] < scores["deps"]:
        scores["infra"] = scores["deps"]


def classify(text: str) -> Classification:
    """Classify log text. Does not read fixture labels.

    Each line is normalized and redacted once, then every rule is scored at
    most once. Matching runs on the redacted line so a secret cannot become
    a signal. Evidence keeps a bounded pool per category.
    """
    body, truncated = _prepare(text)
    failed_jobs = _failed_jobs(body)
    scores = {category: 0 for category in CATEGORIES}
    matched = [False] * len(COMPILED)
    pools: dict[str, list[Hit]] = {category: [] for category in CATEGORIES}
    prefix_stripped = False
    last_text = ""
    last_line = 0

    for line_no, raw in enumerate(body.splitlines(), start=1):
        if failed_jobs is not None:
            job = _job_name(raw)
            if job is not None and job not in failed_jobs:
                continue
        cleaned = normalize_line(raw)
        if cleaned != raw.rstrip("\n\r"):
            prefix_stripped = True
        if not cleaned.strip():
            continue
        redacted_line = redact(cleaned)
        last_text = redacted_line
        last_line = line_no
        for index, (rule, pattern) in enumerate(COMPILED):
            if pattern.search(redacted_line) is None:
                continue
            if not matched[index]:
                matched[index] = True
                scores[rule.category] += rule.weight
            _consider_hit(
                pools[rule.category],
                Hit(
                    line_no=line_no,
                    text=redacted_line,
                    category=rule.category,
                    weight=rule.weight,
                    signal=rule.signal,
                ),
            )

    _tie_cache_eacces_with_lockfile(scores, matched)
    hits = [hit for pool in pools.values() for hit in pool]
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    top_category, top_score = ranked[0]
    second_score = ranked[1][1]
    leaders = [cat for cat, score in ranked if score == top_score and score >= MIN_SCORE]
    close = [
        cat
        for cat, score in ranked
        if cat != top_category and score >= MIN_SCORE and top_score - score <= 2
    ]

    if len(leaders) > 1:
        category = "unknown"
        confidence = 0.42
        alternates = leaders
        evidence_hits = _select_evidence(hits, "unknown") or _select_evidence(
            hits, leaders[0]
        )
        signals = [hit.signal for hit in evidence_hits]
        signals.append("tie between " + ", ".join(leaders))
    elif top_score < MIN_SCORE:
        category = "unknown"
        confidence = _as_float(0.2 + 0.03 * min(top_score, 5))
        alternates = []
        evidence_hits = _select_evidence(hits, "unknown")
        if not evidence_hits and last_text:
            evidence_hits = [
                Hit(last_line, last_text, "unknown", 0, "last log line")
            ]
        signals = _signals_in_rule_order(matched, None)
        if signals:
            signals.append("below the v0 decision threshold")
        else:
            signals.append("no taxonomy signal")
    else:
        category = top_category
        margin_ratio = (top_score - second_score) / top_score
        strength = min(top_score / 24.0, 1.0)
        confidence = 0.62 + 0.2 * strength + 0.12 * margin_ratio
        alternates = close
        if close:
            confidence = min(confidence, 0.64)
        confidence = _as_float(max(0.6, min(0.93, confidence)))
        evidence_hits = _select_evidence(hits, category)
        signals = _signals_in_rule_order(matched, category)

    # Deduplicate signal order while keeping the first occurrence.
    deduped: list[str] = []
    for signal in signals:
        if signal not in deduped:
            deduped.append(signal)

    return Classification(
        category=category,
        confidence=confidence,
        confidence_level=confidence_level(confidence),
        evidence=[
            {"line": hit.line_no, "text": hit.text[:300]} for hit in evidence_hits
        ],
        next_steps=list(NEXT_STEPS[category]),
        scores=scores,
        signals=deduped,
        alternates=alternates,
        truncated=truncated,
        prefix_stripped=prefix_stripped,
    )


def _scan_forbidden(label: str, text: str) -> None:
    for pattern in _FORBIDDEN_IN_CORPUS:
        match = pattern.search(text)
        if match:
            raise CorpusError(
                f"{label} contains a forbidden secret-like pattern "
                f"({pattern.pattern}); fixtures must stay redacted"
            )


def _require_str(meta: dict[str, object], key: str, where: str) -> str:
    value = meta.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CorpusError(f"{where}: {key} must be a non-empty string")
    return value


def load_fixture(directory: Path) -> dict[str, object]:
    meta_path = directory / "meta.json"
    log_path = directory / "log.txt"
    where = directory.name
    if not meta_path.is_file() or not log_path.is_file():
        raise CorpusError(f"{where}: needs meta.json and log.txt")
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CorpusError(f"{where}: meta.json is not valid JSON ({exc})") from exc
    if not isinstance(meta, dict):
        raise CorpusError(f"{where}: meta.json must be an object")

    fixture_id = _require_str(meta, "id", where)
    label = _require_str(meta, "label", where)
    notes = _require_str(meta, "notes", where)
    source = _require_str(meta, "source", where)
    if fixture_id != directory.name:
        raise CorpusError(f"{where}: id {fixture_id!r} does not match the directory")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fixture_id):
        raise CorpusError(f"{where}: id must be lowercase kebab-case")
    if label not in CATEGORIES:
        raise CorpusError(f"{where}: label {label!r} is not in the v0 taxonomy")
    if len(notes) < 20:
        raise CorpusError(f"{where}: notes must describe the case (20+ characters)")
    if source not in ALLOWED_SOURCES:
        raise CorpusError(
            f"{where}: source must be one of {', '.join(sorted(ALLOWED_SOURCES))}"
        )
    if meta.get("redacted") is not True:
        raise CorpusError(f"{where}: redacted must be true")

    expected_host = HOST_BY_DIR.get(directory.parent.name)
    host = meta.get("host")
    if expected_host:
        if host != expected_host:
            raise CorpusError(f"{where}: host must be {expected_host!r}")
    elif host is not None and not isinstance(host, str):
        raise CorpusError(f"{where}: host must be a string when set")

    if log_path.stat().st_size > MAX_BYTES:
        raise CorpusError(
            f"{where}: log.txt is larger than {MAX_BYTES} bytes; fixtures must stay small"
        )
    log_text = log_path.read_text(encoding="utf-8")
    if not log_text.strip():
        raise CorpusError(f"{where}: log.txt is empty")
    if source == "synthetic":
        missing = [marker for marker in SYNTHETIC_MARKERS if marker not in log_text]
        if missing:
            raise CorpusError(
                f"{where}: synthetic log must include {missing} "
                "so the corpus stays obviously invented"
            )
    else:
        lowered = log_text.lower()
        if "redacted" not in lowered:
            raise CorpusError(f"{where}: redacted-public logs must say they are redacted")

    blob = meta_path.read_text(encoding="utf-8") + "\n" + log_text
    _scan_forbidden(where, blob)
    return {
        "id": fixture_id,
        "directory": directory,
        "log_path": log_path,
        "log_text": log_text,
        "meta": meta,
    }


def load_fixtures(directory: Path) -> list[dict[str, object]]:
    if not directory.is_dir():
        raise CorpusError(f"fixtures directory not found: {directory}")
    children = sorted(path for path in directory.iterdir() if path.is_dir())
    if not children:
        raise CorpusError(f"no fixture directories in {directory}")
    fixtures: list[dict[str, object]] = []
    errors: list[str] = []
    for child in children:
        try:
            fixtures.append(load_fixture(child))
        except CorpusError as exc:
            errors.append(str(exc))
    if errors:
        raise CorpusError("\n".join(errors))
    return fixtures


def display_path(path: Path) -> str:
    resolved = path.resolve()
    for base in (Path.cwd().resolve(), REPO_ROOT):
        try:
            return str(resolved.relative_to(base))
        except ValueError:
            continue
    return str(path)


def build_report(
    log_text: str,
    *,
    log_path: Path | None = None,
    fixture: dict[str, object] | None = None,
    truncated: bool = False,
) -> dict[str, object]:
    result = classify(log_text)
    meta = fixture["meta"] if fixture else {}
    assert isinstance(meta, dict)
    expected = meta.get("label") if fixture else None
    report: dict[str, object] = {
        "tool": "ci-doctor",
        "version": VERSION,
        "id": fixture["id"] if fixture else None,
        "log": display_path(log_path) if log_path else None,
        "category": result.category,
        "confidence": result.confidence,
        "confidence_level": result.confidence_level,
        "advisory": True,
        "signals": result.signals,
        "evidence": result.evidence,
        "next_steps": result.next_steps,
        "scores": result.scores,
        "alternates": result.alternates,
        "truncated": bool(result.truncated or truncated),
        "prefix_stripped": result.prefix_stripped,
        "redacted": True,
        "expected_label": expected,
        "label_match": (result.category == expected) if expected else None,
        "notes": redact(str(meta["notes"])) if fixture else None,
        "source": meta.get("source") if fixture else None,
        "synthetic": meta.get("source") == "synthetic" if fixture else None,
        "host": meta.get("host") if fixture else None,
    }
    return report


def format_report(report: dict[str, object]) -> str:
    lines = [
        f"ci-doctor {VERSION}",
        f"id: {report['id'] or '-'}",
        f"log: {report['log'] or '-'}",
        f"category: {report['category']}",
        (
            f"confidence: {report['confidence']:.2f} "
            f"({report['confidence_level']})"
        ),
        "advisory: classification only; not a merge decision",
    ]
    if report.get("expected_label"):
        matched = "yes" if report["label_match"] else "NO"
        lines.append(f"expected_label: {report['expected_label']}")
        lines.append(f"label_match: {matched}")
    alternates = report.get("alternates") or []
    if alternates:
        lines.append("alternates: " + ", ".join(str(item) for item in alternates))
    signals = report.get("signals") or []
    if signals:
        lines.append("signals: " + "; ".join(str(item) for item in signals))
    if report.get("truncated"):
        lines.append("truncated: log exceeded 2MB and was cut before classification")
    if report.get("prefix_stripped"):
        lines.append("prefix_stripped: removed gh job/step/timestamp prefixes")
    lines.append("")
    lines.append("evidence:")
    evidence = report["evidence"]
    assert isinstance(evidence, list)
    if not evidence:
        lines.append("  (none)")
    else:
        for item in evidence:
            assert isinstance(item, dict)
            lines.append(f"  L{item['line']:<4} {item['text']}")
    lines.append("")
    lines.append("next_steps:")
    steps = report["next_steps"]
    assert isinstance(steps, list)
    for index, step in enumerate(steps, start=1):
        lines.append(f"  {index}. {step}")
    if report.get("notes"):
        lines.append("")
        lines.append("notes:")
        lines.append(f"  {report['notes']}")
    if report.get("expected_label") and report.get("label_match") is False:
        lines.append("")
        lines.append("scores: " + json.dumps(report["scores"], sort_keys=True))
    lines.append("")
    return "\n".join(lines)


def format_batch(payload: dict[str, object]) -> str:
    reports = payload["reports"]
    assert isinstance(reports, list)
    rows = [
        f"{'id':<32} {'category':<14} {'conf':<6} {'level':<6} {'expected':<14} match",
    ]
    blocks: list[str] = []
    for report in reports:
        assert isinstance(report, dict)
        if report["label_match"] is None:
            matched = "-"
        else:
            matched = "yes" if report["label_match"] else "NO"
        expected = report["expected_label"] or "-"
        rows.append(
            f"{str(report['id'] or '-'):<32} "
            f"{str(report['category']):<14} "
            f"{float(report['confidence']):<6.2f} "
            f"{str(report['confidence_level']):<6} "
            f"{str(expected):<14} {matched}"
        )
        blocks.append(format_report(report).rstrip())
    rows.append("")
    rows.append(
        f"{payload['matched']}/{payload['count']} fixtures matched the expected label."
    )
    failed = payload["failed"]
    assert isinstance(failed, list)
    if failed:
        rows.append("mismatches:")
        for item in failed:
            rows.append(f"  - {item}")
    rows.append("")
    return "\n".join(rows) + "\n\n" + "\n\n".join(blocks) + "\n"


def resolve_dir(path: Path) -> Path:
    if path.is_dir():
        return path
    alternative = (REPO_ROOT / path).resolve()
    if alternative.is_dir():
        return alternative
    return path


def resolve_file(path: Path) -> Path:
    if path.is_file():
        return path
    alternative = REPO_ROOT / path
    if alternative.is_file():
        return alternative
    return path


# github.com/OWNER/REPO/actions/runs/RUN_ID, with an optional browser /job/N suffix.
_RUN_URL = re.compile(
    r"^https?://github\.com/"
    r"(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)"
    r"/actions/runs/(?P<run_id>\d+)"
    r"(?:/(?:job|jobs)/\d+)?"
    r"/?(?:\?.*)?$",
    re.IGNORECASE,
)
_REPO_SLUG = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
GH_TIMEOUT_SECONDS = 120


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    truncated: bool = False


@dataclass(frozen=True)
class FetchedLog:
    text: str
    truncated: bool


@dataclass(frozen=True)
class RunRequest:
    repo: str
    run_id: str

    def command(self) -> list[str]:
        return [
            "gh",
            "run",
            "view",
            self.run_id,
            "--repo",
            self.repo,
            "--log-failed",
        ]


def parse_run_request(
    run_url: str | None,
    run_id: str | None,
    repo: str | None,
) -> RunRequest:
    """Resolve a public Actions run from a URL, a run id, or both plus --repo."""
    if run_url and run_id:
        raise GhError("Pass only one of --run-url or --run-id.")
    if not run_url and not run_id:
        raise GhError("Pass --run-url or --run-id.")

    parsed_repo: str | None = None
    parsed_id: str | None = None
    if run_url:
        match = _RUN_URL.match(run_url.strip())
        if match is None:
            raise GhError(
                "Could not read a GitHub Actions run URL. "
                "Expected https://github.com/OWNER/REPO/actions/runs/RUN_ID"
            )
        parsed_repo = f"{match.group('owner')}/{match.group('repo')}"
        parsed_id = match.group("run_id")
    if run_id:
        if not re.fullmatch(r"\d+", run_id):
            raise GhError("--run-id must be the numeric Actions run id.")
        parsed_id = run_id
    if repo:
        if _REPO_SLUG.fullmatch(repo) is None:
            raise GhError("--repo must look like owner/repo.")
        if parsed_repo and parsed_repo.lower() != repo.lower():
            raise GhError(
                f"--repo {repo} does not match the URL repository {parsed_repo}."
            )
        parsed_repo = repo
    if not parsed_repo or not parsed_id:
        raise GhError("--run-id needs --repo owner/repo.")
    return RunRequest(parsed_repo, parsed_id)


def format_dry_run(request: RunRequest) -> str:
    command = " ".join(request.command())
    return (
        f"ci-doctor {VERSION}\n"
        "dry_run: true\n"
        f"repo: {request.repo}\n"
        f"run_id: {request.run_id}\n"
        f"command: {command}\n"
    )


def dry_run_payload(request: RunRequest) -> dict[str, object]:
    return {
        "tool": "ci-doctor",
        "version": VERSION,
        "dry_run": True,
        "repo": request.repo,
        "run_id": request.run_id,
        "command": request.command(),
    }


def default_runner(argv: list[str]) -> CommandResult:
    """Run a command and keep at most MAX_BYTES of stdout.

    A live `gh run view --log-failed` can stream far more than we score.
    Hitting the cap kills the process so a full pipe cannot stall the read.
    """
    try:
        proc = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError:
        raise GhError(
            "gh is not installed. Install the GitHub CLI, or save the failed log and run:\n"
            "  python3 scripts/diagnose.py <saved-log>"
        ) from None

    assert proc.stdout is not None
    assert proc.stderr is not None
    stdout_raw = b""
    stderr_raw = b""
    truncated = False

    def consume_stdout() -> None:
        nonlocal stdout_raw, truncated
        data, hit_cap = _read_capped(proc.stdout, MAX_BYTES)
        stdout_raw = data
        truncated = hit_cap
        if hit_cap:
            proc.kill()

    def consume_stderr() -> None:
        nonlocal stderr_raw
        data, hit_cap = _read_capped(proc.stderr, _STDERR_CAP)
        stderr_raw = data
        if hit_cap:
            proc.kill()

    out_thread = threading.Thread(target=consume_stdout, daemon=True)
    err_thread = threading.Thread(target=consume_stderr, daemon=True)
    out_thread.start()
    err_thread.start()
    try:
        try:
            returncode = proc.wait(timeout=GH_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            out_thread.join(timeout=5)
            err_thread.join(timeout=5)
            raise GhError(
                "gh timed out after 120s. Save the failed log and pass that file instead:\n"
                "  python3 scripts/diagnose.py <saved-log>"
            ) from None
        out_thread.join(timeout=5)
        err_thread.join(timeout=5)
        return CommandResult(
            returncode,
            _decode_capped(stdout_raw, truncated),
            stderr_raw.decode("utf-8", errors="replace"),
            truncated,
        )
    finally:
        proc.stdout.close()
        proc.stderr.close()


def ensure_gh_ready(
    runner: Callable[[list[str]], CommandResult],
    which: Callable[[str], str | None],
) -> None:
    """Fail closed before any log fetch. `which` and `runner` are injectable."""
    if not which("gh"):
        raise GhError(
            "gh is not installed. Install the GitHub CLI, or save the failed log and run:\n"
            "  python3 scripts/diagnose.py <saved-log>"
        )
    status = runner(["gh", "auth", "status"])
    if status.returncode != 0:
        raise GhError(
            "gh is not logged in. Run `gh auth login` in your own terminal, "
            "or save the failed log and run:\n"
            "  python3 scripts/diagnose.py <saved-log>"
        )


def fetch_failed_log(
    request: RunRequest,
    *,
    runner: Callable[[list[str]], CommandResult] = default_runner,
    which: Callable[[str], str | None] = shutil.which,
) -> FetchedLog:
    """Fetch failed-step logs and redact them before the caller scores them."""
    ensure_gh_ready(runner, which)
    result = runner(request.command())
    # A size cap kills `gh` on purpose. Keep the bytes already read.
    if result.returncode != 0 and not (result.truncated and result.stdout.strip()):
        detail = redact((result.stderr or result.stdout or "").strip())
        detail = detail[:400]
        message = f"gh could not fetch the failed log (exit {result.returncode})."
        if detail:
            message = f"{message}\n{detail}"
        raise GhError(message)
    if not result.stdout.strip():
        raise GhError(
            "gh returned an empty failed-step log. The run may still be in "
            "progress, or no step failed."
        )
    return FetchedLog(redact(result.stdout), result.truncated)


def run_self_check() -> int:
    failures: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    token = "ghp_" + ("a" * 36)
    aws = "AKIA" + ("0" * 16)
    secret = "example-value-not-real"
    raw = (
        f"Authorization: Bearer {token}\n"
        f"key={aws}\n"
        f"password={secret}\n"
        f"https://npm:{secret}@registry.example.com/npm\n"
        "NODE_AUTH_TOKEN is empty\n"
        "DATABASE_URL is not set\n"
    )
    cleaned = redact(raw)
    check(token not in cleaned, "github token leaked")
    check(aws not in cleaned, "aws key leaked")
    check(secret not in cleaned, "password leaked")
    check("NODE_AUTH_TOKEN is empty" in cleaned, "env name was redacted")
    check("DATABASE_URL is not set" in cleaned, "DATABASE_URL name was redacted")
    supplied = redact("Input required and not supplied: NODE_AUTH_TOKEN")
    check(supplied == "Input required and not supplied: NODE_AUTH_TOKEN", "input name was redacted")
    scope = "The job was not granted id-token: write."
    check(redact(scope) == scope, "permission scope was redacted")
    check(redact(cleaned) == cleaned, "redact is not idempotent")
    jwt = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJzdWIiOiIxMjM0NTY3ODkwIn0"
        ".dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    )
    check(jwt not in redact("bearer " + jwt), "jwt leaked")
    asia = "ASIA" + ("0" * 16)
    stripe = "sk_live_" + ("a" * 24)
    npm_token = "npm_" + ("b" * 36)
    slack = (
        "https://hooks.slack.com/services/"
        + "T" + ("0" * 8)
        + "/B" + ("0" * 8)
        + "/" + ("X" * 24)
    )
    client_secret = "client_secret=example-client-secret-value"
    extra = redact(
        f"{asia}\n{stripe}\n{npm_token}\n{slack}\n{client_secret}\n"
        "x-api-key: example-header-secret\n"
    )
    check(asia not in extra, "aws session key leaked")
    check(stripe not in extra, "stripe key leaked")
    check(npm_token not in extra, "npm token leaked")
    check("hooks.slack.com" not in extra, "slack webhook leaked")
    check("example-client-secret-value" not in extra, "client secret leaked")
    check("example-header-secret" not in extra, "api key header leaked")
    check(redact(extra) == extra, "extended redact is not idempotent")
    check(redact(scope) == scope, "permission scope still intact")

    samples = {
        "test": "FAIL src/a.test.ts\nExpected: 1\nReceived: 2\nexpect(received).toBe(expected)\n",
        "env": "Error: Required environment variable DATABASE_URL is not set\n",
        "deps": "npm ERR! code ERESOLVE\nnpm ERR! ERESOLVE unable to resolve dependency tree\n",
        "permissions": "HttpError: Resource not accessible by integration\n",
        "flake": "Suspected flake: passed on the automatic rerun\nExceeded timeout of 5000 ms\n",
        "infra": "FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory\n",
        "unknown": "##[error]Process completed with exit code 1.\n",
    }
    for expected, sample in samples.items():
        got = classify(sample)
        check(
            got.category == expected,
            f"sample {expected} classified as {got.category}",
        )
        if expected == "unknown":
            check(got.confidence_level == "low", "unknown sample should be low confidence")
        else:
            check(
                got.confidence >= 0.6,
                f"{expected} confidence too low ({got.confidence})",
            )

    prefixed = (
        "build\tRun tests\t2026-10-26T01:14:22.1038427Z FAIL src/a.test.ts\n"
        "build\tRun tests\t2026-10-26T01:14:22.1038427Z Expected: 1\n"
        "build\tRun tests\t2026-10-26T01:14:22.1038427Z Received: 2\n"
    )
    prefixed_result = classify(prefixed)
    check(prefixed_result.category == "test", "gh log prefix hid the Jest failure")
    check(prefixed_result.prefix_stripped, "gh log prefix was not stripped")

    mixed = (
        "FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory\n"
        "FAIL src/a.test.ts\n"
    )
    check(classify(mixed).category == "infra", "heap OOM lost to a stray FAIL line")

    leaked = classify(
        "FAIL src/a.test.ts\nExpected: 1\nAuthorization: Bearer " + token + "\n"
    )
    blob = json.dumps(leaked.evidence)
    check(token not in blob, "evidence leaked a token")
    check(leaked.category == "test", "token line flipped the category")
    check(all(rule.category in CATEGORIES for rule in RULES), "rule outside taxonomy")
    check(set(NEXT_STEPS) == set(CATEGORIES), "next steps missing a category")

    go_line = "FAIL\texample.com/example-app/api\t0.021s\n--- FAIL: TestHealth (0.00s)\n"
    go_result = classify(go_line)
    check(go_result.category == "test", "go FAIL")
    check(not go_result.prefix_stripped, "go tabs were treated as a gh prefix")
    check(classify("ERR_PNPM_OUTDATED_LOCKFILE\n").category == "deps", "pnpm lockfile")
    check(
        classify(
            "Test timeout of 30000ms exceeded.\nSuspected flake: passed on the previous run\n"
        ).category
        == "flake",
        "playwright timeout",
    )
    hard_unknown = "##[error]The operation was canceled.\nNo step log was uploaded.\n"
    hard = classify(hard_unknown)
    check(hard.category == "unknown", f"hard unknown classified as {hard.category}")
    check(max(hard.scores.values()) < MIN_SCORE, "hard unknown cleared the threshold")

    sample_url = (
        "https://github.com/example-org/example-app/actions/runs/123456789/job/42"
    )
    request = parse_run_request(sample_url, None, None)
    check(request.repo == "example-org/example-app", "url repo")
    check(request.run_id == "123456789", "url run id")
    check("--job" not in request.command(), "browser job id leaked into gh argv")
    check(
        request.command()
        == [
            "gh",
            "run",
            "view",
            "123456789",
            "--repo",
            "example-org/example-app",
            "--log-failed",
        ],
        "gh argv",
    )
    try:
        parse_run_request(None, "55", None)
        check(False, "run id without repo should fail")
    except GhError as exc:
        check("--repo" in str(exc), "missing repo message")
    try:
        parse_run_request(sample_url, None, "other/repo")
        check(False, "mismatched repo should fail")
    except GhError as exc:
        check("does not match" in str(exc), "repo mismatch message")

    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        dry_code = main(["--run-url", sample_url, "--dry-run", "--format", "text"])
    dry_text = out.getvalue()
    check(dry_code == 0, f"dry-run exit {dry_code}: {err.getvalue()}")
    check("dry_run: true" in dry_text, "dry-run marker")
    check("gh run view 123456789 --repo example-org/example-app --log-failed" in dry_text, "dry-run command")
    check("--job" not in dry_text, "dry-run included a job id")

    try:
        ensure_gh_ready(lambda _argv: CommandResult(0, "", ""), lambda _name: None)
        check(False, "missing gh should fail")
    except GhError as exc:
        check("not installed" in str(exc), "missing gh message")
        check("Traceback" not in str(exc), "missing gh traceback")

    calls: list[list[str]] = []

    def unauth(argv: list[str]) -> CommandResult:
        calls.append(argv)
        return CommandResult(1, "", "You are not logged into any GitHub hosts")

    try:
        fetch_failed_log(
            request,
            runner=unauth,
            which=lambda _name: "/usr/bin/gh",
        )
        check(False, "logged-out gh should fail")
    except GhError as exc:
        message = str(exc)
        check("not logged in" in message, "logged-out message")
        check("not logged into" not in message, "raw gh auth stderr leaked")
        check("Traceback" not in message, "logged-out traceback")
        check(calls == [["gh", "auth", "status"]], f"logged-out calls {calls}")

    def authed(argv: list[str]) -> CommandResult:
        if argv[:3] == ["gh", "auth", "status"]:
            return CommandResult(0, "", "")
        return CommandResult(
            0,
            "FAIL src/a.test.ts\nAuthorization: Bearer " + token + "\nExpected: 1\n",
            "",
        )

    fetched = fetch_failed_log(request, runner=authed, which=lambda _name: "/usr/bin/gh")
    check(token not in fetched.text, "fetched log was not redacted before scoring")
    check(fetched.truncated is False, "small fetch was marked truncated")
    fetched_report = build_report(fetched.text, truncated=fetched.truncated)
    check(fetched_report["category"] == "test", "redacted fetch lost the test signal")
    check(token not in json.dumps(fetched_report), "live report leaked a token")

    if failures:
        for item in failures:
            print(f"self-check: {item}", file=sys.stderr)
        return 1
    print("self-check: ok", file=sys.stderr)
    return 0


def _emit(text: str, as_json: bool) -> None:
    stream = sys.stderr if as_json else sys.stdout
    print(text, file=stream)


def diagnose_fixture(fixture: dict[str, object]) -> dict[str, object]:
    log_path = fixture["log_path"]
    log_text = fixture["log_text"]
    assert isinstance(log_path, Path)
    assert isinstance(log_text, str)
    return build_report(log_text, log_path=log_path, fixture=fixture)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="diagnose.py",
        allow_abbrev=False,
        description=(
            "Classify a CI log into the ci-doctor v0 taxonomy and print a "
            "redacted report. Offline logs and fixtures, or a live Actions run via gh."
        ),
    )
    parser.add_argument("log", nargs="?", help="Path to a CI log")
    parser.add_argument("--fixture", help="Fixture id under the fixtures directory")
    parser.add_argument(
        "--fixtures-dir",
        help="Classify every fixture directory (each needs meta.json and log.txt)",
    )
    parser.add_argument(
        "--run-url",
        help="GitHub Actions run URL (https://github.com/OWNER/REPO/actions/runs/ID)",
    )
    parser.add_argument("--run-id", help="Numeric Actions run id; requires --repo")
    parser.add_argument(
        "--repo",
        help="owner/repo for --run-id, or a check against --run-url",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --run-url or --run-id, print the gh command and do not fetch",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Report format (default: text)",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Run redaction and taxonomy self-checks",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ci-doctor {VERSION}",
    )
    args = parser.parse_args(argv)

    modes = [
        bool(args.log),
        bool(args.fixture),
        bool(args.fixtures_dir),
        bool(args.run_url) or bool(args.run_id),
    ]
    if sum(modes) > 1:
        parser.error("pass only one log source: a path, --fixture, --fixtures-dir, or a run")
    if args.dry_run and not (args.run_url or args.run_id):
        parser.error("--dry-run is only for --run-url or --run-id")
    if args.repo and not (args.run_url or args.run_id):
        parser.error("--repo is only for --run-url or --run-id")
    if not any(modes) and not args.self_check:
        parser.print_help(sys.stderr)
        return 2

    code = 0
    as_json = args.format == "json"
    if args.self_check:
        check_code = run_self_check()
        if check_code != 0:
            return check_code
        if not any(modes):
            return 0

    try:
        if args.fixtures_dir:
            directory = resolve_dir(Path(args.fixtures_dir))
            fixtures = load_fixtures(directory)
            reports = [diagnose_fixture(fixture) for fixture in fixtures]
            failed = [
                (
                    f"{report['id']}: classified as {report['category']}, "
                    f"expected {report['expected_label']}"
                )
                for report in reports
                if report["label_match"] is False
            ]
            payload: dict[str, object] = {
                "tool": "ci-doctor",
                "version": VERSION,
                "count": len(reports),
                "matched": len(reports) - len(failed),
                "failed": failed,
                "reports": reports,
            }
            if as_json:
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print(format_batch(payload), end="")
            return 1 if failed else 0

        if args.fixture:
            directory = resolve_dir(
                Path(args.fixtures_dir) if args.fixtures_dir else DEFAULT_FIXTURES
            )
            fixtures = load_fixtures(directory)
            match = next(
                (fixture for fixture in fixtures if fixture["id"] == args.fixture),
                None,
            )
            if match is None:
                known = ", ".join(str(fixture["id"]) for fixture in fixtures)
                print(
                    f"unknown fixture {args.fixture!r}. "
                    f"Run --fixtures-dir to list ids. Known: {known}",
                    file=sys.stderr,
                )
                return 2
            report = diagnose_fixture(match)
        elif args.log:
            log_path = resolve_file(Path(args.log))
            if not log_path.is_file():
                print(
                    f"log not found: {args.log}. "
                    "Pass a saved log, --fixture, or --run-url.",
                    file=sys.stderr,
                )
                return 2
            log_text, truncated = read_log_text(log_path)
            report = build_report(log_text, log_path=log_path, truncated=truncated)
        elif args.run_url or args.run_id:
            request = parse_run_request(args.run_url, args.run_id, args.repo)
            if args.dry_run:
                if as_json:
                    print(json.dumps(dry_run_payload(request), indent=2))
                else:
                    print(format_dry_run(request), end="")
                return 0
            fetched = fetch_failed_log(request)
            report = build_report(fetched.text, truncated=fetched.truncated)
            report["id"] = f"{request.repo}#{request.run_id}"
            report["log"] = " ".join(request.command())
            report["repo"] = request.repo
            report["run_id"] = request.run_id
            report["source"] = "github-actions"
            report["synthetic"] = False
            report["host"] = "github-actions"
        else:
            parser.print_help(sys.stderr)
            return 2

        if as_json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(format_report(report), end="")
        if report.get("label_match") is False:
            return 1
        return code
    except (CorpusError, GhError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
