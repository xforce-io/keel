from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "keel-reflect"
    / "scripts"
    / "inspect_context.py"
)


def load_inspector_module():
    spec = importlib.util.spec_from_file_location("keel_reflect_inspect_context", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InspectContextTest(unittest.TestCase):
    def test_git_queries_disable_optional_locks(self) -> None:
        inspector = load_inspector_module()
        with patch.object(inspector.subprocess, "run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = ""

            inspector.run_git(Path.cwd(), "status", "--short")

            environment = run.call_args.kwargs["env"]
            self.assertEqual(environment["GIT_OPTIONAL_LOCKS"], "0")

    def run_inspector(self, cwd: Path, home: Path) -> dict[str, object]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--cwd", str(cwd)],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return json.loads(result.stdout)

    def configure_global_source(self, home: Path) -> Path:
        source = home / ".config" / "agents" / "AGENTS.md"
        source.parent.mkdir(parents=True)
        source.write_text("# Agent Instructions\n", encoding="utf-8")
        link = home / ".grok" / "Agents.md"
        link.parent.mkdir(parents=True)
        link.symlink_to(source)
        return source

    def test_resolves_case_sensitive_grok_link_to_one_global_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            cwd = root / "work"
            cwd.mkdir(parents=True)
            source = self.configure_global_source(home)

            output = self.run_inspector(cwd, home)

            self.assertEqual(output["schema_version"], 2)
            self.assertEqual(output["scope"], "global")
            self.assertEqual(output["canonical_global_target"], str(source.resolve()))
            self.assertEqual(output["configuration_conflicts"], [])
            sources = output["global_sources"]
            assert isinstance(sources, list)
            self.assertTrue(sources)
            self.assertTrue(all("content" not in record for record in sources))

    def test_reports_sanitized_github_origin_without_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            repo = root / "repo"
            repo.mkdir(parents=True)
            self.configure_global_source(home)
            subprocess.run(["git", "init", str(repo)], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "remote",
                    "add",
                    "origin",
                    "https://secret-token@github.com/acme/project.git?token=also-secret",
                ],
                check=True,
            )

            output = self.run_inspector(repo, home)
            repository = output["repository"]
            assert isinstance(repository, dict)
            hosting = repository["hosting"]
            assert isinstance(hosting, dict)

            self.assertEqual(hosting["kind"], "github")
            self.assertEqual(hosting["host"], "github.com")
            self.assertEqual(
                hosting["sanitized_origin"], "https://github.com"
            )
            self.assertNotIn("secret", json.dumps(output))

    def test_recognizes_gitlab_scp_origin(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            repo = root / "repo"
            repo.mkdir(parents=True)
            self.configure_global_source(home)
            subprocess.run(["git", "init", str(repo)], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "remote",
                    "add",
                    "origin",
                    "git@gitlab.example.com:group/project.git",
                ],
                check=True,
            )

            output = self.run_inspector(repo, home)
            repository = output["repository"]
            assert isinstance(repository, dict)
            hosting = repository["hosting"]
            assert isinstance(hosting, dict)

            self.assertEqual(hosting["kind"], "gitlab")
            self.assertEqual(hosting["host"], "gitlab.example.com")
            self.assertEqual(
                hosting["sanitized_origin"], "gitlab.example.com"
            )

    def test_omits_url_path_that_may_contain_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            repo = root / "repo"
            repo.mkdir(parents=True)
            self.configure_global_source(home)
            subprocess.run(["git", "init", str(repo)], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "remote",
                    "add",
                    "origin",
                    "https://github.com/acme/project.git;token=secret",
                ],
                check=True,
            )

            output = self.run_inspector(repo, home)
            repository = output["repository"]
            assert isinstance(repository, dict)
            hosting = repository["hosting"]
            assert isinstance(hosting, dict)

            self.assertEqual(hosting["kind"], "github")
            self.assertEqual(hosting["sanitized_origin"], "https://github.com")
            self.assertNotIn("secret", json.dumps(output))

    def test_omits_remote_helper_with_nested_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            repo = root / "repo"
            repo.mkdir(parents=True)
            self.configure_global_source(home)
            subprocess.run(["git", "init", str(repo)], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "remote",
                    "add",
                    "origin",
                    "ext::curl https://user:secret@example.com/repo",
                ],
                check=True,
            )

            output = self.run_inspector(repo, home)
            repository = output["repository"]
            assert isinstance(repository, dict)
            hosting = repository["hosting"]
            assert isinstance(hosting, dict)

            self.assertEqual(hosting["kind"], "unknown")
            self.assertIsNone(hosting["host"])
            self.assertIsNone(hosting["sanitized_origin"])
            self.assertNotIn("secret", json.dumps(output))

    def test_invalid_url_port_does_not_stop_inspection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            repo = root / "repo"
            repo.mkdir(parents=True)
            self.configure_global_source(home)
            subprocess.run(["git", "init", str(repo)], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "remote",
                    "add",
                    "origin",
                    "https://user:secret@example.com:notaport/repo",
                ],
                check=True,
            )

            output = self.run_inspector(repo, home)
            repository = output["repository"]
            assert isinstance(repository, dict)
            hosting = repository["hosting"]
            assert isinstance(hosting, dict)

            self.assertEqual(hosting["kind"], "unknown")
            self.assertIsNone(hosting["host"])
            self.assertIsNone(hosting["sanitized_origin"])
            self.assertNotIn("secret", json.dumps(output))

    def test_omits_ambiguous_scp_remote_with_embedded_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            repo = root / "repo"
            repo.mkdir(parents=True)
            self.configure_global_source(home)
            subprocess.run(["git", "init", str(repo)], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "remote",
                    "add",
                    "origin",
                    "user:secret@github.com:org/repo.git",
                ],
                check=True,
            )

            output = self.run_inspector(repo, home)
            repository = output["repository"]
            assert isinstance(repository, dict)
            hosting = repository["hosting"]
            assert isinstance(hosting, dict)

            self.assertEqual(hosting["kind"], "unknown")
            self.assertIsNone(hosting["host"])
            self.assertIsNone(hosting["sanitized_origin"])
            self.assertNotIn("secret", json.dumps(output))


if __name__ == "__main__":
    unittest.main()
