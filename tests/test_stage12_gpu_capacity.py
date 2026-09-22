"""Regression for the actual resident-weight double reservation; no GPU calls."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from runners.stage12 import local_api as api


class Capacity(unittest.TestCase):
    profile=dict(context=8192,model_memory_MiB=7000,free_buffer_MiB=768)

    def resident(self,**changes):
        return dict(dict(name=api.MODEL,digest=api.MODEL_DIGEST,size=5729167604,
            size_vram=5729167604,context_length=8192,
            expires_at=(datetime.now(timezone.utc)+timedelta(minutes=2)).isoformat()),**changes)

    def inspect(self,models,free=1953,temp=56):
        def inventory(path,**kwargs):
            self.assertNotEqual(path,'/api/chat')
            return {'/api/ps':dict(models=models),'/api/tags':dict(models=[dict(name=api.MODEL,digest=api.MODEL_DIGEST)]),
                    '/api/version':dict(version='test')}[path]
        with patch.object(api,'snapshot',return_value=dict(free_MiB=free,temperature_C=temp)),patch.object(api,'api',side_effect=inventory):
            return api.readiness(self.profile)

    def test_recorded_residency_does_not_reserve_loaded_weights_twice(self):
        old_required=7000-5729167604/2**20+768
        self.assertGreater(old_required,2238)  # the recorded false refusal
        result=self.inspect([self.resident()])
        self.assertTrue(result['ready'])
        self.assertEqual(result['additional_required_MiB'],768)
        self.assertEqual(result['capacity_mode'],'fully-resident')

    def test_cold_and_loaded_boundaries_keep_safety_buffer(self):
        for models,threshold in [([],7768),([self.resident()],768)]:
            self.assertFalse(self.inspect(models,threshold-1)['ready'])
            self.assertTrue(self.inspect(models,threshold)['ready'])
            self.assertFalse(self.inspect(models,threshold,79)['ready'])

    def test_unsafe_or_unknown_residency_never_receives_credit(self):
        for mutation in (dict(size_vram=1),dict(size_vram=0),dict(size=0),dict(size_vram=-1),dict(size_vram=True),
            dict(size_vram='5729167604'),dict(size_vram=float('nan')),dict(size_vram=5729167605),
            dict(context_length=4096),dict(context_length=None),dict(digest='other'),dict(name='other'),
            dict(expires_at='invalid'),dict(expires_at=None),dict(expires_at='2020-01-01T00:00:00+00:00'),
            dict(expires_at=(datetime.now(timezone.utc)+timedelta(seconds=20)).isoformat())):
            with self.subTest(mutation=mutation):
                result=self.inspect([self.resident(**mutation)],free=10000)
                self.assertFalse(result['ready'])
                self.assertEqual(result['additional_required_MiB'],7768)
        self.assertFalse(self.inspect([self.resident(),self.resident()],10000)['ready'])
        with self.assertRaises(ValueError):self.inspect(None)

    def test_driver_reserved_memory_is_not_free(self):
        with patch.object(api,'native_command',return_value=b'GPU, 12282, 10044, 1953, 285, 20, 56, 90') as cmd:
            result=api.snapshot()
        self.assertEqual(result['free_MiB'],1953)
        self.assertEqual(result['reserved_MiB'],285)
        self.assertIn('memory.free,memory.reserved',cmd.call_args.args[0][1])
        for row in (b'GPU, 12282, 10044, nan, 285, 20, 56, 90',b'GPU, 12282, 10044, -1, 285, 20, 56, 90',b'GPU, 12282, 10044, N/A, 285, 20, 56, 90'):
            with patch.object(api,'native_command',return_value=row),self.assertRaises(ValueError):api.snapshot()


if __name__=='__main__':unittest.main()
