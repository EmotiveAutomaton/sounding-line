"""Prospective counted all-five-card adapter equivalence proof; not yet run.

DESIGN CHECK: LESSONS 3-5. Only the pinned, already constructed fixture sources
are accepted. Recompute all original serialized outputs and independently replay
the adapter in a fresh runtime child; exact equality is required for every card.
Separate counted pause/continue integration is also required before admission.
"""
from pathlib import Path
import json
from unittest.mock import patch
from . import week5_ch_analysis_bounded as adapter
from .week5_ch_source import digest, write_json


def cases(inputs):
    expected={'models_fixture','histories_fixture'}
    if set(inputs)!=expected:raise ValueError('Exact constructed fixture receipts required')
    roots={}
    for label,spec in inputs.items():
        path=Path(spec['path'])
        if digest(path)!=spec['sha256']:raise ValueError('Constructed receipt pin changed')
        receipt=json.loads(path.read_text(encoding='utf8'))
        if receipt.get('constructed') is not True or receipt.get('scientific_admission') is not False:
            raise ValueError('Not an original constructed native proof')
        for name,sha in receipt['source_pins'].items():
            if digest(Path(__file__).with_name(name))!=sha:raise ValueError('Original numerical source changed')
        roots[label]=path.parent
    models=roots['models_fixture'];history=roots['histories_fixture']
    for card in ('CH2','CH3','CH5'):
        config=json.loads((models/(card+'-config.json')).read_text(encoding='utf8'))
        yield card,dict(scores=dict(path=str(models/'scores'))),config,models/card/'SCIENCE.json'
    conf=json.loads((history/'CONFIG.json').read_text(encoding='utf8'))
    for card in ('CH4','CH6'):
        yield card,conf['inputs'],conf['configs'][card],history/card/'SCIENCE.json'


def execute(output,inputs,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if config!={'constructed_fixture':True}:raise ValueError('Exact fixture mode required')
    results={}
    for card,source,settings,expected in cases(inputs):
        request=adapter.requested
        with patch.object(adapter,'requested',lambda path:request(output) or request(path)):
            result=adapter.execute(output/card,source,settings)
        if result['status']=='yielded':return result
        if result['status']!='complete':raise ValueError('Constructed adapter did not complete')
        if digest(output/card/'SCIENCE.json')!=digest(expected):
            raise ValueError('Original numerical output changed for '+card)
        results[card]=dict(exact_original_science_sha256=digest(expected),callbacks=result['new_callbacks'])
    write_json(output/'FIXTURE.json',dict(passed=True,constructed=True,all_five_original_outputs_equal=True,
                                        cards=results,pause_integration_required=True))
    return dict(status='complete',constructed=True,cards=5)


def verify(output,inputs,config):
    output=Path(output)
    for card,source,settings,expected in cases(inputs):
        request=adapter.requested
        with patch.object(adapter,'requested',lambda path:request(output) or request(path)):
            result=adapter.verify(output/card,source,settings)
        if result.get('status')=='yielded':return result
        if not result['verified'] or result['restored_verification_callbacks']!=0:
            raise ValueError('Fresh independent adapter replay incomplete')
        if digest(output/card/'replay/SCIENCE.json')!=digest(expected):
            raise ValueError('Original numerical replay changed for '+card)
    return dict(verified=True,complete_recalculation=True,cards=5,constructed=True)
