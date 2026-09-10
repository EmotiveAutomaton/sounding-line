"""Independent strong-rival selection, crossed source dependence and invalid rows."""
import copy
import pytest
from runners.stage9.record_jobs import select,evaluate


def rows(prefix,n=2):
    out=[]
    probability=lambda p:{'accept':p,'edit':(1-p)/3,'dismiss':(1-p)/3,'ignore':(1-p)/3}
    for i in range(n):
        for view in ('artifact','record'):
            models={k:probability(.6 if k=='lexical' else .8 if k=='surface' else .25) for k in ('lexical','surface','class_prior','majority')}
            if view=='record':models.update(previous_transition=probability(.9),persistence=probability(.7))
            out.append({'key':prefix+str(i),'unit':prefix+'person'+str(i),'stimulus':prefix+'prompt'+str(i),
                'kind':'coauthor','view':view,'truth':'accept','valid':True,'probabilities':models})
    return out


def test_independent_rivals_and_crossed_complete_targets():
    choice=select(rows('dev'));assert choice['coauthor']['artifact']['selected']=='surface'
    assert choice['coauthor']['record']['selected']=='previous_transition'
    actual=evaluate(rows('eval'),choice,True,draws=100)
    assert len(actual['contrasts'])==3 and actual['crossed_source_stimulus']
    assert all(r['estimate']['mean']<0 for r in actual['contrasts'][:2])
    assert actual['contrasts'][2]['estimate']['mean']==0
    assert all(r['source_units']==r['stimuli']==2 for r in actual['contrasts'])
    bad=rows('eval');bad[-1]['unit']='devperson0'
    with pytest.raises(ValueError):evaluate(bad,choice,True,draws=100)
    bad=rows('eval');bad[-1]['stimulus']='devprompt0'
    with pytest.raises(ValueError):evaluate(bad,choice,True,draws=100)


def test_missing_invalid_and_nonfinite_forecasts_stay_visible():
    choice=select(rows('dev'));bad=rows('eval');bad[-1]['valid']=False;bad[-1]['probabilities']=None
    actual=evaluate(bad,choice,True,draws=100)
    assert actual['contrasts'][1]['disposition']=='IMPLEMENTATION INVALID' and actual['contrasts'][1]['assigned']==2
    assert actual['contrasts'][1]['excluded']==0 and actual['contrasts'][1]['scored']==0
    with pytest.raises(ValueError):evaluate(rows('eval')[:-1],choice,True,draws=100)
    zeros=rows('zero',1)
    for row in zeros:
        for model in row['probabilities']:row['probabilities'][model]={'accept':0.,'edit':1.,'dismiss':0.,'ignore':0.}
    result=evaluate(zeros,choice,True,draws=100)
    assert all(r['estimate']['finite_estimate'] is False for r in result['contrasts'])
