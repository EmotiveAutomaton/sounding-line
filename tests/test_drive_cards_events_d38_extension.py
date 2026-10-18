import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from runners.drive.cards import events_d38_extension as card
from runners.drive.cards.events_d39 import match_failures
from tests.test_drive_cards_events_d38 import full_fixture as primary_fixture, write


def menu(key,chosen=0,size=5):
    return dict(key=key,chosen=chosen,options=list(range(size)))


def test_offered_option_drop_and_binary_menu_sensitivity():
    window=dict(before=[menu('a',0,2),menu('b',0,5)],after=[menu('c',-1,2),menu('d',0,5)])
    result=card.overall_drop(window)
    assert result['drop']==pytest.approx(.25) and result['binary_drop']==.5
    assert result['counts']['before']==dict(menus=2,offered_options=7,accepted_menus=2)
    assert card.overall_drop(window,dict(a=-1,b=0,c=-1,d=0))['drop']==0
    with pytest.raises(ValueError,match='outside offered'):card.overall_drop(dict(before=[menu('a',5)],after=[menu('b')]))


def row(writer,kind,key,drop=0.,length=20,gap=10.,session_index=0):
    return dict(key=key,writer=writer,kind=kind,session=writer+str(session_index),session_index=session_index,
        ordinal=int(key[-1]),source_span_ordinal=0,deleted_codepoints=length,request_gap_seconds=gap,
        observed=dict(drop=drop,binary_drop=drop*5),outcome_shuffle=dict(drop=0.),next_menus=[dict(hovers=0)])


@pytest.mark.parametrize('sign,state',[(0,'null'),(1,'positive'),(-1,'negative')])
def test_known_null_positive_reversed_extension(sign,state):
    units=[]
    for wi in range(8):
        writer=str(wi)
        events=[row(writer,'model','m1',.2 if sign==1 else 0.),row(writer,'own','o2',.2 if sign==-1 else 0.)]
        units.append(dict(writer=writer,events=events,failures=dict(model=1,own=1),exclusions=[],menu_exclusions=[]))
    result=card.summarize(units,card.CONFIG)
    assert result['primary']['state']==state and result['primary']['effect']==pytest.approx(sign*.2)
    assert result['binary_menu_uptake_specification']['effect']==sign
    assert result['outcome_shuffle']['state']=='null'


def test_exact_d39_matching_covariates_replacement_and_unsupported_counts():
    events=[row('w','model','m1',length=20,gap=3,session_index=1),row('w','model','m2',length=20,gap=3,session_index=1),
        row('w','own','o3',length=20,gap=3,session_index=1),row('w','own','o4',length=25,gap=100,session_index=8),
        row('u','model','m5',length=100)]
    old,_=match_failures(events,1.25);matched,excluded=card.match(events,card.CONFIG)
    assert len(old)==len(matched)==2 and [m['own'] for m in matched]==['o3','o3']
    for a,b in zip(old,matched):
        for field in ('length_ratio','request_gap_difference','session_index_difference','match_distance'):
            assert a[field]==pytest.approx(b[field])
    assert any(e['key']=='m5' and 'no length' in e['reason'] for e in excluded)
    assert any(e['key']=='o4' and 'not used' in e['reason'] for e in excluded)


def test_equal_model_session_weight_after_matching():
    events=[row('w','model','m1',drop=.2),row('w','model','m2',drop=.2),
        row('w','model','m3',drop=0.,session_index=1),row('w','own','o4')]
    unit=dict(writer='w',events=events,failures=dict(model=3,own=1),exclusions=[],menu_exclusions=[])
    result=card.summarize([unit],card.CONFIG)
    assert result['writer_contrasts'][0]['difference']==pytest.approx(.1)
    assert result['primary']['state']=='invalid'


def complete(inputs):
    base=Path(inputs['d38_completion']).parent
    write(Path(inputs['d38_completion']),dict(status='COMPLETE',fresh_process_verified=True,
        outputs={Path(inputs[k]).relative_to(base).as_posix():card.filehash(inputs[k]) for k in ('d38_summary','d38_binding')}))


def full_fixture(root,writers=3,model_identity_path=None):
    inputs=primary_fixture(root,writers=writers,model_identity_path=model_identity_path)
    sessions=card.read(inputs['sessions']);failures=card.read(inputs['d39_failures'])
    for session in sessions:
        if session['timestamp']==0:
            for menu_row in session['rows']:
                if menu_row['ordinal']>=130:menu_row.update(handling='dismiss',inserted='')
    for failure in failures:
        failure.update(request_gap_seconds=10.,next_menus=[dict(hovers=0)])
        if failure['session_index']==1:
            text='Typed original span.'
            failure.update(kind='own',source_span_ordinal=125,deleted_text=text,deleted_codepoints=len(text))
    write(Path(inputs['sessions']),sessions);write(Path(inputs['d39_failures']),failures)
    write(Path(inputs['d39_inputs']),dict(paths={'sessions':inputs['sessions']},pins={inputs['sessions']:card.filehash(inputs['sessions'])}))
    d39=Path(inputs['d39_completion']).parent
    write(Path(inputs['d39_completion']),dict(status='COMPLETE',fresh_process_verified=True,
        outputs={Path(inputs[k]).relative_to(d39).as_posix():card.filehash(inputs[k]) for k in ('d39_failures','d39_inputs')}))
    binding=card.read(inputs['p5_inputs']);binding['sha256']['sessions']=card.filehash(inputs['sessions']);write(Path(inputs['p5_inputs']),binding)
    p5=Path(inputs['p5_completion']).parent
    write(Path(inputs['p5_completion']),dict(status='COMPLETE',fresh_process_verified=True,
        outputs={Path(inputs[k]).relative_to(p5).as_posix():card.filehash(inputs[k]) for k in ('p5_inputs','p5_summary')}))
    old_inputs=dict(inputs);base=root/'d38'
    inputs.update(d38_summary=str(base/'output/SUMMARY.json'),d38_binding=str(base/'output/BINDING.json'),d38_completion=str(base/'COMPLETE.json'))
    write(Path(inputs['d38_binding']),dict(paths=old_inputs,config=card.primary.CONFIG,pins=card.primary.input_pins(old_inputs)))
    write(Path(inputs['d38_summary']),dict(card='D38',primary=dict(state='positive'),extension_run=False,model_failures=writers,own_failures=writers))
    complete(inputs)
    return inputs


def test_actual_extension_yield_fresh_child_and_changed_input(tmp_path,monkeypatch):
    inputs=full_fixture(tmp_path/'source');output=tmp_path/'output';calls=[];original=card.extract_writer
    def extract(*args):
        calls.append(args[0]);result=original(*args)
        if len(calls)==1:write(output/'YIELD_REQUEST.json',{})
        return result
    monkeypatch.setattr(card,'extract_writer',extract)
    assert card.execute(output,inputs,card.CONFIG)['status']=='yielded'
    (output/'YIELD_REQUEST.json').unlink();result=card.execute(output,inputs,card.CONFIG)
    assert calls==['w0','w1','w2'] and result['primary']['state']=='positive'
    assert result['primary']['effect']==pytest.approx(1/3)
    assert result['binary_menu_uptake_specification']['effect']==1
    assert len(result['pairs'])==3 and not result['event_exclusions']
    request=tmp_path/'VERIFY.json';write(request,dict(inputs=inputs,config=card.CONFIG,output=str(output)))
    code='import json,sys;from pathlib import Path;from runners.drive.cards.events_d38_extension import verify;r=json.load(open(sys.argv[1]));print(json.dumps(verify(Path(r["output"]),r["inputs"],r["config"])))'
    child=subprocess.run([sys.executable,'-B','-c',code,str(request)],text=True,capture_output=True,env=dict(os.environ,PYTHONHASHSEED='7'))
    assert child.returncode==0,child.stderr
    assert json.loads(child.stdout)['verified']
    with pytest.raises(ValueError,match='never rerun'):card.execute(output,inputs,card.CONFIG)
    Path(inputs['d39_failures']).write_text(Path(inputs['d39_failures']).read_text()+' ')
    with pytest.raises(ValueError,match='input changed'):card.verify(output,inputs,card.CONFIG)


def test_conditional_route_missing_covariates_and_support(tmp_path):
    inputs=full_fixture(tmp_path/'source');data=card.source(inputs)
    modified=copy.deepcopy(data[3]);modified[0]['request_gap_seconds']=None
    unit=card.extract_writer('w0',*data[:3],modified,card.CONFIG)
    assert unit['exclusions'][0]['reason']=='missing next menu or finite matching covariates'
    assert card.summarize([unit],card.CONFIG)['primary']['state']=='invalid'
    modified=copy.deepcopy(data[3]);modified[0]['ordinal']=35
    unit=card.extract_writer('w0',*data[:3],modified,card.CONFIG)
    assert any(e['reason']=='fewer than five eligible menus on either side' for e in unit['exclusions'])
    value=card.read(inputs['d38_summary']);value['primary']['state']='null';write(Path(inputs['d38_summary']),value);complete(inputs)
    with pytest.raises(ValueError,match='does not open'):card.source(inputs)


def test_model_origin_excluded_but_own_deletion_has_no_originating_menu(tmp_path):
    inputs=full_fixture(tmp_path/'source');data=card.source(inputs)
    unit=card.extract_writer('w0',*data,card.CONFIG)
    model,own=unit['events']
    assert model['kind']=='model' and own['kind']=='own'
    for e in (model,own):
        assert e['window']['overlapping_keys']==[e['session']+'m12']
        assert len(e['window']['before'])==len(e['window']['after'])==10
        assert all(m['end_ordinal']<=125 for m in e['window']['before'])
        assert all(m['ordinal']>125 for m in e['window']['after'])
