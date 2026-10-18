"""Original parity, canonical mutation, grouped controls and actual full replay."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from threadpoolctl import threadpool_limits

from runners.drive.cards import menus_d2_canonical as c
from runners.drive.cards.menus_io import read, write, sha256, assert_equal
from tests.test_drive_cards_menus_d2_diagnostic import fixture
from tests.test_drive_cards_menus_d2 import test_null_and_planted_choice_rule, test_gradient_and_probability_oracle


def test_original_exact_parity_and_future_label_invariance(tmp_path):
    inputs=fixture(tmp_path/'source');data=c.source.load(inputs); split=data['splits']['w0']
    original,_,_=c.old.load(inputs)
    assert set(original)==set(data['cases'])
    for key,case in data['cases'].items():
        assert case['truth']!=original[key]['truth']
        assert np.array_equal(case['x'],original[key]['x'])
        assert np.array_equal(case['embeddings'],original[key]['embeddings'])
        assert case['dissimilarity']==original[key]['dissimilarity']
    with threadpool_limits(limits=1):
        prepared=c.prepare(split,data['cases'],c.CONFIG['fit'])
        arms={arm:c.fit_arm(prepared,c.targets(data['cases'],arm,c.CONFIG),c.CONFIG['fit']) for arm in ('primary','uniform_control')}
        assert_equal(dict(prepared[2],arms=arms),c.old.fit_recipient(split,data['cases'],c.CONFIG['fit']))
        altered=copy.deepcopy(data['cases'])
        for session in split['test']:
            for row in session['rows']: altered[row['key']]['truth']=1-altered[row['key']]['truth']
        newprepared=c.prepare(split,altered,c.CONFIG['fit'])
        assert_equal(prepared[2],newprepared[2])
        fitted=c.fit_arm(newprepared,c.targets(altered,'primary',c.CONFIG),c.CONFIG['fit'])
        assert fitted['beta']==arms['primary']['beta'] and fitted['penalty']==arms['primary']['penalty']
        assert fitted['predictions']!=arms['primary']['predictions']


def test_every_permutation_preserves_writer_size_counts_and_order():
    cases={f'{w}-{n}-{i}':dict(key=f'{w}-{n}-{i}',writer=w,x=np.zeros((n,1)),truth=i%n)
           for w in ('a','b','c') for n in (2,3,5) for i in range(17)}
    from collections import Counter
    for draw in range(200):
        targets=c.targets(cases,draw,c.CONFIG)
        assert targets==c.targets(dict(reversed(list(cases.items()))),draw,c.CONFIG)
        for writer in ('a','b','c'):
            for size in (2,3,5):
                keys=[k for k,v in cases.items() if v['writer']==writer and len(v['x'])==size]
                assert Counter(targets[k] for k in keys)==Counter(cases[k]['truth'] for k in keys)
    assert c.targets(cases,0,c.CONFIG)!=c.targets(cases,1,c.CONFIG)
    with pytest.raises(ValueError): c.targets(cases,True,c.CONFIG)


def complete_pilot(root,inputs):
    c.execute(root/'output',inputs,c.CONFIG); c.verify(root/'output',inputs,c.CONFIG)
    write(root/'PLAN.json',dict(module='runners.drive.cards.menus_d2_canonical',config=c.CONFIG,synthetic_fixture=True))
    write(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,synthetic_fixture=True,
        outputs={p.relative_to(root).as_posix():sha256(p) for p in root.rglob('*') if p.is_file()}))
    return inputs|dict(pilot_plan=str(root/'PLAN.json'),pilot_complete=str(root/'COMPLETE.json'),pilot_summary=str(root/'output/SUMMARY.json'))


def test_complete_pilot_full_replay_resume_and_tamper(tmp_path):
    inputs=fixture(tmp_path/'source'); pilot=tmp_path/'pilot'; fullinputs=complete_pilot(pilot,inputs)
    report=read(fullinputs['pilot_summary']); assert report['primary'] is None and report['execution_only']
    assert report['full_projected_seconds']>=2*report['timing']['fit_seconds']*4
    out=tmp_path/'full';out.mkdir();write(out/'YIELD_REQUEST.json',dict(reason='fixture'))
    config=c.CONFIG|dict(mode='full');assert c.execute(out,fullinputs,config)['status']=='yielded'
    (out/'YIELD_REQUEST.json').unlink();result=c.execute(out,fullinputs,config)
    assert result['repeated_outcome_control']['total']==200 and result['extension_closed']
    before={p.relative_to(out).as_posix():sha256(p) for p in out.rglob('*') if p.is_file()}
    assert_equal(c.execute(out,fullinputs,config),result)
    assert before=={p.relative_to(out).as_posix():sha256(p) for p in out.rglob('*') if p.is_file()}
    request=tmp_path/'REQUEST.json';write(request,dict(output=str(out),inputs=fullinputs,config=config))
    code='import json,sys;from runners.drive.cards.menus_d2_canonical import verify;r=json.load(open(sys.argv[1]));assert verify(**r)["verified"]'
    env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONHASHSEED='719')
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(request)],env=env,check=True,timeout=120)
    chosen=next((out/'recipients'/c.name('w1')).glob('p*.json.gz'))
    chosen.write_bytes(chosen.read_bytes()+b' ')
    with pytest.raises(ValueError): c.verify(out,fullinputs,config)


def test_validation_refuses_corpus_and_changed_configuration(tmp_path):
    inputs=fixture(tmp_path/'source')
    with pytest.raises(ValueError,match='configuration'):c.load(inputs,c.CONFIG|dict(permutations=199))
    terminal=Path(inputs['original_complete']); value=read(terminal);value.pop('synthetic_metadata_fixture_only')
    terminal.write_text(json.dumps(value),encoding='utf8')
    with pytest.raises(ValueError,match='constructed'):c.load(inputs,c.CONFIG|dict(mode='validation'))
