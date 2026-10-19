import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import engine_input_pilot as producer, engine_d33_consumer as consumer
from runners.stage14.common import read, filehash
from tests.test_drive_engine_sources import fixture as source_fixture, save

CONFIG=dict(mode='constructed', cumulative_wall_seconds=120)


def fixture(root):
    inputs=source_fixture(root/'source')
    config=dict(mode='constructed', expected_sessions=1, session_limit=1, cumulative_wall_seconds=120)
    parent=root/'producer';output=parent/'output'
    producer.execute(output,inputs,config)
    assert producer.verify(output,inputs,config)['verified']
    plan=dict(module='runners.drive.cards.engine_input_pilot',config=config,inputs=inputs,
              pins={str(p.resolve()):filehash(p) for p in (root/'source').rglob('*') if p.is_file()})
    save(parent/'PLAN.json',plan)
    complete=dict(status='COMPLETE',fresh_process_verified=True,
        outputs={p.relative_to(parent).as_posix():filehash(p) for p in parent.rglob('*') if p.is_file()})
    save(parent/'COMPLETE.json',complete)
    rows=[dict(writer='w',session='s',index=i,length=3,personal_surprise=.25,donor_surprise=-.3,
        population_surprisal=2.,log_pause=-.7,log_frequency=-4.,sentence_start=0,after_punctuation=1) for i in (0,1)]
    rows.append(dict(rows[0],session='outside'))
    save(root/'ROWS.json',rows)
    return dict(source_completion=str((parent/'COMPLETE.json').resolve()),rows_fixture=str((root/'ROWS.json').resolve()))


def test_full_handler_known_answer_fresh_serialized_replay_and_reentry(tmp_path):
    inputs=fixture(tmp_path);output=tmp_path/'consumer'
    answer=consumer.execute(output,inputs,CONFIG)
    assert answer['support']['dispositions']=={'outside-input-cohort':1,'not-intact-final-word':1,'awaiting-engine-score':1}
    assert answer['support']['original_rows']==3 and not answer['reader_executed']
    manifest=tmp_path/'RUN.json';save(manifest,dict(inputs=inputs,config=CONFIG))
    code=('import json,sys;from pathlib import Path;from runners.drive.cards.engine_d33_consumer import verify;'
          'd=json.load(open(sys.argv[1]));print(json.dumps(verify(Path(sys.argv[2]),d["inputs"],d["config"])))')
    actual=json.loads(subprocess.check_output([sys.executable,'-B','-c',code,str(manifest),str(output)],text=True))
    assert actual['verified'] and actual['summary']==answer
    hashes=read(output/'TIMING_BINDINGS.json')['outputs']
    assert consumer.execute(output,inputs,CONFIG)==answer
    assert hashes=={p:filehash(output/p) for p in hashes}


@pytest.mark.parametrize('kind',['incomplete','unverified','wrong-producer','changed-source','changed-output','changed-covariate'])
def test_corrupted_sources_or_outputs_refused(tmp_path,kind):
    inputs=fixture(tmp_path);output=tmp_path/'consumer';consumer.execute(output,inputs,CONFIG)
    complete=Path(inputs['source_completion']);root=complete.parent
    if kind in ('incomplete','unverified'):
        c=read(complete);c['status' if kind=='incomplete' else 'fresh_process_verified']='FAILED' if kind=='incomplete' else False;save(complete,c)
    elif kind=='wrong-producer':
        p=read(root/'PLAN.json');p['module']='unknown';save(root/'PLAN.json',p)
        c=read(complete);c['outputs']['PLAN.json']=filehash(root/'PLAN.json');save(complete,c)
    elif kind=='changed-source':
        p=tmp_path/'source/raw/s.jsonl';p.write_bytes(p.read_bytes().replace(b'cat',b'rat'))
    elif kind=='changed-output':
        save(output/'SUMMARY.json',dict(status='complete'))
    else:
        rows=read(inputs['rows_fixture']);rows[0]['log_pause']=99;save(inputs['rows_fixture'],rows)
    with pytest.raises(ValueError):consumer.verify(output,inputs,CONFIG)


def test_resealed_false_occurrence_is_refused_by_fresh_source(tmp_path):
    inputs=fixture(tmp_path);root=Path(inputs['source_completion']).parent
    # Replacing the completed producer with fabricated content cannot pass its
    # independently bound document and source reconstruction.
    index=read(root/'output/INDEX.json');unit=root/'output'/index[0]['file']
    from runners.drive.cards.timing_p6 import gzread
    value=gzread(unit);value['occurrences'][0]['character_ids']=[100,101,102];save(unit,value)
    index[0]['sha256']=filehash(unit);save(root/'output/INDEX.json',index)
    binding=read(root/'output/TIMING_BINDINGS.json')
    for p in binding['outputs']:binding['outputs'][p]=filehash(root/'output'/p)
    save(root/'output/TIMING_BINDINGS.json',binding)
    c=read(inputs['source_completion'])
    for p in c['outputs']:c['outputs'][p]=filehash(root/p)
    save(inputs['source_completion'],c)
    consumer.execute(tmp_path/'consumer',inputs,CONFIG)
    with pytest.raises(ValueError,match='fresh input reconstruction'):consumer.verify(tmp_path/'consumer',inputs,CONFIG)


def test_full_corpus_scope_is_not_silently_admitted():
    with pytest.raises(ValueError,match='bounded consumer'):consumer.validate({},dict(consumer.CONFIG,mode='main'))
    with pytest.raises(ValueError,match='exact original'):consumer.validate({},consumer.CONFIG)
