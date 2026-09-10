"""Discarded real-adapter readout, precision, free-generation and maximum-context pilot.

DESIGN CHECK: I03/X06/X07/X12. No scientific admission or hypothesis score is produced.
NULL: missing component, exceeded bound or changed package must be invalid.
ALTERNATIVE: all 128 options, identical-continuation ties and STOP survive real inference.
Historical 1e-6 and amended .01 precision criteria are both retained, not tuned here.
"""
import argparse
import math
import os
from pathlib import Path
import time
import uuid
import urllib.error

from runners.stage9.common import REPO, ROOT, closure, digest, freeze, read, write
from runners.stage9.runtime import execute
from runners.stage9.service_owner import resident, post


def queue_identity():
    value = os.environ.get('S9_CELL_IDENTITY')
    if value is not None and (len(value) != 64 or any(c not in '0123456789abcdef' for c in value)):
        raise ValueError('invalid actual calibration cell identity')
    return value


def completed(output, plan):
    receipt = read(output / 'COMPLETE.json')
    if (receipt.get('cell_identity') != plan['cell_identity'] or receipt.get('plan_sha256') != digest(plan)
        or not receipt.get('outputs')
        or closure([REPO / p for p in receipt['outputs']['files']]) != receipt['outputs']):
        raise ValueError('completed calibration identity or output closure changed')
    return receipt


def examples(corpus):
    cases = []
    for row in corpus['validation_choices'][:2]:
        cases.append({'name': 'genuine-' + str(len(cases)), 'evidence': {'prefix': row['prefix'], 'options': row['options']}})
    for n in (2, 13, 25, 65, 128):
        # Distinct IDs with deliberately duplicated continuation bytes test exact ties.
        options = {f'option-{i:03d}': 'STOP' for i in range(n)}
        cases.append({'name': 'identical-stop-' + str(n), 'evidence': {'prefix': 'Next action: ', 'options': options}})
    cases.append({'name': 'late-short-option', 'evidence': {'prefix': 'The next action is ',
                  'options': {**{f'o{i:03d}': 'unusual long irrelevant impossible continuation' for i in range(127)}, 'zSTOP': 'STOP'}}})
    cases.append({'name': 'distinct-maximum-support', 'evidence': {'prefix': 'Next action:\n',
                  'options': {f'a{i:03d}': f'00 write sec{i // 8 + 1} s{i // 8 + 1}.{i % 8 + 1} done' for i in range(128)}}})
    return cases


def maker_series_case(tok, limit=4096):
    from runners.stage8.constructor import population as pop
    from runners.stage8.constructor.gradient import make_world_ext
    from runners.stage8.reader import logfmt as lf
    from runners.stage7.constructor import worlds as wlib
    for i in range(100):
        world = pop.sample_world(pop.pop_lid(i, 'essay', 9960000), finish=True)
        if not world['degenerate']:
            break
    else:
        raise ValueError('no supported discarded long-series task')
    names = world['state']['names']
    ev = pop.evidence_at(world, world['cut'], {'unit_ref': 'u', 'condition_ref': 'long-pilot'})
    header, lines = lf.header_from_evidence(ev), lf.prefix_lines(ev['process_prefix'])
    options = {a: lf.event_line(world['cut'], *a.split(':')) for a in ev['query']['next_action_options']}
    maximum_tail = max(len(tok(t, add_special_tokens=False).input_ids) for t in options.values())
    earlier, lineages = [], []
    for k in range(32):
        lid = world['lid'] + '|earlier' + str(k)
        previous = make_world_ext(lid, 'essay', 'essay', goal=wlib.GOALS[k % len(wlib.GOALS)], law_name=names['law'],
                                  belief=names['belief'], residue=names['residue'], tendency=names['tendency'], finish=False)
        previous['goal_name'] = previous['state']['proximal_goal']['name_ref']
        text = pop.world_log(previous, False)
        candidate = lf.compose(earlier + [text], header, lines)
        if len(tok(candidate, add_special_tokens=True).input_ids) + maximum_tail > limit:
            break
        earlier.append(text)
        lineages.append(lid)
    prefix = lf.compose(earlier, header, lines)
    n = len(tok(prefix, add_special_tokens=True).input_ids)
    if len(earlier) < 7 or n < limit // 2:
        raise ValueError('long-context pilot did not realize a long distinct maker series')
    return {'prefix': prefix, 'options': options}, {'actual_prefix_tokens': n, 'maximum_tail_tokens': maximum_tail,
             'distinct_earlier_works': len(earlier), 'private_lineages': lineages, 'limit': limit,
             'information': 'same-maker full process records; explicit diagnostic, no artifact-only claim'}


def run(family, training, output):
    output, training = Path(output).resolve(), Path(training).resolve()
    cell_identity = queue_identity()
    complete = read(training / 'COMPLETE.json')
    adapter = training / complete['selected_checkpoint']
    adapter_closure = closure([adapter])
    if adapter_closure['sha256'] != complete['selected_checkpoint_sha256']:
        raise ValueError('selected trained checkpoint changed')
    corpus = read(ROOT / 'private/pilot' / (family + '-corpus.json'))
    cases = examples(corpus)
    plan = {'family': family, 'cell_identity': cell_identity, 'training_complete': complete, 'adapter': adapter_closure,
            'cases_sha256': digest(cases), 'sources': closure([REPO / 'runners/stage9', REPO / 'runners/readout_repair.py',
               REPO / 'runners/stage7/runtime.py', REPO / 'runners/s5_lib.py']),
            'precision_variants': ['bfloat16-cuda-b4', 'bfloat16-cuda-b1', 'float16-cuda-b4', 'float32-cpu-b4'],
            'context_limit': 4096, 'support_limit': 128, 'old_tolerance': 1e-6, 'amended_tolerance': .01,
            'scope': 'discarded finite apparatus calibration; no competence or population claim'}
    freeze(output / 'PLAN.json', plan)
    if (output / 'COMPLETE.json').exists():
        return completed(output, plan)
    predictions, diagnostics = {}, []
    started = time.time()
    for precision, device, batch in [('bfloat16', 'cuda', 4), ('bfloat16', 'cuda', 1), ('float16', 'cuda', 4), ('float32', 'cpu', 4)]:
        key = f'{precision}-{device}-b{batch}'
        config = {'family': family, 'adapter': str(adapter.resolve()), 'adapter_sha256': adapter_closure['sha256'],
                  'precision': precision, 'device': device, 'batch_size': batch, 'max_context': 4096,
                  'max_support': 128, 'max_new_tokens': 2048}
        with resident(output / 'services' / (key + '-' + uuid.uuid4().hex[:8]), config) as (ready, token):
            def measured(evidence, operation='choice', **extra):
                task = {'operation': operation, 'identity': {**ready['identity'], 'information_sha256': digest(evidence)}, **extra}
                result = execute(evidence, task, ready['endpoint'], token, root=output / 'capsules', timeout=900)
                if not result['accepted']:
                    write(output / 'FAILED_CAPSULE.json', result)
                    raise ValueError('real capsule invalid; retain failure and inspect')
                return result
            rows = {}
            for case in cases:
                result = measured(case['evidence'])
                pred = result['prediction']
                freeze(output / 'predictions' / key / (case['name'] + '.json'), result)
                if case['name'].startswith('identical-stop-'):
                    if len(pred['ties']) != len(case['evidence']['options']) or any(abs(p - 1 / len(pred['probs'])) > 1e-12 for p in pred['probs'].values()):
                        raise ValueError('real identical-continuation tie failed')
                rows[case['name']] = result
            reordered = {'prefix': cases[-1]['evidence']['prefix'], 'options': dict(reversed(list(cases[-1]['evidence']['options'].items())))}
            repeat = measured(reordered)['prediction']
            rows['permutation'] = repeat
            if rows[cases[-1]['name']]['prediction']['probs'] != repeat['probs']:
                raise ValueError('input order changed canonical real scoring')
            if key == 'bfloat16-cuda-b4':
                for kind in ('support_overflow', 'empty_continuation', 'wrong_identity'):
                    evidence = {'prefix': 'Next action: ', 'options': {'a': 'STOP'}}
                    identity = {**ready['identity'], 'information_sha256': digest(evidence)}
                    if kind == 'support_overflow':
                        evidence['options'] = {str(i): 'STOP' for i in range(129)}
                    elif kind == 'empty_continuation':
                        evidence['options']['a'] = ''
                    else:
                        identity['adapter_sha256'] = '0' * 64
                    try:
                        post(ready['endpoint'], token, '/infer', {'operation': 'score', **evidence, 'identity': identity})
                    except urllib.error.HTTPError as exc:
                        if exc.code != 422:
                            raise
                        diagnostics.append({'attack': kind, 'rejected': True})
                    else:
                        raise ValueError('invalid request was accepted: ' + kind)
                from transformers import AutoTokenizer
                tok = AutoTokenizer.from_pretrained(ready['identity']['model'], revision=ready['identity']['revision'], local_files_only=True)
                long_evidence, long_metadata = maker_series_case(tok)
                long_result = measured(long_evidence)
                freeze(output / 'LONG_CONTEXT.json', {'result': long_result, **long_metadata})
                generation = measured({'prefix': corpus['validation_choices'][0]['prefix'], 'options': {}},
                                      operation='generate', max_new_tokens=256, seed=99001)
                freeze(output / 'GENERATION.json', generation)
            predictions[key] = rows
    reference = predictions['float32-cpu-b4']
    distances = {}
    for key, rows in predictions.items():
        values = [math.fsum(abs(rows[c['name']]['prediction']['probs'][k] - reference[c['name']]['prediction']['probs'][k])
                  for k in c['evidence']['options']) / 2 for c in cases]
        maximum = max(values)
        distances[key] = {'maximum_total_variation_from_fp32_cpu': maximum,
                          'old_1e_minus6_pass': maximum <= 1e-6, 'amended_0_01_pass': maximum <= .01}
    receipt = {'plan_sha256': digest(plan), 'cell_identity': cell_identity,
               'completed_at': time.time(), 'wall_seconds': time.time() - started,
               'cases_per_variant': len(cases), 'variants': len(predictions), 'distances': distances,
               'invalidity': diagnostics, 'scope': plan['scope'],
               'precision_limit': 'finite observed fixtures; CPU/GPU comparison changes device and dtype together',
               'generation_limit': 'one discarded greedy sample; not a competence gate or historical sampled-generation reproduction',
               'outputs': closure([output / p for p in ('PLAN.json', 'predictions', 'services', 'capsules', 'LONG_CONTEXT.json', 'GENERATION.json')])}
    freeze(output / 'COMPLETE.json', receipt)
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--family', required=True, choices=['qwen', 'smollm'])
    p.add_argument('--training', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    run(a.family, a.training, a.output)
