"""Storage recovery refusals and full original/resumed pipeline equivalence."""
import gzip
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from runners.drive import v1_phase0_v3 as v
from tests.test_drive_v1_v2 import fixture


class RecoveryTests(unittest.TestCase):
    def test_preparation_preserves_grid_cap_and_remaining_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            prior, out = repo/'prior', repo/'new'
            grid = v.original.GRID
            old = dict(pins={}, grid=grid, runtime=v.original.runtime(), max_wall_seconds=72000,
                       max_resource_wait_seconds=43200, max_output_bytes=10*1024**3)
            v.freeze(prior/'PLAN.json', old)
            sha = v.filehash(prior/'PLAN.json')
            owner = dict(native=dict(pid=1), plan_sha256=sha, at='2026-10-17T00:00:00+00:00')
            terminal = dict(status='FAILED', reason='output byte ceiling', at='2026-10-17T06:00:00+00:00')
            v.freeze(prior/'OWNER.json', owner)
            v.freeze(prior/'FAILED.json', terminal)
            for p in ('runners/drive/v1_phase0_v3.py', 'tests/test_drive_v1_v3.py', 'docs/design/stage-15/drive/V1_PHASE0_V3.md'):
                (repo/p).parent.mkdir(parents=True, exist_ok=True)
                (repo/p).write_text('fixture', encoding='utf8')
            for name in v.FILES:
                v.freeze(prior/'worlds/000'/name, dict(cell=grid[0]))
            with patch.object(v, 'REPO', repo), patch.object(v, 'PRIOR', prior), patch.object(v, 'ROOT', out), \
                 patch.object(v, 'EXPECTED_PRIOR_PLAN', sha), patch.object(v, 'native_identity', return_value=None), \
                 patch.object(v, 'pins', side_effect=lambda paths: {p.relative_to(repo).as_posix(): v.filehash(p) for p in paths}):
                v.prepare()
                plan = v.read(out/'PLAN.json')
                self.assertEqual(plan['grid'], grid)
                self.assertEqual(plan['max_wall_seconds'], 50400)
                self.assertEqual(plan['max_output_bytes'], old['max_output_bytes'])
                self.assertEqual(plan['reuse'][0]['world'], 0)
                with self.assertRaisesRegex(ValueError, 'existing recovery'): v.prepare()

    def test_lossless_deterministic_immutable_and_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root/'a.json.gz', root/'b.json.gz'
            raw = b'{"unicode":"\xe2\x86\x92", "exact": 1.0000}\n'
            first = v.retain_bytes(a, raw, root, 100_000_000)
            self.assertEqual(gzip.decompress(a.read_bytes()), raw)
            self.assertEqual(first, v.retain_bytes(a, raw, root, 100_000_000))
            v.retain_bytes(b, raw, root, 100_000_000)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with self.assertRaisesRegex(ValueError, 'immutable'):
                v.retain_bytes(a, raw+b' ', root, 100_000_000)
            with self.assertRaisesRegex(RuntimeError, 'ceiling'):
                v.retain_bytes(root/'c.json.gz', raw, root, v.META_RESERVE)
            self.assertFalse((root/'c.json.gz').exists())
            a.write_bytes(a.read_bytes()[:-5])
            with self.assertRaises((EOFError, OSError)):
                v.read_gzip(a)

    def test_predecessor_liveness_unknown_and_terminal_refusals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            identity = dict(pid=1, created_ticks=2, executable='fixture')
            v.freeze(root/'OWNER.json', dict(native=identity))
            v.freeze(root/'FAILED.json', dict(status='FAILED', reason='output byte ceiling'))
            with patch.object(v, 'native_identity', return_value=identity):
                with self.assertRaisesRegex(ValueError, 'live'): v.prior_terminal(root)
            with patch.object(v, 'native_identity', side_effect=OSError('unknown')):
                with self.assertRaises(OSError): v.prior_terminal(root)
            with patch.object(v, 'native_identity', return_value=None):
                self.assertEqual(v.prior_terminal(root)[1]['reason'], 'output byte ceiling')
                v.atomic(root/'FAILED.json', dict(status='FAILED', reason='other failure'))
                with self.assertRaisesRegex(ValueError, 'unexpected'): v.prior_terminal(root)
                v.freeze(root/'MONITOR_FAILED.json', dict(status='UNKNOWN'))
                with self.assertRaisesRegex(ValueError, 'separate review'): v.prior_terminal(root)

    def test_prefix_gaps_missing_files_and_wrong_cells(self):
        grid = [dict(seed=i) for i in range(3)]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def world(i):
                for name in v.FILES:
                    v.freeze(root/'worlds'/f'{i:03d}'/name, dict(cell=grid[i]))
            world(0)
            self.assertEqual(len(v.checkpoint_prefix(root, grid)), 1)
            world(2)
            with self.assertRaisesRegex(ValueError, 'noncontiguous'): v.checkpoint_prefix(root, grid)
            (root/'worlds/002/RESULT.json').unlink()
            (root/'worlds/000/FITS.json').unlink()
            with self.assertRaisesRegex(ValueError, 'incomplete'): v.checkpoint_prefix(root, grid)
            v.freeze(root/'worlds/000/FITS.json', dict(cell=grid[0]))
            v.atomic(root/'worlds/000/RESULT.json', dict(cell=grid[1]))
            with self.assertRaisesRegex(ValueError, 'identity'): v.checkpoint_prefix(root, grid)

    def test_resumed_whole_pipeline_equals_original_and_refuses_changed_reuse(self):
        original = v.original
        sessions = fixture()
        base = {r['key']: [.25]*4 for s in sessions for r in s['rows']}
        grid = [dict(effect='offset', delta=delta, seed=10+i, replicate=0) for i, delta in enumerate((0., .8))]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            phase, prior, out = root/'phase', root/'prior', root/'new'
            v.freeze(phase/'prepared/SESSIONS.json', sessions)
            v.freeze(phase/'T0c/PREDICTIONS.json', [dict(key=k, probabilities={'B-pop': p}) for k, p in base.items()])
            with patch.object(original, 'ROOT', prior), patch.object(original, 'PHASE', phase):
                original.compute(dict(grid=grid), lambda _: None)
            expected = v.read(prior/'SUMMARY.json')
            reuse = [dict(world=0, files={name: v.filehash(prior/'worlds/000'/name) for name in v.FILES})]
            plan = dict(grid=grid, reuse=reuse, max_output_bytes=100_000_000)
            # Exactly one refit: a reused world never calls the optimizer.
            with patch.object(original, 'fit_world', wraps=original.fit_world) as fitting:
                v.compute(plan, lambda _: None, root=out, prior=prior, phase=phase)
                self.assertEqual(fitting.call_count, 1)
            self.assertEqual(expected, v.read(out/'SUMMARY.json'))
            for i in range(2):
                for name in v.FILES:
                    self.assertEqual((prior/'worlds'/f'{i:03d}'/name).read_bytes(), gzip.decompress((out/'worlds'/f'{i:03d}'/(name+'.gz')).read_bytes()))
            before = {p.relative_to(out).as_posix(): v.filehash(p) for p in out.rglob('*') if p.is_file()}
            v.compute(plan, lambda _: None, root=out, prior=prior, phase=phase)
            self.assertEqual(before, {p.relative_to(out).as_posix(): v.filehash(p) for p in out.rglob('*') if p.is_file()})
            (prior/'worlds/000/FITS.json').write_bytes(b'[]\n')
            with self.assertRaisesRegex(ValueError, 'bytes changed'):
                v.compute(plan, lambda _: None, root=root/'refused', prior=prior, phase=phase)
            self.assertFalse((root/'refused/SUMMARY.json').exists())
            self.assertFalse((root/'refused/worlds/001').exists())

    def test_full_handler_completion_and_failure_release_only_own_lease(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            root = repo/'attempt'
            (repo/'results').mkdir()
            grid = [dict(effect='offset', delta=0., seed=1, replicate=0)]
            plan = dict(pins={}, grid=grid, runtime=v.original.runtime(), max_wall_seconds=60,
                        max_resource_wait_seconds=60, max_output_bytes=100_000_000)
            v.freeze(root/'PLAN.json', plan)
            real_freeze = v.freeze
            def monitored_freeze(path, value):
                result = real_freeze(path, value)
                if path.name == 'OWNER.json':
                    real_freeze(root/'MONITOR_READY.json', dict(owner_sha256=v.filehash(path)))
                return result
            def fake_compute(plan, guard, **kwargs):
                guard(dict(world=0))
                real_freeze(root/'SUMMARY.json', dict(all_worlds_complete=True))
            with patch.object(v, 'ROOT', root), patch.object(v, 'REPO', repo), patch.object(v.original, 'GRID', grid), \
                 patch.object(v, 'limits'), patch.object(v, 'prior_terminal'), patch.object(v, 'resource_snapshot', return_value={}), \
                 patch.object(v, 'require_resources'), patch.object(v, 'native_identity', return_value=dict(pid=1)), \
                 patch.object(v, 'freeze', side_effect=monitored_freeze), patch.object(v, 'compute', side_effect=fake_compute):
                v.run()
                self.assertEqual(v.read(root/'COMPLETE.json')['status'], 'COMPLETE')
                self.assertFalse((repo/'results/.cpu.lock').exists())
                with self.assertRaises(FileExistsError): v.run()
            # A second isolated attempt exercises the actual exception handler.
            failed = repo/'failed'
            v.freeze(failed/'PLAN.json', plan)
            root = failed
            def fail_compute(*args, **kwargs): raise RuntimeError('fixture failure')
            with patch.object(v, 'ROOT', root), patch.object(v, 'REPO', repo), patch.object(v.original, 'GRID', grid), \
                 patch.object(v, 'limits'), patch.object(v, 'prior_terminal'), patch.object(v, 'resource_snapshot', return_value={}), \
                 patch.object(v, 'require_resources'), patch.object(v, 'native_identity', return_value=dict(pid=1)), \
                 patch.object(v, 'freeze', side_effect=monitored_freeze), patch.object(v, 'compute', side_effect=fail_compute):
                with self.assertRaisesRegex(RuntimeError, 'fixture failure'): v.run()
                self.assertEqual(v.read(root/'FAILED.json')['reason'], 'fixture failure')
                self.assertFalse((root/'COMPLETE.json').exists())
                self.assertFalse((repo/'results/.cpu.lock').exists())


if __name__ == '__main__':
    unittest.main()
