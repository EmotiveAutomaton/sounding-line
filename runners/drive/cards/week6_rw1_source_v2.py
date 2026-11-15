"""Successor marker forms/review over V1's unchanged original sentence sample.

DESIGN CHECK: LESSONS 2,3. Source V1 and its qualified fixtures stay immutable.
This successor adds the prospective time/place column to the same 200 rows.
Blank or constructed receipts cannot prove independent real annotations; every
reviewable result still needs owner provenance and semantic review.
"""
from . import week6_rw1_source_v1 as source
from . import week6_rw1_context_v1 as context
from . import week6_rw1_intake_v1 as marker

seal, io = source.seal, source.io
MODULE = 'runners.drive.cards.week6_rw1_source_v2'


def prepared(root):
    root, _, _ = seal.complete(root, source.MODULE); result = seal.read(root / 'output/RESULT.json')
    if result.get('card') != 'RW1-source' or result.get('complete_preparation') is not True:
        raise ValueError('Complete unchanged V1 original source required')
    if (result['source_identity']['module_sha256'] != io.sha(source.__file__)
            or result['source_identity']['marker_sha256'] != io.sha(marker.__file__)):
        raise ValueError('Qualified V1 source or plan marker changed')
    sample = seal.read(root / 'output/SAMPLE.json')['sentences']; binding = marker.manifest_digest(sample)
    if binding != result['sample_manifest_sha256']: raise ValueError('Unchanged original 200 sentences required')
    return root, sample, binding


def annotation_form(sample, binding, kind):
    form = source.annotation_form(sample, binding, kind)
    form.update(schema='RW1-independent-marker-forms-v2', context_version=context.VERSION,
                context_sha256=io.sha(context.__file__), form_adapter_sha256=io.sha(__file__))
    form['guidance'] += (' Also judge whether the plan specifies a time or place in meaning; '
                        'use unknown if unclear.' if kind == 'hand'
                        else ' Also apply the finite time/place list; literal unmatched is false.')
    for row in form['annotations']: row['time_place_label'] = None
    return form


def read_form(path, sample, binding, kind):
    form, hashed = source.read_form(path, sample, binding, kind)
    if (form.get('schema') != 'RW1-independent-marker-forms-v2'
            or form.get('context_version') != context.VERSION or form.get('context_sha256') != io.sha(context.__file__)
            or form.get('form_adapter_sha256') != io.sha(__file__)):
        raise ValueError('Time/place schema or pinned implementation differs')
    if any(type(r.get('time_place_label')) is not bool and not (kind == 'hand' and r.get('time_place_label') == 'unknown')
           for r in form['annotations']):
        raise ValueError('Every time/place column needs a real label or explicit hand unknown')
    return form, hashed


def review(inputs):
    if set(inputs) != {'prepared_run', 'builder_a_hand', 'builder_a_list', 'builder_b_hand', 'builder_b_list'}:
        raise ValueError('Original preparation and two complete hand/list pairs required')
    root, sample, binding = prepared(inputs['prepared_run']); receipts = []; pairs = []; hashes = {}
    for prefix in ('builder_a', 'builder_b'):
        hand, hh = read_form(inputs[prefix + '_hand'], sample, binding, 'hand')
        listed, lh = read_form(inputs[prefix + '_list'], sample, binding, 'list')
        if hand['builder_id'] != listed['builder_id'] or listed.get('hand_receipt_sha256') != hh:
            raise ValueError('Each list must bind its independently sealed hand form')
        hashes[prefix] = {'hand': hh, 'list': lh}; pairs.append((hand, listed))
        receipts.append({'builder_id': hand['builder_id'], 'manifest_sha256': binding, 'marker_version': marker.VERSION,
            'revision': 0, 'independently_annotated': True,
            'provenance_sha256': source.digest({'hand': hand['provenance_sha256'], 'list': listed['provenance_sha256'], 'files': hashes[prefix]}),
            'annotations': [{'id': s['id'], 'by_hand': h['label'], 'by_list': l['label']}
                            for s, h, l in zip(sample, hand['annotations'], listed['annotations'], strict=True)]})
    return {'card': 'RW1-marker-review-v2', **marker.qualification(sample, *receipts),
        'context_qualification': context.qualification(sample, pairs),
        'context_sha256': io.sha(context.__file__), 'form_adapter_sha256': io.sha(__file__),
        'form_sha256': hashes, 'prepared_complete_sha256': io.sha(root / 'COMPLETE.json'),
        'record_kind': 'run', 'theory_tags': [], 'by_construction': False, 'activation': []}


def operation(output, inputs, config):
    output = source.private_output(output); output.mkdir(parents=True, exist_ok=True)
    if config == {'phase': 'RW1-marker-forms-v2'} and set(inputs) == {'prepared_run'}:
        root, sample, binding = prepared(inputs['prepared_run'])
        for kind in ('hand', 'list'): seal.checkpoint(output / (kind.upper() + '_FORM.json'), annotation_form(sample, binding, kind))
        result = {'card': 'RW1-marker-forms-v2', 'complete_preparation': True, 'sample_manifest_sha256': binding,
            'prepared_complete_sha256': io.sha(root / 'COMPLETE.json'), 'independent_annotations_complete': False,
            'files': {kind: io.sha(output / (kind.upper() + '_FORM.json')) for kind in ('hand', 'list')},
            'production_admitted': False, 'human_outcomes_computed': False}
    elif config == {'phase': 'RW1-marker-review-v2'}: result = review(inputs)
    else: raise ValueError('Exact successor forms or marker-review phase required')
    io.write_json(output / 'RESULT.json', result); return result


def execute(output, inputs, config): return operation(output, inputs, config)


def verify(output, inputs, config):
    output = source.private_output(output); result = operation(output / 'independent-replay', inputs, config)
    if seal.read(output / 'RESULT.json') != result: raise ValueError('Successor forms/marker replay differs')
    return {'verified': True, 'independence_and_semantics_require_owner_review': True, 'human_outcomes_computed': False}
