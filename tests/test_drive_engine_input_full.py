import json
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import engine_input_full as card, engine_input_pilot as pilot
from runners.drive.cards.timing_p6 import gzread
from runners.stage14.common import read, filehash
from tests.test_drive_engine_sources import fixture as one_source, save

CONFIG = dict(mode='constructed', expected_sessions=2, reuse_sessions=1, cumulative_wall_seconds=120)


def fixture(root):
    """Two source sessions; the second is reconstructed, the first reused."""
    source = root/'source'; inputs = one_source(source)
    raw = source/'raw/t.jsonl'; raw.write_bytes((source/'raw/s.jsonl').read_bytes())
    for prefix, suffix in [('p2', '.json'), ('p5/output', '.json.gz'), ('p6/output', '.json.gz')]:
        path = source/prefix/('s'+suffix)
        value = gzread(path) if path.suffix == '.gz' else read(path)
        value['session']='t'; save(source/prefix/('t'+suffix), value)
    p5 = source/'p5/output/t.json.gz'; value=gzread(p5)
    value['p2_sha256']=filehash(source/'p2/t.json');save(p5,value)
    rows=read(inputs['prepared_sessions']);rows.append(dict(rows[0],session='t'));save(inputs['prepared_sessions'],rows)
    rows=read(inputs['raw_roster']);rows.append(dict(session='t',path='raw/t.jsonl',source_sha256=filehash(raw)));save(inputs['raw_roster'],rows)
    pins=read(inputs['source_pins']);pins['raw/t.jsonl']=filehash(raw);save(inputs['source_pins'],pins)
    for prefix, folder, suffix in [('session','p2','.json'),('p5','p5/output','.json.gz'),('p6','p6/output','.json.gz')]:
        save(inputs[prefix+'_index'],[dict(session=s,writer='w',file=s+suffix,sha256=filehash(source/folder/(s+suffix))) for s in ['s','t']])
    save(inputs['foundation_plan'],dict(pins={Path(inputs[k]).relative_to(source.resolve()).as_posix():filehash(inputs[k])
        for k in ['prepared_sessions','raw_roster','source_pins']}))
    save(inputs['foundation_complete'],dict(status='COMPLETE',plan_sha256=filehash(inputs['foundation_plan']),
        outputs={'SESSION_INDEX.json':filehash(inputs['session_index'])}))
    for prefix in ['p5','p6']:
        binding=source/prefix/'output'/('INPUTS.json' if prefix=='p5' else 'P6_BINDINGS.json')
        value=read(binding)
        if prefix=='p5':
            value['config']['expected_sessions']=2
            for k,orig in [('p2_index','session_index'),('sessions','prepared_sessions'),('source_roster','raw_roster')]:
                value['sha256'][k]=filehash(inputs[orig])
        else:
            value['index_sha256']=filehash(inputs['p6_index'])
            value['inputs']={k:filehash(inputs[k]) for k in value['inputs']}
        save(binding,value)
        save(inputs[prefix+'_completion'],dict(status='COMPLETE',fresh_process_verified=True,
            outputs={p.relative_to(source/prefix).as_posix():filehash(p) for p in [Path(inputs[prefix+'_index']),binding]}))
    parent=root/'producer';out=parent/'output';config=dict(mode='constructed',expected_sessions=2,session_limit=2,cumulative_wall_seconds=120)
    pilot.execute(out,inputs,config);assert pilot.verify(out,inputs,config)['verified']
    save(parent/'PLAN.json',dict(module='runners.drive.cards.engine_input_pilot',inputs=inputs,config=config,
        pins={str(p.resolve()):filehash(p) for p in source.rglob('*') if p.is_file()}))
    save(parent/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
        outputs={p.relative_to(parent).as_posix():filehash(p) for p in parent.rglob('*') if p.is_file()}))
    return dict(source_completion=str((parent/'COMPLETE.json').resolve()))


def test_known_answer_fresh_process_reuse_and_immutable_reentry(tmp_path):
    inputs=fixture(tmp_path);out=tmp_path/'full'
    result=card.execute(out,inputs,CONFIG)
    assert result['primary_sessions']==2 and result['reused_sessions']==1 and result['new_sessions']==1
    assert [json.loads(x)['text'] for x in (out/'DOCUMENTS.jsonl').read_text().splitlines()]==['dog ','dog ']
    parent=Path(inputs['source_completion']).parent/'output'
    assert (out/pilot.relative('s')).read_bytes()==(parent/pilot.relative('s')).read_bytes()
    manifest=tmp_path/'RUN.json';save(manifest,dict(inputs=inputs,config=CONFIG))
    code=('import json,sys;from runners.drive.cards.engine_input_full import verify;'
          'p=json.load(open(sys.argv[1]));print(json.dumps(verify(sys.argv[2],p["inputs"],p["config"])))')
    actual=json.loads(subprocess.check_output([sys.executable,'-B','-c',code,str(manifest),str(out)],text=True))
    assert actual['verified'] and actual['fresh_source_replay_sessions']==1 and actual['authenticated_prior_replay_sessions']==1
    hashes=read(out/'TIMING_BINDINGS.json')['outputs']
    assert card.execute(out,inputs,CONFIG)==result
    assert hashes=={k:filehash(out/k) for k in hashes}


def test_saved_boundary_resume(tmp_path):
    inputs=fixture(tmp_path);out=tmp_path/'full';save(out/'YIELD_REQUEST.json',dict(reason='fixture pause'))
    assert card.execute(out,inputs,CONFIG)['status']=='yielded'
    original=(out/pilot.relative('s')).read_bytes();(out/'YIELD_REQUEST.json').unlink()
    assert card.execute(out,inputs,CONFIG)['status']=='complete'
    assert (out/pilot.relative('s')).read_bytes()==original and card.verify(out,inputs,CONFIG)['verified']


@pytest.mark.parametrize('kind',['source','parent','output','checkpoint','resealed'])
def test_corruption_refusal(tmp_path,kind):
    inputs=fixture(tmp_path);out=tmp_path/'full';card.execute(out,inputs,CONFIG)
    if kind=='source':
        p=tmp_path/'source/raw/t.jsonl';p.write_bytes(p.read_bytes()+b' ')
    elif kind=='parent':
        p=Path(inputs['source_completion']);v=read(p);v['fresh_process_verified']=False;save(p,v)
    elif kind=='output': (out/'DOCUMENTS.jsonl').write_bytes(b'{}\n')
    else:
        p=out/pilot.relative('t');v=gzread(p);v['occurrences'][0]['character_ids']=[100,101,102];save(p,v)
        if kind=='resealed':
            save(p.with_suffix('.sha256.json'),dict(sha256=filehash(p)))
            binding=read(out/'TIMING_BINDINGS.json')
            for key in binding['outputs']:binding['outputs'][key]=filehash(out/key)
            save(out/'TIMING_BINDINGS.json',binding)
    with pytest.raises(ValueError):card.verify(out,inputs,CONFIG)


def test_full_scope_and_cost_are_fixed():
    with pytest.raises(ValueError):card.validate({},card.CONFIG)
    with pytest.raises(ValueError):card.validate(dict.fromkeys(card.INPUTS,'x'),dict(card.CONFIG,cumulative_wall_seconds=28800))
    with pytest.raises(ValueError):card.validate({'source_completion':'x'},dict(CONFIG,reuse_sessions=2))


def test_cumulative_cost_reserves_reader_and_refuses_recharged_or_invalid_values():
    prior=1514.1829486000306;active=949.8856067999732
    receipt=dict(active_wall_seconds=active,total_charged_wall_seconds=prior+active)
    value=card.reserve_cost(prior,active,receipt,13500)
    assert value['remaining_after_source']>=value['reader_reserve']
    with pytest.raises(ValueError,match='reservation'):card.reserve_cost(prior,active,receipt,14500)
    with pytest.raises(ValueError,match='receipt'):card.reserve_cost(prior/2,active,receipt,13500)
    with pytest.raises(ValueError,match='receipt'):card.reserve_cost(prior,active,dict(receipt,active_wall_seconds=1),13500)
    with pytest.raises(ValueError,match='invalid'):card.reserve_cost(prior,float('nan'),receipt,13500)
