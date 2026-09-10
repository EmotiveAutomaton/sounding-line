import copy
from pathlib import Path
import pytest

from runners.stage9.common import read
from runners.stage9.purpose_jobs import forecast_unit
from tests.test_stage9_purpose_reader import bundle


def test_full_forecast_grid_keeps_privileged_information_separate_and_reconstructs_calls(tmp_path):
    data=bundle();query=data['evidence'];query['earlier']=query['earlier']*4
    query['earlier']=query['earlier'][:7]
    case={'unit':'fixture','role':'pilot','target':query['support'][1],
          'realized':True,'views':{'process_record':query},'private_factors':{'domain':'text','purpose':'first'}}
    package={'library':{k:data[k] for k in ('candidates','prior','shared_groups')},
        'models':{'process_record':{'fixture':{'version':'s9-conditional-choice-v1','weights':{},
                                            'individual':False,'uniform_mixture':.01}}},
        'types':{'process_record':{t:1/8 for t in data['candidates']['a']['purpose']}}}
    path=tmp_path/'grid';result=forecast_unit(case,package,data['purpose_groups'],path)
    assert len(result['costs'])==7 and all(c['accepted'] for c in result['costs'])
    assert set(result['rows'])=={'process_record|dose0','process_record|dose7'}
    for row in result['rows'].values():
        assert len(row['predictions'])==10 and all(row['validity'].values())
        hashes=row['model_input_sha256']
        assert hashes['inferred_distribution']==hashes['single_purpose']==hashes['purpose_agnostic']
        assert hashes['supplied_true']!=hashes['supplied_false']!=hashes['inferred_distribution']
    for cost in result['costs']:
        supplied=read(Path(cost['capsule'])/'evidence.json')
        if cost['operation'] in ('ordinary','baselines'):
            assert 'supplied_purpose' not in supplied and 'private_factors' not in supplied
    assert forecast_unit(case,package,data['purpose_groups'],path,resume_only=True)==result
    changed=copy.deepcopy(case);changed['private_factors']['purpose']='second'
    with pytest.raises(ValueError,match='inputs changed'):
        forecast_unit(changed,package,data['purpose_groups'],path,resume_only=True)
