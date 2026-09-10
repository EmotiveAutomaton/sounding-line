import pytest
from runners.stage9.arxivedits import LABELS
from runners.stage9.arxivedits_baseline import fit_predict,prior,vector


def test_paper_weight_and_truth_blind_features():
    row={'independent_unit':'a','label':'Content','before':'old title','artifact':'new title'}
    other=row|{'independent_unit':'b','label':'Format'}
    assert prior([row,other])==prior([row]*8+[other])
    assert vector(row,'pair')==vector(row|{'label':'Format'},'pair')
    with pytest.raises(ValueError,match='overlap'):fit_predict([row],[row],'pair')


def test_planted_text_signal_and_fixed_missing_class_support():
    training=[{'independent_unit':str(i),'label':'Content' if i%2 else 'Format',
               'artifact':'meaning fact' if i%2 else 'punctuation layout','before':''} for i in range(30)]
    testing=[r|{'independent_unit':'held'+str(i)} for i,r in enumerate(training[:2])]
    forecasts=fit_predict(training,testing,'artifact')
    for row,p in zip(testing,forecasts):
        assert set(p)==set(LABELS) and abs(sum(p.values())-1)<1e-9 and min(p.values())>0
        assert max(p,key=p.get)==row['label']
