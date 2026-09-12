#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "keel"
STAGE_SKILLS = (
    "keel",
    "keel-issue",
    "keel-how",
    "keel-design",
    "keel-dev",
    "keel-verify",
    "keel-review",
    "keel-release",
    "keel-reflect",
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
            self.assertFalse((home / ".grok" / "agents" / "reviewer.md").exists())
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
            self.assertIn("library/keel-how:", ok.stdout)
            self.assertIn("library/keel-reflect:", ok.stdout)
            self.assertNotIn("library: 未安装", ok.stdout)


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


def _router_stage_order() -> list[str]:
    text = (ROOT / "skills" / "keel" / "SKILL.md").read_text(encoding="utf-8")
    return re.findall(r"^\| \d+ \| `(keel(?:-[a-z]+)?)` \|", text, re.M)


class KeelHowContractTests(unittest.TestCase):
    def test_router_orders_how_after_issue_before_design_and_dev(self) -> None:
        order = _router_stage_order()
        self.assertEqual(
            order,
            [
                "keel-issue",
                "keel-how",
                "keel-design",
                "keel-dev",
                "keel-verify",
                "keel-review",
                "keel-release",
            ],
        )
        self.assertNotIn("keel-reflect", order)
        router = (ROOT / "skills" / "keel" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`keel-how`（可按该环节 skip）→ `keel-design`", router)
        self.assertIn("`keel-how`（可按该环节 skip）→ `keel-dev`", router)
        self.assertIn("下一合法环节是 `keel-how`", router)
        self.assertNotIn("explorer-prompt", router)
        self.assertNotIn("grok-4.6-fast-xhigh", router)

    def test_how_stage_skip_citation_and_blocked(self) -> None:
        how = (ROOT / "skills" / "keel-how" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("skip: 已定位机制", how)
        self.assertIn("skip: 无现成机制可讲", how)
        self.assertIn("skip: 单模块且入口已钉死", how)
        self.assertIn("跨模块", how)
        self.assertIn("BLOCKED", how)
        self.assertIn("出处", how)
        self.assertNotIn("explorer-prompt", how)
        self.assertNotIn("grok-4.6-fast-xhigh", how)
        self.assertNotIn(".grok/skills/verify-", how)
        self.assertIn("不是 `keel-verify`", how)


class KeelReflectContractTests(unittest.TestCase):
    def test_reflect_is_not_a_delivery_stage(self) -> None:
        router = (ROOT / "skills" / "keel" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("keel-reflect", _router_stage_order())
        self.assertIn("沉淀不在本状态机内", router)
        self.assertIn("不要在端到端结束时默认跑复盘", router)

    def test_reflect_uses_three_lenses_and_approval(self) -> None:
        text = (ROOT / "skills" / "keel-reflect" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Accepted", text)
        self.assertIn("Rejected", text)
        self.assertIn("Backlog", text)
        self.assertIn("判断", text)
        self.assertIn("工具", text)
        self.assertIn("唱反调", text)
        self.assertIn("不自动建单", text)
        self.assertIn("inspect_context.py", text)
        self.assertNotIn("grok-4.6-fast-xhigh", text)
        self.assertIn("你批了才建", text)


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
