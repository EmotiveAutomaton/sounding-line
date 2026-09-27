import math
import json
import pytest
from runners.stage13.scoring import probabilities,proper_loss,span_scores,interval,threshold,confusion
from runners.stage13.splits import components,partition


def test_invalid_is_not_repaired_and_all_attempt_loss():
    for bad in ([.2,.2],[True,False],[float('nan'),0],{'p':[1,0]},'```[1,0]```',None):
        assert probabilities(bad,2) is None
        assert proper_loss(bad,0,2)['brier']==2
    assert proper_loss('[1,0]',0,2)['brier']==0
    assert proper_loss([0,1],0,2)['brier']==2
    assert proper_loss([.5,.5],0,2)['log_loss']==pytest.approx(math.log(2))


def test_locations_have_strict_and_relaxed_but_wrong_span_fails():
    assert span_scores([[2,6]],[[2,6]],10)['strict']['f1']==1
    assert span_scores([[2,6]],[[3,6]],10)['strict']['f1']==0
    assert span_scores([[2,6]],[[3,6]],10)['relaxed']['f1']==1
    assert span_scores([[0,2]],[[5,7]],10)['relaxed']['f1']==0
    assert span_scores([[2,4],[4,6]],[[2,6]],10)['relaxed']['precision']==.5
    with pytest.raises(ValueError):span_scores([[2,6],[4,8]],[],10)


def test_calibration_ties_zero_errors_and_unknown_precision():
    cut=threshold([.1]*300+[.9]*2,.01)
    r=confusion([0]*302+[1]*8,[.1]*300+[.9]*2+[1]*8,cut)
    assert r['fp']==2 and r['tp']==8
    assert confusion([0]*300+[1],[.1]*301,.1)['precision'] is None
    assert confusion([0]*300,[.1]*300,.1)['zero_fp_95_upper']==pytest.approx(1-.05**(1/300))


def test_cluster_interval_survives_json_and_order():
    v=[0,1,1,1];u=['z','z','a','b']
    expected=interval(v,u)
    assert expected==interval(v[::-1],u[::-1])
    assert expected==interval(*json.loads(json.dumps([v,u])))
    assert expected['units']==3 and expected['mean']==pytest.approx(5/6)


def test_copy_and_near_copy_quarantine_and_stable_partition():
    text=' '.join('word'+str(i) for i in range(200))
    sources={'a':dict(text=text,split='train'),'b':dict(text=text+' extra',split='test'),'c':dict(text='wholly unrelated item',split='dev')}
    roots,conflicts,links=components(sources)
    assert roots['a']==roots['b'] and roots['a'] in conflicts
    assert roots['c'] not in conflicts
    assert partition('dev','same')==partition('dev','same')


def test_complete_detector_consumer_freezes_calibration_before_reserve(tmp_path):
    from runners.stage13.detectors import fit_and_select,evaluate,SURFACE_NAMES
    def rows(part):
        result=[]
        for i in range(12):
            for label in (0,1):
                r=dict(key=f'{part}-{i}-{label}',unit=f'{part}-{i}',label=label,surface=[float(label)]*len(SURFACE_NAMES),e5_logit=-3+6*label,e5_probability=.05+.9*label,lm_nll=2.-label,lm_logrank=1.-.5*label,domain='fixture',generator='fixture' if label else 'human-seed',version=label,operation='insert' if label else 'none',text='fixed fixture')
                for prefix in ('located','direct'):
                    for name in ('mean','max','entropy','transitions','fraction'):r[prefix+'_'+name]=float(label)
                result.append(r)
        return result
    selected=fit_and_select(rows('train'),rows('dev'),rows('cal'),tmp_path)
    assert len(selected['finalists'])==2 and not selected['reserve_opened']
    report=evaluate(selected,rows('reserve'))
    assert 'all' in report['comparisons']
    assert report['comparisons']['all']['released-e5']['thresholds']['0.01']['fpr']==0
    assert report['comparisons']['all']['released-e5']['thresholds']['0.01']['tpr']==1
