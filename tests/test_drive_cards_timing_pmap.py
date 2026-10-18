"""Serialized source-to-primary checks; no corpus or model inference."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pytest

from runners.drive.cards import timing_pmap as card
from runners.drive.cards import timing_pmap_stats as stats
from runners.drive.cards import timing_pmap_source as source
from runners.drive.cards.timing_census import read,write,filehash
from runners.drive.cards.timing_p6 import gzwrite,gzread
from runners.drive.cards.timing_text import replay_words
from runners.drive.timeline import rebuild
from runners.stage9.coauthor import units
from runners.stage9.common import digest


def fixture(root, mode='positive'):
    root=Path(root).resolve(); root.mkdir(parents=True,exist_ok=True)
    rawroot=root/'raw';rawroot.mkdir();p2root=root/'p2';p5root=root/'p5';p6root=root/'p6'
    content=root/'content'; content.mkdir(); audit=root/'audit'; audit.mkdir()
    metas=[];roster=[];p2ix=[];p5ix=[];p6ix=[];pins={};records=[];auditrows=[];vectors=[]
    for wi in range(6):
      for si in range(4):
        sid=f'w{wi}_s{si}';writer=f'w{wi}';prompt=f'p{si%2}';base=1000000+wi*100000+si*10000
        events=[dict(eventName='system-initialize',eventTimestamp=base,currentDoc='Prompt\n')]
        menurows=[];canon=[];document='Prompt\n'
        naccept=wi+1 if mode=='negative' else 2
        for mi in range(8):
            ordinal=len(events);chosen=mi<naccept;handling='accept' if chosen else 'dismiss';key=f'{sid}_m{mi}'
            options=[dict(index=0,original=' yes',trimmed='yes'),dict(index=1,original=' no',trimmed='no')]
            events.append(dict(eventName='suggestion-open',eventTimestamp=base+len(events)*10))
            events.append(dict(eventName='suggestion-select' if chosen else 'suggestion-close',eventTimestamp=base+len(events)*10))
            if chosen:
                events.append(dict(eventName='text-insert',eventSource='api',eventTimestamp=base+len(events)*10,
                    textDelta={'ops':[{'retain':len(units(document))-1},{'insert':' yes'}]}))
                document=document[:-1]+' yes\n'
            menu=dict(key=key,session=sid,writer=writer,prompt=prompt,ordinal=ordinal,end_ordinal=len(events),
                handling=handling,menu=[' yes',' no'],inserted=' no' if chosen else '',open_at=base+ordinal*10)
            menurows.append(menu)
            canon.append(dict(ordinal=ordinal,usable=True,decision=handling,options=options,
                matched_option_indices=[0] if chosen else [],verified_insertion=chosen,selected_index=1 if chosen else None,
                logged_index_agrees=False if chosen else None,exclusion=None))
            vindex=len(vectors); av=np.zeros(384);av[wi]=1;dv=np.zeros(384);dv[20]=1
            vectors.extend([av,dv]);records.append(dict(key=key,session=sid,writer=writer,options=[vindex,vindex+1]))
        text=(' '+('style'+str(wi) if mode=='positive' else 'common')+' text. ')*3
        for char in text:
            events.append(dict(eventName='text-insert',eventSource='user',eventTimestamp=base+len(events)*10,
                textDelta={'ops':[{'retain':len(units(document))-1},{'insert':char}]}))
            document=document[:-1]+char+'\n'
        raw=rawroot/(sid+'.jsonl');raw.write_text('\n'.join(json.dumps(e) for e in events)+'\n',encoding='utf8')
        rh=filehash(raw);pins[raw.relative_to(root).as_posix()]=rh
        timeline=rebuild(events,menurows);timeline.update(session=sid,writer=writer,prompt=prompt,source_sha256=rh)
        p2=p2root/(sid+'.json');write(p2,timeline);p2ix.append(dict(session=sid,writer=writer,file=p2.name,sha256=filehash(p2)))
        meta=dict(session=sid,writer=writer,prompt=prompt,timestamp=base,end_at=events[-1]['eventTimestamp'],rows=menurows);metas.append(meta)
        roster.append(dict(session=sid,path=raw.relative_to(root).as_posix(),source_sha256=rh))
        p5=p5root/(sid+'.json.gz');gzwrite(p5,dict(session=sid,writer=writer,prompt=prompt,source_sha256=rh,p2_sha256=filehash(p2),edits=[]))
        p5ix.append(dict(session=sid,file=p5.name,sha256=filehash(p5)))
        p6=p6root/(sid+'.json.gz');gzwrite(p6,dict(session=sid,writer=writer,prompt=prompt,timestamp=base,end_at=meta['end_at'],words=replay_words(events)['words']))
        p6ix.append(dict(session=sid,writer=writer,file=p6.name,sha256=filehash(p6)))
        cp=root/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/sessions'/(digest({'coauthor-session':raw.stem})+'.json')
        write(cp,dict(usable=True,reconstructed=True,errors=[],events=canon,final_document=timeline['final_document']))
        ch=filehash(cp);pins[cp.relative_to(root).as_posix()]=ch
        for m,c in zip(menurows,canon):
            auditrows.append(dict(key=m['key'],session=sid,writer=writer,ordinal=m['ordinal'],prepared_handling=m['handling'],
                canonical_handling=c['decision'],canonical_sha256=ch,canonical_positions=[0] if c['decision']=='accept' else [],
                raw_source_sha256=rh,index_status='proven_disjoint_choice' if c['decision']=='accept' else 'not_accepted'))
    write(root/'SESSIONS.json',metas);write(root/'ROSTER.json',roster);write(root/'SOURCE_PINS.json',pins)
    write(p2root/'INDEX.json',p2ix);write(p5root/'INDEX.json',p5ix);write(p6root/'INDEX.json',p6ix)
    plan=p2root/'PLAN.json';write(plan,dict(pins={p.relative_to(root).as_posix():filehash(p) for p in (root/'SESSIONS.json',root/'ROSTER.json',root/'SOURCE_PINS.json')}))
    def complete(folder,names,**extra):
        write(folder/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,outputs={name:filehash(folder/name) for name in names},**extra))
    complete(p2root,['INDEX.json'],plan_sha256=filehash(plan));complete(p5root,['INDEX.json']);complete(p6root,['INDEX.json'])
    tc=root/'tc';write(tc/'PRIMARY.json',dict(timing_mode='logged_delta'));complete(tc,['PRIMARY.json'])
    write(content/'RECORDS.json',records);np.save(content/'VECTORS.npy',np.array(vectors,dtype=np.float32),allow_pickle=False)
    write(content/'PLAN.json',dict(pins={'SESSIONS.json':filehash(root/'SESSIONS.json')}));complete(content,['RECORDS.json','VECTORS.npy','PLAN.json'])
    write(audit/'ROWS.json',auditrows);complete(audit,['ROWS.json'])
    inputs=dict(repo_root=str(root),foundation_complete=str(p2root/'COMPLETE.json'),foundation_plan=str(plan),session_index=str(p2root/'INDEX.json'),
        prepared_sessions=str(root/'SESSIONS.json'),raw_roster=str(root/'ROSTER.json'),source_pins=str(root/'SOURCE_PINS.json'),
        p6_index=str(p6root/'INDEX.json'),p6_completion=str(p6root/'COMPLETE.json'),p5_index=str(p5root/'INDEX.json'),p5_completion=str(p5root/'COMPLETE.json'),
        tc_primary=str(tc/'PRIMARY.json'),tc_completion=str(tc/'COMPLETE.json'),content_complete=str(content/'COMPLETE.json'),selection_audit_complete=str(audit/'COMPLETE.json'))
    write(root/'INPUTS.json',inputs);return inputs


@pytest.mark.parametrize('mode,state',[('positive','positive'),('null','null'),('negative','negative')])
def test_serialized_signed_null_reverse_fresh_process(tmp_path,mode,state):
    inputs=fixture(tmp_path/'sources',mode);out=tmp_path/'output';start=time.monotonic()
    result=card.execute(out,inputs,card.CONFIG)
    assert result['primary']['state']==state
    assert result['permutations']==200
    assert result['source_audit']['canonical_choice_disagreements']>0
    assert 0<=result['primary_session_permutation_null']['invalid_draws']<=200
    assert read(out/'FIRST_TENTH.json')['completed_permutations']==20
    code='import json,sys;from pathlib import Path;from runners.drive.cards.timing_pmap import verify,CONFIG;print(verify(Path(sys.argv[1]),json.load(open(sys.argv[2])),CONFIG))'
    child=subprocess.run([sys.executable,'-c',code,str(out),str(tmp_path/'sources/INPUTS.json')],capture_output=True,text=True,
        env={**os.environ,'PYTHONHASHSEED':'919','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'},timeout=90)
    assert child.returncode==0,child.stdout+child.stderr
    write(tmp_path/'FIXTURE_RECEIPT.json',dict(mode=mode,elapsed_seconds=time.monotonic()-start,
        output_bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),fresh_exit=child.returncode))


def test_identity_ties_missing_and_fixed_probe_gallery():
    a=np.eye(6);r=stats.identify(a,a)
    assert r['accuracy']==1
    r=stats.identify(np.ones((6,4)),np.ones((6,4)))
    assert r['accuracy']==pytest.approx(1/6) and r['tied_probes']==6
    with pytest.raises(ValueError,match='absent'):stats.identify(np.full((6,4),np.nan),np.ones((6,4)))
    a=np.eye(6);a[0,0]=np.nan;r=stats.identify(a,np.eye(6));assert r['missing_A']==1 and r['writers']==6
    # Probe repeats do not remove competitors from the fixed gallery.
    assert stats.interval([1,0,1,0,1,0])['writers']==6


def test_dictionary_ties_unicode_and_prompt_blocks():
    rows=[dict(word_counts={f'w{i:03}':1 for i in range(110)},punctuation_counts={'!':2},bigram_counts={' a':5})]
    d=source.dictionary(rows)
    assert d['words']==[f'w{i:03}' for i in range(100)] and d['punctuation']==['!']
    rows=[dict(session=str(i),writer='w',prompt=str(i%2),timestamp=i) for i in range(4)]
    h,e=stats.split_sessions(rows);assert not e
    assert [{r['prompt'] for r in part} for part in h['w']]==[{'0'},{'1'}]


def test_raw_unicode_deletion_internal_insert_and_no_keypress():
    events=[dict(eventName='system-initialize',eventTimestamp=0,currentDoc='P\n'),
        dict(eventName='suggestion-open',eventTimestamp=1),dict(eventName='suggestion-select',eventTimestamp=2),
        dict(eventName='insert',eventSource='api',eventTimestamp=3,textDelta={'ops':[{'retain':1},{'insert':'a😀b'}]}),
        dict(eventName='insert',eventSource='user',eventTimestamp=4,textDelta={'ops':[{'retain':2},{'insert':'x'}]}),
        dict(eventName='delete',eventSource='user',eventTimestamp=5,textDelta={'ops':[{'retain':3},{'delete':2}]}),
        dict(eventName='insert',eventSource='user',eventTimestamp=6,textDelta={'ops':[{'retain':4},{'insert':'yz'}]})]
    canonical=dict(events=[dict(ordinal=1,usable=True,decision='edit',verified_insertion=True,matched_option_indices=[0],options=[dict(index=0,original='a😀b')])])
    r=source.raw_features(events,dict(final_document='Paxbyz\n'),canonical)
    assert r['accepted_characters']==3 and r['edited_accepted_characters']==1
    assert r['internal_added_characters']==1
    assert r['bigram_counts'].get('yz')==1 and 'yz' not in r['bigram_intervals']


def test_source_refusal_and_checkpoint_resume(tmp_path):
    inputs=fixture(tmp_path/'sources');out=tmp_path/'run/output'
    write(out/'YIELD_REQUEST.json',dict(reason='fixture'))
    first=card.execute(out,inputs,card.CONFIG);assert first['status']=='yielded' and first['completed']==1
    old=list((out/'sessions').glob('*.json.gz'))[0];oldbytes=old.read_bytes()
    (out/'YIELD_REQUEST.json').unlink()
    result=card.execute(out,inputs,card.CONFIG);assert result['primary']['state']=='positive' and old.read_bytes()==oldbytes
    raw=Path(inputs['repo_root'])/'raw/w0_s0.jsonl';raw.write_text(raw.read_text(encoding='utf8')+'\n',encoding='utf8')
    with pytest.raises(ValueError,match='source'):card.verify(out,inputs,card.CONFIG)
    with pytest.raises(ValueError,match='configuration'):card.execute(out,inputs,{**card.CONFIG,'permutations':1})


def test_forged_saved_session_rejected_even_rebound(tmp_path):
    from runners.drive.cards.timing_stats import bind
    inputs=fixture(tmp_path/'sources');out=tmp_path/'output';card.execute(out,inputs,card.CONFIG)
    binding=read(out/'TIMING_BINDINGS.json');p=out/'sessions/w0_s0.json.gz';r=gzread(p);r['requests']+=1;p.unlink();gzwrite(p,r)
    (out/'TIMING_BINDINGS.json').unlink()
    bind(out,inputs,card.CONFIG,list(binding['outputs']))
    with pytest.raises(ValueError,match='reconstruct'):card.verify(out,inputs,card.CONFIG)


def test_fake_coverage_has_no_redraw(tmp_path):
    inputs=fixture(tmp_path/'sources');s=source.Sources(inputs);rows=[s.session(k) for k in sorted(s.p2)]
    d=source.dictionary(rows);p=stats.prepare(rows,d)
    assignment={r['session']:('onlyA' if r['prompt']=='p0' else 'onlyB') for r in rows}
    f=stats.fake_one(rows,d,p,assignment);assert f['primary'] is None
    report=stats.summarize(p,[f]);assert report['fake_channels']['style']['own_minus_fake']['state']=='invalid'


def test_zero_draw_range_invalid_p_and_paired_fake(tmp_path):
    exact=stats.interval([5/6]*6)
    assert exact['bootstrap_se']==0 and exact['z'] is None and exact['approximate_two_sided_wald_p'] is None
    inputs=fixture(tmp_path/'sources');s=source.Sources(inputs);rows=[s.session(k) for k in sorted(s.p2)]
    d=source.dictionary(rows);p=stats.prepare(rows,d)
    # Shift complete A sessions by one identity and B by two. Both sides keep
    # exact real session counts/prompt support, but stable identity is broken.
    assignment={r['session']:'w'+str((int(r['writer'][1:])+(1 if r['prompt']=='p0' else 2))%6) for r in rows}
    f=stats.fake_one(rows,d,p,assignment);report=stats.summarize(p,[f]*200)
    assert report['fake_channels']['style']['own_minus_fake']['state']=='positive'
    invalid={**f,'primary':None};report=stats.summarize(p,[f,invalid])
    assert report['primary_session_permutation_null']['state']=='invalid'
    assert report['primary_session_permutation_null']['one_sided_p'] is None


def test_control_timing_projection_survives_partial_resume(tmp_path,monkeypatch):
    inputs=fixture(tmp_path/'sources');out=tmp_path/'run/output';real_progress=card.progress
    def progress(path,value):
        real_progress(path,value)
        if Path(path).name=='PROGRESS.json' and value.get('phase')=='permutations' and value['done']==5:
            write(out/'YIELD_REQUEST.json',dict(reason='fixture control boundary'))
    monkeypatch.setattr(card,'progress',progress)
    assert card.execute(out,inputs,card.CONFIG)['status']=='yielded'
    saved={p.name:p.read_bytes() for p in (out/'permutations').glob('*')}
    old_time=sum(read(p)['elapsed_seconds'] for p in (out/'permutations').glob('*.receipt.json'))
    monkeypatch.setattr(card,'progress',real_progress);(out/'YIELD_REQUEST.json').unlink()
    card.execute(out,inputs,card.CONFIG)
    first=read(out/'FIRST_TENTH.json')
    assert first['measured_control_seconds']>=old_time
    assert first['projected_cpu_seconds']==pytest.approx(2*(first['source_phase_seconds']+first['resume_and_checkpoint_overhead_seconds']+10*first['measured_control_seconds']))
    assert all((out/'permutations'/name).read_bytes()==value for name,value in saved.items())
