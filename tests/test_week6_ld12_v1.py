"""Constructed source, model and complete-person replay checks for LD1 and LD2."""
import numpy as np
import pytest

from runners.drive.cards import week6_ld12_common_v1 as core


def test_reference_fits_match_literal_whole_people():
    rng = np.random.default_rng(548)
    people = np.repeat(np.arange(24), 14)
    z = rng.normal(size=(len(people), 2))
    y = rng.random(len(people)) < .5
    weights = rng.integers(0, 4, 24)
    w = weights[people]
    main, _, _ = core.arithmetic(False)
    a = main(z, people, w)[0]
    b = core.reference_within(z, people, w)[0]
    np.testing.assert_allclose(a, b, atol=1e-12)
    design = np.column_stack((np.ones(len(w)), a))
    repeats = np.repeat(np.arange(len(w)), w)
    ones = np.ones(len(repeats))
    actual = core.arithmetic(False)[1](design, y, w)
    np.testing.assert_allclose(actual, core.reference_logit(design, y, w), atol=1e-8)
    np.testing.assert_allclose(actual, core.reference_logit(design[repeats], y[repeats], ones), atol=1e-8)
    np.testing.assert_allclose(core.arithmetic(False)[2](design, y, w),
                               core.reference_linear(design, y, w), atol=1e-10)


@pytest.mark.parametrize("bad", [[1], [-1, 3], [0, 0], [1, .5], [1, np.nan]])
def test_draw_requires_person_multiplicities(bad):
    with pytest.raises(ValueError):
        core.multiplicities(2, bad)


def test_reference_declares_zero_weight_and_empty_panels():
    with pytest.raises(core.fits.InvalidFit):
        core.reference_within(np.empty(0), np.empty(0), np.empty(0))
    with pytest.raises(core.fits.InvalidFit):
        core.reference_within(np.ones(3), np.arange(3), np.zeros(3))
