import pytest
from runners.stage9.scholawrite_baseline import features,fit_predict
from runners.stage9.scholawrite import CATEGORIES


def test_feature_boundary_and_past_difference():
    with pytest.raises(ValueError):features({'document':'text','next_category':'PLANNING'})
    f=features({'document':'one two','previous_document':'one','previous_category':'IMPLEMENTATION','previous_location':'last_quarter'})
    assert f['past_added']>0 and f['past_removed']==0


def test_fit_rejects_group_and_content_leakage_and_learns_known_signal():
    training=[{'unit':'fit'+str(i%3),'content':str(i),'category':CATEGORIES[i%2],
               'artifact':{'planted':float(i%2)}} for i in range(80)]
    testing=[{'unit':'held','content':'unseen','artifact':{'planted':1.}}]
    p=fit_predict(training,testing,'artifact','category',CATEGORIES)[0]
    assert p['IMPLEMENTATION']>p['PLANNING'] and min(p.values())>0 and abs(sum(p.values())-1)<1e-10
    with pytest.raises(ValueError):fit_predict(training,[testing[0]|{'unit':'fit0'}],'artifact','category',CATEGORIES)
    with pytest.raises(ValueError):fit_predict(training,[testing[0]|{'content':'1'}],'artifact','category',CATEGORIES)
