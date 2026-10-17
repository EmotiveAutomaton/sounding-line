import unittest
from runners.drive.gpu_telemetry import Memory,reading,compare,checked

class TelemetryTests(unittest.TestCase):
    def memory(self):return Memory(total=12*2**30,reserved=256*2**20,free=8000*2**20+512,used=(12*1024-256-8000)*2**20-512)
    def test_known_units_and_conservative_rounding(self):
        self.assertEqual(reading(self.memory(),60),dict(free_MiB=8000,used_MiB=4032,temperature_C=60))
    def test_error_and_invalid_accounting_refuse(self):
        with self.assertRaises(RuntimeError):checked(13)
        for key,value in [('total',0),('free',13*2**30),('reserved',0)]:
            m=self.memory();setattr(m,key,value)
            with self.assertRaises(ValueError):reading(m,50)
        for t in (0,150):
            with self.assertRaises(ValueError):reading(self.memory(),t)
    def test_mismatch_refuses_but_rounding_passes(self):
        a=dict(uuid='GPU-fixture',free_MiB=8000,used_MiB=4032,temperature_C=60)
        self.assertTrue(compare(a,dict(a,free_MiB=8001),a))
        for key,value in [('uuid','other'),('free_MiB',8100),('used_MiB',4200),('temperature_C',70)]:
            with self.assertRaises(ValueError):compare(a,dict(a,**{key:value}),a)

if __name__=='__main__':unittest.main()
