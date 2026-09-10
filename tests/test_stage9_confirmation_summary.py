import copy

import pytest

from runners.stage9 import confirmation_summary as subject
from runners.stage9.common import digest, write


def fixture(tmp_path, monkeypatch, selected=True):
    monkeypatch.setattr(subject, 'REPO', tmp_path)
    freeze = {'id':'freeze','produces':'freeze/COMPLETE.json'}
    execute = {'id':'execute','module':'runners.stage9.confirmation_baselines',
               'arguments':['--claim','one','--scope','pilot','--freeze',str(tmp_path/'freeze')]}
    final = {'id':'final','module':'runners.stage9.confirmation_summary','role':'closure',
             'after':['freeze','execute'],'allow_failed_dependencies':True}
    plan = {'jobs':[freeze,execute,final],'confirmation_result_jobs':{'one':'execute'}}
    context = {'plan':plan,'review':{'selected':[{'id':'one'}] if selected else [],
                                   'policy':{'candidates':{'one':{}}}},'scope':'pilot','freeze_job':'freeze',
               'freeze_complete_sha256':'a'*64,'claims_sha256':'b'*64}
    state = {'manifest_sha256':digest(plan),'jobs':{'execute':{
        'status':'FAILED','reason':'retained worker failure','disposition_sha256':'c'*64}}}
    write(tmp_path/'STATUS.json',state)
    seen=[]
    monkeypatch.setattr(subject,'verify_disposition',lambda q,j,s:seen.append(s['status']))
    cell = digest({'manifest_sha256':digest(plan),'job':final})
    return context,cell,seen


def test_failed_selected_execution_remains_in_its_original_family(tmp_path, monkeypatch):
    context,cell,seen=fixture(tmp_path,monkeypatch)
    result=subject.collect(context,tmp_path,cell)
    assert seen==['FAILED'] and result['family']['selected_count']==1
    assert result['family']['claims']['one']['status']=='FAILED'
    assert result['family']['claims']['one']['multiplicity']['reject'] is False
    assert not result['scientific_confirmation']


def test_empty_selection_has_no_execution_or_fabricated_result(tmp_path, monkeypatch):
    context,cell,seen=fixture(tmp_path,monkeypatch,False)
    result=subject.collect(context,tmp_path,cell)
    assert not seen and not result['execution_receipts'] and result['family']['selected_count']==0


@pytest.mark.parametrize('fault',['running','other_claim','missing_dependency','missing_mapping'])
def test_final_family_refuses_unfinished_or_substituted_execution(tmp_path, monkeypatch, fault):
    context,cell,_=fixture(tmp_path,monkeypatch)
    if fault=='running':
        write(tmp_path/'STATUS.json',{'manifest_sha256':digest(context['plan']),'jobs':{'execute':{'status':'RUNNING'}}})
    else:
        plan=context['plan']
        if fault=='other_claim':plan['jobs'][1]['arguments'][1]='replacement'
        elif fault=='missing_dependency':plan['jobs'][2]['after']=['freeze']
        else:plan['confirmation_result_jobs']={}
        write(tmp_path/'STATUS.json',{'manifest_sha256':digest(plan),'jobs':{'execute':{'status':'FAILED'}}})
        cell=digest({'manifest_sha256':digest(plan),'job':plan['jobs'][2]})
    with pytest.raises(ValueError):subject.collect(context,tmp_path,cell)
