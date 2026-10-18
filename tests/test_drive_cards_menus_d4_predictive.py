"""Canonical actual-file D4 controls and scalar200-permutation parity."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
from tests.test_drive_cards_events_d4 import full_fixture,directions
from runners.drive.cards import menus_d4_predictive as m
from runners.drive.cards import menus_d4_predictive_source as source
from runners.drive.cards import menus_d4_predictive_stats as stats
from runners.drive.cards.menus_io import read,write,sha256
from runners.stage14.common import digest


def overwrite(path,value):Path(path).write_text(json.dumps(value),encoding='utf8')


def fixture(root):
    root=Path(root).resolve();inputs=full_fixture(root)
    sessions=read(inputs['sessions']);proofs=[];pins={};sourcepins={}
    for session in sessions:
        events=[]
        for row in session['rows']:
            row['inserted']=row['menu'][1]
            events.append(dict(ordinal=row['ordinal'],decision='edit',usable=True,verified_insertion=True,
                options=[dict(index=i+7,original=t) for i,t in enumerate(row['menu'])],matched_option_indices=[7],
                selected_index=1,logged_index_agrees=False))
            proofs.append(dict(key=row['key'],writer=row['writer'],session=row['session'],ordinal=row['ordinal'],open_at=row['open_at'],
                canonical_handling='edit',prepared_handling='edit',canonical_positions=[0],prepared_positions=[1],
                canonical_option_ids=[7,8],verified_insertion=True,canonical_usable=True,logged_selected_index=1,
                logged_index_agrees=False,index_status='proven_disjoint_choice',raw_source_sha256=digest(session['session'])))
        path=root/'canonical'/(session['session']+'.json');write(path,dict(usable=True,reconstructed=True,events=events))
        sourcepins[path.relative_to(root).as_posix()]=sha256(path);pins[str(path)]=sha256(path)
        for proof in proofs[-len(session['rows']):]:proof.update(canonical_path=str(path),canonical_sha256=sha256(path))
    base=root/'results/phase_2_4_stage_15/raw';path=base/'phase0-v1/prepared/SESSIONS.json';write(path,sessions)
    sourcepath=path.with_name('SOURCE_PINS.json');write(sourcepath,sourcepins);inputs['sessions']=str(path)
    binding=read(inputs['p5_inputs']);binding['paths']['sessions']=str(path);binding['sha256']['sessions']=sha256(path);overwrite(inputs['p5_inputs'],binding)
    p5complete=read(inputs['p5_completion']);p5root=Path(inputs['p5_completion']).parent
    for key in ('p5_index','p5_summary','p5_inputs'):p5complete['outputs'][Path(inputs[key]).relative_to(p5root).as_posix()]=sha256(inputs[key])
    overwrite(inputs['p5_completion'],p5complete)
    foundation=base/'drive-foundation-v1';plan=foundation/'PLAN.json';complete=foundation/'COMPLETE.json'
    write(plan,dict(pins={p.relative_to(root).as_posix():sha256(p) for p in (path,sourcepath)},synthetic_fixture_only=True))
    write(complete,dict(status='COMPLETE',plan_sha256=sha256(plan),synthetic_fixture_only=True))
    for p in (path,sourcepath,plan,complete):pins[str(p)]=sha256(p)
    audit=root/'audit';write(audit/'ROWS.json',proofs);write(audit/'INPUT_PINS.json',pins)
    script=root/'synthetic_audit.py';script.write_text('# Explicit synthetic source audit.\n',encoding='utf8')
    write(audit/'COMPLETE.json',dict(status='COMPLETE',schema_version=1,source_path=str(script),source_sha256=sha256(script),
        outputs={n:sha256(audit/n) for n in ('ROWS.json','INPUT_PINS.json')},no_fits=True,no_raw_replay=True,no_inference=True,no_repaired_scores=True,synthetic_fixture_only=True))
    visibility=Path(inputs['content_records']).with_name('VISIBILITY.json')
    write(visibility,[dict(role='suggestion',text_sha256=digest(t)) for t in ('first','second')])
    receipt=read(inputs['content_complete']);receipt['outputs']['VISIBILITY.json']=sha256(visibility);overwrite(inputs['content_complete'],receipt)
    helper=Path(__file__).resolve().parents[1]/'.agent-state/drive-20261017/builder3/selected_source_audit_reader.py'
    inputs.update(selection_reader=str(helper),selection_complete=str(audit/'COMPLETE.json'),visibility=str(visibility));return inputs


def test_canonical_choices_preserve_training_and_refuse_vector_text(tmp_path):
    inputs=fixture(tmp_path/'source');data=source.load(inputs);metadata,units=source.writer_data('w0',data,m.CONFIG)
    assert metadata['exclusion'] is None and all(r['chosen']==0 for r in metadata['calibration']+metadata['test'])
    assert all(p['prepared_positions']==[1] for p in metadata['canonical_choice_audit']['test'])
    assert len(units)==24 and all(v['corrections']==6 for origin in metadata['support'].values() for v in origin.values())
    scope=read(inputs['visibility']);scope[0]['text_sha256']='0'*64;overwrite(inputs['visibility'],scope)
    with pytest.raises(ValueError,match='visibility source'):source.load(inputs)


def test_all200_candidate_loss_permutations_match_original_scalar():
    e=directions();vectors=np.vstack([e[0],-e[0],e[1]])
    models=dict(content=[stats.original.fit_votes(np.vstack([e[0]]*6),p) for p in stats.original.PENALTIES],
        housekeeping=[stats.original.fit_votes(np.vstack([e[1],-e[1]]*3),p) for p in stats.original.PENALTIES])
    rows=[dict(key=f'k{i}',session='a' if i<4 else 'b',chosen=i%2,options=[0,1] if i%3 else [1,0]) for i in range(9)]
    rows.append(dict(key='three',session='b',chosen=2,options=[0,1,2]))
    result=stats.permutation_scores(models,rows,rows,vectors,'writer')
    for i in range(200):
        cal=[r|dict(chosen=result['choice_positions']['calibration'][i][j]) for j,r in enumerate(rows)]
        test=[r|dict(chosen=result['choice_positions']['test'][i][j]) for j,r in enumerate(rows)]
        expected=stats.original.score_pair(models,cal,test,vectors)
        assert {k:result['selected'][k][i] for k in result['selected']}==expected['selected']
        for k in ('primary','content_gain','housekeeping_gain'):assert result[k][i]==pytest.approx(expected['scores'][k],abs=1e-14)
    assert all(a['singleton_size_strata']==1 for a in result['audit']['calibration'])
    assert any(a['changed'] for a in result['audit']['test'])


def test_exact_null_positive_reverse_and_unrepairable_bias():
    e=directions();vectors=np.vstack([e[0],-e[0]])
    null=[stats.original.fit_votes(np.vstack([e[0],-e[0]]),p) for p in stats.original.PENALTIES]
    aligned=[stats.original.fit_votes(np.vstack([e[0]]*6),p) for p in stats.original.PENALTIES]
    rows=[dict(key=f'k{i}',session='s',chosen=0,options=[0,1]) for i in range(8)]
    result=stats.permutation_scores(dict(content=null,housekeeping=null),rows,rows,vectors,'w')
    assert np.array_equal(result['primary'],np.zeros(200))
    for chosen,state in ((0,'positive'),(1,'negative')):
        test=[r|dict(chosen=chosen) for r in rows]
        score=stats.original.score_pair(dict(content=aligned,housekeeping=null),rows,test,vectors)['scores']['primary']
        assert stats.original.interval([score]*4,2000,20261018)['state']==state
    # Permutation preserves all-first selection: a position-driven positive
    # control must remain visible, never become a quiet manufactured null.
    biased=stats.permutation_scores(dict(content=aligned,housekeeping=null),rows,rows,vectors,'w')
    assert min(biased['primary'])>0
    fake=[dict(writer=str(w),arms=dict(model=dict(scores={k:biased[k][0] for k in ('primary','content_gain','housekeeping_gain')})),
        permutations=biased,cohesion={},exclusion=None) for w in range(3)]
    summary=stats.summarize(fake,[dict(writer=str(w),support={}) for w in range(3)],m.CONFIG)
    assert summary['outcome_permutation']['biased_pipeline_flag'] and summary['outcome_permutation']['p_one_sided']==1


def test_actual_yield_reentry_fresh_full_source_replay(tmp_path):
    inputs=fixture(tmp_path/'source');out=tmp_path/'output';out.mkdir();write(out/'YIELD_REQUEST.json',dict(reason='fixture'))
    assert m.execute(out,inputs,m.CONFIG)['status']=='yielded';(out/'YIELD_REQUEST.json').unlink()
    result=m.execute(out,inputs,m.CONFIG)
    assert result['state']=='positive' and result['eligible_writers']==3
    assert result['source_choice_audit']['supported']['test']==dict(rows=12,changed=12)
    before={p.relative_to(out).as_posix():sha256(p) for p in out.rglob('*') if p.is_file()}
    assert m.execute(out,inputs,m.CONFIG)==result
    assert before=={p.relative_to(out).as_posix():sha256(p) for p in out.rglob('*') if p.is_file()}
    request=tmp_path/'REQUEST.json';write(request,dict(output=str(out),inputs=inputs,config=m.CONFIG))
    code='import json,sys;from runners.drive.cards.menus_d4_predictive import verify;r=json.load(open(sys.argv[1]));assert verify(**r)["verified"]'
    env=os.environ.copy();env.update(PYTHONHASHSEED='719',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(request)],env=env,check=True,timeout=40)
    path=next((out/'writers').glob('*/UNITS.npy'));path.write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash differs'):m.verify(out,inputs,m.CONFIG)
