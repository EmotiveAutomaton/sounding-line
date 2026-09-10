import copy
import math
from pathlib import Path
import pytest

from runners.stage9 import selection_reader as reader,comparison_runtime
from runners.stage9.common import read
from runners.stage9.mark_program import neutral_program
from runners.stage9.program_inference import Budget
from runners.stage9.selection_cases import construct
from runners.stage9.series_cases import construct_attempt,COHORTS


def work(topic='current'):
    return {'context':{'topic':topic,'audience':'peer','tools':{'library':True,'source_access':True},
        'deadline':'loose','sections':[{'name':'s','slots':['a','b']}]},'marks':['write:s:a']}


def bundle(programs=None):
    programs=programs or {'a':neutral_program(),'b':neutral_program()}
    return {'view':'artifact','current':work(),'pool':{'o':work('prior')},'purchases':{},
        'candidates':programs,'prior':{c:1/len(programs) for c in programs},'shared_groups':{c:c for c in programs},
        'strategy':'future_prediction','allow_stop':True,'cost_nats':0.,'seed':991}


def test_next_observation_erases_stop_and_failed_actions_with_known_mass():
    p=neutral_program();p['available_types']=['write'];p['action_noise']=p['outcome_noise']=0.
    p['expertise']['success']['write']=.6;p['stop']={'intercept':math.log(1/3),'progress':0.,'deadline':0.,'self':0.}
    w=work();a=reader.observation_distribution(p,w,'artifact',Budget(100))
    record={**w,'events':[{'i':0,'type':'write','section':'s','slot':'a','outcome':'done'}],'observed_stop':None}
    r=reader.observation_distribution(p,record,'process_record',Budget(100))
    assert a['unchanged']==pytest.approx(.55,abs=1e-14) and a['mark|write:s:b']==pytest.approx(.45,abs=1e-14)
    assert a['unchanged']==pytest.approx(r['stop']+sum(v for k,v in r.items() if k.startswith('failed|')),abs=1e-14)
    assert sum(a.values())==pytest.approx(1.,abs=1e-14) and sum(r.values())==pytest.approx(1.,abs=1e-14)
    assert reader.purchased_symbol(record,{**record,'observed_stop':True},'process_record')=='stop'
    assert reader.purchased_symbol(w,w,'artifact')=='unchanged'
    with pytest.raises(ValueError,match='one next decision'):reader.purchased_symbol(record,record,'process_record')


def test_noisy_identical_makers_have_no_information_and_repetition_changes_nothing():
    b=bundle();out=reader.forecast(b,Budget(10000))
    assert out['calculations']['o']['observation_entropy_nats']>0
    assert out['calculations']['o']['expected_model_information_nats']==0
    assert out['calculations']['o']['expected_future_log_gain_nats']==0 and out['stop']
    repeated=copy.deepcopy(b);repeated['pool']['z']=copy.deepcopy(repeated['pool']['o'])
    same=reader.forecast(repeated,Budget(10000))
    assert same['persistent_weights']==out['persistent_weights'] and same['prediction']==out['prediction']
    assert same['unique_previews']==1 and same['duplicate_aliases']=={'z':'o'}
    repeated['purchases']['z']=copy.deepcopy(repeated['pool']['z'])
    with pytest.raises(ValueError,match='duplicate'):reader.forecast(repeated,Budget(10000))
    b['strategy']='entropy';assert not reader.forecast(b,Budget(10000))['stop']
    with pytest.raises(ValueError,match='undeclared'):reader.forecast({**b,'future_target':'stop'},Budget(10000))


def test_actual_fitted_update_matches_independent_likelihood_product_and_cost_stops():
    a=neutral_program();b=copy.deepcopy(a);b['purpose']['check']+=3.
    inp=bundle({'a':a,'b':b});before=reader.forecast(inp,Budget(10000))
    assert before['calculations']['o']['expected_future_log_gain_nats']>1e-8
    assert not before['stop']
    costly={**inp,'cost_nats':10.};assert reader.forecast(costly,Budget(10000))['stop']
    purchased={**work('prior'),'marks':['check:s:b','write:s:a']}
    inp['purchases']={'o':purchased};after=reader.forecast(inp,Budget(10000))
    unnormalized={}
    for name,p in inp['candidates'].items():
        current=math.exp(reader.first_action_likelihood(p,inp['current'],'artifact',Budget(100)))
        preview=math.exp(reader.first_action_likelihood(p,inp['pool']['o'],'artifact',Budget(100)))
        observed=reader.observation_distribution(p,inp['pool']['o'],'artifact',Budget(100))['mark|check:s:b']
        unnormalized[name]=.5*current*preview*observed
    total=sum(unnormalized.values())
    assert after['persistent_weights']==pytest.approx({k:v/total for k,v in unnormalized.items()},abs=1e-14)
    assert after['stop'] and after['purchased_observations']==1 and not after['calculations']


@pytest.fixture(scope='module')
def actual():
    case=construct_attempt(key='selection-source-fixture-v1',cohort=COHORTS[0],role='pilot',dose=7)
    assert case['realized'];return case


def test_actual_observation_pool_ignores_old_unseen_trajectories(actual):
    cf=construct(actual)
    assert len(cf['public']['artifact']['pool'])==len(cf['purchase_draws'])==7
    changed=copy.deepcopy(actual);changed['target']='old future'
    for w in changed['source_worlds']:w['trajectory']={'steps':[],'changes':[{'future':'changed'}]}
    assert construct(changed)==cf
    for view in ('artifact','process_record'):
        assert all(reader.purchased_symbol(cf['public'][view]['pool'][k],w,view)==cf['symbols'][view][k]
                   for k,w in cf['purchases'][view].items())


def test_restricted_reader_selects_before_only_that_purchase_is_revealed(actual,tmp_path):
    cf=construct(actual);p=neutral_program()
    inp={**cf['public']['artifact'],'purchases':{},'candidates':{'a':p},'prior':{'a':1.},'shared_groups':{'a':'a'},
         'strategy':'random','allow_stop':False,'cost_nats':.05,'seed':991}
    result=comparison_runtime.execute(inp,operation='select_observation',budget=800000,root=tmp_path/'before')
    assert result['accepted'] and not result['prediction']['stop']
    selected=result['prediction']['selected'];assert read(Path(result['capsule'])/'evidence.json')['purchases']=={}
    inp['purchases']={selected:cf['purchases']['artifact'][selected]}
    after=comparison_runtime.execute(inp,operation='select_observation',budget=800000,root=tmp_path/'after')
    assert after['accepted'] and after['prediction']['purchased_observations']==1
    assert after['prediction']['selected_content_id']!=result['prediction']['selected_content_id']
    actual_input=read(Path(after['capsule'])/'evidence.json')
    assert set(actual_input['purchases'])=={selected} and 'target' not in actual_input and 'oracle' not in actual_input
