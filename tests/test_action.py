"""Action entrypoint. No network."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "action_entry", ROOT / "scripts" / "action_entry.py"
)
assert SPEC is not None and SPEC.loader is not None
action_entry = importlib.util.module_from_spec(SPEC)
sys.modules["action_entry"] = action_entry
SPEC.loader.exec_module(action_entry)


class BoomHttp:
    def __call__(self, method, url, headers, body=None):
        raise AssertionError(f"network used: {method} {url}")


class FakeHttp:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict, bytes | None]] = []
        self.next: list[tuple[int, bytes]] = []

    def push(self, status: int, body: bytes) -> None:
        self.next.append((status, body))

    def __call__(self, method, url, headers, body=None):
        self.calls.append((method, url, dict(headers), body))
        if not self.next:
            raise AssertionError(f"unexpected {method} {url}")
        status, payload = self.next.pop(0)
        return status, payload, {}


def _env(tmp: Path, **extra: str) -> dict[str, str]:
    base = {
        "GITHUB_STEP_SUMMARY": str(tmp / "summary.md"),
        "GITHUB_OUTPUT": str(tmp / "output.txt"),
        "GITHUB_REPOSITORY": "example-org/example-app",
        "INPUT_TOKEN": "token-must-not-leak",
        "INPUT_COMMENT": "false",
        "INPUT_LOG_PATH": "",
        "INPUT_FIXTURE": "",
        "INPUT_RUN_ID": "",
        "INPUT_PULL_REQUEST": "",
        "INPUT_API_URL": "https://api.github.com",
    }
    base.update(extra)
    return base


class ActionEntryTest(unittest.TestCase):
    def test_fixture_is_offline_and_deps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = _env(Path(tmp), INPUT_FIXTURE="npm-ci-lockfile-drift")
            code = action_entry.run(env, BoomHttp())
            summary = Path(env["GITHUB_STEP_SUMMARY"]).read_text(encoding="utf-8")
            output = Path(env["GITHUB_OUTPUT"]).read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertIn("category=deps", output)
        self.assertIn("advisory=true", output)
        self.assertIn("`deps`", summary)
        self.assertIn("Not a merge decision", summary)
        self.assertIn(action_entry.COMMENT_MARKER, summary)
        self.assertNotIn("token-must-not-leak", summary)

    def test_log_path_redacts_before_the_summary(self) -> None:
        token = "ghp_" + "EXAMPLETOKEN"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "ci.log"
            log.write_text(f"FAIL src/a.test.ts Authorization: Bearer {token}\n", encoding="utf-8")
            env = _env(root, INPUT_LOG_PATH=str(log))
            code = action_entry.run(env, BoomHttp())
            summary = (root / "summary.md").read_text(encoding="utf-8")
            output = (root / "output.txt").read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertIn("category=test", output)
        self.assertNotIn(token, summary)
        self.assertIn("[REDACTED", summary)
        self.assertNotIn("<script>", summary)

    def test_markup_in_evidence_is_escaped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "ci.log"
            log.write_text("FAIL src/<script>.test.ts\n", encoding="utf-8")
            env = _env(root, INPUT_LOG_PATH=str(log))
            code = action_entry.run(env, BoomHttp())
            summary = (root / "summary.md").read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertIn("&lt;script&gt;", summary)
        self.assertNotIn("<script>", summary)

    def test_two_sources_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = _env(
                Path(tmp),
                INPUT_FIXTURE="npm-ci-lockfile-drift",
                INPUT_RUN_ID="1",
            )
            code = action_entry.run(env, BoomHttp())
        self.assertEqual(code, 2)

    def test_missing_log_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = _env(Path(tmp), INPUT_LOG_PATH="missing.log")
            code = action_entry.run(env, BoomHttp())
        self.assertEqual(code, 2)

    def test_comment_without_a_pull_request_does_not_call_the_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = _env(
                Path(tmp),
                INPUT_FIXTURE="npm-ci-lockfile-drift",
                INPUT_COMMENT="true",
            )
            code = action_entry.run(env, BoomHttp())
        self.assertEqual(code, 1)

    def test_comment_is_created_then_updated(self) -> None:
        http = FakeHttp()
        http.push(200, b"[]")
        http.push(201, b'{"id": 9}')
        with tempfile.TemporaryDirectory() as tmp:
            env = _env(
                Path(tmp),
                INPUT_FIXTURE="npm-ci-lockfile-drift",
                INPUT_COMMENT="true",
                INPUT_PULL_REQUEST="42",
            )
            code = action_entry.run(env, http)
        self.assertEqual(code, 0)
        self.assertEqual(http.calls[1][0], "POST")
        posted = json.loads(http.calls[1][3].decode())
        self.assertIn(action_entry.COMMENT_MARKER, posted["body"])
        self.assertNotIn("token-must-not-leak", posted["body"])

        http.push(
            200,
            json.dumps([{"id": 9, "body": "old\n" + action_entry.COMMENT_MARKER}]).encode(),
        )
        http.push(200, b'{"id": 9}')
        with tempfile.TemporaryDirectory() as tmp:
            env = _env(
                Path(tmp),
                INPUT_FIXTURE="npm-test-assertion",
                INPUT_COMMENT="yes",
                INPUT_PULL_REQUEST="42",
            )
            code = action_entry.run(env, http)
        self.assertEqual(code, 0)
        self.assertEqual(http.calls[3][0], "PATCH")
        self.assertTrue(http.calls[3][1].endswith("/issues/comments/9"))

    def test_in_progress_run_is_unknown_without_a_comment(self) -> None:
        http = FakeHttp()
        http.push(404, b'{"message":"Not Found"}')
        with tempfile.TemporaryDirectory() as tmp:
            env = _env(Path(tmp), GITHUB_RUN_ID="99", INPUT_COMMENT="true", INPUT_PULL_REQUEST="7")
            code = action_entry.run(env, http)
            summary = (Path(tmp) / "summary.md").read_text(encoding="utf-8")
            output = (Path(tmp) / "output.txt").read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertEqual(len(http.calls), 1)
        self.assertIn("category=unknown", output)
        self.assertIn("still running", summary)

    def test_explicit_missing_run_fails(self) -> None:
        http = FakeHttp()
        http.push(404, b'{"message":"Not Found"}')
        with tempfile.TemporaryDirectory() as tmp:
            env = _env(Path(tmp), INPUT_RUN_ID="99")
            code = action_entry.run(env, http)
        self.assertEqual(code, 1)

    def test_zip_keeps_the_failed_job(self) -> None:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("green.txt", "suspected flake\nThe job succeeded.\n")
            archive.writestr(
                "red.txt",
                "AssertionError: expected 200 received 503\n"
                "##[error]Process completed with exit code 1.\n",
            )
        http = FakeHttp()
        http.push(200, buffer.getvalue())
        with tempfile.TemporaryDirectory() as tmp:
            env = _env(Path(tmp), INPUT_RUN_ID="55")
            code = action_entry.run(env, http)
            output = (Path(tmp) / "output.txt").read_text(encoding="utf-8")
            summary = (Path(tmp) / "summary.md").read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertIn("category=test", output)
        self.assertNotIn("suspected flake", summary)
        self.assertNotIn("token-must-not-leak", http.calls[0][1])

    def test_redirect_drops_authorization_off_host(self) -> None:
        headers = {"Authorization": "Bearer secret", "Accept": "application/json"}
        kept = action_entry.scrub_redirect(
            "https://api.github.com/repos/a/b/actions/runs/1/logs",
            "https://api.github.com/elsewhere",
            headers,
        )
        self.assertEqual(kept["Authorization"], "Bearer secret")
        dropped = action_entry.scrub_redirect(
            "https://api.github.com/repos/a/b/actions/runs/1/logs",
            "https://results.blob.core.windows.net/logs",
            headers,
        )
        self.assertNotIn("Authorization", dropped)
        self.assertEqual(dropped["Accept"], "application/json")

    def test_committed_demo_matches_the_generator(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "render_demo", ROOT / "scripts" / "render_demo.py"
        )
        assert spec is not None and spec.loader is not None
        render_demo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(render_demo)
        text, report = render_demo.load_report()
        self.assertIn("category: deps", text)
        terminal = (ROOT / "docs" / "demo-terminal.svg").read_text(encoding="utf-8")
        summary = (ROOT / "docs" / "demo-summary.svg").read_text(encoding="utf-8")
        self.assertEqual(terminal, render_demo.build_terminal_svg(text))
        self.assertEqual(summary, render_demo.build_summary_svg(report))
        self.assertIn("scripts/render_demo.py", terminal)
        self.assertIn("Not a screenshot of GitHub", summary)


if __name__ == "__main__":
    unittest.main()
