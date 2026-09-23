"""Known-answer execution, original-law identity and full handler reentry."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import contextmanager
from runners.stage12.common import REPO, RAW, read, freeze, digest
from runners.stage12 import execution_access as E, law_sensitivity as L
from runners.stage12.output_interface import VERSION


@contextmanager
def service(*args, **kwargs):
    yield {}


class ExecutionTests(unittest.TestCase):
    def test_rounding_and_directional_fidelity(self):
        p = E.rounded_answer([1/3, 1/3, 1/3, 0.])
        self.assertEqual(p, [.334, .333, .333, 0.])
        self.assertTrue(E.fidelity(p,p)['copied_exactly'])
        self.assertFalse(E.fidelity(p,[0., .333, .333, .334])['copied_exactly'])
        self.assertFalse(E.fidelity(None,p)['execution_valid'])
        self.assertFalse(E.fidelity([float('nan')]*4,p)['execution_valid'])

    def test_full_execution_matrix_and_idempotent_handler(self):
        from runners.stage11_2.world import make_unit
        with tempfile.TemporaryDirectory(dir=REPO/'results') as tmp:
            root = Path(tmp)
            units = [make_unit('dev',i)[0] for i in range(16,36)]
            freeze(root/'results/phase_2_4_stage_11_2/raw/fixture/dev-public.json',units)
            source = root/'jobs/source'
            card = dict(candidate_ids=[r['unit'] for r in units],output_interface=VERSION)
            with patch.object(E,'REPO',root):
                compiled = E.compile(source,card,lambda **kw:None,root)
                self.assertEqual(compiled,E.compile(source,card,lambda **kw:None,root))
            self.assertEqual(compiled['maximum_calls'],280)
            requests = read(source/'REQUESTS.json')
            targets = {r['id']:r for r in read(source/'EVALUATOR_ONLY.json')}
            calls = {}
            def call(request,n,path,state,raw):
                key = path.name
                if key in calls:
                    self.assertEqual(calls[key][0],digest(request))
                    return calls[key][1]
                p = targets[key]['supplied_answer']
                freeze(path/'RAW.json',dict(done=True,done_reason='stop',message=dict(content=json.dumps(dict(analysis='FAKE TRANSPORT ONLY',probabilities=p)))))
                result = dict(probabilities=p,wall_seconds=1,prompt_tokens=50,output_tokens=30)
                calls[key] = digest(request),result
                return result
            profile = dict(output=2048)
            gate = root/'jobs/gate'
            freeze(gate/'ADMISSION.json',dict(reader_admitted=True))
            freeze(gate/'READER_READY.json',dict(profile=profile,output_interface=VERSION))
            freeze(gate/'ROWS.json',[dict(call_class='forecast',call=dict(wall_seconds=10,prompt_tokens=50,output_tokens=30))])
            card.update(compile_card='source',canary_card='gate',profile=profile,effective_requests_digest=digest(requests))
            with patch.object(E.local_api,'service',service), patch.object(E.local_api,'call',side_effect=call):
                first = E.run(root/'out',card,lambda **kw:None,root)
                self.assertEqual(first,E.run(root/'out',card,lambda **kw:None,root))
            self.assertEqual(len(calls),280)
            self.assertEqual(first['calls'],280)
            self.assertTrue(all(r['copied_exactly'] for r in read(root/'out/ROWS.json')))
            for unit in units:
                for q in E.QUERIES:
                    rows = {r['condition']:r for r in requests if r['unit']==unit['unit'] and r['query']==q}
                    self.assertEqual(rows['raw_history']['request'],rows['unchanged_repeat']['request'])
                    self.assertEqual(set(rows),set(E.CONDITIONS))
            card['effective_requests_digest'] = 'changed'
            with self.assertRaisesRegex(ValueError,'roster differs'):
                E.run(root/'bad',card,lambda **kw:None,root)

    def test_original_raw_replay_and_changed_law_without_generation(self):
        if not (RAW/'jobs/S12-operator-7-20260923-v1/COMPLETE.json').exists():
            self.skipTest('private completed source not installed')
        card = dict(compile_card='S12-operator-compile-20260923-v1',
            generator_source=str(RAW/'inputs/ghost-source-v1'),lineages=[1],
            source_jobs=[f'S12-operator-{i}-20260923-v1' for i in range(8)])
        with tempfile.TemporaryDirectory(dir=REPO/'results') as tmp:
            out = Path(tmp)
            with patch('runners.stage12.local_api.api',side_effect=AssertionError('network forbidden')):
                first = L.run(out,card,lambda **kw:None,RAW)
                self.assertEqual(first,L.run(out,card,lambda **kw:None,RAW))
            self.assertEqual(first['rows'],288)
            self.assertEqual(first['calls'],0)
            rows=read(out/'ROWS.json')
            zero={r['id']:r for r in rows if r['lineage']==0}
            changed={r['id']:r for r in rows if r['lineage']==1}
            self.assertTrue(any(zero[k]['target']!=changed[k]['target'] for k in zero))
            self.assertTrue(all(zero[k]['support_sha256']==changed[k]['support_sha256'] for k in zero))
            self.assertEqual(sum(r['reader']['invalid'] for r in zero.values()),1)


if __name__=='__main__':
    unittest.main()
