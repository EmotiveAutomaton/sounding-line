"""Frozen human-review gate, requiring an actual fully verified source receipt.

DESIGN CHECK: LESSONS 2--5. Missing/incomplete source or review always refuses.
>=3% frequency and >=80 correct of exactly100 apply under null and alternative.
This handler licenses the lexical instrument only; it never licenses science.
"""
from pathlib import Path
import json
from . import week5_rf_cp_source_v1 as source
from . import week5_rf_cp_markers_v1 as markers


def read(path):
    return json.loads(Path(path).read_text('utf8'))


def load(inputs, config):
    native = Path(inputs['source_native_root']); output = native/'output'
    complete = read(native/'COMPLETE.json'); verified = read(native/'VERIFIED.json'); plan = read(native/'PLAN.json')
    if source.sha(native/'COMPLETE.json') != config['source_native_complete_sha256']:
        raise ValueError('Native source completion changed')
    if complete.get('status') != 'COMPLETE' or complete.get('fresh_process_verified') is not True or verified.get('verified') is not True:
        raise ValueError('Native source is not fully independently verified')
    if plan.get('module') != 'runners.drive.cards.week5_rf_cp_source_v1':
        raise ValueError('Wrong source producer')
    names = ['PLAN.json', 'VERIFIED.json'] + ['output/'+n for n in
        ('BINDING.json','SOURCE_COMPLETE.json','SOURCE_VERIFIED.json','SUMMARY.json','REVIEW_PRIVATE.json')]
    if any(complete['outputs'].get(n) != source.sha(native/n) for n in names):
        raise ValueError('Native source output pin changed')
    binding = read(output/'BINDING.json'); proof = read(output/'SOURCE_VERIFIED.json')
    if binding['source_module_sha256'] != source.sha(source.__file__) or binding['marker_module_sha256'] != source.sha(markers.__file__):
        raise ValueError('Qualified source instrument identity changed')
    if binding['constructed_fixture'] != bool(config.get('constructed_fixture')):
        raise ValueError('Constructed versus human source mismatch')
    if proof.get('verified') is not True or proof['source_complete_sha256'] != source.sha(output/'SOURCE_COMPLETE.json') or proof['binding_sha256'] != source.sha(output/'BINDING.json'):
        raise ValueError('Complete source replay proof mismatch')
    annotation = Path(inputs['annotations'])
    if source.sha(annotation) != config['annotations_sha256']:
        raise ValueError('Frozen manual annotations changed')
    review = read(annotation)
    required_method = 'constructed_labels' if binding['constructed_fixture'] else 'manual_private_read'
    if review.get('method') != required_method or not review.get('reviewer') or review.get('private_review_sha256') != source.sha(output/'REVIEW_PRIVATE.json'):
        raise ValueError('Manual review provenance missing or changed')
    if any(not isinstance(row.get('reason'),str) or not row['reason'].strip() for row in review['labels']):
        raise ValueError('Every private judgment requires a reason')
    summary, sample = read(output/'SUMMARY.json'), read(output/'REVIEW_PRIVATE.json')
    if summary['family'] != config['family'] or summary['family'] != binding['family']:
        raise ValueError('Review family changed')
    return summary, sample, review['labels']


def execute(output, inputs, config):
    summary, sample, labels = load(inputs, config)
    result = markers.instrument_gate(summary, sample, labels)
    result.update(scientific_admission=False, admission_scope='lexical_instrument_only',
        source_native_complete_sha256=config['source_native_complete_sha256'], annotations_sha256=config['annotations_sha256'])
    source.write_equal(Path(output)/'INSTRUMENT.json',result)
    return result


def verify(output, inputs, config):
    # Independent counting implementation, not a call to instrument_gate.
    summary, sample, labels = load(inputs, config)
    expected = [(x['family'],x['id']) for x in sample]
    actual = [(x['family'],x['id']) for x in labels]
    if len(set(expected)) != len(expected) or len(set(actual)) != len(actual) or sorted(expected) != sorted(actual):
        raise ValueError('Independent adjudication roster differs')
    if any(type(row.get('correct')) is not bool for row in labels):
        raise ValueError('Independent review is incomplete')
    result = read(Path(output)/'INSTRUMENT.json'); passes=[]
    for family in markers.families(summary['family']):
        rows=[row for row in labels if row['family']==family]
        frequency=summary['family_hits'][family]/summary['records'] if summary['records'] else 0
        correct=len([row for row in rows if row['correct']])
        passed=len(rows)==100 and correct>=80 and frequency>=.03
        if result['details'][family] != {'reviewed':len(rows),'correct':correct,'frequency':frequency,'pass':passed}:
            raise ValueError('Independent instrument arithmetic differs')
        passes.append(passed)
    if result['admitted'] != (bool(summary['source_gate']) and all(passes)) or result['scientific_admission'] is not False:
        raise ValueError('Independent instrument verdict differs')
    return {'verified':True,'complete_manual_gate_arithmetic_replayed':True,'semantic_labels_rejudged':False,'scientific_admission':False}
