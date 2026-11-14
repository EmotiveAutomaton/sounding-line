"""Constructed-only complete native intake fixture; never reads public archives.

DESIGN CHECK: LESSONS 2--5 and packet W. Literal hand answers are external to
the adapters. Exact wrong pins, incomplete review and tampered blocks must fail.
The fixture qualifies source/marker engineering, never semantic correctness,
real frequency, election identity or RF1/CP1 scientific-model sensitivity.
"""
from pathlib import Path
import gzip
import json
from . import week5_rf_cp_source_v1 as source
from . import week5_rf_cp_markers_v1 as markers
from . import week5_rf_cp_fixture_v1 as fixture
from . import week5_rf_cp_instrument_v1 as gate


def require_refusal(call):
    try:
        call()
    except ValueError:
        return True
    raise ValueError('Required refusal did not fire')


def known_answers():
    for text, expected in fixture.RF_CASES:
        got = markers.rf_counts(text)['counts']
        if tuple(got[k][p] for k in markers.RF for p in ('for', 'against')) != expected:
            raise ValueError('RF literal hand answer differs')
    for pair in fixture.CP_PAIRS:
        for text, tokens, expected in pair:
            got = markers.cp_counts(text)
            if got['tokens'] != tokens or tuple(got['counts'][k] for k in markers.CP) != expected:
                raise ValueError('CP literal hand answer differs')
    summary = {'family':'CP1', 'records':1000, 'family_hits':{k:30 for k in markers.CP}, 'source_gate':True, 'by_construction':True}
    sample = [{'family':k, 'id':str(i)} for k in markers.CP for i in range(100)]
    labels = [dict(row, correct=int(row['id']) < 80) for row in sample]
    if not markers.instrument_gate(summary, sample, labels)['admitted']:
        raise ValueError('Exact 80/100, 3% gate boundary refused')
    labels[79]['correct'] = False
    if markers.instrument_gate(summary, sample, labels)['admitted']:
        raise ValueError('Below correctness gate admitted')
    require_refusal(lambda: markers.instrument_gate(summary, sample, labels[:-1]))
    return {'RF_literal_comments': 12, 'CP_literal_pairs': 10, 'gate_boundary_and_incomplete_review': True}


def setup(output):
    path = output / 'CONSTRUCTED_INPUTS.json'
    if path.exists():
        return json.loads(path.read_text('utf8'))
    records = {}
    for family in ('RF1', 'CP1'):
        archive, salt, n = fixture.prepare(output / 'constructed-inputs' / family, family, repeat=60)
        records[family] = {'inputs': {'archive':str(archive.resolve()), 'identity_salt':str(salt.resolve())},
            'config': {'family':family, 'constructed_fixture':True,
                'fixture_archive_sha256':source.sha(archive), 'fixture_expected_records':n}}
    source.write_equal(path, records)
    return records


def execute(output, inputs, config):
    if inputs:
        raise ValueError('Constructed fixture accepts no external source inputs')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    cases = setup(output); proof = {'schema':'RF-CP-NATIVE-FIXTURE-1', 'hand_answers':known_answers(), 'families':{},
        'record_kind':'run', 'by_construction':True, 'theory_tags':[], 'scientific_admission':False}
    for family, case in cases.items():
        target = output / family
        initial = source.execute(target, case['inputs'], dict(case['config'], max_new_blocks=1))
        if not (target / 'SOURCE_COMPLETE.json').exists() and initial.get('status') != 'yielded':
            raise ValueError('Bounded source continuation was not exercised')
        first_block = source.sha(target / 'block-000000.json.gz')
        result = source.execute(target, case['inputs'], case['config'])
        if source.sha(target / 'block-000000.json.gz') != first_block:
            raise ValueError('Sealed source prefix changed')
        if not result['source_gate'] or result['scientific_admission']:
            raise ValueError('Constructed source gate differs')
        replay = source.verify(target, case['inputs'], case['config'])
        if replay.get('verified') is not True:
            raise ValueError('Full source replay missing')
        if source.execute(target, case['inputs'], case['config']) != result:
            raise ValueError('Completed source reentry changed')
        require_refusal(lambda: source.binding_for(case['inputs'], dict(case['config'], fixture_archive_sha256='0'*64)))
        proof['families'][family] = {'records':result['records'], 'source_complete_sha256':source.sha(target/'SOURCE_COMPLETE.json'),
                                    'complete_replay':True, 'closed_prefix_preserved':True, 'wrong_source_pin_refused':True}
        native=output/('constructed-native-'+family)
        if not native.exists():
            gin,gcfg=fixture.constructed_native_receipt(native,target)
            source.write_equal(output/(family+'-GATE-INPUTS.json'),{'inputs':gin,'config':gcfg})
        else:
            spec=json.loads((output/(family+'-GATE-INPUTS.json')).read_text('utf8'));gin,gcfg=spec['inputs'],spec['config']
        gated=gate.execute(output/('gate-'+family),gin,gcfg)
        if not gated['admitted'] or gated['scientific_admission']:
            raise ValueError('Actual constructed annotation gate differs')
        gate.verify(output/('gate-'+family),gin,gcfg)
        require_refusal(lambda:gate.execute(output/'wrong-scope',gin,dict(gcfg,constructed_fixture=False)))
        proof['families'][family]['complete_manual_gate_handler']=True
    source.write_equal(output/'FIXTURE.json', proof)
    return proof


def verify(output, inputs, config):
    output = Path(output)
    prior = json.loads((output/'FIXTURE.json').read_text('utf8'))
    if prior['hand_answers'] != known_answers():
        raise ValueError('Literal hand answers changed')
    cases = json.loads((output/'CONSTRUCTED_INPUTS.json').read_text('utf8'))
    for family, case in cases.items():
        proof = source.verify(output/family, case['inputs'], case['config'])
        if proof.get('verified') is not True or source.sha(output/family/'SOURCE_COMPLETE.json') != prior['families'][family]['source_complete_sha256']:
            raise ValueError('Complete native fixture replay differs')
        spec=json.loads((output/(family+'-GATE-INPUTS.json')).read_text('utf8'))
        if gate.verify(output/('gate-'+family),spec['inputs'],spec['config']).get('verified') is not True:
            raise ValueError('Independent gate handler replay differs')
    return {'verified':True, 'complete_constructed_intake_replayed':True, 'scientific_admission':False}
