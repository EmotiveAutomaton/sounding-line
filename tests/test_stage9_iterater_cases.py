import copy,math
import pytest
from runners.stage9.iterater_cases import iterater_rows,study_partitions
from runners.stage9.revision_analysis import select,evaluate
from runners.stage9.revision_predictions import case_contract,active_contract,ITERA_CASES
from runners.stage9.split_guard import Separation


def document(key,depth,before,after,labels,votes):
    return {'key':key,'revision_depth':depth,'before':before,'artifact':after,'labels':labels,'raw_votes':votes,
        'edits':[{'major_intent':label,'raw_intents':v} for label,v in zip(labels,votes)],
        'domain':'known','source':'IteraTeR-HUMAN-doc','group':'g','independent_unit':'g','split':'train'}


def test_genuine_future_targets_never_select_earlier_evidence():
    records=[document('a',1,'first','current',['clarity'],[['clarity','style','clarity']]),
        document('b',2,'current','private future',['style','fluency'],[['style','clarity'],['fluency']])]
    links=[{'current':'a','future':'b','split':'train'}]
    rows=iterater_rows(records,links);future=next(r for r in rows if r['task']=='future')
    assert future['raw_votes']==records[1]['raw_votes'] and future['labels']==['style','fluency']
    altered=copy.deepcopy(records);altered[1]['artifact']='a different future'
    altered[1]['labels'][0]='clarity';altered[1]['edits'][0]['major_intent']='clarity'
    changed=next(r for r in iterater_rows(altered,links) if r['task']=='future')
    assert changed['views']==future['views'] and changed['labels']!=future['labels']
    assert set(rows[0]['views'])=={'artifact','pair'} and set(future['views'])=={'artifact','record'}
    for field,value in [('before','wrong predecessor'),('independent_unit','another'),('revision_depth',3)]:
        broken=copy.deepcopy(records);broken[1][field]=value
        with pytest.raises(ValueError):iterater_rows(broken,links)
    broken=copy.deepcopy(records);broken[0]['raw_votes'][0]=['unknown']
    with pytest.raises(ValueError):iterater_rows(broken,links)


def grid(prefix):
    rows=[]
    for task,views in case_contract(ITERA_CASES)['views'].items():
        for i in range(4):
            for view in sorted(views):
                probabilities={k:{'a':p,'b':1-p} for k,p in [('lexical_delta',.7),('surface_delta',.8),('class_prior',.6),('majority',.1)]}
                if view=='record':probabilities['previous_cycle']={'a':.7,'b':.3}
                rows.append({'key':task+str(i),'unit':prefix+str(i),'task':task,'view':view,
                    'labels':['a','a','b'],'valid':True,'probabilities':probabilities})
    return rows


def test_human_views_have_exactly_the_declared_contrasts_and_no_invented_record():
    dev=grid('dev');rows=grid('test');selection=select(dev)
    result=evaluate(rows,selection,100,case_operation=ITERA_CASES)
    assert len(result['contrasts'])==6 and not result['confirmation_eligible']
    assert 'IteraTeR HUMAN' in result['source_scope']
    for contrast in result['contrasts']:
        assert contrast['estimate']['n_units']==4 and contrast['target_annotations']==12
        if contrast['left']['view']!=contrast['right']['view']:assert contrast['estimate']['mean']==0.
    # Dropping the same required view in development and evaluation cannot hide it.
    missing=[r for r in rows if (r['task'],r['view'])!=('future','record')]
    missing_dev=[r for r in dev if (r['task'],r['view'])!=('future','record')]
    with pytest.raises(ValueError):evaluate(missing,select(missing_dev),100,case_operation=ITERA_CASES)
    with pytest.raises(ValueError):evaluate(rows,selection,100,case_operation='invented-source')
    with pytest.raises(ValueError):evaluate(rows,selection,100)


def study_rows():
    rows=[];allocation={}
    for lane in ('train','development','evaluation'):
        for domain in ('arxiv','news','wiki'):
            unit=lane+'-'+domain;allocation[unit]=lane
            rows.append({'key':unit,'unit':unit,'source_group':'iterater:'+unit,'domain':domain,
                'task':'retrospective','labels':['clarity'],'views':{'artifact':{'text':unit},'pair':{'before':unit+' old','after':unit}}})
            if lane!='evaluation':
                rows.append({'key':unit+'-future','unit':unit,'source_group':'iterater:'+unit,'domain':domain,
                    'task':'future','labels':['style'],'views':{'artifact':{'text':unit},'record':{'before':unit+' old','after':unit,'earlier_labels':['clarity']}}})
    cross=Separation({r['source_group']:{} for r in rows},{'long_overlap_edges':[]})
    return rows,allocation,cross


def test_missing_real_future_does_not_delete_retrospective_or_hide_targets():
    rows,allocation,cross=study_rows();lanes,metadata=study_partitions(rows,allocation,cross,'within')
    assert metadata['active_tasks']==['retrospective']
    assert metadata['task_dispositions']['future']['disposition']=='NOT RUN WITH REASON'
    assert len(metadata['unavailable_task_cases'])==6
    assert all(len(own)==3 and all(r['task']=='retrospective' for r in own) for own in lanes.values())
    identity={'operation':ITERA_CASES,'data_scope':'constructed unit check',**metadata}
    contract=active_contract(identity);assert set(contract['views'])=={'retrospective'}
    dev=[r for r in grid('dev') if r['task']=='retrospective'];test=[r for r in grid('test') if r['task']=='retrospective']
    result=evaluate(test,select(dev),100,case_operation=ITERA_CASES,case_identity=identity)
    assert len(result['contrasts'])==3 and result['task_dispositions']==metadata['task_dispositions']
    broken=copy.deepcopy(identity);del broken['task_dispositions']['future']
    with pytest.raises(ValueError):active_contract(broken)


def test_domain_transfer_excludes_target_domain_from_training_and_selection():
    rows,allocation,cross=study_rows()
    for domain in ('arxiv','news','wiki'):
        lanes,metadata=study_partitions(rows,allocation,cross,'leave-'+domain)
        assert {r['domain'] for r in lanes['evaluation']}=={domain}
        assert all(r['domain']!=domain for lane in ('train','development') for r in lanes[lane])
        assert metadata['domain_exclusions'] and metadata['target_domain_excluded_from_fitting_and_selection']
        assert len(lanes['train'])==len(lanes['development'])==2
    with pytest.raises(ValueError):study_partitions(rows,allocation,cross,'invented-domain')
