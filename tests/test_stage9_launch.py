import copy
import pytest
from runners.stage9.common import digest,write,file_hash
from runners.stage9.launch import verify_certificate,verify_forecast,checked,validate,REQUIRED


def test_bare_acceptance_or_empty_evidence_cannot_launch(monkeypatch):
    import runners.stage9.queue as queue
    monkeypatch.setattr(queue,'validate_manifest',lambda p: True)
    monkeypatch.setattr(queue,'verify_sources',lambda s: None)
    plan={'kind':'science','sources':{},'jobs':[]}
    with pytest.raises(ValueError,match='nonvacuous'):
        verify_certificate(plan,{'accepted':True,'manifest_sha256':digest(plan),'evidence':[]})
    with pytest.raises(ValueError,match='evidence set'):
        verify_certificate(plan,{'version':2,'accepted':True,'manifest_sha256':digest(plan),'checked_evidence':{}})
    assert len(REQUIRED)==9


def test_evidence_hash_and_workspace_boundary_are_actual_checks(tmp_path,monkeypatch):
    import runners.stage9.launch as launch
    monkeypatch.setattr(launch,'REPO',tmp_path)
    path=tmp_path/'receipt.json';write(path,{'complete':True})
    pointer={'path':'receipt.json','sha256':file_hash(path)}
    assert checked(pointer)=={'complete':True}
    write(path,{'complete':False})
    with pytest.raises(ValueError,match='changed'):checked(pointer)
    with pytest.raises(ValueError,match='real repository file'):
        checked({'path':'../outside.json','sha256':'unused'})


def test_measured_forecast_enforces_real_rate_costs_and_serial_runtime(tmp_path,monkeypatch):
    import runners.stage9.launch as launch
    monkeypatch.setattr(launch,'REPO',tmp_path)
    path=tmp_path/'pilot.json';write(path,{'seconds':60.})
    row={'measured_seconds':60.,'measured_units':8,'planned_units':600,'multiplier':2.,
         'overhead_seconds':100.,'forecast_seconds':9100.,'pilot':{'path':'pilot.json','sha256':file_hash(path)},
         'measured_field':['seconds']}
    forecast={'jobs':{'fit':row},'preparation_gpu_reserved_seconds':1000.,'scheduling':'serial',
              'remaining_wall_seconds':10000.,'forecast_at':0.,'initial_queue_seconds':9100.,
              'underfill_reason':'bounded guard fixture, not a scientific depth forecast'}
    plan={'jobs':[{'id':'fit','resource':'gpu','estimated_gpu_seconds':9100.}], 'horizon_epoch':11000.}
    verify_forecast(forecast,plan)
    for field,value in (('measured_seconds',59.),('forecast_seconds',9000.),('measured_units',0.)):
        changed=copy.deepcopy(forecast);changed['jobs']['fit'][field]=value
        with pytest.raises(ValueError):verify_forecast(changed,plan)
    with pytest.raises(ValueError,match='serial|concurrency'):
        verify_forecast(forecast|{'remaining_wall_seconds':9000.},plan)
    with pytest.raises(ValueError,match='envelope'):
        verify_forecast(forecast|{'preparation_gpu_reserved_seconds':92*3600.},plan)


def test_rehearsal_mapping_distinguishes_dispatcher_operations_and_families():
    from runners.stage9.launch import handler_operation
    def job(operation,family):
        return {'module':'runners.stage9.training_jobs','arguments':[operation,'--family',family]}
    signatures={handler_operation(job(op,f)) for op in ('fit','collect','pack') for f in ('qwen','smollm')}
    assert len(signatures)==6
    assert handler_operation(job('fit','qwen')|{'arguments':['fit','--family','qwen','--seed','9001']})==handler_operation(job('fit','qwen'))
    with pytest.raises(ValueError,match='duplicate'):
        handler_operation(job('fit','qwen')|{'arguments':['fit','--family','qwen','--family','smollm']})
    with pytest.raises(ValueError,match='operation'):
        handler_operation({'module':'runners.stage9.artifact_analysis','arguments':[]})


def test_neural_rehearsal_cannot_substitute_base_archive_or_fitted_package():
    from runners.stage9.launch import handler_operation
    job={'module':'runners.stage9.neural_operations','arguments':['--operation','offered','--family','qwen']}
    fitted=handler_operation(job)
    base=handler_operation(job|{'arguments':job['arguments']+['--package-kind','base']})
    archive=handler_operation(job|{'arguments':job['arguments']+['--package-kind','archive']})
    assert len({fitted,base,archive})==3


def test_generation_preparation_rehearsal_matches_actual_population():
    from runners.stage9.launch import handler_operation
    job={'module':'runners.stage9.generation_cases','arguments':['--population','original']}
    assert handler_operation(job)!=handler_operation(job|{'arguments':['--population','expanded']})
    with pytest.raises(ValueError,match='population'):handler_operation(job|{'arguments':[]})


def test_repair_rehearsal_matches_actual_fitting_inference_and_admission():
    from runners.stage9.launch import handler_operation
    signatures=set()
    for module,operations in (('repair_jobs',('fit','predict','select')),('repair_admission',('calibrate','evaluate'))):
        for operation in operations:signatures.add(handler_operation({'module':'runners.stage9.'+module,'arguments':[operation]}))
        with pytest.raises(ValueError,match='operation'):handler_operation({'module':'runners.stage9.'+module,'arguments':[]})
    assert len(signatures)==5


def test_human_rehearsals_preserve_operations_partitions_and_domains():
    from runners.stage9.launch import handler_operation
    signatures=set()
    for module,operations in (('revision_predictions',('fit','predict')),('revision_analysis',('select','evaluate')),
        ('broll_jobs',('prepare','fit','predict','select','evaluate'))):
        for operation in operations:
            for lane in (('development','evaluation') if operation=='predict' else (None,)):
                args=[operation]+(['--lane',lane] if lane else [])
                signatures.add(handler_operation({'module':'runners.stage9.'+module,'arguments':args}))
        with pytest.raises(ValueError):handler_operation({'module':'runners.stage9.'+module,'arguments':[]})
    assert len(signatures)==11
    domain={'module':'runners.stage9.iterater_cases','arguments':[]}
    domains={handler_operation(domain)}
    for study in ('within','leave-arxiv','leave-news','leave-wiki'):
        domains.add(handler_operation(domain|{'arguments':['--study',study]}))
    assert len(domains)==5
    with pytest.raises(ValueError):handler_operation(domain|{'arguments':['--study','unknown']})
    with pytest.raises(ValueError):handler_operation({'module':'runners.stage9.broll_jobs','arguments':['predict']})


def test_code_change_rehearsal_matches_each_compiled_operation_and_partition():
    from runners.stage9.launch import handler_operation
    module='runners.stage9.commit_jobs'
    operations=[['prepare'],['fit'],['predict','--lane','development'],['predict','--lane','evaluation'],['select'],['evaluate']]
    assert len({handler_operation({'module':module,'arguments':args}) for args in operations})==6
    for args in ([],['unknown'],['predict'],['predict','--lane','unknown']):
        with pytest.raises(ValueError):handler_operation({'module':module,'arguments':args})


def test_prospective_handler_rehearsal_preserves_dataset_and_operations():
    from runners.stage9.launch import handler_operation
    module='runners.stage9.record_jobs'
    arguments=[['prepare','--dataset','coauthor'],['fit'],['predict','--lane','development'],['predict','--lane','evaluation'],['select'],['evaluate']]
    assert len({handler_operation({'module':module,'arguments':a}) for a in arguments})==6
    for args in ([],['prepare'],['prepare','--dataset','unknown'],['predict']):
        with pytest.raises(ValueError):handler_operation({'module':module,'arguments':args})


def test_rehearsal_isolation_mapping_covers_each_actual_reviewed_package():
    from runners.stage9.closure_probe import RUNTIMES
    from runners.stage9.launch import handler_operation
    actual={'reader','baseline_matrix','revision','record','commit','broll',
            'repair','kernel','inference','mark','comparison'}
    assert set(RUNTIMES)==actual
    signatures={handler_operation({'module':'runners.stage9.closure_probe',
                                  'arguments':['--runtime',runtime]}) for runtime in actual}
    assert len(signatures)==11
    assert {row[1] for row in signatures}=={'probe-'+runtime for runtime in actual}


@pytest.mark.parametrize('arguments',[[],['--runtime'],['--runtime','unreviewed'],
                                   ['--runtime','reader','--runtime','revision']])
def test_rehearsal_rejects_missing_unknown_or_ambiguous_isolation_package(arguments):
    from runners.stage9.launch import handler_operation
    with pytest.raises(ValueError):
        handler_operation({'module':'runners.stage9.closure_probe','arguments':arguments})
