import json,sys,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from runners.next_round import label_contract as m

class LabelContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.items=m.roster()

    def oracle(self):return [m.parse(r,dict(text=json.dumps(dict(answer=r['label'])))) for r in self.items]

    def test_full_roster_pairing_and_literal_constructions(self):
        self.assertEqual(len(self.items),896)
        self.assertEqual(len({r['slot'] for r in self.items}),896)
        for r in self.items:
            paired=[x for x in self.items if all(x[k]==r[k] for k in ('model','target','context_kind','arm'))]
            self.assertEqual(len(paired),2);self.assertEqual(paired[0]['prompt'],paired[1]['prompt'])
            other=next(x for x in self.items if all(x[k]==r[k] for k in ('model','target','context_kind','repeat')) and x['arm']!=r['arm'])
            self.assertEqual(r['schema'],other['schema'])
            self.assertEqual(r['prompt'].split('Input data: ')[1],other['prompt'].split('Input data: ')[1])
        q6=[r for r in m.targets() if r['question']=='Q6']
        self.assertEqual({r['label'] for r in q6},{'first','second','third','mixed'})
        self.assertTrue(all('I and you ' in r['text'] for r in q6 if r['label']=='mixed'))
        self.assertEqual(sum(r['label']==[] for r in m.targets()),4)

    def test_oracle_and_null_and_signed_contrast(self):
        rows=self.oracle();s=m.summarize(rows,self.items)
        self.assertTrue(all(g['correct']==g['attempted'] for g in s['cells'].values()))
        self.assertTrue(all(g['improved']==g['worsened']==0 for g in s['paired'].values()))
        self.assertTrue(all(g['disagree']==0 for g in s['repeat_disagreement'].values()))
        constant=[m.parse(r,dict(text=json.dumps(dict(answer='first' if r['question']=='Q6' else [])))) for r in self.items]
        s=m.summarize(constant,self.items)
        self.assertTrue(any(g['correct']==0 for g in s['cells'].values()))
        for row in rows:
            if row['arm']=='scoped':row.update(valid=False,answer=None,correct=False)
        s=m.summarize(rows,self.items)
        self.assertTrue(all(g['improved']>0 and g['worsened']==0 for g in s['paired'].values()))
        for row in rows:
            row.update(valid=row['arm']=='scoped',answer=row['label'] if row['arm']=='scoped' else None,correct=row['arm']=='scoped')
        s=m.summarize(rows,self.items)
        self.assertTrue(all(g['worsened']>0 and g['improved']==0 for g in s['paired'].values()))

    def test_missing_duplicate_and_invalid_whole_response(self):
        rows=self.oracle()
        for bad in (rows[:-1],rows[:-1]+[rows[0]]):
            with self.assertRaises(ValueError):m.summarize(bad,self.items)
        self.assertFalse(m.parse(self.items[0],dict(text='{"answer":"first"} trailing'))['valid'])
        theme=next(r for r in self.items if r['question']=='Q10')
        self.assertFalse(m.parse(theme,dict(text='{"answer":["unclear","care"]}'))['valid'])

    def test_actual_full_loop_offline_replay_mutation_and_reentry(self):
        native=dict(pid=7,created_ticks=8,executable='software-fixture')
        labels={r['prompt']:r['label'] for r in self.items};callcount=[]
        def inspect(model,owned=False):return dict(version=m.lm.VERSION,model=model,resident=[dict(digest=model['digest'],size_vram=0,context_length=8192)] if owned else [])
        def api(path,body=None,**kwargs):
            if path=='/api/ps':return dict(models=[])
            if body.get('keep_alive')==0:return {}
            callcount.append(body);return dict(done=True,done_reason='stop',response=json.dumps(dict(answer=labels[body['prompt']])))
        with TemporaryDirectory(dir=Path.cwd()/'.agent-state') as tmp:
            repo=Path(tmp);root=repo/'raw';(repo/'results').mkdir();root.mkdir()
            m.freeze(root/'ITEMS.json',self.items)
            m.freeze(root/'PLAN.json',dict(pins=m.pins([root/'ITEMS.json']),models=m.lm.MODELS,service_native=native,maximum_calls=896,max_wall_seconds=120))
            realfreeze=m.freeze
            def freeze(path,value):
                realfreeze(path,value)
                if path.name=='OWNER.json':realfreeze(root/'MONITOR_READY.json',dict(owner_sha256=m.filehash(path)))
            with patch.object(m,'REPO',repo),patch.object(m,'native_identity',return_value=native),patch.object(m.lm,'native_identity',return_value=native),patch.object(m,'freeze',side_effect=freeze),patch.object(m.lm,'inspect',side_effect=inspect),patch.object(m.lm,'api',side_effect=api):
                m.run(root)
                with self.assertRaises(FileExistsError):m.run(root)
            self.assertEqual(len(callcount),896);self.assertFalse((repo/'results/.literal-cpu.lock').exists())
            self.assertFalse((root/'FAILED.json').exists());self.assertTrue((root/'REPLAY.json').exists())
            sys.path.insert(0,str(Path.cwd()/'tools'))
            from codex_watch import valid_json
            self.assertTrue(valid_json(root/'COMPLETE.json'))
            m.freeze(root/'fixture-failure.json',dict(status='FAILED',error='fixture'))
            self.assertTrue(valid_json(root/'fixture-failure.json'))
            self.assertFalse(valid_json(root/'PLAN.json'))
            with patch.object(m.lm,'api',side_effect=AssertionError('offline replay must not dispatch')):
                self.assertEqual(m.replay(root)['calls'],896)
                raw=next((root/'calls').glob('*/*/RAW.json'));raw.write_text('{}',encoding='utf8')
                with self.assertRaises(ValueError):m.replay(root)

if __name__=='__main__':unittest.main()
