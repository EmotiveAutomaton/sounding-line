"""Complete outer folds retain project dependence, strong rivals and failures."""
import copy
import pytest
from runners.stage9.record_jobs import contract,select,fold_summary


def forecasts(project,signal=.8):
    rows=[]
    for kind,classes in contract('scholawrite').items():
        truth=classes[0]
        for view in ('artifact','record'):
            names=['lexical','surface','class_prior','majority']+(['previous_transition','persistence'] if view=='record' else [])
            probabilities={}
            for name in names:
                p=signal if name=='lexical' else 1/len(classes)
                probabilities[name]={c:p if c==truth else (1-p)/(len(classes)-1) for c in classes}
            rows.append({'key':project+kind,'unit':project,'stimulus':project,'kind':kind,
                         'truth':truth,'view':view,'valid':True,'probabilities':probabilities})
    return rows


def folds(signal=.8):
    projects=list('ABCDE');out=[]
    for i,project in enumerate(projects):
        dev=projects[(i+1)%5]
        out.append({'fold':i,'held_project':project,'selection_project':dev,
                    'allocation':{p:'evaluation' if p==project else 'development' if p==dev else 'train' for p in projects},
                    'predictions':forecasts(project,signal),'selection':select(forecasts(dev,signal))})
    return out


def test_outer_profile_retains_all_projects_and_known_signal():
    result=fold_summary(folds(),draws=100)
    assert result['projects']==5 and len(result['contrasts'])==6
    assert not result['scientific_admission'] and not result['confirmation_eligible']
    for row in result['contrasts']:
        assert row['profile']['source_units']==5 and row['profile']['assigned']==5
        assert len(row['leave_one_project_out'])==5
        mean=row['profile']['estimate']['mean']
        assert mean==0 if row['comparison']=='record_gain' else mean>0
    bad=fold_summary(folds(.05),draws=100)
    assert all(r['profile']['estimate']['mean']<0 for r in bad['contrasts'] if r['comparison']!='record_gain')


def test_missing_fold_wrong_selection_and_bad_call_cannot_disappear():
    original=folds()
    with pytest.raises(ValueError):fold_summary(original[:-1],draws=100)
    bad=copy.deepcopy(original);bad[-1]['fold']=0
    with pytest.raises(ValueError):fold_summary(bad,draws=100)
    bad=copy.deepcopy(original);bad[0]['selection']['schola_category']['record']['source_units']=['A']
    with pytest.raises(ValueError):fold_summary(bad,draws=100)
    bad=copy.deepcopy(original);bad[0]['predictions'][0].update(valid=False,probabilities=None)
    result=fold_summary(bad,draws=100)
    affected=[r for r in result['contrasts'] if r['profile']['kind']=='schola_category' and r['comparison']!='record_rival']
    assert all(r['profile']['disposition']=='IMPLEMENTATION INVALID' and r['profile']['assigned']==5 and r['profile']['excluded']==0 for r in affected)
    bad=copy.deepcopy(original);bad[0]['selection']['schola_category']['record'].update(accepted=False,selected=None)
    result=fold_summary(bad,draws=100)
    affected=next(r for r in result['contrasts'] if r['profile']['kind']=='schola_category' and r['comparison']=='record_rival')
    assert affected['profile']['disposition']=='NOT RUN WITH REASON' and affected['profile']['assigned']==5


def test_outer_source_operation_signatures_require_each_rotation():
    from runners.stage9.launch import handler_operation
    def job(*args):return {'module':'runners.stage9.record_jobs','arguments':list(args)}
    signatures=[handler_operation(job('prepare','--dataset','scholawrite','--fold',str(i))) for i in range(5)]
    assert len(set(signatures))==5
    assert handler_operation(job('collect'))[1]=='collect'
    for args in [('prepare','--dataset','scholawrite'),('prepare','--dataset','scholawrite','--fold','5'),('prepare','--dataset','coauthor','--fold','0')]:
        with pytest.raises(ValueError):handler_operation(job(*args))
