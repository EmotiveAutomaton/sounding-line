import numpy as np
import pytest
from runners.drive.cards import week5_md4_ic as ic


def test_separate_condition_bootstrap_preserves_person_mean():
    rows=[dict(condition=c,slope=i*.001) for c in ic.primary.CONDITIONS for i in range(24)]
    point,bank,counts=ic.operators(rows,2000);y=np.array([r['slope'] for r in rows])
    assert counts==dict.fromkeys(ic.primary.CONDITIONS,24)
    assert np.allclose(point@y,[.0115]*3)
    assert np.allclose(bank.sum(axis=2),1)
    with pytest.raises(ValueError):ic.operators(rows[:10],2000)
