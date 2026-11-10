"""Bounded GO2 copy-boundary and strict byte-decoding source successor."""
from pathlib import Path
from types import FunctionType
import json
from . import week5_go as core
from . import week5_go_history_bounded as old
from . import week5_go_history_h2 as history

prepare=FunctionType(old.prepare.__code__,dict(old.prepare.__globals__,history=history,__file__=__file__),
                     old.prepare.__name__,old.prepare.__defaults__,old.prepare.__closure__)


def execute(output,inputs,config):
    if config.get('phase')!='prepare':raise ValueError('source-only successor')
    return prepare(Path(output),inputs,config)


def verify(output,inputs,config):
    output=Path(output);actual=prepare(output/'independent-replay',inputs,config)
    if actual.get('status')=='yielded':return {**actual,'verified':False}
    if actual!=json.loads((output/'SOURCE.json').read_text('utf8')):raise ValueError('healed history byte/source replay differs')
    for name in ('anchors.json','first-drafts.json'):
        if core.sha(output/name)!=core.sha(output/'independent-replay'/name):raise ValueError('healed history rows differ')
    return {'verified':True,'complete_same_document_byte_and_source_replay':True}
