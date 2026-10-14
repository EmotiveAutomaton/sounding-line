import math
import numpy as np
import pytest
from runners.stage14_midweek.analyze_modal import score, paired, holm, calibration, compare, histogram


def test_histogram_survives_json_immutable_reentry():
    import json
    value=histogram([8,8,12,16])
    assert value=={'8':2,'12':1,'16':1}
    assert json.loads(json.dumps(value))==value


def test_known_scores_and_invalid_system_penalty():
    assert score([1,0,0,0],0)['half_brier'] == 0
    assert score([.25]*4,0)['half_brier'] == .375
    assert score([0,1,0,0],0)['half_brier'] == 1
    assert score(None,0) == dict(half_brier=1., log_loss=None, system_log_loss=-math.log(.01), accuracy=0.)
    assert score([.7,.1,.1,.1],0,1)['accuracy'] == 0
    with pytest.raises(ValueError):score([float('nan'),0,0,1],0)


def test_writer_weight_null_and_determinism():
    rows=[dict(writer='a',prompt='x')]*9+[dict(writer='b',prompt='y')]
    out=paired(rows,[0]*9+[1],True)
    assert out['mean']==.5  # Event weighting would return .1.
    assert out==paired(rows,[0]*9+[1],True)
    null=paired(rows,[0]*10,True)
    assert null['mean']==0 and null['interval']==[0,0] and null['crossed_interval']==[0,0] and null['p_raw']==1
    constant=paired(rows,[.2]*10)
    assert constant['interval']==pytest.approx([.2,.2])
    assert constant['crossed_interval']==pytest.approx([.2,.2])


def test_log_loss_uses_exact_matched_valid_rows():
    rows=[dict(key=str(i),writer='a',prompt='x') for i in range(2)]
    predictions={'0':{'a':dict(scores=score(None,0)),'b':dict(scores=score([.97,.01,.01,.01],0))},
                 '1':{'a':dict(scores=score([.25]*4,0)),'b':dict(scores=score([.25]*4,0))}}
    valid=compare(rows,predictions,'a','b','log_loss')
    assert valid['targets']==1 and valid['excluded_targets']==1 and valid['mean']==0
    assert compare(rows,predictions,'a','b','half_brier')['mean']<0
    assert compare(rows,predictions,'a','b','system_log_loss')['targets']==2


def test_holm_retains_five_unavailable_tests():
    family=list('abcdefghijk')
    result=holm(dict(a=.001,b=.01,c=.1,d=.2,e=.3,f=.4),family)
    assert result['a']==pytest.approx(.011)
    assert result['b']==pytest.approx(.1)
    assert all(result[k] is None for k in 'ghijk')


def test_calibration_bins_and_stated_choice_confidence():
    out=calibration([[.7,.1,.1,.1],[0,1,0,0]],[1,1],[1,0],[1,1])
    assert out['choice_argmax_mismatches']==1
    assert out['bins'][1]['confidence']==.1 and out['bins'][9]['confidence']==1
    assert out['bins'][0]['n']==0 and out['bins'][0]['confidence'] is None
    assert out['ece']==pytest.approx(.95)
