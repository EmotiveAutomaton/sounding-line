import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
from runners.drive.cards import menus_d20 as d
from runners.drive.cards import menus_d20_sources as s
from runners.drive.cards.menus_io import read,write,sha256
from runners.drive.cards.timing_p6 import gzwrite


def semantic_rows(reverse=False):
    result=[]
    for w in range(8):
        for half in range(2):
            word=['apple','orange','banana','pear','grape','melon','peach','berry'][w]
            target=['apple','orange','banana','pear','grape','melon','peach','berry'][(w+1)%8] if reverse else word
            vector=np.eye(384)[w].tolist();win=np.eye(384)[(w+1)%8 if reverse else w].tolist()
            result.append(dict(key=f'w{w}s{half}',writer=f'w{w}',session=f'w{w}s{half}',prompt='p',half=half,
                progress_decile=0,handling='dismiss',options=[word],option_vectors=[vector],window=' '.join([target]*50),window_vector=win))
    return result


def test_exact_donor_expectation_and_known_positive_negative_null():
    config=d.CONFIG|dict(bootstrap=80)
    rows=semantic_rows();comp,writers,ex=d.comparisons(rows,'lexical')
    value=d.summarize(comp,writers,config)
    assert value['primary']['effect']==pytest.approx(14/15)
    assert value['primary']['state']=='positive' and ex=={}
    comp,writers,_=d.comparisons(semantic_rows(True),'lexical')
    assert d.summarize(comp,writers,config)['primary']['state']=='negative'
    for row in rows:row.update(options=['shared'],window=' '.join(['shared']*50))
    comp,writers,_=d.comparisons(rows,'lexical')
    result=d.summarize(comp,writers,config)['primary']
    assert result['effect']==0 and result['state']=='null'


def test_donor_weights_rebuilt_and_recipient_copies_excluded():
    comp,writers,_=d.comparisons(semantic_rows(),'lexical')
    weights=np.array([2,0,1,1,1,1,1,1]);point,means,_=d.estimates(comp,writers,weights)
    # Writer0's other session appears twice, but neither sampled copy of the
    # recipient session appears. Other writer nodes supply twelve donor sessions.
    assert means['w0']==pytest.approx(1-2/14)
    assert means['w2']==pytest.approx(1-1/15)
    assert point==pytest.approx((2*(1-2/14)+6*(1-1/15))/8)


def test_word_boundary_short_tails_and_no_later_word_leakage():
    words=[dict(index=i,is_word=True,ordinal=i,completed_ordinal=i+1,token=f'w{i}',revised=i%2==0) for i in range(80)]
    result=s.word_window(words,10)
    assert [w['index'] for w in result]==list(range(11,61))
    words[61]['token']='later_changed'
    assert [w['token'] for w in s.word_window(words,10)]==[w['token'] for w in result]
    assert s.word_window(words,40) is None
    assert sum(w['revised'] for w in result)==25


def test_uniform_session_then_menu_weights_not_pooled_menus():
    rows=semantic_rows()[:3]
    rows[0].update(writer='a',session='a',key='a',window='apple',options=['apple'])
    rows[1].update(writer='b',session='b',key='b',options=['apple'])
    rows[2].update(writer='c',session='c',key='c',options=['orange'])
    rows.extend([rows[2]|dict(key='duplicate'+str(i)) for i in range(9)])
    comparison,writers,_=d.comparisons(rows,'lexical')
    target=next(r for r in comparison if r['key']=='a')
    assert sum(target['donor_sum'])/sum(target['donor_sessions'])==.5


def fixture(tmp_path,shared=False):
    """Actual serialized producer-shaped inputs; local frozen encoder only."""
    base=Path.cwd()/'results/phase_2_4_stage_15/raw/drive-content-features-v2/MODEL.json'
    if not base.exists():raise FileNotFoundError('native fixture requires the explicitly frozen local MiniLM identity')
    root=tmp_path/'source';root.mkdir();p2=root/'p2';p2.mkdir();p5=root/'p5';p5.mkdir();p6=root/'p6';p6.mkdir();content=root/'content';content.mkdir()
    sessions=[];features=[];ledger_index=[];timeline_index=[];vectors=[]
    for i,row in enumerate(semantic_rows()):
        if shared:row.update(options=['shared'],option_vectors=[np.eye(384)[0].tolist()])
        sid=row['session'];menu=dict(key=row['key'],ordinal=0,handling='dismiss',menu=row['options'])
        sessions.append(dict(session=sid,writer=row['writer'],prompt='p',timestamp=row['half'],rows=[menu]))
        features.append(dict(key=row['key'],session=sid,writer=row['writer'],options=[i]));vectors.extend(row['option_vectors'])
        words=[dict(index=j,is_word=True,ordinal=j+2,completed_ordinal=j+3,token=row['options'][0],revised=False) for j in range(50)]
        name=sid+'.json.gz';gzwrite(p6/name,dict(session=sid,writer=row['writer'],prompt='p',words=words))
        ledger_index.append(dict(session=sid,writer=row['writer'],file=name,sha256=sha256(p6/name)))
        name=sid+'.json';write(p2/name,dict(session=sid,writer=row['writer'],prompt='p',decisions=[dict(key=row['key'],ordinal=0,resolution_ordinal=1,handling='dismiss')]))
        timeline_index.append(dict(session=sid,writer=row['writer'],file=name,sha256=sha256(p2/name)))
    write(root/'SESSIONS.json',sessions);write(content/'RECORDS.json',features);np.save(content/'VECTORS.npy',np.asarray(vectors,np.float32),allow_pickle=False)
    (content/'MODEL.json').write_bytes(base.read_bytes())
    write(content/'COMPLETE.json',dict(status='COMPLETE',outputs={n:sha256(content/n) for n in ('RECORDS.json','VECTORS.npy','MODEL.json')}))
    write(p2/'INDEX.json',timeline_index);write(p2/'COMPLETE.json',dict(status='COMPLETE',outputs={'INDEX.json':sha256(p2/'INDEX.json')}))
    write(p5/'INDEX.json',[dict(session=r['session']) for r in sessions])
    paths=dict(sessions=str(root/'SESSIONS.json'),content_model=str(content/'MODEL.json'))
    write(p5/'INPUTS.json',dict(paths=paths,sha256={k:sha256(v) for k,v in paths.items()}))
    write(p5/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs={n:sha256(p5/n) for n in ('INDEX.json','INPUTS.json')}))
    write(p6/'INDEX.json',ledger_index)
    write(p6/'PLAN.json',dict(inputs={'prepared_sessions':paths['sessions']},pins={paths['sessions']:sha256(paths['sessions'])}))
    write(p6/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs={n:sha256(p6/n) for n in ('INDEX.json','PLAN.json')}))
    inputs=paths|dict(content_records=str(content/'RECORDS.json'),content_vectors=str(content/'VECTORS.npy'),content_complete=str(content/'COMPLETE.json'),
        foundation_complete=str(p2/'COMPLETE.json'),session_index=str(p2/'INDEX.json'),p5_inputs=str(p5/'INPUTS.json'),p5_index=str(p5/'INDEX.json'),
        p5_completion=str(p5/'COMPLETE.json'),p6_index=str(p6/'INDEX.json'),p6_plan=str(p6/'PLAN.json'),p6_completion=str(p6/'COMPLETE.json'))
    return inputs,d.CONFIG|dict(bootstrap=30,threads=1,batch_size=16)


def test_actual_offline_encoder_execute_resume_fresh_verify(tmp_path):
    inputs,config=fixture(tmp_path);output=tmp_path/'output';output.mkdir();write(output/'YIELD_REQUEST.json',{})
    assert d.execute(output,inputs,config)['status']=='yielded';(output/'YIELD_REQUEST.json').unlink()
    result=d.execute(output,inputs,config)
    assert result['primary']['state']=='positive' and result['counts']['dismissed']==16
    before={str(p):sha256(p) for p in output.rglob('*') if p.is_file()}
    assert d.execute(output,inputs,config)==result
    assert before=={str(p):sha256(p) for p in output.rglob('*') if p.is_file()}
    request=tmp_path/'REQUEST.json';write(request,dict(output=str(output),inputs=inputs,config=config))
    code='import json,sys;from runners.drive.cards.menus_d20 import verify;r=json.load(open(sys.argv[1]));assert verify(**r)["source_windows_replayed"]'
    subprocess.run([sys.executable,'-B','-c',code,str(request)],check=True,timeout=60,env=os.environ|dict(PYTHONHASHSEED='319'))
    target=next((output/'sessions').glob('*.json'));target.write_text(target.read_text(encoding='utf8')+' ',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):d.verify(output,inputs,config)


def test_empty_strata_content_and_population_support_fail_closed():
    row=semantic_rows()[0]
    comparison,writers,excluded=d.comparisons([row],'lexical')
    assert comparison==[] and excluded['no other-session donor in prompt/progress stratum']==1
    assert d.summarize(comparison,writers,d.CONFIG|dict(bootstrap=5))['primary']['state']=='invalid'
    assert d.lexical([d.content_words('the and')],d.content_words('apple')) is None


def test_actual_full_pipeline_null_stays_null(tmp_path):
    inputs,config=fixture(tmp_path,shared=True)
    result=d.execute(tmp_path/'output',inputs,config)
    for channel in ('lexical','embedding'):
        for arm in ('observed','outcome_control'):
            effect=result['arms'][channel+'_'+arm]['primary']
            assert effect['effect']==pytest.approx(0,abs=1e-15)
            assert effect['ci95']==pytest.approx([0,0],abs=1e-15)
    assert result['primary']['state']=='null'
    assert d.verify(tmp_path/'output',inputs,config)['verified']
