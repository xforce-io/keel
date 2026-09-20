from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'bin/keel'
FIXTURE = ROOT / 'skills/keel-release/examples/check'
SHA = 'a' * 40


class DeliveryCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(FIXTURE, self.root / 'delivery')
        self.record = self.root / 'delivery/complete.json'
        self.data = json.loads(self.record.read_text())

    def run_check(self, data=None, *extra, json_output=True, ci=True, cli=CLI):
        if data is not None:
            self.record.write_text(json.dumps(data))
        cmd = [sys.executable, str(cli), 'check', str(self.record), '--issue', '20',
               '--candidate', SHA, '--stories', 'S1,S2,S3']
        if ci:
            cmd += ['--required-ci', 'unit']
        if json_output:
            cmd += ['--json']
        return subprocess.run(cmd + list(extra), cwd=self.root, capture_output=True, text=True)

    def blocked(self, data, *extra, **kw):
        run = self.run_check(data, *extra, **kw)
        self.assertEqual(run.returncode, 1, run.stderr + run.stdout)
        value = json.loads(run.stdout)
        self.assertEqual(value['status'], 'BLOCKED')
        failed = [c for c in value['checks'] if c['status'] == 'fail']
        self.assertTrue(failed)
        for c in failed:
            self.assertTrue(c['next_stage'])
            self.assertTrue(c['resume_when'])
            self.assertTrue(c['source'])
        return failed

    def test_complete_and_text_json_agree(self):
        run = self.run_check()
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        self.assertEqual(json.loads(run.stdout)['status'], 'PASS')
        run = self.run_check(json_output=False)
        self.assertEqual(run.returncode, 0)
        self.assertTrue(run.stdout.startswith('PASS\n'))

    def test_read_only_and_no_command_execution(self):
        self.data['stories'][0]['command'] = 'touch SHOULD_NOT_EXIST'
        self.record.write_text(json.dumps(self.data))
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(self.run_check().returncode, 0)
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_missing_duplicate_reordered_and_failed_stories(self):
        for rows in (self.data['stories'][:-1], self.data['stories'] + self.data['stories'][:1],
                     list(reversed(self.data['stories']))):
            with self.subTest(rows=rows):
                d = copy.deepcopy(self.data); d['stories'] = rows
                self.blocked(d)
        self.data['stories'][0]['status'] = 'fail'
        self.blocked(self.data)

    def test_each_required_section_missing(self):
        for field in ('design', 'stories', 'verify', 'review', 'ci'):
            with self.subTest(field=field):
                d = copy.deepcopy(self.data); del d[field]
                self.blocked(d)

    def test_evidence_missing_modified_or_directory(self):
        for path in ('missing.txt', '.'):
            d = copy.deepcopy(self.data); d['verify']['evidence']['path'] = path
            self.blocked(d)
        (self.record.parent / 'evidence.txt').write_text('changed')
        self.blocked(self.data)

    def test_review_gates(self):
        for field, value in [('status', 'CHANGES_REQUESTED'), ('status', 'BLOCKED'),
                             ('human', 'required'), ('human', None), ('reviewer_host', ''),
                             ('reviewer_model', ''), ('source', 'invented')]:
            with self.subTest(field=field, value=value):
                d = copy.deepcopy(self.data); d['review'][field] = value
                self.blocked(d)

    def approved_record(self):
        data = copy.deepcopy(self.data)
        data['review']['human'] = 'required'
        data['human_approval'] = dict(status='approved', actor='test-human',
                                     candidate_sha=SHA, evidence=copy.deepcopy(data['review']['evidence']))
        return data

    def test_human_approval_closes_required_gate_without_rewriting_review(self):
        data = self.approved_record()
        run = self.run_check(data)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(json.loads(run.stdout)['status'], 'PASS')
        self.assertEqual(json.loads(self.record.read_text())['review']['human'], 'required')
        del data['human_approval']
        failed = self.blocked(data)
        self.assertIn('human_approval.status', [c['id'] for c in failed])

    def test_human_approval_requires_all_fields_and_current_evidence(self):
        for field in ('status', 'actor', 'candidate_sha', 'evidence'):
            data = self.approved_record(); del data['human_approval'][field]
            self.blocked(data)
        for field, value in [('status', 'pending'), ('status', 'rejected'), ('actor', ' '),
                             ('candidate_sha', 'b' * 40), ('evidence', {'path': 'missing'})]:
            with self.subTest(field=field, value=value):
                data = self.approved_record(); data['human_approval'][field] = value
                self.blocked(data)
        for value in (None, [], True, 5, 'approved'):
            data = self.approved_record(); data['human_approval'] = value
            self.blocked(data)
        data = self.approved_record(); data['human_approval']['evidence']['sha256'] = '0' * 64
        self.blocked(data)

    def test_human_approval_never_overrides_review_or_other_gates(self):
        for field, value in [('status', 'CHANGES_REQUESTED'), ('status', 'BLOCKED'),
                             ('human', None), ('candidate_sha', 'b' * 40), ('source', 'fake')]:
            data = self.approved_record(); data['review'][field] = value
            self.blocked(data)
        data = self.approved_record(); data['stories'][0]['status'] = 'fail'
        self.blocked(data)
        data = self.approved_record(); data['ci']['checks'][0]['status'] = 'pending'
        self.blocked(data)

    def test_optional_does_not_hide_invalid_supplied_approval(self):
        data = self.approved_record(); data['review']['human'] = 'optional'
        self.assertEqual(self.run_check(data).returncode, 0)
        data['human_approval']['status'] = 'rejected'
        self.blocked(data)
        del data['human_approval']
        self.assertEqual(self.run_check(data).returncode, 0)

    def test_all_candidate_bindings(self):
        for section in ('stories', 'verify', 'review', 'ci'):
            d = copy.deepcopy(self.data)
            row = d[section][0] if section == 'stories' else d[section]
            row['candidate_sha'] = 'b' * 40
            self.blocked(d)
        self.blocked(self.data, '--candidate', 'b' * 40)

    def test_design_version_and_issue(self):
        self.data['design']['version'] = ''
        self.blocked(self.data)
        self.blocked(None, '--issue', '21')

    def test_ci_incomplete_failed_pending_and_duplicate(self):
        for state in ('fail', 'pending', 'cancel', 'skip'):
            d = copy.deepcopy(self.data); d['ci']['checks'][0]['status'] = state
            self.blocked(d)
        for rows in ([], self.data['ci']['checks'] * 2):
            d = copy.deepcopy(self.data); d['ci']['checks'] = rows
            self.blocked(d)
        self.blocked(self.data, '--required-ci', 'missing')

    def test_cli_gui_and_legal_skip(self):
        for kind in ('cli', 'gui'):
            d = copy.deepcopy(self.data); d['verify']['user_path'] = kind
            self.assertEqual(self.run_check(d).returncode, 0)
            d['verify'].update(status='skip', reason='not applicable')
            self.blocked(d)
        self.data['verify'].update(user_path='none', status='skip', reason='无用户路径，批准范围见证据')
        self.assertEqual(self.run_check(self.data).returncode, 0)
        self.data['verify']['reason'] = ''
        self.blocked(self.data)

    def test_no_ci_requires_explicit_skip_evidence(self):
        self.data['ci'].update(status='skip', reason='项目确认没有必需 CI，见证据', checks=[])
        self.assertEqual(self.run_check(self.data, ci=False).returncode, 0)
        self.blocked(self.data)
        del self.data['ci']['evidence']
        self.blocked(self.data, ci=False)

    def test_claimed_pass_without_evidence_blocked(self):
        for field in ('design', 'verify', 'review', 'ci'):
            d = copy.deepcopy(self.data); del d[field]['evidence']
            self.blocked(d)

    def test_recovery_and_new_candidate_invalidates_old_evidence(self):
        d = copy.deepcopy(self.data); del d['review']
        self.blocked(d)
        self.assertEqual(self.run_check(self.data).returncode, 0)
        self.blocked(self.data, '--candidate', 'b' * 40)
        def update(value):
            if isinstance(value, dict):
                for key in value:
                    if key == 'candidate_sha': value[key] = 'b' * 40
                    else: update(value[key])
            elif isinstance(value, list):
                for item in value: update(item)
        update(self.data)
        self.assertEqual(self.run_check(self.data, '--candidate', 'b' * 40).returncode, 0)

    def test_bad_json_and_invalid_types_fail_closed(self):
        for raw in ('{', '[]', '{"schema_version":1,"schema_version":1}', '\xff'):
            self.record.write_text(raw)
            self.blocked(None)
        for field in self.data:
            for value in (None, [], True, 5):
                d = copy.deepcopy(self.data); d[field] = value
                with self.subTest(field=field, value=value):
                    self.blocked(d)
        d = copy.deepcopy(self.data); d['ci']['checks'][0]['name'] = {}
        self.blocked(d)

    def test_unexpandable_record_path_returns_blocked_json(self):
        self.record = Path('~keel_nonexistent_user_8206942251/delivery.json')
        failed = self.blocked(None)
        self.assertEqual([c['id'] for c in failed], ['record'])

    def test_arguments_and_schema(self):
        for extra in (('--stories', 'S1,S1'), ('--candidate', 'short'), ('--issue', '0')):
            self.blocked(self.data, *extra)
        self.data['schema_version'] = 2
        self.blocked(self.data)

    def test_copied_cli_is_standalone(self):
        copied = self.root / 'keel'
        shutil.copy2(CLI, copied)
        self.assertEqual(self.run_check(cli=copied).returncode, 0)


if __name__ == '__main__':
    unittest.main()
