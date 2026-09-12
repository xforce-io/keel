#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "keel"


def run_keel(home: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["KEEL_HOME"] = str(home)
    env["KEEL_ROOT"] = str(ROOT)
    env["PATH"] = str(ROOT / "bin") + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        [sys.executable, str(CLI), "--home", str(home), "--bin-dir", str(home / ".local" / "bin"), *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


class KeelInstallTests(unittest.TestCase):
    def test_install_links_library_and_detected_hosts_not_agents(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            (home / ".grok").mkdir()
            (home / ".claude").mkdir()
            (home / ".agents" / "skills").mkdir(parents=True)
            result = run_keel(home, "install")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            library = home / ".local" / "share" / "agent-skills" / "library" / "keel"
            self.assertTrue((library / "SKILL.md").is_file())
            self.assertTrue(library.is_symlink())
            self.assertEqual(library.resolve(), (ROOT / "skills" / "keel").resolve())
            grok = home / ".grok" / "skills" / "keel"
            self.assertTrue(grok.is_symlink())
            self.assertEqual(grok.resolve(), (ROOT / "skills" / "keel").resolve())
            self.assertTrue((home / ".claude" / "skills" / "keel").is_symlink())
            self.assertFalse((home / ".agents" / "skills" / "keel").exists())
            self.assertTrue((home / ".local" / "bin" / "keel").exists())

    def test_install_skips_foreign_skill(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            dest = home / ".local" / "share" / "agent-skills" / "library" / "keel"
            dest.mkdir(parents=True)
            (dest / "SKILL.md").write_text("---\nname: other\n---\n", encoding="utf-8")
            result = run_keel(home, "install")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("skip", result.stdout)
            self.assertEqual((dest / "SKILL.md").read_text(encoding="utf-8"), "---\nname: other\n---\n")

    def test_uninstall_removes_our_links_only(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            (home / ".grok").mkdir()
            first = run_keel(home, "install")
            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            removed = run_keel(home, "uninstall")
            self.assertEqual(removed.returncode, 0, removed.stderr + removed.stdout)
            self.assertFalse(
                (home / ".local" / "share" / "agent-skills" / "library" / "keel").exists()
            )
            self.assertFalse((home / ".grok" / "skills" / "keel").exists())
            self.assertFalse((home / ".local" / "bin" / "keel").exists())

    def test_doctor_reports_missing_then_installed(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            missing = run_keel(home, "doctor")
            self.assertEqual(missing.returncode, 0, missing.stderr + missing.stdout)
            self.assertIn("未安装", missing.stdout)
            run_keel(home, "install")
            ok = run_keel(home, "doctor")
            self.assertEqual(ok.returncode, 0, ok.stderr + ok.stdout)
            self.assertIn("library:", ok.stdout)
            self.assertNotIn("library: 未安装", ok.stdout)


if __name__ == "__main__":
    unittest.main()
