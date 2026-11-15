"""UNRUN small structural tests; run only in the owner assigned counted fixture."""
import unittest
from runners.drive.cards.week5_at_queue_collect_v1 import original_scope


class OriginalScope(unittest.TestCase):
    def test_full_scope(self):original_scope(list(range(165)),27007)
    def test_missing_word(self):
        with self.assertRaises(ValueError):original_scope(list(range(165)),27006)
    def test_missing_chunk(self):
        with self.assertRaises(ValueError):original_scope(list(range(164)),27007)
    def test_duplicated_chunk(self):
        with self.assertRaises(ValueError):original_scope([*range(164),163],27007)
    def test_reordered_chunk(self):
        values=list(range(165));values[133],values[134]=values[134],values[133]
        with self.assertRaises(ValueError):original_scope(values,27007)
    def test_partial_native_fixture_not_pilot(self):
        with self.assertRaises(ValueError):original_scope([163,164],36)


if __name__=='__main__':unittest.main()
