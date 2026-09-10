"""Known diagnostic outcomes and rehashed corruption; no model execution.

Case construction and neural unit execution are fixture boundaries here. The
actual summary functions, immutable unit checks, original identity projection,
output inventory and queue dispatch run normally. Existing operation tests and
the separately archived saved-pilot replay cover the neural boundary itself.
"""
import copy
from pathlib import Path

import pytest

from runners.stage9 import closure_diagnostics as subject,operation_analysis as analysis
from runners.stage9.common import closure,digest,file_hash,read,write
from runners.stage9.scoring import score_json


def known_rows(kind):
    case={'unit':'known-source','private_factors':{'domain':'known-domain'}}
    if kind=='finite':
        queries=[]
        for condition,truth in [('distinction_left','yes'),('distinction_right','no'),
                                ('compression_left','yes'),('compression_right','yes')]:
            queries.append({'query':{'sequence':['a','b'],'condition':condition,'truth':truth},
                'call':{'accepted':True,'prediction':{'probs':{'yes':float(truth=='yes'),'no':float(truth=='no')}}}})
        rows={'finite_queries':[{'unit':case['unit'],'result':{'projection_identity':'known-projection','queries':queries}}]}
    elif kind=='prefix':
        # An unrealized assigned state stays visible and supplies no contrast.
        rows={'prefix_match':[{'unit':case['unit'],'result':{'realized':False,
            'matched_generated_state':False,'reason':'fixture has no matched state'}}]}
    elif kind=='supplied':
        calls={name:{'accepted':True,'prediction':{'probs':{'a':.5,'b':.5}}}
               for name in ('explicit','full','parameters_only')}
        rows={'supplied_kernel':[{'unit':case['unit'],'domain':'known-domain',
            'result':{'calls':calls,'target':'a','information_sha256':digest('same supplied state')}}]}
    else:
        # Early STOP has a known zero sustained-action rate at every horizon.
        result={'attempts':[{'evidence_sha256':digest('same initial question'),'valid_execution':True}],
            'assistance':'fixture assistance','stopped':True,'failure':None,
            'horizons':{str(h):{'reached_action_horizon':False,'all_observed_actions_legal':True,
                              'stopped':True,'reset_realized':False} for h in analysis.HORIZONS}}
        rows={op:[{'unit':case['unit'],'result':copy.deepcopy(result)}] for op in analysis.ROLLOUTS}
    return [case],rows


def saved(tmp_path,monkeypatch,kind='supplied'):
    for module in (subject,analysis):
        monkeypatch.setattr(module,'REPO',tmp_path)
        monkeypatch.setattr(module,'inside',lambda path:Path(path).resolve())
    monkeypatch.setattr(analysis,'ROOT',tmp_path)
    monkeypatch.setattr(subject,'verify_committed',lambda *a:None)
    cases,rows=known_rows(kind);cases_path=tmp_path/'cases';write(cases_path/'COMPLETE.json',{'fixture':'assigned cohort'})
    case_sha=file_hash(cases_path/'COMPLETE.json');package={'reader':'same known package'}
    monkeypatch.setattr(analysis,'case_inputs',lambda *a:(copy.deepcopy(cases),'pilot',case_sha))
    groups={'known-projection':[cases[0]['unit']]} if kind=='finite' else None
    monkeypatch.setattr(analysis,'group_cases',lambda own:(own,copy.deepcopy(groups)))
    monkeypatch.setattr(analysis,'unit_result',lambda case,op,call:copy.deepcopy(rows[op][0]))
    paths={}
    for op,data in rows.items():
        path=tmp_path/'inputs'/op;paths[op]=str(path)
        identity={'cell_identity':digest(op),'scope':'pilot','role':'pilot','operation':op,
            'cases_complete_sha256':case_sha,'units':[cases[0]['unit']],'projection_groups':groups}
        write(path/'IDENTITY.json',identity);write(path/'PACKAGE.json',package)
        write(path/'units'/(digest(cases[0]['unit'])+'.json'),
              {'identity':digest(identity),'key':cases[0]['unit'],'complete':True,'row':data[0]})
        write(path/'COMPLETE.json',{'identity_sha256':digest(identity),'cell_identity':identity['cell_identity'],
            'outputs':closure([path/'IDENTITY.json',path/'PACKAGE.json',path/'units'])})
    declaration=tmp_path/'PLAN.json';write(declaration,{'operation':kind,'inputs':paths})
    output=tmp_path/'private/operation-analysis-pilots/fixture'
    job={'id':'diagnostic','module':subject.MODULE,'arguments':['--output',str(output),'--cases',str(cases_path),
        '--plan',str(declaration),'--scope','pilot'],'produces':str(output/'COMPLETE.json')}
    files={'runners/stage9/original.py':digest('original source')}
    queue_files=files|{'runners/run_arg_replication.py':digest('queue-only source')}
    plan={'jobs':[job],'sources':{'files':queue_files,'sha256':digest(queue_files)}}
    cell=digest({'manifest_sha256':digest(plan),'job':job})
    # Literal original identity, independent of the constructor under test.
    identity={'cell_identity':cell,'operation':'complete-operation-analysis-v1','kind':kind,'scope':'pilot',
        'source':{'files':files,'sha256':digest(files)},'plan_sha256':file_hash(declaration),
        'inputs':{op:file_hash(Path(p)/'COMPLETE.json') for op,p in paths.items()},
        'packages':{op:package for op in paths},'cases_complete_sha256':case_sha}
    write(output/'IDENTITY.json',identity)
    write(output/'PROFILE.json',score_json(analysis.summarize(kind,cases,rows)))
    done={'cell_identity':cell,'identity_sha256':digest(identity),'execution_complete':True,'scientific_admission':False,
        'wall_seconds':1.,'parent_cpu_seconds':.5}
    def seal():
        done['identity_sha256']=digest(read(output/'IDENTITY.json'))
        done['outputs']=closure([p for p in output.iterdir() if p.name not in ('COMPLETE.json','WRITER.lock')])
        write(output/'COMPLETE.json',done)
    seal()
    from runners.stage9.queue import writer
    with writer(output):pass
    def forbidden(*a,**k):pytest.fail('read-only diagnostic acquired a writer or started execution')
    for name in ('Units','writer','run','freeze'):monkeypatch.setattr(analysis,name,forbidden)
    return output,job,plan,done,seal


@pytest.mark.parametrize('kind',['finite','prefix','supplied','rollouts'])
def test_all_diagnostics_reconstruct_known_outcomes_and_preserve_bytes(tmp_path,monkeypatch,kind):
    output,job,plan,_,_=saved(tmp_path,monkeypatch,kind)
    before=closure([tmp_path]);result=subject.inspect_completed(job,plan,tmp_path)
    assert result['status']=='RECONSTRUCTED' and result['kind']==kind
    assert result['scientific_admission'] is False and result['new_reader_calls']==result['new_reserve_openings']==0
    assert closure([tmp_path])==before
    profile=read(output/'PROFILE.json')
    if kind=='finite':assert profile['exact_supported_battery_pass'] is True and profile['longer_distinction']['rate']==1
    elif kind=='prefix':
        assert len(profile['attempts'])==1 and profile['attempts'][0]['realized'] is False
        assert profile['domains']['known-domain']['contrasts']['altered']['contrast'] is None
    elif kind=='supplied':
        assert all(v['estimate']['mean']==0 for v in profile['comparisons']['all'].values())
    else:
        for condition in profile['domains']['known-domain']['conditions'].values():
            assert condition['stop_rate']['raw_rate']==1
            assert all(h['reached_action_horizon']['raw_rate']==0 for h in condition['horizons'].values())
    write(tmp_path/'STATUS.json',{'jobs':{'diagnostic':{'status':'COMPLETE'}}})
    assert subject.queue_audits(plan,tmp_path,{'diagnostic':job})['jobs']=={'diagnostic':result}


@pytest.mark.parametrize('fault',['profile','profile_boolean','profile_scope','identity','source','input_hash',
    'cell','execution_boolean','admission','missing_output','extra_output','unlisted_output','writer_payload',
    'dispatcher','produce','original_commit','plan','case_scope','case_hash','unit_key','unit_boolean','unit_row',
    'missing_unit','package','read_only'])
def test_rehashed_substitutions_refuse(tmp_path,monkeypatch,fault):
    output,job,plan,done,seal=saved(tmp_path,monkeypatch)
    if fault.startswith('profile'):
        value=read(output/'PROFILE.json')
        if fault=='profile_scope':value['scientific_admission']=True
        elif fault=='profile_boolean':value['comparisons']['all']['direct_vs_uniform']['estimate']['mean']=False
        else:value['comparisons']['all']['direct_vs_uniform']['estimate']['mean']=1
        write(output/'PROFILE.json',value)
    elif fault in ('identity','source','input_hash'):
        value=read(output/'IDENTITY.json')
        if fault=='identity':value['scope']='scientific'
        elif fault=='source':value['source']['sha256']=digest('other source')
        else:value['inputs']['supplied_kernel']=digest('substitute complete')
        write(output/'IDENTITY.json',value)
    elif fault in ('cell','execution_boolean','admission'):
        done[{'cell':'cell_identity','execution_boolean':'execution_complete','admission':'scientific_admission'}[fault]]=1
    elif fault=='missing_output':(output/'PROFILE.json').unlink()
    elif fault=='extra_output':write(output/'EXTRA.json',{})
    elif fault=='dispatcher':job['module']='runners.stage9.neural_operations'
    elif fault=='produce':job['produces']=str(tmp_path/'other/COMPLETE.json')
    elif fault=='original_commit':
        def refuse(*a):raise ValueError('missing original commit')
        monkeypatch.setattr(subject,'verify_committed',refuse)
    elif fault=='plan':write(tmp_path/'PLAN.json',{'operation':'supplied','inputs':{}})
    elif fault in ('case_scope','case_hash','package','unit_key','unit_boolean','unit_row','missing_unit'):
        path=tmp_path/'inputs/supplied_kernel'
        if fault=='package':write(path/'PACKAGE.json',{'reader':'substituted package'})
        elif fault in ('case_scope','case_hash'):
            value=read(path/'IDENTITY.json');value['scope' if fault=='case_scope' else 'cases_complete_sha256']='changed'
            write(path/'IDENTITY.json',value)
        else:
            unit=next((path/'units').glob('*.json'));value=read(unit)
            if fault=='missing_unit':unit.unlink()
            else:
                if fault=='unit_key':value['key']='different'
                elif fault=='unit_boolean':value['complete']=1
                else:value['row']['result']['calls']['explicit']['accepted']=1
                write(unit,value)
        identity=read(path/'IDENTITY.json')
        write(path/'COMPLETE.json',{'identity_sha256':digest(identity),'cell_identity':identity['cell_identity'],
            'outputs':closure([path/'IDENTITY.json',path/'PACKAGE.json',path/'units'])})
    elif fault=='read_only':
        original=analysis.summarize
        def mutate(*a):
            result=original(*a);write(tmp_path/'cases/UNEXPECTED.json',{});return result
        monkeypatch.setattr(analysis,'summarize',mutate)
    seal()
    if fault=='unlisted_output':write(output/'UNLISTED.json',{})
    if fault=='writer_payload':(output/'WRITER.lock').write_bytes(b'unexpected payload')
    with pytest.raises((ValueError,KeyError,FileNotFoundError)):
        subject.inspect_completed(job,plan,tmp_path)


def test_failed_unrun_and_active_jobs_never_open_diagnostic_inputs(tmp_path,monkeypatch):
    monkeypatch.setattr(subject,'inspect_completed',lambda *a:pytest.fail('noncompleted inputs opened'))
    checked=[];monkeypatch.setattr(subject,'verify_disposition',lambda q,j,s:checked.append(s['status']))
    prior={k:{'module':subject.MODULE} for k in ('failed','blocked')}
    states={k:{'status':v,'reason':'original nonexecution','disposition_sha256':digest(v)}
            for k,v in [('failed','FAILED'),('blocked','NOT_RUN')]}
    write(tmp_path/'STATUS.json',{'jobs':states})
    assert subject.queue_audits({},tmp_path,prior)['jobs']==states and checked==['FAILED','NOT_RUN']
    states['failed']['status']='RUNNING';write(tmp_path/'STATUS.json',{'jobs':states})
    with pytest.raises(ValueError,match='terminal'):subject.queue_audits({},tmp_path,prior)
