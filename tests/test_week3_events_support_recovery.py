"""Both recorded source failures must replay without losing FR1/TR5 events."""
import copy
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.cards import week3_frames_input_support_recovery as fr
from runners.drive.cards import week3_frames_inputs as original_fr
from runners.drive.cards import week3_trust_input_support_recovery as tr
from runners.drive.cards import week3_trust_input_recovery as first_tr
from runners.drive.cards import week3_trust_inputs as original_tr
from runners.drive.cards import week3_outcome_blocks_inputs as original_source
from runners.drive.cards import week3_outcome_blocks_recovery as first_source
from runners.drive.cards.timing_census import read,write
from runners.drive.cards.timing_p6 import gzread
from runners.drive.cards.timing_text import replay_words
from tests.test_week3_trust_inputs import session

FIELDS={'option_count','comparator_supported','comparator_support'}
PRIVATE=Path('.agent-state/drive-20261025')


def singleton_fixture():
    f=session(later_delete=True)
    # The original failure event and its preceding kept acceptances all remain.
    for c in f['canonical']['events']:
        c['options']=[o for o in c['options'] if o['index'] in c['matched_option_indices']]
    f['p6']=replay_words(f['events'])
    return f


def private(name):
    path=PRIVATE/name
    if not path.is_file():pytest.skip('private actual-source fixture not installed')
    return read(path)


def handler_fixture():
    # WC2's invented sessions omit P2 decision rows because its own handler
    # does not consume them. FR1/TR5 fixtures use complete decision timelines.
    rows=[session('constructed'+str(i),'writer'+str(i//2),failed=i%2==0) for i in range(4)]
    for row in rows:row['p6']=replay_words(row['events'])
    for c in rows[0]['canonical']['events']:
        c['options']=[o for o in c['options'] if o['index'] in c['matched_option_indices']]
    return rows+[private(name) for name in (
        'WC2_ACTUAL_FAILURE_FIXTURE.json','WC2_MISSING_COMPARATOR_FIXTURE.json')]


def test_singletons_preserve_fr1_deleted_events_and_tr5_failure_history():
    base=session(later_delete=True);base['p6']=replay_words(base['events'])
    f=singleton_fixture()
    with pytest.raises(ValueError,match='no unchosen comparator'):
        first_source.spans(f['events'],f['timeline'],f['canonical'])
    with fr.canonical_append():actual_fr=original_fr.prepare_session(**f)
    assert actual_fr==original_fr.prepare_session(**base)
    assert any(e['kind']=='deleted' for e in actual_fr['events'])
    with tr.canonical_survival():actual=original_tr.prepare_session(**f)
    expected=original_tr.prepare_session(**base)
    assert len(actual['spans'])==len(expected['spans'])==18
    assert actual['failures']==expected['failures']
    assert len(actual['menu'])==len(expected['menu'])==18
    for a,b in zip(actual['spans'],expected['spans']):
        normalized={k:v for k,v in a.items() if k not in FIELDS}
        b=copy.deepcopy(b);b['unchosen']=[]
        assert normalized==b
        assert a['canonical'] and a['option_count']==1 and not a['comparator_supported']
    failed=next(s for s in actual['spans'] if s['failure_removed']==8)
    first=actual['spans'][0]
    assert original_tr.kept(first,failed['failure_ordinal'])
    assert not original_tr.kept(first,len(f['events'])-1)


@pytest.mark.parametrize('name',[
    'WC2_ACTUAL_FAILURE_FIXTURE.json','WC2_MISSING_COMPARATOR_FIXTURE.json'])
def test_both_actual_failures_retain_complete_sessions(name):
    f=private(name)
    if name.startswith('WC2_ACTUAL'):
        with pytest.raises(ValueError,match='actual inserted'):
            original_fr.prepare_session(**f)
    else:
        opening=f['events'][766]
        assert len(opening['currentSuggestions'])==1 and str(opening['currentN'])=='5'
        with pytest.raises(ValueError,match='no unchosen comparator'):
            first_source.spans(f['events'],f['timeline'],f['canonical'])
    with fr.canonical_append():a=original_fr.prepare_session(**f)
    with tr.canonical_survival():b=original_tr.prepare_session(**f)
    assert a['session']==b['session']==f['meta']['session']
    assert len(b['spans'])==sum(e['eventName']=='suggestion-select' for e in f['events'])
    assert len(b['menu'])==sum(c['usable'] for c in f['canonical']['events'])
    assert [s['origin'] for s in b['spans']]==[s['origin'] for s in tr.repaired.spans(f['events'],f['timeline'],f['canonical'])]
    for span in b['spans']:
        assert span['retention'][-1][1]==span['retained_codepoints']
        if span['failure_ordinal'] is not None:
            assert 5*span['failure_removed']>=4*span['original_codepoints']
    if name.startswith('WC2_MISSING'):
        row=next(s for s in b['spans'] if s['origin']==766)
        assert row['canonical'] and row['option_count']==1 and row['unchosen']==[]
        assert row['comparator_support']=='single_option_menu'


def test_original_first_failure_proof_unchanged_except_support_metadata():
    f=private('WC2_ACTUAL_FAILURE_FIXTURE.json')
    expected=first_tr.history(f['events'],f['timeline'],f['canonical'])
    actual=tr.history(f['events'],f['timeline'],f['canonical'])
    assert {k:{a:b for a,b in v.items() if a not in FIELDS} for k,v in actual.items()}==expected


@pytest.mark.parametrize('module,card',[
    ('week3_frames_input_support_recovery',fr),('week3_trust_input_support_recovery',tr)])
def test_six_session_actual_fixture_fresh_handler_replay(tmp_path,module,card):
    rows=handler_fixture()
    assert len(rows)==6
    actual_ids={private(name)['meta']['session'] for name in (
        'WC2_ACTUAL_FAILURE_FIXTURE.json','WC2_MISSING_COMPARATOR_FIXTURE.json')}
    assert actual_ids<={r['meta']['session'] for r in rows}
    path=tmp_path/'fixture.json';write(path,rows)
    inputs={'fixture':str(path)}
    config=dict(card.CONFIG,mode='constructed',expected_sessions=6,session_limit=6)
    out=tmp_path/'out';result=card.execute(out,inputs,config)
    assert card.execute(out,inputs,config)==result
    stored=gzread(out/'EVENTS.json.gz')
    assert {s['session'] for s in stored['sessions']}=={r['meta']['session'] for r in rows}
    assert result['summary']['sessions']==6 and not result['summary']['scientific_admission']
    manifest=tmp_path/'manifest.json';write(manifest,dict(output=str(out),inputs=inputs,config=config))
    code="import json,sys;from runners.drive.cards."+module+" import verify;x=json.load(open(sys.argv[1]));assert verify(x['output'],x['inputs'],x['config'])['verified']"
    subprocess.run([sys.executable,'-X','utf8','-B','-c',code,str(manifest)],check=True,timeout=60)
    path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError,match='replay differs'):card.verify(out,inputs,config)


@pytest.mark.parametrize('card',[fr,tr])
def test_error_restores_scoped_dependencies_and_ambiguity_still_fails(tmp_path,card):
    f=singleton_fixture();c=f['canonical']['events'][0]
    c['options'].append(dict(index=0,original=c['options'][0]['original']))
    c['matched_option_indices']=[1,0]
    path=tmp_path/'fixture.json';write(path,[f])
    before=(original_source.spans,original_tr.history,first_tr.repaired)
    config=dict(card.CONFIG,mode='constructed',expected_sessions=1,session_limit=1)
    with pytest.raises(ValueError,match='unique canonical choice'):
        card.execute(tmp_path/'out',{'fixture':str(path)},config)
    assert (original_source.spans,original_tr.history,first_tr.repaired)==before
