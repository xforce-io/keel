#!/usr/bin/env python3
"""Create a NEW scratch directory with synthetic reverification inputs."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', help='尚不存在的临时目录；不覆盖任何文件')
    args = parser.parse_args()
    root = Path(args.directory)
    root.mkdir(mode=0o700)
    for name in ('ui.txt', 'algorithm.txt', 'resource.txt', 'old.txt', 'precheck.txt', 'approval.txt'):
        (root / name).write_text('合成样例，仅验证合同：' + name, encoding='utf-8')
    def sha(name):
        return hashlib.sha256((root / name).read_bytes()).hexdigest()
    def evidence(name):
        return {'path': name, 'sha256': sha(name)}
    rows = []
    for name, method, changed in [('ui', 'user-path', True), ('algorithm', 'agent', False), ('resource', 'user-path', True)]:
        rows.append({'id': name, 'method': method, 'decision': 'rerun' if changed else 'retain',
                     'reason': '本轮改变了依赖' if changed else '依赖未变，保留原始运行依据',
                     'dependencies': [{'path': name + '.txt', 'before': '0' * 64 if changed else sha(name + '.txt'), 'after': sha(name + '.txt')}],
                     'old_evidence': {'candidate_sha': 'a' * 40, 'evidence': evidence('old.txt')}})
    costs = {k: 0 for k in ('elapsed_seconds', 'model_calls', 'cli_calls', 'atomic_reads', 'upstream_requests',
                            'input_tokens', 'cached_input_tokens', 'output_tokens')}
    costs.update(elapsed_seconds=10, model_calls=1, input_tokens=None, cached_input_tokens=None, output_tokens=None)
    plan = {'schema_version': 1, 'task_id': 'example-31', 'candidate_sha': 'b' * 40, 'baseline_sha': 'a' * 40,
            'items': rows, 'out_of_scope': {}, 'history': [], 'extensions': [], 'next_kind': 'review',
            'prechecks': [{'id': k, 'status': 'pass', 'candidate_sha': 'b' * 40, 'evidence': evidence('precheck.txt')}
                          for k in ('streams', 'consumers', 'resources')],
            'budget': {'limits': {'elapsed_seconds': 600, 'model_calls': 5}, 'planned': costs}}
    (root / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(root / 'plan.json')


if __name__ == '__main__':
    main()
