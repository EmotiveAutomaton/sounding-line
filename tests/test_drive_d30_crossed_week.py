"""Known-answer, paired population, complete storage and actual-handler tests."""
import copy
import json
import os
import gzip
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards import timing_d30_crossed_week as card
from runners.drive.cards import timing_d30_crossed_week_pilot as cost_pilot
from runners.drive.cards.timing_census import read, write, filehash
from tests.test_drive_cards_timing_d30_crossed import constructed
from tests.test_drive_cards_timing_d30_crossed_main import admitted_sources, schedule_kernel
from tests.test_drive_cards_timing_d30_crossed import serialized_sources
from runners.drive.cards.timing_stats import sufficient, fit

SMALL = dict(card.CONFIG, bootstrap_draws=25, permutations=200)


def supported_sources(root):
    """Extra observation noise prevents a deliberately near-perfect marker fit.

    The old near-degenerate fixture remains in the retained failed suite; this
    broader known-answer case does not relax the variance ceiling.
    """
    root=Path(root);inputs=serialized_sources(root/'source',1)
    for name in ('primary','extension'):
        folder=Path(inputs[name+'_completion']).parent
        path=folder/'output/D30_INTERMEDIATES.json.gz'
        with gzip.open(path,'rt',encoding='utf-8') as stream:saved=json.load(stream)
        rng=np.random.default_rng(91)
        for r in saved['rows']:r['pause_seconds']*=math.exp(float(rng.normal(0,.4)))
        matrix,_=card.pilot.specification.designs(saved['rows'],saved['timing_mode'])
        with gzip.open(path,'wt',encoding='utf-8') as stream:json.dump(saved,stream)
        baseline=dict(effect=fit(sufficient(matrix['designs'][int(name=='extension')],matrix['y'],matrix['writers'],True))[0],
                      observations=len(matrix['y']),writers=len(set(matrix['writers'])))
        (folder/'output/D30_PRIMARY.json').write_text(json.dumps(baseline),encoding='utf-8')
        complete=read(folder/'COMPLETE.json');complete['outputs']={p.relative_to(folder).as_posix():filehash(p) for p in folder.rglob('*') if p.is_file() and p.name!='COMPLETE.json'}
        (folder/'COMPLETE.json').write_text(json.dumps(complete),encoding='utf-8')
    attempt=root/'pilot';p=card.pilot
    p.execute(attempt/'output',inputs,p.CONFIG)
    write(attempt/'VERIFIED.json',p.verify(attempt/'output',inputs,p.CONFIG))
    write(attempt/'PLAN.json',dict(module=p.__name__,config=p.CONFIG,inputs=inputs,at='2026-10-18T00:00:00+00:00',pins={str(Path(p.__file__).resolve()):filehash(p.__file__)}))
    write(attempt/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,at='2026-10-18T00:00:10+00:00',
        outputs={q.relative_to(attempt).as_posix():filehash(q) for q in attempt.rglob('*') if q.is_file()}))
    return dict(inputs,pilot_completion=str(attempt/'COMPLETE.json'))


def matrices(signal=1):
    primary=constructed(signal)
    fake=copy.deepcopy(primary)
    fake['x']=[[1-row[0]]+row[1:] for row in primary['x']]
    return dict(primary=primary,label_shuffle=fake,paired_own=primary,paired_fake=fake)


def evidence(m):
    n=len(m['primary']['y'])
    return dict(paired_invalid_reason=None,paired_occurrences=n,primary_occurrences=n,dropped_occurrences=0,
                paired_real_writers=len(set(m['primary']['writers'])),timing_control_writer_differences=[])


def test_reference_null_bias_direction_and_degenerate_case():
    assert card.reference(0,[0]*200)['upper_tail_permutation_p']==1
    assert not card.reference(0,[0]*200)['bias_flag']
    assert card.reference(1,[1]*200)['bias_flag']
    null=[-1,1]*100
    assert card.reference(2,null)['upper_tail_permutation_p']==1/201
    assert card.reference(-2,null)['upper_tail_permutation_p']==1
    with pytest.raises(ValueError,match='incomplete'):
        card.reference(0,[0,float('nan')])


def test_stable_objective_dense_gradient_and_strict_gates(monkeypatch):
    m=constructed();p=card.stable.prepare(**m);theta=np.log1p([.2,.5])
    actual,gradient=card.stable.evaluate(p,theta)
    expected=card.pilot.evaluate(card.pilot.prepare(**m),np.expm1(theta))
    assert actual['effect']==pytest.approx(expected['effect'],abs=1e-10)
    assert actual['objective']==pytest.approx(expected['objective'],abs=1e-8)
    for i in range(2):
        step=np.eye(2)[i]*1e-5
        numerical=(card.stable.evaluate(p,theta+step)[0]['objective']-card.stable.evaluate(p,theta-step)[0]['objective'])/2e-5
        assert gradient[i]==pytest.approx(numerical,rel=1e-6,abs=1e-5)
    assert card.stable.fit(**constructed(0))['effect']==0
    zero=dict(m,y=[0.]*len(m['y']))
    with pytest.raises(ValueError,match='residual variance'):card.stable.fit(**zero)
    monkeypatch.setattr(card.pilot,'MAX_RATIO',.001)
    with pytest.raises(ValueError,match='variance ceiling'):card.stable.fit(**m)


def test_corrected_cost_pilot_replay_and_no_inferential_claim(tmp_path):
    inputs=supported_sources(tmp_path/'source');output=tmp_path/'output'
    report=cost_pilot.execute(output,inputs,cost_pilot.CONFIG)
    assert report['instrument_only'] and not report['scientific_main_admitted']
    assert not {'effect','state','ci_low','ci_high'}.intersection(report)
    assert cost_pilot.verify(output,inputs,cost_pilot.CONFIG)['primary']==report
    assert cost_pilot.execute(output,inputs,cost_pilot.CONFIG)==report
    with pytest.raises(ValueError,match='exact corrected'):
        cost_pilot.source(inputs,dict(cost_pilot.CONFIG,bootstrap_pilot_draws=True))


def test_pairing_changes_only_target_on_exact_original_rows(monkeypatch):
    rows=[dict(writer=f'w{i//4}',session=f's{i//2}',marker=f'm{i%4}') for i in range(16)]
    primary=dict(x=[[i%2,math.sin(i)] for i in range(16)],y=[float(i%5) for i in range(16)],
                 writers=[r['writer'] for r in rows],markers=[r['marker'] for r in rows])
    def design(indexed,mode):
        return primary,[dict(r,label='local' if i%2 else 'pervasive') for i,r in enumerate(indexed)],[]
    monkeypatch.setattr(card.legacy,'design',design)
    monkeypatch.setattr(card.pilot.original,'shuffle_marker_labels',lambda r,g:[v['label'] for v in r])
    def classify(fake_rows):
        return {(r['writer'],r['marker']):dict(label='local' if r['marker']=='m1' else 'pervasive')
                for r in fake_rows if r['marker']!='m3'},[]
    monkeypatch.setattr(card.pilot.original,'classify_markers',classify)
    got,proof=card.paired_designs(rows,'per_character',primary)
    assert proof['paired_occurrences']==12 and proof['dropped_occurrences']==4
    own,fake=got['paired_own'],got['paired_fake']
    assert own is not None and fake is not None
    assert own['writers']==fake['writers'] and own['y']==fake['y'] and own['markers']==fake['markers']
    assert all(a[1:]==b[1:] for a,b in zip(own['x'],fake['x']))
    assert proof['paired_primary_indices']==[i for i in range(16) if i%4!=3]
    monkeypatch.setattr(card.pilot.original,'classify_markers',lambda r:({},[]))
    missing,gap=card.paired_designs(rows,'per_character',primary)
    assert missing['primary']==primary and missing['paired_own'] is None
    assert gap['paired_occurrences']==0 and gap['paired_invalid_reason']


def test_complete_schedule_resume_paired_indices_and_mutation(tmp_path,monkeypatch):
    m=matrices();m={k:{key:v[:60]+v[-60:] for key,v in a.items()} for k,a in m.items()}
    monkeypatch.setattr(card.stable,'fit',schedule_kernel)
    seen=[]
    original=card.legacy.resample
    def capture(matrix,selected,groups):
        seen.append(list(selected));return original(matrix,selected,groups)
    monkeypatch.setattr(card.legacy,'resample',capture)
    def stop(phase,done,total):
        if done==25:raise card.Yield('fixture')
    with pytest.raises(card.Yield):card.compute(m,card.CONFIG,tmp_path,stop)
    saved=tmp_path/'bootstrap/block-00000.json';before=saved.read_bytes()
    result=card.compute(m,card.CONFIG,tmp_path)
    assert saved.read_bytes()==before
    assert result==card.compute(m,card.CONFIG)
    assert len(result['permutations'])==200 and all(len(a)==2000 for a in result['bootstrap'].values())
    assert all(seen[i+2]==seen[i+3] for i in range(0,len(seen),4))
    record=read(saved);record['values'].pop();saved.write_text(json.dumps(record),encoding='utf-8')
    saved.with_suffix('.receipt.json').write_text(json.dumps(dict(sha256=filehash(saved))),encoding='utf-8')
    with pytest.raises(ValueError,match='binding/coverage'):card.compute(m,card.CONFIG,tmp_path)


def test_exact_paired_null_and_support_failure_are_distinct(monkeypatch):
    m=matrices();m['paired_fake']=copy.deepcopy(m['paired_own'])
    monkeypatch.setattr(card.stable,'fit',schedule_kernel)
    fits=card.compute(m,SMALL)
    result=card.summarize(m,evidence(m),fits,SMALL)['controls']['paired_own_minus_fake']
    assert result['effect']==result['ci_low']==result['ci_high']==0 and result['state']=='null'
    m['paired_own']=m['paired_fake']=None
    e=dict(evidence(m),paired_invalid_reason='no shared support',paired_occurrences=0)
    result=card.summarize(m,e,card.compute(m,SMALL),SMALL)
    assert result['controls']['paired_own_minus_fake']['state']=='invalid'


@pytest.mark.parametrize('signal,state',[(1,'positive'),(-1,'negative')])
def test_real_crossed_known_direction_and_paired_effect(signal,state):
    m=matrices(signal)
    # Real full estimator; a small bootstrap fixture, with all 200 permutations.
    fitted=card.compute(m,SMALL)
    got=card.summarize(m,evidence(m),fitted,SMALL)
    assert got['state']==state
    assert got['effect']==pytest.approx(signal,abs=1e-7)
    paired=got['controls']['paired_own_minus_fake']
    assert paired['effect']==pytest.approx(2*signal,abs=1e-7) and paired['state']==state
    if signal==1:assert got['controls']['repeated_outcome']['upper_tail_permutation_p']==1/201


def test_actual_serialized_handler_reentry_fresh_process_and_refusals(tmp_path,monkeypatch):
    inputs=supported_sources(tmp_path/'source')
    with pytest.raises(ValueError,match='exact week'):card.source(inputs,SMALL)
    monkeypatch.setattr(card,'CONFIG',SMALL)
    output=tmp_path/'output';write(output/'YIELD_REQUEST.json',{})
    assert card.execute(output,inputs,SMALL)['status']=='yielded'
    retained=(output/'bootstrap/block-00000.json').read_bytes()
    (output/'YIELD_REQUEST.json').unlink()
    result=card.execute(output,inputs,SMALL)
    assert result['state']=='positive' and result['controls']['repeated_outcome']['permutations']==200
    assert (output/'bootstrap/block-00000.json').read_bytes()==retained
    manifest=tmp_path/'verify.json';write(manifest,dict(output=str(output),inputs=inputs,config=SMALL))
    code="import json,sys; from pathlib import Path; from runners.drive.cards import timing_d30_crossed_week as c; p=json.load(open(sys.argv[1])); c.CONFIG=p['config']; print(json.dumps(c.verify(Path(p['output']),p['inputs'],p['config'])))"
    child=subprocess.run([sys.executable,'-B','-c',code,str(manifest)],capture_output=True,text=True,timeout=180,
                         env=dict(os.environ,PYTHONHASHSEED='431'))
    assert child.returncode==0,child.stderr
    assert json.loads(child.stdout)['primary']==result
    assert card.execute(output,inputs,SMALL)==result
    terminal=Path(inputs['pilot_completion']);terminal.write_bytes(terminal.read_bytes()+b' ')
    with pytest.raises(ValueError):card.verify(output,inputs,SMALL)


def native_inputs(root):
    return supported_sources(Path(root))


def execute(output,inputs,config):
    """Counted native fixture: real serialized source, known answer and all controls."""
    assert config==SMALL
    card.CONFIG=SMALL
    # Instrument path is also exercised in the counted native runtime.
    cost_pilot.execute(Path(output)/'cost-pilot',inputs,cost_pilot.CONFIG)
    result=card.execute(output,inputs,config)
    assert result['state']=='positive' and result['controls']['repeated_outcome']['permutations']==200
    return result


def verify(output,inputs,config):
    assert config==SMALL
    card.CONFIG=SMALL
    cost_pilot.verify(Path(output)/'cost-pilot',inputs,cost_pilot.CONFIG)
    result=card.verify(output,inputs,config)
    # Also exercise a supported paired branch under the real estimator.
    m=matrices();result2=card.summarize(m,evidence(m),card.compute(m,SMALL),SMALL)
    assert result2['controls']['paired_own_minus_fake']['state']=='positive'
    result['supported_paired_known_answer_verified']=True
    return result
