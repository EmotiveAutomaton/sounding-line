"""SC2 matched-model controls use invented conversations and whole-dyad weights."""
import unittest
from unittest.mock import patch

import numpy as np

from runners.drive.sealed import week6_sc2_model_v1 as m


def invented(n=36):
    rng = np.random.default_rng(220044)
    pairs = []
    for i in range(n):
        people = ("a", f"b{i}")
        minutes = rng.uniform(12., 55.)
        share = rng.uniform(.15, .85)
        rows = []
        for j, portion in enumerate((share, 1. - share)):
            humor, noise, other = rng.normal(size=3)
            liking = 2.4 * humor + .06 * minutes - .5 * portion + .18 * noise
            status = -1.25 * humor + .14 * minutes + portion + .8 * other
            rows.append((people[j], people[1-j], humor, liking, status, minutes, portion))
        pairs.append((f"chat-{i:03}", tuple(rows)))
    return pairs


def both(data):
    return m.distribution(data), m.distribution(data, replay=True)


class TestMatchedHumor(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(m, "DRAWS", 40)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.data, self.n = m.matrix(invented())

    def test_planted_and_two_thousand_draws(self):
        with patch.object(m, "DRAWS", 2000):
            a, b = both(self.data)
            rows = m.aggregate(a, b, self.n, len(self.data))
        self.assertEqual(self.n, 37)
        self.assertEqual(a.shape, (2001, 3))
        self.assertTrue(np.allclose(a[:, 2], a[:, 0] - a[:, 1]))
        self.assertGreater(rows[0]["lower"], 0)
        self.assertLess(rows[1]["upper"], 0)
        self.assertGreater(rows[2]["lower"], m.BAR)
        self.assertTrue(all(r["valid_draws"] == 2000 for r in rows))

    def test_identical_and_swapped_outcomes(self):
        data = self.data.copy()
        data[..., 4] = data[..., 3]
        a, b = both(data)
        self.assertTrue(np.allclose(a, b))
        self.assertTrue(np.allclose(a[:, 2], 0))
        reverse = m.distribution(self.data[..., [0, 1, 2, 4, 3]])
        self.assertTrue(np.allclose(reverse[:, 2], -m.distribution(self.data)[:, 2]))

    def test_translation_rescaling_and_independent_refit(self):
        a = m.distribution(self.data)
        altered = self.data * [1.5, 60., 100., .125, 3.] + [113., 24., -18., 78., -103.]
        self.assertTrue(np.allclose(a, m.distribution(altered, replay=True)))

    def test_same_draw_multiplicities_for_reciprocal_rows(self):
        weights = list(m.indexed_weights(len(self.data)))
        self.assertTrue(all(w.sum() == len(self.data) for w in weights))
        a = m.distribution(self.data, replay=True)
        for i in (1, 12, 35):
            long = np.repeat(self.data, weights[i], axis=0).reshape(-1, 5)
            z = (long - long.mean(axis=0)) / long.std(axis=0)
            coef = np.linalg.lstsq(z[:, :3], z[:, 3:], rcond=m.RANK_RCOND)[0][0]
            np.testing.assert_allclose(a[i], [*coef, coef[0] - coef[1]])

    def test_constant_status_preserves_liking(self):
        data = self.data.copy()
        data[..., 4] = 19.7
        a, b = both(data)
        rows = m.aggregate(a, b, self.n, len(data))
        self.assertEqual(rows[1]["valid_draws"], 0)
        self.assertIsNone(rows[2]["estimate"])
        self.assertIsNotNone(rows[0]["lower"])

    def test_constant_only_in_one_resample(self):
        data = self.data.copy()
        data[..., 4] = 19.7
        data[0, 0, 4] = -1.
        rows = m.aggregate(*both(data), self.n, len(data))
        self.assertGreater(rows[1]["invalid_draws"], 0)
        self.assertGreater(rows[1]["valid_draws"], 0)
        self.assertIsNone(rows[1]["lower"])

    def test_rank_deficient_controls(self):
        data = self.data.copy()
        data[..., 1] = 3. * data[..., 2] + 16.
        a, b = both(data)
        self.assertTrue(np.isnan(a).all() and np.isnan(b).all())

    def test_unique_people_and_descriptive_small_roster(self):
        pairs = invented(12)
        data, n = m.matrix(pairs)
        rows = m.aggregate(*both(data), n, len(data))
        self.assertTrue(all(r["n"] == 13 and r["conversations"] == 12 and
                            r["sufficient_conversations"] == 0 for r in rows))
        with self.assertRaises(ValueError):
            m.matrix([*pairs, pairs[0]])
        left, right = pairs[0][1]
        with self.assertRaises(ValueError):
            m.matrix([("x", (left, ("new", *right[1:])))])

    def test_disagreement_and_truncation_refuse_return(self):
        a, b = both(self.data)
        b[7, 0] += .01
        with self.assertRaises(ValueError):
            m.aggregate(a, b, self.n, len(self.data))
        with self.assertRaises(ValueError):
            m.aggregate(a[:-1], a[:-1], self.n, len(self.data))


if __name__ == "__main__":
    unittest.main()
