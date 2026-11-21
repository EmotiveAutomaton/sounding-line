"""Constructed-only tests of CANDOR reciprocal labels and bounded clock controls."""
import unittest

from runners.drive.sealed import week6_sc2_source_v1 as source


def fixture(conversation="made-up", a="artist", b="baker"):
    survey = [(conversation, a, b, 2, 3, 4), (conversation, b, a, 7, 8, 9)]
    clock = [(conversation, 120)]
    runs = [(conversation, 0, a, 0, 22), (conversation, 1, a, 25, 45),
            (conversation, 2, b, 38, 48), (conversation, 3, a, 40, 50),
            (conversation, 4, b, 50, 65), (conversation, 5, b, 108, 123)]
    return survey, clock, runs


class TestCohorts(unittest.TestCase):
    def test_direction_and_overlap(self):
        survey, clock, runs = fixture()
        result, counts = source.pair_rows(survey[::-1], clock, runs[::-1])
        self.assertEqual(counts["retained_conversations"], 1)
        self.assertEqual(counts["retained_people"], 2)
        by_target = {row[0]: row for row in result[0][1]}
        self.assertEqual(by_target["artist"][1:5], ("baker", 7., 8., 9.))
        self.assertEqual(by_target["baker"][1:5], ("artist", 2., 3., 4.))
        self.assertEqual(by_target["artist"][5], 2.)
        self.assertEqual(by_target["artist"][6], .5)
        self.assertEqual(by_target["baker"][6], .5)

    def test_union_and_clipping(self):
        edges = [(0, "a", 0, 30), (1, "a", 1, 7), (2, "a", 2, 5),
                 (3, "b", 6, 15), (4, "b", 0, 100)]
        shares, error = source.controls(edges, ("a", "b"), 10)
        self.assertIsNone(error)
        self.assertAlmostEqual(shares["a"], .6)
        self.assertAlmostEqual(shares["b"], .4)

    def test_missing_or_duplicate_clock(self):
        survey, clock, runs = fixture()
        for invalid in ([], clock + clock, [("made-up", 0)], [("made-up", float("nan"))]):
            result, counts = source.pair_rows(survey, invalid, runs)
            self.assertEqual((result, counts["recording_clock"]), ([], 1))

    def test_bad_dyads(self):
        survey, clock, runs = fixture()
        for invalid, reason in ((survey[:1], "non_dyadic_survey"), (survey + survey[:1], "non_dyadic_survey"),
                                (survey[:1] * 2, "nonreciprocal_survey"),
                                ([("made-up", "x", "x", 2, 3, 4)] * 2, "nonreciprocal_survey")):
            result, counts = source.pair_rows(invalid, clock, runs)
            self.assertEqual((result, counts[reason]), ([], 1))

    def test_complete_pair_required(self):
        survey, clock, runs = fixture()
        survey[0] = ("made-up", "artist", "baker", 2, None, 4)
        result, counts = source.pair_rows(survey, clock, runs)
        self.assertEqual((result, counts["incomplete_ratings"]), ([], 1))

    def test_malformed_turns(self):
        survey, clock, runs = fixture()
        for edit, reason in ((("made-up", 1, "third", 25, 45), "unmatched_speaker"),
                             (("made-up", 3, "artist", 25, 45), "turn_index"),
                             (("made-up", 1, "artist", 45, 25), "invalid_timing"),
                             (("made-up", 1, "artist", True, 25), "invalid_timing")):
            rows = runs.copy()
            rows[1] = edit
            result, counts = source.pair_rows(survey, clock, rows)
            self.assertEqual((result, counts[reason]), ([], 1))

    def test_speech_from_both_recipients(self):
        survey, clock, runs = fixture()
        only_one = [(c, i, "artist", lo, hi) for c, i, _, lo, hi in runs]
        result, counts = source.pair_rows(survey, clock, only_one)
        self.assertEqual((result, counts["missing_speaker_time"]), ([], 1))
        self.assertEqual(source.pair_rows(survey, clock, runs[:2])[1]["insufficient_turns"], 1)

    def test_people_repeated_across_conversations(self):
        groups = [fixture("first", "shared", "p1"), fixture("second", "p2", "shared")]
        survey, clock, runs = ([r for group in groups for r in group[j]] for j in range(3))
        result, counts = source.pair_rows(survey, clock, runs)
        self.assertEqual((len(result), counts["retained_people"]), (2, 3))

    def test_source_contract_has_only_needed_fields(self):
        self.assertLess(sum(size * 3 for _, size, _ in source.PINS.values()), 2_000_000_000)
        self.assertEqual(source.COLUMNS["speech"], ("conversation_id", "turn_id", "speaker", "start", "stop"))
        self.assertEqual(set(source.PINS), set(source.COLUMNS))
        self.assertTrue(all(len(digest) == 64 for _, _, digest in source.PINS.values()))
