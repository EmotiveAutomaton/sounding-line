"""Constructed metadata chains cannot authenticate fabricated EV content."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from runners.drive.engine_sources import Sources
from runners.drive.cards.timing_census import read, filehash
from runners.drive.cards.timing_text import replay_words


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf8')
    path.write_bytes(gzip.compress(data, mtime=0) if path.suffix == '.gz' else data)


def seal(i):
    root = Path(i['repo_root'])
    for prefix, record in [('session', root/'p2/s.json'), ('p5', root/'p5/output/s.json.gz'),
                           ('p6', root/'p6/output/s.json.gz')]:
        save(i[prefix+'_index'], [dict(session='s', writer='w', file=record.name, sha256=filehash(record))])
    save(i['foundation_plan'], dict(pins={Path(i[k]).relative_to(root).as_posix(): filehash(i[k])
        for k in ('prepared_sessions', 'raw_roster', 'source_pins')}))
    save(i['foundation_complete'], dict(status='COMPLETE', plan_sha256=filehash(i['foundation_plan']),
        outputs={'SESSION_INDEX.json': filehash(i['session_index'])}))
    p6_binding = Path(i['p6_index']).parent/'P6_BINDINGS.json'
    save(p6_binding, dict(config={}, repo_root=str(root), index_sha256=filehash(i['p6_index']),
        inputs={k: filehash(i[k]) for k in ('foundation_complete', 'prepared_sessions', 'raw_roster', 'session_index')}))
    p5_binding = Path(i['p5_index']).parent/'INPUTS.json'
    aliases = dict(p2_index='session_index', sessions='prepared_sessions', source_roster='raw_roster')
    save(p5_binding, dict(paths={**{k:i[v] for k,v in aliases.items()}, 'source_root':str(root)},
        sha256={k:filehash(i[v]) for k,v in aliases.items()}, config=dict(expected_sessions=1)))
    for name, binding in [('p5', p5_binding), ('p6', p6_binding)]:
        base = Path(i[name+'_completion']).parent
        save(i[name+'_completion'], dict(status='COMPLETE', fresh_process_verified=True,
            outputs={p.relative_to(base).as_posix(): filehash(p) for p in (Path(i[name+'_index']), binding)}))


def fixture(root):
    root = root.resolve()
    events = [dict(eventName='system-initialize', eventTimestamp=0, currentDoc=''),
        dict(eventName='text-insert', eventTimestamp=100, eventSource='user', textDelta=dict(ops=[dict(insert='cat ')])),
        dict(eventName='text-delete', eventTimestamp=200, eventSource='user', textDelta=dict(ops=[dict(delete=3), dict(insert='dog')]))]
    raw = root/'raw/s.jsonl'; raw.parent.mkdir(parents=True)
    raw.write_text('\n'.join(json.dumps(e) for e in events), encoding='utf8')
    replay = replay_words(events)
    identity = dict(session='s', writer='w', prompt='p')
    timing = dict(timestamp=0, end_at=1)
    save(root/'p2/s.json', dict(**identity, final_document=replay['final_document'], source_sha256=filehash(raw)))
    save(root/'p6/output/s.json.gz', dict(**identity, **timing, words=[dict(w,
        population_probability=.5, population_surprisal=.693147, population_log_frequency=-1.) for w in replay['words']]))
    save(root/'p5/output/s.json.gz', dict(**identity, **timing, source_sha256=filehash(raw),
        p2_sha256=filehash(root/'p2/s.json'), final_sha256=hashlib.sha256(b'dog ').hexdigest(),
        sentences=[dict(start_codepoint=0, end_codepoint=3, text='dog', origin_counts={'typed':3}, writer_typed=True)]))
    i = dict(repo_root=str(root), foundation_complete=str(root/'p2/COMPLETE.json'), foundation_plan=str(root/'p2/PLAN.json'),
        session_index=str(root/'p2/SESSION_INDEX.json'), prepared_sessions=str(root/'SESSIONS.json'),
        raw_roster=str(root/'ROSTER.json'), source_pins=str(root/'PINS.json'),
        p5_index=str(root/'p5/output/SESSION_INDEX.json'), p5_completion=str(root/'p5/COMPLETE.json'),
        p6_index=str(root/'p6/output/P6_INDEX.json'), p6_completion=str(root/'p6/COMPLETE.json'))
    save(i['prepared_sessions'], [dict(**identity, **timing)])
    save(i['raw_roster'], [dict(session='s', path='raw/s.jsonl', source_sha256=filehash(raw)),
        dict(session='upstream-only', path='unused.jsonl', source_sha256='0'*64)])
    save(i['source_pins'], {'raw/s.jsonl': filehash(raw)})
    seal(i)
    return i


def test_exact_source_and_fresh_serialized_replay(tmp_path):
    i = fixture(tmp_path/'source')
    source = Sources(i, expected_sessions=1)
    assert source.population['upstream_only_session_ids'] == ['upstream-only']
    value = source.session('s')
    assert [r['final_codepoints'] for r in value['occurrences']] == [None, [0,3]]
    assert value['document']['text'] == 'dog '
    manifest = tmp_path/'inputs.json'; save(manifest, i)
    code = ('import json,sys;from runners.drive.engine_sources import Sources;'
        'print(json.dumps(Sources(json.load(open(sys.argv[1])),expected_sessions=1).session("s"),sort_keys=True))')
    env = dict(os.environ, PYTHONHASHSEED='917')
    actual = subprocess.check_output([sys.executable, '-B', '-c', code, str(manifest)], env=env, text=True)
    assert json.loads(actual) == value


def test_raw_mutation_refused(tmp_path):
    i = fixture(tmp_path/'source'); source = Sources(i, expected_sessions=1)
    path = Path(i['repo_root'])/'raw/s.jsonl'
    path.write_text(path.read_text().replace('cat', 'rat'))
    with pytest.raises(ValueError, match='raw EV source differs'):
        source.session('s')


@pytest.mark.parametrize('mutation,match', [('provenance','P5 source partition'),
    ('identity','source identity'), ('chronology','source chronology'), ('occurrence','P6 occurrence fields')])
def test_resealed_false_derived_content_refused(tmp_path, mutation, match):
    i = fixture(tmp_path/'source')
    target = Path(i['repo_root'])/('p6/output/s.json.gz' if mutation=='occurrence' else 'p5/output/s.json.gz')
    value = json.loads(gzip.decompress(target.read_bytes()))
    if mutation == 'provenance': value['sentences'][0]['origin_counts'] = {'accepted':3}
    elif mutation == 'identity': value['writer'] = 'other'
    elif mutation == 'chronology': value['end_at'] = 2
    else: value['words'][0]['revised'] = False
    save(target,value); seal(i)
    with pytest.raises(ValueError, match=match): Sources(i,expected_sessions=1).session('s')


def test_wrong_bound_population_and_metadata_refused(tmp_path):
    i = fixture(tmp_path/'source')
    with pytest.raises(ValueError, match='frozen count'): Sources(i)
    path = Path(i['p5_index']).parent/'INPUTS.json'
    value = read(path); value['sha256']['sessions'] = '0'*64; save(path,value)
    complete = read(i['p5_completion']); complete['outputs']['output/INPUTS.json'] = filehash(path)
    save(i['p5_completion'], complete)
    with pytest.raises(ValueError, match='P5 source metadata'): Sources(i,expected_sessions=1)


def test_incomplete_terminal_and_missing_p5_unit_refused(tmp_path):
    i = fixture(tmp_path/'source')
    complete = read(i['p5_completion']); complete['fresh_process_verified'] = False; save(i['p5_completion'],complete)
    with pytest.raises(ValueError, match='dependency not verified'): Sources(i,expected_sessions=1)
    seal(i); save(i['p5_index'], [])
    complete = read(i['p5_completion']); complete['outputs']['output/SESSION_INDEX.json'] = filehash(i['p5_index'])
    save(i['p5_completion'],complete)
    with pytest.raises(ValueError, match='empty or duplicate'): Sources(i,expected_sessions=1)
