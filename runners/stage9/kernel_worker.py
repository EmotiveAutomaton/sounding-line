"""Restricted numeric-program worker. No constructor import or truth access."""
import hashlib
import json
import time
import traceback

from . import kernel
from .base import loaded_sources, probe, save


def main():
    started = time.monotonic()
    try:
        with open('task.json', encoding='utf-8') as stream:
            task = json.load(stream)
        if task.get('probe'):
            save('receipt', probe(task))
            return 0
        with open('evidence.json', encoding='utf-8') as stream:
            evidence = json.load(stream)
        if set(evidence) != {'programs', 'weights', 'support'} or task.get('operation') != 'execute_program_mixture':
            raise ValueError('explicit program, weights and full support required')
        sha = hashlib.sha256(json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if task['information_sha256'] != sha:
            raise ValueError('operative information differs from frozen identity')
        programs, support = evidence['programs'], evidence['support']
        if not 1 <= len(programs) <= 64 or not 1 <= len(support) <= 128 or len(set(support)) != len(support):
            raise ValueError('program or support count outside finite kernel envelope')
        expected_support = {'stop'} | {kernel.action_id(a) for p in programs for a in p['pending']}
        if set(support) != expected_support:
            raise ValueError('missing or spurious candidate-program action support')
        probs = kernel.mixture(programs, evidence['weights'])
        result = {'valid': True, 'probs': {k: probs.get(k, 0.) for k in support},
                  'information_sha256': sha, 'kernel_version': kernel.VERSION,
                  'operation': task['operation'], 'assistance': 'explicit numeric candidate-program execution'}
        save('prediction', result)
        save('receipt', {'valid': True, 'wall_seconds': time.monotonic()-started, 'loaded_sources': loaded_sources()})
        return 0
    except Exception:
        save('error', {'valid': False, 'traceback': traceback.format_exc()})
        return 1
