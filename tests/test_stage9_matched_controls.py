import copy
import json
import pytest
from runners.stage9.matched_controls import choose,construct,validate
from runners.stage9.series_cases import COHORTS,construct_attempt,dose_view
from runners.stage9.recipes import parameter_partition


@pytest.mark.parametrize('role',['pilot','development','discovery'])
def test_actual_other_maker_preserves_public_conditions_and_split(role):
    attempts=[construct_attempt(key='matched-'+role+str(i),cohort=COHORTS[i],role=role,dose=3) for i in range(4)]
    case=next(c for c in attempts if c['realized']);earlier=case['source_worlds'][1:]
    result=construct(earlier,role,'independent-control')
    assert validate(earlier,result,role,'independent-control')
    assert validate(earlier,json.loads(json.dumps(result)),role,'independent-control')
    assert result['plan']['original']!=result['plan']['alternative']
    for i,new in enumerate(result['worlds']):
        assert parameter_partition(new)==('training' if role=='pilot' else role)
        assert new['doc']==earlier[i]['doc'] and new['state']['external_context']==earlier[i]['state']['external_context']
    query=dose_view(case,3,replacement=result['views']['artifact'])
    assert query['current']==case['views']['artifact']['current'] and query['support']==case['views']['artifact']['support']
    changed=copy.deepcopy(earlier)
    for w in changed:w['trajectory']={'steps':[],'stop_kind':'hazard'}
    # Even the earlier realized outcomes cannot drive selection of the maker.
    assert choose(changed,role,'independent-control')==result['plan']
    altered=copy.deepcopy(result);altered['views']['artifact'][0]['context']['deadline']='changed'
    with pytest.raises(ValueError):validate(earlier,altered,role,'independent-control')
    with pytest.raises(ValueError):validate(earlier,result,role,'different-namespace')


def test_saved_control_replay_from_cold_interpreter(tmp_path):
    import subprocess
    import sys
    from runners.stage9.common import REPO,write
    case=next(c for i in range(4) if (c:=construct_attempt(key='cold-matching-'+str(i),cohort=COHORTS[i],role='pilot',dose=3))['realized'])
    earlier=case['source_worlds'][1:];result=construct(earlier,'pilot','cold-control')
    path=tmp_path/'saved.json';write(path,{'earlier':earlier,'result':result})
    code='from runners.stage9.common import read; from runners.stage9.matched_controls import validate; import sys; r=read(sys.argv[1]); validate(r["earlier"],r["result"],"pilot","cold-control")'
    completed=subprocess.run([sys.executable,'-B','-c',code,str(path)],cwd=REPO,capture_output=True,text=True)
    assert completed.returncode==0,completed.stderr
    changed=json.loads(json.dumps(result))
    changed['worlds'][0]['trajectory']['changes'][0][0]+=1
    from runners.stage9.series_cases import content_identity
    changed['sources'][0]=content_identity(changed['worlds'][0])
    with pytest.raises(ValueError,match='do not reproduce'):validate(earlier,changed,'pilot','cold-control')
