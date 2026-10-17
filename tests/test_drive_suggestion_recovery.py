import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from runners.drive.suggestion_corpus_v2 import recovery_inputs,filehash

def write(path,value):path.write_text(json.dumps(value),encoding='utf8')

class RecoveryAdmissionTests(unittest.TestCase):
    def fixture(self,root):
        prior=root/'prior';diagnostic=root/'diagnostic';prior.mkdir();diagnostic.mkdir()
        identity=dict(pid=42,created_ticks=123,executable='fixture')
        for path in (prior,diagnostic):
            write(path/'OWNER.json',dict(at='2026-10-17T14:00:00+00:00',native=identity))
            write(path/'PLAN.json',dict(pins={}))
        write(prior/'FAILED.json',dict(at='2026-10-17T14:00:10+00:00'))
        for name in ('CASES.json','CENSUS.json','SELECTION.json'):write(prior/name,{'fixture':name})
        write(diagnostic/'SUMMARY.json',dict(remedy_supported=True))
        write(diagnostic/'COMPLETE.json',dict(at='2026-10-17T14:00:10+00:00',outputs={'SUMMARY.json':filehash(diagnostic/'SUMMARY.json')}))
        inspection=root/'inspection.json';write(inspection,dict(retained={n:filehash(prior/n) for n in ('CASES.json','CENSUS.json','SELECTION.json')}))
        failure=root/'failure.json';write(failure,dict(status='VERIFIED_APPARATUS_FAILURE',terminal_sha256=filehash(prior/'FAILED.json'),inspection_sha256=filehash(inspection)))
        precision=root/'precision.json';write(precision,dict(status='VERIFIED_COMPLETE_DIAGNOSTIC',remedy_supported=True,terminal_sha256=filehash(diagnostic/'COMPLETE.json')))
        return dict(prior=prior,diagnostic=diagnostic,failure=failure,precision=precision,inspection=inspection),identity
    @patch('runners.drive.suggestion_corpus_v2.native_identity',return_value=None)
    def test_complete_admission_and_changed_input_refusal(self,native):
        with tempfile.TemporaryDirectory() as td:
            args,_=self.fixture(Path(td));self.assertEqual(recovery_inputs(**args)['charged_seconds'],20.)
            (args['prior']/'CASES.json').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'retained input changed'):recovery_inputs(**args)
    @patch('runners.drive.suggestion_corpus_v2.native_identity',return_value=None)
    def test_failed_precision_never_admits(self,native):
        with tempfile.TemporaryDirectory() as td:
            args,_=self.fixture(Path(td));p=json.loads(args['precision'].read_text());p['remedy_supported']=False;write(args['precision'],p)
            with self.assertRaisesRegex(ValueError,'unadmitted'):recovery_inputs(**args)
    def test_live_predecessor_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            args,identity=self.fixture(Path(td))
            with patch('runners.drive.suggestion_corpus_v2.native_identity',return_value=identity):
                with self.assertRaisesRegex(ValueError,'predecessor live'):recovery_inputs(**args)
    @patch('runners.drive.suggestion_corpus_v2.native_identity',return_value=None)
    def test_recovery_cannot_reset_aggregate_allowance(self,native):
        with tempfile.TemporaryDirectory() as td:
            args,_=self.fixture(Path(td));write(args['prior']/'FAILED.json',dict(at='2026-10-17T17:00:00+00:00'))
            p=json.loads(args['failure'].read_text());p['terminal_sha256']=filehash(args['prior']/'FAILED.json');write(args['failure'],p)
            with self.assertRaisesRegex(ValueError,'allowance exhausted'):recovery_inputs(**args)

if __name__=='__main__':unittest.main()
