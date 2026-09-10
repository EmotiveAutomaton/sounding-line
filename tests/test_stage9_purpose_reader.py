import copy
import pytest

from runners.stage9.program_inference import Budget
from runners.stage9.purpose_reader import forecast
from runners.stage9.comparison_runtime import execute
from runners.stage9.artifact_view import support
from tests.test_stage9_erased_inference import A, B, program, recorded


def bundle(equal=False):
    current=recorded([])
    query={'version':'s9-visible-artifact-v1','view':'process_record','current':current,
           'earlier':[recorded([A]),recorded([B])],'support':support(current,'process_record')}
    return {'evidence':query,'candidates':{'a':program(.5 if equal else .9),'b':program(.5 if equal else .1)},
            'prior':{'a':.5,'b':.5},'shared_groups':{'a':'maker','b':'maker'},
            'purpose_groups':{'a':'first','b':'second'},'mode':'ordinary'}


def test_absent_purpose_signal_is_zero_and_duplicate_history_is_not_new_evidence():
    data=bundle(True);result=forecast(data,Budget(10000))
    rows=result['predictions'];expected=rows['inferred_distribution']['prediction']
    assert all(r['prediction']==pytest.approx(expected) for r in rows.values())
    repeated=copy.deepcopy(data);repeated['evidence']['earlier']*=3
    again=forecast(repeated,Budget(10000))
    assert again['predictions']['inferred_distribution']['weights']==rows['inferred_distribution']['weights']
    for purpose in ('first','second'):
        supplied={**data,'mode':'supplied','supplied_purpose':{p:float(p==purpose) for p in ('first','second')}}
        assert forecast(supplied,Budget(10000))['predictions']['supplied']['prediction']==pytest.approx(expected)


def test_true_and_false_purpose_change_future_but_do_not_relabel_earlier_works():
    data=bundle();ordinary=forecast(data,Budget(10000))
    assert ordinary['purpose_posterior']==pytest.approx({'first':.5,'second':.5})
    assert len(ordinary['predictions']['single_purpose']['selected_purposes'])==2
    a=forecast({**data,'mode':'supplied','supplied_purpose':{'first':1.,'second':0.}},Budget(10000))['predictions']['supplied']
    b=forecast({**data,'mode':'supplied','supplied_purpose':{'first':0.,'second':1.}},Budget(10000))['predictions']['supplied']
    assert a['prediction'][A]==pytest.approx(.675)
    assert b['prediction'][A]==pytest.approx(.075)
    assert a['likelihood_receipts']==b['likelihood_receipts']
    assert a['distinct_earlier_works']==b['distinct_earlier_works']==2


def test_missing_support_hidden_truth_wrong_view_and_bad_distribution_refuse():
    for mutate in (lambda d:d.update(hidden_truth='first'),lambda d:d['purpose_groups'].pop('a'),
                   lambda d:d['evidence'].update(view='artifact'),
                   lambda d:d.update(mode='supplied',supplied_purpose={'first':1.,'second':1.})):
        data=bundle();mutate(data)
        with pytest.raises(ValueError):forecast(data,Budget(10000))


def test_actual_restricted_purpose_calls_equal_independent_computation(tmp_path):
    for i,data in enumerate((bundle(),{**bundle(),'mode':'supplied','supplied_purpose':{'first':1.,'second':0.}})):
        actual=execute(data,operation='purpose_comparison',root=tmp_path/str(i))
        assert actual['accepted'],actual
        expected=forecast(data,Budget(500000))
        assert actual['prediction']['predictions']==expected['predictions']
    hidden={**bundle(),'hidden_truth':'first'}
    assert not execute(hidden,operation='purpose_comparison',root=tmp_path/'hidden')['accepted']
