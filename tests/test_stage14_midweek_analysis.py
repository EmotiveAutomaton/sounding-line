import pytest
from runners.stage14_midweek.analyze_baselines import interval,crossed

def test_null_and_known_constant_gain_keep_correct_units():
    assert interval([0,0,0])=={'mean':0.,'interval':[0.,0.]}
    assert interval([.2,.2,.2])['interval']==pytest.approx([.2,.2])
    # Unequal event counts cannot change a constant writer/prompt gain.
    rows=[dict(writer='one',prompt='a')]*8+[dict(writer='two',prompt='a'),dict(writer='two',prompt='b')]
    assert crossed(rows,[.2]*10)==pytest.approx([.2,.2])
    with pytest.raises(ValueError):interval([float('nan')])
