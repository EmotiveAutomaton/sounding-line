import copy

import pytest

from runners.stage9.construction import Replay, POP
from runners.stage9.recipes import sampled_world
from runners.stage9.kernel import probabilities, mixture
from runners.stage9.kernel_preparation import supplied_program


def test_declared_numeric_program_matches_constructor_without_world_access():
    for domain in POP.DOMAINS:
        for i in range(20):
            world = sampled_world(POP.pop_lid(i, domain, 9950000), 'both')
            for cut in (0, min(4, len(world['trajectory']['steps']))):
                replay = Replay(world, world['trajectory']['steps'][:cut])
                program = supplied_program(replay)
                actual, expected = probabilities(program), replay.probabilities()
                assert set(actual) == set(expected)
                assert max(abs(actual[k]-expected[k]) for k in actual) < 1e-12
                assert 'lid' not in program and 'names' not in program


def test_missing_factor_and_non_normalized_mixture_fail():
    world = sampled_world(POP.pop_lid(1, 'essay', 9950000))
    program = supplied_program(Replay(world))
    missing = copy.deepcopy(program)
    del missing['belief']
    with pytest.raises(ValueError):
        probabilities(missing)
    with pytest.raises(ValueError):
        mixture([program], [.9])
    assert mixture([program, program], [.3, .7]) == pytest.approx(probabilities(program))
