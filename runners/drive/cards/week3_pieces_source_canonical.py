"""Canonical WB1 source successor: isolate mutable action provenance.

DESIGN CHECK: LESSONS 2-5 reviewed 2026-10-26; source fidelity, exact replay
and complete native validation apply. NULL/ALTERNATIVE: every action must end
at its own raw source clock. Shared ordinal lists must not let a merged burst
extend a revision or deletion anchor. Copy each action independently before
the unchanged collapse operation. Require all non-provenance fields, complete
population, writer split and bin edges to equal the prior verified preparation.
Changed clocks or other source semantics refuse; no tolerance is widened.
This repairs a data defect and licenses source inputs only, never a claim.
"""
from contextlib import contextmanager
import copy
from pathlib import Path
import math

from runners.drive.cards import week3_pieces_input as original
from runners.drive.cards.week3_pieces_input_recovery import checked_clock
from runners.drive.cards import week3_pieces_coverage as coverage
from runners.drive.cards.timing_census import read, filehash
from runners.drive.cards.timing_p6 import gzread, write_equal

KEYS={'source_inputs','previous_complete','previous_index','previous_result','previous_split','previous_edges'}


@contextmanager
def isolated_provenance():
    old_clock,old_collapse,old_extract=original.checked_clock,original.collapse_actions,original.extract_session
    def collapse(actions):
        # Copy items separately: deepcopy of the whole list preserves aliases.
        return old_collapse([copy.deepcopy(a) for a in actions])
    def extract(events,timeline):
        result=old_extract(events,timeline)
        clocks=checked_clock(events)
        for action in result['actions']:
            at=action['source_ordinals'][-1]
            if not 0 <= at < len(events) or not math.isclose(action['seconds'],clocks[at],rel_tol=0,abs_tol=1e-7):
                raise ValueError('canonical action anchor differs from source clock')
        return result
    original.checked_clock,original.collapse_actions,original.extract_session=checked_clock,collapse,extract
    try:
        yield
    finally:
        original.checked_clock,original.collapse_actions,original.extract_session=old_clock,old_collapse,old_extract


def run(output,inputs,config,verify=False):
    if set(inputs)!=KEYS:
        raise ValueError('exact canonical predecessor and source inputs required')
    for k in KEYS-{'source_inputs','previous_complete'}:
        coverage.authenticated(inputs['previous_complete'],inputs[k])
    sources=read(inputs['source_inputs'])
    old_result=read(inputs['previous_result'])
    output=Path(output)
    with isolated_provenance():
        result=original.prepare(output,sources,config,verify)
    if result!=old_result:
        raise ValueError('canonical source aggregate changed beyond provenance')
    old_index_path=Path(inputs['previous_index'])
    old_index={r['session']:r for r in read(old_index_path)}
    new_index=read(output/'WB1_INPUT_INDEX.json')
    if set(old_index)!={r['session'] for r in new_index}:
        raise ValueError('canonical source population differs')
    changed_sessions=changed_actions=0
    for item in new_index:
        previous=old_index[item['session']]
        old_path=(old_index_path.parent/previous['file']).resolve()
        old_path.relative_to(old_index_path.parent.resolve())
        if filehash(old_path)!=previous['sha256']:
            raise ValueError('canonical predecessor session changed')
        old=gzread(old_path)
        new=gzread(output/item['file'])
        differences=sum(a['source_ordinals']!=b['source_ordinals'] for a,b in zip(old['actions'],new['actions']))
        changed_sessions+=bool(differences);changed_actions+=differences
        for record in (old,new):
            for action in record['actions']:action.pop('source_ordinals')
        if old!=new:
            raise ValueError('canonical source changed non-provenance semantics')
    for key,name in [('previous_split','WB1_WRITER_SPLIT.json'),('previous_edges','WB1_BIN_EDGES.json')]:
        if read(inputs[key])!=read(output/name):raise ValueError('canonical frozen split or bins changed')
    correction=dict(status='canonical_source_prepared',sessions=result['sessions'],changed_sessions=changed_sessions,
        changed_actions=changed_actions,only_source_ordinals_changed=True,all_raw_anchor_clocks_checked=True,
        original_population_split_bins_preserved=True,scientific_result=False)
    if verify:
        if read(output/'CANONICAL_SOURCE_CHANGE.json')!=correction:raise ValueError('canonical correction replay differs')
    else:write_equal(output/'CANONICAL_SOURCE_CHANGE.json',correction)
    return correction


def execute(output,inputs,config):return run(output,inputs,config)


def verify(output,inputs,config):
    result=run(output,inputs,config,True)
    return dict(verified=True,complete_source_replay=True,only_source_ordinals_changed=True,
        sessions=result['sessions'],scientific_result=False)
