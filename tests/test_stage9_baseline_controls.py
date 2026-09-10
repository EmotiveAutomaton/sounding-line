from pathlib import Path
from runners.stage9.baseline_controls import unit_result
from runners.stage9.baseline_matrix_runtime import execute
from runners.stage9.common import read
from runners.stage9.matched_controls import construct
from tests.test_stage9_artifact_comparisons import actual_case
from tests.test_stage9_comparison_runtime import bundle


def test_actual_controlled_capsules_preserve_task_support_and_duplicate_identity(tmp_path):
    case=actual_case();control=construct(case['source_worlds'][1:],'pilot','ordinary-control-fixture')
    data=bundle();models={'models':{v:{'model':data['population']} for v in ('artifact','process_record')},
        'types':{v:data['population_types'] for v in ('artifact','process_record')}}
    calls={}
    def call(bundle,key):
        result=execute(bundle,root=tmp_path/key);assert result['accepted']
        assert read(Path(result['capsule'])/'evidence.json')==bundle
        calls[key]=bundle;return result
    row=unit_result(case,control,models,call,(0,1))
    assert len(calls)==4 and len(row['costs'])==4 and len(row['rows'])==12
    for view in ('artifact','process_record'):
        same,other=calls['same-'+view]['evidences'],calls['other-'+view]['evidences']
        assert same['dose0']==other['dose0']
        assert same['dose1']['current']==other['dose1']['current']
        assert same['dose1']['support']==other['dose1']['support']
        assert other['dose1']['earlier']==control['views'][view]
        for condition in ('','other-'):
            one=row['rows'][view+'|'+condition+'dose1'];repeated=row['rows'][view+'|'+condition+'repeat7']
            assert one['predictions']==repeated['predictions']
            assert one['unique_prior_works']==repeated['unique_prior_works']==1
    assert row['truth']==case['target']
