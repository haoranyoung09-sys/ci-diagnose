"""Edge cases for scripts/diagnose.py. Stdlib unittest only."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("diagnose", ROOT / "scripts" / "diagnose.py")
assert SPEC is not None and SPEC.loader is not None
diagnose = importlib.util.module_from_spec(SPEC)
sys.modules["diagnose"] = diagnose
SPEC.loader.exec_module(diagnose)

TOKEN = "ghp_" + ("a" * 36)
JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiIxMjM0NTY3ODkwIn0"
    ".dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
)
SYNTHETIC = "synthetic redacted fixture\nnot a real workflow run\n"


def run_main(argv: list[str]) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = diagnose.main(argv)
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 2
    return code, out.getvalue(), err.getvalue()


def write_fixture(root: Path, fixture_id: str, meta: dict[str, object], log: str) -> Path:
    directory = root / "gha" / fixture_id
    directory.mkdir(parents=True)
    (directory / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    (directory / "log.txt").write_text(log, encoding="utf-8")
    return directory


def valid_meta(fixture_id: str, **overrides: object) -> dict[str, object]:
    meta: dict[str, object] = {
        "id": fixture_id,
        "label": "unknown",
        "notes": "Synthetic case used only by the edge-case tests.",
        "source": "synthetic",
        "redacted": True,
        "host": "github-actions",
    }
    meta.update(overrides)
    return meta


class EmptyLogsTest(unittest.TestCase):
    def test_empty_string_is_unknown(self) -> None:
        result = diagnose.classify("")
        self.assertEqual(result.category, "unknown")
        self.assertEqual(result.confidence_level, "low")
        self.assertEqual(result.confidence, 0.2)
        self.assertEqual(result.signals, ["no taxonomy signal"])
        self.assertEqual(result.evidence, [])

    def test_whitespace_file_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "blank.log"
            path.write_text(" \n\t\n\n", encoding="utf-8")
            code, out, err = run_main([str(path)])
        self.assertEqual(code, 0, err)
        self.assertIn("category: unknown", out)
        self.assertIn("no taxonomy signal", out)
        self.assertNotIn("Traceback", err)


class LargeLogsTest(unittest.TestCase):
    def test_in_memory_log_is_capped(self) -> None:
        text = "FAIL src/a.test.ts\n" + ("noise line\n" * 200_000)
        self.assertGreater(len(text.encode()), diagnose.MAX_BYTES)
        result = diagnose.classify(text)
        self.assertTrue(result.truncated)
        self.assertEqual(result.category, "test")
        self.assertLessEqual(len(result.evidence), diagnose.MAX_EVIDENCE)
        self.assertEqual(result.scores["test"], 6)

    def test_file_reader_stops_before_the_tail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "huge.log"
            with path.open("wb") as handle:
                handle.write(b"FAIL src/a.test.ts\n")
                handle.write(b"n\n" * 1_200_000)
                handle.write(b"TAILMARKER " + TOKEN.encode() + b"\n")
            self.assertGreater(path.stat().st_size, diagnose.MAX_BYTES)
            text, truncated = diagnose.read_log_text(path)
            code, out, err = run_main([str(path), "--format", "json"])
        self.assertTrue(truncated)
        self.assertNotIn("TAILMARKER", text)
        self.assertNotIn(TOKEN, text)
        self.assertLessEqual(len(text.encode()), diagnose.MAX_BYTES)
        self.assertEqual(code, 0, err)
        report = json.loads(out)
        self.assertTrue(report["truncated"])
        self.assertEqual(report["category"], "test")
        self.assertNotIn(TOKEN, out)
        self.assertNotIn("TAILMARKER", out)

    def test_runner_kills_a_huge_stdout(self) -> None:
        code = (
            "import sys\n"
            "sys.stdout.buffer.write(b'FAIL src/a.test.ts\\n')\n"
            "sys.stdout.buffer.write(b'n\\n' * 1200000)\n"
            "sys.stdout.buffer.write(b'TAILMARKER\\n')\n"
        )
        result = diagnose.default_runner([sys.executable, "-c", code])
        self.assertTrue(result.truncated)
        self.assertIn("FAIL src/a.test.ts", result.stdout)
        self.assertNotIn("TAILMARKER", result.stdout)
        self.assertLessEqual(len(result.stdout.encode()), diagnose.MAX_BYTES)


class RedactionTest(unittest.TestCase):
    def test_secret_shapes_are_masked(self) -> None:
        raw = (
            f"FAIL src/a.test.ts Authorization: Bearer {TOKEN} "
            f"password=example-value-not-real token={JWT}\n"
        )
        result = diagnose.classify(raw)
        blob = json.dumps(result.evidence)
        self.assertEqual(result.category, "test")
        self.assertNotIn(TOKEN, blob)
        self.assertNotIn(JWT, blob)
        self.assertNotIn("example-value-not-real", blob)
        self.assertIn("[REDACTED", blob)
        only = diagnose.classify(f"Authorization: Bearer {TOKEN}\n")
        only_blob = json.dumps(only.evidence)
        self.assertNotIn(TOKEN, only_blob)
        self.assertIn("[REDACTED", only_blob)
        again = diagnose.redact(diagnose.redact(raw))
        self.assertEqual(again, diagnose.redact(raw))

    def test_permission_scope_and_env_names_stay(self) -> None:
        scope = "The job was not granted id-token: write."
        self.assertEqual(diagnose.redact(scope), scope)
        self.assertIn(
            "NODE_AUTH_TOKEN is empty",
            diagnose.redact("NODE_AUTH_TOKEN is empty"),
        )
        self.assertEqual(
            diagnose.redact("x-api-key: write"),
            "x-api-key: write",
        )

    def test_more_secret_shapes_are_masked(self) -> None:
        samples = {
            "ASIA" + ("0" * 16): "[REDACTED_AWS_ACCESS_KEY]",
            "sk_live_" + ("a" * 24): "[REDACTED_API_KEY]",
            "AIza" + ("b" * 35): "[REDACTED_API_KEY]",
            "npm_" + ("c" * 36): "[REDACTED_NPM_TOKEN]",
            "pypi-" + ("d" * 32): "[REDACTED_PYPI_TOKEN]",
            "dckr_pat_" + ("e" * 32): "[REDACTED_DOCKER_TOKEN]",
            "hf_" + ("f" * 32): "[REDACTED_HF_TOKEN]",
        }
        slack = (
            "https://hooks.slack.com/services/"
            + "T" + ("0" * 8)
            + "/B" + ("0" * 8)
            + "/" + ("X" * 24)
        )
        samples[slack] = "[REDACTED_SLACK_WEBHOOK]"
        for secret, marker in samples.items():
            cleaned = diagnose.redact("value " + secret + " tail")
            self.assertNotIn(secret, cleaned)
            self.assertIn(marker, cleaned)
            self.assertEqual(diagnose.redact(cleaned), cleaned)
        self.assertNotIn(
            "example-client-secret-value",
            diagnose.redact("client_secret=example-client-secret-value"),
        )
        self.assertNotIn(
            "example-header-secret",
            diagnose.redact("x-api-key: example-header-secret"),
        )

    def test_loader_rejects_a_secret_without_echoing_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_fixture(
                root,
                "leaky-log",
                valid_meta("leaky-log"),
                SYNTHETIC + f"Authorization: Bearer {TOKEN}\n",
            )
            with self.assertRaises(diagnose.CorpusError) as ctx:
                diagnose.load_fixtures(root / "gha")
        message = str(ctx.exception)
        self.assertNotIn(TOKEN, message)
        self.assertIn("forbidden", message)

    def test_loader_rejects_an_oversized_fixture_before_reading_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = write_fixture(
                root,
                "too-big",
                valid_meta("too-big"),
                SYNTHETIC,
            )
            log_path = directory / "log.txt"
            with log_path.open("ab") as handle:
                handle.truncate(diagnose.MAX_BYTES + 1)
            with self.assertRaises(diagnose.CorpusError) as ctx:
                diagnose.load_fixture(directory)
        self.assertNotIn(TOKEN, str(ctx.exception))
        self.assertIn("larger than", str(ctx.exception))


class FixtureMetadataTest(unittest.TestCase):
    def test_missing_directory(self) -> None:
        with self.assertRaises(diagnose.CorpusError) as ctx:
            diagnose.load_fixtures(Path("/tmp/ci-doctor-missing-fixtures-dir"))
        self.assertIn("not found", str(ctx.exception))

    def test_bad_meta_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "gha" / "bad-meta"
            root.mkdir(parents=True)
            (root / "log.txt").write_text(SYNTHETIC + "exit 1\n", encoding="utf-8")
            (root / "meta.json").write_text("{", encoding="utf-8")
            with self.assertRaises(diagnose.CorpusError) as ctx:
                diagnose.load_fixture(root)
            self.assertIn("not valid JSON", str(ctx.exception))

            (root / "meta.json").write_text(
                json.dumps(valid_meta("bad-meta", redacted=False)),
                encoding="utf-8",
            )
            with self.assertRaises(diagnose.CorpusError) as ctx:
                diagnose.load_fixture(root)
            self.assertIn("redacted must be true", str(ctx.exception))

            (root / "meta.json").write_text(
                json.dumps(valid_meta("other-id")),
                encoding="utf-8",
            )
            with self.assertRaises(diagnose.CorpusError) as ctx:
                diagnose.load_fixture(root)
            self.assertIn("does not match", str(ctx.exception))

            (root / "meta.json").write_text(
                json.dumps(valid_meta("bad-meta", notes="too short")),
                encoding="utf-8",
            )
            with self.assertRaises(diagnose.CorpusError) as ctx:
                diagnose.load_fixture(root)
            self.assertIn("notes", str(ctx.exception))

    def test_whitespace_fixture_log_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = write_fixture(
                Path(tmp),
                "blank-fixture",
                valid_meta("blank-fixture"),
                " \n\t\n",
            )
            with self.assertRaises(diagnose.CorpusError) as ctx:
                diagnose.load_fixture(directory)
        self.assertIn("empty", str(ctx.exception))


class AmbiguousSignalsTest(unittest.TestCase):
    def test_equal_scores_become_unknown(self) -> None:
        text = "does not have permission\nNODE_AUTH_TOKEN is empty\n"
        result = diagnose.classify(text)
        self.assertEqual(result.category, "unknown")
        self.assertEqual(result.confidence, 0.42)
        self.assertEqual(result.confidence_level, "low")
        self.assertEqual(result.alternates, ["env", "permissions"])
        self.assertTrue(any(signal.startswith("tie between") for signal in result.signals))

    def test_close_call_caps_confidence(self) -> None:
        clear = diagnose.classify("AssertionError: expected 200\n")
        close = diagnose.classify(
            "AssertionError: expected 200\nThe runner has received a shutdown signal\n"
        )
        self.assertEqual(close.category, "test")
        self.assertEqual(close.confidence, 0.64)
        self.assertIn("infra", close.alternates)
        self.assertLess(close.confidence, clear.confidence)
        self.assertEqual(clear.confidence_level, "high")
        self.assertEqual(close.confidence_level, "medium")

    def test_truncated_tail_is_not_scored(self) -> None:
        text = ("noise line\n" * 200_000) + "FAIL src/hidden.test.ts\n"
        self.assertGreater(len(text.encode()), diagnose.MAX_BYTES)
        result = diagnose.classify(text)
        self.assertTrue(result.truncated)
        self.assertEqual(result.category, "unknown")
        self.assertNotIn("FAIL path line", result.signals)

    def test_green_job_cannot_outrank_the_failed_step(self) -> None:
        text = (
            "lint\tSetup\t2026-10-26T01:14:22.1038427Z suspected flake\n"
            "lint\tSetup\t2026-10-26T01:14:22.2038427Z The job succeeded.\n"
            "build\tTest\t2026-10-26T01:14:23.1038427Z AssertionError: expected 200\n"
            "build\tTest\t2026-10-26T01:14:23.2038427Z "
            "##[error]Process completed with exit code 1.\n"
        )
        result = diagnose.classify(text)
        self.assertEqual(result.category, "test")
        self.assertNotIn("suspected flake", result.signals)
        self.assertNotIn("flake", result.alternates)


class GhPathsTest(unittest.TestCase):
    def test_missing_binary_has_no_traceback(self) -> None:
        with self.assertRaises(diagnose.GhError) as ctx:
            diagnose.default_runner(["/nonexistent/gh-not-installed"])
        self.assertIn("not installed", str(ctx.exception))
        self.assertNotIn("Traceback", str(ctx.exception))

        with self.assertRaises(diagnose.GhError) as ctx:
            diagnose.ensure_gh_ready(
                lambda _argv: diagnose.CommandResult(0, "", ""),
                lambda _name: None,
            )
        self.assertIn("not installed", str(ctx.exception))

    def test_logged_out_does_not_fetch_or_leak_stderr(self) -> None:
        calls: list[list[str]] = []

        def unauth(argv: list[str]) -> diagnose.CommandResult:
            calls.append(argv)
            return diagnose.CommandResult(1, "", "You are not logged into any GitHub hosts")

        request = diagnose.parse_run_request(None, "123456789", "example-org/example-app")
        with self.assertRaises(diagnose.GhError) as ctx:
            diagnose.fetch_failed_log(
                request,
                runner=unauth,
                which=lambda _name: "/usr/bin/gh",
            )
        message = str(ctx.exception)
        self.assertIn("not logged in", message)
        self.assertNotIn("not logged into", message)
        self.assertNotIn("Traceback", message)
        self.assertEqual(calls, [["gh", "auth", "status"]])

    def test_truncated_nonzero_fetch_is_kept(self) -> None:
        def runner(argv: list[str]) -> diagnose.CommandResult:
            if argv[:3] == ["gh", "auth", "status"]:
                return diagnose.CommandResult(0, "", "")
            return diagnose.CommandResult(-9, "FAIL src/a.test.ts\nExpected: 1\n", "", True)

        request = diagnose.parse_run_request(None, "55", "example-org/example-app")
        fetched = diagnose.fetch_failed_log(
            request,
            runner=runner,
            which=lambda _name: "/usr/bin/gh",
        )
        report = diagnose.build_report(fetched.text, truncated=fetched.truncated)
        self.assertTrue(fetched.truncated)
        self.assertTrue(report["truncated"])
        self.assertEqual(report["category"], "test")

    def test_malformed_url_and_missing_repo(self) -> None:
        code, _out, err = run_main(
            ["--run-url", "https://example.com/not-a-run", "--dry-run"]
        )
        self.assertEqual(code, 2)
        self.assertIn("Could not read", err)
        self.assertNotIn("Traceback", err)

        code, _out, err = run_main(["--run-id", "123456789"])
        self.assertEqual(code, 2)
        self.assertIn("--repo", err)
        self.assertNotIn("Traceback", err)

        code, _out, err = run_main(["--run-id", "abc", "--repo", "example-org/example-app"])
        self.assertEqual(code, 2)
        self.assertIn("numeric", err)

        with self.assertRaises(diagnose.GhError):
            diagnose.parse_run_request("not a url", None, None)

    def test_dry_run_and_self_check(self) -> None:
        url = "https://github.com/example-org/example-app/actions/runs/123456789/job/42"
        code, out, err = run_main(["--run-url", url, "--dry-run"])
        self.assertEqual(code, 0, err)
        self.assertIn(
            "gh run view 123456789 --repo example-org/example-app --log-failed",
            out,
        )
        self.assertNotIn("--job", out)
        self.assertNotIn("Traceback", err)

        code, out, err = run_main(["--self-check"])
        self.assertEqual(code, 0, err)
        self.assertIn("self-check: ok", err)
        self.assertEqual(out, "")

        code, _out, err = run_main(["--dry-run"])
        self.assertEqual(code, 2)
        self.assertIn("--dry-run", err)


class EncodingTest(unittest.TestCase):
    def test_non_ascii_lines(self) -> None:
        result = diagnose.classify("FAIL src/健康.test.ts 期望值与实际值不一致\n")
        self.assertEqual(result.category, "test")
        blob = json.dumps(result.evidence, ensure_ascii=False)
        self.assertIn("健康", blob)
        self.assertIn("期望值与实际值不一致", blob)
        unknown = diagnose.classify("没有匹配到分类\n")
        self.assertEqual(unknown.category, "unknown")
        unknown_blob = json.dumps(unknown.evidence, ensure_ascii=False)
        self.assertIn("没有匹配到分类", unknown_blob)

    def test_invalid_utf8_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "odd.log"
            path.write_bytes(b"FAIL src/a.test.ts\n\xff\xfe not utf8\n")
            text, truncated = diagnose.read_log_text(path)
            code, out, err = run_main([str(path)])
        self.assertFalse(truncated)
        self.assertIn("FAIL src/a.test.ts", text)
        self.assertIn("\ufffd", text)
        self.assertEqual(diagnose.classify(text).category, "test")
        self.assertEqual(code, 0, err)
        self.assertIn("category: test", out)


class CorpusFixturesTest(unittest.TestCase):
    def test_published_fixtures_still_match(self) -> None:
        fixtures = diagnose.load_fixtures(ROOT / "fixtures" / "gha")
        self.assertGreaterEqual(len(fixtures), 102)
        for fixture in fixtures:
            report = diagnose.diagnose_fixture(fixture)
            self.assertTrue(
                report["label_match"],
                f"{report['id']} classified as {report['category']}",
            )

    def test_canceled_and_bare_unknowns(self) -> None:
        for fixture_id in ("canceled-step-unknown", "bare-exit-unknown"):
            fixture = diagnose.load_fixture(ROOT / "fixtures" / "gha" / fixture_id)
            report = diagnose.diagnose_fixture(fixture)
            self.assertEqual(report["category"], "unknown")
            self.assertEqual(report["confidence_level"], "low")
            self.assertTrue(report["label_match"])
            self.assertLess(float(report["confidence"]), 0.6)

    def test_near_miss_fixtures_stay_label_blind(self) -> None:
        expected = {
            "timeout-and-assertion-unknown": ("unknown", ["flake", "test"], 0.42),
            "empty-token-and-permission-unknown": ("unknown", ["env", "permissions"], 0.42),
            "force-push-refusal-only-unknown": ("unknown", [], None),
            "cache-eacces-unknown": ("unknown", [], None),
            "bare-http-403": ("permissions", [], None),
            "phpunit-assert-failed": ("test", [], None),
            "poetry-lock-and-assertion-unknown": ("unknown", ["deps", "test"], 0.42),
            "oom-and-permission-unknown": ("unknown", ["infra", "permissions"], 0.42),
            "oidc-role-and-empty-arn-unknown": ("unknown", ["env", "permissions"], 0.42),
            "checkout-tls-verify-flake": ("flake", [], None),
            "checkout-tls-and-assertion-unknown": ("unknown", ["flake", "test"], 0.42),
            "external-dataset-host-flake": ("flake", [], None),
            "dataset-and-assertion-unknown": ("unknown", ["flake", "test"], 0.42),
            "mcr-pull-egress-blocked": ("infra", [], None),
            "ghcr-pull-io-timeout": ("infra", [], None),
            "egress-and-permission-unknown": ("unknown", ["infra", "permissions"], 0.42),
            "checkout-tls-hook-cascade-flake": ("flake", [], None),
            "checkout-hook-only-unknown": ("unknown", [], None),
            "multi-job-one-step-failed": ("test", [], None),
            "multi-job-green-noise-unknown": ("unknown", [], None),
            "registry-pull-auth-denied": ("permissions", [], None),
            "registry-auth-and-egress-unknown": ("unknown", ["infra", "permissions"], 0.42),
            "service-healthcheck-timeout-flake": ("flake", [], None),
            "helm-healthcheck-timeout-flake": ("flake", [], None),
            "healthcheck-and-assertion-unknown": ("unknown", ["flake", "test"], 0.42),
            "external-host-chronic-flake": ("flake", [], None),
            "bundler-lockfile-out-of-date": ("deps", [], None),
            "go-sum-checksum-mismatch": ("deps", [], None),
            "cargo-lock-needs-update": ("deps", [], None),
            "dns-name-resolution-infra": ("infra", [], None),
            "actions-cache-restore-corrupt": ("infra", [], None),
            "cache-eacces-and-lockfile-unknown": ("unknown", ["deps", "infra"], 0.42),
            "registry-rate-and-auth-unknown": ("unknown", ["flake", "permissions"], 0.42),
            "docker-pull-rate-limit-flake": ("flake", [], None),
            "kernel-oom-killed-infra": ("infra", [], None),
            "runner-arch-mismatch-infra": ("infra", [], None),
            "node-engine-mismatch-env": ("env", [], None),
        }
        for fixture_id, (category, alternates, confidence) in expected.items():
            fixture = diagnose.load_fixture(ROOT / "fixtures" / "gha" / fixture_id)
            report = diagnose.diagnose_fixture(fixture)
            self.assertEqual(report["category"], category, fixture_id)
            self.assertEqual(report["alternates"], alternates, fixture_id)
            self.assertTrue(report["label_match"], fixture_id)
            if confidence is not None:
                self.assertEqual(report["confidence"], confidence, fixture_id)
            else:
                self.assertLess(float(report["confidence"]), 0.8, fixture_id)
        phpunit = diagnose.diagnose_fixture(
            diagnose.load_fixture(ROOT / "fixtures" / "gha" / "phpunit-assert-failed")
        )
        self.assertIn("PHPUnit assertion failed", phpunit["signals"])
        self.assertNotIn("pytest FAILED line", phpunit["signals"])
        checkout = diagnose.diagnose_fixture(
            diagnose.load_fixture(ROOT / "fixtures" / "gha" / "checkout-tls-verify-flake")
        )
        self.assertEqual(
            checkout["signals"],
            ["checkout TLS certificate verification failed"],
        )
        dataset = diagnose.diagnose_fixture(
            diagnose.load_fixture(ROOT / "fixtures" / "gha" / "external-dataset-host-flake")
        )
        self.assertEqual(
            dataset["signals"],
            ["external dataset or host dependency failed"],
        )
        registry = diagnose.diagnose_fixture(
            diagnose.load_fixture(ROOT / "fixtures" / "gha" / "mcr-pull-egress-blocked")
        )
        self.assertEqual(registry["signals"], ["registry pull or egress blocked"])
        rate_limit = diagnose.diagnose_fixture(
            diagnose.load_fixture(ROOT / "fixtures" / "gha" / "docker-rate-limit-flake")
        )
        self.assertNotIn("registry pull or egress blocked", rate_limit["signals"])
        cascade = diagnose.diagnose_fixture(
            diagnose.load_fixture(
                ROOT / "fixtures" / "gha" / "checkout-tls-hook-cascade-flake"
            )
        )
        self.assertIn(
            "downstream hook did not run after checkout", cascade["signals"]
        )
        self.assertNotIn("test", cascade["alternates"])
        green = diagnose.diagnose_fixture(
            diagnose.load_fixture(
                ROOT / "fixtures" / "gha" / "multi-job-green-noise-unknown"
            )
        )
        self.assertNotIn("suspected flake", green["signals"])
        auth = diagnose.diagnose_fixture(
            diagnose.load_fixture(ROOT / "fixtures" / "gha" / "registry-pull-auth-denied")
        )
        self.assertNotIn("registry pull or egress blocked", auth["signals"])
        health = diagnose.diagnose_fixture(
            diagnose.load_fixture(
                ROOT / "fixtures" / "gha" / "service-healthcheck-timeout-flake"
            )
        )
        self.assertEqual(health["signals"], ["service health check timed out"])
        chronic = diagnose.diagnose_fixture(
            diagnose.load_fixture(ROOT / "fixtures" / "gha" / "external-host-chronic-flake")
        )
        self.assertNotIn("flake or flaky wording", chronic["signals"])
        dns = diagnose.diagnose_fixture(
            diagnose.load_fixture(ROOT / "fixtures" / "gha" / "dns-name-resolution-infra")
        )
        self.assertEqual(dns["signals"], ["DNS name resolution failed"])
        self.assertNotIn("permissions", dns["alternates"])
        cache = diagnose.diagnose_fixture(
            diagnose.load_fixture(
                ROOT / "fixtures" / "gha" / "actions-cache-restore-corrupt"
            )
        )
        self.assertEqual(cache["signals"], ["actions cache restore failed"])
        self.assertNotIn("deps", cache["alternates"])
        compose = diagnose.diagnose_fixture(
            diagnose.load_fixture(ROOT / "fixtures" / "gha" / "compose-db-url-unset")
        )
        self.assertEqual(compose["category"], "env")
        self.assertNotIn("service health check timed out", compose["signals"])
        layer = diagnose.classify(
            "failed to compute cache key: layer does not exist\n"
        )
        self.assertEqual(layer.category, "infra")
        self.assertNotIn("pytest FAILED line", layer.signals)
        ignored = diagnose.diagnose_fixture(
            diagnose.load_fixture(
                ROOT / "fixtures" / "gha" / "continue-on-error-lockfile-deps"
            )
        )
        self.assertNotIn("suspected flake", ignored["signals"])
        rate = diagnose.diagnose_fixture(
            diagnose.load_fixture(ROOT / "fixtures" / "gha" / "docker-pull-rate-limit-flake")
        )
        self.assertEqual(rate["signals"], ["registry pull rate limit"])
        maven = diagnose.diagnose_fixture(
            diagnose.load_fixture(
                ROOT / "fixtures" / "gha" / "maven-dependencies-unresolved-deps"
            )
        )
        self.assertEqual(
            maven["signals"], ["Maven could not resolve project dependencies"]
        )
        cargo_net = diagnose.diagnose_fixture(
            diagnose.load_fixture(ROOT / "fixtures" / "gha" / "cargo-registry-network-flake")
        )
        self.assertEqual(cargo_net["category"], "flake")
        self.assertNotIn("Cargo lockfile could not select a version", cargo_net["signals"])
        compile_fail = diagnose.diagnose_fixture(
            diagnose.load_fixture(ROOT / "fixtures" / "gha" / "cargo-type-mismatch-test")
        )
        self.assertIn("compiler rejected the crate", compile_fail["signals"])
        self.assertEqual(compile_fail["category"], "test")

    def test_npm_signal_order_matches_the_readme(self) -> None:
        fixture = diagnose.load_fixture(ROOT / "fixtures" / "gha" / "npm-test-assertion")
        report = diagnose.diagnose_fixture(fixture)
        self.assertEqual(
            report["signals"],
            [
                "expect(received) mismatch",
                "FAIL path line",
                "expected vs received",
                "Jest tests failed summary",
                "test suite failed summary",
            ],
        )


if __name__ == "__main__":
    unittest.main()
