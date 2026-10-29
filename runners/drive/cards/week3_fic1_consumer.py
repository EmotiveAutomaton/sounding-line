"""Connect frozen FIC1 reconstruction and scoring on constructed worlds only.

DESIGN CHECK: LESSONS 3-5, CONTROLS 1-7 reread 2026-10-28.
NULL prompt-only records have identical real/context scores and cannot pass.
ALTERNATIVE persistent planted fingerprints must clear both numerical gates.
Fixed support/topology is required on every draw; missing draws cannot be
dropped. This engineering validation does not license human inference or
claim a population false-positive rate, sensitivity or genre-effect power.
"""
from copy import deepcopy
from pathlib import Path

from threadpoolctl import threadpool_limits
from runners.stage14.common import read, filehash, freeze, atomic
from . import week3_fic1_context as context
from . import week3_fic1_scoring as scoring
from . import week3_fic1_prefixes as prefix
from .timing_text import replay_words
from .timing_revision_events import replay_revision_events

WORDS = ('alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf', 'hotel', 'india')
FIXTURE = dict(constructed=True, worlds=['prompt_only', 'writer_plant'])
CONFIG = dict(card='FIC1-consumer-native', schema=1, mode='constructed',
              writers=9, sessions=72, word_limits=[2, 4, 8],
              permutations=1000, bootstrap_draws=2000, seed=20261026)


def world(kind):
    if kind not in FIXTURE['worlds']:
        raise ValueError('unknown constructed world')
    units, rows = [], []
    for wi in range(9):
        for genre in context.gallery.GENRES:
            for pi in range(4):
                factor = wi if kind == 'writer_plant' else pi
                text = (WORDS[factor]+' ')*12
                step = 10+7*factor
                events = [dict(eventName='system-initialize', eventTimestamp=0,
                               eventSource='user', currentDoc='')]
                events += [dict(eventName='text-insert', eventTimestamp=(i+1)*step,
                                eventSource='user', textDelta=dict(ops=[dict(retain=i), dict(insert=c)]))
                           for i, c in enumerate(text)]
                replay = replay_words(events)
                audit = replay_revision_events(events)['revision_events']
                pairs = prefix.base.raw_pairs(events, replay, dict(events=[]))
                words = replay['words']
                wc, pc = prefix.features.counts(words)
                whole = dict(word_counts=wc, punctuation_counts=pc,
                    bigram_counts=pairs['bigram_counts'], bigram_intervals=pairs['bigram_intervals'],
                    tc_timing_mode='logged_delta',
                    within_intervals=[v for w in words if w['is_word'] for v in w['within_intervals']],
                    onset_intervals=[w['pause_seconds'] for w in words
                                     if w['is_word'] and w['pause_seconds'] is not None])
                meta = dict(session=f'w{wi}-{genre}-{pi}', writer=f'w{wi}', genre=genre,
                            half=pi % 2, pair=pi, prompt=f'{genre}-{pi}', timestamp=float(pi))
                u = prefix.unit(meta, words, audit, pairs, whole)
                if u['typed_words'] != 12 or wc != {WORDS[factor]:12}:
                    raise ValueError('constructed word replay differs')
                units.append(u)
                rows.append(dict(**meta, typed_words=12, final_words=12,
                    final_characters=len(text), final_accepted_characters=0,
                    final_counts=dict(word_counts=wc, punctuation_counts=pc)))
    return dict(units=units, rows=rows,
                dictionary=dict(words=list(WORDS), punctuation=['.'], character_bigrams=[]))


def topology(prepared):
    return dict(rosters=prepared['rosters'], writer_folds=prepared['writer_folds'],
                rotations=[{k:r[k] for k in ('donor_fold','donors','probes','galleries')}
                           for r in prepared['rotations']])


def variants(prepared):
    out = []
    for name in sorted(prepared['rosters']):
        for genre in context.gallery.GENRES:
            for adjustment in (['raw', 'length_adjusted', 'length_and_ai_adjusted']
                               if name == 'final_style.full' else
                               ['raw', 'length_adjusted'] if name.endswith('.full') else ['raw']):
                out.append((name, genre, adjustment))
    return out


def key(spec):
    return '|'.join(spec)


def matrix_scores(matrix, writers, adjustment):
    if matrix['writers'] != writers:
        raise ValueError('fixed gallery differs')
    if matrix['state'] != 'prepared':
        return None
    data = matrix[adjustment]
    return scoring.gallery_scores(data['A'], data['B'], writers)


def joined(prepared, spec, arm):
    if arm not in ('observed', 'context'):
        raise ValueError('explicit observed/context arm required')
    name, genre, adjustment = spec
    roster = prepared['rosters'][name]
    if len(roster) < 3:
        return None
    values = {}
    for rotation in prepared['rotations']:
        gallery = rotation['galleries'][name]
        probes = rotation['probes'][name]
        if (set(rotation['donors']) & set(gallery) or
                not set(probes) <= set(gallery) or set(probes) & set(values)):
            raise ValueError('writer rotation is not disjoint or uniquely covered')
        matrix = rotation[arm][name][genre]
        if len(gallery) < 3:
            return None
        scores = matrix_scores(matrix, gallery, adjustment)
        if scores is None:
            return None
        values.update((w, scores[w]) for w in probes)
    if set(values) != set(roster):
        raise ValueError('fixed probe roster is incomplete')
    return {w:values[w] for w in roster}


def evaluate(data, draws=1000, checkpoint=lambda *_:None):
    # Short draws are engineering timing only; compare() still requires 1000.
    if type(draws) is not int or not 1 <= draws <= 1000:
        raise ValueError('bounded positive draw count required')
    prepared = context.prepare(data, CONFIG)
    fixed = deepcopy(topology(prepared))
    specs = variants(prepared)
    observed = {key(s):joined(prepared,s,'observed') for s in specs}
    reference = {key(s):joined(prepared,s,'context') for s in specs}
    banks = {key(s):[] for s in specs}
    for i in range(draws):
        labels = context.role_assignment(data['units'], prepared['writer_folds'], i, CONFIG['seed'])
        draw = context.prepare(data, CONFIG, labels)
        if topology(draw) != fixed:
            raise ValueError('reference changed frozen topology')
        for s in specs:
            banks[key(s)].append(joined(draw,s,'observed'))
        checkpoint(i+1, draws)
    literal = {}
    for s in specs:
        name, genre, adjustment = s
        roster = prepared['rosters'][name]
        literal[key(s)] = (matrix_scores(prepared['literal_leave_writer_out'][name][genre], roster, adjustment)
                          if len(roster) >= 3 else None)
    results = {}
    if draws == 1000:
        for s in specs:
            roster = prepared['rosters'][s[0]]
            results[key(s)] = (scoring.compare(observed[key(s)], reference[key(s)], banks[key(s)], roster)
                              if len(roster) >= 3 else dict(state='unsupported', numerical_pass=False))
    return dict(topology=fixed, observed=observed, context=reference, banks=banks,
                literal_leave_writer_out=literal, literal_licenses_claim=False,
                comparisons=results, completed_draws=draws, human_admission=False)


def known_answer(kind, result):
    if result['completed_draws'] != 1000 or not result['comparisons']:
        raise ValueError('full reference required for known-answer decision')
    if kind == 'prompt_only':
        equal = all(result['observed'][k] == result['context'][k] for k in result['observed'])
        return equal and all(r['state']=='not_detected' and not r['numerical_pass']
                             for r in result['comparisons'].values())
    if kind == 'writer_plant':
        return all(r['numerical_pass'] for r in result['comparisons'].values())
    raise ValueError('unknown constructed world')


def run(output, inputs, config, verification=False):
    if config != CONFIG or set(inputs) != {'fixture'} or read(inputs['fixture']) != FIXTURE:
        raise ValueError('fixed constructed-only consumer; human mode refused')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    gates = {}
    def retain(name, value):
        if verification:
            if read(output/name) != value:
                raise ValueError('independent consumer replay differs: '+name)
        else:
            freeze(output/name, value)
    with threadpool_limits(limits=1):
        for kind in FIXTURE['worlds']:
            def progress(done, total):
                if done == 1 or done % 25 == 0 or done == total:
                    atomic(output/'PROGRESS.json',dict(world=kind,phase='verify' if verification else 'execute',
                                                       draws=done,total=total))
            result = evaluate(world(kind), checkpoint=progress)
            retain(kind+'.json',result)
            gates[kind] = known_answer(kind,result)
    summary = dict(card=config['card'],constructed=True,known_answers=gates,
                   construction_scoring_connected=True,complete_banks=True,
                   all_known_answers_pass=all(gates.values()),
                   full_pipeline_calibration_complete=False,human_identification_computed=False,
                   scientific_admission=False)
    retain('SUMMARY.json',summary)
    retain('BINDING.json',dict(config=config,fixture_sha256=filehash(inputs['fixture'])))
    if not all(gates.values()):
        raise ValueError('constructed consumer known-answer gate failed')
    if verification:
        return dict(verified=True,all_worlds_and_draws_rebuilt=True,constructed=True)
    return dict(status='complete',scientific_admission=False)


def execute(output, inputs, config): return run(output,inputs,config)
def verify(output, inputs, config): return run(output,inputs,config,True)
