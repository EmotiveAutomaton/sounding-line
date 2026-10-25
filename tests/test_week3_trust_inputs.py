import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import week3_trust_inputs as w
from runners.drive.cards.timing_census import write
from runners.stage9.coauthor import units


def session(sid='s0',writer='w0',failed=True,later_delete=False,retype=True):
    events=[dict(eventName='system-initialize',eventTimestamp=0,currentDoc='\n',eventSource='system')]
    choices=[];decisions=[];doc='';starts={};origins={}
    def add(name,source='system',ops=None,**kw):
        e=dict(eventName=name,eventSource=source,eventTimestamp=len(events)*1000,**kw)
        if ops is not None:e['textDelta']={'ops':ops}
        events.append(e)
    for i in range(18):
        add('suggestion-get');add('suggestion-open',currentTemperature=.7);origin=len(events)-1;origins[i]=origin
        add('suggestion-select');resolution=len(events)-1
        span='abcdefghij';starts[i]=len(units(doc));add('text-insert',ops=[{'retain':len(units(doc))},{'insert':span}]);doc+=span
        choices.append(dict(ordinal=origin,usable=True,decision='accept',verified_insertion=True,
                            matched_option_indices=[1],options=[dict(index=1,original=span),dict(index=0,original='other')]))
        decisions.append(dict(ordinal=origin,resolution_ordinal=resolution,handling='accept',latency_kind='observed'))
        if i==8:
            if failed:
                pos=starts[i];add('text-delete','user',[{'retain':pos},{'delete':8}]);doc=doc[:pos]+doc[pos+8:]
                if retype:add('text-insert','user',[{'retain':pos},{'insert':'abcd'}]);doc=doc[:pos]+'abcd'+doc[pos:]
            else:
                add('cursor-move');add('cursor-move')
    if later_delete:
        add('text-delete','user',[{'delete':10}]);doc=doc[10:]
    return dict(meta=dict(session=sid,writer=writer,prompt='p',timestamp=1),events=events,
                timeline=dict(decisions=decisions,final_document=doc+'\n'),
                canonical=dict(events=choices,final_document=doc+'\n'),p6={})


def fixture():return [session('s'+str(i),'w'+str(i//2),i%2==0) for i in range(4)]


def test_unicode_survival_is_at_anchor_not_final():
    f=session(later_delete=True);spans=w.history(f['events'],f['timeline'],f['canonical'])
    failed=next(r for r in spans.values() if r['failure_removed']==8)
    first=spans[min(spans)]
    assert w.kept(first,failed['failure_ordinal'])
    assert not w.kept(first,len(f['events'])-1)
    assert first['retention'][0][1]==10
    assert first['retention'][-1][1]==0


def test_run_counts_original_acceptance_history_and_pools_five():
    menu=[dict(origin=i,handling='accept') for i in range(8)]
    spans={i:dict(canonical=True,original_codepoints=10,retention=[(i,10),(100,0)]) for i in range(8)}
    assert w.run_length(menu,spans,7,20)==5
    assert w.run_length(menu,spans,7,100)==0
    menu[5]['handling']='dismiss'
    assert w.run_length(menu,spans,7,20)==1


def test_strict_retype_exact_thirty_sixty_seconds_and_position():
    f=session();spans=w.history(f['events'],f['timeline'],f['canonical']);s=next(x for x in spans.values() if x['failure_ordinal'] is not None)
    assert w.strict_retyped(f['events'],s)
    anchor=s['failure_ordinal'];f['events'][anchor+1]['eventTimestamp']=f['events'][anchor]['eventTimestamp']+60001
    assert not w.strict_retyped(f['events'],s)
    f=session(retype=False);s=next(x for x in w.history(f['events'],f['timeline'],f['canonical']).values() if x['failure_ordinal'] is not None)
    assert not w.strict_retyped(f['events'],s)


def test_five_menu_windows_and_same_delay_anchor_match():
    a=w.prepare_session(**session());b=w.prepare_session(**session('control',failed=False))
    f=a['failures'][0]
    assert len(f['window']['before'])==len(f['window']['after'])==5
    controls=w.matched_controls(f,a,[b])
    assert controls
    for c in controls:
        span=next(s for s in b['spans'] if s['origin']==c['origin'])
        assert c['anchor_seconds']-b['clocks'][span['inserted_ordinal']]==f['delay_seconds']
        assert (c['run_length'],c['decile'])==(f['run_length'],f['decile'])


def test_full_serialized_source_replay_and_unsupported_not_null(tmp_path):
    path=tmp_path/'source.json';write(path,fixture());inputs={'fixture':str(path)}
    config=dict(w.CONFIG,mode='constructed',expected_sessions=4,session_limit=4)
    out=tmp_path/'out';result=w.execute(out,inputs,config)
    assert result['summary']['matched_failures']>=2
    assert result['summary']['support_state']=='unsupported'
    assert w.execute(out,inputs,config)==result
    manifest=tmp_path/'manifest.json';write(manifest,dict(output=str(out),inputs=inputs,config=config))
    code="import json,sys;from runners.drive.cards.week3_trust_inputs import verify;x=json.load(open(sys.argv[1]));assert verify(x['output'],x['inputs'],x['config'])['verified']"
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(manifest)],check=True,timeout=60)
    path.write_text(path.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='replay differs'):w.verify(out,inputs,config)
