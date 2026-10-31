"""Drive current and copy-installed CLI using retained synthetic inputs and raw outputs."""
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'bin/keel'
A, B = 'a' * 40, 'b' * 40


def main():
    output = Path(sys.argv[1]).resolve(); output.mkdir(parents=True)
    root = output / 'inputs'
    subprocess.run([sys.executable, str(ROOT / 'skills/keel-verify/examples/reverify/make_example.py'), str(root)], check=True, capture_output=True)
    base = json.loads((root / 'plan.json').read_text())
    records = []
    def invoke(name, args, expected=0, cli=CLI, home=None):
        command = [sys.executable, str(cli)] + (['--home', str(home)] if home else []) + args
        r = subprocess.run(command, capture_output=True, text=True, cwd=root)
        (output / (name + '.stdout')).write_text(r.stdout)
        (output / (name + '.stderr')).write_text(r.stderr)
        assert r.returncode == expected, (name, r.returncode, r.stdout, r.stderr)
        records.append({'name': name, 'argv': command, 'exit': r.returncode})
        return json.loads(r.stdout, parse_constant=lambda v: (_ for _ in ()).throw(AssertionError(v))) if '--json' in args else r.stdout
    def plan(name, data, expected=0, extra=(), previous=False, cli=CLI, home=None, json_output=True, adopt=False):
        file = root / (name + '.json'); file.write_text(json.dumps(data))
        args = ['reverify', str(file), '--task', 'example-31', '--candidate', B, '--baseline', A,
                '--items', 'ui,algorithm,resource', '--prechecks', 'streams,consumers,resources', '--root', str(root),
                '--changed-path', 'ui.txt', '--changed-path', 'resource.txt']
        args += ['--previous', str(root / 'plan.json')] if previous else (['--adopt-history'] if adopt else ['--initial'])
        if json_output: args += ['--json']
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
        result = invoke(name, args + list(extra), expected, cli, home)
        assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
        return result
    invoke('help', ['reverify', '--help'])
    good = plan('presentation-resource-unchanged-analysis', base)
    assert good['actions'][1]['decision'] == 'retain'
    plan('text', base, json_output=False)
    assert good['budget']['limits']['model_calls'] == 5 and good['budget']['projected']['model_calls'] == 1
    deleted = copy.deepcopy(base)
    for row in deleted['items']:
        row['decision'] = 'rerun'
        for dep in row['dependencies']: dep['after'] = None
    blocked = plan('missing-root-is-not-deletion', deleted, 1, extra=['--root', str(root / 'missing')])
    assert blocked['budget'] == good['budget'] and blocked['cumulative'] == good['cumulative']
    invalid_previous = copy.deepcopy(base); invalid_previous.pop('schema_version')
    (root / 'plan.json').write_text(json.dumps(invalid_previous))
    plan('previous-version-required', base, 1, previous=True)
    (root / 'plan.json').write_text(json.dumps(base))
    d = copy.deepcopy(base); d['items'][1]['dependencies'][0]['before'] = '0' * 64; d['items'][1]['decision'] = 'rerun'
    plan('algorithm-changed', d)
    d = copy.deepcopy(base); d['items'][1]['decision'] = 'rerun'; plan('redundant-agent', d, 1)
    plan('explicit-required-agent', d, extra=['--require-agent', 'algorithm'])
    for streams, degree, adopted, resources in [(['hourly'], 'full', True, ['core', 'decoder']),
                                               (['hourly', 'monthly'], 'failed', True, ['core', 'decoder']),
                                               (['hourly', 'monthly'], 'full', True, ['core'])]:
        checks = {'streams': set(streams) == {'hourly', 'monthly'}, 'consumers': not adopted or degree != 'failed',
                  'resources': set(resources) == {'core', 'decoder'}}
        failed = next(k for k, value in checks.items() if not value)
        evidence_file = root / ('observed-' + failed + '.txt'); evidence_file.write_text(json.dumps(checks))
        proof = {'path': evidence_file.name, 'sha256': hashlib.sha256(evidence_file.read_bytes()).hexdigest()}
        d = copy.deepcopy(base)
        for row in d['prechecks']:
            row.update(status='pass' if checks[row['id']] else 'fail', evidence=proof)
        plan('precheck-' + failed, d, 1)
    # Damaged links are existing entries, never deleted files. Valid internal links remain usable.
    original = (root / 'algorithm.txt').read_bytes()
    (root / 'algorithm.txt').unlink(); (root / 'algorithm.txt').symlink_to('missing-target')
    d = copy.deepcopy(base); d['items'][1]['decision'] = 'rerun'; d['items'][1]['dependencies'][0]['after'] = None
    plan('dangling-link-not-deletion', d, 1)
    (root / 'algorithm.txt').unlink(); (root / 'algorithm.txt').symlink_to('old.txt')
    d['items'][1]['dependencies'][0]['after'] = hashlib.sha256((root / 'old.txt').read_bytes()).hexdigest()
    plan('valid-internal-link', d)
    (root / 'algorithm.txt').unlink(); (root / 'algorithm.txt').write_bytes(original)
    metrics = copy.deepcopy(base['budget']['planned']); metrics.update(cli_calls=2, atomic_reads=5, upstream_requests=8)
    def continuation(n):
        d = copy.deepcopy(base); d['history'] = [{'id': str(i), 'candidate_sha': A, 'kind': 'review', 'verdict': 'CHANGES_REQUESTED', 'failure_classes': ['contract'], 'metrics': copy.deepcopy(metrics)} for i in range(n)]
        d['retry'] = {'root_cause': 'contract gap', 'strategy_change': 'test all consumers first', 'exit_condition': 'one additional round'}
        return d
    d = continuation(1); r = plan('resume-metering-unknown', d, previous=True)
    assert r['cumulative']['input_tokens'] is None and r['cumulative']['upstream_requests'] == 8
    d = continuation(1)
    d['history'][0]['metrics'].update(atomic_reads=None, upstream_requests=None)
    d['budget']['planned'].update(atomic_reads=None, upstream_requests=None)
    d['history'][0]['evidence'] = {'path': 'old.txt', 'sha256': hashlib.sha256((root / 'old.txt').read_bytes()).hexdigest()}
    r = plan('40-adopt-unknown-unlimited', d, adopt=True)
    assert all(r['cumulative'][key] is None and r['budget']['projected'][key] is None for key in ('atomic_reads', 'upstream_requests'))
    for key in ('atomic_reads', 'upstream_requests'):
        limited = copy.deepcopy(d); limited['budget']['limits'][key] = 100
        r = plan('40-unknown-limited-' + key, limited, 1, adopt=True)
        assert any(check['field'] == 'budget.unknown.' + key for check in r['checks'])
    missing = copy.deepcopy(d); missing['history'][0]['evidence']['path'] = 'missing-review.txt'
    plan('40-missing-review-evidence', missing, 1, adopt=True)
    r = plan('40-initial-rejects-history', d, 1)
    assert any('--adopt-history' in check['field'] for check in r['checks'])
    (root / 'plan.json').write_text(json.dumps(d))
    plan('40-adopted-history-continuation', d, previous=True)
    altered = copy.deepcopy(d); altered['history'] = []
    plan('40-no-history-reset', altered, 1, previous=True)
    (root / 'plan.json').write_text(json.dumps(base))
    three = continuation(3)
    for row in three['history']: row['evidence'] = d['history'][0]['evidence']
    plan('40-three-round-limit', three, 1, adopt=True)
    three['extensions'] = [{'after_round': 3, 'additional_reviews': 1, 'actor': 'synthetic-user',
                            'evidence': {'path': 'approval.txt', 'sha256': hashlib.sha256((root / 'approval.txt').read_bytes()).hexdigest()}}]
    plan('40-authorized-extension', three, adopt=True)
    d['budget']['limits']['model_calls'] = 1; boundary = plan('budget-boundary', d, 1, previous=True)
    assert boundary['budget']['limits']['model_calls'] == 1 and boundary['budget']['projected']['model_calls'] == 2
    d = continuation(1); d['budget']['limits']['input_tokens'] = 100; plan('unknown-token-limit', d, 1, previous=True)
    for count in (1, 2):
        overflow = continuation(count)
        for row in overflow['history']: row['metrics']['elapsed_seconds'] = 1e308
        overflow['budget']['planned']['elapsed_seconds'] = 1e308
        overflow['budget']['limits']['elapsed_seconds'] = 1e308
        result = plan('finite-sum-overflow-' + str(count), overflow, 1, previous=True)
        assert result['budget']['projected']['elapsed_seconds'] is None
    bad = continuation(1); bad['prechecks'][0]['status'] = 'fail'
    result = plan('failed-precheck-keeps-costs', bad, 1, previous=True)
    assert result['budget']['projected']['model_calls'] == 2 and result['cumulative']['model_calls'] == 1
    d = continuation(3); plan('three-rounds', d, 1, previous=True)
    evidence = {'path': 'approval.txt', 'sha256': hashlib.sha256((root / 'approval.txt').read_bytes()).hexdigest()}
    d['extensions'] = [{'after_round': 3, 'additional_reviews': 1, 'actor': 'synthetic-user', 'evidence': evidence}]
    plan('one-more-round', d, previous=True)
    for folder in ('prior-location', 'next-location'):
        previous_dir = root / folder; previous_dir.mkdir()
        (previous_dir / 'previous.json').write_text(json.dumps(d))
        (previous_dir / 'approval.txt').write_bytes((root / 'approval.txt').read_bytes())
        plan('cross-directory-' + folder, d, previous=True,
             extra=['--previous', str(previous_dir / 'previous.json')])
    (previous_dir / 'approval.txt').unlink()
    plan('current-proof-cannot-replace-old', d, 1, previous=True,
         extra=['--previous', str(previous_dir / 'previous.json')])
    (root / 'plan.json').write_text(json.dumps(d))
    d['history'] += [continuation(4)['history'][-1]]; plan('fourth-exhausted', d, 1, previous=True)
    inflated = copy.deepcopy(d); inflated['extensions'][0]['additional_reviews'] = 2
    plan('cannot-inflate-old-extension', inflated, 1, previous=True)
    extended = copy.deepcopy(d); extended['extensions'].append({'after_round': 4, 'additional_reviews': 1, 'actor': 'synthetic-user', 'evidence': evidence})
    plan('cannot-reuse-old-authorization', extended, 1, previous=True)
    second = root / 'second-approval.txt'; second.write_text('合成批准：第四轮后追加一轮')
    extended['extensions'][-1]['evidence'] = {'path': second.name, 'sha256': hashlib.sha256(second.read_bytes()).hexdigest()}
    plan('new-boundary-authorization', extended, previous=True)
    d['history'] = []; plan('cannot-clear-history', d, 1, previous=True)
    home = output / 'scratch-home'; home.mkdir()
    try:
        invoke('install-copy', ['install', '--copy'], home=home)
        copied = home / '.local/bin/keel'
        invoke('doctor', ['doctor'], cli=copied, home=home)
        invoke('copy-help', ['reverify', '--help'], cli=copied, home=home)
        plan('copy-ready', base, cli=copied, home=home)
        adopted = continuation(1); adopted['history'][0]['evidence'] = {'path': 'old.txt', 'sha256': hashlib.sha256((root / 'old.txt').read_bytes()).hexdigest()}
        plan('copy-adopt-history', adopted, cli=copied, home=home, adopt=True)
        d = copy.deepcopy(base); d['prechecks'][0]['status'] = 'fail'; plan('copy-blocked', d, 1, cli=copied, home=home)
        for name in ('keel-dev', 'keel-verify', 'keel-review'):
            body = (home / '.local/share/agent-skills/library' / name / 'SKILL.md').read_text()
            assert '复验准备合同' in body
    finally:
        invoke('uninstall', ['uninstall'], home=home)
    result = {'candidate': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'kind': 'synthetic CLI E2E; no business Agent execution', 'records': records,
              'allAssertions': True, 'modelRunsExecutedByPlan': 0}
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({'candidate': result['candidate'], 'commands': len(records), 'allAssertions': True}))


if __name__ == '__main__': main()
