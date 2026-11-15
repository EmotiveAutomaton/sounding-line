"""UNRUN constructed tests. Owner must assign a counted slot before invocation.

DESIGN CHECK: LESSONS 3-5. No human inputs or model loading. Exhaustive manifest
bands and corruption refusals are identical under null and alternative outcomes.
Actual native lifecycle coverage belongs to week5_at_queue_v1_fixture.
"""
import copy
from pathlib import Path
import tempfile
import unittest
from runners.drive.cards import week5_at_queue_v1 as q


def spec():
    batches=[dict(batch_ordinal=i,input_rows=f'constructed/{i}.gz',words=164 if i<164 else 111)
             for i in range(165)]
    return dict(schema='AT_QUEUE_V1',owner_bound=True,
        original_roster=dict(sha256=q.ROSTER_SHA),model_proposal=dict(sha256=q.MODEL_PROPOSAL_SHA),
        model_ordinal=0,numerical_spec=q.NUMERIC,native_limits=q.LIMITS,scorer=q.SCORER,numerical_threads=2,
        start_ordinal=133,end_ordinal_exclusive=165,batches=batches,
        score_config=dict(context='final',context_length=1024,max_wall_seconds=900),
        caps=dict(queue_wall_seconds=43200,queue_cpu_seconds=230400,chunk_cpu_seconds=7200,
                  chunk_wall_seconds=1700,projected_peak_ram_GiB=20,output_bytes=2**30),
        prefix=dict(count=133,owner_reviewed=True,file_pins={'constructed':'0'*64}),child_pins={'constructed':'0'*64})


class Contracts(unittest.TestCase):
    def test_exact_manifest_allowed(self): q.validate_manifest(spec())

    def test_non_owner_bound_refuses(self):
        x=spec();x['owner_bound']=False
        with self.assertRaises(ValueError):q.validate_manifest(x)

    def test_every_ordinal_required(self):
        for mutation in ('missing','duplicate','swap','extend'):
            x=spec()
            if mutation=='missing':x['batches'].pop()
            elif mutation=='duplicate':x['batches'][134]['batch_ordinal']=133
            elif mutation=='swap':x['batches'][133],x['batches'][134]=x['batches'][134],x['batches'][133]
            else:x['batches'].append(dict(x['batches'][-1]))
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):q.validate_manifest(x)

    def test_no_precision_context_reader_guard_substitution(self):
        for key,value in [('model_ordinal',1),('numerical_spec',dict(q.NUMERIC,model_computation='float32')),
                          ('native_limits',dict(q.LIMITS,start_commit_bytes=1)),('scorer','anything_else'),
                          ('score_config',dict(context='final',context_length=256,max_wall_seconds=900)),
                          ('numerical_threads',4)]:
            x=spec();x[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):q.validate_manifest(x)

    def test_budget_and_clock_bands(self):
        for key,value in [('queue_wall_seconds',43201),('queue_cpu_seconds',750001),('chunk_wall_seconds',1801),
                          ('chunk_cpu_seconds',7201),('output_bytes',float('nan')),('projected_peak_ram_GiB',19)]:
            x=spec();x['caps'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):q.validate_manifest(x)

    def test_prefix_gap_refused(self):
        x=spec();x['prefix']['count']=132
        with self.assertRaises(ValueError):q.validate_manifest(x)

    def test_path_traversal_refused(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):q.below(Path(t),'../outside')

    def test_checkpoint_corruption_refused(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'data').write_bytes(b'original')
            seal=dict(files=q.inventory(root));q.check_seal(root,seal)
            (root/'data').write_bytes(b'changed')
            with self.assertRaises(ValueError):q.check_seal(root,seal)

    def test_operational_request_excluded_but_scores_not(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'YIELD_REQUEST.json').write_bytes(b'{}');(root/'block-00000.json').write_bytes(b'{}')
            self.assertEqual(set(q.inventory(root)),{'block-00000.json'})


if __name__=='__main__':unittest.main()
