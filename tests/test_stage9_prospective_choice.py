import copy
from runners.stage9.generation_pilot import original_world
from runners.stage9.series_cases import prepare_case
from runners.stage9.prospective_choice import choice_input
from runners.stage9.neural_operations import unit_result


def case():
    world=original_world('S9GEN|essay|pilot|original|reader|3')
    result=prepare_case(world,[],3,'pilot')
    assert result['realized']
    # prepare_case creates public/truth projections; the source-preparation owner
    # attaches its original world separately, as construct_attempt does in science.
    return {**result,'source_worlds':[world]}


def test_structured_views_share_options_and_artifact_has_no_hidden_clock():
    row=case();artifact=choice_input(row,'artifact_choice');process=choice_input(row,'process_choice')
    assert artifact['options']==process['options']
    assert '"events"' not in artifact['prefix'] and '"events"' in process['prefix']
    assert 'action number' not in artifact['prefix'] and 'requested_boundary' not in artifact['prefix']
    assert 'earlier' not in artifact['prefix'] and 'stop' in artifact['options']


def test_private_truth_and_future_changes_cannot_change_the_choice_inputs():
    row=case();altered=copy.deepcopy(row);altered['target']='stop'
    world=altered['source_worlds'][0]
    world['trajectory']['steps']=world['trajectory']['steps'][:3]+[{'hidden_future':'CANARY'}]
    world['trajectory']['changes']=[(30,'CANARY')]
    world['state']['persistent_tendency']={'private':'CANARY'}
    for op in ('genuine_choice','process_choice','artifact_choice'):
        assert choice_input(row,op)==choice_input(altered,op)
        assert 'CANARY' not in choice_input(altered,op)['prefix']


def test_actual_shared_handler_executes_each_choice_and_repair_operation():
    row=case();seen=[]
    def call(evidence,task,index):
        seen.append(index)
        if task['operation']=='generate':return {'accepted':True,'prediction':{'text':'00 stop'}}
        options=evidence['options'];return {'accepted':True,'prediction':{'probs':{k:1/len(options) for k in options}}}
    for op in ('genuine_choice','process_choice','artifact_choice'):
        result=unit_result(row,op,call)
        assert result['result']['target']==row['target']
    for op in ('local_repair_artifact','local_repair_process'):
        result=unit_result(row,op,call)
        assert result['result']['repair_execution']['legal'] and not result['result']['repair_execution']['goal_improving']
    assert len(seen)==7
