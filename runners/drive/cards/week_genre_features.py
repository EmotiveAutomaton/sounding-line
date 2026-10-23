"""GEN1 matched style and occurrence-bound rhythm, without an outcome test.

DESIGN CHECK: LESSONS 2-5 and CONTROLS 1-7 read 2026-10-23. Under null
and alternative, completed word identities and source bytes must match exactly.
Whole-session pairs must reproduce PMAP; partial prefixes retain only selected
token atoms and adjoining whitespace chains, never other words from the same
delta. Missing timing stays missing. Tampering, an incorrect split, or a
provenance disagreement refuses the component, not the scientific hypothesis.
"""
from collections import Counter, defaultdict, deque
import json
import math
from pathlib import Path
import time
import unicodedata

from . import week_genre_inputs_recovery as source
from .week_genre_atoms import raw_pairs
from .timing_census import read, filehash
from .timing_p6 import gzread, gzip_equal, write_equal, progress
from .timing_pmap_source import completed, indexed, bound_record
from runners.stage9.common import digest

CONFIG = dict(card='GEN1-features', schema=1, whitespace='connected_to_retained_token',
              dictionary='original_full_PMAP', timing='logged_delta')


def subset(row, match, audit, pairs):
    words = row['words']; stop = match['token_stop_exclusive']
    if not 0 < stop <= len(words) or match['original_token_count'] != len(words):
        raise ValueError('Invalid retained token prefix')
    retained = words[:stop]
    if [w['index'] for w in retained if w['is_word']] != match['word_indices']:
        raise ValueError('Retained word identity differs')
    if len(audit) != len(words) or [a['index'] for a in audit] != list(range(len(words))):
        raise ValueError('Occurrence audit coverage differs')
    for word, identity in zip(words, audit):
        ids = identity['character_ids']
        text = ''.join(pairs['typed_atoms'][i] for i in ids)
        if len(set(ids)) != len(ids) or len(text) != word['length'] or text.casefold() != word['token']:
            raise ValueError('Exact character identity or spelling differs')
    selected = {i for a in audit[:stop] for i in a['character_ids']}
    # Completion order is not raw event order. Membership is mandatory even
    # when multiple unretained words were inserted before this completion.
    boundary = max(w['completed_ordinal'] for w in retained)
    candidates = [p for p in pairs['pairs'] if p['ordinal'] <= boundary]
    neighbors = defaultdict(set)
    for p in candidates:
        neighbors[p['a']].add(p['b']); neighbors[p['b']].add(p['a'])
    queue = deque(sorted(selected)); allowed = set(selected)
    while queue:
        for other in sorted(neighbors[queue.popleft()]):
            if other not in allowed and pairs['typed_atoms'][other].isspace():
                allowed.add(other); queue.append(other)
    kept = [p for p in candidates if p['a'] in allowed and p['b'] in allowed]
    counts = Counter(w['token'] for w in retained if w['is_word'])
    punctuation = Counter(w['token'] for w in retained if not w['is_word'] and
                          all(unicodedata.category(c).startswith('P') for c in w['token']))
    intervals = defaultdict(list)
    for pair in kept:
        if pair['seconds'] is not None: intervals[pair['pair']].append(pair['seconds'])
    within = [dt for w in retained if w['is_word'] for dt in w['within_intervals']
              if math.isfinite(dt) and dt >= 0]
    onset = [w['pause_seconds'] for w in retained if w['is_word'] and
             w['pause_seconds'] is not None and math.isfinite(w['pause_seconds']) and w['pause_seconds'] >= 0]
    if sum(counts.values()) != match['typed_words']: raise ValueError('Matched exposure changed')
    return dict(**match, word_counts=dict(sorted(counts.items())), punctuation_counts=dict(sorted(punctuation.items())),
        within_intervals=within, onset_intervals=onset,
        bigram_intervals={k:v for k,v in sorted(intervals.items())},
        timing_scope=dict(source_pairs=len(pairs['pairs']), retained_pairs=len(kept),
                          retained_token_atoms=len(selected), retained_whitespace_atoms=len(allowed-selected)))


def load(inputs):
    if set(inputs) != {'matching_completion', 'revision_completion'}:
        raise ValueError('Exact completed GEN1 and revision inputs required')
    mc, rc = (Path(inputs[k]).resolve() for k in ('matching_completion', 'revision_completion'))
    for name in ('PLAN.json', 'output/SUPPORT.json', 'output/MATCHES.json.gz', 'output/BINDINGS.json'):
        completed(mc, mc.parent/name)
    mp = read(mc.parent/'PLAN.json')
    if mp['config'] != source.CONFIG: raise ValueError('Matching configuration differs')
    rows, bindings, _ = source.load(mp['inputs'])
    if bindings != read(mc.parent/'output/BINDINGS.json'): raise ValueError('Matching source binding changed')
    support, matches = source.base.match(rows)
    if support != read(mc.parent/'output/SUPPORT.json') or matches != gzread(mc.parent/'output/MATCHES.json.gz'):
        raise ValueError('Matching reconstruction differs')
    pc = Path(mp['inputs']['pmap_completion']).resolve()
    pp = read(pc.parent/'PLAN.json')['inputs']
    completed(pc, pc.parent/'output/STYLE_DICTIONARY.json')
    for name in ('PLAN.json', 'output/INDEX.json'): completed(rc, rc.parent/name)
    rp = read(rc.parent/'PLAN.json')['inputs']
    if any(rp[k] != pp[k] for k in ('repo_root','p6_index','p6_completion','session_index','raw_roster','source_pins')):
        raise ValueError('Revision and PMAP source identities differ')
    revision = indexed(rc.parent/'output/INDEX.json')
    if set(revision) != {r['session'] for r in rows}: raise ValueError('Revision primary population differs')
    pmap = {}
    receipt = read(pc)
    for name in sorted(receipt['outputs']):
        if name.startswith('output/sessions/') and name.endswith('.json.gz'):
            value = gzread(pc.parent/name); pmap[value['session']] = (name, value)
    return rows, matches, support, pc, pp, pmap, rc, revision


def run(output, inputs, config, verify=False):
    if config != CONFIG: raise ValueError('Frozen feature configuration required')
    started = time.perf_counter(); output = Path(output); output.mkdir(parents=True, exist_ok=True)
    rows, matches, support, pc, pp, pmap, rc, revision = load(inputs)
    words = {r['session']:r for r in rows}; roster = indexed(pp['raw_roster'])
    p2 = indexed(pp['session_index']); pins = read(pp['source_pins']); root = Path(pp['repo_root']).resolve()
    values, hashes = [], {str(Path(v).resolve()):filehash(v) for v in inputs.values()}
    for match in matches:
        sid = match['session']; oldname, old = pmap[sid]; completed(pc, pc.parent/oldname)
        timeline = bound_record(pp['session_index'], p2[sid])
        revpath = rc.parent/'output'/revision[sid]['file']; completed(rc, revpath)
        rev = bound_record(rc.parent/'output/INDEX.json', revision[sid])
        raw = (root/roster[sid]['path']).resolve(); raw.relative_to(root)
        ch = root/'results/phase_2_4_stage_9/private/prepared/coauthor-v2/sessions'/(digest({'coauthor-session':raw.stem})+'.json')
        for path, key in ((raw,'raw'), (ch,'canonical')):
            h = filehash(path)
            if old['source_hashes'][key] != h or pins.get(path.relative_to(root).as_posix()) != h:
                raise ValueError('Original raw/canonical pin differs')
            hashes[str(path)] = h
        if rev['source_hashes'] != {k:old['source_hashes'][k] for k in ('raw','p2','p6')}:
            raise ValueError('Revision occurrence sources differ')
        if any(rev[k] != match[k] or old[k] != match[k] for k in ('session','writer','prompt','timestamp')):
            raise ValueError('Matched source identity differs')
        events = [json.loads(line) for line in raw.read_text(encoding='utf8').splitlines()]
        pairs = raw_pairs(events, timeline, read(ch))
        if any(pairs[k] != old[k] for k in ('bigram_counts','bigram_intervals')):
            raise ValueError('Unrestricted pair replay differs from completed PMAP')
        feature = subset(words[sid], match, rev['revision_events'], pairs)
        feature['tc_timing_mode'] = old['tc_timing_mode']; values.append(feature)
        hashes[str(revpath.resolve())] = filehash(revpath)
        progress(output/'PROGRESS.json', dict(phase='verify-features' if verify else 'features',
                 done=len(values), total=len(matches)))
    summary = dict(card=CONFIG['card'], sessions=len(values), writers=len({r['writer'] for r in values}),
        typed_words=sum(r['typed_words'] for r in values), mode=support['mode'],
        primary_population_supported=support['primary_population_supported'],
        source_pairs=sum(r['timing_scope']['source_pairs'] for r in values),
        retained_pairs=sum(r['timing_scope']['retained_pairs'] for r in values), scientific_admission=False)
    dictionary = read(pc.parent/'output/STYLE_DICTIONARY.json')
    payloads = {'SUMMARY.json':summary, 'DICTIONARY.json':dictionary, 'BINDINGS.json':hashes, 'SUPPORT.json':support}
    for name, value in payloads.items():
        if verify:
            if read(output/name) != value: raise ValueError('Feature replay differs: '+name)
        else: write_equal(output/name, value)
    if verify:
        if gzread(output/'FEATURES.json.gz') != values: raise ValueError('Matched feature replay differs')
    else: gzip_equal(output/'FEATURES.json.gz', values)
    write_equal(output/('VERIFY_TIME.json' if verify else 'EXECUTE_TIME.json'), dict(seconds=time.perf_counter()-started))
    return dict(verified=True, summary=summary) if verify else summary


def execute(output, inputs, config): return run(output, inputs, config)
def verify(output, inputs, config): return run(output, inputs, config, True)
