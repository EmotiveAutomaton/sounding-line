"""Current opportunity excludes its own outcome and all later handling."""
import copy
import pytest
from runners.stage9.coauthor_cases import session_rows,components
from runners.stage9.split_guard import Separation


def session():
    return {'key':'session','writer':'writer','prompt':'prompt','domain':'creative','usable':True,'events':[
        {'ordinal':1,'usable':True,'decision':'accept','document':'first draft','options':[{'trimmed':'first suggestion'}]},
        {'ordinal':2,'usable':False,'decision':'ignore','document':'ambiguous','options':[{'trimmed':'unused'}]},
        {'ordinal':3,'usable':True,'decision':'dismiss','document':'later draft','options':[{'trimmed':'last suggestion'}]}]}


def test_future_handling_mutation_and_unsupported_history():
    original=session();rows,excluded=session_rows(original)
    assert len(rows)==2 and len(excluded)==1
    assert rows[0]['views']['record']['earlier_handling']==[]
    assert rows[1]['views']['record']['earlier_handling']==['accept'] and rows[1]['prior_source_ordinals']==[1]
    altered=copy.deepcopy(original);altered['events'][-1]['decision']='edit';changed,_=session_rows(altered)
    assert [r['views'] for r in rows]==[r['views'] for r in changed]
    altered['events'].reverse()
    with pytest.raises(ValueError):session_rows(altered)


def test_long_text_links_are_dependencies_not_extra_people():
    groups={k:{'corpus':'coauthor'} for k in ('coauthor:a','coauthor:b','coauthor:c')}
    cross=Separation(groups,{'long_overlap_edges':[{'groups':['coauthor:a','coauthor:b'],
        'witnesses':[{'roles':['artifact']},{'roles':['artifact']}]}]})
    mapping=components(cross,'coauthor')
    assert mapping['coauthor:a']==mapping['coauthor:b'] and mapping['coauthor:a']!=mapping['coauthor:c']
