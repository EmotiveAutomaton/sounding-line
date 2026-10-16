import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from runners.next_round import literal_models as m

class ModelsTests(unittest.TestCase):
    def test_known_answer_and_constant_null_full_roster(self):
        _,battery,constructed,_=m.engine()
        class Fake:
            pin='software-fixture'
            def ask(self,q,**kw):return {'answer':answers[(kw['context'],kw['text'],kw['before'])]}
        for q in m.QUESTIONS:
            items=constructed(q);answers={(i['context'],i['text'],i['before']):i['expected'] for i in items}
            self.assertEqual(len(answers),200)
            self.assertTrue(m.gate_summary(battery(Fake(),q,items),items)['constructed_feature_eligible'],q)
            answers={key:items[0]['expected'] for key in answers}
            self.assertFalse(m.gate_summary(battery(Fake(),q,items),items)['constructed_feature_eligible'],q)

    def test_whole_response_and_explicit_qwen_control(self):
        self.assertIs(m.request(m.MODELS['qwen9'],'x',{})['think'],False)
        self.assertNotIn('think',m.request(m.MODELS['llama3'],'x',{}))
        for raw in (dict(done=True,done_reason='length'),dict(done=True,done_reason='stop',thinking='unexpected')):
            with self.assertRaises(ValueError):m.text_response(raw)
        with self.assertRaises(RuntimeError):m.text_response(dict(done=False))

    def test_raw_retention_duplicate_and_unknown_transport(self):
        model=m.MODELS['qwen9'];resident=dict(version=m.VERSION,model=model,resident=[dict(digest=model['digest'],size_vram=0,context_length=8192)])
        with TemporaryDirectory() as tmp:
            backend=m.Backend(model,Path(tmp),lambda:None)
            raw=dict(done=True,done_reason='stop',response='{"answer":"yes"}')
            with patch.object(m,'inspect',return_value=resident),patch.object(m,'api',return_value=raw):
                self.assertEqual(backend.complete('x',{})['text'],raw['response'])
                with self.assertRaises(RuntimeError):backend.complete('x',{})
            self.assertEqual(len(list(Path(tmp).rglob('RAW.json'))),1)
            replay=m.Replay(model,Path(tmp));self.assertEqual(replay.complete('x',{})['text'],raw['response'])
            with self.assertRaises(RuntimeError):replay.complete('x',{})
        with TemporaryDirectory() as tmp:
            backend=m.Backend(model,Path(tmp),lambda:None)
            with patch.object(m,'inspect',return_value=resident),patch.object(m,'api',side_effect=TimeoutError):
                with self.assertRaises(TimeoutError):backend.complete('x',{})
                self.assertTrue(backend.uncertain)
                with self.assertRaises(RuntimeError):backend.close()

    def test_foreign_and_gpu_residency_refuse(self):
        model=m.MODELS['llama3']
        for row in (dict(digest='foreign',size_vram=0,context_length=8192),dict(digest=model['digest'],size_vram=1,context_length=8192)):
            with patch.object(m,'api',side_effect=[dict(version=m.VERSION),dict(models=[dict(name=model['name'],digest=model['digest'])]),dict(models=[row])]):
                with self.assertRaises(RuntimeError):m.inspect(model,True)

    def test_complete_recorded_question_replays_without_network(self):
        import json
        Transcriber,battery,constructed,_=m.engine();items=constructed('Q5')
        answers={(i['context'],i['text'],i['before']):i['expected'] for i in items}
        model=m.MODELS['llama3'];resident=dict(version=m.VERSION,model=model,resident=[dict(digest=model['digest'],size_vram=0,context_length=8192)])
        def api(path,body):
            inputs=json.loads(body['prompt'].split('\nInput data: ')[1])
            answer=answers[(inputs['context'],inputs['text'],inputs['before'])]
            return dict(done=True,done_reason='stop',response=json.dumps(dict(answer=answer)))
        with TemporaryDirectory() as tmp:
            backend=m.Backend(model,Path(tmp),lambda:None)
            with patch.object(m,'inspect',return_value=resident),patch.object(m,'api',side_effect=api):
                original=battery(Transcriber(backend,m.MemoryCache()),'Q5',items)
            with patch.object(m,'api',side_effect=AssertionError('replay must be offline')):
                replay=m.Replay(model,Path(tmp))
                replayed=battery(Transcriber(replay,m.MemoryCache()),'Q5',items)
            self.assertEqual(original,replayed);self.assertEqual(len(replay.seen),200)

if __name__=='__main__':unittest.main()
