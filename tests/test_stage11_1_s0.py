from collections import Counter
from runners.stage11_1.diagnose import capped_training
from runners.stage11_1.common import contract


def test_training_cap_is_three_and_outcome_blind():
    rows=[dict(key=f'{w}-{i}',writer=w,truth='accept') for w in 'abcde' for i in range(21)]
    selected=capped_training(rows)
    assert len(selected)==15 and set(Counter(r['writer'] for r in selected).values())=={3}
    swapped=[dict(r,truth='dismiss') for r in reversed(rows)]
    assert [r['key'] for r in capped_training(swapped)]==[r['key'] for r in selected]


def test_continuation_contract_does_not_reset_on_resume(tmp_path):
    first=contract(tmp_path)
    assert contract(tmp_path)==first and first['gear']==1
    assert sum(first['branch_attempts'].values())==first['maximum_attempts']==6400
    assert first['checkpoint']=='2026-09-20T15:00:00+00:00'
