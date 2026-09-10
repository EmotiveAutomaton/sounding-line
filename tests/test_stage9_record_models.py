"""Current-state signal, history controls, native supports and source weighting."""
import pytest
from runners.stage9.record_features import SUPPORT,features,predict
from runners.stage9.record_models import all_models,weights_and_prior


def sample(i,kind,record=False):
    positive=i%2==0
    evidence={'document':'bright meadow' if positive else 'dark tunnel'}
    if kind=='coauthor':
        evidence['suggestions']=['Continue the scene']
        if record:evidence['earlier_handling']=[]
        truth='accept' if positive else 'dismiss'
    else:
        if record:evidence.update(previous_document='earlier version',previous_category='PLANNING',previous_location='first_quarter')
        truth=('PLANNING' if positive else 'REVISION') if kind=='schola_category' else ('first_quarter' if positive else 'last_quarter')
    return {'key':str(i),'unit':str(i),'truth':truth,'evidence':evidence}


@pytest.mark.parametrize('kind',list(SUPPORT))
def test_current_text_known_signal_and_explicit_missing_classes(kind):
    rows=[sample(i,kind) for i in range(64)];models=all_models(rows,kind,False);target=sample(100,kind)
    actual=predict(target['evidence'],models['lexical']);base=predict(target['evidence'],models['class_prior'])
    assert actual[target['truth']]>base[target['truth']]+.25
    assert set(actual)==set(SUPPORT[kind]) and all(p>0 for p in actual.values()) and sum(actual.values())==pytest.approx(1)
    assert predict(target['evidence'],models['surface'])==pytest.approx(predict(sample(101,kind)['evidence'],models['surface']))
    with pytest.raises(ValueError):predict({**target['evidence'],'next_label':target['truth']},models['lexical'])


def test_history_rivals_and_no_history_fallback():
    rows=[sample(i,'coauthor',True) for i in range(32)];models=all_models(rows,'coauthor',True);e=sample(100,'coauthor',True)['evidence']
    assert predict(e,models['previous_transition'])==pytest.approx(predict(e,models['class_prior']))
    assert predict(e,models['persistence'])==predict(e,models['class_prior'])
    with pytest.raises(ValueError):predict({'document':e['document'],'suggestions':e['suggestions']},models['previous_transition'])
    assisted={**e,'earlier_handling':['edit']};assert predict(assisted,models['persistence'])['edit']>.99


def test_group_mass_and_single_class_retention():
    rows=[sample(i,'schola_category') for i in range(4)]
    for row in rows[1:]:row['unit']='repeated'
    weights,prior=weights_and_prior(rows,'schola_category');assert weights[0]==pytest.approx(sum(weights[1:]))
    for row in rows:row['truth']='PLANNING'
    models=all_models(rows,'schola_category',False)
    assert models['lexical']['method']=='prior' and set(predict(rows[0]['evidence'],models['lexical']))==set(SUPPORT['schola_category'])
    with pytest.raises(ValueError):weights_and_prior(rows+[rows[0]],'schola_category')
