import copy,math
import pytest
from runners.stage9 import choice_analysis as analysis


def battery(monkeypatch,kind='signal',repeated=False):
    cases=[];predictions={};baselines=[]
    monkeypatch.setattr(analysis,'choice_input',lambda c,op:{'prefix':('same' if repeated else c['unit']),
                                                          'options':{'a':' a','b':' b'}})
    for i in range(192):
        key='case'+str(i);truth='a' if (i//2)%2==0 else 'b'
        cases.append({'unit':key,'role':'discovery','target':truth,
            'private_factors':{'domain':('essay','workshop_doc')[i%2],'law':'fixed','purpose':'fixed'}})
        p=.8 if kind=='constant' or (kind=='signal' and truth=='a') else .2 if kind=='signal' else .5
        predictions[key]={'accepted':True,'prediction':{'probs':{'a':p,'b':1-p}}}
        baselines.append({'unit':key,'truth':truth,'rows':{'process_record|dose0':
            {'support':['a','b'],'validity':{'prior':True},'predictions':{'prior':{'a':.5,'b':.5}}}}})
    selected={'process_record|dose0':{'accepted':True,'selection':{'selected':'prior','units':['separate-development']}}}
    return cases,predictions,baselines,selected


def test_planted_signal_zero_and_constant_reader_have_known_distinct_answers(monkeypatch):
    for kind,expected in [('signal',math.log(1.6)),('zero',0.),('constant',math.log(.64)/2)]:
        cases,preds,baseline,selection=battery(monkeypatch,kind)
        result,rows=analysis.summarize(cases,'genuine_choice',preds,baseline,selection,scope='scientific',draws=100)
        for group in result['groups']['domain'].values():
            assert group['contrast']['mean']==pytest.approx(expected)
            assert group['component_criterion_pass']==(kind=='signal')
        assert len(rows)==192 and result['scientific_admission'] is False


def test_repeated_questions_cannot_inflate_the_independent_count(monkeypatch):
    cases,preds,baseline,selection=battery(monkeypatch,repeated=True)
    result,rows=analysis.summarize(cases,'genuine_choice',preds,baseline,selection,scope='scientific',draws=100)
    assert result['distinct_public_questions']==1
    for group in result['groups']['domain'].values():
        assert group['contrast']['n_units']==1 and group['contrast']['ci'] is None
        assert not group['component_criterion_pass']


def test_incomplete_invalid_support_and_development_reuse_fail_closed(monkeypatch):
    cases,preds,baseline,selection=battery(monkeypatch)
    with pytest.raises(ValueError,match='complete offered'):
        analysis.summarize(cases[:-1],'genuine_choice',preds,baseline,selection,scope='scientific')
    preds['case0']['accepted']=False
    result,rows=analysis.summarize(cases,'genuine_choice',preds,baseline,selection,scope='scientific',draws=100)
    assert len(rows)==192 and result['groups']['domain']['essay']['invalid']==1
    assert result['groups']['domain']['essay']['contrast'] is None
    preds['case0']={'accepted':True,'prediction':{'probs':{'a':1.}}}
    with pytest.raises(ValueError,match='omitted support'):
        analysis.summarize(cases,'genuine_choice',preds,baseline,selection,scope='scientific')
    selection['process_record|dose0']['selection']['units'].append('case0')
    with pytest.raises(ValueError,match='development unit'):
        analysis.summarize(cases,'genuine_choice',preds,baseline,selection,scope='scientific')


def test_real_zero_probability_remains_an_infinite_loss(monkeypatch):
    cases,preds,baseline,selection=battery(monkeypatch)
    preds['case0']['prediction']['probs']={'a':0.,'b':1.}
    result,rows=analysis.summarize(cases,'genuine_choice',preds,baseline,selection,scope='scientific',draws=100)
    assert rows[0]['reader_log_score']==-math.inf
    assert result['groups']['domain']['essay']['contrast']['finite_estimate'] is False
    assert not result['groups']['domain']['essay']['component_criterion_pass']
