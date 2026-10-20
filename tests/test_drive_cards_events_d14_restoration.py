import copy
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
from runners.drive.cards import events_d14_restoration as card
from runners.drive.cards import events_p5 as p5
from runners.drive.cards.events_d4 import save
from runners.drive.timeline import rebuild
from runners.stage9.coauthor import replay
from tests.test_drive_cards_events_d18 import Stream, event, write


def scope(text, tail=False):
    result=dict(full_tokens=len(text),used_tokens=min(len(text),254),truncated=len(text)>254,codepoint_end=min(len(text),254))
    if tail:
        result.update(first_native_token=max(0,len(text)-254),codepoint_start=max(0,len(text)-254),codepoint_end=len(text))
    return result


def one_correction(effect=1., split='excluded'):
    e=np.eye(384)
    before=e[1] if effect>=0 else e[0]
    after=effect*e[0]+np.sqrt(1-effect**2)*e[1] if effect>=0 else e[1]
    row=dict(key='m',writer='w',session='s',ordinal=1,handling='edit')
    edit=dict(ordinal=4,origin='model',accepted_owners_touched=[1],deleted_origin_counts={'accepted':3},
        before='Before.',after='After.',before_vector=0,after_vector=1,split=split)
    saved=dict(edits=[edit],visibility=[scope('Before.'),scope('After.')])
    eligible={'m':dict(topic_drift=1.)};paragraphs={'m':dict(vector=e[0].tolist(),scope=scope('Context.',True))}
    return dict(rows=[row],writer='w',session='s'),saved,np.vstack([before,after]),eligible,paragraphs


@pytest.mark.parametrize('effect,state',[(1.,'positive'),(0.,'null'),(-1.,'negative')])
def test_known_signed_null_restoration_without_split_selection(effect,state):
    args=one_correction(effect)
    rows,excluded=card.first_touch_rows(*args)
    assert not excluded and rows[0]['restoration']==pytest.approx(effect)
    assert rows[0]['deterministic_split']=='excluded'
    units=[dict(writer=f'w{i}',rows=[dict(rows[0],writer=f'w{i}')],exclusions=[],
        original_edit_menus=1,original_d14_rows=1,original_noneligible_menus=0) for i in range(3)]
    result=card.summarize(units,card.CONFIG)
    assert result['primary']['effect']==pytest.approx(effect) and result['primary']['state']==state
    assert result['paragraph_anchor_shuffle']['effect']==pytest.approx(effect)
    if effect==0:
        assert result['before_after_direction_swap']['effect']==0
        assert result['before_after_direction_swap']['state']=='null'
    assert result['control_support']['writers_with_one_correction']==3
    assert result['zero_embedding_changes']==(3 if effect==0 else 0)
    # Removing the only independent peers is invalid even with a planted sign.
    assert card.summarize(units[:1],card.CONFIG)['primary']['state']=='invalid'


def test_first_touch_is_fixed_before_outcomes_and_never_rescued():
    args=list(one_correction());first=args[1]['edits'][0]
    later=dict(first,ordinal=8)
    for change,reason in [({'deleted_origin_counts':{'accepted':3,'typed':1}},'mixed changed-span'),
                          ({'accepted_owners_touched':[1,7]},'exclusive accepted owner'),
                          ({'origin':'other'},'exclusive accepted owner'),({'after':''},'empty before or after')]:
        saved=dict(args[1],edits=[later,dict(first,**change)])
        rows,exclusions=card.first_touch_rows(args[0],saved,*args[2:])
        assert not rows and len(exclusions)==1 and reason in exclusions[0]['reason']
        assert exclusions[0]['ordinal']==4
    rows,excluded=card.first_touch_rows(args[0],dict(args[1],edits=[]),*args[2:])
    assert not rows and 'no recovered first touch' in excluded[0]['reason']
    with pytest.raises(ValueError,match='does not follow'):
        card.first_touch_rows(args[0],dict(args[1],edits=[dict(first,ordinal=0)]),*args[2:])


def test_orthogonal_movement_is_retained_as_zero_restoration():
    args=list(one_correction(1.));args[2][1]=np.eye(384)[2]
    rows,excluded=card.first_touch_rows(*args)
    assert not excluded and rows[0]['restoration']==0 and not rows[0]['zero_embedding_change']


def test_duplicate_negative_index_bad_scope_and_embedding_refuse():
    args=list(one_correction());first=args[1]['edits'][0]
    with pytest.raises(ValueError,match='coverage'):
        card.first_touch_rows(args[0],dict(args[1],edits=[first,first]),*args[2:])
    with pytest.raises(ValueError,match='vector index'):
        card.first_touch_rows(args[0],dict(args[1],edits=[dict(first,before_vector=-1)]),*args[2:])
    saved=copy.deepcopy(args[1]);saved['visibility'][0]['truncated']=True
    with pytest.raises(ValueError,match='token scope'):card.first_touch_rows(args[0],saved,*args[2:])
    args[2][0]=0
    with pytest.raises(ValueError,match='embedding'):card.first_touch_rows(*args)


def test_equal_session_then_writer_weight_and_control_reproducibility():
    rows,_=card.first_touch_rows(*one_correction(1.));positive=rows[0]
    rows,_=card.first_touch_rows(*one_correction(-1.));negative=rows[0]
    units=[]
    for i in range(3):
        own=[dict(positive,key=f'a{j}',session='a',accepted_ordinal=j) for j in range(10)]
        own+=[dict(negative,key='b',session='b')]
        units.append(dict(writer=f'w{i}',rows=own,exclusions=[],original_edit_menus=11,original_d14_rows=11,original_noneligible_menus=0))
    result=card.summarize(units,card.CONFIG)
    assert result['primary']['effect']==0 and result['primary']['state']=='null'
    assert result==card.summarize(list(reversed(units)),card.CONFIG)
    assert result['control_support']['anchor_vectors_changed']==0


def full_fixture(root,writers=3,effect=1.):
    """Real raw/P2/P5 source shapes, known synthetic frozen embeddings."""
    root=Path(root);content=root/'content';p5root=root/'p5';d14=root/'d14'
    content.mkdir(parents=True);e=np.eye(384,dtype=np.float32)
    inputs={k:str(content/(k+'.json')) for k in card.SHARED if k!='content_vectors'}
    inputs['content_vectors']=str(content/'VECTORS.npy')
    inputs.update(d14_summary=str(d14/'output/SUMMARY.json'),d14_inputs=str(d14/'output/INPUTS.json'),
        d14_index=str(d14/'output/WRITER_INDEX.json'),d14_completion=str(d14/'COMPLETE.json'),
        p5_index=str(p5root/'output/SESSION_INDEX.json'),p5_inputs=str(p5root/'output/INPUTS.json'),
        p5_summary=str(p5root/'output/SUMMARY.json'),p5_source_pins=str(p5root/'output/SOURCE_PINS.json'),
        p5_completion=str(p5root/'COMPLETE.json'),p2_index=str(root/'p2/SESSION_INDEX.json'),
        source_roster=str(root/'ROSTER.json'),source_root=str(root))
    sessions,records,p5index,p2index,roster,d14index,rawpins=[],[],[],[],[],[],{}
    d14files=[]
    for wi in range(writers):
        writer=f'w{wi}';oldrows,paragraphs=[],[]
        for si in range(2):
            sid=f'{writer}s{si}';key=f'{sid}m';prompt='Context.\n';s=Stream(prompt)
            options=[dict(index=0,original=' Off topic.',trimmed='Off topic.'),dict(index=1,original=' Other.',trimmed='Other.')]
            owner=len(s.events);s.events.append(event(owner,'suggestion-open',currentSuggestions=options))
            s.events.append(event(len(s.events),'suggestion-select',currentSuggestionIndex=0))
            s.add([{'retain':len(s.doc)-1},{'insert':' Off topic.'}],source='api')
            s.add([{'retain':len(prompt)-1},{'delete':len(' Off topic.')},{'insert':' Context.'}],name='text-delete')
            s.add(name='system-end',source='api')
            canonical=replay(s.events)
            assert canonical['reconstructed'] and not canonical['errors'] and canonical['events'][0]['usable']
            assert canonical['events'][0]['decision']=='edit'
            menu=dict(key=key,writer=writer,session=sid,ordinal=owner,end_ordinal=len(s.events),
                open_at=si*100+1,document=prompt,menu=[' Off topic.',' Other.'],inserted=' Off topic.',handling='edit')
            session=dict(session=sid,writer=writer,timestamp=si*100,end_at=si*100+99,rows=[menu]);sessions.append(session)
            timeline=rebuild(s.events,[menu]);raw=root/'raw'/f'{sid}.jsonl';raw.parent.mkdir(parents=True,exist_ok=True)
            raw.write_text(''.join(json.dumps(v)+'\n' for v in s.events),encoding='utf8')
            p2path=root/'p2'/f'{sid}.json';write(p2path,timeline)
            roster.append(dict(session=sid,writer=writer,path=raw.relative_to(root).as_posix(),source_sha256=card.filehash(raw)))
            p2index.append(dict(session=sid,writer=writer,file=p2path.name,sha256=card.filehash(p2path)))
            rawpins.update({str(raw):card.filehash(raw),str(p2path):card.filehash(p2path)})
            extracted=p5.extract_session(s.events,timeline);assert len(extracted['edits'])==1
            edit=extracted['edits'][0]
            before=e[1] if effect>=0 else e[0];after=effect*e[0]+np.sqrt(1-effect**2)*e[1] if effect>=0 else e[1]
            edit.update(before_vector=0,after_vector=1,**p5.classify(edit['before'],edit['after'],before,after,1,1))
            saved=dict(extracted,writer=writer,session=sid,timestamp=session['timestamp'],end_at=session['end_at'],
                source_sha256=card.filehash(raw),p2_sha256=card.filehash(p2path),visibility=[scope(edit['before']),scope(edit['after'])])
            fpath=p5root/'output/sessions'/f'{sid}.json.gz';fpath.parent.mkdir(parents=True,exist_ok=True)
            with gzip.open(fpath,'wt',encoding='utf8') as stream:json.dump(saved,stream)
            vpath=fpath.with_suffix('.npy');np.save(vpath,np.vstack([before,after]))
            p5index.append(dict(session=sid,file=fpath.relative_to(p5root/'output').as_posix(),sha256=card.filehash(fpath),
                vectors=vpath.relative_to(p5root/'output').as_posix(),vectors_sha256=card.filehash(vpath)))
            records.append(dict(key=key,session=sid,writer=writer,options=[0,1]))
            text,start,end=card.paragraph(prompt)
            paragraphs.append(dict(key=key,vector=e[0].tolist(),scope=scope(text,True),start_codepoint=start,end_codepoint=end))
            oldrows.append(dict(key=key,writer=writer,session=sid,handling='edit',position=0,topic_drift=1.))
        path=d14/'output/writers'/f'{writer}.json';save(path,dict(rows=oldrows,paragraphs=paragraphs))
        d14index.append(dict(writer=writer,file=path.relative_to(d14/'output').as_posix(),sha256=card.filehash(path)))
        d14files.append(path)
    write(Path(inputs['sessions']),sessions);write(Path(inputs['content_records']),records);np.save(inputs['content_vectors'],np.vstack([e[1],e[2]]))
    model=root/'model/revision';model.mkdir(parents=True);weight=model/'fixture';weight.write_bytes(b'synthetic model identity, no inference')
    write(Path(inputs['content_model']),dict(repo='sentence-transformers/all-MiniLM-L6-v2',path=str(model),revision='revision',files={weight.name:card.filehash(weight)}))
    write(Path(inputs['content_complete']),dict(status='COMPLETE',outputs={Path(inputs[k]).name:card.filehash(inputs[k]) for k in ('content_records','content_vectors','content_model')}))
    write(Path(inputs['p8_rows']),[]);write(Path(inputs['p8_summary']),dict(status='complete',table_sha256=card.filehash(inputs['p8_rows'])))
    write(Path(inputs['p8_verified']),dict(verified=True));write(Path(inputs['p2_index']),p2index);write(Path(inputs['source_roster']),roster)
    write(Path(inputs['p5_index']),p5index);write(Path(inputs['p5_summary']),dict(sessions=len(sessions)));write(Path(inputs['p5_source_pins']),rawpins)
    keys=('sessions','content_model','p2_index','source_roster','source_root')
    write(Path(inputs['p5_inputs']),dict(paths={k:inputs[k] for k in keys},sha256={k:card.filehash(inputs[k]) for k in keys if k!='source_root'}))
    write(Path(inputs['p5_completion']),dict(status='COMPLETE',fresh_process_verified=True,
        outputs={Path(inputs[k]).relative_to(p5root).as_posix():card.filehash(inputs[k]) for k in ('p5_index','p5_summary','p5_inputs','p5_source_pins')}))
    write(Path(inputs['d14_summary']),dict(card='D14',phase='main',execution_only=False,extension_run=False,primary=dict(state='marginal'),selected_writers=sorted({s['writer'] for s in sessions})))
    write(Path(inputs['d14_index']),d14index)
    write(Path(inputs['d14_inputs']),dict(config=dict(phase='main',threads=2,batch_size=16,bootstrap=2000,seed=20261017,pca_dimensions=16),
        paths={k:inputs[k] for k in card.SHARED},pins={inputs[k]:card.filehash(inputs[k]) for k in card.SHARED}))
    paths=d14files+[Path(inputs[k]) for k in ('d14_summary','d14_inputs','d14_index')]
    write(Path(inputs['d14_completion']),dict(status='COMPLETE',fresh_process_verified=True,
        outputs={p.relative_to(d14).as_posix():card.filehash(p) for p in paths}))
    return inputs


def test_completed_primary_gate_source_joins_and_bound_capsule(tmp_path):
    inputs=full_fixture(tmp_path);assert len(card.source(inputs)['d14'])==3
    summary=card.read(inputs['d14_summary'])
    for changed in (dict(summary,phase='pilot'),dict(summary,primary={'state':'null'}),dict(summary,extension_run=True)):
        write(Path(inputs['d14_summary']),changed)
        receipt=card.read(inputs['d14_completion']);receipt['outputs']['output/SUMMARY.json']=card.filehash(inputs['d14_summary']);write(Path(inputs['d14_completion']),receipt)
        with pytest.raises(ValueError,match='does not open'):card.source(inputs)
    write(Path(inputs['d14_summary']),summary)
    receipt['outputs']['output/SUMMARY.json']=card.filehash(inputs['d14_summary']);write(Path(inputs['d14_completion']),receipt)
    Path(inputs['p8_rows']).write_text('changed',encoding='utf8')
    with pytest.raises(ValueError,match='preserved primary source changed'):card.input_pins(inputs)


def test_full_yield_resume_fresh_source_verification_and_mutations(tmp_path,monkeypatch):
    inputs=full_fixture(tmp_path/'sources');output=tmp_path/'output';original=card.extract_writer;calls=[]
    def extract(*args):
        calls.append(args[0]);result=original(*args)
        if len(calls)==1:write(output/'YIELD_REQUEST.json',{})
        return result
    monkeypatch.setattr(card,'extract_writer',extract)
    assert card.execute(output,inputs,card.CONFIG)['status']=='yielded'
    (output/'YIELD_REQUEST.json').unlink();result=card.execute(output,inputs,card.CONFIG)
    assert calls==['w0','w1','w2'] and result['primary']['effect']==1. and result['primary']['state']=='positive'
    assert result['rows']==6 and result['original_edit_menus']==6 and not result['exclusions']
    assert card.read(output/'FIRST_TENTH.json')['forecast_cpu_seconds']==900
    request=tmp_path/'VERIFY.json';write(request,dict(output=str(output),inputs=inputs,config=card.CONFIG))
    code='import json,sys;from pathlib import Path;from runners.drive.cards.events_d14_restoration import verify;r=json.load(open(sys.argv[1]));print(json.dumps(verify(Path(r["output"]),r["inputs"],r["config"])))'
    child=subprocess.run([sys.executable,'-B','-c',code,str(request)],capture_output=True,text=True,env=dict(os.environ,PYTHONHASHSEED='816'))
    assert child.returncode==0,child.stderr
    assert json.loads(child.stdout)['verified']
    with pytest.raises(ValueError,match='never rerun'):card.execute(output,inputs,card.CONFIG)
    raw=Path(inputs['source_root'])/card.read(inputs['source_roster'])[0]['path'];prior=raw.read_bytes();raw.write_bytes(prior+b'\n')
    with pytest.raises(ValueError,match='raw/P2 source changed'):card.verify(output,inputs,card.CONFIG)
    raw.write_bytes(prior)
    summary=output/'SUMMARY.json';summary.write_text(summary.read_text(encoding='utf8')+' ',encoding='utf8')
    with pytest.raises(ValueError,match='output changed'):card.verify(output,inputs,card.CONFIG)
