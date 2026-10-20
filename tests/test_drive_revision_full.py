"""Two-session native fixture exercises exact reuse and new source replay."""
from pathlib import Path
import pytest
from runners.drive.cards import timing_revision_full as full
from runners.drive.cards.timing_revision_source import Sources
from runners.drive.cards.timing_revision_input import relative
from runners.drive.cards.timing_p6 import gzip_equal,gzread
from tests.test_drive_cards_timing_revision_source import fixture as single,save,seal,read,filehash

CONFIG=dict(mode='constructed',expected_sessions=2,pilot_sessions=1,cumulative_wall_seconds=120)

def fixture(root):
    root=Path(root);original=single(root/'source');source=Path(original['repo_root'])
    raw=source/'raw/t.jsonl';raw.write_bytes((source/'raw/s.jsonl').read_bytes())
    for key,name in [('session_index','t.json'),('p6_index','t.json.gz')]:
        index=read(original[key]);prior=Path(original[key]).parent/index[0]['file'];value=gzread(prior) if prior.suffix=='.gz' else read(prior)
        value.update(session='t',writer='z');target=Path(original[key]).parent/name;save(target,value)
        index.append(dict(session='t',writer='z',file=name,sha256=filehash(target)));save(original[key],index)
    rows=read(original['prepared_sessions']);rows.append(dict(rows[0],session='t',writer='z'));save(original['prepared_sessions'],rows)
    rows=read(original['raw_roster']);rows.append(dict(session='t',path='raw/t.jsonl',source_sha256=filehash(raw)));save(original['raw_roster'],rows)
    pins=read(original['source_pins']);pins['raw/t.jsonl']=filehash(raw);save(original['source_pins'],pins);seal(original)
    pilot=root/'constructed-pilot';out=pilot/'output';value=Sources(original).session('s');gzip_equal(out/relative('s'),value)
    save(out/'INDEX.json',[dict(session='s',file=relative('s'),sha256=filehash(out/relative('s')),source_hashes=value['source_hashes'])])
    save(out/'INPUTS.json',dict(selected=['s']));save(out/'SUMMARY.json',dict(constructed=True,selected_sessions=1))
    save(pilot/'PLAN.json',dict(inputs=original,module=__name__,config={'constructed':True}))
    save(pilot/'VERIFIED.json',dict(verified=True,full_uncached_replay=True,summary=read(out/'SUMMARY.json')))
    save(pilot/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,synthetic_fixture=True,outputs={p.relative_to(pilot).as_posix():filehash(p) for p in pilot.rglob('*') if p.is_file()}))
    return dict(original,pilot_complete=str((pilot/'COMPLETE.json').resolve()))

def test_reuse_new_work_reentry_and_fresh_verification(tmp_path):
    inputs=fixture(tmp_path/'source');out=tmp_path/'out'
    summary=full.execute(out,inputs,CONFIG);assert summary['original_occurrences']==4 and summary['retained_changes']==2
    prior=(Path(inputs['pilot_complete']).parent/'output'/relative('s')).read_bytes();assert (out/relative('s')).read_bytes()==prior
    assert read(out/'FIRST_TENTH.json')['new_sessions']==1
    assert full.execute(out,inputs,CONFIG)==summary
    assert full.verify(out,inputs,CONFIG)['full_uncached_replay']

def test_yield_prefix_resume_and_raw_tamper(tmp_path):
    inputs=fixture(tmp_path/'source');out=tmp_path/'out';out.mkdir();save(out/'YIELD_REQUEST.json',{})
    assert full.execute(out,inputs,CONFIG)['status']=='yielded'
    assert not (out/'FIRST_TENTH.json').exists()
    (out/'YIELD_REQUEST.json').unlink();full.execute(out,inputs,CONFIG)
    raw=Path(inputs['repo_root'])/'raw/t.jsonl';raw.write_bytes(raw.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='raw revision source'):full.verify(out,inputs,CONFIG)

@pytest.mark.parametrize('change',['pilot','new','scope','unverified','ceiling'])
def test_refusals(tmp_path,change):
    inputs=fixture(tmp_path/'source');out=tmp_path/'out';full.execute(out,inputs,CONFIG)
    if change=='pilot':(Path(inputs['pilot_complete']).parent/'output'/relative('s')).write_bytes(b'changed')
    if change=='new':(out/relative('t')).write_bytes(b'changed')
    if change=='scope':
        with pytest.raises(ValueError):full.execute(out,inputs,dict(CONFIG,expected_sessions=3))
        return
    if change=='unverified':
        p=Path(inputs['pilot_complete']);v=read(p);v['fresh_process_verified']=False;save(p,v)
    if change=='ceiling':save(out/'ACTIVE_TIME.json',dict(seconds=121))
    with pytest.raises((ValueError,TimeoutError)):full.verify(out,inputs,CONFIG)

def execute(output,inputs,config):
    value=full.execute(output,inputs,config)
    assert value['original_occurrences']==4 and value['retained_pilot_sessions']==1 and value['retained_changes']==2
    return value

def verify(output,inputs,config):return full.verify(output,inputs,config)
