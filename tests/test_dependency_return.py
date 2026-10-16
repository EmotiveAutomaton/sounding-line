import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runners.next_round import dependency_return as relay


class DependencyReturnTests(unittest.TestCase):
    def test_missing_pending_and_wrong_scope_do_not_admit(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/'witness.json'
            self.assertIsNone(relay.completed_return(source))
            source.write_text(json.dumps(dict(scope='ghost', status='RUNNING')))
            self.assertIsNone(relay.completed_return(source))
            source.write_text(json.dumps(dict(scope='unrelated', status='PASS')))
            with self.assertRaises(ValueError):
                relay.completed_return(source)

    def test_actual_relay_preserves_failed_return_without_admitting_or_reentry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/'witness.json'
            blob = b'{"scope":"ghost", "status":"FAIL", "control":false}\n'
            source.write_bytes(blob)
            with patch.object(relay, 'REPO', root), patch.object(relay, 'native_identity', return_value={'pid': 123}):
                relay.run(source, root/'out', max_seconds=1, poll_seconds=1)
                self.assertEqual((root/'out/SOURCE_WITNESS.json').read_bytes(), blob)
                receipt = json.loads((root/'out/RETURN_READY.json').read_text())
                self.assertFalse(receipt['scientific_admission'])
                self.assertEqual(receipt['status'], 'REVIEW_REQUIRED')
                with self.assertRaises(FileExistsError):
                    relay.run(source, root/'out', max_seconds=1, poll_seconds=1)

    def test_cancel_does_not_consume_available_return(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'out').mkdir()
            (root/'out/CANCEL').touch()
            source = root/'witness.json'
            source.write_text(json.dumps(dict(scope='ghost', status='PASS')))
            with patch.object(relay, 'REPO', root), patch.object(relay, 'native_identity', return_value={'pid': 123}):
                relay.run(source, root/'out', max_seconds=1, poll_seconds=1)
            self.assertTrue((root/'out/CANCELLED.json').exists())
            self.assertFalse((root/'out/RETURN_READY.json').exists())


if __name__ == '__main__':
    unittest.main()
