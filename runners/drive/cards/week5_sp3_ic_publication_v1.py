"""SP3 sensitivity with the already-qualified child-local JSON publisher.

DESIGN CHECK: LESSONS 3-5 and CONTROLS 6-7 reread. The null and signed
alternatives retain every original world, draw, source and gate. Publication
must preserve exact numerical arrays; changed or incomplete banks fail closed.
No live source is edited. The named writer is restored even on an exception.
"""
from pathlib import Path
import json
from . import week5_sp3_ic as original
from . import week5_qualification_io as publication
from .week5_sp3_ic_fixture_v2 import world_bank


def contract(inputs, config):
    if set(inputs) != {'data'}:
        raise ValueError('Exact SP3 sensitivity data input required')
    if set(config) - {'phase', 'draws', 'worlds', 'max_wall_seconds'} or config.get('phase') != 'SP3.ic':
        raise ValueError('Registered SP3 sensitivity configuration required')
    if config.get('draws', 2000) != 2000 or config.get('worlds', 100) != 100:
        raise ValueError('Full fixed SP3 sensitivity grid required')


def execute(output, inputs, config):
    contract(inputs, config)
    world_bank(output)
    with publication.publication([(original.parent, 'write')]):
        result = original.execute(output, inputs, config)
    world_bank(output, complete=result.get('status') == 'ok')
    return result


def verify(output, inputs, config):
    contract(inputs, config)
    output = Path(output)
    saved = json.loads((output / 'RESULT.json').read_text('utf8'))
    complete = saved.get('status') == 'ok'
    world_bank(output, complete=complete)
    world_bank(output / 'independent-replay')
    with publication.publication([(original.parent, 'write')]):
        result = original.verify(output, inputs, config)
    world_bank(output / 'independent-replay', complete=complete and result.get('verified') is True)
    return result
