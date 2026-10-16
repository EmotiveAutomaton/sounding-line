import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from pathlib import Path
from runners.next_round.literal_admission import engine,gate_summary,Backend,MODEL,MODEL_DIGEST

class LiteralTests(unittest.TestCase):
    def test_catalogue_known_answers_and_constant_null(self):
        Transcriber,battery,constructed,Cache=engine()
        class Fake:
            pin='constructed-only'
            def ask(self,q,**kw):return {'answer':answers[(kw.get('context'),kw['text'],kw.get('before'))]}
        for q in ('Q8','Q9','Q7','Q1','Q3','Q4','Q6','Q10'):
            items=constructed(q);answers={(i['context'],i['text'],i.get('before')):i['expected'] for i in items}
            self.assertEqual(len(answers),200)
            passed=gate_summary(battery(Fake(),q,items),items)
            self.assertTrue(passed['constructed_feature_eligible'],q)
            answers={k:items[0]['expected'] for k in answers}
            failed=gate_summary(battery(Fake(),q,items),items)
            self.assertFalse(failed['constructed_feature_eligible'],q)

    def test_wrong_categorical_is_not_admitted_by_format(self):
        items=[dict(id=str(i),expected=str(i%4)) for i in range(200)]
        raw=dict(passed=True,accuracy=.25,outcomes=[dict(id=i['id'],valid=True,answer='0') for i in items])
        self.assertFalse(gate_summary(raw,items)['constructed_feature_eligible'])

    def test_actual_recorded_backend(self):
        with TemporaryDirectory() as tmp:
            calls=[];resident=dict(resident=[dict(name=MODEL,digest=MODEL_DIGEST,size_vram=0,context_length=8192)])
            def api(path,body=None,**kw):
                calls.append((path,body))
                return dict(done=True,done_reason='stop',response='{"answer":"yes"}')
            backend=Backend(Path(tmp),lambda:None)
            with patch('runners.next_round.literal_admission.inspect_service',return_value=resident),patch('runners.next_round.literal_admission.api',side_effect=api):
                self.assertEqual(backend.complete('question',{})['text'],'{"answer":"yes"}')
                self.assertEqual(calls[0][1]['options']['num_gpu'],0)
                self.assertTrue(list(Path(tmp).rglob('RAW.json')))
                with self.assertRaises(RuntimeError):backend.complete('question',{})
            self.assertEqual(len(calls),1)

    def test_unknown_transport_has_no_retry(self):
        with TemporaryDirectory() as tmp:
            backend=Backend(Path(tmp),lambda:None)
            with patch('runners.next_round.literal_admission.inspect_service',return_value={}),patch('runners.next_round.literal_admission.api',side_effect=TimeoutError):
                with self.assertRaises(TimeoutError):backend.complete('question',{})
                self.assertTrue(backend.uncertain)
                with self.assertRaises(RuntimeError):backend.close()

if __name__=='__main__':unittest.main()
