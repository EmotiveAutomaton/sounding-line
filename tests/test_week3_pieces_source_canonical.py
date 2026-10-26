import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from runners.drive.cards import week3_pieces_input as original
from runners.drive.cards import week3_pieces_source_canonical as canonical
from runners.drive.cards.week3_pieces_input_recovery import canonical_clock,checked_clock
from runners.drive.cards.week3_pieces_effects import effect_windows
from runners.drive.cards.timing_census import read,write,filehash
from runners.drive.cards.timing_p6 import gzread,gzwrite
from runners.drive.timeline import rebuild
from tests import test_week3_pieces_input as base


def alias_events():
    epoch=1615189114123
    events=[dict(eventName='system-initialize',eventSource='api',eventTimestamp=epoch,currentDoc='abcd\n')]
    for t,position,char in [(100,1,'X'),(200,2,'Y')]:
        events.append(dict(eventName='text-insert',eventSource='user',eventTimestamp=epoch+t,
            textDelta={'ops':[{'retain':position},{'insert':char}]}))
    events.append(dict(eventName='system-close',eventTimestamp=epoch+100000))
    return events,[],None


def fixture(root):
    saved=base.fixture_events; base.fixture_events=alias_events
    try:sources=base.fixture_inputs(root/'source')
    finally:base.fixture_events=saved
    prep=root/'previous';config=dict(mode='constructed',expected_sessions=8,seed=20261026)
    with canonical_clock():original.execute(prep/'output',sources,config)
    write(prep/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
        outputs={p.relative_to(prep).as_posix():filehash(p) for p in prep.rglob('*') if p.is_file()}))
    bundle=root/'source_inputs.json';write(bundle,sources)
    return dict(source_inputs=str(bundle),previous_complete=str(prep/'COMPLETE.json'),
        previous_index=str(prep/'output/WB1_INPUT_INDEX.json'),previous_result=str(prep/'output/WB1_INPUT_RESULT.json'),
        previous_split=str(prep/'output/WB1_WRITER_SPLIT.json'),previous_edges=str(prep/'output/WB1_BIN_EDGES.json'))


def test_alias_cause_and_exact_repaired_future_anchor():
    events,menus,_=alias_events();timeline=rebuild(events,menus)
    with canonical_clock():old=original.extract_session(events,timeline)
    revision=next(a for a in old['actions'] if a['kind']=='revision')
    assert revision['source_ordinals']==[1,2] and revision['seconds']==.1
    with canonical.isolated_provenance():new=original.extract_session(events,timeline)
    revision=next(a for a in new['actions'] if a['kind']=='revision')
    assert revision['source_ordinals']==[1] and revision['seconds']==.1
    assert next(a for a in new['actions'] if a['kind']=='burst')['source_ordinals']==[1,2]
    occurrence=dict(source_ordinal=1,seconds=.1)
    assert effect_windows(events,timeline,[occurrence])[0]['full_followup']
    with pytest.raises(ValueError,match='anchor differs'):
        effect_windows(events,timeline,[dict(source_ordinal=2,seconds=.1)])


def test_each_input_is_immutable_and_patch_restores():
    shared=[1];actions=[dict(kind='revision',length=1,seconds=.1,source_ordinals=shared),
        dict(kind='insert',length=1,seconds=.1,source_ordinals=shared),
        dict(kind='insert',length=1,seconds=.2,source_ordinals=[2])]
    before=copy.deepcopy(actions);old=original.collapse_actions
    with pytest.raises(RuntimeError),canonical.isolated_provenance():
        result=original.collapse_actions(actions)
        assert result[0]['source_ordinals']==[1] and result[1]['source_ordinals']==[1,2]
        assert actions==before
        raise RuntimeError('test cleanup')
    assert original.collapse_actions is old


def test_full_serialized_canonical_replay_and_mutation_refusal(tmp_path):
    inputs=fixture(tmp_path);out=tmp_path/'canonical';config=dict(mode='constructed',expected_sessions=8,seed=20261026)
    result=canonical.execute(out,inputs,config)
    assert result['changed_sessions']==8 and result['changed_actions']==8
    assert canonical.verify(out,inputs,config)['complete_source_replay']
    manifest=tmp_path/'manifest.json';write(manifest,dict(output=str(out),inputs=inputs,config=config))
    code="import json,sys;from runners.drive.cards.week3_pieces_source_canonical import verify;x=json.load(open(sys.argv[1]));assert verify(**x)['verified']"
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(manifest)],check=True,timeout=60,
        env=dict(os.environ,PYTHONHASHSEED='341',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2'))
    d=read(out/'WB1_BIN_EDGES.json');d['burst']['median']+=1;(out/'WB1_BIN_EDGES.json').write_text(json.dumps(d),encoding='utf8')
    with pytest.raises(ValueError,match='aggregate changed'):
        canonical.verify(out,inputs,config)


def test_previous_provenance_tampering_is_not_an_allowed_correction(tmp_path):
    inputs=fixture(tmp_path);index_path=Path(inputs['previous_index'])
    item=read(index_path)[0];path=index_path.parent/item['file'];row=gzread(path)
    row['actions'][0]['source_ordinals']=[999]
    path.unlink();gzwrite(path,row)
    with pytest.raises(ValueError,match='predecessor session changed'):
        canonical.execute(tmp_path/'canonical',inputs,dict(mode='constructed',expected_sessions=8,seed=20261026))
