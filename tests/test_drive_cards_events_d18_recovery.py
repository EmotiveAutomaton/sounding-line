import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
from runners.drive.cards import events_d18 as original
from runners.drive.cards import events_d18_recovery as card
from runners.drive.cards import events_d18_spans_recovery as spans
from runners.drive.cards.events_d4 import save, read_sealed
from runners.drive.timeline import rebuild
from runners.stage9.coauthor import replay, units
from tests.test_drive_cards_events_d18 import Stream, event, full_fixture, FakeEncoder, write


def repeated_source():
    options=[dict(index=0,original='BBBB.',trimmed='BBBB.'),dict(index=1,original='CCCCCCC',trimmed='CCCCCCC')]
    s=Stream();owner=len(s.events)
    s.events.append(event(len(s.events),'suggestion-open',currentSuggestions=options))
    s.events.append(event(len(s.events),'suggestion-select',currentSuggestionIndex=0))
    s.add([{'retain':len(s.doc)-1},{'insert':'BBBB.'}],source='api')
    s.add([{'retain':4},{'delete':1},{'insert':'X'}],name='text-delete')
    s.events.append(event(len(s.events),'suggestion-reopen',currentSuggestions=options))
    s.events.append(event(len(s.events),'suggestion-select',currentSuggestionIndex=1))
    s.add([{'retain':len(s.doc)-1},{'insert':'CCCCCCC'}],source='api')
    s.insert('typed original',True);s.insert('typed survivor')
    return s.events,rebuild(s.events,[]),owner


def test_canonical_repeated_selection_keeps_document_and_excludes_both_spans():
    events,timeline,owner=repeated_source();canonical=replay(events)
    assert canonical['reconstructed'] and not canonical['errors'] and canonical['final_document']==timeline['final_document']
    assert canonical['events'][0]['exclusion']=='selection has no active undecided set' and not canonical['events'][0]['usable']
    with pytest.raises(ValueError,match='duplicate accepted'):original.spans.extract(events,timeline)
    result=spans.extract(events,timeline,[])
    invalid=[r for r in result['spans'] if r['origin']=='unusable_selection']
    assert len(invalid)==2 and [r['source_ordinal'] for r in invalid]==[owner,owner]
    assert result['support']['unusable_selection_original_codepoints']==12
    assert result['support']['accepted_spans']==0
    pairs,excluded=spans.match(result['spans'])
    assert all(p['origin']=='typed' for p in pairs)
    assert sum(e['reason']=='canonical repeated-selection origin excluded' for e in excluded)==2
    assert result['canonical_exclusions']==[dict(source_ordinal=owner,reason='selection has no active undecided set',source_spans=2)]


def test_usable_missing_wrong_exclusion_and_present_p2_never_bypass(monkeypatch):
    events,timeline,owner=repeated_source();canonical=replay(events)
    for mode in ('usable','missing','other_reason','unverified','bad_final'):
        changed=copy.deepcopy(canonical)
        if mode=='usable':changed['events'][0]['usable']=True
        elif mode=='missing':changed['events']=[]
        elif mode=='other_reason':changed['events'][0]['exclusion']='different semantic failure'
        elif mode=='unverified':changed['events'][0]['verified_insertion']=False
        else:changed['final_document']='changed'
        monkeypatch.setattr(spans,'replay',lambda events,c=changed:c)
        with pytest.raises(ValueError,match='canonical'):spans.extract(events,timeline,[])
    monkeypatch.setattr(spans,'replay',replay)
    with pytest.raises(ValueError,match='canonical exclusion'):spans.extract(events,dict(timeline,decisions=[dict(ordinal=owner)]),[])
    with pytest.raises(ValueError,match='canonical exclusion'):spans.extract(events,timeline,[owner])


def test_ordinary_extraction_is_byte_value_identical():
    s=Stream();s.insert('deleted',True);s.insert('retains')
    events,timeline=s.result()
    assert spans.extract(events,timeline,[])==original.spans.extract(events,timeline)
    assert spans.match(spans.extract(events,timeline)['spans'])==original.spans.match(original.spans.extract(events,timeline)['spans'])


def recovery_fixture(root,monkeypatch=None,model_identity_path=None):
    inputs=full_fixture(root/'sources',writers=2,model_identity_path=model_identity_path)
    index=card.read(inputs['p2_index']);roster=card.read(inputs['source_roster']);events,timeline,owner=repeated_source()
    raw=Path(inputs['source_root'])/roster[1]['path'];raw.write_text(''.join(json.dumps(e)+'\n' for e in events),encoding='utf8')
    p2=Path(inputs['p2_index']).parent/index[1]['file'];write(p2,timeline)
    roster[1]['source_sha256']=card.filehash(raw);index[1]['sha256']=card.filehash(p2)
    write(Path(inputs['source_roster']),roster);write(Path(inputs['p2_index']),index)
    p5=card.read(inputs['p5_inputs'])
    for k in ('p2_index','source_roster'):p5['sha256'][k]=card.filehash(inputs[k])
    write(Path(inputs['p5_inputs']),p5)
    p5root=Path(inputs['p5_completion']).parent
    write(Path(inputs['p5_completion']),dict(status='COMPLETE',fresh_process_verified=True,
        outputs={Path(inputs[k]).relative_to(p5root).as_posix():card.filehash(inputs[k]) for k in ('p5_inputs','p5_summary')}))
    failed=root/'failed';output=failed/'output';output.mkdir(parents=True)
    pins=original.input_pins(inputs)
    write(output/'BINDING.json',dict(paths=inputs,config=card.CONFIG,pins=pins))
    # Real failed-source fixture, with the first unchanged session's exact
    # synthetic extraction saved as it would be before the repeated-selection.
    item=original.source(inputs)[0];raw,p2=original.source_paths(item,inputs)
    unit=original.extract_session(item,raw,p2,card.CONFIG);vectors,scopes=FakeEncoder().encode(unit['text_inputs'])
    unit=original.score_session(unit,vectors,scopes);unit['elapsed_seconds']=.25
    import hashlib
    stem=hashlib.sha256(item['session'].encode()).hexdigest()[:24]
    save(output/'sessions'/(stem+'.npy'),vectors);save(output/'sessions'/(stem+'.json'),unit)
    bad=original.source(inputs)[1];raw,p2=original.source_paths(bad,inputs)
    with pytest.raises(ValueError,match='duplicate accepted'):
        original.extract_session(bad,raw,p2,card.CONFIG)
    original_file=Path(original.__file__);old_spans=Path(original.spans.__file__)
    write(failed/'PLAN.json',dict(module='runners.drive.cards.events_d18',inputs=inputs,config=card.CONFIG,
        pins={str(original_file):card.filehash(original_file),str(old_spans):card.filehash(old_spans),**pins}))
    write(failed/'FAILED.json',dict(status='FAILED',error='duplicate accepted span origin',synthetic=True))
    result=dict(inputs,failed_plan=str(failed/'PLAN.json'),failed_binding=str(output/'BINDING.json'),failed_receipt=str(failed/'FAILED.json'))
    return result,output


def test_full_recovery_byte_reuse_yield_fresh_child_and_changed_old_pin(tmp_path,monkeypatch):
    inputs,failed=recovery_fixture(tmp_path);output=tmp_path/'retry';monkeypatch.setattr(card,'Encoder',FakeEncoder)
    extract=card.extract_session;calls=[]
    def collect(*args):calls.append(args[0]['session']);return extract(*args)
    monkeypatch.setattr(card,'extract_session',collect)
    # Stop at first restored boundary, before any previously unsaved extraction.
    original_save=card.save
    def with_yield(path,value):
        original_save(path,value)
        if path.name=='RECOVERY.json':write(output/'YIELD_REQUEST.json',{})
    monkeypatch.setattr(card,'save',with_yield)
    assert card.execute(output,inputs,card.CONFIG)['status']=='yielded' and not calls
    monkeypatch.setattr(card,'save',original_save);(output/'YIELD_REQUEST.json').unlink()
    result=card.execute(output,inputs,card.CONFIG)
    assert len(calls)==7 and result['sessions']==8 and len(result['canonical_source_exclusions'])==1
    for old in (failed/'sessions').glob('*'):
        assert (output/'sessions'/old.name).read_bytes()==old.read_bytes()
    request=tmp_path/'VERIFY.json';write(request,dict(inputs=inputs,config=card.CONFIG,output=str(output)))
    code='import json,sys;from pathlib import Path;from runners.drive.cards.events_d18_recovery import verify;r=json.load(open(sys.argv[1]));print(json.dumps(verify(Path(r["output"]),r["inputs"],r["config"])))'
    child=subprocess.run([sys.executable,'-B','-c',code,str(request)],text=True,capture_output=True,env=dict(os.environ,PYTHONHASHSEED='111'))
    assert child.returncode==0,child.stderr
    assert json.loads(child.stdout)['verified']
    with pytest.raises(ValueError,match='never rerun'):card.execute(output,inputs,card.CONFIG)
    old=next((failed/'sessions').glob('*.json'));old.write_text(old.read_text(encoding='utf8')+' ',encoding='utf8')
    with pytest.raises(ValueError,match='checkpoint hash'):card.verify(output,inputs,card.CONFIG)
