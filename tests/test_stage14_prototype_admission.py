import numpy as np
import pytest
from runners.stage14_midweek.prototype_admission import (
    ACTIONS, fixtures, mapping, probabilities, proper, evaluate,
)


def record(case, answer=None):
    answer=case['truth'] if answer is None else answer
    return dict(id=case['id'],rotations=[dict(order=mapping(j),logits=[
        8. if action==ACTIONS[answer] else 0. for action in mapping(j)]) for j in range(4)])


def noise():
    return [dict(order=mapping(j),logits=[4.,0.,-2.,1.]) for j in range(4)]


def test_score_known_answers_and_wrong_confidence():
    assert proper([1.,0.,0.,0.],0)==0
    assert proper([.25]*4,0)==.375
    assert proper([0.,1.,0.,0.],0)==1
    with pytest.raises(ValueError):proper([float('nan')]*4,0)


def test_mapping_invariance_and_letter_null():
    for j in range(4):
        p=probabilities([10. if a=='edit' else 0. for a in mapping(j)],mapping(j))
        assert np.argmax(p)==1
    mean=np.mean([probabilities(r['logits'],r['order']) for r in noise()],axis=0)
    assert np.allclose(mean,[.25]*4)


def test_admission_all_classes_and_rotation_roster():
    records=[record(c) for c in fixtures()]
    assert evaluate(records,noise())['admitted']
    records[0]['rotations'].pop()
    with pytest.raises(ValueError):evaluate(records,noise())


def test_class_collapse_refuses_even_at_overall_boundary():
    records=[record(c,0 if c['truth']==3 else None) for c in fixtures()]
    result=evaluate(records,noise())
    assert result['correct']==12 and not result['admitted']


def test_boundary_and_below_are_exhaustive():
    records=[record(c,(c['truth']+1)%4 if i%4==0 else None) for i,c in enumerate(fixtures())]
    assert evaluate(records,noise())['admitted']
    records[1]=record(fixtures()[1],1)
    assert not evaluate(records,noise())['admitted']


def test_reordered_incomplete_nonfinite_refuse():
    records=[record(c) for c in fixtures()]
    with pytest.raises(ValueError):evaluate(records[:-1],noise())
    with pytest.raises(ValueError):evaluate(list(reversed(records)),noise())
    records[0]['rotations'][0]['logits'][0]=float('inf')
    with pytest.raises(ValueError):evaluate(records,noise())
