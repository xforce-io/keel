#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "keel"
STAGE_SKILLS = (
    "keel",
    "keel-issue",
    "keel-design",
    "keel-dev",
    "keel-verify",
    "keel-review",
    "keel-release",
)
LOOKUP = ROOT / "skills" / "keel-verify" / "lookup.py"


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
    def test_install_links_all_skills_not_agents(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            (home / ".grok").mkdir()
            (home / ".claude").mkdir()
            (home / ".agents" / "skills").mkdir(parents=True)
            result = run_keel(home, "install")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            for name in STAGE_SKILLS:
                library = home / ".local" / "share" / "agent-skills" / "library" / name
                self.assertTrue((library / "SKILL.md").is_file(), name)
                self.assertTrue(library.is_symlink(), name)
                self.assertEqual(library.resolve(), (ROOT / "skills" / name).resolve())
                grok = home / ".grok" / "skills" / name
                self.assertTrue(grok.is_symlink(), name)
                self.assertTrue((home / ".claude" / "skills" / name).is_symlink(), name)
                self.assertFalse((home / ".agents" / "skills" / name).exists(), name)
            self.assertTrue((home / ".local" / "bin" / "keel").exists())

    def test_install_skips_foreign_skill_but_installs_siblings(self) -> None:
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
            sibling = home / ".local" / "share" / "agent-skills" / "library" / "keel-design"
            self.assertTrue(sibling.is_symlink())

    def test_uninstall_removes_our_links_only(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            (home / ".grok").mkdir()
            first = run_keel(home, "install")
            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            removed = run_keel(home, "uninstall")
            self.assertEqual(removed.returncode, 0, removed.stderr + removed.stdout)
            for name in STAGE_SKILLS:
                self.assertFalse(
                    (home / ".local" / "share" / "agent-skills" / "library" / name).exists(),
                    name,
                )
                self.assertFalse((home / ".grok" / "skills" / name).exists(), name)
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
            self.assertIn("library/keel:", ok.stdout)
            self.assertIn("library/keel-design:", ok.stdout)
            self.assertIn("library/keel-verify:", ok.stdout)
            self.assertNotIn("library: 未安装", ok.stdout)


class KeelReviewContractTests(unittest.TestCase):
    def test_rework_path_requires_keel_verify(self) -> None:
        text = (ROOT / "skills" / "keel-review" / "SKILL.md").read_text(encoding="utf-8")
        start = text.index("修复由实现代理")
        chunk = text[start : start + 500]
        self.assertIn("keel-verify", chunk)
        self.assertIn("CHANGES_REQUESTED", chunk)
        self.assertIn("keel-dev` → `keel-verify", chunk)


class KeelVerifyLookupTests(unittest.TestCase):
    def _run_lookup(self, app_root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(LOOKUP), str(app_root)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_finds_grok_handbook_and_ignores_cursor(self) -> None:
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw)
            grok = app / ".grok" / "skills" / "verify-notes"
            grok.mkdir(parents=True)
            (grok / "SKILL.md").write_text("# notes\n", encoding="utf-8")
            features = grok / "features"
            features.mkdir()
            (features / "README.md").write_text("# map\n", encoding="utf-8")
            (features / "create-note.md").write_text("# create\n", encoding="utf-8")
            cursor = app / ".cursor" / "skills" / "verify-notes"
            cursor.mkdir(parents=True)
            (cursor / "SKILL.md").write_text("# cursor-only\n", encoding="utf-8")
            (cursor / "features").mkdir()
            (cursor / "features" / "other.md").write_text("# other\n", encoding="utf-8")
            result = self._run_lookup(app)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "found")
            self.assertEqual(len(payload["handbooks"]), 1)
            handbook = payload["handbooks"][0]
            self.assertEqual(handbook["name"], "verify-notes")
            self.assertEqual(Path(handbook["skill_file"]).resolve(), (grok / "SKILL.md").resolve())
            self.assertEqual(handbook["feature_files"], ["create-note.md"])
            self.assertNotIn(".cursor", handbook["skill_file"])

    def test_cursor_only_handbook_is_missing(self) -> None:
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw)
            cursor = app / ".cursor" / "skills" / "verify-notes"
            cursor.mkdir(parents=True)
            (cursor / "SKILL.md").write_text("# cursor\n", encoding="utf-8")
            (cursor / "features").mkdir()
            (cursor / "features" / "create-note.md").write_text("# create\n", encoding="utf-8")
            result = self._run_lookup(app)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "missing")

    def test_grok_skill_without_features_is_missing(self) -> None:
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw)
            grok = app / ".grok" / "skills" / "verify-notes"
            grok.mkdir(parents=True)
            (grok / "SKILL.md").write_text("# notes\n", encoding="utf-8")
            result = self._run_lookup(app)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "missing")


if __name__ == "__main__":
    unittest.main()
