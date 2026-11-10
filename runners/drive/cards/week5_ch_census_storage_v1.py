"""Lossless history representation around the frozen full census/replay code.

No source eligibility, selection, checkpoint denominator or scientific value
changes. A resumed prefix must already use the explicit storage representation.
Independent verification still parses the whole raw source from ordinal zero
and retains its own complete database, comparing every logical value.
"""
from pathlib import Path
from . import week5_ch_source as original
from . import week5_ch_census_replay as replay
from . import week5_ch_pipeline_checkpoint as ck
from . import week5_ch_storage_v1 as storage


def run(operation, output, inputs, config):
    if config.get('phase') != 'census':
        raise ValueError('Only the original census phase is commissioned here')
    if not {'source', 'salt'} <= set(inputs) or set(inputs)-{'source', 'salt', 'resume_frame'}:
        raise ValueError('Unexpected census input')
    paths = []
    for name, spec in inputs.items():
        path = ck.checked(spec, lambda:ck.require(output))
        if name == 'resume_frame':
            con = storage.connect(path)
            try:
                if con.execute('PRAGMA application_id').fetchone()[0] != storage.APPLICATION_ID:
                    raise ValueError('Original prefix must pass separate new-file storage migration first')
            finally:
                con.close()
            paths.append(path)
    old_compare = replay.compare
    try:
        # Bound decompression memory to a single source row per side here.
        replay.compare = lambda a,b:storage.compare(a,b,replay.TABLES,lambda:ck.require(output))
        with storage.bridge([original, replay], output, paths):
            return getattr(replay, operation)(output, inputs, config)
    finally:
        replay.compare = old_compare


def execute(output, inputs, config):
    return ck.guarded(lambda o,i,c:run('execute',o,i,c), output, inputs, config)


def verify(output, inputs, config):
    return ck.guarded(lambda o,i,c:run('verify',o,i,c), output, inputs, config)
