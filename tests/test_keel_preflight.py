from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_keel import run_keel

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "keel"
SHA = "a" * 40
OTHER = "b" * 40
EXPORT = hashlib.sha256(b"export-v3").hexdigest()
LINE = re.compile(
    r"^\[(pass|fail)\] acceptance_id=(\S*) field=(\S*) branch=(\S*) class=(\S*) — "
)
CHAIN = ["independent-failure", "rework", "new-inspection", "human-accept-close"]


def required_item(acceptance_id="S1.A1", **changes):
    row = {
        "id": acceptance_id,
        "branches": list(CHAIN),
        "entries": ["browser"],
        "object": "export-current",
        "version": "v3",
        "export_sha256": EXPORT,
        "decision_id": "decide-9",
        "revision": "r2",
    }
    row.update(changes)
    return row


def evidence_item(file_sha, acceptance_id="S1.A1", **changes):
    row = {
        "id": acceptance_id,
        "task_id": "task-current",
        "branches": list(CHAIN),
        "entries": ["browser"],
        "object": "export-current",
        "version": "v3",
        "export_sha256": EXPORT,
        "decision_id": "decide-9",
        "revision": "r2",
        "evidence": {"path": "play.txt", "sha256": file_sha},
    }
    row.update(changes)
    return row


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.play = self.root / "play.txt"
        self.play.write_text("played export-current v3\n", encoding="utf-8")
        self.file_sha = hashlib.sha256(self.play.read_bytes()).hexdigest()

    def run_preflight(self, required_items, evidence_items, *, candidate=SHA, issue=26,
                      task="task-current", previous=None, json_output=True, cli=CLI, home=None,
                      record_extra=None):
        required = {"schema_version": 1, "issue": issue, "candidate_sha": candidate,
                    "task_id": task, "items": required_items}
        record = {"schema_version": 1, "issue": issue, "candidate_sha": candidate,
                  "items": evidence_items}
        if record_extra:
            record.update(record_extra)
        (self.root / "required.json").write_text(json.dumps(required), encoding="utf-8")
        (self.root / "record.json").write_text(json.dumps(record), encoding="utf-8")
        cmd = [sys.executable, str(cli)]
        env = None
        if home is not None:
            cmd += ["--home", str(home), "--bin-dir", str(home / ".local" / "bin")]
            env = os.environ.copy()
            env["KEEL_ROOT"] = str(ROOT)
            env["KEEL_HOME"] = str(home)
        cmd += ["preflight", str(self.root / "record.json"),
                "--issue", str(issue), "--candidate", candidate,
                "--required", str(self.root / "required.json")]
        if previous is not None:
            cmd += ["--previous", str(previous)]
        if json_output:
            cmd += ["--json"]
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = subprocess.run(cmd, cwd=self.root, capture_output=True, text=True, env=env)
        after = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result.before = before
        result.after = after
        return result

    def parsed(self, required_items, evidence_items, **kwargs):
        result = self.run_preflight(required_items, evidence_items, **kwargs)
        self.assertEqual(result.before, result.after)
        self.assertNotIn("产品验收 PASS", result.stdout)
        self.assertNotIn("可送审", result.stdout)
        if kwargs.get("json_output", True):
            self.assertEqual(result.stderr, "")
            payload = json.loads(result.stdout)
            self.assertIs(payload["product_acceptance"], False)
            self.assertEqual(payload["ready_for_review"], result.returncode == 0)
            self.assertEqual(payload["status"], "PASS" if result.returncode == 0 else "BLOCKED")
            text = self.run_preflight(required_items, evidence_items, **{**kwargs, "json_output": False})
            self.assertEqual(text.returncode, result.returncode)
            self.assertEqual(text.before, text.after)
            self.assertNotIn("产品验收 PASS", text.stdout)
            rows = [LINE.match(line) for line in text.stdout.splitlines() if line.startswith("[")]
            self.assertTrue(all(rows))
            seen = [(m.group(2), m.group(3), m.group(4), m.group(1), m.group(5)) for m in rows]
            expected = [(c["acceptance_id"], c["field"], c["branch"], c["status"], c["class"])
                        for c in payload["checks"]]
            self.assertEqual(seen, expected)
            self.assertEqual(text.stdout.splitlines()[0], payload["status"])
            if result.returncode == 0:
                self.assertIn("本次可以交接", text.stdout)
                self.assertNotIn("本次不能交接", text.stdout)
            else:
                self.assertIn("本次不能交接", text.stdout)
                self.assertNotIn("本次可以交接", text.stdout)
            return payload
        return result

    def test_missing_required_id(self):
        payload = self.parsed(
            [required_item("S1.A1"), required_item("S1.A2")],
            [evidence_item(self.file_sha, "S1.A1")],
        )
        self.assertEqual(payload["status"], "BLOCKED")
        failed = [c for c in payload["checks"] if c["status"] == "fail"]
        self.assertEqual([(c["acceptance_id"], c["field"], c["class"]) for c in failed],
                         [("S1.A2", "id", "missing-id")])

    def test_missing_branch_or_stage_close(self):
        evidence = evidence_item(self.file_sha, branches=["independent-failure", "rework", "new-inspection"])
        payload = self.parsed([required_item()], [evidence])
        failed = [c for c in payload["checks"] if c["status"] == "fail"]
        self.assertEqual(failed[0]["acceptance_id"], "S1.A1")
        self.assertEqual(failed[0]["branch"], "human-accept-close")
        self.assertEqual(failed[0]["class"], "missing-branch")
        self.assertIn("human-accept-close", failed[0]["reason"])

    def test_missing_entry(self):
        payload = self.parsed([required_item()], [evidence_item(self.file_sha, entries=[])])
        failed = [c for c in payload["checks"] if c["status"] == "fail"]
        self.assertEqual([(c["acceptance_id"], c["field"], c["class"]) for c in failed],
                         [("S1.A1", "entries", "missing-entry")])
        self.assertIn("入口", failed[0]["reason"])

    def test_cross_task_substitution(self):
        payload = self.parsed([required_item()], [evidence_item(self.file_sha, task_id="task-other")])
        failed = [c for c in payload["checks"] if c["status"] == "fail"]
        self.assertEqual([(c["acceptance_id"], c["field"], c["class"]) for c in failed],
                         [("S1.A1", "task_id", "cross-task")])

    def test_stale_object_version_or_export_digest(self):
        cases = {
            "object": "export-old",
            "version": "v1",
            "export_sha256": hashlib.sha256(b"export-old").hexdigest(),
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                payload = self.parsed([required_item()], [evidence_item(self.file_sha, **{field: value})])
                failed = [c for c in payload["checks"] if c["status"] == "fail"]
                self.assertEqual([(c["acceptance_id"], c["field"], c["class"]) for c in failed],
                                 [("S1.A1", field, "stale-association")])

    def test_decision_or_revision_mismatch(self):
        for field, value in (("decision_id", "decide-old"), ("revision", "r1")):
            with self.subTest(field=field):
                payload = self.parsed([required_item()], [evidence_item(self.file_sha, **{field: value})])
                failed = [c for c in payload["checks"] if c["status"] == "fail"]
                self.assertEqual([(c["acceptance_id"], c["field"], c["class"]) for c in failed],
                                 [("S1.A1", field, "decision-mismatch")])

    def test_evidence_file_missing_or_digest_mismatch(self):
        missing = evidence_item(self.file_sha)
        missing["evidence"] = {"path": "missing.txt", "sha256": self.file_sha}
        digest = evidence_item("0" * 64)
        for label, row in (("missing", missing), ("digest", digest)):
            with self.subTest(label=label):
                payload = self.parsed([required_item()], [row])
                failed = [c for c in payload["checks"] if c["status"] == "fail"]
                self.assertEqual([(c["acceptance_id"], c["field"], c["class"]) for c in failed],
                                 [("S1.A1", "evidence.sha256", "evidence-file")])

    def test_complete_input_passes_without_product_acceptance(self):
        payload = self.parsed([required_item()], [evidence_item(self.file_sha)])
        self.assertEqual(payload["status"], "PASS")
        self.assertTrue(payload["ready_for_review"])
        self.assertIs(payload["product_acceptance"], False)
        first = self.run_preflight([required_item()], [evidence_item(self.file_sha)])
        second = self.run_preflight([required_item()], [evidence_item(self.file_sha)])
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertEqual(second.stdout, first.stdout)
        ignored = self.run_preflight(
            [required_item()], [evidence_item(self.file_sha)],
            record_extra={"command": "touch SHOULD_NOT_EXIST"},
        )
        self.assertEqual(ignored.returncode, 0, ignored.stdout + ignored.stderr)
        self.assertFalse((self.root / "SHOULD_NOT_EXIST").exists())
        self.assertEqual(ignored.before, ignored.after)

    def test_failed_preflight_cannot_be_handed_off_until_gaps_are_filled(self):
        short = evidence_item(self.file_sha, branches=["new-inspection"])
        blocked = self.parsed([required_item()], [short])
        self.assertFalse(blocked["ready_for_review"])
        self.assertIn("human-accept-close", [c["branch"] for c in blocked["checks"]])
        passed = self.parsed([required_item()], [evidence_item(self.file_sha)])
        self.assertTrue(passed["ready_for_review"])
        self.assertEqual(passed["candidate_sha"], SHA)

    def test_previous_pass_dies_when_candidate_or_evidence_changes(self):
        first = self.parsed([required_item()], [evidence_item(self.file_sha)])
        previous = self.root / "previous.json"
        previous.write_text(json.dumps(first), encoding="utf-8")
        self.play.write_text("played export-current v3 again\n", encoding="utf-8")
        new_sha = hashlib.sha256(self.play.read_bytes()).hexdigest()
        stale = self.parsed([required_item()], [evidence_item(new_sha)], previous=previous)
        self.assertFalse(stale["ready_for_review"])
        self.assertIn("evidence.sha256", [c["field"] for c in stale["checks"] if c["status"] == "fail"])
        fresh = self.parsed([required_item()], [evidence_item(new_sha)])
        self.assertTrue(fresh["ready_for_review"])
        self.assertNotEqual(fresh["binding"], first["binding"])
        moved = self.parsed([required_item()], [evidence_item(new_sha)], candidate=OTHER, previous=previous)
        self.assertEqual(
            [c["field"] for c in moved["checks"] if c["class"] == "stale-pass"],
            ["candidate_sha"],
        )

    def test_failure_rework_chain_needs_human_accept_and_close(self):
        partial = evidence_item(self.file_sha, branches=["new-inspection"])
        blocked = self.parsed([required_item()], [partial])
        self.assertIn("human-accept-close", [c["branch"] for c in blocked["checks"]])
        self.assertFalse(blocked["ready_for_review"])
        closed = self.parsed([required_item()], [evidence_item(self.file_sha)])
        self.assertTrue(closed["ready_for_review"])
        self.assertIn("human-accept-close", closed["associations"][0]["branches"])

    def test_operation_record_must_match_current_export(self):
        old = evidence_item(self.file_sha, version="v1", entries=["operation-record"])
        required = required_item(entries=["operation-record"])
        blocked = self.parsed([required], [old])
        self.assertEqual([c["field"] for c in blocked["checks"] if c["status"] == "fail"], ["version"])
        self.assertIn("S1.A1", blocked["checks"][0]["acceptance_id"])
        current = self.parsed([required], [evidence_item(self.file_sha, entries=["operation-record"])])
        self.assertTrue(current["ready_for_review"])
        self.assertEqual(current["associations"][0]["version"], "v3")

    def test_l18_and_reused_contract_lists_are_caller_supplied(self):
        source = (ROOT / "skills/keel-verify/scripts/preflight.py").read_text(encoding="utf-8")
        cli = (ROOT / "bin/keel").read_text(encoding="utf-8")
        self.assertNotIn("atelier", source.lower())
        self.assertNotIn("Artifact", source)
        self.assertNotIn("atelier", cli.lower())
        spaces = (["S1.A1", "S4.A6"], ["contract.login", "contract.export"])
        for ids in spaces:
            with self.subTest(ids=ids):
                required = [{"id": aid, "branches": [], "entries": ["cli"]} for aid in ids]
                evidence = [{
                    "id": aid,
                    "task_id": "task-current",
                    "branches": [],
                    "entries": ["cli"],
                    "evidence": {"path": "play.txt", "sha256": self.file_sha},
                } for aid in ids]
                passed = self.parsed(required, evidence)
                self.assertTrue(passed["ready_for_review"])
                self.assertEqual([c["acceptance_id"] for c in passed["checks"] if c["class"] == "consistent"], ids)
                missed = self.parsed(required, evidence[:-1])
                self.assertEqual(
                    [c["acceptance_id"] for c in missed["checks"] if c["class"] == "missing-id"],
                    [ids[-1]],
                )

    def test_copy_installed_cli_runs_the_same_command(self):
        home = self.root / "home"
        home.mkdir()
        installed = run_keel(home, "install", "--copy")
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        copied = home / ".local" / "bin" / "keel"
        payload = self.parsed([required_item()], [evidence_item(self.file_sha)], cli=copied, home=home)
        self.assertTrue(payload["ready_for_review"])
        help_run = subprocess.run([sys.executable, str(copied), "preflight", "--help"],
                                  capture_output=True, text=True)
        self.assertEqual(help_run.returncode, 0)
        self.assertIn("--required", help_run.stdout)
        self.assertIn("--previous", help_run.stdout)

    def test_syntax_error_is_distinct_from_a_blocked_preflight(self):
        result = subprocess.run([sys.executable, str(CLI), "preflight", "record.json"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
