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
  find) [ "$2" = "code-review" ] && echo /fake/code-review/SKILL.md || exit 1 ;;
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
    with_local_skill: bool = True,
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
            self.assertIn("code-review: ok", ok.stdout)
            self.assertNotIn("未安装", ok.stdout)

    def test_doctor_flags_missing_local_skill_and_code_review(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            run_keel(home, "install")
            result = run_keel(home, "doctor", with_local_skill=False)
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            self.assertIn("local-skill: ⚠ 未在 PATH", result.stdout)
            self.assertIn("code-review", result.stdout)


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
        self.assertNotIn("keel-ticket", order)
        self.assertNotIn("keel-start", order)
        self.assertNotIn("keel-verify-maintain", order)
        router = (ROOT / "skills" / "keel" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`keel-how`（可按该环节 skip）→ `keel-design`", router)
        self.assertIn("`keel-how`（可按该环节 skip）", router)
        self.assertIn("`keel-dev`", router)
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


class WhenToAskContractTests(unittest.TestCase):
    MUST_ASK = (
        "force-push 到共享分支",
        "合入默认分支",
        "部署",
        "删生产数据",
        "对客消息",
    )

    def test_when_to_ask_file_is_the_only_table(self) -> None:
        path = ROOT / "skills" / "keel" / "references" / "when-to-ask.md"
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# 何时问人\n"))
        self.assertIn("必须问", text)
        self.assertIn("默认不问", text)
        self.assertIn("测试-only", text)
        self.assertIn("不以 AGENTS.md", text)
        self.assertIn("写不写 ≠ 问不问", text)
        self.assertIn("when-to-write.md", text)
        self.assertIn("`human: optional`", text)
        self.assertIn("不另给 `human:`", text)
        self.assertNotIn("never-block", text)
        self.assertNotIn("pause", text)
        for item in self.MUST_ASK:
            self.assertIn(item, text)

    def test_router_reads_when_to_ask_and_does_not_copy_the_table(self) -> None:
        router = (ROOT / "skills" / "keel" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/when-to-ask.md", router)
        self.assertIn("references/when-to-write.md", router)
        self.assertNotIn("必须问", router)
        self.assertNotIn("默认不问", router)
        self.assertNotIn("force-push 到共享分支", router)
        self.assertNotIn("删生产数据", router)
        self.assertNotIn("对客消息", router)
        self.assertNotIn("必须写 L1", router)

    def test_when_to_write_file_controls_l1_not_agents_triggers(self) -> None:
        path = ROOT / "skills" / "keel" / "references" / "when-to-write.md"
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# 何时写设计\n"))
        self.assertIn("必须写 L1", text)
        self.assertIn("跳过写 L1", text)
        self.assertIn("测试-only", text)
        self.assertIn("不以 AGENTS.md 的「L1 触发」", text)
        self.assertIn("章节结构", text)
        design = (ROOT / "skills" / "keel-design" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("../keel/references/when-to-write.md", design)
        self.assertIn("先完整读取", design)
        self.assertIn("不以 AGENTS.md 的触发列表为准", design)
        self.assertIn("章节结构、事实源、批准用语仍套用有效 `AGENTS.md`", design)
        self.assertNotIn("必须写 L1", design)
        self.assertNotIn("套用有效 `AGENTS.md` 的 L1/L2 触发", design)

    def test_dev_and_end_to_end_continue_after_writing_l1(self) -> None:
        router = (ROOT / "skills" / "keel" / "SKILL.md").read_text(encoding="utf-8")
        start = router.index("- **dev**")
        chunk = router[start : router.index("\n", start)]
        self.assertIn("keel-design", chunk)
        self.assertNotIn("BLOCKED", chunk)
        self.assertNotIn("停在 `keel-design`", chunk)
        self.assertIn("design-write-if-triggered", router)
        self.assertNotIn("human-approved", router)
        e2e_start = router.index("- **end-to-end**")
        e2e = router[e2e_start : router.index("\n", e2e_start)]
        self.assertNotIn("人工批准", e2e)
        self.assertIn("审查硬条件", router[e2e_start : e2e_start + 400])
        dev = (ROOT / "skills" / "keel-dev" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("没有人工批准", dev)
        self.assertNotIn("设计门禁", dev)
        glossary = (ROOT / "docs" / "glossary.md").read_text(encoding="utf-8")
        self.assertRegex(
            glossary,
            re.compile(r"^\| keel-design \|.*交回路由", re.M),
        )
        self.assertNotRegex(
            glossary,
            re.compile(r"^\| keel-design \|.*停在人工批准", re.M),
        )
        self.assertNotRegex(
            glossary,
            re.compile(r"^\| dev \|.*不绕过", re.M),
        )

    def test_design_flow_still_stops(self) -> None:
        router = (ROOT / "skills" / "keel" / "SKILL.md").read_text(encoding="utf-8")
        start = router.index("- **design**")
        chunk = router[start : router.index("\n", start)]
        self.assertIn("停在人工批准", chunk)
        glossary = (ROOT / "docs" / "glossary.md").read_text(encoding="utf-8")
        self.assertRegex(
            glossary,
            re.compile(r"^\| design \|.*停在人工批准", re.M),
        )
        design = (ROOT / "skills" / "keel-design" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("停在人工批准", design)
        self.assertNotIn("端到端做完", design)
        self.assertIn("交回路由", design)
        self.assertIn("不判断要不要人", design)
        self.assertIn("不给出 `human: required`", design)

    def test_stage_skills_do_not_copy_when_to_ask_table(self) -> None:
        for name in ("keel-design", "keel-dev", "keel-release"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertNotIn("必须问", text, name)
            self.assertNotIn("默认不问", text, name)
            self.assertNotIn("force-push 到共享分支", text, name)
            self.assertNotIn("删生产数据", text, name)
            self.assertNotIn("对客消息", text, name)

    def test_no_second_delivery_entry(self) -> None:
        skills = ROOT / "skills"
        self.assertFalse((skills / "keel" / "references" / "pause.md").exists())
        self.assertFalse(
            (skills / "keel" / "references" / "reversible-vs-irreversible.md").exists()
        )
        self.assertFalse((skills / "keel" / "references" / "style.md").exists())
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("when-to-ask.md", readme)
        self.assertIn("when-to-write.md", readme)
        self.assertIn("写设计", readme)
        self.assertNotIn("设计并停在人工批准", readme)
        router = (ROOT / "skills" / "keel" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`cat-mode` 不启动 route", router)


class CatModeContractTests(unittest.TestCase):
    def test_cat_mode_cites_shared_contracts_without_copying_tables(self) -> None:
        text = (ROOT / "skills" / "cat-mode" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("../keel/references/when-to-ask.md", text)
        self.assertIn("../keel/references/when-to-write.md", text)
        self.assertIn("先完整读取", text)
        self.assertIn("不是交付环节", text)
        self.assertIn("不启动 route / design / dev / end-to-end", text)
        self.assertNotIn("必须问", text)
        self.assertNotIn("默认不问", text)
        self.assertNotIn("force-push 到共享分支", text)
        self.assertNotIn("删生产数据", text)
        self.assertNotIn("对客消息", text)
        self.assertNotIn("必须写 L1", text)
        self.assertIn("disable-model-invocation: true", text)
        desc = text.split("---", 2)[1]
        self.assertNotIn("处理 Issue", desc)
        self.assertNotIn("端到端完成", desc)

    def test_glossary_lists_cat_mode_as_style_not_delivery(self) -> None:
        glossary = (ROOT / "docs" / "glossary.md").read_text(encoding="utf-8")
        self.assertRegex(
            glossary,
            re.compile(r"^\| cat-mode \|.*不是交付环节.*不是流程", re.M),
        )
        router = (ROOT / "skills" / "keel" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("cat-mode", _router_stage_order())
        self.assertIn("风格不在本状态机内", router)


class KeelReflectContractTests(unittest.TestCase):
    def test_reflect_is_not_a_delivery_stage(self) -> None:
        router = (ROOT / "skills" / "keel" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("keel-reflect", _router_stage_order())
        self.assertIn("沉淀不在本状态机内", router)
        self.assertIn("不要在端到端结束时默认跑复盘", router)

    def test_ticket_is_not_a_delivery_stage(self) -> None:
        router = (ROOT / "skills" / "keel" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("keel-ticket", _router_stage_order())
        self.assertIn("建票不在本状态机内", router)
        self.assertIn("建完不默认 `route`", router)
        self.assertIn("禁止改道 `keel-ticket`", router)
        glossary = (ROOT / "docs" / "glossary.md").read_text(encoding="utf-8")
        self.assertRegex(
            glossary,
            re.compile(r"^\| keel-ticket \|.*不是交付环节", re.M),
        )
        ticket = (ROOT / "skills" / "keel-ticket" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("feat/{issue}-{short-desc}", ticket)
        self.assertIn("bugfix/{issue}-{short-desc}", ticket)
        self.assertIn("不自动 `route`", ticket)
        self.assertIn("git checkout -b <name> <default-ref>", ticket)
        self.assertIn("`title`、`description`", ticket)
        self.assertNotIn("create-github-issue", ticket.split("禁止别称")[0])
        issue = (ROOT / "skills" / "keel-issue" / "SKILL.md").read_text(encoding="utf-8")
        release = (ROOT / "skills" / "keel-release" / "SKILL.md").read_text(encoding="utf-8")
        dev = (ROOT / "skills" / "keel-dev" / "SKILL.md").read_text(encoding="utf-8")
        for text in (issue, release, dev):
            self.assertIn("BLOCKED", text)
            self.assertIn("feat/{issue}-*", text)
            self.assertIn("bugfix/{issue}-*", text)
        self.assertIn("chore/*", issue)
        self.assertIn("手工", issue)

    def test_start_is_not_a_delivery_stage(self) -> None:
        router = (ROOT / "skills" / "keel" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("keel-start", _router_stage_order())
        self.assertIn("进仓不在本状态机内", router)
        self.assertIn("不要先跑 `keel-start`", router)
        self.assertIn("不调用 monastery", router)
        glossary = (ROOT / "docs" / "glossary.md").read_text(encoding="utf-8")
        self.assertRegex(
            glossary,
            re.compile(r"^\| keel-start \|.*不是交付环节", re.M),
        )
        start = (ROOT / "skills" / "keel-start" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("只读", start)
        self.assertIn("仅当本轮明确说「清」", start)
        self.assertIn("不调用", start)
        self.assertIn("monastery", start)
        self.assertIn("先 `git checkout <默认短名>`", start)
        self.assertIn("gh pr list --head", start)
        self.assertIn("commit-tree", start)
        self.assertIn("for-each-ref", start)
        self.assertIn("state=merged", start)
        self.assertIn("工作区脏 → `BLOCKED`", start)
        self.assertIn("不回退 `gh`", start)
        self.assertIn("禁止 `checkout origin/", start)

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

    def test_verdict_requires_exactly_one_human_field(self) -> None:
        review = (ROOT / "skills" / "keel-review" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`human: required`", review)
        self.assertIn("`human: optional`", review)
        self.assertIn("审查未完成", review)
        self.assertIn("不得补写", review)
        reviewer = (ROOT / "agents" / "reviewer.md").read_text(encoding="utf-8")
        self.assertIn("human: required", reviewer)
        self.assertIn("human: optional", reviewer)

    def test_hard_conditions_forbid_optional(self) -> None:
        text = (ROOT / "skills" / "keel-review" / "SKILL.md").read_text(encoding="utf-8")
        start = text.index("硬条件")
        chunk = text[start:]
        self.assertIn("SKILL.md", chunk)
        self.assertIn("安装", chunk)
        self.assertIn("鉴权", chunk)
        self.assertIn("公开 CLI", chunk)
        self.assertIn("`P0`", chunk)
        self.assertIn("三轮", chunk)
        self.assertIn("无法证明", chunk)
        self.assertIn("不得 `optional`", chunk)

    def test_release_requires_pass_and_optional(self) -> None:
        release = (ROOT / "skills" / "keel-release" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`human: optional`", release)
        self.assertIn("`human: required`", release)
        self.assertIn("BLOCKED", release)
        self.assertIn("reviewer_host", release)
        review = (ROOT / "skills" / "keel-review" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`PASS` 且 `human: optional`", review)

    def test_review_model_resolves_from_bind_not_inherit(self) -> None:
        review = (ROOT / "skills" / "keel-review" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("**Cursor：**", review)
        self.assertIn("`~/.config/keel/reviewer`", review)
        self.assertIn("禁止 `inherit`", review)
        self.assertIn("禁止未声明自选", review)
        self.assertIn("reviewer_host", review)
        self.assertIn("reviewer_model", review)
        self.assertIn("`bind-file`", review)
        self.assertNotIn("claude-opus", review)
        self.assertNotIn("grok-4.6", review)
        reviewer = (ROOT / "agents" / "reviewer.md").read_text(encoding="utf-8")
        self.assertIn("reviewer_host", reviewer)
        self.assertIn("`~/.config/keel/reviewer`", reviewer)

    def test_verify_maintenance_regression_skips_review(self) -> None:
        text = (ROOT / "skills" / "keel-verify" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## 维护回归（无 Issue / 全图）", text)
        self.assertIn("完成表**不**交给 `keel-review`", text)
        self.assertIn(".grok/verify-runs/regression/", text)
        self.assertIn("keel-verify-maintain", text)

    def test_dev_blocks_unmapped_user_visible_stories(self) -> None:
        dev = (ROOT / "skills" / "keel-dev" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("功能地图不是「额外证据文件」", dev)
        self.assertIn("features/README.md", dev)
        self.assertIn("对不上 → `BLOCKED`", dev)
        self.assertIn("无用户路径", dev)
        self.assertNotIn("不要新增项目没有的证据文件、截图工厂或额外 E2E 层", dev)

    def test_release_requires_verify_table_for_user_visible(self) -> None:
        release = (ROOT / "skills" / "keel-release" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("keel-verify", release)
        self.assertIn("pytest", release)
        self.assertIn("BLOCKED", release)
        router = (ROOT / "skills" / "keel" / "SKILL.md").read_text(encoding="utf-8")
        route = router[router.index("- **route**") : router.index("- **design**")]
        self.assertIn("禁止以开 PR/MR 代替", route)
        self.assertIn("keel-verify", route)

    def test_l2_test_plan_must_name_feature_file(self) -> None:
        design = (ROOT / "skills" / "keel-design" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("features/<file>.md", design)
        self.assertIn("一一对应", design)
        when = (
            ROOT / "skills" / "keel" / "references" / "when-to-write.md"
        ).read_text(encoding="utf-8")
        self.assertIn("features/<file>.md", when)

    def test_verify_maintain_is_not_a_delivery_stage(self) -> None:
        router = (ROOT / "skills" / "keel" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("功能地图维护不在本状态机内", router)
        self.assertNotIn("keel-verify-maintain", _router_stage_order())
        glossary = (ROOT / "docs" / "glossary.md").read_text(encoding="utf-8")
        self.assertRegex(
            glossary,
            re.compile(r"^\| keel-verify-maintain \|.*不是交付环节", re.M),
        )
        self.assertRegex(
            glossary,
            re.compile(r"^\| 功能地图 \|", re.M),
        )
        maintain = (
            ROOT / "skills" / "keel-verify-maintain" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("只编辑该 `verify-*` 目录", maintain)
        self.assertIn("不改产品代码", maintain)
        self.assertIn("完成表**不**交给 `keel-review`", maintain)
        self.assertIn(".grok/verify-runs/regression/", maintain)
        self.assertNotIn("git mv", maintain)


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
            ["doctor.md", "install.md", "review.md", "start.md", "sync.md", "ticket.md", "uninstall.md", "verify-gates.md"],
        )


class HandbookPathWordingTests(unittest.TestCase):
    DOCS = (
        "README.md",
        "docs/glossary.md",
        "skills/keel/SKILL.md",
        "skills/keel-dev/SKILL.md",
        "skills/keel-verify/SKILL.md",
    )

    def test_s5_docs_name_the_neutral_handbook_path(self) -> None:
        for relative in self.DOCS:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(".agents/skills/verify-", text, relative)

    def test_s5_legacy_path_is_never_the_handbook_location(self) -> None:
        for relative in self.DOCS:
            for line in (ROOT / relative).read_text(encoding="utf-8").splitlines():
                if ".grok/skills/verify-" not in line:
                    continue
                negated = any(marker in line for marker in ("旧", "retired", "不认", "不是手册", "no longer"))
                self.assertTrue(negated, f"{relative} still presents the legacy path as a handbook location: {line}")

    def test_legacy_migration_commands_live_only_in_the_lookup_hint(self) -> None:
        # Restating the commands here is what let the doc drift into advising an unconditional
        # delete; lookup.py picks move / reconcile-then-delete / delete and owns the wording.
        text = (ROOT / "skills" / "keel-verify" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("hint", text)
        for command in ("git mv", "git rm"):
            self.assertNotIn(command, text, f"keel-verify SKILL.md restates '{command}' instead of relaying hint")


if __name__ == "__main__":
    unittest.main()
