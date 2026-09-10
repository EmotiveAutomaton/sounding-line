"""Known released-successor chronology, no future evidence and text-dependency checks."""
import copy
import pytest
from runners.stage9.common import digest
from runners.stage9.schola_cases import projected,separate,KINDS


def source():
    texts={digest(t):t for t in ('before','current','later')}
    before,current,later=map(digest,('before','current','later'))
    a={'key':'a','source_ordinal':0,'next_source_ordinal':1,'unit':'project','author':'author','session':'session',
       'before':before,'after':current,'category':'IMPLEMENTATION','location':'last_quarter',
       'usable':True,'gap_ms':1000,'next_category':'REVISION','next_location':'first_quarter'}
    b=a|{'key':'b','source_ordinal':1,'next_source_ordinal':None,'before':current,'after':later,
         'category':'REVISION','location':'first_quarter','usable':False,'exclusion':'end of stream'}
    return {'texts':texts,'records':[a,b]}


def test_verified_successor_changes_truth_without_changing_present_views():
    project=source();rows,excluded=projected(project)
    assert len(rows)==2 and excluded==[{'key':'b','reason':'end of stream'}]
    assert {r['kind'] for r in rows}==set(KINDS)
    for row in rows:
        assert row['views']['artifact']=={'document':'current'}
        assert row['views']['record']=={'document':'current','previous_document':'before',
                                       'previous_category':'IMPLEMENTATION','previous_location':'last_quarter'}
    altered=copy.deepcopy(project);altered['records'][0]['next_category']='PLANNING';altered['records'][1]['category']='PLANNING'
    changed,_=projected(altered)
    assert [r['views'] for r in changed]==[r['views'] for r in rows]
    assert [r['truth'] for r in changed]!=[r['truth'] for r in rows]
    for field,value in [('next_source_ordinal',3),('gap_ms',0),('gap_ms',1800001),('next_category','PLANNING')]:
        bad=copy.deepcopy(project);bad['records'][0][field]=value
        with pytest.raises(ValueError):projected(bad)
    for field,value in [('before',digest('before')),('author','another'),('session','another')]:
        bad=copy.deepcopy(project);bad['records'][1][field]=value
        with pytest.raises(ValueError):projected(bad)


def test_project_and_current_text_dependencies_exclude_lower_priority_only():
    class Cross:
        def filter_fit(self,fit,held):return fit-({'linked'} if 'eval' in held else set()),[]
    allocation={'eval':'evaluation','dev':'development','fit':'train','linked':'train'};rows=[]
    for unit in allocation:
        for label in ('shared','unique-'+unit):
            for kind in KINDS:
                rows.append({'key':unit+label+kind,'source_key':unit+label,'unit':unit,'source_group':unit,
                             'kind':kind,'current_text_sha256':label})
    parts,excluded=separate(rows,allocation,Cross())
    assert len(parts['evaluation'])==4 and len(parts['development'])==len(parts['train'])==2
    assert all(r['unit']=='fit' and r['current_text_sha256']=='unique-fit' for r in parts['train'])
    assert len(excluded)==8
    assert {r['reason'] for r in excluded}=={'copied normalized current text across fold','source dependency crosses project fold'}
