"""Authenticated, compact views of D20's completed lossless source extraction.

No encoder, fit, raw-event replay, or selected-option identity is used. Fresh
verification reconstructs the original next50-word windows from frozen P6/P2
and checks every retained source row before computing the extension.
"""
from pathlib import Path
import json
import numpy as np
from . import menus_d20 as original
from . import menus_d20_recovery as recovery
from .events_d4_sources import bind_completed
from .menus_io import read, sha256, assert_equal, input_hashes

EXTRA = frozenset(('primary_plan', 'primary_complete', 'primary_summary', 'primary_comparisons'))


def context(inputs):
    if not EXTRA.issubset(inputs):
        raise ValueError('D20 extension missing explicit primary inputs')
    inherited = {k:v for k,v in inputs.items() if k not in EXTRA}
    plan = read(inputs['primary_plan']); summary = read(inputs['primary_summary'])
    root = Path(inputs['primary_plan']).resolve().parent
    if Path(inputs['primary_complete']).resolve() != root/'COMPLETE.json':
        raise ValueError('D20 completion/plan roots differ')
    if plan.get('module') != 'runners.drive.cards.menus_d20_recovery':
        raise ValueError('D20 extension requires completed immutable recovery')
    assert_equal(plan['inputs'], inherited)
    for name in ('primary_plan', 'primary_summary', 'primary_comparisons'):
        bind_completed(inputs['primary_complete'], inputs[name])
    if Path(inputs['primary_summary']).resolve() != root/'output'/'SUMMARY.json':
        raise ValueError('D20 primary summary path differs')
    if Path(inputs['primary_comparisons']).resolve() != root/'output'/'COMPARISONS.json.gz':
        raise ValueError('D20 primary comparisons path differs')
    for name, digest in plan['pins'].items():
        if sha256(name) != digest:
            raise ValueError('D20 completed source pin changed: '+name)
    scientific, binding, _, _ = recovery.context(root/'output', inherited, plan['config'])
    assert_equal(summary['input_hashes'], binding['inputs'])
    assert_equal(summary['config'], plan['config'])
    if summary['primary']['state'] not in ('positive', 'marginal'):
        raise ValueError('D20 registered reliability extension gate is closed')
    assert_equal(summary['primary'], summary['arms']['lexical_observed']['primary'])
    raw, _ = recovery.sealed_bytes(Path(inputs['primary_comparisons']))
    comparisons = json.loads(raw)
    if sha256(inputs['primary_comparisons']) != summary['comparisons_hash']:
        raise ValueError('changed D20 primary comparison hash')
    return dict(data=original.source.load(scientific), binding=binding, root=root,
                complete=read(inputs['primary_complete']), summary=summary, comparisons=comparisons)


def lean(rows):
    result = []
    for row in original.prepared(rows):
        keep = {k:row[k] for k in ('key','writer','session','prompt','half','progress_decile','handling')}
        keep.update(options=[sorted(v) for v in row['content_options']],
                    window=None if row['content_window'] is None else sorted(row['content_window']),
                    vector=None if row['mean_vector'] is None else row['mean_vector'].tolist(),
                    window_vector=row.get('window_vector'))
        result.append(keep)
    return result


def session(ctx, sid):
    path = ctx['root']/'output'/'sessions'/(sid+'.json.gz')
    rel = path.relative_to(ctx['root']).as_posix()
    if ctx['complete']['outputs'].get(rel) != sha256(path):
        raise ValueError('changed completed D20 session')
    bind_completed(ctx['root']/'COMPLETE.json', path.with_suffix('.seal.json'))
    raw, _ = recovery.sealed_bytes(path); saved = json.loads(raw)
    assert_equal(saved['binding'], ctx['binding'])
    recovery.validate_rows(ctx['data'], sid, saved)
    expected = ctx['summary']['session_hashes'].get(path.relative_to(ctx['root']/'output').as_posix())
    if expected != sha256(path):
        raise ValueError('D20 summary session binding differs')
    return lean(saved['rows']), saved['support']
