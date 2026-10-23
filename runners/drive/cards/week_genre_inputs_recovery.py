"""GEN1 source join recovery; preserve the exact completed PMAP population.

DESIGN CHECK: LESSONS 2-5, CONTROLS 1-7 read 2026-10-22. Both signal and null
inputs retain identical completed-PMAP/word-ledger populations. The larger raw
archive must cover all admitted sessions, but extras do not enter the study.
Changed, missing, duplicate or mismatched primary records fail closed. Matching
and support policy remain byte-identical in the original component. No outcome
or feature extraction is introduced. Native fixture includes upstream extras.
"""
from pathlib import Path

from . import week_genre_inputs as base
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal
from .timing_pmap_source import completed, indexed, bound_record

CONFIG = base.CONFIG


def load(inputs):
    if set(inputs) != {'pmap_completion'}:
        raise ValueError('Exact completed PMAP input required')
    complete = Path(inputs['pmap_completion']).resolve()
    receipt = completed(complete, complete.parent/'PLAN.json')
    p = read(complete.parent/'PLAN.json')['inputs']
    fp = read(p['foundation_plan']); foundation = read(p['foundation_complete'])
    if foundation.get('status') != 'COMPLETE' or foundation['plan_sha256'] != filehash(p['foundation_plan']):
        raise ValueError('Foundation plan changed')
    root = Path(p['repo_root']).resolve(); raw_roster = Path(p['raw_roster']).resolve()
    if fp['pins'].get(raw_roster.relative_to(root).as_posix()) != filehash(raw_roster):
        raise ValueError('Genre roster changed')
    completed(p['p6_completion'], p['p6_index'])
    roster, words = indexed(raw_roster), indexed(p['p6_index'])
    names = sorted(n for n in receipt['outputs'] if n.startswith('output/sessions/') and n.endswith('.json.gz'))
    if not names:
        raise ValueError('Completed PMAP population absent')
    primary_path = complete.parent/'output/PRIMARY.json'
    completed(complete, primary_path)
    primary, source_files = {}, []
    for name in names:
        path = (complete.parent/name).resolve(); path.relative_to(complete.parent)
        completed(complete, path); row = gzread(path)
        if row['session'] in primary:
            raise ValueError('Duplicate completed PMAP session')
        primary[row['session']] = row
        source_files.append(path)
    if read(primary_path)['source_audit']['sessions'] != len(primary):
        raise ValueError('Completed PMAP population count differs')
    if primary.keys() != words.keys() or not primary.keys() <= roster.keys():
        raise ValueError('Exact PMAP/word population equality and raw coverage required')
    rows = []
    fields = ('session', 'writer', 'prompt', 'timestamp')
    for sid, meta in sorted(primary.items()):
        row = bound_record(p['p6_index'], words[sid])
        if tuple(row[k] for k in fields) != tuple(meta[k] for k in fields) or tuple(
                row[k] for k in fields) != tuple(roster[sid][k] for k in fields):
            raise ValueError('Genre/PMAP/word identity mismatch')
        rows.append(dict(row, genre=roster[sid]['domain']))
    paths = [complete, complete.parent/'PLAN.json', Path(p['foundation_complete']),
             Path(p['foundation_plan']), raw_roster, Path(p['p6_completion']), Path(p['p6_index']), primary_path]+source_files
    population = dict(primary_sessions=len(primary), raw_roster_sessions=len(roster),
        upstream_only_sessions=sorted(roster.keys()-primary.keys()),
        policy='Exact completed PMAP/P6 equality; raw roster covers every primary; upstream extras never enter matching')
    return rows, {str(path.resolve()): filehash(path) for path in paths}, population


def run(output, inputs, config, verify=False):
    output = Path(output)
    rows, bindings, population = load(inputs)
    summary, manifest = base.match(rows, config)
    values = {'SUPPORT.json': summary, 'BINDINGS.json': bindings, 'SOURCE_POPULATION.json': population}
    if verify:
        if any(read(output/name) != value for name, value in values.items()) or gzread(output/'MATCHES.json.gz') != manifest:
            raise ValueError('GEN1 matched input recovery replay differs')
        return dict(verified=True, scientific_admission=False, exact_primary_population=True)
    output.mkdir(parents=True, exist_ok=True)
    for name, value in values.items(): write_equal(output/name, value)
    gzip_equal(output/'MATCHES.json.gz', manifest)
    return dict(status='COMPLETE_INPUT_MATCHING', scientific_admission=False, exact_primary_population=True)


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, verify=True)
