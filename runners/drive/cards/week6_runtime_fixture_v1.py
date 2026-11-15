"""Literal-only native boundary fixture; never accepts research inputs.

DESIGN CHECK: LESSONS 3-5. Exact arithmetic is known before execution. Fresh
native verification must recover ten, retain cooperative yields, and reject a
fast final output that exceeds the byte ceiling. No statistical interpretation.
"""
import json
import time
from pathlib import Path


def execute(output, inputs, config):
    assert inputs == {'literal': [2, 3, 5]}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output/'CHECKPOINT.json').write_text(json.dumps({'literal': inputs['literal']}), encoding='utf8')
    if config['scenario'] == 'resource_yield':
        deadline = time.monotonic()+10
        while not (output/'YIELD_REQUEST.json').exists():
            if time.monotonic() > deadline:
                raise TimeoutError('Constructed resource request absent')
            time.sleep(.02)
        return {'status': 'yielded', 'fixture_only': True}
    if config['scenario'] == 'execute_yield':
        return {'status': 'yielded', 'fixture_only': True}
    return {'sum': sum(inputs['literal']), 'fixture_only': True}


def verify(output, inputs, config):
    assert inputs == {'literal': [2, 3, 5]}
    rows = json.loads((Path(output)/'CHECKPOINT.json').read_text('utf8'))['literal']
    total = 0
    for number in rows:
        total += number
    assert total == 10 and rows == inputs['literal']
    if config['scenario'] == 'verify_yield':
        return {'status': 'yielded', 'verified': False, 'fixture_only': True}
    if config['scenario'] == 'verify_overcap':
        # Finish between the supervisor's periodic scans.
        time.sleep(.4)
        (Path(output)/'FINAL_BYTES.bin').write_bytes(b'x'*65536)
    return {'verified': True, 'sum': total, 'fixture_only': True}
