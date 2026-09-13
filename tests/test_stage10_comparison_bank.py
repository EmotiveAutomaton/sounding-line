from dataclasses import asdict
import copy
import pytest
from runners.stage10 import comparison_bank,comparison_inputs,revision_source,await_local
from runners.stage10.queue import read
from runners.stage10.ollama import write_new
from tests.test_stage10_revision import record


def test_whole_source_cells_costs_null_and_incomplete_denominators():
    tasks=[];labels={};routes={'R0':{},'R2':{},'R3':{}}
    for i in range(3):
        task=revision_source.task_from(record(i,'held-'+str(i)),'artifact');tasks.append(asdict(task))
        labels[task.task_id]={'correct_choice':task.choices[0][0],'writer_component':str(i),'prompt_component':str(i),'source_event':str(i)}
        forecast={'choice':task.choices[0][0],'probabilities':{k:1/3 for k,v in task.choices},'insufficient_evidence':True,'explanation':'known null'}
        for a in routes:routes[a][task.task_id]={'status':'VALID','forecast':forecast,'model_calls':2,'generated_tokens':100}
    cells=comparison_inputs.capsules(tasks,labels,routes,'known population','fixture')
    bundle={'schema':'stage10.comparison-bank.1','sources':{},'cells':cells,'scope':'constructed'}
    result=comparison_bank.analyze(bundle)['results'][0]
    assert result['paired']['R3 vs R2']['brier']['estimate']==0
    assert result['costs']['R3']['model_calls']==6
    broken=copy.deepcopy(bundle);del broken['cells'][0]['predictions']['R3'][tasks[0]['task_id']]
    with pytest.raises(ValueError,match='incomplete'):comparison_bank.analyze(broken)
    changed=copy.deepcopy(bundle);changed['cells'][0]['predictions']['R3'][tasks[0]['task_id']]={'task_public':revision_source.task_from(record(),'artifact').public(),'status':'INVALID','forecast':None}
    with pytest.raises(ValueError):comparison_bank.analyze(changed)


def test_native_wait_advances_only_on_terminal_and_refuses_disappearance(tmp_path):
    owner=tmp_path/'OWNER.json';write_new(owner,{'native':{'pid':42,'created_ticks':123}})
    complete=tmp_path/'source/COMPLETE.json';failed=tmp_path/'source/FAILED.json';calls=[]
    def pause(seconds):calls.append(seconds);write_new(complete,{'status':'COMPLETE','all_jobs_succeeded':False})
    output=tmp_path/'wait'
    result=await_local.run(owner,complete,failed,output,inspect=lambda _:read(owner)['native'],pause=pause)
    assert result['status']=='COMPLETE' and calls==[10]
    assert read(output/'PREDECESSOR.json')['all_jobs_succeeded'] is False
    with pytest.raises(RuntimeError,match='disappeared'):
        await_local.run(owner,tmp_path/'missing',failed,tmp_path/'other',inspect=lambda _:None,pause=lambda _:None)
