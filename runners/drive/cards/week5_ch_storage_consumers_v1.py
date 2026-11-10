"""Explicit codec integration for unchanged bounded CH merge/sample/history.

Merged histories keep SLCHZ1 storage. The positions gzip and projected player
history JSON are unchanged plain logical outputs, usable by existing scorers
and CH2--CH6 mathematics. Original SQL/scientific code stays byte-identical.
"""
from . import week5_ch_source as source
from . import week5_ch_merge_bounded as merge
from . import week5_ch_sample_bounded as sample
from . import week5_ch_history_index_bounded as history
from . import week5_ch_history_index as history_original
from . import week5_ch_storage_v1 as storage


def run(operation, output, inputs, config):
    route = config.get('phase')
    handlers = {'merge':merge, 'sample':sample, 'history_index':history}
    if route not in handlers:
        raise ValueError('Explicit reviewed compressed-source consumer route required')
    paths = [spec['path'] for spec in inputs.values() if isinstance(spec, dict) and 'path' in spec]
    with storage.bridge([source, merge, sample, history, history_original], output, paths):
        return getattr(handlers[route], operation)(output, inputs, config)


def execute(output, inputs, config):
    return run('execute', output, inputs, config)


def verify(output, inputs, config):
    return run('verify', output, inputs, config)
