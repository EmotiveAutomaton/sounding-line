import copy
import math
from pathlib import Path
import pytest

from runners.stage9.familiarity_entry_cases import construct
from runners.stage9.familiarity_cases import construct as familiarity
from runners.stage9.series_cases import construct_attempt,COHORTS
from runners.stage9.selection_reader import purchased_symbol
from runners.stage9 import selection_reader as reader,comparison_runtime
from runners.stage9.mark_program import neutral_program
from runners.stage9.program_inference import Budget
from runners.stage9.common import read


def fixture_bundle():
    def w(topic):
        return {'context':{'topic':topic,'audience':'peer','tools':{'library':True,'source_access':True},
            'deadline':'loose','sections':[{'name':'s','slots':['a','b']}]},'marks':['write:s:a']}
    return {'view':'artifact','current':w('current'),'pool':{'o':w('prior')},'purchases':{},
        'candidates':{'a':neutral_program(),'b':neutral_program()},'prior':{'a':.5,'b':.5},
        'shared_groups':{'a':'A','b':'B'},'strategy':'future_prediction','allow_stop':True,'cost_nats':0.,'seed':1}


@pytest.fixture(scope='module')
def case():
    c=construct_attempt(key='familiarity-source-fixture-v1',cohort=COHORTS[0],role='pilot',dose=7)
    assert c['realized']
    return c


def test_entry_cross_preserves_existing_choice_and_future_and_all_public_matches(case):
    result=construct(case);previous=familiarity(case)
    assert result['prefixes']==previous['prefixes'] and result['outcomes']==previous['outcomes']
    assert result['other_maker_plan']==previous['other_maker_plan']
    assert result['other_maker_plan']['original']!=result['other_maker_plan']['alternative']
    for stratum in ('expected','unexpected'):
        a,b=(result['conditions'][f+'|'+stratum] for f in ('familiar','unfamiliar'))
        assert a['target']==b['target'] and a['recognition_target']!=b['recognition_target']
        for view in ('artifact','process_record'):
            assert a['public'][view]['current']==b['public'][view]['current']
            assert set(a['public'][view])=={'view','current','pool'}
            assert len(a['public'][view]['pool'])==len(b['public'][view]['pool'])==3
            assert [w['context'] for w in a['public'][view]['pool'].values()]==[w['context'] for w in b['public'][view]['pool'].values()]
            for cf in (a,b):
                for n,p in cf['purchases'][view].items():
                    assert purchased_symbol(cf['public'][view]['pool'][n],p,view)==cf['symbols'][view][n]
    for familiarity_name in ('familiar','unfamiliar'):
        a,b=(result['conditions'][familiarity_name+'|'+s] for s in ('expected','unexpected'))
        assert a['purchases']==b['purchases']
        for view in ('artifact','process_record'):assert a['public'][view]['pool']==b['public'][view]['pool']


def test_entry_construction_ignores_old_future_and_refuses_repeated_source(case):
    result=construct(case);changed=copy.deepcopy(case);changed['target']='unused old future'
    for w in changed['source_worlds']:w['trajectory']={'steps':[],'changes':[{'unknown':'unused'}]}
    assert construct(changed)==result
    repeated=copy.deepcopy(case);repeated['source_worlds'][2]=copy.deepcopy(repeated['source_worlds'][1])
    with pytest.raises(ValueError,match='duplicate|repeats'):construct(repeated)


def test_identical_makers_leave_link_prior_and_duplicate_evidence_unchanged():
    b=fixture_bundle();out=reader.familiarity_forecast(b,Budget(100000))
    assert out['recognition']==pytest.approx({'same':.5,'different':.5},abs=1e-14)
    assert out['calculations']['o']['expected_future_log_gain_nats']==0
    assert out['calculations']['o']['expected_model_information_nats']==0 and out['stop']
    b['pool']['z']=copy.deepcopy(b['pool']['o']);repeated=reader.familiarity_forecast(b,Budget(100000))
    assert repeated['prediction']==out['prediction'] and repeated['recognition']==out['recognition']
    assert repeated['persistent_weights']==out['persistent_weights']
    with pytest.raises(ValueError,match='undeclared'):
        reader.familiarity_forecast({**b,'recognition_target':'same'},Budget(100000))


def test_link_and_future_information_match_independent_small_joint(monkeypatch):
    b=fixture_bundle();b['candidates']['b']['purpose']['write']=99.
    def first(p,w,view,budget):
        a=p['purpose']['write']!=99.
        return math.log((.9 if a else .1) if w['context']['topic']=='current' else (.8 if a else .2))
    monkeypatch.setattr(reader,'first_action_likelihood',first)
    monkeypatch.setattr(reader,'policy',lambda p,w:{'yes':.9 if p['purpose']['write']!=99. else .1,
                                                 'no':.1 if p['purpose']['write']!=99. else .9})
    monkeypatch.setattr(reader,'observation_distribution',lambda p,w,v,budget:
        {'unchanged':.7 if p['purpose']['write']!=99. else .3,'mark|write:s:b':.3 if p['purpose']['write']!=99. else .7})
    out=reader.familiarity_forecast(b,Budget(100000))
    assert out['recognition']['same']==pytest.approx(.185/.31,abs=1e-14)
    assert out['prediction']['yes']==pytest.approx(.265/.31,abs=1e-14)
    # Enumerate a tiny joint table directly in probability space. The four rows
    # collapse shared/independent branch masses by (current type, archive type).
    joint=[[0.,0.],[0.,0.]]
    for mass,py,po in ((.27,.9,.7),(.0225,.9,.3),(.01,.1,.7),(.0075,.1,.3)):
        for y in (0,1):
            for o in (0,1):joint[y][o]+=mass/.31*(py if y else 1-py)*(po if o else 1-po)
    ym=[sum(row) for row in joint];om=[sum(joint[y][o] for y in (0,1)) for o in (0,1)]
    expected=sum(joint[y][o]*math.log(joint[y][o]/(ym[y]*om[o])) for y in (0,1) for o in (0,1))
    assert out['calculations']['o']['expected_future_log_gain_nats']==pytest.approx(expected,abs=1e-14)
    independent=reader.forecast(b,Budget(100000),same_prior=0.)
    assert independent['prediction']['yes']==pytest.approx(.82,abs=1e-14)
    assert independent['calculations']['o']['expected_future_log_gain_nats']==0 and independent['stop']
    b['purchases']={'o':copy.deepcopy(b['pool']['o'])}
    after=reader.familiarity_forecast(b,Budget(100000))
    assert after['recognition']['same']==pytest.approx(.1275/.205,abs=1e-14)
    assert reader.forecast(b,Budget(100000),same_prior=0.)['prediction']['yes']==pytest.approx(.82,abs=1e-14)
    assert reader.forecast(b,Budget(100000),same_prior=1.)['prediction']==pytest.approx(reader.forecast(b,Budget(100000))['prediction'],abs=1e-14)


def test_restricted_familiar_entry_selects_before_reveal_and_refuses_truth(case,tmp_path):
    cf=construct(case)['conditions']['unfamiliar|unexpected'];p=neutral_program()
    b={**cf['public']['artifact'],'purchases':{},'candidates':{'a':p},'prior':{'a':1.},'shared_groups':{'a':'A'},
       'strategy':'random','allow_stop':False,'cost_nats':.05,'seed':1}
    before=comparison_runtime.execute(b,operation='select_familiar_observation',budget=800000,root=tmp_path/'before')
    assert before['accepted'] and before['prediction']['recognition']==pytest.approx({'same':.5,'different':.5},abs=1e-14)
    chosen=before['prediction']['selected']
    assert read(Path(before['capsule'])/'evidence.json')['purchases']=={}
    b['purchases']={chosen:cf['purchases']['artifact'][chosen]}
    after=comparison_runtime.execute(b,operation='select_familiar_observation',budget=800000,root=tmp_path/'after')
    assert after['accepted'] and after['prediction']['purchased_observations']==1
    assert set(read(Path(after['capsule'])/'evidence.json')['purchases'])=={chosen}
    denied=comparison_runtime.execute({**b,'recognition_target':'different'},operation='select_familiar_observation',budget=800000,root=tmp_path/'denied')
    assert not denied['accepted']
