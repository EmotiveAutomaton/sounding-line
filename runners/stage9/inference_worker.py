"""Restricted execution of finite inference over explicitly permitted evidence.

DESIGN CHECK: I05/X02; LESSONS 3--5. Missing evidence, exceeded budget or a
boundary violation invalidates execution. An exact fixture must match inside the
real capsule. No constructor, label store, model weights or external endpoints.
"""
import json
import time
import traceback

from . import inference
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
        if task['information_sha256'] != inference.identity(evidence):
            raise ValueError('operative information identity mismatch')
        if type(task['budget']) is not int or not 1 <= task['budget'] <= 200000:
            raise ValueError('budget outside finite capsule envelope')
        budget = inference.Budget(task['budget'])
        common = {'prior', 'observations', 'actions', 'query'}
        if len(evidence['observations']) > 128 or not 1 <= len(evidence['prior']) <= 64:
            raise ValueError('history or catalogue outside finite capsule envelope')
        if task['operation'] == 'behavioral_mixture':
            if set(evidence) != common | {'programs'}:
                raise ValueError('undeclared behavioral evidence')
            result = inference.behavioral_mixture(evidence['programs'], evidence['prior'],
                evidence['observations'], evidence['actions'], evidence['query'], budget)
        elif task['operation'] == 'inverse_planning':
            if set(evidence) != common | {'graph', 'hypotheses'}:
                raise ValueError('undeclared planning evidence')
            if len(evidence['graph']['states']) > 128 or len(evidence['graph']['support']) > 128:
                raise ValueError('graph outside finite capsule envelope')
            result = inference.inverse_planning(evidence['graph'], evidence['hypotheses'], evidence['prior'],
                evidence['observations'], evidence['actions'], evidence['query'], budget)
        else:
            raise ValueError('unrecognized finite inference operation')
        save('prediction', {**result, 'valid': True, 'information_sha256': task['information_sha256'],
                            'operation': task['operation'], 'assistance': 'explicit finite representation execution'})
        save('receipt', {'valid': True, 'wall_seconds': time.monotonic()-started,
                         'loaded_sources': loaded_sources()})
        return 0
    except Exception:
        save('error', {'valid': False, 'traceback': traceback.format_exc()})
        return 1
