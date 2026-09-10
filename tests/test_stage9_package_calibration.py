import copy
import pytest
from runners.stage9 import package_calibration as calibration
from runners.stage9.common import digest


def fixture():
    inputs={'known':{'prefix':'x','options':{'a':'one','b':'two'}}}
    rows={'-'.join(map(str,v)):{'known':{'a':.5,'b':.5}} for v in calibration.VARIANTS}
    return inputs,rows


def test_precision_known_answers_original_amended_and_failed():
    inputs,rows=fixture()
    result=calibration.compare(rows,inputs)
    assert result['maximum_required_distance']==0 and result['old_1e_minus6_pass']
    rows['float16-cuda-4']['known']={'a':.505,'b':.495}
    result=calibration.compare(rows,inputs)
    assert result['maximum_required_distance']==pytest.approx(.005)
    assert not result['old_1e_minus6_pass'] and result['amended_0_01_pass']
    rows['float16-cuda-1']['known']={'a':.52,'b':.48}
    assert not calibration.compare(rows,inputs)['instrument_accepted']


def test_incomplete_support_variants_and_nonfinite_refuse():
    inputs,rows=fixture()
    for change in ('variant','case','support','nonfinite'):
        x=copy.deepcopy(rows)
        if change=='variant':del x['float32-cpu-4']
        elif change=='case':x['float16-cuda-4']={}
        elif change=='support':x['float16-cuda-4']['known']={'a':1.}
        else:x['float16-cuda-4']['known']={'a':float('nan'),'b':.5}
        with pytest.raises(ValueError):calibration.compare(x,inputs)
    with pytest.raises(ValueError):calibration.compare({k:{} for k in rows},{})


def test_package_matching_retains_every_score_dependency():
    p={k:'fixture' for k in ('model','revision','adapter_sha256','scorer_sha256','renderer',
        'attention_implementation','long_context_batch_rule','torch','transformers','peft')}
    p.update(base_files={'tokenizer.json':'known-tokenizer','model.safetensors':'known-weights'},
        precision='float16',device='cuda',batch_size=4,max_context=4096,max_support=128,
        max_new_tokens=32,generation={'mode':'greedy'},scorer_sources={'sha256':'fixture'})
    p['base_files_sha256']=digest(p['base_files'])
    calibration.compatible(p,p)
    q=copy.deepcopy(p);q.update(max_new_tokens=336,generation={'mode':'sampled'})
    calibration.compatible(p,q)  # Only score semantics; no generation precision license.
    for key in set(p)-{'max_new_tokens','generation'}:
        q=copy.deepcopy(p);q[key]='different'
        with pytest.raises((ValueError,TypeError)):calibration.compatible(p,q)
    q=copy.deepcopy(p);del q['torch']
    with pytest.raises(ValueError):calibration.compatible(p,q)
