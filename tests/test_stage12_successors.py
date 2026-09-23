"""Known-answer, complete-roster and idempotent replay checks for new cells."""
import json
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from runners.stage12.common import REPO, freeze, read, digest, filehash
from runners.stage12 import retention_access, local_operator, local_interpretation, casebook
from runners.stage12.output_interface import VERSION, rows_for_card


@contextmanager
def fake_service(*args, **kwargs):
    yield {}


class Successors(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=REPO/'results')
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.calls = {}

    def call(self, request, n, path, state, raw):
        binding = digest(request)
        if str(path) in self.calls:
            prior, result = self.calls[str(path)]
            self.assertEqual(prior, binding)
            return result
        body = dict(analysis='TEST FIXTURE ONLY', probabilities=[1.0]+[0.0]*(n-1))
        if 'claims' in request['format']['properties']:
            body.update(claims=[], unknown=True, next_evidence='Independent operation record.')
        freeze(path/'RAW.json', dict(message=dict(content=json.dumps(body))))
        result = dict(probabilities=body['probabilities'], wall_seconds=1, prompt_tokens=100, output_tokens=100)
        self.calls[str(path)] = binding, result
        return result

    def gate(self, raw):
        gate = raw/'jobs/gate'; profile = dict(output=2048)
        freeze(gate/'ADMISSION.json', dict(reader_admitted=True))
        freeze(gate/'READER_READY.json', dict(status='complete',profile=profile,output_interface=VERSION))
        freeze(gate/'ROWS.json', [dict(call_class=k,call=dict(wall_seconds=10,prompt_tokens=100,output_tokens=100)) for k in ('forecast','account')])
        return dict(canary_card='gate', profile=profile, output_interface=VERSION)

    def test_access_exact_reference_and_whole_handler_reentry(self):
        from runners.stage11_2.world import make_unit
        units = [make_unit('dev',i)[0] for i in (12,13,14,15)]
        freeze(self.root/'results/phase_2_4_stage_11_2/raw/fixture/dev-public.json', units)
        source = self.root/'jobs/source'
        with patch.object(retention_access,'REPO',self.root):
            prepared = retention_access.compile(source,dict(candidate_ids=[u['unit'] for u in units]),lambda **kw:None,self.root)
        self.assertTrue(all(prepared['controls'].values()))
        self.assertEqual(prepared['maximum_calls'],68)
        card = dict(self.gate(self.root),compile_card='source',candidate_ids=[u['unit'] for u in units])
        with patch.object(retention_access.local_api,'service',fake_service), patch.object(retention_access.local_api,'call',side_effect=self.call):
            first = retention_access.run(self.root/'out',card,lambda **kw:None,self.root)
            second = retention_access.run(self.root/'out',card,lambda **kw:None,self.root)
        self.assertEqual(first,second)
        self.assertEqual(len(self.calls),68)
        rows=read(self.root/'out/ROWS.json')
        self.assertEqual(len(rows),56)
        self.assertEqual({r['condition'] for r in rows},set(retention_access.CONDITIONS))
        for unit in units:
            for q in retention_access.QUERIES:
                prefix=str(self.root/'out/calls'/f"{unit['unit']}-{q}-")
                self.assertEqual(self.calls[prefix+'raw_history'][0],self.calls[prefix+'unchanged_repeat'][0])

    def test_varied_operations_native_reference_and_handler_reentry(self):
        path=REPO/'results/phase_2_4_stage_12/raw/inputs/ghost-source-v1/ghostscale/validation/soundingline/v19/local_world.py'
        if not path.exists():
            self.skipTest('Frozen external native source not installed')
        card=dict(generator_source=str(path.parents[4]),lineage=0)
        summary=local_operator.compile(self.root/'jobs/source',card,lambda **kw:None,self.root)
        self.assertTrue(all(summary['controls'].values()))
        references=read(self.root/'jobs/source/REFERENCES.json')
        self.assertEqual(len(references),24)
        operations=[r['actual']['steps'][0]['operation'] for r in references[::3]]
        self.assertEqual({op:operations.count(op) for op in operations},{op:2 for op in local_operator.OPERATIONS})
        requests=read(self.root/'jobs/source/REQUESTS.json')
        effective=rows_for_card(requests,dict(output_interface=VERSION))
        self.assertEqual(len({digest(r['request']) for r in effective}),144)
        for r in references:
            self.assertNotIn('goal',json.dumps(r['public']['inputs'].get('observations',[])))
        run_card=dict(self.gate(self.root),compile_card='source',sources=list(range(24)))
        with patch.object(local_interpretation.local_api,'service',fake_service), patch.object(local_interpretation.local_api,'call',side_effect=self.call):
            first=local_interpretation.run(self.root/'out',run_card,lambda **kw:None,self.root)
            second=local_interpretation.run(self.root/'out',run_card,lambda **kw:None,self.root)
        self.assertEqual(first,second)
        self.assertEqual(len(self.calls),144)
        self.assertTrue(all(r['correspondence']['supported_witnessed_events']==0 for r in read(self.root/'out/ROWS.json')))

    def test_casebook_binding_metrics_and_changed_source_refusal(self):
        from runners.stage12.provider import packet,metrics
        directory=self.root/'jobs/source'
        packets=[packet('case',dict(endpoint='unit',anchors=[dict(id='unit',start=0,end=4)]),'fixture',[],tier=t) for t in ('E0','E1','E2','O')]
        freeze(directory/'PACKETS.json',packets)
        freeze(directory/'METRICS.json',[dict(case_id='case',tier=t,method='fixture',**metrics([],[])) for t in ('E0','E1','E2','O')])
        freeze(directory/'CONSTRUCTED_NULL.json',dict(unknown_metrics=dict(supported_useful_events=0),wrong_location_metrics=dict(correctly_located_useful_events=0)))
        freeze(directory/'COMPLETE.json',dict(status='complete',output_files={p.name:filehash(p) for p in directory.glob('*.json')}))
        card=dict(sources=[dict(job='source',terminal_sha256=filehash(directory/'COMPLETE.json'),cheap_baseline=True,null_controls=True,scientific_status='test fixture')])
        result=casebook.run(self.root/'out',card,lambda **kw:None,self.root)
        self.assertEqual(result['packets'],4)
        self.assertTrue(all(p['correspondence_metrics'] is not None for p in read(self.root/'out/PACKETS.json')))
        (directory/'METRICS.json').write_text('[]',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'output changed'):
            casebook.run(self.root/'bad',card,lambda **kw:None,self.root)


if __name__=='__main__':
    unittest.main()
