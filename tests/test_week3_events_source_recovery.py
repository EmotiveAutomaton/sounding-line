import copy
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import week3_frames_input_recovery as fr
from runners.drive.cards import week3_frames_inputs as old_fr
from runners.drive.cards import week3_trust_input_recovery as tr
from runners.drive.cards import week3_trust_inputs as old_tr
from runners.drive.cards import week3_outcome_blocks_inputs as old_wc
from runners.drive.cards.timing_census import read,write
from runners.stage9.coauthor import units
from tests.test_week3_trust_inputs import session


def transformed(kind):
    f=session();doc=''
    for event in f['events']:
        if event['eventName']=='text-insert' and event['eventSource']=='system':
            span='abcdefghij'
            if kind=='replace':event['textDelta']={'ops':[{'delete':len(units(doc+'\n'))},{'insert':doc+span+'\n'}]}
            elif kind=='shift':event['textDelta']={'ops':[{'retain':len(units(doc+'\n'))},{'insert':span[1:]+'\n'},{'delete':0}]}
            doc+=span
            # Replacements are tested only before the fixture's first deletion.
            if len(doc)==30:break
    return f


def test_full_document_replacement_retains_prior_accepted_atoms():
    f=transformed('replace')
    with pytest.raises(ValueError,match='actual inserted|canonical append'):
        old_tr.history(f['events'],f['timeline'],f['canonical'])
    repaired=tr.history(f['events'],f['timeline'],f['canonical'])
    base=session();expected=old_tr.history(base['events'],base['timeline'],base['canonical'])
    assert repaired==expected


def test_actual_failure_session_replays_with_all_events_and_same_threshold():
    path=Path('.agent-state/drive-20261025/WC2_ACTUAL_FAILURE_FIXTURE.json')
    if not path.is_file():pytest.skip('private actual-source regression fixture not installed')
    f=read(path)
    with pytest.raises(ValueError,match='actual inserted'):
        old_fr.prepare_session(**f)
    with fr.canonical_append():assert old_fr.prepare_session(**f)['session']==f['meta']['session']
    with tr.canonical_survival():
        value=old_tr.prepare_session(**f)
    assert value['session']==f['meta']['session']
    for span in value['spans']:
        if span['failure_ordinal'] is not None:
            assert 5*span['failure_removed']>=4*span['original_codepoints']


@pytest.mark.parametrize('module,original',[('week3_frames_input_recovery',fr),('week3_trust_input_recovery',tr)])
def test_complete_wrapper_fresh_native_replay_and_restore(tmp_path,module,original):
    # Full-document replacement fixture is a constructed encoding of the same
    # canonical choices, with exactly the original final text.
    value=transformed('replace')
    if module.startswith('week3_frames'):
        from runners.drive.cards.timing_text import replay_words
        value['p6']=replay_words(value['events'])
    path=tmp_path/'fixture.json';write(path,[value]);inputs={'fixture':str(path)}
    config=dict(original.CONFIG,mode='constructed',expected_sessions=1,session_limit=1);out=tmp_path/'out'
    original.execute(out,inputs,config)
    manifest=tmp_path/'manifest.json';write(manifest,dict(output=str(out),inputs=inputs,config=config))
    code="import json,sys;from runners.drive.cards."+module+" import verify;x=json.load(open(sys.argv[1]));assert verify(x['output'],x['inputs'],x['config'])['verified']"
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(manifest)],check=True,timeout=60)
    previous_wc=old_wc.spans;previous_history=old_tr.history
    with pytest.raises(ValueError):original.execute(tmp_path/'bad',{},config)
    assert old_wc.spans is previous_wc and old_tr.history is previous_history
