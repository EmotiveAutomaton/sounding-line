"""Package the constructed rehearsal; does not launch or access a source.

DESIGN CHECK: LESSONS 2-5. Exact original SM0 bytes are embedded unchanged.
A new destination and fixed source digest are mandatory; no overwrite or upload.
"""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
source = (HERE/'run.py').read_text('utf8')
assert hashlib.sha256(source.encode('utf8')).hexdigest() == '29d34d96e4ac85611a26081566d35e8274ee361ae0b1c5bbf68f02cb4ec7e449'
fixture = (HERE/'fixture.py').read_text('utf8')
payload = 'PROBE_SOURCE = '+repr(source)+'\n'+fixture
compile(payload, '<sealed-rehearsal>', 'exec')
destination = Path(sys.argv[1]); destination.mkdir(parents=True, exist_ok=False)
(destination/'run.py').write_bytes(payload.encode('utf8'))
manifest = dict(constructed_only=True,expected_cases=22,max_cpu_seconds=600,
    max_wall_seconds=600,numerical_threads=2,private_source_reads=0,
    source_sha256=hashlib.sha256(source.encode('utf8')).hexdigest(),
    fixture_sha256=hashlib.sha256(fixture.encode('utf8')).hexdigest(),
    job_sha256=hashlib.sha256(payload.encode('utf8')).hexdigest())
(destination/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
print(json.dumps(manifest))
