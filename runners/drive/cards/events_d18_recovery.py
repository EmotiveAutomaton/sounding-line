"""D18 single engineering recovery; original failed attempt stays immutable.

DESIGN CHECK: LESSONS 3-5. Independent odd/even rates have zero expected
correlation; concordant/reversed writer rankings retain positive/negative signs.
Constant halves, <4 writers or any undefined bootstrap draw are invalid, never
null. Same-origin/session length matching precedes embedding. Partial survival,
system deletion and unmatched spans stay in the census. Prompt-fit is a frozen
embedding proxy; no latent goal, need, fluency or causal interpretation follows.
"""
import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from .events_p5 import read, write, filehash, model_identity, Encoder
from .events_d4 import save, read_sealed, sealed, assert_close
from .events_d4_sources import bind_completed
from .events_d4_stats import stable_seed
from . import events_d18_spans_recovery as spans
from . import events_d18_reuse as reuse
from . import states_v2 as states

CONFIG = dict(threads=2, batch_size=16, bootstrap=2000, seed=20261017,
              length_ratio=1.25, minimum_sessions_per_half=2)
INPUTS = {'p2_index', 'source_roster', 'source_root', 'sessions', 'content_model',
          'content_complete', 'p5_inputs', 'p5_summary', 'p5_completion'} | reuse.EXTRA_INPUTS
FORECAST = 3600


def input_pins(inputs):
    pins = {str(Path(p)): filehash(p) for k, p in inputs.items() if k != 'source_root'}
    identity = read(inputs['content_model']); model_identity(inputs['content_model'])
    pins.update({str(Path(identity['path']) / rel): digest for rel, digest in identity['files'].items()})
    return pins


def source(inputs):
    for key in ('p5_inputs', 'p5_summary'):
        bind_completed(inputs['p5_completion'], inputs[key])
    p5 = read(inputs['p5_inputs'])
    for key in ('p2_index', 'source_roster', 'source_root', 'sessions', 'content_model'):
        if Path(p5['paths'][key]).resolve() != Path(inputs[key]).resolve():
            raise ValueError('P5 source path differs')
        if key != 'source_root' and p5['sha256'][key] != filehash(inputs[key]):
            raise ValueError('P5 source hash differs')
    complete = read(inputs['content_complete'])
    if complete.get('status') != 'COMPLETE' or [v for k, v in complete['outputs'].items()
            if Path(k).name == Path(inputs['content_model']).name] != [filehash(inputs['content_model'])]:
        raise ValueError('CONTENT model completion differs')
    sessions, index, roster = read(inputs['sessions']), read(inputs['p2_index']), read(inputs['source_roster'])
    session_map = {s['session']: s for s in sessions}
    index_map = {r['session']: r for r in index}
    roster_map = {r['session']: r for r in roster}
    if (len(session_map) != len(sessions) or len(index_map) != len(index) or len(roster_map) != len(roster)
            or set(session_map) != set(index_map) or not set(session_map) <= set(roster_map)
            or read(inputs['p5_summary'])['sessions'] != len(index)):
        raise ValueError('D18 cohort coverage differs')
    ordered = []
    for writer in sorted({s['writer'] for s in sessions}):
        own = sorted((s for s in sessions if s['writer'] == writer), key=lambda s: (s['timestamp'], s['session']))
        for order, session in enumerate(own):
            sid = session['session']
            if any(r['writer'] != writer for r in (index_map[sid], roster_map[sid])) or not math.isfinite(session['timestamp']):
                raise ValueError('D18 source writer/chronology differs')
            ordered.append(dict(session=sid, writer=writer, session_order=order,
                p2=index_map[sid], raw=roster_map[sid], prepared_ordinals=[r['ordinal'] for r in session['rows']]))
    return ordered


def source_paths(item, inputs):
    raw_root = Path(inputs['source_root']).resolve()
    p2_root = Path(inputs['p2_index']).resolve().parent
    raw = (raw_root / item['raw']['path']).resolve(); raw.relative_to(raw_root)
    p2 = (p2_root / item['p2']['file']).resolve(); p2.relative_to(p2_root)
    if filehash(raw) != item['raw']['source_sha256'] or filehash(p2) != item['p2']['sha256']:
        raise ValueError('D18 raw/P2 input changed')
    return raw, p2


def extract_session(item, raw, p2, config):
    with raw.open(encoding='utf8') as f:
        events = [json.loads(line) for line in f]
    extracted = spans.extract(events, read(p2), item['prepared_ordinals'])
    pairs, exclusions = spans.match(extracted['spans'], config['length_ratio'])
    prompt_available = bool(extracted['prompt'].strip())
    text_inputs, lookup = [], {}
    def add(text):
        if text not in lookup:
            lookup[text] = len(text_inputs); text_inputs.append(text)
        return lookup[text]
    if prompt_available and pairs:
        add(extracted['prompt'])
        by_key = {s['key']: s for s in extracted['spans']}
        for pair in pairs:
            for kind in ('deleted', 'retained'):
                pair[kind + '_vector'] = add(by_key[pair[kind]]['text'])
    return dict(session=item['session'], writer=item['writer'], session_order=item['session_order'],
        source_sha256=item['raw']['source_sha256'], p2_sha256=item['p2']['sha256'],
        **extracted, pairs=pairs, exclusions=exclusions, prompt_available=prompt_available, text_inputs=text_inputs)


def score_session(unit, vectors, scopes):
    vectors = np.asarray(vectors, float)
    if vectors.shape != (len(unit['text_inputs']), 384) or len(scopes) != len(vectors):
        raise ValueError('D18 encoding coverage differs')
    if len(vectors) and (not np.isfinite(vectors).all() or not np.allclose(np.linalg.norm(vectors, axis=1), 1., atol=1e-5, rtol=0)):
        raise ValueError('D18 invalid encoding')
    for text, scope in zip(unit['text_inputs'], scopes):
        if (scope['used_tokens'] != min(scope['full_tokens'], 254) or scope['full_tokens'] < 0
                or scope['truncated'] != (scope['full_tokens'] > 254) or not 0 <= scope['codepoint_end'] <= len(text)):
            raise ValueError('D18 invalid native token scope')
    pairs = []
    if unit['prompt_available']:
        for pair in unit['pairs']:
            a = float(np.clip(vectors[pair['deleted_vector']] @ vectors[0], -1, 1))
            b = float(np.clip(vectors[pair['retained_vector']] @ vectors[0], -1, 1))
            pairs.append(dict(pair, deleted_prompt_fit=a, retained_prompt_fit=b, sacrifice=int(a < b), tied=bool(a == b)))
    return dict(unit, scored_pairs=pairs, token_scopes=scopes,
        session_exclusion=None if pairs else 'empty supplied prompt/context' if not unit['prompt_available'] else 'no eligible length-matched pair')


def correlation(pairs):
    values = np.asarray(pairs, float)
    if values.ndim != 2 or values.shape[1] != 2 or not np.isfinite(values).all():
        raise ValueError('invalid reliability inputs')
    centered = values - values.mean(axis=0)
    denominator = float(np.prod(np.linalg.norm(centered, axis=0)))
    return float(np.clip((centered[:, 0] @ centered[:, 1]) / denominator, -1, 1)) if denominator > 1e-12 else None


def reliability(pairs, config):
    if len(pairs) < 4:
        return dict(effect=None, ci95=None, state='invalid', writers=len(pairs), reason='fewer than four split-half writers')
    values = np.asarray(pairs, float); point = correlation(values)
    if point is None:
        return dict(effect=None, ci95=None, state='invalid', writers=len(pairs), reason='constant split half')
    rng = np.random.default_rng(config['seed'])
    draws = [correlation(values[index]) for index in rng.integers(len(values), size=(config['bootstrap'], len(values)))]
    invalid = sum(d is None for d in draws)
    if invalid:
        return dict(effect=point, ci95=None, state='invalid', writers=len(pairs), invalid_bootstrap=invalid,
            reason='undefined bootstrap correlation; no draw dropped')
    low, high = np.quantile(draws, [.025, .975]).tolist()
    se = float(np.std(draws, ddof=1)); z = point / se if se > 0 else None
    return dict(effect=point, ci95=[low, high], state=states.contrast_state(point, low, high), writers=len(pairs),
        standard_error=se, z=z, p_approx=math.erfc(abs(z) / math.sqrt(2)) if z is not None else None,
        p_method='two-sided normal-reference Wald approximation; descriptive, not permutation p', invalid_bootstrap=0)


def summarize(units, config):
    units = sorted(units, key=lambda u: (u['writer'], u['session_order'], u['session']))
    by_writer = defaultdict(list); support = Counter(); per_writer = []; all_rates = []
    for unit in units:
        by_writer[unit['writer']].append(unit); support.update(unit['support'])
    values = {key: [] for key in ('all', 'accepted', 'typed', 'pair_label_shuffle')}
    for writer, own in sorted(by_writer.items()):
        rng = np.random.default_rng(stable_seed(config['seed'], writer))
        rates = []
        for session in own:
            changed = [dict(p, sacrifice=(int(p['deleted_prompt_fit'] > p['retained_prompt_fit']) if rng.integers(2) else p['sacrifice']))
                       for p in session['scored_pairs']]
            counts = {key: [p['sacrifice'] for p in session['scored_pairs'] if key == 'all' or p['origin'] == key]
                      for key in ('all', 'accepted', 'typed')}
            counts['pair_label_shuffle'] = [p['sacrifice'] for p in changed]
            rates.append(dict(session=session['session'], session_order=session['session_order'],
                rates={key: float(np.mean(v)) if v else None for key, v in counts.items()},
                pairs={key: len(v) for key, v in counts.items()}, ties=sum(p['tied'] for p in session['scored_pairs'])))
        halves, exclusions = {}, {}
        for arm in values:
            groups = [[r['rates'][arm] for r in rates if r['session_order'] % 2 == half and r['rates'][arm] is not None] for half in (0, 1)]
            if min(map(len, groups)) >= config['minimum_sessions_per_half']:
                pair = [float(np.mean(g)) for g in groups]; values[arm].append(pair); halves[arm] = pair
            else:
                exclusions[arm] = dict(reason='fewer than two usable sessions per chronological parity', sessions=list(map(len, groups)))
        per_writer.append(dict(writer=writer, halves=halves, exclusions=exclusions)); all_rates.extend(rates)
    return dict(card='D18', primary=reliability(values['all'], config),
        accepted_specification=reliability(values['accepted'], config), typed_specification=reliability(values['typed'], config),
        pair_label_shuffle=reliability(values['pair_label_shuffle'], config), per_writer=per_writer, session_rates=all_rates,
        support=dict(support), sessions=len(units), writers=len(by_writer), matched_pairs=sum(len(u['scored_pairs']) for u in units),
        tied_pairs=sum(p['tied'] for u in units for p in u['scored_pairs']),
        truncated_inputs=sum(s['truncated'] for u in units for s in u['token_scopes']),
        session_exclusions=[dict(session=u['session'], reason=u['session_exclusion']) for u in units if u['session_exclusion']],
        span_exclusions=[dict(session=u['session'], **e) for u in units for e in u['exclusions']],
        canonical_source_exclusions=[dict(session=u['session'],**e) for u in units for e in u.get('canonical_exclusions',[])],
        method='Pearson correlation across writers of odd/even chronological session mean prompt-fit sacrifice rates; >=2 usable sessions each half',
        sacrifice='Strict deleted cosine-to-prompt < retained cosine-to-prompt; exact ties count zero and remain in denominator',
        matching='Same session/origin; deleted original source order, unused intact survivor nearest absolute log codepoint-length ratio <=1.25, tie earliest source ordinal/key',
        span_scope='Original accepted insertion or maximal spatially contiguous consecutive pure writer insertion run; replacement insertion chunks separate',
        restricted_population='Fully user-deleted versus fully retained contiguous original spans; partial survival, internal insertion, system deletion and whitespace-only spans excluded, all totals retained',
        prompt_scope='Exact released initial document, also authenticated P2 initial_document; supplied prompt/context, not a recovered private goal',
        embedding_scope='Frozen CONTENT_V2/P5 CPU MiniLM; first254 native tokens plus CLS/SEP, truncation scopes retained',
        control='Independent fixed random swap of deleted/retained labels per matched pair within writer; matching/geometry held fixed',
        extension='Fluency sacrifice after P1; held, not measured', extension_run=False, scientific_admission=False)


def execute(output: Path, inputs: dict, config: dict) -> dict:
    if config != CONFIG or set(inputs) != INPUTS:
        raise ValueError('frozen D18 inputs/config differ')
    output = Path(output); output.mkdir(parents=True, exist_ok=True); started = time.monotonic()
    binding = dict(paths=inputs, config=config, pins=input_pins(inputs))
    if (output / 'BINDING.json').exists():
        if read(output / 'BINDING.json') != binding:
            raise ValueError('D18 resume binding differs')
        if (output / 'SUMMARY.json').exists():
            raise ValueError('D18 completed output is never rerun')
    elif any(output.iterdir()):
        raise ValueError('D18 unbound existing output')
    else:
        write(output / 'BINDING.json', binding)
    roster = source(inputs)
    recovery, reusable = reuse.authenticate(inputs, config, roster, binding['pins'])
    save(output / 'RECOVERY.json', recovery)
    encoder = None; units, index = [], []; elapsed = 0.
    for item in roster:
        clock = time.monotonic(); raw, p2 = source_paths(item, inputs)
        stem = 'sessions/' + hashlib.sha256(item['session'].encode()).hexdigest()[:24]
        path, vector_path = output / (stem + '.json'), output / (stem + '.npy')
        if sealed(path):
            unit = read_sealed(path); vectors = read_sealed(vector_path)
            if (unit['source_sha256'] != item['raw']['source_sha256'] or unit['p2_sha256'] != item['p2']['sha256']
                    or any(unit[k] != item[k] for k in ('session', 'writer', 'session_order'))):
                raise ValueError('D18 checkpoint source differs')
        elif item['session'] in reusable:
            unit,vectors=reuse.restore(reusable[item['session']],path,vector_path)
        else:
            data = extract_session(item, raw, p2, config)
            if data['text_inputs']:
                if encoder is None:
                    encoder = Encoder(inputs['content_model'], config['threads'], config['batch_size'])
                vectors, scopes = encoder.encode(data['text_inputs'])
            else:
                vectors, scopes = np.empty((0, 384), np.float32), []
            unit = score_session(data, vectors, scopes)
            save(vector_path, vectors); unit['elapsed_seconds'] = time.monotonic() - clock
            save(path, unit)
        units.append(unit); elapsed += unit['elapsed_seconds']
        index.append(dict(session=item['session'], file=stem + '.json', vectors=stem + '.npy',
            sha256=filehash(path), vectors_sha256=filehash(vector_path)))
        if len(index) == max(1, math.ceil(.1 * len(roster))) and not (output / 'FIRST_TENTH.json').exists():
            write(output / 'FIRST_TENTH.json', dict(sessions=len(index), total_sessions=len(roster),
                projected_cpu_seconds=2 * elapsed * len(roster) / len(index), forecast_cpu_seconds=FORECAST,
                projection_scope='Twice extraction cost for conservative source replay/summary verification allowance'))
        if (output / 'YIELD_REQUEST.json').exists():
            return dict(status='yielded', sessions_saved=len(index), sessions_total=len(roster))
    save(output / 'SESSION_INDEX.json', index)
    result = summarize(units, config)
    result.update(elapsed_seconds=time.monotonic() - started, saved_extraction_seconds=elapsed, forecast_cpu_seconds=FORECAST)
    write(output / 'SUMMARY.json', result)
    write(output / 'OUTPUT_HASHES.json', {p.relative_to(output).as_posix(): filehash(p) for p in output.rglob('*')
        if p.is_file() and p.name not in ('OUTPUT_HASHES.json', 'YIELD_REQUEST.json')})
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); binding = read(output / 'BINDING.json')
    if binding['paths'] != inputs or binding['config'] != config or config != CONFIG or set(inputs) != INPUTS:
        raise ValueError('D18 verification binding differs')
    for path, expected in binding['pins'].items():
        if filehash(path) != expected:
            raise ValueError('D18 input changed')
    for relative, expected in read(output / 'OUTPUT_HASHES.json').items():
        if filehash(output / relative) != expected:
            raise ValueError('D18 output changed')
    roster = source(inputs)
    recovery,_ = reuse.authenticate(inputs,config,roster,binding['pins'])
    if read_sealed(output/'RECOVERY.json')!=recovery:raise ValueError('D18 recovery provenance changed')
    index = read_sealed(output / 'SESSION_INDEX.json'); units = []
    if [e['session'] for e in index] != [r['session'] for r in roster]:
        raise ValueError('D18 session coverage differs')
    for item, entry in zip(roster, index):
        raw, p2 = source_paths(item, inputs)
        unit = read_sealed(output / entry['file']); vectors = read_sealed(output / entry['vectors'])
        if filehash(output / entry['file']) != entry['sha256'] or filehash(output / entry['vectors']) != entry['vectors_sha256']:
            raise ValueError('D18 index hashes differ')
        data = extract_session(item, raw, p2, config)
        rebuilt = score_session(data, vectors, unit['token_scopes'])
        assert_close(rebuilt, {k: unit[k] for k in rebuilt}); units.append(unit)
    result = summarize(units, config); saved = read(output / 'SUMMARY.json')
    assert_close(result, {k: saved[k] for k in result})
    return dict(verified=True, primary_recomputed=result['primary'], summary_sha256=filehash(output / 'SUMMARY.json'),
        scientific_admission=False, source_replay='Complete original atom/provenance/matching replay; saved frozen embeddings, no duplicate neural pass')
