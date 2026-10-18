import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from runners.drive.cards import menus_d12 as d
from runners.drive.cards.menus_io import read, write, sha256


def fixture(tmp_path):
    sessions=[];producer=[]
    for w in range(15):
        for s in range(4):
            sid=f'w{w}s{s}';rows=[]
            for i in range(12):
                key=f'{sid}m{i}';menu=['a','bb','ccc','dddd','eeeee']
                chosen=min(4,(w+i%3)//3)
                row=dict(key=key,writer=f'w{w}',session=sid,ordinal=i,menu=menu,
                         handling='accept' if i<w else 'edit',inserted=menu[chosen])
                rows.append(row)
                for j,score in enumerate([-3.,-1.,0.,2.,77.54]):
                    producer.append(dict(key=key,writer=f'w{w}',session=sid,ordinal=i,
                        position=j,suggestion_index=j,logged_score=score))
            sessions.append(dict(writer=f'w{w}',session=sid,timestamp=s,rows=rows))
    root=tmp_path/'source';root.mkdir()
    write(root/'SESSIONS.json',sessions)
    (root/'SUGGESTIONS.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in producer),encoding='utf8')
    write(root/'PLAN.json',dict(pins={str((root/'SESSIONS.json').resolve()):sha256(root/'SESSIONS.json')}))
    write(root/'COMPLETE.json',dict(status='COMPLETE',outputs={n:sha256(root/n) for n in ['PLAN.json','SUGGESTIONS.jsonl']}))
    return dict(sessions=str(root/'SESSIONS.json'),p8=str(root/'SUGGESTIONS.jsonl'),
                p8_complete=str(root/'COMPLETE.json')), d.CONFIG|dict(bootstrap=100,permutations=100)


def test_raw_negative_scores_rank_ties_and_missing(tmp_path):
    inputs,config=fixture(tmp_path);sessions,producer=d.load(inputs)
    writers,by_key=d.prepare(sessions,producer)
    unit=d.writer_rows('w0',writers['w0'],by_key,config['seed'])
    row=unit['rows'][0];values=np.array([-3.,-1.,0.,2.,77.54])
    assert row['raw_scores']==values.tolist()
    assert row['standardized_selected']==pytest.approx(((values-values.mean())/values.std())[0])
    assert row['selected_rank']==5 and row['least']
    for p in by_key[row['key']]:p['logged_score']=7.
    result=d.writer_rows('w0',writers['w0'],by_key,config['seed'])
    assert result['exclusions']['constant_score_menu']==1
    by_key[row['key']][0]['logged_score']=None
    assert d.writer_rows('w0',writers['w0'],by_key,config['seed'])['exclusions']['menu_has_missing_score']==1
    by_key[row['key']][0]['logged_score']=8.
    by_key[row['key']][1]['logged_score']=8.
    tied=d.writer_rows('w0',writers['w0'],by_key,config['seed'])['rows'][0]
    assert tied['selected_rank']==1.5 and tied['favorite_ties']==2


def test_known_reliability_positive_reverse_and_constant(tmp_path):
    inputs,config=fixture(tmp_path);sessions,producer=d.load(inputs)
    writers,by_key=d.prepare(sessions,producer)
    units=[d.writer_rows(w,s,by_key,config['seed']) for w,s in writers.items()]
    result=d.summarize(units,config)
    assert result['primary']['effect']==pytest.approx(1.) and result['state']=='positive'
    assert result['writer_label_permutation']['p_two_sided']<=.05
    for unit in units:
        for row in unit['rows']:
            if row['half']==1:row['standardized_selected']*=-1
    assert d.summarize(units,config)['state']=='negative'
    for unit in units:
        for row in unit['rows']:row['standardized_selected']=0.
    assert d.summarize(units,config)['state']=='invalid'
    assert d.interval(0.,[-1.,0.,1.]*10,config)['state']=='null'


def test_session_split_uses_complete_roster_and_order_invariance(tmp_path):
    inputs,config=fixture(tmp_path);sessions,producer=d.load(inputs)
    first=copy.deepcopy(sessions)
    for r in first[0]['rows']:r['handling']='dismiss'
    writers,by_key=d.prepare(first[::-1],producer[::-1])
    unit=d.writer_rows('w0',writers['w0'],by_key,config['seed'])
    assert [r['half'] for r in unit['rows'][::12]]==[0,1,0,1]
    assert [r['session_ordinal'] for r in unit['rows'][::12]]==[0,1,2,3]
    producer[0]['position']=1
    with pytest.raises(ValueError,match='coverage'):d.prepare(sessions,producer)


def test_serialized_reentry_fresh_source_verifier_and_mutation(tmp_path):
    inputs,config=fixture(tmp_path);out=tmp_path/'output';result=d.execute(out,inputs,config)
    assert result['writers']==15 and result['state']=='positive'
    before={str(p):sha256(p) for p in out.rglob('*') if p.is_file()}
    assert d.execute(out,inputs,config)==result
    assert before=={str(p):sha256(p) for p in out.rglob('*') if p.is_file()}
    request=tmp_path/'REQUEST.json';write(request,dict(output=str(out),inputs=inputs,config=config))
    code='import json,sys;from runners.drive.cards.menus_d12 import verify;r=json.load(open(sys.argv[1]));assert verify(**r)["source_replayed"]'
    env=os.environ.copy();env['PYTHONHASHSEED']='829'
    subprocess.run([sys.executable,'-B','-c',code,str(request)],check=True,timeout=30,env=env)
    file=next((out/'writers').glob('*.json'));file.write_text(file.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):d.verify(out,inputs,config)


def test_yield_resume_and_incomplete_source(tmp_path):
    inputs,config=fixture(tmp_path);out=tmp_path/'output';out.mkdir()
    write(out/'YIELD_REQUEST.json',dict(reason='fixture'))
    assert d.execute(out,inputs,config)['status']=='yielded'
    assert not (out/'SUMMARY.json').exists()
    (out/'YIELD_REQUEST.json').unlink()
    assert d.execute(out,inputs,config)['writers']==15
    receipt=read(inputs['p8_complete']);receipt['status']='RUNNING'
    Path(inputs['p8_complete']).write_text(json.dumps(receipt),encoding='utf8')
    with pytest.raises(ValueError,match='incomplete'):d.authenticate(inputs)


def test_undefined_bootstrap_is_invalid_and_population_guard(tmp_path):
    _,config=fixture(tmp_path)
    assert d.interval(.2,[None]*6+[.1]*94,config)['state']=='invalid'
    with pytest.raises(ValueError,match='insufficient'):d.summarize([],config)
