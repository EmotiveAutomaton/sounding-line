"""Owner-gated RW1 whole-pipeline analysis with bounded, sealed draw checkpoints.

DESIGN CHECK: LESSONS 2,3. Native source completion is not marker validity.
Actual independently annotated, qualified marker receipts and exact owner review
precede any corpus projection into the estimator. Fresh replay repeats every
learned vocabulary and target, not just the final coefficient. No admission is
inferred from constructed fixtures or a copied/licensed source.
"""
from pathlib import Path
import time

import numpy as np

from . import week6_rw1_v1 as math
from . import week6_rw1_source_v1 as source
from . import week6_rw1_intake_v1 as marker
from . import week6_rw1_source_v2 as forms
from . import week6_rw1_context_v1 as context
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io
from . import week5_rr3_v1 as compare

MODULE = 'runners.drive.cards.week6_rw1_runner_v1'


def review_contract(source_complete, marker_complete, context_qualified=False):
    return {'admission': 'RW1-association-v1', 'approved': True,
        'source_complete_sha256': source_complete, 'marker_complete_sha256': marker_complete,
        'independent_real_marker_provenance_reviewed': True,
        'source_adapter_sha256': io.sha(source.__file__), 'marker_sha256': io.sha(marker.__file__),
        'math_sha256': io.sha(math.__file__), 'runner_sha256': io.sha(__file__),
        'semantic': math.SEMANTIC, 'context_sha256': io.sha(context.__file__),
        'form_adapter_sha256': io.sha(forms.__file__), 'time_place_semantics_and_provenance_reviewed': context_qualified}


def load(inputs):
    required = {'prepared_run', 'marker_review_run', 'owner_review'}
    if set(inputs) != required:
        raise ValueError('Exact RW1 preparation, marker qualification and owner review required')
    root, _, _ = seal.complete(inputs['prepared_run'], source.MODULE)
    checked, _, _ = seal.complete(inputs['marker_review_run'], forms.MODULE)
    prepared = seal.read(root / 'output/RESULT.json'); qualified = seal.read(checked / 'output/RESULT.json')
    if (prepared.get('card') != 'RW1-source' or prepared.get('complete_preparation') is not True
            or prepared.get('people') != 2500 or qualified.get('card') != 'RW1-marker-review-v2'
            or qualified.get('status') != 'reviewable'
            or qualified.get('prepared_complete_sha256') != io.sha(root / 'COMPLETE.json')
            or qualified.get('source_manifest_sha256') != prepared.get('sample_manifest_sha256')):
        raise ValueError('Actual complete source and passing independent marker receipt required')
    ident = prepared['source_identity']
    if (ident.get('module_sha256') != io.sha(source.__file__) or ident.get('marker_sha256') != io.sha(marker.__file__)
            or ident.get('source_sha256') != source.OSF_DECLARED_SHA256 or ident.get('git_blob') != source.GIT_BLOB):
        raise ValueError('Original source or qualified marker implementation differs')
    if qualified.get('context_sha256') != io.sha(context.__file__) or qualified.get('form_adapter_sha256') != io.sha(forms.__file__):
        raise ValueError('Qualified context marker or form implementation changed')
    context_qualified = qualified['context_qualification']['status'] == 'reviewable'
    expected = review_contract(io.sha(root / 'COMPLETE.json'), io.sha(checked / 'COMPLETE.json'), context_qualified)
    if seal.read(inputs['owner_review']) != expected:
        raise ValueError('Owner scientific and marker review does not bind this implementation')
    path = root / 'output/RECORDS.json'
    if io.sha(path) != prepared['files']['RECORDS.json']: raise ValueError('Prepared source projection changed')
    records = seal.read(path)['records']
    if len(records) != 2500 or sorted(r['source_row'] for r in records) != list(range(2500)):
        raise ValueError('Every original source person must remain in the prospective roster')
    return math.prepare(records, context_qualified), expected


def settings(config):
    if (set(config) - {'phase', 'draws', 'max_new_draws', 'max_wall_seconds'}
            or config.get('phase') != 'RW1' or config.get('draws', 2000) != 2000):
        raise ValueError('Exact RW1 2000-draw phase required')
    count, seconds = config.get('max_new_draws', 20), float(config.get('max_wall_seconds', 600))
    if type(count) is not int or count <= 0 or not np.isfinite(seconds) or not 0 < seconds <= 1200:
        raise ValueError('Positive bounded RW1 draw quantum required')
    return count, seconds


def operation(output, inputs, config):
    output = source.private_output(output); output.mkdir(parents=True, exist_ok=True)
    limit, seconds = settings(config); began = time.monotonic(); cpu = time.process_time()
    data, identity = load(inputs); binding = math.digest({'identity': identity, 'semantics': math.SEMANTIC})
    state = seal.state(output / 'STATE.json', binding, {'completed': 0})
    if type(state['completed']) is not int or not 0 <= state['completed'] <= 2000:
        raise ValueError('Invalid original draw checkpoint count')
    if 'point' not in state:
        state['point'] = math.estimate(data, np.ones(len(data['people'])), keep_words=True)
        state['dispositions'] = data['dispositions']; seal.checkpoint(output / 'STATE.json', state)
    point = state['point']; added = 0
    if point['targets']['worry']['status'] == 'ok':
        while state['completed'] < 2000:
            if added >= limit or source.bounded(output, began, seconds):
                io.write_json(output / 'COST.json', {'process_CPU_seconds': time.process_time() - cpu,
                    'scope': 'this invocation; native whole-family charge remains external'})
                return {'status': 'yielded', 'verified': False, 'completed': state['completed'], 'total': 2000}
            ordinal = state['completed']; draw = math.bootstrap_draw(data, ordinal)
            seal.checkpoint(output / 'draws' / f'{ordinal:05d}.json', {'binding': binding, 'ordinal': ordinal, 'draw': draw})
            state['completed'] += 1; added += 1; seal.checkpoint(output / 'STATE.json', state)
        bank = []
        for ordinal in range(2000):
            saved = seal.state(output / 'draws' / f'{ordinal:05d}.json', binding, {})
            if saved.get('ordinal') != ordinal: raise ValueError('Original draw ordinal missing')
            bank.append(saved['draw'])
        targets = math.summarize(point, bank)
    else:
        targets = {name: {**value, 'outcome': None} for name, value in point['targets'].items()}
    result = {'card': 'RW1', 'complete_computation': True, 'source_identity': identity,
        'targets': targets, 'draws': state['completed'], 'point_vocabulary_audit': point.get('vocabularies', []),
        'half_manifest_sha256': data['half_manifest_sha256'], 'dispositions': state['dispositions'],
        'literal_unknown_or_absent_plan_counts': data['literal_unknown_or_absent_plan_counts'],
        'time_place_secondary_complete': data['time_place_qualified_input'],
        'complete_card': data['time_place_qualified_input'], 'record_kind': 'claim',
        'theory_tags': ['H17-PLAN', 'STRESS-KEY'], 'by_construction': False, 'activation': [],
        'scope': 'one population, one topic, one month, one country; observational correlation; learned lexical control'}
    io.write_json(output / 'RESULT.json', result)
    io.write_json(output / 'COST.json', {'process_CPU_seconds': time.process_time() - cpu,
        'scope': 'this invocation; total native, source, preparation and fresh replay charge external'})
    return result


def execute(output, inputs, config): return operation(output, inputs, config)


def verify(output, inputs, config):
    output = source.private_output(output); result = operation(output / 'independent-replay', inputs, config)
    if result.get('status') == 'yielded': return result
    compare.compare_record(seal.read(output / 'RESULT.json'), result)
    original = sorted((output / 'draws').glob('*.json'))
    replayed = sorted((output / 'independent-replay/draws').glob('*.json'))
    original = [p for p in original if not p.name.endswith('.seal.json')]
    replayed = [p for p in replayed if not p.name.endswith('.seal.json')]
    if [p.name for p in original] != [p.name for p in replayed]: raise ValueError('Full draw replay inventory differs')
    for a, b in zip(original, replayed, strict=True): compare.compare_record(seal.read(a), seal.read(b))
    return {'verified': True, 'every_vocabulary_and_target_draw_replayed': True,
            'replay_scope': 'fresh complete reconstruction; independent dense oracle is a constructed fixture'}
