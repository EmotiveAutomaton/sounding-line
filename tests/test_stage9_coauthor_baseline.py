import pytest
from runners.stage9.coauthor_baseline import features, model_fit, predict


def test_features_reject_future_target_fields():
    evidence={'document':'A current draft','suggestions':['An available continuation']}
    with pytest.raises(ValueError):features(evidence|{'selected_index':0})
    with pytest.raises(ValueError):features(evidence|{'decision':'accept'})
    assert features(evidence)['mean_context_overlap']==0


def test_known_prospective_history_beats_no_signal_and_keeps_all_classes():
    rows=[]
    for i in range(200):
        truth='accept' if i%2 else 'dismiss'
        evidence={'document':'same current draft','suggestions':['same available continuation']}
        rows.append({'truth':truth,'artifact':evidence,'record':evidence|{'earlier_handling':[truth]*3}})
    fitted=model_fit(rows,'record');output=predict(fitted,rows,'record')
    assert all(p[r['truth']]>.9 and sum(p.values())==pytest.approx(1) for p,r in zip(output,rows))
    blind=predict(model_fit(rows,'artifact'),rows,'artifact')
    assert all(p['accept']==pytest.approx(p['dismiss']) for p in blind)
