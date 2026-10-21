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
        return json.loads(r.stdout) if '--json' in args else r.stdout
    def plan(name, data, expected=0, extra=(), previous=False, cli=CLI, home=None, json_output=True):
        file = root / (name + '.json'); file.write_text(json.dumps(data))
        args = ['reverify', str(file), '--task', 'example-31', '--candidate', B, '--baseline', A,
                '--items', 'ui,algorithm,resource', '--prechecks', 'streams,consumers,resources', '--root', str(root),
                '--changed-path', 'ui.txt', '--changed-path', 'resource.txt']
        args += ['--previous', str(root / 'plan.json')] if previous else ['--initial']
        if json_output: args += ['--json']
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
        result = invoke(name, args + list(extra), expected, cli, home)
        assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
        return result
    invoke('help', ['reverify', '--help'])
    good = plan('presentation-resource-unchanged-analysis', base)
    assert good['actions'][1]['decision'] == 'retain'
    plan('text', base, json_output=False)
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
    metrics = copy.deepcopy(base['budget']['planned']); metrics.update(cli_calls=2, atomic_reads=5, upstream_requests=8)
    def continuation(n):
        d = copy.deepcopy(base); d['history'] = [{'id': str(i), 'candidate_sha': A, 'kind': 'review', 'verdict': 'CHANGES_REQUESTED', 'failure_classes': ['contract'], 'metrics': metrics} for i in range(n)]
        d['retry'] = {'root_cause': 'contract gap', 'strategy_change': 'test all consumers first', 'exit_condition': 'one additional round'}
        return d
    d = continuation(1); r = plan('resume-metering-unknown', d, previous=True)
    assert r['cumulative']['input_tokens'] is None and r['cumulative']['upstream_requests'] == 8
    d['budget']['limits']['model_calls'] = 1; plan('budget-boundary', d, 1, previous=True)
    d = continuation(1); d['budget']['limits']['input_tokens'] = 100; plan('unknown-token-limit', d, 1, previous=True)
    d = continuation(3); plan('three-rounds', d, 1, previous=True)
    evidence = {'path': 'approval.txt', 'sha256': hashlib.sha256((root / 'approval.txt').read_bytes()).hexdigest()}
    d['extensions'] = [{'after_round': 3, 'additional_reviews': 1, 'actor': 'synthetic-user', 'evidence': evidence}]
    plan('one-more-round', d, previous=True)
    (root / 'plan.json').write_text(json.dumps(d))
    d['history'] += [continuation(4)['history'][-1]]; plan('fourth-exhausted', d, 1, previous=True)
    d['history'] = []; plan('cannot-clear-history', d, 1, previous=True)
    home = output / 'scratch-home'; home.mkdir()
    try:
        invoke('install-copy', ['install', '--copy'], home=home)
        copied = home / '.local/bin/keel'
        invoke('doctor', ['doctor'], cli=copied, home=home)
        invoke('copy-help', ['reverify', '--help'], cli=copied, home=home)
        plan('copy-ready', base, cli=copied, home=home)
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
