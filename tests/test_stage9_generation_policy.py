"""The original sampler inherits base top-k and EOS instead of replacing them."""
import pytest
from runners.stage9.generation_policy import LEGACY, GREEDY, policy, overrides


def test_legacy_keeps_multitoken_eos_and_top_k():
    inherited = {'top_k': 20, 'eos_token_id': [3, 9], 'do_sample': False, 'top_p': .8}
    resolved = policy(LEGACY, inherited, 3, 3)
    assert resolved['effective']['eos_token_id'] == [3, 9]
    assert resolved['effective']['top_k'] == 20
    assert resolved['effective']['top_p'] == 1.
    assert resolved['effective']['do_sample'] is True
    assert 'eos_token_id' not in resolved['overrides']
    assert inherited['top_p'] == .8
    assert policy(GREEDY, inherited, 3, 3)['effective']['eos_token_id'] == 3


def test_unregistered_sampling_overrides_fail():
    with pytest.raises(ValueError):
        overrides({'do_sample': True, 'temperature': .7})
