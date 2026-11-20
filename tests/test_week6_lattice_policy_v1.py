"""Fixed constructed CPU-accounting cases under the native Gear 2 witness."""
import numpy
import pytest
from runners.drive.cards.week6_lattice_policy_fixture_v1 import EXPECTED, run_cases


@pytest.fixture(scope='session')
def results(tmp_path_factory):
    measured = run_cases(tmp_path_factory.mktemp('fabricated-ledger'))
    assert sorted(measured) == sorted(EXPECTED)
    return measured


@pytest.mark.parametrize('case', EXPECTED)
def test_prospective_allowance(case, results):
    assert case in results
