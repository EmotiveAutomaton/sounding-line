"""Reviewed standard-library capsule entrypoint; no data, constructor or model imports.

DESIGN CHECK: Stage 9 I03/X02/X06 and LESSONS sections 3–5.
NULL: outside-file reads/writes or missing choice components fail the package.
ALTERNATIVE: complete all-option evidence yields the same distribution in every order.
The inference endpoint supplies likelihoods, never evaluator truth or an outcome label.
"""
import hashlib
import json
import os
import socket
import sys
import time
import traceback
import urllib.request

from .readout import readout
from . import features


def save(name, value):
    with open('out/' + name + '.json', 'w', encoding='utf-8') as out:
        json.dump(value, out, ensure_ascii=False, sort_keys=True, allow_nan=False)


def request_timeout(task):
    value=task.get('request_timeout_seconds',600)
    if type(value) is not int or value not in (600,1800):raise ValueError('undeclared bounded request deadline')
    if value==1800 and (task.get('operation')!='choice' or task.get('identity',{}).get('device')!='cpu'
        or task['identity'].get('precision')!='float32'):
        raise ValueError('long request deadline is only for FP32 CPU scoring')
    return value


def request(payload,timeout=600):
    data = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8')
    if len(data) > 2 * 1024**2:
        raise ValueError('request outside frozen transport envelope')
    endpoint = os.environ['S7_ENDPOINT']
    req = urllib.request.Request(endpoint + '/infer', data, {
        'Content-Type': 'application/json', 'Authorization': 'Bearer ' + os.environ['S7_TOKEN']})
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=timeout) as response:
        raw = response.read(4 * 1024**2 + 1)
        if len(raw) > 4 * 1024**2:
            raise ValueError('response outside frozen transport envelope')
        return json.loads(raw)


def probe(task):
    attempts = []
    def attempt(name, call):
        try:
            result = call()
            if hasattr(result, 'close'):
                result.close()
            attempts.append({'name': name, 'denied': False})
        except RuntimeError as exc:
            attempts.append({'name': name, 'denied': str(exc).startswith('capsule boundary:'), 'error': str(exc)})
        except Exception as exc:
            # Missing files or OS access errors cannot masquerade as capsule denial.
            attempts.append({'name': name, 'denied': False, 'error': repr(exc)})
    for i, path in enumerate(task['forbidden_paths']):
        attempt('read_' + str(i), lambda p=path: open(p, 'rb'))
        attempt('write_' + str(i), lambda p=path: open(p, 'r+b'))
    for module in ('runners', 'soundingline', 'torch', 'ctypes', 'subprocess'):
        attempt('import_' + module, lambda m=module: __import__(m))
    attempt('other_loopback', lambda: socket.create_connection(('127.0.0.1', task['other_port']), timeout=1))
    attempt('external_network', lambda: socket.create_connection(('192.0.2.1', 443), timeout=1))
    attempt('environment_mutation', lambda: os.putenv('S9_FIXTURE', 'denied'))
    return {'all_raised': bool(attempts) and all(a['denied'] for a in attempts), 'attempts': attempts,
            'sys_path': sys.path, 'env_keys': sorted(os.environ), 'mechanism': 'CPython audit-hook boundary; not OS file isolation'}


def run(task, evidence):
    if task['operation'] == 'copy_baseline':
        if set(evidence) != {'prefix', 'options'} or not task['copy_source'] or task['copy_source'] not in evidence['prefix']:
            raise ValueError('copied-text rival source must be an exact part of permitted evidence')
        return {'valid': True, 'probs': features.copy_probabilities(task['copy_source'], evidence['options']),
                'method': 'fixed character similarity copied-text rival; temperature coefficient 8; uniform mixture .01'}
    if task['operation'] == 'text_baseline':
        parameters = task['parameters']
        sha = hashlib.sha256(json.dumps(parameters, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
        if sha != task['parameters_sha256']:
            raise ValueError('baseline parameter hash mismatch')
        return {'valid': True, 'probs': features.predict(evidence, parameters),
                'parameters_sha256': sha, 'view': task['view']}
    if set(evidence) != {'prefix', 'options'}:
        raise ValueError('reader receives only its explicit prefix and complete support')
    identity = task['identity']
    sha = hashlib.sha256(json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    if sha != identity['information_sha256']:
        raise ValueError('evidence identity mismatch')
    timeout=request_timeout(task)
    if task['operation'] == 'choice':
        def score(prefix, options):
            result = request({'operation': 'score', 'prefix': prefix, 'options': options, 'identity': identity},timeout=timeout)
            if result.get('identity') != identity or result.get('valid') is not True:
                raise ValueError('model service returned an invalid or different package')
            return result['components']
        return readout(evidence['prefix'], evidence['options'], score, identity)
    if task['operation'] == 'generate':
        if evidence['options']:
            raise ValueError('free generation does not receive an offered action set')
        result = request({'operation': 'generate', 'prefix': evidence['prefix'], 'identity': identity,
                          'max_new_tokens': task['max_new_tokens'], 'seed': task['seed']})
        if result.get('identity') != identity or result.get('valid') is not True:
            raise ValueError('invalid generation package')
        return result
    raise ValueError('unsupported operation')


def main():
    started = time.monotonic()
    try:
        with open('task.json', encoding='utf-8') as src:
            task = json.load(src)
        if task.get('probe'):
            save('receipt', probe(task))
        else:
            with open('evidence.json', encoding='utf-8') as src:
                evidence = json.load(src)
            result = run(task, evidence)
            if result.get('valid') is not True:
                raise ValueError(result.get('reason', 'invalid prediction'))
            save('prediction', result)
            save('receipt', {'valid': True, 'wall_seconds': time.monotonic() - started,
                             'loaded_sources': loaded_sources()})
        return 0
    except Exception:
        save('error', {'valid': False, 'traceback': traceback.format_exc()})
        return 1


def loaded_sources():
    result = {}
    for name, module in list(sys.modules.items()):
        path = getattr(module, '__file__', None)
        if path and name.split('.')[0] == 'reader':
            with open(path, 'rb') as src:
                result[name] = hashlib.sha256(src.read()).hexdigest()
    return result
