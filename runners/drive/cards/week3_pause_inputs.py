"""PP1 inputs from fully replayed, frozen WB1 event extraction.

DESIGN CHECK: LESSONS 3-5, timing exclusions and Week3 PP1 read 2026-10-25.
This preparation never estimates a gradient. All canonical sessions remain in
the census; absent locations and missing within-word support are explicit. The
source archive's domain supplies genre, not the prepared metadata's empty field.
"""
from collections import Counter, defaultdict
from pathlib import Path

from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal
from .week3_pieces_coverage import authenticated

LOCATIONS = ('within_word', 'before_word', 'before_sentence', 'before_paragraph', 'before_revision')


def load(inputs, config):
    if set(inputs) != {'preparation_complete', 'preparation_index', 'preparation_result', 'raw_roster'}:
        raise ValueError('exact PP1 event source inputs required')
    if set(config) != {'mode', 'expected_sessions', 'seed'} or config['mode'] not in {'corpus', 'constructed'} or config['seed'] != 20261026:
        raise ValueError('frozen PP1 source configuration required')
    if config['mode'] == 'corpus' and config['expected_sessions'] != 1399:
        raise ValueError('full canonical PP1 population required')
    for key in ('preparation_index', 'preparation_result'):
        authenticated(inputs['preparation_complete'], inputs[key])
    result = read(inputs['preparation_result'])
    paths = result['source_bindings']
    if paths.get(str(Path(inputs['raw_roster']).resolve())) != filehash(inputs['raw_roster']):
        raise ValueError('genre roster is not the original authenticated source')
    for path, digest in paths.items():
        if filehash(path) != digest:
            raise ValueError('original PP1 source changed')
    roster_list = read(inputs['raw_roster'])
    roster = {r['session']: r for r in roster_list}
    if len(roster) != len(roster_list):
        raise ValueError('duplicate raw session metadata')
    index_path = Path(inputs['preparation_index']).resolve()
    rows = []
    for item in sorted(read(index_path), key=lambda r: r['session']):
        path = (index_path.parent / item['file']).resolve()
        path.relative_to(index_path.parent)
        if filehash(path) != item['sha256']:
            raise ValueError('prepared PP1 session changed')
        row = gzread(path)
        meta = roster[row['session']]
        if (row['session'], row['writer'], row['prompt'], row['timestamp']) != (item['session'], item['writer'], meta['prompt'], meta['timestamp']):
            raise ValueError('PP1 identity join differs')
        if meta['writer'] != row['writer'] or meta['domain'] not in {'creative', 'argumentative'}:
            raise ValueError('PP1 writer/genre metadata invalid')
        kept = [dict(x) for x in row['intervals'] if x['location'] in LOCATIONS]
        if any(x['interval_seconds'] <= 0 or x['target'] not in {'single_character_insert', 'deletion'} for x in kept):
            raise ValueError('PP1 intervals invalid')
        rows.append(dict(session=row['session'], writer=row['writer'], prompt=row['prompt'], timestamp=row['timestamp'], genre=meta['domain'],
                         intervals=kept, source_exclusions=row['interval_exclusions'], separator_intervals=sum(x['location']=='separator' for x in row['intervals'])))
    if len(rows) != config['expected_sessions'] or len({r['session'] for r in rows}) != len(rows):
        raise ValueError('canonical PP1 session census changed')
    by_writer = defaultdict(list)
    for row in rows:
        by_writer[row['writer']].append(row)
    for sessions in by_writer.values():
        for order, row in enumerate(sorted(sessions, key=lambda r: (r['timestamp'], r['session']))):
            row['session_order'] = order
    summary = dict(card='PP1-inputs', scientific_result=False, sessions=len(rows), writers=len(by_writer),
                   genres={g:dict(sessions=sum(r['genre']==g for r in rows),
                                  intervals=sum(len(r['intervals']) for r in rows if r['genre']==g),
                                  locations=dict(Counter(x['location'] for r in rows if r['genre']==g for x in r['intervals'])))
                           for g in ('creative', 'argumentative')},
                   interval_scope='writer single-character insert endpoints, plus separately tagged deletion targets; suggestion-touching and multi-insert intervals excluded by authenticated source replay',
                   within_word_missing_sessions=[r['session'] for r in rows if not any(x['location']=='within_word' for x in r['intervals'])])
    bindings = dict(config=config, inputs={k:filehash(v) for k,v in inputs.items()}, original_source_bindings=paths)
    return rows, summary, bindings


def run(output, inputs, config, verify=False):
    output = Path(output)
    rows, summary, bindings = load(inputs, config)
    if verify:
        if gzread(output/'PP1_INTERVALS.json.gz') != rows or read(output/'PP1_INPUT_RESULT.json') != summary or read(output/'PP1_INPUT_BINDING.json') != bindings:
            raise ValueError('PP1 complete source replay differs')
        return dict(verified=True, scientific_admission=False)
    gzip_equal(output/'PP1_INTERVALS.json.gz', rows)
    write_equal(output/'PP1_INPUT_RESULT.json', summary)
    write_equal(output/'PP1_INPUT_BINDING.json', bindings)
    return summary


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
