#!/usr/bin/env python3
"""GitHub Action entrypoint for ci-diagnose.

Stdlib only. No LLM and no extra packages. Fixture and log-path modes do
not use the network. Run-log download and the opt-in PR comment use the
GitHub API with the workflow token.

Exit codes:
  0  report written, or the current run is still in progress
  1  the logs API or the comment API failed
  2  bad inputs
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

COMMENT_MARKER = "<!-- ci-doctor -->"
HttpFn = Callable[[str, str, dict[str, str], bytes | None], tuple[int, bytes, dict[str, str]]]


class ActionError(Exception):
    """A usage or API failure whose message is safe to print."""


def _load_diagnose():
    path = Path(__file__).resolve().parent / "diagnose.py"
    spec = importlib.util.spec_from_file_location("diagnose", path)
    if spec is None or spec.loader is None:
        raise ActionError(f"diagnose.py is missing next to {__file__}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["diagnose"] = module
    spec.loader.exec_module(module)
    return module


def as_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def scrub_redirect(old_url: str, new_url: str, headers: dict[str, str]) -> dict[str, str]:
    """Drop Authorization when a redirect leaves the API host.

    The logs endpoint redirects to blob storage. The token must not follow.
    """
    old, new = urlsplit(old_url), urlsplit(new_url)
    if (old.scheme, old.netloc) == (new.scheme, new.netloc):
        return dict(headers)
    return {key: value for key, value in headers.items() if key.lower() != "authorization"}


def _header(headers: dict[str, str], name: str) -> str:
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return ""


def urllib_request(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | None = None,
) -> tuple[int, bytes, dict[str, str]]:
    """HTTP with manual redirects. Authorization stays on the API host."""
    current = url
    current_headers = dict(headers)
    payload = body
    current_method = method
    for _ in range(6):
        request = Request(current, data=payload, headers=current_headers, method=current_method)
        try:
            with urlopen(request, timeout=60) as response:
                raw = response.read()
                got = {key: value for key, value in response.headers.items()}
                return response.status, raw, got
        except HTTPError as exc:
            detail = exc.read()
            got = {key: value for key, value in exc.headers.items()}
            if exc.code in {301, 302, 303, 307, 308}:
                location = got.get("Location") or got.get("location")
                if not location:
                    raise ActionError(f"GitHub API redirect {exc.code} had no Location") from exc
                nxt = location if location.startswith("http") else _join(current, location)
                current_headers = scrub_redirect(current, nxt, current_headers)
                current = nxt
                if exc.code in {301, 302, 303} and current_method != "GET":
                    current_method = "GET"
                    payload = None
                continue
            return exc.code, detail, got
        except URLError as exc:
            raise ActionError(f"GitHub API request failed: {exc.reason}") from exc
    raise ActionError("GitHub API redirected too many times")


def _join(base: str, location: str) -> str:
    if location.startswith("/"):
        parts = urlsplit(base)
        return f"{parts.scheme}://{parts.netloc}{location}"
    return location


def _api_message(body: bytes) -> str:
    try:
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return ""
    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, str):
            return message[:200]
    return ""


def _failed_log_text(name: str, text: str) -> bool:
    lowered = text.lower()
    if "##[error]" in lowered:
        return True
    return re.search(r"process completed with exit code (?!0\b)\d+", lowered) is not None


def text_from_log_download(raw: bytes, limit: int) -> str:
    """Turn a logs zip, or a plain body, into one classifier string.

    When the zip has both failed and successful job files, only the failed
    files are kept. A green job must not outrank the job that failed.
    """
    if raw[:2] == b"PK":
        files: list[tuple[str, str]] = []
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                chunk = archive.read(info).decode("utf-8", errors="replace")
                files.append((info.filename, chunk))
        if not files:
            raise ActionError("the run log archive was empty")
        failed = [(name, text) for name, text in files if _failed_log_text(name, text)]
        chosen = failed if failed and len(failed) < len(files) else files
        pieces: list[str] = []
        total = 0
        for name, text in chosen:
            block = f"# log file: {name}\n{text}"
            pieces.append(block)
            total += len(block)
            if total >= limit:
                break
        return "\n".join(pieces)[:limit]
    return raw.decode("utf-8", errors="replace")[:limit]


def _event_pull_request(path: str | None) -> str:
    if not path:
        return ""
    file = Path(path)
    if not file.is_file():
        return ""
    try:
        event = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if not isinstance(event, dict):
        return ""
    pull = event.get("pull_request")
    if isinstance(pull, dict) and pull.get("number"):
        return str(pull["number"])
    run = event.get("workflow_run")
    if isinstance(run, dict):
        pulls = run.get("pull_requests")
        if isinstance(pulls, list) and pulls and isinstance(pulls[0], dict):
            number = pulls[0].get("number")
            if number:
                return str(number)
    issue = event.get("issue")
    if isinstance(issue, dict) and issue.get("pull_request") and issue.get("number"):
        return str(issue["number"])
    return ""


def escape_md(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_summary(report: dict[str, object]) -> str:
    """Markdown for the job summary and the optional PR comment."""
    evidence = report.get("evidence") or []
    steps = report.get("next_steps") or []
    signals = report.get("signals") or []
    alternates = report.get("alternates") or []
    assert isinstance(evidence, list)
    assert isinstance(steps, list)
    lines = [
        COMMENT_MARKER,
        "## CI Doctor",
        "",
        "Advisory classification. Not a merge decision.",
        "",
        "| | |",
        "| --- | --- |",
        f"| category | `{report['category']}` |",
        (
            f"| confidence | {float(report['confidence']):.2f} "
            f"({report['confidence_level']}) |"
        ),
        "| advisory | classification only; not a merge decision |",
    ]
    if alternates:
        lines.append("| alternates | " + ", ".join(f"`{item}`" for item in alternates) + " |")
    if report.get("truncated"):
        lines.append("| truncated | log was cut at 2MB before scoring |")
    lines.extend(["", "### Evidence", ""])
    if not evidence:
        lines.append("No evidence line.")
    else:
        for item in evidence:
            assert isinstance(item, dict)
            shown = escape_md(str(item["text"])).replace("`", "'")
            lines.append(f"- L{item['line']}: `{shown}`")
    lines.extend(["", "### Next step", ""])
    if steps:
        lines.append("1. " + escape_md(str(steps[0])))
    else:
        lines.append("1. Ask for the failed step log.")
    if signals:
        shown = "; ".join(escape_md(str(item)) for item in signals[:8])
        lines.extend(["", "Signals: " + shown])
    lines.append("")
    return "\n".join(lines)


def write_outputs(path: str | None, report: dict[str, object]) -> None:
    if not path:
        return
    evidence = report.get("evidence") or []
    assert isinstance(evidence, list)
    preview = " | ".join(
        f"L{item['line']}: {item['text']}" for item in evidence if isinstance(item, dict)
    )
    steps = report.get("next_steps") or []
    next_step = str(steps[0]) if isinstance(steps, list) and steps else ""
    fields = {
        "category": str(report["category"]),
        "confidence": f"{float(report['confidence']):.2f}",
        "confidence-level": str(report["confidence_level"]),
        "advisory": "true",
        "next-step": next_step.replace("\n", " ")[:500],
        "evidence": preview.replace("\n", " ")[:1000],
    }
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("a", encoding="utf-8") as handle:
        for key, value in fields.items():
            if "\n" in value:
                handle.write(f"{key}<<EOF_CI_DOCTOR\n{value}\nEOF_CI_DOCTOR\n")
            else:
                handle.write(f"{key}={value}\n")


def write_summary(path: str | None, markdown: str) -> None:
    if not path:
        print(markdown)
        return
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("a", encoding="utf-8") as handle:
        handle.write(markdown)
        if not markdown.endswith("\n"):
            handle.write("\n")


def _auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "ci-diagnose",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_run_log(
    http: HttpFn,
    api: str,
    repo: str,
    run_id: str,
    token: str,
    limit: int,
) -> str:
    if not token:
        raise ActionError("run-id needs a token with actions: read. Pass token, or use log-path.")
    if not repo or "/" not in repo:
        raise ActionError("GITHUB_REPOSITORY must look like owner/repo to download logs.")
    if not run_id.isdigit():
        raise ActionError("run-id must be the numeric Actions run id.")
    url = f"{api}/repos/{repo}/actions/runs/{run_id}/logs"
    status, body, _headers = http("GET", url, _auth_headers(token), None)
    if status == 404:
        raise ActionError(f"run log not found for {run_id}",)
    if status == 403:
        raise ActionError("the token cannot read Actions logs. Grant actions: read.")
    if status >= 400:
        raise ActionError(f"GitHub API {status}: {_api_message(body) or 'log download failed'}")
    return text_from_log_download(body, limit)


class _NotFound(ActionError):
    """The logs endpoint has no archive yet."""


def fetch_run_log_status(
    http: HttpFn,
    api: str,
    repo: str,
    run_id: str,
    token: str,
    limit: int,
) -> str:
    try:
        return fetch_run_log(http, api, repo, run_id, token, limit)
    except ActionError as exc:
        if str(exc).startswith("run log not found"):
            raise _NotFound(str(exc)) from exc
        raise


def upsert_comment(
    http: HttpFn,
    api: str,
    repo: str,
    number: str,
    token: str,
    body: str,
) -> str:
    if not token:
        raise ActionError("comment: true needs a token. The default GITHUB_TOKEN works on a pull request.")
    if not number.isdigit():
        raise ActionError("pull-request must be a number.")
    headers = _auth_headers(token)
    headers["Content-Type"] = "application/json"
    list_url = f"{api}/repos/{repo}/issues/{number}/comments?per_page=100"
    status, raw, _got = http("GET", list_url, headers, None)
    if status == 403:
        raise ActionError("the token cannot post a pull request comment. Grant pull-requests: write.")
    if status >= 400:
        raise ActionError(f"GitHub API {status}: {_api_message(raw) or 'could not list comments'}")
    try:
        comments = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ActionError("GitHub comment list was not JSON") from exc
    existing = None
    if isinstance(comments, list):
        for comment in comments:
            if isinstance(comment, dict) and COMMENT_MARKER in str(comment.get("body") or ""):
                existing = comment
                break
    payload = json.dumps({"body": body}).encode("utf-8")
    if existing and existing.get("id"):
        url = f"{api}/repos/{repo}/issues/comments/{existing['id']}"
        status, raw, _got = http("PATCH", url, headers, payload)
        action = "updated"
    else:
        url = f"{api}/repos/{repo}/issues/{number}/comments"
        status, raw, _got = http("POST", url, headers, payload)
        action = "created"
    if status in {401, 403}:
        raise ActionError("the token cannot post a pull request comment. Grant pull-requests: write.")
    if status >= 400:
        raise ActionError(f"GitHub API {status}: {_api_message(raw) or 'could not write the comment'}")
    return action


def _placeholder(reason: str) -> dict[str, object]:
    return {
        "category": "unknown",
        "confidence": 0.2,
        "confidence_level": "low",
        "advisory": True,
        "evidence": [],
        "next_steps": [reason],
        "signals": ["run log is not available yet"],
        "alternates": [],
        "truncated": False,
    }


def run(environ: dict[str, str] | None = None, http: HttpFn | None = None) -> int:
    env = os.environ if environ is None else environ
    client = http or urllib_request
    diagnose = _load_diagnose()
    log_path = (env.get("INPUT_LOG_PATH") or "").strip()
    fixture = (env.get("INPUT_FIXTURE") or "").strip()
    run_id = (env.get("INPUT_RUN_ID") or "").strip()
    sources = [bool(log_path), bool(fixture), bool(run_id)]
    if sum(sources) > 1:
        print(
            "pass only one of log-path, fixture, or run-id",
            file=sys.stderr,
        )
        return 2
    implicit_run = False
    if not any(sources):
        run_id = (env.get("GITHUB_RUN_ID") or "").strip()
        implicit_run = True
        if not run_id:
            print(
                "pass log-path, fixture, or run-id",
                file=sys.stderr,
            )
            return 2

    token = (env.get("INPUT_TOKEN") or env.get("GITHUB_TOKEN") or "").strip()
    api = (env.get("INPUT_API_URL") or env.get("GITHUB_API_URL") or "https://api.github.com").rstrip("/")
    repo = (env.get("GITHUB_REPOSITORY") or "").strip()
    comment = as_bool(env.get("INPUT_COMMENT"))
    pull = (env.get("INPUT_PULL_REQUEST") or "").strip() or _event_pull_request(env.get("GITHUB_EVENT_PATH"))

    try:
        if log_path:
            path = Path(log_path)
            if not path.is_file():
                raise ActionError(f"log-path not found: {log_path}")
            text, truncated = diagnose.read_log_text(path)
            report = diagnose.build_report(text, log_path=path, truncated=truncated)
        elif fixture:
            directory = diagnose.REPO_ROOT / "fixtures" / "gha" / fixture
            loaded = diagnose.load_fixture(directory)
            report = diagnose.diagnose_fixture(loaded)
        else:
            try:
                text = fetch_run_log_status(
                    client, api, repo, run_id, token, diagnose.MAX_BYTES
                )
            except _NotFound as exc:
                if not implicit_run:
                    raise ActionError(str(exc)) from exc
                report = _placeholder(
                    "This job is still running, so its log archive is not available yet. "
                    "Use a workflow_run job on the completed run, or pass log-path from a saved file."
                )
                summary = render_summary(report)
                write_summary(env.get("GITHUB_STEP_SUMMARY"), summary)
                write_outputs(env.get("GITHUB_OUTPUT"), report)
                print(summary)
                return 0
            report = diagnose.build_report(text, truncated=len(text.encode("utf-8")) >= diagnose.MAX_BYTES)
    except diagnose.CorpusError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except ActionError as exc:
        print(str(exc), file=sys.stderr)
        text = str(exc).lower()
        if text.startswith("log-path not found") or text.startswith("pass "):
            return 2
        return 1

    summary = render_summary(report)
    write_summary(env.get("GITHUB_STEP_SUMMARY"), summary)
    write_outputs(env.get("GITHUB_OUTPUT"), report)
    print(summary)

    if comment and report.get("signals") == ["run log is not available yet"]:
        print("comment skipped: no run log yet", file=sys.stderr)
        return 0
    if comment:
        try:
            if not pull:
                raise ActionError(
                    "comment: true needs a pull request. Set pull-request, or run on pull_request."
                )
            if not repo:
                raise ActionError("GITHUB_REPOSITORY must look like owner/repo to post a comment.")
            action = upsert_comment(client, api, repo, pull, token, summary)
        except ActionError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"pull request comment {action}", file=sys.stderr)
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
