import copy
from pathlib import Path
import pytest

from runners.stage9.common import read
from runners.stage9.proposal_jobs import forecast_unit
from runners.stage9.launch import handler_operation
from tests.test_stage9_purpose_reader import bundle


def test_actual_crossed_pool_grid_keeps_oracle_outside_readers(tmp_path):
    data=bundle();query=data['evidence'];query['earlier']=(query['earlier']*4)[:7]
    oracle={a:float(i==1) for i,a in enumerate(query['support'])}
    case={'unit':'fixture','role':'pilot','target':query['support'][1],'oracle':oracle,
          'realized':True,'views':{'process_record':query},'private_factors':{'domain':'text','purpose':'first'}}
    package={'library':{k:data[k] for k in ('candidates','prior','shared_groups')},
        'models':{'process_record':{'fixture':{'version':'s9-conditional-choice-v1','weights':{},
                                            'individual':False,'uniform_mixture':.01}}},
        'types':{'process_record':{t:1/8 for t in data['candidates']['a']['purpose']}}}
    result=forecast_unit(case,package,data['purpose_groups'],tmp_path/'grid')
    assert len(result['costs'])==10 and all(c['accepted'] for c in result['costs'])
    cell=result['rows']['process_record|dose7']
    assert len(cell['predictions'])==12 and all(cell['validity'].values())
    for name in ('narrow','expanded','catalogue'):
        assert cell['quality'][name+'|stateful']['pool_sha256']==cell['quality'][name+'|bag']['pool_sha256']
    assert cell['predictions']['supplied_state_law_ceiling']==oracle
    for cost in result['costs']:
        visible=read(Path(cost['capsule'])/'evidence.json')
        assert not {'oracle','truth','private_factors'}.intersection(visible)
    assert forecast_unit(case,package,data['purpose_groups'],tmp_path/'grid',resume_only=True)==result
    changed=copy.deepcopy(case);changed['oracle']={a:1/len(oracle) for a in oracle}
    updated=forecast_unit(changed,package,data['purpose_groups'],tmp_path/'grid',resume_only=True)
    assert updated['costs']==result['costs']
    assert {k:v for k,v in updated['rows']['process_record|dose7']['predictions'].items() if k!='supplied_state_law_ceiling'}=={
        k:v for k,v in cell['predictions'].items() if k!='supplied_state_law_ceiling'}


def test_launch_distinguishes_purpose_and_proposal_consumers():
    a={'module':'runners.stage9.purpose_jobs','arguments':[]}
    b={'module':a['module'],'arguments':['--consumer','proposal']}
    assert handler_operation(a)!=handler_operation(b)
    for args in (['--consumer'],['--consumer','bad'],['--consumer','purpose','--consumer','proposal']):
        with pytest.raises(ValueError):handler_operation({'module':a['module'],'arguments':args})
