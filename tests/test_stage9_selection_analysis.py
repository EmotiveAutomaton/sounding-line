import copy
import math
import pytest
from runners.stage9.selection_analysis import describe,transitions
from runners.stage9.selection_jobs import STRATEGIES,STOP_COSTS


def fixture():
    row={'unit':'u','truth':'a','traces':{},'rows':{}}
    for view in ('artifact','process_record'):
        for strategy in STRATEGIES:
            before={'prediction':{'a':.5,'b':.5},'model_entropy_nats':1.,'selected':'offer','stop':False,
                'purchased_observations':0,'calculations':{'offer':{'expected_model_information_nats':.1,'expected_future_log_gain_nats':.2}}}
            after={'prediction':{'a':.25,'b':.75},'model_entropy_nats':1.2,'selected':None,'stop':True,
                'purchased_observations':1,'calculations':{}}
            row['traces'][view+'|'+strategy]={'valid':True,'allow_stop':False,'strategy':strategy,'cost_nats':0.,
                'steps':[{'step':0,'accepted':True,'purchased':[],'output':before},
                         {'step':1,'accepted':True,'purchased':['offer'],'output':after}]}
        row['rows'][view+'|future_prediction|7']={'validity':{'program':True},'predictions':{'program':{'a':.25,'b':.75}},
            'preview_cost':7,'purchase_cost':1,'full_view':True}
        for cost in STOP_COSTS:
            row['rows'][view+'|future-stop-'+str(cost)+'|stopped']={'validity':{'program':True},
                'predictions':{'program':{'a':.5,'b':.5}},'preview_cost':7,'purchase_cost':0}
    return row


def test_realized_gain_and_uncertainty_can_get_worse_with_positive_prediction():
    row=fixture();values=transitions(row,'artifact','random')
    assert values[0]['realized_future_gain']==pytest.approx(-math.log(2))
    assert values[0]['realized_model_entropy_reduction']==pytest.approx(-.2)
    result=describe([row],['u'],draws=100)
    assert len(result)==20 and all(v['disposition']=='DESCRIPTIVE' for v in result.values())
    assert result['artifact|random']['purchased_transitions']==1
    assert result['artifact|stopping-utility-0.05']['saved_purchases']==[{'unit':'u','saved_purchases':1}]


def test_missing_purchase_or_unit_refuses_and_invalid_is_not_dropped():
    row=fixture();bad=copy.deepcopy(row)
    bad['traces']['artifact|random']['steps'][1]['purchased']=['unselected']
    with pytest.raises(ValueError,match='saved pre-purchase'):transitions(bad,'artifact','random')
    with pytest.raises(ValueError,match='allocation'):describe([row],['u','omitted'],draws=100)
    row['traces']['artifact|random']['valid']=False
    r=describe([row],['u'],draws=100)['artifact|random']
    assert r['disposition']=='IMPLEMENTATION INVALID' and r['assigned_units']==1 and r['scored_units']==0


def test_zero_forecast_keeps_its_infinite_loss():
    row=fixture()
    row['traces']['artifact|random']['steps'][1]['output']['prediction']={'a':0.,'b':1.}
    assert transitions(row,'artifact','random')[0]['realized_future_gain']==-math.inf
    r=describe([row],['u'],draws=100)['artifact|random']
    assert r['scored_units']==1 and r['excluded_units']==0
    assert r['metrics']['realized_future_gain']['finite_estimate'] is False
