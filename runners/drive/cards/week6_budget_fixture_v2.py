"""Literal-only checkpoint fixture for the v1 to v2 budget transition.

DESIGN CHECK: LESSONS 3-5. The immutable payload is [2, 3, 5]; independent
verification must recover ten. Operational quanta never change the payload.
No research source or scientific parameter is accepted.
"""
import json
from pathlib import Path


def execute(output, inputs, config):
    assert inputs == {'literal': [2, 3, 5]}
    assert set(config) == {'max_new_draws'}
    quantum = config['max_new_draws']
    assert type(quantum) is int and quantum > 0
    path = Path(output)/'CHECKPOINT.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = json.loads(path.read_text()) if path.exists() else []
    assert previous == inputs['literal'][:len(previous)]
    rows = inputs['literal'][:min(3, len(previous)+quantum)]
    path.write_bytes((json.dumps(rows)+'\n').encode())
    if len(rows) < 3:
        return {'status': 'yielded', 'fixture_only': True, 'completed': len(rows)}
    return {'sum': sum(rows), 'fixture_only': True}


def verify(output, inputs, config):
    assert inputs == {'literal': [2, 3, 5]}
    rows = json.loads((Path(output)/'CHECKPOINT.json').read_text())
    assert rows == [2, 3, 5]
    total = 0
    for number in rows:
        total += number
    assert total == 10
    return {'verified': True, 'sum': total, 'fixture_only': True}
