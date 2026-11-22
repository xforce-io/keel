#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "keel"
STAGE_SKILLS = (
    "cat-mode",
    "keel",
    "keel-issue",
    "keel-how",
    "keel-design",
    "keel-dev",
    "keel-verify",
    "keel-review",
    "keel-release",
    "keel-reflect",
    "keel-ticket",
    "keel-start",
    "keel-sync",
    "keel-verify-maintain",
)
LOOKUP = ROOT / "skills" / "keel-verify" / "lookup.py"


FAKE_LOCAL_SKILL = """#!/bin/sh
case "$1" in
  refresh) echo refreshed ;;
  *) exit 2 ;;
esac
"""


def fake_tools_dir(home: Path) -> Path:
    tools = home / "fake-tools"
    tools.mkdir(exist_ok=True)
    exe = tools / "local-skill"
    if not exe.exists():
        exe.write_text(FAKE_LOCAL_SKILL, encoding="utf-8")
        exe.chmod(0o755)
    return tools


def run_keel(
    home: Path,
    *args: str,
    cli: Path = CLI,
    root: Path | None = ROOT,
    with_local_skill: bool = False,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["KEEL_HOME"] = str(home)
    env.pop("KEEL_ROOT", None)
    if root is not None:
        env["KEEL_ROOT"] = str(root)
    path = [str(ROOT / "bin"), env.get("PATH", "")]
    if with_local_skill:
        path.insert(0, str(fake_tools_dir(home)))
    else:
        path = [str(home / "empty-path")]
    env["PATH"] = os.pathsep.join(path)
    return subprocess.run(
        [sys.executable, str(cli), "--home", str(home), "--bin-dir", str(home / ".local" / "bin"), *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def copy_checkout(dest: Path) -> Path:
    import shutil

    shutil.copytree(ROOT, dest, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    return dest


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
            agent = home / ".grok" / "agents" / "reviewer.md"
            self.assertTrue(agent.is_symlink())
            self.assertEqual(agent.resolve(), (ROOT / "agents" / "reviewer.md").resolve())

    def test_install_skips_foreign_skill_but_installs_siblings(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            dest = home / ".local" / "share" / "agent-skills" / "library" / "keel"
            dest.mkdir(parents=True)
            (dest / "SKILL.md").write_text("---\nname: other\n---\n", encoding="utf-8")
            result = run_keel(home, "install")
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            self.assertIn("library/keel: skip", result.stdout)
            self.assertIn("1 项未完成", result.stderr)
            self.assertEqual((dest / "SKILL.md").read_text(encoding="utf-8"), "---\nname: other\n---\n")
            sibling = home / ".local" / "share" / "agent-skills" / "library" / "keel-design"
            self.assertTrue(sibling.is_symlink())
            removed = run_keel(home, "uninstall")
            self.assertIn("library/keel: skip-foreign", removed.stdout)
            self.assertTrue((dest / "SKILL.md").is_file())

    def test_install_reclaims_dangling_symlink(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            library = home / ".local" / "share" / "agent-skills" / "library"
            library.mkdir(parents=True)
            (library / "keel").symlink_to(home / "gone" / "skills" / "keel")
            result = run_keel(home, "install")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual((library / "keel").resolve(), (ROOT / "skills" / "keel").resolve())

    def test_install_replaces_link_into_moved_checkout(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            old = copy_checkout(home / "old-keel")
            first = run_keel(home, "install", cli=old / "bin" / "keel", root=old)
            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            library = home / ".local" / "share" / "agent-skills" / "library" / "keel"
            self.assertEqual(library.resolve(), (old / "skills" / "keel").resolve())
            second = run_keel(home, "install")
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
            self.assertEqual(library.resolve(), (ROOT / "skills" / "keel").resolve())
            self.assertEqual((home / ".local" / "bin" / "keel").resolve(), CLI.resolve())

    def test_install_fails_fast_outside_checkout_without_state(self) -> None:
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            stray = home / "stray-keel"
            stray.mkdir()
            shutil.copy2(CLI, stray / "keel")
            result = run_keel(home, "doctor", cli=stray / "keel", root=None)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            self.assertIn("not inside a keel checkout", result.stdout + result.stderr)


class KeelCopyModeTests(unittest.TestCase):
    def _install_copy(self, home: Path, checkout: Path) -> subprocess.CompletedProcess[str]:
        return run_keel(home, "install", "--copy", cli=checkout / "bin" / "keel", root=checkout)

    def test_copy_upgrade_refreshes_and_uninstall_removes(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            (home / ".grok").mkdir()
            checkout = copy_checkout(home / "checkout")
            first = self._install_copy(home, checkout)
            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            library = home / ".local" / "share" / "agent-skills" / "library" / "keel-verify"
            self.assertFalse(library.is_symlink())
            self.assertTrue((library / "lookup.py").is_file())
            state = json.loads((home / ".config" / "keel" / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(state["root"]), checkout.resolve())
            self.assertIn(str(library.resolve()), state["copies"])

            for relative in ("skills/keel-verify/SKILL.md", "skills/keel-verify/lookup.py", "agents/reviewer.md"):
                with (checkout / relative).open("a", encoding="utf-8") as handle:
                    handle.write("\n# upgraded\n")
            second = self._install_copy(home, checkout)
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
            self.assertIn("library/keel-verify: copy", second.stdout)
            self.assertIn("# upgraded", (library / "SKILL.md").read_text(encoding="utf-8"))
            self.assertIn("# upgraded", (library / "lookup.py").read_text(encoding="utf-8"))
            self.assertIn(
                "# upgraded",
                (home / ".grok" / "agents" / "reviewer.md").read_text(encoding="utf-8"),
            )

            removed = run_keel(home, "uninstall", cli=checkout / "bin" / "keel", root=checkout)
            self.assertEqual(removed.returncode, 0, removed.stderr + removed.stdout)
            self.assertIn("library/keel-verify: removed", removed.stdout)
            self.assertFalse(library.exists())
            self.assertFalse((home / ".grok" / "agents" / "reviewer.md").exists())
            self.assertFalse((home / ".local" / "bin" / "keel").exists())
            self.assertFalse((home / ".config" / "keel" / "state.json").exists())

    def test_copied_cli_finds_checkout_from_state(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            checkout = copy_checkout(home / "checkout")
            first = self._install_copy(home, checkout)
            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            installed_cli = home / ".local" / "bin" / "keel"
            self.assertFalse(installed_cli.is_symlink())
            doctor = run_keel(home, "doctor", cli=installed_cli, root=None)
            self.assertEqual(doctor.returncode, 0, doctor.stderr + doctor.stdout)
            self.assertIn(f"root: {checkout.resolve()}", doctor.stdout)
            again = run_keel(home, "install", "--copy", cli=installed_cli, root=None)
            self.assertEqual(again.returncode, 0, again.stderr + again.stdout)

            import shutil

            shutil.rmtree(checkout)
            gone = run_keel(home, "doctor", cli=installed_cli, root=None)
            self.assertEqual(gone.returncode, 1, gone.stderr + gone.stdout)
            self.assertIn("is gone", gone.stdout + gone.stderr)

    def test_symlink_then_copy_then_symlink_swaps_cleanly(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            library = home / ".local" / "share" / "agent-skills" / "library" / "keel"
            self.assertEqual(run_keel(home, "install").returncode, 0)
            self.assertTrue(library.is_symlink())
            self.assertEqual(run_keel(home, "install", "--copy").returncode, 0)
            self.assertFalse(library.is_symlink())
            self.assertTrue((library / "SKILL.md").is_file())
            self.assertEqual(run_keel(home, "install").returncode, 0)
            self.assertTrue(library.is_symlink())
            state = json.loads((home / ".config" / "keel" / "state.json").read_text(encoding="utf-8"))
            self.assertNotIn(str(library), state["copies"])

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
            self.assertFalse((home / ".grok" / "agents" / "reviewer.md").exists())
            self.assertFalse((home / ".local" / "bin" / "keel").exists())

    def test_doctor_reports_missing_then_installed(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            missing = run_keel(home, "doctor")
            self.assertEqual(missing.returncode, 1, missing.stderr + missing.stdout)
            self.assertIn("未安装", missing.stdout)
            self.assertIn("项需要处理", missing.stderr)
            run_keel(home, "install")
            ok = run_keel(home, "doctor")
            self.assertEqual(ok.returncode, 0, ok.stderr + ok.stdout)
            self.assertIn("library/keel: symlink", ok.stdout)
            self.assertIn("library/keel-design:", ok.stdout)
            self.assertRegex(ok.stdout, r"(?m)^skills:.*\bkeel-sync\b")
            self.assertIn("library/keel-verify:", ok.stdout)
            self.assertIn("library/keel-how:", ok.stdout)
            self.assertIn("library/keel-reflect:", ok.stdout)
            self.assertNotIn("code-review: ok", ok.stdout)
            self.assertNotIn("未安装", ok.stdout)

    def test_install_doctor_uninstall_without_external_review_tools(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            installed = run_keel(home, "install")
            self.assertEqual(installed.returncode, 0, installed.stderr + installed.stdout)
            state = home / ".config/keel/state.json"
            before = state.read_bytes()
            result = run_keel(home, "doctor", with_local_skill=False)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertNotIn("local-skill", result.stdout)
            self.assertNotIn("code-review", result.stdout)
            self.assertEqual(state.read_bytes(), before)
            removed = run_keel(home, "uninstall")
            self.assertEqual(removed.returncode, 0, removed.stderr + removed.stdout)
            self.assertFalse(state.exists())

    def test_doctor_does_not_invoke_optional_locator(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            installed = run_keel(home, "install", with_local_skill=True)
            self.assertEqual(installed.returncode, 0, installed.stderr + installed.stdout)
            self.assertIn("refreshed", installed.stdout)
            marker = home / "locator-called"
            # Any invocation would create the marker and fail, including a bogus find result.
            (fake_tools_dir(home) / "local-skill").write_text(
                f'#!/bin/sh\ntouch "{marker}"\nexit 1\n', encoding="utf-8"
            )
            result = run_keel(home, "doctor", with_local_skill=True)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertFalse(marker.exists())


class KeelReviewerAgentTests(unittest.TestCase):
    def test_install_skips_foreign_reviewer_agent(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            dest = home / ".grok" / "agents" / "reviewer.md"
            dest.parent.mkdir(parents=True)
            dest.write_text(
                "---\nname: reviewer\nmodel: grok-4.5\npermission_mode: plan\n---\nlocal\n",
                encoding="utf-8",
            )
            result = run_keel(home, "install")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("grok-agent/reviewer: skip", result.stdout)
            self.assertIn("model: grok-4.5", dest.read_text(encoding="utf-8"))
            doctor = run_keel(home, "doctor")
            self.assertIn("本机已有", doctor.stdout)
            self.assertIn("model=grok-4.5", doctor.stdout)

    def test_shipped_agent_is_plan_without_model_slug(self) -> None:
        text = (ROOT / "agents" / "reviewer.md").read_text(encoding="utf-8")
        end = text.find("\n---", 3)
        front = text[3:end]
        self.assertIn("permission_mode: plan", front)
        self.assertNotIn("model:", front)

    def test_doctor_lists_reviewer_after_install(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            (home / ".grok").mkdir()
            missing = run_keel(home, "doctor")
            self.assertIn("grok-agent/reviewer: 未安装", missing.stdout)
            run_keel(home, "install")
            ok = run_keel(home, "doctor")
            self.assertIn("grok-agent/reviewer: symlink", ok.stdout)
            self.assertIn("未绑模型", ok.stdout)


class KeelVerifyLookupTests(unittest.TestCase):
    def _run_lookup(self, app_root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(LOOKUP), str(app_root)],
            check=False,
            capture_output=True,
            text=True,
        )

    @staticmethod
    def _write_handbook(root: Path, name: str, feature: str = "create-note.md") -> Path:
        handbook = root / name
        features = handbook / "features"
        features.mkdir(parents=True)
        (handbook / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
        (features / "README.md").write_text("# map\n", encoding="utf-8")
        (features / feature).write_text("# feature\n", encoding="utf-8")
        return handbook

    def test_s1_finds_agents_handbook_and_ignores_cursor(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw)
            agents = self._write_handbook(app / ".agents" / "skills", "verify-notes")
            cursor = app / ".cursor" / "skills" / "verify-notes"
            cursor.mkdir(parents=True)
            (cursor / "SKILL.md").write_text("# cursor-only\n", encoding="utf-8")
            (cursor / "features").mkdir()
            (cursor / "features" / "README.md").write_text("# other\n", encoding="utf-8")
            result = self._run_lookup(app)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "found")
            self.assertEqual(len(payload["handbooks"]), 1)
            handbook = payload["handbooks"][0]
            self.assertEqual(handbook["name"], "verify-notes")
            self.assertEqual(Path(handbook["skill_file"]).resolve(), (agents / "SKILL.md").resolve())
            self.assertEqual(handbook["feature_files"], ["create-note.md"])
            self.assertNotIn(".cursor", handbook["skill_file"])
            self.assertNotIn("legacy", payload)

    def test_s2_legacy_grok_only_is_missing_with_migration_hint(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw)
            self._write_handbook(app / ".grok" / "skills", "verify-notes")
            result = self._run_lookup(app)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "missing")
            self.assertNotIn("handbooks", payload)
            self.assertEqual(payload["legacy"], ["verify-notes"])
            self.assertIn("mkdir -p .agents/skills && git mv", payload["hint"])

    def test_s3_agents_and_legacy_side_by_side_reports_one_agents_handbook(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw)
            agents = self._write_handbook(app / ".agents" / "skills", "verify-notes")
            self._write_handbook(app / ".grok" / "skills", "verify-notes", feature="stale.md")
            result = self._run_lookup(app)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "found")
            self.assertEqual(len(payload["handbooks"]), 1)
            handbook = payload["handbooks"][0]
            self.assertEqual(Path(handbook["skill_file"]).resolve(), (agents / "SKILL.md").resolve())
            self.assertEqual(handbook["feature_files"], ["create-note.md"])
            self.assertEqual(payload["legacy"], ["verify-notes"])
            self.assertIn("git rm -r", payload["hint"])
            self.assertNotIn("git mv", payload["hint"])

    def test_found_with_unmigrated_legacy_of_other_name_gets_move_hint(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw)
            self._write_handbook(app / ".agents" / "skills", "verify-web")
            self._write_handbook(app / ".grok" / "skills", "verify-cli")
            result = self._run_lookup(app)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual([item["name"] for item in payload["handbooks"]], ["verify-web"])
            self.assertEqual(payload["legacy"], ["verify-cli"])
            self.assertIn("git mv", payload["hint"])
            self.assertNotIn("git rm", payload["hint"])

    def test_found_with_mixed_duplicate_and_unmigrated_legacy_gets_move_hint(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw)
            self._write_handbook(app / ".agents" / "skills", "verify-notes")
            self._write_handbook(app / ".agents" / "skills", "verify-web")
            self._write_handbook(app / ".grok" / "skills", "verify-notes", feature="stale.md")
            self._write_handbook(app / ".grok" / "skills", "verify-cli")
            result = self._run_lookup(app)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual([item["name"] for item in payload["handbooks"]], ["verify-notes", "verify-web"])
            self.assertEqual(payload["legacy"], ["verify-cli", "verify-notes"])
            # The move must be scoped: `git mv` onto an existing dir nests the old copy inside it.
            self.assertIn("git mv", payload["hint"])
            self.assertIn("Never 'git mv' onto an existing directory", payload["hint"])
            self.assertIn("reconcile the two by hand, then 'git rm -r'", payload["hint"])

    def test_missing_with_legacy_colliding_with_incomplete_agents_dir_warns_before_moving(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw)
            (app / ".agents" / "skills" / "verify-notes").mkdir(parents=True)
            self._write_handbook(app / ".grok" / "skills", "verify-notes")
            result = self._run_lookup(app)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "missing")
            self.assertEqual(payload["legacy"], ["verify-notes"])
            self.assertIn("Never 'git mv' onto an existing directory", payload["hint"])

    def test_legacy_dir_is_reported_even_when_empty_and_alongside_incomplete_agents_dir(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw)
            (app / ".grok" / "skills" / "verify-old").mkdir(parents=True)
            agents = app / ".agents" / "skills" / "verify-notes"
            agents.mkdir(parents=True)
            (agents / "SKILL.md").write_text("# notes\n", encoding="utf-8")
            (app / ".agents" / "skills" / "verify-not-a-dir").write_text("stray file\n", encoding="utf-8")
            result = self._run_lookup(app)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "missing")
            self.assertEqual(payload["legacy"], ["verify-old"])
            self.assertEqual(payload["incomplete"], {"verify-notes": ["features", "features/README.md"]})

    def test_agents_handbook_with_directory_named_skill_md_is_incomplete(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw)
            agents = app / ".agents" / "skills" / "verify-notes"
            (agents / "SKILL.md").mkdir(parents=True)
            (agents / "features").mkdir()
            (agents / "features" / "README.md").write_text("# map\n", encoding="utf-8")
            result = self._run_lookup(app)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "missing")
            self.assertEqual(payload["incomplete"], {"verify-notes": ["SKILL.md"]})

    def test_s4_cursor_only_handbook_is_missing(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw)
            self._write_handbook(app / ".cursor" / "skills", "verify-notes")
            result = self._run_lookup(app)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "missing")
            self.assertNotIn("handbooks", payload)
            self.assertNotIn("legacy", payload)

    def test_agents_handbook_without_features_readme_is_incomplete(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw)
            agents = app / ".agents" / "skills" / "verify-notes"
            (agents / "features").mkdir(parents=True)
            (agents / "SKILL.md").write_text("# notes\n", encoding="utf-8")
            (agents / "features" / "create-note.md").write_text("# create\n", encoding="utf-8")
            result = self._run_lookup(app)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "missing")
            self.assertEqual(payload["incomplete"], {"verify-notes": ["features/README.md"]})

    def test_agents_skill_without_features_is_missing(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw)
            agents = app / ".agents" / "skills" / "verify-notes"
            agents.mkdir(parents=True)
            (agents / "SKILL.md").write_text("# notes\n", encoding="utf-8")
            result = self._run_lookup(app)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "missing")

    def test_keel_checkout_has_verify_keel_handbook(self) -> None:
        result = self._run_lookup(ROOT)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "found")
        self.assertEqual([item["name"] for item in payload["handbooks"]], ["verify-keel"])
        handbook = payload["handbooks"][0]
        self.assertEqual(
            Path(handbook["skill_file"]).resolve(),
            (ROOT / ".agents" / "skills" / "verify-keel" / "SKILL.md").resolve(),
        )
        self.assertEqual(
            sorted(handbook["feature_files"]),
            sorted(path.name for path in (ROOT / ".agents/skills/verify-keel/features").glob("*.md")
                   if path.name != "README.md"),
        )


class VerifyScratchSafetyTests(unittest.TestCase):
    def test_handbook_and_all_features_never_target_live_home_variables(self) -> None:
        handbook = ROOT / ".agents/skills/verify-keel"
        unsafe = re.compile(r"\$(?:HOME|BIN)\b|\$\{(?:HOME|BIN)\}")
        for path in handbook.rglob("*.md"):
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(unsafe.search(path.read_text(encoding="utf-8")))


class DomainHandoffContractTests(unittest.TestCase):
    """Lock the draft, how, and backlog handoff order the agents actually read."""

    def test_scenario_check_runs_before_clarification_read(self) -> None:
        design = (ROOT / "skills/keel-design/SKILL.md").read_text(encoding="utf-8")
        read_at = design.index("完整读取 [按需澄清](references/clarification.md)")
        before = design[:read_at]
        for phrase in ("规则之间的矛盾", "遗漏的失败结果", "能推翻当前假设的反例"):
            self.assertIn(phrase, before)
        self.assertLess(before.index("规则之间的矛盾"), before.rindex("不同选择会改变产品结果"))

    def test_how_handoff_allows_source_without_a_contract(self) -> None:
        how = (ROOT / "skills/keel-how/SKILL.md").read_text(encoding="utf-8")
        start = how.index("涉及业务术语歧义")
        end = how.index("简单单模块改动无需补一套领域模型", start)
        chunk = how[start:end]
        self.assertIn("引用源码", chunk)
        self.assertIn("已有契约存在时一并引用", chunk)
        self.assertIn("没有书面契约时仍交接", chunk)
        self.assertIn("标为未验证", chunk)
        self.assertIn("不因缺契约文档而阻断", chunk)
        self.assertNotIn("每项引用已有契约与源码", chunk)
        self.assertIn("简单单模块改动无需补一套领域模型", how[end:])

    def test_backlog_admits_evidenced_codebase_improvements(self) -> None:
        reflect = (ROOT / "skills/keel-reflect/SKILL.md").read_text(encoding="utf-8")
        backlog = reflect.split("## Backlog", 1)[1].split("## 4.", 1)[0]
        self.assertIn("有证据且保持现有行为的代码库改进", backlog)
        self.assertIn("抽象偏好", backlog)
        self.assertIn("当前验收尚未完成", backlog)
        issues = (ROOT / "skills/keel-reflect/references/issues.md").read_text(encoding="utf-8")
        header = issues.split("## 准入与合并", 1)[0]
        self.assertIn("有证据且保持现有行为的代码库改进", header)
        self.assertNotIn("只在 `keel-reflect` 的 Backlog 里存在产品 Issue 候选时读取本文件", header)


if __name__ == "__main__":
    unittest.main()
