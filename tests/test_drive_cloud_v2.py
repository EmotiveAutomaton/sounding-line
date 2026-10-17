import unittest
from runners.drive.cloud_v2 import params,engine,Replay,Collect,MemoryCache,QUESTIONS
from runners.stage14.common import digest


class RepairTests(unittest.TestCase):
    def test_full_known_answer_offline_replay_preserves_contract(self):
        Transcriber,battery,constructed,_=engine();backend=Collect();tr=Transcriber(backend,MemoryCache());answers={}
        for q in QUESTIONS:
            backend.question=q
            for item in constructed(q):
                backend.expected=item['expected'];tr.ask(q,context=item['context'],text=item['text'],before=item.get('before'),admission_test=True)
                ident=backend.rows[-1]['custom_id'];import json
                answers[ident]=dict(result=dict(type='succeeded',message=dict(model=backend.model_id,stop_reason='end_turn',content=[dict(type='text',text=json.dumps({'answer':item['expected']}))])))
        self.assertEqual(len(answers),1800)
        for q in QUESTIONS:
            r=battery(Transcriber(Replay(answers),MemoryCache()),q,constructed(q));self.assertTrue(r['passed'])
        for row in backend.rows:
            shape=row['params']['output_config']['format']['schema']['properties']['answer']
            self.assertNotIn('maxItems',shape);self.assertNotIn('uniqueItems',shape)
        from tompathy_engine.transcribe.runner import validate_answer
        with self.assertRaises(ValueError):validate_answer('Q10',{'answer':['care','care']})
        with self.assertRaises(ValueError):validate_answer('Q10',{'answer':['not-a-label']})


if __name__=='__main__':unittest.main()
