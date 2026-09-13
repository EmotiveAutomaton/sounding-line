from copy import deepcopy
from dataclasses import replace
import pytest
from runners.stage10 import comparison,gear3_comparison as g3,human_memory_checks as fixtures
from runners.stage10.contracts import digest


def make_cell(tasks, probabilities, groups=None):
    answers={t.task_id:{'group':groups[i] if groups else str(i),'event':'event-'+str(i),'dependencies':[],
                        'truth':t.choices[0][0]} for i,t in enumerate(tasks)}
    predictions={}
    for t,p in zip(tasks,probabilities):
        forecast=None if p is None else {'choice':t.choices[0][0],
            'probabilities':{k:p if i==0 else (1-p)/(len(t.choices)-1) for i,(k,v) in enumerate(t.choices)},
            'explanation':'fixture','insufficient_evidence':False}
        predictions[t.task_id]={'task_public':t.public(),'status':'INVALID' if p is None else 'VALID','forecast':forecast}
    return comparison.cell(tasks,answers,predictions,'frozen-fixture')


def test_interaction_known_answer_null_invalid_and_infinite():
    tasks=[fixtures.task(i+100,2) for i in range(3)]
    identical=make_cell(tasks,[.5,None,0])
    cells={k:deepcopy(identical) for k in ('9b-R2','9b-R3','27b-R2','27b-R3')}
    result=g3.interaction(cells)
    assert result['brier']['estimate']==0 and result['finite_log']['observations']==1
    cells['27b-R3']=make_cell(tasks,[1,None,0])
    expected=(identical['rows'][0]['brier_system'])/3
    assert g3.interaction(cells)['brier']['estimate']==pytest.approx(expected)
    cells['27b-R3']['rows'].pop()
    with pytest.raises(ValueError):g3.interaction(cells)


@pytest.mark.parametrize('condition',['other-writer','artifact-only'])
def test_exact_history_delta_and_common_donor_graph(condition):
    tasks=[replace(fixtures.task(i+100,2),evidence_view='process-record',
                   evidence={**fixtures.task(i+100,2).evidence,'earlier_handling':['accept','edit']}) for i in range(2)]
    altered=[];donors={}
    for t in tasks:
        donor_public=deepcopy(t.public());donor_public['evidence']['earlier_handling']=['reject','accept']
        donors[t.task_id]={'group':'shared-donor','dependencies':['shared-donor-prompt'],
                           'public':donor_public,'source_record_sha256':digest(donor_public)}
        evidence=deepcopy(t.evidence)
        if condition=='other-writer':evidence['earlier_handling']=['reject','accept']
        else:evidence.pop('earlier_handling')
        altered.append(replace(t,evidence=evidence,evidence_view='artifact' if condition=='artifact-only' else 'process-record'))
    left=make_cell(tasks,[.5,.5]);right=make_cell(altered,[.5,.5]);before=deepcopy((left,right))
    with pytest.raises(ValueError):comparison.paired(left,right)
    result=g3.history_contrast(left,right,condition=condition,donors=donors)
    assert result['brier']['estimate']==0 and result['brier']['components']==1
    assert (left,right)==before
    for field in ('truth','event','group'):
        bad=deepcopy(right);bad['rows'][0][field]='changed'
        with pytest.raises(ValueError):g3.history_contrast(left,bad,condition=condition,donors=donors)
    bad=deepcopy(right);bad['rows'][0]['public']['choices'].reverse()
    with pytest.raises(ValueError):g3.history_contrast(left,bad,condition=condition,donors=donors)
    bad=deepcopy(donors);bad[tasks[0].task_id]['public']['evidence']['earlier_handling'].pop()
    with pytest.raises(ValueError):g3.history_contrast(left,right,condition=condition,donors=bad)


def test_writer_replication_and_component_bootstrap_are_stable():
    tasks=[fixtures.task(i+200,2) for i in range(10)]
    x=make_cell(tasks,[.5]*10);y=make_cell(tasks,[1]*10)
    cells={'9b-R2':x,'9b-R3':x,'27b-R2':x,'27b-R3':y}
    result=g3.interaction(cells)
    assert result['brier']['components']==10 and '2000' in result['brier']['method']
    for c in cells.values():c['rows'].reverse()
    assert g3.interaction(cells)==result
