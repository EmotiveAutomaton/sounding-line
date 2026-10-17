import copy,gzip,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tests.test_drive_suggestion_corpus import CorpusTests
from runners.drive.suggestion_corpus_v3 import checkpoint,load_checkpoint,digest,canonical,storage_recovery,filehash

class StorageTests(unittest.TestCase):
    def test_real_tokenizer_container_shape_and_corruption(self):
        cases,rows=CorpusTests().fixture()
        for row in rows:
            for score in row['scores']:score['codepoint_offsets']=[tuple(x) for x in score['codepoint_offsets']]
        payload=dict(model='m',plan_sha256='p',input_sha256=digest(cases),rows=rows)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'chunk.json.gz';record=checkpoint(path,payload,cases)
            actual=load_checkpoint(path,record,cases,'p','m')
            self.assertNotEqual(actual,payload);self.assertEqual(canonical(actual),canonical(payload))
            self.assertEqual(path.read_bytes(),gzip.compress((canonical(payload)+'\n').encode(),compresslevel=6,mtime=0))
            changed=copy.deepcopy(cases);changed[0]['menu'][0]='zz'
            with self.assertRaisesRegex(ValueError,'binding'):load_checkpoint(path,record,changed,'p','m')
            path.write_bytes(path.read_bytes()+b'bad')
            with self.assertRaisesRegex(ValueError,'binding'):load_checkpoint(path,record,cases,'p','m')
    def test_changed_json_value_still_refuses(self):
        cases,rows=CorpusTests().fixture();payload=dict(rows=rows)
        altered=copy.deepcopy(payload);altered['rows'][0]['scores'][0]['codepoint_offsets'][0]=(0,2)
        with tempfile.TemporaryDirectory() as td,patch('runners.drive.suggestion_corpus_v3.json.loads',return_value=altered):
            with self.assertRaisesRegex(ValueError,'readback'):checkpoint(Path(td)/'x.gz',payload,cases)
    def test_schema_failure_still_refuses(self):
        cases,rows=CorpusTests().fixture();rows.pop()
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'incomplete'):checkpoint(Path(td)/'x.gz',dict(rows=rows),cases)
    @patch('runners.drive.suggestion_corpus_v3.native_identity',return_value=None)
    def test_storage_admission_binding_and_lifetime(self,native):
        def save(path,value):path.write_text(canonical(value),encoding='utf8')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);save(root/'PLAN.json',dict(pins={}))
            save(root/'OWNER.json',dict(at='2026-10-17T14:00:00+00:00',native=dict(pid=1),plan_sha256=filehash(root/'PLAN.json')))
            save(root/'FAILED.json',dict(at='2026-10-17T14:00:15+00:00',reason='checkpoint readback'))
            (root/'one.json.gz').write_bytes(b'fixture')
            proof=dict(status='VERIFIED_CHECKPOINT_REPRESENTATION_FAILURE',exact_failure_reproduced_from_actual_payload=True,canonical_json_equal=True,stored_json_and_score_schema_valid=True,terminal_sha256=filehash(root/'FAILED.json'),plan_sha256=filehash(root/'PLAN.json'),retained_chunk_sha256=filehash(root/'one.json.gz'))
            receipt=root/'receipt.json';save(receipt,proof)
            self.assertEqual(storage_recovery(root,receipt)['charged_seconds'],15.)
            native.return_value=dict(pid=1)
            with self.assertRaisesRegex(ValueError,'live'):storage_recovery(root,receipt)
            native.return_value=None;(root/'one.json.gz').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'checkpoint changed'):storage_recovery(root,receipt)

if __name__=='__main__':unittest.main()
