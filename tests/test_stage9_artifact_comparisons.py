import copy
import pytest
from runners.stage9.artifact_comparisons import validate_cases,forecast_unit,contrast_rows
from runners.stage9.comparison_analysis import complete_rows
from runners.stage9.series_cases import COHORTS,construct_attempt
from tests.test_stage9_comparison_runtime import bundle


def actual_case():
    for i in range(20):
        case=construct_attempt(key='consumer-fixture-'+str(i),cohort=COHORTS[0],role='pilot',dose=1)
        if case['realized']:return case
    raise AssertionError('fixture did not realize its actual prospective boundary')


def test_actual_sources_private_factors_and_targets_validate_independently():
    case=actual_case();assert validate_cases([case],'pilot')
    changed=copy.deepcopy(case);changed['target']='invented'
    with pytest.raises(ValueError):validate_cases([changed],'pilot')
    changed=copy.deepcopy(case);changed['private_factors']['purpose']='invented'
    with pytest.raises(ValueError):validate_cases([changed],'pilot')
    with pytest.raises(ValueError):validate_cases([case,case],'pilot')
    with pytest.raises(ValueError):validate_cases([case],'discovery')


def test_saved_world_validation_in_a_fresh_interpreter(tmp_path):
    import subprocess
    import sys
    from runners.stage9.common import REPO,write
    path=tmp_path/'cases.json';write(path,[actual_case()])
    code='from runners.stage9.common import read; from runners.stage9.artifact_comparisons import validate_cases; import sys; validate_cases(read(sys.argv[1]), "pilot")'
    result=subprocess.run([sys.executable,'-B','-c',code,str(path)],cwd=REPO,capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_real_program_budget_failure_preserves_independent_baselines(tmp_path):
    case=actual_case();data=bundle()
    package={'models':{v:{'model':data['population']} for v in ('artifact','process_record')},
        'types':{v:data['population_types'] for v in ('artifact','process_record')},
        'library':{k:data[k] for k in ('candidates','prior','shared_groups')}}
    row=forecast_unit(case,package,tmp_path/'unit',doses=(0,1),budget=1)
    assert len(row['rows'])==6
    for cell in row['rows'].values():
        assert cell['validity']['model|population']
        assert not cell['validity']['program_mixture']
        assert 'program_mixture' not in cell['predictions']
    projected=contrast_rows([row],'artifact|dose1',['model|population','model|cheap-8.0'])
    assert complete_rows(projected,[case['unit']],['model|population','model|cheap-8.0'])
    bad=contrast_rows([row],'artifact|dose1',['model|population','program_mixture'])
    with pytest.raises(ValueError):complete_rows(bad,[case['unit']],['model|population','program_mixture'])
    # The same immutable calls can be audited and adopted; no new capsule is run.
    assert forecast_unit(case,package,tmp_path/'unit',doses=(0,1),budget=1)==row
    private_keys={'source_worlds','private_factors','oracle','target','role','unit'}
    from runners.stage9.common import read
    for cost in row['costs']:
        from pathlib import Path
        visible=read(Path(cost['capsule'])/'evidence.json')
        assert not private_keys & set(visible)


def test_matched_control_is_actually_consumed_and_resume_requires_its_calls(tmp_path):
    from runners.stage9.matched_controls import construct
    from runners.stage9.common import digest,read
    from pathlib import Path
    case=actual_case();data=bundle()
    package={'models':{v:{'model':data['population']} for v in ('artifact','process_record')},
        'types':{v:data['population_types'] for v in ('artifact','process_record')},
        'library':{k:data[k] for k in ('candidates','prior','shared_groups')}}
    control=construct(case['source_worlds'][1:],'pilot','consumer-control')
    root=tmp_path/'unit';row=forecast_unit(case,package,root,doses=(0,1),control=control,budget=1)
    assert len(row['rows'])==12 and len(row['costs'])==10
    assert row['control_sha256']==digest(control)
    for cost in row['costs']:
        queries=read(Path(cost['capsule'])/'evidence.json')['evidences']
        expected=case['views'][cost['view']]['earlier'] if cost['context_condition']=='same' else control['views'][cost['view']]
        assert queries['dose1']['earlier']==expected[:1]
        assert queries['dose1']['current']==case['views'][cost['view']]['current']
    for view in ('artifact','process_record'):
        for name in ('dose0','other-dose0'):
            assert row['rows'][view+'|'+name]['validity']['model|population']
        assert row['rows'][view+'|dose0']['predictions']==row['rows'][view+'|other-dose0']['predictions']
    assert forecast_unit(case,package,root,doses=(0,1),control=control,budget=1,resume_only=True)==row
    (root/'other/artifact-baselines.json').unlink()
    with pytest.raises(ValueError,match='missing an immutable'):
        forecast_unit(case,package,root,doses=(0,1),control=control,budget=1,resume_only=True)


def test_record_only_control_executes_no_artifact_capsules_and_retains_failed_routes(tmp_path):
    from runners.stage9.matched_controls import construct
    from runners.stage9.common import read,closure
    from pathlib import Path
    case=actual_case();data=bundle()
    package={'models':{v:{'model':data['population']} for v in ('artifact','process_record')},
        'types':{v:data['population_types'] for v in ('artifact','process_record')},
        'library':{k:data[k] for k in ('candidates','prior','shared_groups')}}
    control=construct(case['source_worlds'][1:],'pilot','record-only-control')
    root=tmp_path/'record-only'
    row=forecast_unit(case,package,root,doses=(0,1),control=control,budget=1,views=('process_record',))
    assert len(row['rows'])==6 and len(row['costs'])==4
    assert all(key.startswith('process_record|') for key in row['rows'])
    for cell in row['rows'].values():
        assert cell['validity']['model|population']
        assert not cell['validity']['program_mixture'] and 'program_mixture' not in cell['predictions']
    for cost in row['costs']:
        assert cost['view']=='process_record'
        for query in read(Path(cost['capsule'])/'evidence.json')['evidences'].values():
            assert query['view']=='process_record'
    assert not list(root.glob('**/artifact-*.json'))
    before=closure([root])
    assert forecast_unit(case,package,root,doses=(0,1),control=control,budget=1,views=['process_record'],resume_only=True)==row
    assert closure([root])==before


@pytest.mark.parametrize('views',[(),('unknown',),('artifact','artifact'),'process_record'])
def test_invalid_view_assignment_refuses_before_execution(tmp_path,views):
    with pytest.raises(ValueError,match='evidence views'):
        forecast_unit({}, {}, tmp_path/'unused',views=views)
    assert not (tmp_path/'unused').exists()


def test_launch_matching_distinguishes_record_only_from_both_view_rehearsal():
    from runners.stage9.launch import handler_operation
    def job(args):return {'module':'runners.stage9.artifact_comparisons','arguments':args}
    both=handler_operation(job([]));record=handler_operation(job(['--views','process_record','--role','pilot']))
    assert both!=record
    assert handler_operation(job(['--views','process_record','artifact']))==both
    with pytest.raises(ValueError):handler_operation(job(['--views']))
    with pytest.raises(ValueError):handler_operation(job(['--views','artifact','--views','process_record']))
