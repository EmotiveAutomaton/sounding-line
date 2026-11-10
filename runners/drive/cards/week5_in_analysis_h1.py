"""IN analysis admission guard, retaining frozen estimators and all comparisons.

DESIGN CHECK: LESSONS 2–5; CONTROLS 6–7. The known-answer successor fixture
exercises actual IN1–3 handlers. Under either sign or the null, fewer than
twenty participant clusters is descriptive, never a directional gate.
"""
import json
from pathlib import Path
from . import week5_in as original


def execute(output: Path, inputs: dict, config: dict) -> dict:
    result = original.execute(output, inputs, config)
    if config.get('phase') in ('IN2','IN3') and result.get('status') == 'ok' and result['clusters'] < 20:
        result['outcome'] = 'below floor, descriptive'
        original.write_json(output/'RESULT.json',result)
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    if config.get('phase') not in ('IN2','IN3'):
        return original.verify(output,inputs,config)
    expected=json.loads((output/'RESULT.json').read_text('utf8'))
    result=execute(output/'independent-replay',inputs,config)
    if result != expected:
        raise ValueError('complete IN analysis replay mismatch')
    return {'verified':True,'phase':config['phase'],'full_replay':True,'cluster_floor_enforced':True}
