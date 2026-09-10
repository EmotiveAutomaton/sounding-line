import pytest
from runners.stage9.broll import selections,partition,literal


def test_highlights_are_sets_of_word_opportunities_not_normalized_choices():
    chunks=selections("{'4': {'1': 'blue,', '0': 'Deep'}, '1': {'0': 'sea'}}")
    assert [r['highlight_index'] for r in chunks]==[1,4]
    assert chunks[1]['words']==['deep','blue']
    assert selections('{}')==[]
    with pytest.raises(ValueError):selections("{'0':['not a positional dictionary']}")
    with pytest.raises((ValueError,SyntaxError)):literal("__import__('os').system('echo invalid')",dict)


def test_pilot_exposure_cannot_be_resealed_and_partitions_are_stable():
    keys=[str(i) for i in range(102)]
    result=partition(keys,['0','1'])
    assert result['0']==result['1']=='pilot'
    assert sum(v=='reserve' for v in result.values())==30
    assert partition(list(reversed(keys)),['1','0'])==result


def test_individual_selection_model_recovers_known_preference_and_null():
    from runners.stage9.broll_baseline import learned_rates,probabilities
    from runners.stage9.scoring import brier
    scripts={'a':{'support':['noun','adj'],'pos':{'noun':'noun','adj':'adj'}},
             'b':{'support':['newnoun','newadj'],'pos':{'newnoun':'noun','newadj':'adj'}}}
    own={'script_key':'a','goal':'informative','labels':[1,0]}
    wrong=own|{'labels':[0,1]}
    population=learned_rates([own,wrong],scripts)
    prior=probabilities(scripts['b'],'informative',population)
    personal=probabilities(scripts['b'],'informative',population,[own]*20,scripts)
    reversed_=probabilities(scripts['b'],'informative',population,[wrong]*20,scripts)
    assert brier(personal,[1,0]) < brier(prior,[1,0]) < brier(reversed_,[1,0])
    assert probabilities(scripts['b'],'informative',population,[],scripts)==prior
    assert personal==probabilities(scripts['b'],'informative',population,[own]*20,scripts)
