"""Known-answer gates for the retrospective adapter and literal consumer."""
import copy
import json
from pathlib import Path
import pytest
from runners.stage11 import core, run, report
from runners.stage11.replay import replay
from runners.stage9.coauthor import units


def event(name, **kw): return dict(eventName=name,**kw)
def menu(text='XYZ'): return [dict(index=0,original=text,trimmed=text)]
def base(doc='ab\n',text='XYZ'):
    return [event('system-initialize',currentDoc=doc),event('suggestion-open',currentSuggestions=menu(text)),
            event('suggestion-select',currentSuggestionIndex=0),
            event('text-insert',eventSource='api',textDelta={'ops':[{'retain':len(units(doc))-1},{'insert':text}]})]


def test_unicode_shift_overlap_and_exact_surviving_span():
    rows=base('a😀b\n')+[event('text-insert',eventSource='user',textDelta={'ops':[{'insert':'long'}]}),
        event('text-delete',eventSource='user',textDelta={'ops':[{'retain':7},{'delete':3}]})]
    r=replay(rows)['events'][0]
    assert r['end_document']=='longa😀Z\n' and r['decision']=='edit'
    s=r['terminal_spans'][0]
    assert s['text']=='Z' and r['end_document'][s['start']:s['end']]=='Z'


def test_cutoff_precedes_next_menu_and_its_delta_final_closure():
    rows=base()+[event('suggestion-open',currentSuggestions=menu('late'),textDelta={'ops':[{'insert':'AFTER'}]}),
                 event('text-insert',eventSource='user',textDelta={'ops':[{'insert':'LAST'}]})]
    r=replay(rows)
    assert r['events'][0]['end_document']=='abXYZ\n' and r['events'][0]['cutoff_ordinal']==4
    assert r['events'][1]['end_document']=='LASTAFTERabXYZ\n' and r['events'][1]['cutoff_ordinal']==6


def test_reopen_duplicate_offers_complete_deletion():
    rows=base();rows[1]['currentSuggestions']+= [dict(index=1,original='XYZ',trimmed='XYZ')]
    rows[2:2]=[event('suggestion-close'),event('suggestion-reopen',currentSuggestions=copy.deepcopy(rows[1]['currentSuggestions']))]
    rows.append(event('text-delete',eventSource='user',textDelta={'ops':[{'retain':2},{'delete':3}]}))
    r=replay(rows)['events'][0]
    assert r['decision']=='edit' and r['terminal_spans']==[] and r['reopens']==1
    assert r['matched_option_indices']==[0,1] and r['review']==r['endorsement']=='unknown'


@pytest.mark.parametrize('delta',[{'ops':[{'retain':99}]},{'ops':[{'delete':-1}]},'bad',{'ops':[{'retain':1},{'delete':1}]}])
def test_malformed_or_surrogate_split_excluded(delta):
    r=replay(base('a😀b\n')+[event('text-delete',eventSource='user',textDelta=delta)])
    assert not r['reconstructed'] and not r['events'][0]['usable']


def test_same_artifact_distinct_histories_and_exact_method_evidence():
    rows=run.synthetic_rows()
    assert rows[0]['truth']!=rows[1]['truth']
    assert core.canonical(rows[0]['views']['artifact'])==core.canonical(rows[1]['views']['artifact'])
    for r in rows:
        for v in core.VIEWS:
            bodies=[json.loads(core.request_for(r['views'][v],a)['messages'][1]['content']) for a in core.ARMS]
            assert core.canonical(bodies[0]['evidence'])==core.canonical(bodies[1]['evidence'])
        assert set(r['views']['artifact'])=={'episode_end_document','menu_was_available'}
        assert set(r['views']['alternatives'])-set(r['views']['artifact'])=={'pre_menu_document','displayed_suggestions','differences'}


def test_unsupported_goal_sharing_review_unresolved():
    r=run.synthetic_rows()[0]
    for op in ('forward','review','endorse','wanted to persuade'):
        p=dict(actor='human',operation=op,quote='A small',alternative='unknown',depends_on='none',missing_evidence='record')
        result=report.audit_event(p,r)
        assert result['record_relation']=='unresolved'


def test_probability_rule_and_loss_direction():
    def raw(p):return dict(done=True,done_reason='stop',message=dict(content=json.dumps(dict(probabilities=p,explanation='x'))))
    p=core.parse(raw([.333,.333,.334,0]),'direct')
    assert sum(p['probabilities'])==1
    for bad in ([1,0,0],[1,-.1,.1,0],[.4]*4,[float('nan'),0,0,1],[True,0,0,0]):
        with pytest.raises(ValueError):core.parse(raw(bad),'direct')
    assert core.scores([1,0,0,0],'accept')['brier']==0
    assert core.scores([1,0,0,0],'edit')['log_loss']=='infinite'
    assert core.scores(None,'accept')['brier']==1 and core.scores(None,'accept')['accuracy']==0


def test_rounding_trace_and_truncation():
    raw=dict(done=True,done_reason='stop',message=dict(content=json.dumps(dict(probabilities=[.25,.25,.25,.251],explanation='x'))))
    assert core.parse(raw,'direct')['original_probability_sum']==1.001
    raw['done_reason']='length'
    with pytest.raises(ValueError):core.parse(raw,'direct')


def test_literal_rehearsal_resume_semantic_reparse_and_tamper(tmp_path,monkeypatch):
    run.rehearse(tmp_path)
    def forbidden(*a,**k):raise AssertionError('resume made an extra request')
    monkeypatch.setattr(run,'api',forbidden)
    run.rehearse(tmp_path)
    original=report.analyze(tmp_path,False)
    assert len(original['cells'])==8
    path=next((tmp_path/'calls').rglob('RAW.json'));raw=core.read(path)
    body=json.loads(raw['message']['content']);body['probabilities']=[1,0,0,0];raw['message']['content']=json.dumps(body)
    path.write_text(json.dumps(raw),encoding='utf-8')
    with pytest.raises(ValueError):report.analyze(tmp_path,False)


def test_balancing_components_and_training_only_control():
    from runners.stage11.prepare import balanced
    rows=[dict(key=str(i),writer='w'+str(i%4)) for i in range(40)]
    chosen=balanced(rows,24,3)
    assert len(chosen)==12 and all(sum(r['writer']==w for r in chosen)==3 for w in {r['writer'] for r in rows})
    x=[dict(writer='a',prompt='1',session='x'),dict(writer='b',prompt='1',session='y'),dict(writer='b',prompt='2',session='z')]
    assert report.components(x)==1
    r=run.synthetic_rows()[0];train=[]
    for i,a in enumerate(core.ACTIONS):train.append(dict(**{k:v for k,v in r.items() if k not in ('writer','truth')},writer=str(i),truth=a))
    fitted=core.fit(train)
    for v in core.VIEWS:
        assert core.predict(r['views'][v],v,fitted,'prior')==[.25]*4
        assert core.predict(r['views'][v],v,fitted,'features')==[.25]*4


def test_incomplete_attempt_never_retried(tmp_path,monkeypatch):
    target=tmp_path/'attempt';target.mkdir()
    monkeypatch.setattr(run,'api',lambda *a,**k:pytest.fail('new call'))
    with pytest.raises(ValueError): run.call(target,run.synthetic_rows()[0]['views']['artifact'],'direct')
