import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from runners.drive.cards import week3_insertion_provenance_h1 as h
from runners.drive.cards.timing_events import accepted_lifetimes


@pytest.mark.parametrize('kind,surviving', [('plain',4),('newline',4),('rewrite',4),('edited',2),('deleted',0)])
def test_known_original_units_and_legacy_parity(kind,surviving):
    events,timeline=h.fixture(kind)
    result=h.reconstruct(events,timeline)
    assert result['eligible']=={1:dict(original_utf16=4,surviving_utf16=surviving)}
    old=accepted_lifetimes(events,timeline['final_document'])
    assert all(old[1][k]==v for k,v in result['eligible'][1].items())


def test_repeated_and_unmatched_remain_in_physical_census():
    for kind,count in [('repeated',2),('unmatched',1)]:
        result=h.reconstruct(*h.fixture(kind))
        assert not result['eligible'] and len(result['physical'])==count
        assert all(not r['eligible'] and r['exclusion'] for r in result['physical'])
        assert len({r['insertion_ordinal'] for r in result['physical']})==count
        assert sum(r['original_utf16'] for r in result['physical'])==9


def test_missing_canonical_eligibility_is_refused():
    events,timeline=h.fixture('plain'); timeline['decisions']=[]
    with pytest.raises(ValueError,match='eligible population'): h.reconstruct(events,timeline)


def test_source_and_final_provenance_corruption_refused():
    events,timeline=h.fixture('plain')
    t=copy.deepcopy(timeline); t['final_document']+='bad'
    with pytest.raises(ValueError,match='final document'): h.reconstruct(events,t)
    t=copy.deepcopy(timeline)
    next(r for r in t['final_spans'] if r['origin']=='accepted')['end_utf16']+=1
    with pytest.raises(ValueError,match='survival differs'): h.reconstruct(events,t)
    events[3]['textDelta']={'ops':[{'retain':9999},{'insert':'x'}]}
    with pytest.raises(ValueError,match='canonical document'): h.reconstruct(events,timeline)


def test_full_serialized_native_replay_and_mutation(tmp_path):
    h.execute(tmp_path,{},h.CONFIG)
    code='from runners.drive.cards import week3_insertion_provenance_h1 as h;import sys;assert h.verify(sys.argv[1],{},h.CONFIG)["verified"]'
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(tmp_path)],check=True,
        env=dict(os.environ,PYTHONHASHSEED='431'),timeout=60)
    p=next((tmp_path/'sessions').glob('*.json')); x=json.loads(p.read_text()); x['reconstruction']['final_utf16']+=1
    p.write_text(json.dumps(x),encoding='utf8')
    with pytest.raises(ValueError,match='independent source'): h.verify(tmp_path,{},h.CONFIG)


def test_configuration_cannot_silently_reduce_full_population(tmp_path):
    with pytest.raises(ValueError,match='frozen source'): h.execute(tmp_path,{'source_inputs':'unused'},dict(h.CONFIG,mode='corpus',expected_sessions=10))
