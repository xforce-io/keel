from __future__ import annotations
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from tests.test_keel import run_keel

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'bin/keel'
A, B = 'a' * 40, 'b' * 40


def metrics(kind='review', **changes):
    row = dict.fromkeys(('elapsed_seconds', 'model_calls', 'cli_calls', 'atomic_reads', 'upstream_requests',
                         'input_tokens', 'cached_input_tokens', 'output_tokens'), 0)
    row.update(elapsed_seconds=10, model_calls=int(kind in ('review', 'agent')))
    row.update(changes)
    return row


class ReverifyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for f in ('ui.txt', 'algorithm.txt', 'resource.txt', 'old.txt', 'precheck.txt', 'approval.txt'):
            (self.root / f).write_text(f)
        self.data = self.plan()
        self.previous = self.root / 'previous.json'; self.write(self.previous, self.data)

    def sha(self, name):
        return hashlib.sha256((self.root / name).read_bytes()).hexdigest()

    def evidence(self, name):
        return {'path': name, 'sha256': self.sha(name)}

    def write(self, path, data):
        path.write_text(json.dumps(data))

    def plan(self):
        rows = []
        for name, method, changed in [('ui', 'user-path', True), ('algorithm', 'agent', False), ('resource', 'user-path', True)]:
            value = self.sha(name + '.txt')
            rows.append({'id': name, 'method': method, 'decision': 'rerun' if changed else 'retain',
                         'reason': '实际受影响路径' if changed else '本轮依赖一致，保留原始运行身份',
                         'dependencies': [{'path': name + '.txt', 'before': '0' * 64 if changed else value, 'after': value}],
                         'old_evidence': {'candidate_sha': A, 'evidence': self.evidence('old.txt')}})
        return {'schema_version': 1, 'task_id': 'task-31', 'candidate_sha': B, 'baseline_sha': A,
                'items': rows, 'out_of_scope': {},
                'prechecks': [{'id': name, 'candidate_sha': B, 'status': 'pass', 'evidence': self.evidence('precheck.txt')}
                              for name in ('streams', 'consumers', 'resources')],
                'history': [], 'extensions': [], 'next_kind': 'review',
                'budget': {'limits': {'elapsed_seconds': 600, 'model_calls': 5}, 'planned': metrics()}}

    def run_plan(self, data=None, extra=(), previous=False, cli=CLI, json_output=True, adopt=False):
        file = self.root / 'plan.json'; self.write(file, self.data if data is None else data)
        args = [sys.executable, str(cli), *(['--home', str(cli.parents[2])] if cli != CLI else []), 'reverify', str(file), '--task', 'task-31', '--candidate', B,
                '--baseline', A, '--root', str(self.root), '--items', 'ui,algorithm,resource',
                '--prechecks', 'streams,consumers,resources', '--changed-path', 'ui.txt', '--changed-path', 'resource.txt']
        args += ['--previous', str(self.previous)] if previous else (['--adopt-history'] if adopt else ['--initial'])
        if json_output: args += ['--json']
        return subprocess.run(args + list(extra), capture_output=True, text=True, cwd=self.root)

    def blocked(self, data=None, **kw):
        r = self.run_plan(data, **kw); self.assertEqual(r.returncode, 1, r.stderr + r.stdout)
        j = json.loads(r.stdout); self.assertEqual(j['status'], 'BLOCKED'); return j

    def history(self, count=1):
        return [{'id': str(i), 'candidate_sha': A, 'kind': 'review', 'verdict': 'CHANGES_REQUESTED',
                 'failure_classes': ['contract-consumer'], 'metrics': metrics()} for i in range(count)]

    def retry(self, data):
        data['retry'] = {'root_cause': '声明与消费不一致', 'strategy_change': '先检查全部消费入口', 'exit_condition': '只追加本轮；仍失败则交人'}

    def test_three_change_classes_and_no_redundant_agent(self):
        r = self.run_plan(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        j = json.loads(r.stdout); self.assertEqual(j['status'], 'READY'); self.assertFalse(any(a['executed'] for a in j['actions']))
        self.assertEqual(j['actions'][1]['decision'], 'retain')
        d = copy.deepcopy(self.data); d['items'][1]['dependencies'][0]['before'] = '0' * 64
        self.blocked(d)
        d['items'][1]['decision'] = 'rerun'; self.assertEqual(self.run_plan(d).returncode, 0)
        d = copy.deepcopy(self.data); d['items'][1]['decision'] = 'rerun'
        self.blocked(d)
        self.assertEqual(self.run_plan(d, extra=['--require-agent', 'algorithm']).returncode, 0)
        self.blocked(extra=['--require-agent', 'algorithm'])
        d = copy.deepcopy(self.data); d['items'][2]['decision'] = 'retain'; self.blocked(d)

    def test_dependency_identity_coverage_and_old_evidence(self):
        for field, value in [('candidate_sha', A), ('baseline_sha', B), ('task_id', 'new-task')]:
            d = copy.deepcopy(self.data); d[field] = value; self.blocked(d)
        (self.root / 'algorithm.txt').write_text('changed')
        self.blocked(); (self.root / 'algorithm.txt').write_text('algorithm.txt')
        self.blocked(extra=['--changed-path', 'unaccounted.txt'])
        d = copy.deepcopy(self.data); d['out_of_scope']['unaccounted.txt'] = '与本票验收无依赖'
        self.assertEqual(self.run_plan(d, extra=['--changed-path', 'unaccounted.txt']).returncode, 0)
        d['items'][1]['old_evidence']['candidate_sha'] = 'invalid'; self.blocked(d)
        d['items'][1]['old_evidence']['candidate_sha'] = 'c' * 40
        self.assertEqual(self.run_plan(d, extra=['--changed-path', 'unaccounted.txt']).returncode, 0)
        d = copy.deepcopy(self.data); d['items'][1]['old_evidence']['evidence']['sha256'] = '0' * 64; self.blocked(d)

    def test_precheck_failures_and_malformed_data_block_before_model(self):
        for i in range(3):
            d = copy.deepcopy(self.data); d['prechecks'][i]['status'] = 'fail'; self.blocked(d)
        for value in (None, {}, 'pass'):
            d = copy.deepcopy(self.data); d['prechecks'] = value; self.blocked(d)
        d = copy.deepcopy(self.data); d['prechecks'][0]['candidate_sha'] = A; self.blocked(d)
        d['prechecks'][0]['candidate_sha'] = B; d['prechecks'][0]['evidence']['path'] = 'missing'; self.blocked(d)

    def test_usage_unknown_is_not_free_and_counters_are_independent(self):
        d = copy.deepcopy(self.data); d['history'] = self.history(); self.retry(d)
        d['history'][0]['metrics'].update(cli_calls=2, atomic_reads=5, upstream_requests=8)
        r = self.run_plan(d, previous=True); self.assertEqual(r.returncode, 0, r.stdout)
        c = json.loads(r.stdout)['cumulative']; self.assertEqual([c[k] for k in ('cli_calls', 'atomic_reads', 'upstream_requests')], [2, 5, 8])
        self.assertIsNone(c['input_tokens']); self.assertEqual(c['model_calls'], 1)
        d['budget']['limits']['input_tokens'] = 1000
        self.blocked(d, previous=True)
        d['history'][0]['metrics'].update(input_tokens=100, cached_input_tokens=90, output_tokens=10)
        d['budget']['planned'].update(input_tokens=100, cached_input_tokens=80, output_tokens=10)
        self.assertEqual(self.run_plan(d, previous=True).returncode, 0)
        d['history'][0]['metrics']['cached_input_tokens'] = 101; self.blocked(d, previous=True)

    def test_unknown_fine_grained_counters_respect_budget_limits(self):
        d = copy.deepcopy(self.data); d['history'] = self.history(); self.retry(d)
        d['history'][0]['metrics'].update(atomic_reads=None, upstream_requests=None)
        d['budget']['planned'].update(atomic_reads=None, upstream_requests=None)
        result = self.run_plan(d, previous=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        report = json.loads(result.stdout)
        for key in ('atomic_reads', 'upstream_requests'):
            self.assertIsNone(report['cumulative'][key])
            self.assertIsNone(report['budget']['projected'][key])
            limited = copy.deepcopy(d); limited['budget']['limits'][key] = 100
            self.assertIn('budget.unknown.' + key, str(self.blocked(limited, previous=True)['checks']))

    def test_budget_boundaries_extension_and_unchanged_authorization(self):
        d = copy.deepcopy(self.data); d['history'] = self.history(); self.retry(d)
        d['budget']['limits']['model_calls'] = 1; self.blocked(d, previous=True)
        d['budget']['limits']['model_calls'] = 2; self.assertEqual(self.run_plan(d, previous=True).returncode, 0)
        d['budget']['limits']['elapsed_seconds'] = 10; self.blocked(d, previous=True)
        d = copy.deepcopy(self.data); d['budget']['limits']['model_calls'] = 6; self.blocked(d, previous=True)
        d['budget_authorization'] = {'actor': 'user', 'evidence': self.evidence('approval.txt')}
        self.assertEqual(self.run_plan(d, previous=True).returncode, 0)
        d['budget']['planned']['elapsed_seconds'] = float('inf'); self.blocked(d, previous=True)

    def test_three_rounds_pause_resume_and_explicit_extra_round(self):
        d = copy.deepcopy(self.data); d['history'] = self.history(3); self.retry(d)
        self.blocked(d, previous=True)
        d['extensions'] = [{'after_round': 3, 'additional_reviews': 1, 'actor': 'user', 'evidence': self.evidence('approval.txt')}]
        self.assertEqual(self.run_plan(d, previous=True).returncode, 0)
        self.write(self.previous, d)
        d['history'] += [self.history(4)[-1]]
        self.blocked(d, previous=True)
        d['history'] = d['history'][1:]; self.blocked(d, previous=True)
        d = copy.deepcopy(self.data); d['history'] = self.history(); self.retry(d)
        self.write(self.previous, d)
        self.assertEqual(self.run_plan(d, previous=True).returncode, 0)
        del d['retry']; self.blocked(d, previous=True)
        self.blocked(d)  # --initial cannot erase a nonempty task history.

    def test_adopt_existing_reviews_and_continue_without_reset(self):
        d = copy.deepcopy(self.data); d['history'] = self.history(); self.retry(d)
        d['history'][0]['evidence'] = self.evidence('old.txt')
        result = self.run_plan(d, adopt=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)['cumulative']['model_calls'], 1)
        self.write(self.previous, d)
        self.assertEqual(self.run_plan(d, previous=True).returncode, 0)
        changed = copy.deepcopy(d); changed['history'][0]['verdict'] = 'PASS'
        self.assertIn('history.append-only', str(self.blocked(changed, previous=True)['checks']))
        (self.root / 'old.txt').write_text('changed')
        self.assertIn('history.evidence', str(self.blocked(d, previous=True)['checks']))

    def test_adopt_requires_review_evidence_and_enforces_round_limit(self):
        self.assertIn('adopt-history', str(self.blocked(adopt=True)['checks']))
        d = copy.deepcopy(self.data); d['history'] = self.history(); self.retry(d)
        self.assertIn('history.evidence', str(self.blocked(d, adopt=True)['checks']))
        d['history'][0]['evidence'] = self.evidence('old.txt')
        self.blocked(d)  # --initial remains restricted to empty history.
        d['history'] = self.history(3)
        for row in d['history']: row['evidence'] = self.evidence('old.txt')
        self.assertIn('review.round_limit', str(self.blocked(d, adopt=True)['checks']))
        d['extensions'] = [{'after_round': 3, 'additional_reviews': 1, 'actor': 'user', 'evidence': self.evidence('approval.txt')}]
        self.assertEqual(self.run_plan(d, adopt=True).returncode, 0)
        d['history'][0]['evidence']['sha256'] = '0' * 64
        self.assertIn('history.evidence.sha256', str(self.blocked(d, adopt=True)['checks']))

    def test_adopt_evidence_uses_previous_directory(self):
        d = copy.deepcopy(self.data); d['history'] = self.history(); self.retry(d)
        d['history'][0]['evidence'] = self.evidence('old.txt')
        original = self.root / 'original'; original.mkdir()
        (original / 'old.txt').write_text('old.txt')
        self.previous = original / 'previous.json'; self.write(self.previous, d)
        self.assertEqual(self.run_plan(d, previous=True).returncode, 0)
        (original / 'old.txt').unlink()
        self.assertIn('history.evidence', str(self.blocked(d, previous=True)['checks']))

    def test_existing_extension_cannot_be_inflated_removed_or_rewritten(self):
        previous = copy.deepcopy(self.data); previous['history'] = self.history(3); self.retry(previous)
        extension = {'after_round': 3, 'additional_reviews': 1, 'actor': 'user', 'evidence': self.evidence('approval.txt')}
        previous['extensions'] = [extension]; self.write(self.previous, previous)
        current = copy.deepcopy(previous); current['history'] = self.history(4)
        for key, value in [('additional_reviews', 2), ('actor', 'other')]:
            d = copy.deepcopy(current); d['extensions'][0][key] = value
            result = self.blocked(d, previous=True)
            self.assertIn('extensions.append-only', str(result['checks']))
        d = copy.deepcopy(current); d['extensions'] = []; self.blocked(d, previous=True)
        current['extensions'].append({'after_round': 4, 'additional_reviews': 1, 'actor': 'user', 'evidence': self.evidence('approval.txt')})
        self.blocked(current, previous=True)
        (self.root / 'second-approval.txt').write_text('第四轮之后明确新增一轮的合成批准')
        current['extensions'][-1]['evidence'] = self.evidence('second-approval.txt')
        self.assertEqual(self.run_plan(current, previous=True).returncode, 0)

    def test_text_and_json_readonly_and_copy_install(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        d = copy.deepcopy(self.data); d['command'] = 'touch SHOULD_NOT_EXIST'
        r = self.run_plan(d, json_output=False); self.assertEqual(r.returncode, 0, r.stdout)
        self.assertFalse((self.root / 'SHOULD_NOT_EXIST').exists())
        self.assertTrue(r.stdout.startswith('READY\n')); self.assertIn('不签产品验收', r.stdout)
        for name, value in before.items(): self.assertEqual((self.root / name).read_bytes(), value)
        home = self.root / 'home'; home.mkdir()
        r = run_keel(home, 'install', '--copy')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        copied = home / '.local/bin/keel'
        self.assertEqual(self.run_plan(cli=copied).returncode, 0)
        help_run = subprocess.run([sys.executable, str(copied), 'reverify', '--help'], capture_output=True, text=True)
        self.assertEqual(help_run.returncode, 0); self.assertIn('--previous', help_run.stdout)

    def test_duplicate_keys_bad_types_and_outside_dependencies(self):
        r = self.run_plan(); file = self.root / 'plan.json'
        file.write_text('{"task_id":"task-31","task_id":"other"}')
        bad = subprocess.run(r.args, capture_output=True, text=True, cwd=self.root)
        self.assertEqual(bad.returncode, 1); self.assertEqual(json.loads(bad.stdout)['status'], 'BLOCKED')
        for key, value in [('elapsed_seconds', True), ('model_calls', -1), ('model_calls', 1.5)]:
            d = copy.deepcopy(self.data); d['budget']['planned'][key] = value; self.blocked(d)
        d = copy.deepcopy(self.data); d['items'][0]['dependencies'][0]['path'] = '../outside'
        self.blocked(d)

    def test_missing_root_is_not_a_valid_deletion_plan(self):
        d = copy.deepcopy(self.data)
        for row in d['items']:
            row['decision'] = 'rerun'
            for dep in row['dependencies']: dep['after'] = None
        self.blocked(d, extra=['--root', str(self.root / 'typo')])
        self.blocked(d, extra=['--root', str(self.root / 'ui.txt')])
        (self.root / 'algorithm.txt').unlink()
        d = copy.deepcopy(self.data); d['items'][1]['decision'] = 'rerun'; d['items'][1]['dependencies'][0]['after'] = None
        self.assertEqual(self.run_plan(d).returncode, 0)
        (self.root / 'algorithm.txt').mkdir()
        self.blocked(d)

    def test_previous_requires_versioned_identity(self):
        for key, value in [('schema_version', None), ('schema_version', 2), ('schema_version', True), ('candidate_sha', None), ('baseline_sha', 'short')]:
            previous = copy.deepcopy(self.data)
            if value is None: previous.pop(key)
            else: previous[key] = value
            self.write(self.previous, previous)
            self.blocked(previous=True)

    def test_budget_report_shows_actual_limit_planned_and_projection(self):
        r = self.run_plan(); b = json.loads(r.stdout)['budget']
        self.assertEqual(b['limits']['model_calls'], 5); self.assertEqual(b['planned']['model_calls'], 1)
        self.assertEqual(b['projected']['model_calls'], 1)
        d = copy.deepcopy(self.data); d['history'] = self.history(1); self.retry(d)
        d['budget']['limits']['model_calls'] = 1
        b = self.blocked(d, previous=True)['budget']
        self.assertEqual(b['projected']['model_calls'], 2); self.assertEqual(b['limits']['model_calls'], 1)
        r = self.run_plan(json_output=False); self.assertIn('budget:', r.stdout); self.assertIn('projected', r.stdout)

    def test_dangling_links_are_not_deletion_and_internal_regular_links_work(self):
        target = self.root / 'algorithm.txt'
        original = target.read_text(); target.unlink(); target.symlink_to('absent')
        d = copy.deepcopy(self.data); d['items'][1]['decision'] = 'rerun'
        d['items'][1]['dependencies'][0]['after'] = None
        self.blocked(d)
        target.unlink(); target.symlink_to('old.txt')
        d['items'][1]['dependencies'][0]['after'] = self.sha('old.txt')
        self.assertEqual(self.run_plan(d).returncode, 0)
        target.unlink(); target.symlink_to(self.root.parent / 'outside')
        self.blocked(d)
        target.unlink(); (self.root / 'broken-parent').symlink_to('absent-dir')
        d['items'][1]['dependencies'][0].update(path='broken-parent/file', after=None)
        self.blocked(d)
        target.write_text(original)

    def test_blocked_business_checks_keep_valid_cost_context(self):
        d = copy.deepcopy(self.data); d['history'] = self.history(); self.retry(d)
        for change in ('root', 'dependency', 'precheck'):
            value = copy.deepcopy(d); extra = ()
            if change == 'root': extra = ['--root', str(self.root / 'missing')]
            elif change == 'dependency': value['items'][0]['dependencies'][0]['after'] = '1' * 64
            else: value['prechecks'][0]['status'] = 'fail'
            r = self.blocked(value, previous=True, extra=extra)
            self.assertEqual(r['cumulative']['model_calls'], 1)
            self.assertEqual(r['budget']['limits']['elapsed_seconds'], 600)
            self.assertEqual(r['budget']['planned']['model_calls'], 1)
            self.assertEqual(r['budget']['projected']['model_calls'], 2)

    def test_overflow_is_blocked_strict_json_and_never_free(self):
        for count in (1, 2):
            d = copy.deepcopy(self.data); d['history'] = self.history(count); self.retry(d)
            for row in d['history']: row['metrics']['elapsed_seconds'] = 1e308
            d['budget']['planned']['elapsed_seconds'] = 1e308
            d['budget']['limits']['elapsed_seconds'] = 1e308
            r = self.blocked(d, previous=True)
            json.dumps(r, allow_nan=False)
            self.assertIsNone(r['budget']['projected']['elapsed_seconds'])
            if count == 2: self.assertIsNone(r['cumulative']['elapsed_seconds'])
            self.assertIn('overflow', str(r['checks']))
        d['history'][0]['metrics']['elapsed_seconds'] = 10 ** 400
        self.blocked(d, previous=True)  # Mixing a huge integer with a float also overflows.
        d = copy.deepcopy(self.data); d['budget']['limits']['elapsed_seconds'] = 1e308
        run = self.run_plan(d); file = self.root / 'plan.json'
        file.write_text(file.read_text().replace('1e+308', '1e999'))
        run = subprocess.run(run.args, capture_output=True, text=True, cwd=self.root)
        self.assertEqual(run.returncode, 1, run.stderr)
        json.loads(run.stdout, parse_constant=lambda v: self.fail(v))

    def test_inherited_extension_uses_previous_directory_not_current_shadow(self):
        previous = copy.deepcopy(self.data); previous['history'] = self.history(3); self.retry(previous)
        previous['extensions'] = [{'after_round': 3, 'additional_reviews': 1, 'actor': 'user',
                                   'evidence': self.evidence('approval.txt')}]
        old_dir = self.root / 'original'; old_dir.mkdir()
        (old_dir / 'approval.txt').write_text('approval.txt')
        self.previous = old_dir / 'previous.json'; self.write(self.previous, previous)
        (self.root / 'approval.txt').write_text('different current-directory shadow')
        self.assertEqual(self.run_plan(previous, previous=True).returncode, 0)
        (old_dir / 'approval.txt').unlink()
        (self.root / 'approval.txt').write_text('approval.txt')
        self.blocked(previous, previous=True)  # Current shadow must not replace missing old proof.
        # Multiple moves: preserve the prior record and its proof together at every hop.
        next_dir = self.root / 'second'; next_dir.mkdir()
        (next_dir / 'approval.txt').write_text('approval.txt')
        self.previous = next_dir / 'previous.json'; self.write(self.previous, previous)
        self.assertEqual(self.run_plan(previous, previous=True).returncode, 0)
        # Newly appended authorization resolves in the current directory.
        current = copy.deepcopy(previous); current['history'] = self.history(4)
        (self.root / 'new-proof.txt').write_text('new round approval')
        current['extensions'].append({'after_round': 4, 'additional_reviews': 1, 'actor': 'user',
                                      'evidence': self.evidence('new-proof.txt')})
        self.assertEqual(self.run_plan(current, previous=True).returncode, 0)

    def test_minimal_semantic_failure_examples(self):
        # Generic contract failures; these are not hospital data or an Agent eval.
        for streams, degree, adopted, resources in [(['hourly'], 'full', True, ['core', 'decoder']),
                                                   (['hourly', 'monthly'], 'failed', True, ['core', 'decoder']),
                                                   (['hourly', 'monthly'], 'full', True, ['core'])]:
            outcomes = [set(streams) == {'hourly', 'monthly'}, not adopted or degree != 'failed',
                        set(resources) == {'core', 'decoder'}]
            self.assertFalse(all(outcomes))
            d = copy.deepcopy(self.data)
            (self.root / 'semantic-check.txt').write_text(json.dumps(dict(zip(('streams', 'consumers', 'resources'), outcomes))))
            for row, passed in zip(d['prechecks'], outcomes):
                row['status'] = 'pass' if passed else 'fail'
                row['evidence'] = self.evidence('semantic-check.txt')
            self.blocked(d)
        self.assertEqual(self.run_plan().returncode, 0)


if __name__ == '__main__':
    unittest.main()
