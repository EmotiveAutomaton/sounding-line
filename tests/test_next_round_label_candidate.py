import json,sys,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from runners.next_round import label_candidate as m

class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.items=m.roster()

    def rows(self,answer=None):
        return [m.lc.parse(r,dict(text=json.dumps(dict(answer=r['label'] if answer is None else answer(r))))) for r in self.items]

    def test_original_full_roster_fixed_prompt_and_candidate_pin(self):
        _,_,constructed,_=m.lc.lm.engine()
        self.assertEqual(len(self.items),400)
        for q in m.QUESTIONS:
            subset=[r for r in self.items if r['question']==q]
            self.assertEqual([r['item'] for r in subset],constructed(q))
            self.assertTrue(all(r['prompt'].startswith(m.lc.SCOPE+m.lc.DEFINITIONS[q]) for r in subset))
        s=m.summarize(self.rows(),self.items)
        self.assertFalse(s['engine_admission']);self.assertFalse(s['feature_admission'])
        self.assertTrue(all(x['constructed_feature_eligible'] for x in s['questions'].values()))
        canonical=m.lc.read(m.lc.lm.ROOT/'qwen9/Q6/SUMMARY.json')['canonical']['transcriber_pin']
        self.assertNotEqual(s['questions']['Q6']['canonical']['transcriber_pin'],canonical)

    def test_nulls_and_reachable_classwise_failure(self):
        s=m.summarize(self.rows(lambda r:'first' if r['question']=='Q6' else []),self.items)
        self.assertTrue(all(not x['constructed_feature_eligible'] for x in s['questions'].values()))
        bad=self.rows(lambda r:r['label'] if r['label']!=[] else ['care'])
        s=m.summarize(bad,self.items)['questions']['Q10']
        self.assertTrue(s['canonical']['passed']);self.assertGreaterEqual(s['canonical']['accuracy'],.85)
        self.assertFalse(s['constructed_feature_eligible'])
        rows=self.rows()
        for wrong in (rows[:-1],rows[:-1]+[rows[0]]):
            with self.assertRaises(ValueError):m.summarize(wrong,self.items)
        rows[0]['correct']=False
        with self.assertRaises(ValueError):m.summarize(rows,self.items)

    def test_actual_complete_loop_replay_terminals_mutation_and_reentry(self):
        native=dict(pid=7,created_ticks=8,executable='software-fixture');callcount=[]
        labels={r['prompt']:r['label'] for r in self.items}
        def inspect(model,owned=False):return dict(version=m.lc.lm.VERSION,model=model,resident=[dict(digest=model['digest'],size_vram=0,context_length=8192)] if owned else [])
        def api(path,body=None,**kwargs):
            if path=='/api/ps':return dict(models=[])
            if body.get('keep_alive')==0:return {}
            callcount.append(body)
            return dict(done=True,done_reason='stop',response=json.dumps(dict(answer=labels[body['prompt']])))
        with TemporaryDirectory(dir=Path.cwd()/'.agent-state') as tmp:
            repo=Path(tmp);root=repo/'raw';(repo/'results').mkdir();root.mkdir()
            m.freeze(root/'ITEMS.json',self.items)
            m.freeze(root/'PLAN.json',dict(pins=m.pins([root/'ITEMS.json']),model=m.MODEL,service_native=native,maximum_calls=400,max_wall_seconds=120))
            realfreeze=m.freeze
            def freeze(path,value):
                realfreeze(path,value)
                if path.name=='OWNER.json':realfreeze(root/'MONITOR_READY.json',dict(owner_sha256=m.filehash(path)))
            with patch.object(m,'REPO',repo),patch.object(m,'native_identity',return_value=native),patch.object(m.lc.lm,'native_identity',return_value=native),patch.object(m,'freeze',side_effect=freeze),patch.object(m.lc.lm,'inspect',side_effect=inspect),patch.object(m.lc.lm,'api',side_effect=api):
                m.run(root)
                with self.assertRaises(FileExistsError):m.run(root)
            self.assertEqual(len(callcount),400);self.assertFalse((repo/'results/.literal-cpu.lock').exists())
            self.assertFalse((root/'FAILED.json').exists())
            sys.path.insert(0,str(Path.cwd()/'tools'))
            from codex_watch import valid_json
            self.assertTrue(valid_json(root/'COMPLETE.json'));self.assertFalse(valid_json(root/'PLAN.json'))
            with patch.object(m.lc.lm,'api',side_effect=AssertionError('replay is offline')):
                self.assertEqual(m.replay(root)['calls'],400)
                path=next((root/'calls').glob('*/*/RAW.json'));path.write_text('{}',encoding='utf8')
                with self.assertRaises(ValueError):m.replay(root)

    def test_actual_transport_failure_retains_lease_and_emits_failure(self):
        native=dict(pid=7,created_ticks=8,executable='software-fixture')
        with TemporaryDirectory(dir=Path.cwd()/'.agent-state') as tmp:
            repo=Path(tmp);root=repo/'raw';(repo/'results').mkdir();root.mkdir()
            m.freeze(root/'ITEMS.json',self.items)
            m.freeze(root/'PLAN.json',dict(pins=m.pins([root/'ITEMS.json']),model=m.MODEL,service_native=native,maximum_calls=400,max_wall_seconds=120))
            realfreeze=m.freeze
            def freeze(path,value):
                realfreeze(path,value)
                if path.name=='OWNER.json':realfreeze(root/'MONITOR_READY.json',dict(owner_sha256=m.filehash(path)))
            with patch.object(m,'REPO',repo),patch.object(m,'native_identity',return_value=native),patch.object(m.lc.lm,'native_identity',return_value=native),patch.object(m,'freeze',side_effect=freeze),patch.object(m.lc.lm,'inspect',return_value={}),patch.object(m.lc.lm,'api',side_effect=RuntimeError('unknown transport')):
                with self.assertRaisesRegex(RuntimeError,'unknown transport'):m.run(root)
            self.assertTrue((repo/'results/.literal-cpu.lock').exists());self.assertFalse((root/'COMPLETE.json').exists())
            self.assertEqual(len(list((root/'calls').glob('*/*/DISPATCH.json'))),1)
            sys.path.insert(0,str(Path.cwd()/'tools'))
            from codex_watch import valid_json
            self.assertTrue(valid_json(root/'FAILED.json'))

if __name__=='__main__':unittest.main()
