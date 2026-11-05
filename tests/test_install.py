"""Installer. Uses a temp HOME and does not touch the repo skill link."""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "scripts" / "install.sh"


def run(args: list[str], home: Path, cwd: Path | None = None, path: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    if path is not None:
        env["PATH"] = path
    return subprocess.run(
        ["bash", str(INSTALL), *args],
        cwd=cwd or ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


class InstallScriptTest(unittest.TestCase):
    def test_help(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            completed = run(["--help"], Path(tmp))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--force", completed.stdout)
        self.assertIn("v0.13.0", completed.stdout)
        self.assertIn("haoranyoung09-sys/ci-diagnose", completed.stdout)

    def test_user_install_is_idempotent_and_refuses_a_real_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            project = Path(tmp) / "proj"
            home.mkdir()
            project.mkdir()
            first = run(["--user", "--cli"], home)
            self.assertEqual(first.returncode, 0, first.stderr)
            link = home / ".agents" / "skills" / "ci-doctor"
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), (ROOT / "skills" / "ci-doctor").resolve())
            wrapper = home / ".local" / "bin" / "diagnose"
            self.assertTrue(wrapper.is_file())
            self.assertIn("diagnose.py", wrapper.read_text(encoding="utf-8"))
            mode = wrapper.stat().st_mode
            self.assertTrue(mode & stat.S_IXUSR)
            again = run(["--user", "--cli"], home)
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertIn("already", again.stdout)
            placed = run(["--project"], home, cwd=project)
            self.assertEqual(placed.returncode, 0, placed.stderr)
            self.assertTrue((project / ".agents" / "skills" / "ci-doctor").is_symlink())
            blocked = Path(tmp) / "blocked"
            (blocked / ".agents" / "skills" / "ci-doctor").mkdir(parents=True)
            refused = run(["--project"], home, cwd=blocked)
            self.assertEqual(refused.returncode, 1)
            self.assertIn("--force", refused.stderr)
            self.assertTrue((blocked / ".agents" / "skills" / "ci-doctor").is_dir())

    def test_old_python_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            bindir = Path(tmp) / "bin"
            home.mkdir()
            bindir.mkdir()
            fake = bindir / "python3"
            fake.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            fake.chmod(0o755)
            completed = run(["--user"], home, path=f"{bindir}:/usr/bin:/bin")
        self.assertEqual(completed.returncode, 1)
        self.assertIn("3.9", completed.stderr)
        self.assertFalse((home / ".agents").exists())


if __name__ == "__main__":
    unittest.main()
