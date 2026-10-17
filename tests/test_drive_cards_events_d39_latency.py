import copy
import pytest
from runners.drive.cards.events_d39_latency import summarize


def fixture():
    failures=[];matches=[]
    for i in range(3):
        for kind,value in [('model',5.),('own',2.)]:
            failures.append(dict(session=f'{kind}{i}',ordinal=1,kind=kind,next_menus=[dict(observed_latency_seconds=value,latency_kind='observed_selection_or_close')]))
        matches.append(dict(writer=str(i),model_session=f'model{i}',model_ordinal=1,own_session=f'own{i}',own_ordinal=1))
    return failures,matches


def test_known_difference_null_and_missing_never_zero():
    failures,matches=fixture();r=summarize(failures,matches)
    assert r['effect_seconds']==3 and r['ci95_seconds']==[3,3]
    failures[0]['next_menus'][0]['observed_latency_seconds']=None
    r=summarize(failures,matches);assert r['observed_pairs']==2 and r['missing_model']==1 and r['effect_seconds']==3
    for row in failures:row['next_menus'][0]['observed_latency_seconds']=2
    assert summarize(failures,matches)['effect_seconds']==0


def test_changed_or_ambiguous_latency_refuses():
    failures,matches=fixture()
    for value in (-1,float('nan')):
        bad=copy.deepcopy(failures);bad[0]['next_menus'][0]['observed_latency_seconds']=value
        with pytest.raises(ValueError):summarize(bad,matches)
    bad=copy.deepcopy(failures);bad.append(copy.deepcopy(bad[0]));bad[-1]['next_menus'][0]['observed_latency_seconds']=9
    with pytest.raises(ValueError):summarize(bad,matches)
