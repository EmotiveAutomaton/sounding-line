"""Exact zero-option reopens, immutable parity, wall charge and source refusals."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import pytest

from runners.drive.cards import timing_d33_supported_recovery as card
from runners.drive.cards import timing_d33_supported as original
from runners.drive.cards import timing_d33_supported_source as source
from runners.drive.cards.timing_census import read,write,filehash
from runners.drive.cards.timing_p6 import gzread
from runners.drive.cards.timing_pmap_source import bound_record
from runners.drive.cards.timing_revision_source import Sources as RawSources,INPUTS as RAW_INPUTS

REPO=Path(__file__).resolve().parents[1]
PRIVATE=REPO/'.agent-state/drive-20261017/builder2'


def fixture_events():
    return [dict(eventName='system-initialize',eventTimestamp=0,currentDoc='prompt '),
        dict(eventName='suggestion-open',eventTimestamp=1,currentSuggestions=[dict(index=8,original='hidden',trimmed='shown')]),
        dict(eventName='suggestion-reopen',eventTimestamp=2,currentSuggestions=[]),
        dict(eventName='insert',eventTimestamp=3,eventSource='user',textDelta={'ops':[{'retain':7},{'insert':'future '}]}),
        dict(eventName='suggestion-open',eventTimestamp=4,currentSuggestions=[dict(index=3,original='later',trimmed='later')])]


def words():
    return [dict(index=i,token=token,ordinal=3,population_probability=.05,context=[],is_word=True)
            for i,token in enumerate(['shown','future','later','hidden','prompt'])]


def actual_inputs():
    root=REPO/'results/phase_2_4_stage_15/raw/drive-wave-20261017-w1/D33.pair-supported'
    p=read(root/'PLAN.json')
    return dict(p['inputs'],failed_plan=str(root/'PLAN.json'),failed_record=str(root/'FAILED.json'),failed_owner=str(root/'OWNER.json'))


def test_literal_reopen_preserves_source_clock_and_fresh_process(tmp_path):
    events=fixture_events();before=deepcopy(events);value,audit=card.screen_covariates(events,words())
    assert events==before and audit==[2]
    assert [value[i]['on_screen'] for i in range(5)]==[1,0,0,0,1]
    oracle=deepcopy(events);oracle[2]['eventName']='no-new-display'
    assert value==source.screen_covariates(oracle,words())
    call=tmp_path/'CALL.json';write(call,dict(events=events,words=words(),expected={str(k):v for k,v in value.items()}))
    code="import sys,json;from runners.drive.cards.timing_d33_supported_recovery import screen_covariates;d=json.load(open(sys.argv[1],encoding='utf8'));v,a=screen_covariates(d['events'],d['words']);assert a==[2] and {str(k):x for k,x in v.items()}==d['expected']"
    child=subprocess.run([sys.executable,'-c',code,str(call)],cwd=REPO,capture_output=True,text=True,timeout=30,
        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name=='nt' else 0)
    assert child.returncode==0,child.stderr


@pytest.mark.parametrize('name,payload,prior',[('suggestion-open',[],True),('suggestion-reopen',[],False),
    ('suggestion-reopen','[]',True),('suggestion-reopen',None,True),('suggestion-reopen',{},True),
    ('suggestion-reopen',[dict(index=1,original='x')],True)])
def test_only_literal_empty_reopen_after_known_display_is_admitted(name,payload,prior):
    events=fixture_events();events[2].update(eventName=name,currentSuggestions=payload)
    if not prior:events[1]['eventName']='no-display'
    with pytest.raises(ValueError):card.screen_covariates(events,words())


def test_actual_saved_prefix_and_all_affected_source_sessions(tmp_path):
    started=time.perf_counter();inputs=actual_inputs();base,old,prior,files=card.validate(inputs,original.configuration('pair'))
    assert prior==318.406307 and len(files)==10
    raw=RawSources({k:base[k] for k in RAW_INPUTS});diag=read(PRIVATE/'D33_SCREEN_SOURCE_DIAGNOSIS_20261018.json')
    ids=sorted({p.name.removesuffix('.json.gz') for p in files}|{e['session'] for e in diag['exception_events']})
    obj=object.__new__(card.Sources);obj.raw=raw;obj.inputs=base;obj.lookup={};obj.output=tmp_path/'audit';obj.verifying=False;obj.audits={}
    for sid in ids:obj.lookup[sid]=bound_record(base['p6_index'],raw.p6[sid])
    equal=0
    for sid in ids:
        result=obj.covariates(sid)
        if (old/'sessions'/(sid+'.json.gz')).exists():
            assert result==gzread(old/'sessions'/(sid+'.json.gz'));equal+=1
    summary=card.audit_summary([obj]);assert equal==10 and summary['literal_empty_reopens']==5 and summary['affected_sessions']==4
    # A resealed/output-only audit cannot replace authenticated raw evidence.
    sid=next(s for s,v in obj.audits.items() if v['literal_empty_reopen_ordinals'])
    audit_path=obj.output/'schema-audit'/(sid+'.json');forged=read(audit_path);forged['literal_empty_reopen_ordinals']=[]
    audit_path.write_text(json.dumps(forged),encoding='utf8');obj.verifying=True
    with pytest.raises(ValueError,match='audit differs'):obj.covariates(sid)
    write(tmp_path/'ACTUAL_PARITY.json',dict(seconds=time.perf_counter()-started,source_sessions=len(ids),
        original_saved_covariates_equal=equal,empty_reopens=5,affected_sessions=4,prior_controller_seconds=prior,
        complete_raw_p6_replay=True,canonical_document_checks=True,source_text_disclosed=False,scientific_fit=False))


def test_wrapper_charges_original_wall_once_and_preserves_checkpoint_bytes(tmp_path,monkeypatch):
    inputs=actual_inputs();config=original.configuration('pair');output=tmp_path/'output';seen=[]
    def fake_function(code,environment):
        def run(out,values,cfg):
            charged=read(out/'ACTIVE_TIME.json')['seconds'];assert charged>=318.406307
            environment['write_equal'](out/'FIRST_TENTH.json',dict(projected_cpu_seconds=2*charged+200))
            assert read(out/'FIRST_TENTH.json')['projected_cpu_seconds']==pytest.approx(charged+200)
            seen.append(charged)
            return dict(status='yielded')
        return run
    monkeypatch.setattr(card,'FunctionType',fake_function)
    assert card.execute(output,inputs,config)['status']=='yielded'
    old=Path(inputs['failed_plan']).parent/'output'
    for p in (old/'sessions').glob('*.json.gz'):assert (output/'sessions'/p.name).read_bytes()==p.read_bytes()
    path=next((output/'sessions').glob('*.json.gz'));path.write_bytes(b'forged')
    with pytest.raises(ValueError,match='checkpoint bytes changed'):card.execute(output,inputs,config)
    assert len(seen)==1


def test_recovery_refuses_changed_population_or_config():
    inputs=actual_inputs()
    with pytest.raises(ValueError,match='exact single'):card.validate(inputs,original.configuration('pair2'))
    with pytest.raises(ValueError,match='exact single'):card.validate(inputs,dict(original.configuration('pair'),bootstrap_draws=25))
