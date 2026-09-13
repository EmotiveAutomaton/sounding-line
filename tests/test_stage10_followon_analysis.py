import copy
from dataclasses import asdict,replace
from pathlib import Path
import pytest
from runners.stage10 import followon_analysis as f,comparison,comparison_inputs as ci,runway_packet
from runners.stage10.contracts import digest
from runners.stage10.ollama import write_new
from runners.stage10.queue import read
from runners.stage10.revision_bank import finish,sha
from tests.test_stage10_revision import record


def pair_fixture():
    task=ci.revision_source.task_from(record(),'process-record')
    a=replace(task,evidence={'document':'known','earlier_handling':['accept']})
    b=replace(a,task_id=digest('other')[:32],evidence={**a.evidence,'earlier_handling':['ignore']})
    truth=a.choices[0][0];p={k:1/len(a.choices) for k,v in a.choices}
    forecast={'choice':truth,'probabilities':p,'insufficient_evidence':True,'explanation':'uniform null'}
    answer={'truth':truth,'group':'writer','dependencies':['prompt'],'event':'event'}
    def cell(t):return comparison.cell([t],{t.task_id:answer},{t.task_id:{'task_public':t.public(),'status':'VALID','forecast':forecast}},'history')
    pair={'original':asdict(a),'altered':asdict(b),'original_writer':'writer','donor_writer':'other'}
    return a,b,pair,cell


def test_history_intervention_has_separate_null_and_refuses_other_changes():
    a,b,pair,cell=pair_fixture();result=f.history_difference(cell(a),cell(b),[pair])
    assert result['brier']['estimate']==0 and result['generated_accuracy']['estimate']==0
    changed=replace(b,evidence={**b.evidence,'document':'changed menu'})
    with pytest.raises(ValueError,match='undeclared history'):f.history_difference(cell(a),cell(changed),[pair])
    with pytest.raises(ValueError,match='paired row roster'):comparison.paired(cell(a),cell(b))


def test_second_model_complete_join_preserves_original_null(tmp_path,monkeypatch):
    monkeypatch.setattr(f,'ROOT',tmp_path)
    a,b,pair,cell=pair_fixture();tasks=[asdict(a)];labels={a.task_id:{'correct_choice':a.choices[0][0],'writer_component':'writer','prompt_component':'prompt','source_event':'event'}}
    forecast=cell(a)['rows'][0];probability={k:1/len(a.choices) for k,v in a.choices}
    value={'status':'VALID','forecast':{'choice':a.choices[0][0],'probabilities':probability,'insufficient_evidence':True,'explanation':'null'},'model_calls':1}
    arms=['R0','R2','R3','R1-memory','R4-grounded'];routes={arm:{a.task_id:value} for arm in arms}
    bundle={'schema':'stage10.comparison-bank.1','sources':{},'scope':'fixture','cells':ci.capsules(tasks,labels,routes,'null','fixture')}
    write_new(tmp_path/'coauthor-comparison-inputs-v1/BUNDLE.json',bundle)
    selected=tmp_path/'selection';prediction=tmp_path/'prediction'
    write_new(selected/'SELECTION.json',{'arms':arms,'model':'known second profile'})
    write_new(selected/'evaluation-public.json',{'tasks':tasks});finish(selected,'fixture')
    write_new(prediction/'ROSTER.json',{'rows':[{'task_id':a.task_id,'arm':arm,'result':value} for arm in arms]});finish(prediction,'fixture')
    f.second_model(selected,prediction,tmp_path/'analysis')
    result=ci.comparison_bank.analyze(read(tmp_path/'analysis/BUNDLE.json'))
    assert result['results'][0]['paired']['second-local/R0 vs R0']['brier']['estimate']==0


def test_final_packet_retains_failure_and_rejects_missing_job(tmp_path):
    output=tmp_path/'report';queue=tmp_path/'queue';target=tmp_path/'done';write_new(target/'COMPLETE.json',{'status':'COMPLETE'})
    jobs=[{'id':'done','output':target.as_posix(),'resource':'cpu','purpose':'known fixture'},
          {'id':'failed','output':str(tmp_path/'failed'),'resource':'gpu','purpose':'retained failure'},
          {'id':'report','output':output.as_posix(),'resource':'cpu','purpose':'assemble'}]
    plan=tmp_path/'PLAN.json';write_new(plan,{'jobs':jobs})
    for job in jobs[:2]:
        write_new(queue/'jobs'/(job['id']+'.json'),{'job_sha256':digest(job),'status':'COMPLETE' if job['id']=='done' else 'FAILED',
          'files':{'COMPLETE.json':sha(target/'COMPLETE.json')},'started_at':'2026-09-13T01:00:00+00:00','finished_at':'2026-09-13T01:01:00+00:00'})
    runway_packet.assemble(plan,queue,output);value=read(output/'RESULT.json')
    assert not value['all_jobs_succeeded'] and value['jobs'][1]['status']=='FAILED' and not value['final_stage_packet']
    with pytest.raises(ValueError,match='final reviewed queue boundary'):runway_packet.assemble(plan,tmp_path/'missing',tmp_path/'other')
