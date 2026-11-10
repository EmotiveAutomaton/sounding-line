"""Packet section 0.6 single-author texture, retaining complete GO1 readers.

DESIGN CHECK: remove multi-author documents before fixed roster allocation.
Never infer authorship from absent flags or reuse the original candidate bank.
"""
from pathlib import Path
from types import FunctionType
import json
from . import week5_go1_pipeline_v2 as base


def scope(inputs,config):
    if config.get('version') or config.get('field','motivation')!='motivation' or config.get('rest','rest')!='rest':
        raise ValueError('Single-author texture uses current Motivation and remaining text')
    rows=json.loads(Path(inputs['documents']).read_text('utf8'))['documents']
    if any(not isinstance(r.get('multi_author'),bool) for r in rows):
        raise ValueError('Explicit source multi-author flags required')
    included=[r for r in rows if not r['multi_author']]
    eligible=[r for r in included if r.get('motivation','').strip() and r.get('rest','').strip()]
    return eligible,dict(source_documents=len(rows),multi_author_excluded=len(rows)-len(included),
        single_author_documents=len(included),eligible_documents=len(eligible),
        eligible_author_clusters=len({r['author'] for r in eligible}),
        scope='current pinned single-author proposals; Motivation retrieval; descriptive texture')


def prepared_rows(inputs,config):
    rows,_=scope(inputs,config)
    return rows,base.core.allocate(rows,config.get('distractors',49))


def execute(output,inputs,config):
    _,exposure=scope(inputs,config)
    config=dict(config,cell='GO1.single-author')
    operation=FunctionType(base.execute.__code__,dict(base.execute.__globals__,prepared_rows=prepared_rows))
    value=operation(Path(output),inputs,config)
    if value.get('status')=='yielded':return value
    value.update(single_author_texture=True,source_exposure=exposure)
    name='SCORED.json' if config['phase']=='GO1-score' and value.get('status')!='unsupported' else 'RESULT.json'
    base.core.write(Path(output)/name,value)
    return value


def verify(output,inputs,config):
    operation=FunctionType(base.verify.__code__,dict(base.verify.__globals__,execute=execute))
    return operation(Path(output),inputs,config)
