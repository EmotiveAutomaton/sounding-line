"""D38 acceptance-drop gradients after authenticated model-span deletions.

DESIGN CHECK: LESSONS 3-5. Known flat/positive/reverse early-late gradients must
retain zero/sign. The source event is D39's >=80% original-codepoint deletion,
not a diagnosis of fear, trauma or regret. Original acceptance is excluded.
Overlapping menus, missing two-sided support and tied terciles are explicit
exclusions. All offered-option outcomes are behavior, not inferred consideration.
"""
import hashlib
import math
import time
from collections import defaultdict
from pathlib import Path
import numpy as np
from .events_p5 import read, write, filehash, model_identity, Encoder
from .events_d4 import save, read_sealed, sealed, assert_close
from .events_d4_stats import interval, stable_seed
from .events_d4_sources import bind_completed

CONFIG = dict(threads=2, batch_size=16, bootstrap=2000, seed=20261017, window=10, minimum_menus=5)
INPUTS = {'sessions', 'content_records', 'content_vectors', 'content_model', 'content_complete',
    'd39_failures', 'd39_inputs', 'd39_completion', 'p5_inputs', 'p5_summary', 'p5_completion'}
FORECAST = 1800


def input_pins(inputs):
    pins = {str(Path(p)): filehash(p) for p in inputs.values()}
    identity = read(inputs['content_model']); model_identity(inputs['content_model'])
    pins.update({str(Path(identity['path']) / rel): digest for rel, digest in identity['files'].items()})
    return pins


def source(inputs):
    for key in ('d39_failures', 'd39_inputs'):
        bind_completed(inputs['d39_completion'], inputs[key])
    for key in ('p5_inputs', 'p5_summary'):
        bind_completed(inputs['p5_completion'], inputs[key])
    p5, d39 = read(inputs['p5_inputs']), read(inputs['d39_inputs'])
    for binding in (p5, d39):
        if Path(binding['paths']['sessions']).resolve() != Path(inputs['sessions']).resolve():
            raise ValueError('D38 source session binding differs')
    if p5['sha256']['sessions'] != filehash(inputs['sessions']) or d39['pins'][str(Path(inputs['sessions']))] != filehash(inputs['sessions']):
        raise ValueError('D38 source session hash differs')
    if Path(p5['paths']['content_model']).resolve() != Path(inputs['content_model']).resolve() or p5['sha256']['content_model'] != filehash(inputs['content_model']):
        raise ValueError('P5 and CONTENT model identity differ')
    complete = read(inputs['content_complete'])
    if complete.get('status') != 'COMPLETE':
        raise ValueError('CONTENT_V2 incomplete')
    for key in ('content_records', 'content_vectors', 'content_model'):
        values = [digest for name, digest in complete['outputs'].items() if Path(name).name == Path(inputs[key]).name]
        if values != [filehash(inputs[key])]:
            raise ValueError('CONTENT_V2 binding differs')
    sessions, records, failures = read(inputs['sessions']), read(inputs['content_records']), read(inputs['d39_failures'])
    if read(inputs['p5_summary'])['sessions'] != len(sessions):
        raise ValueError('P5/source session census differs')
    menus = {r['key']: r for s in sessions for r in s['rows']}
    record_map = {r['key']: r for r in records}
    session_map = {s['session']: s for s in sessions}
    if len(session_map) != len(sessions) or len(record_map) != len(records) or len(menus) != sum(len(s['rows']) for s in sessions) or set(menus) != set(record_map):
        raise ValueError('D38 source coverage differs')
    seen = set()
    for event in failures:
        key = (event['session'], event['ordinal'], event['kind'], event['source_span_ordinal'])
        if key in seen or event['session'] not in session_map or event['writer'] != session_map[event['session']]['writer']:
            raise ValueError('D38 failure identity differs')
        seen.add(key)
        if event['kind'] == 'model' and (event['original_codepoints'] <= 0 or 5 * event['deleted_codepoints'] < 4 * event['original_codepoints']
                or len(event['deleted_text']) != event['original_codepoints'] or event['source_span_ordinal'] >= event['ordinal']):
            raise ValueError('model failure is below frozen eighty-percent threshold')
    vectors = np.load(inputs['content_vectors'], mmap_mode='r', allow_pickle=False)
    if vectors.ndim != 2 or vectors.shape[1] != 384:
        raise ValueError('content vector shape differs')
    return sessions, record_map, vectors, failures


def eligible_menu(menu, record, vectors):
    if not menu['menu']:
        return None, 'empty offered menu'
    if record['writer'] != menu['writer'] or record['session'] != menu['session'] or len(record['options']) != len(menu['menu']):
        raise ValueError('D38 content/menu join differs')
    selected = [i for i, text in enumerate(menu['menu']) if text == menu['inserted']]
    if menu['handling'] in ('accept', 'edit'):
        if len(selected) != 1:
            return None, 'selected offer missing or ambiguous'
        chosen = selected[0]
    elif menu['handling'] in ('dismiss', 'ignore'):
        chosen = -1
    else:
        raise ValueError('unknown handling')
    values = vectors[record['options']]
    if not np.isfinite(values).all() or not np.allclose(np.linalg.norm(values, axis=1), 1., atol=1e-5, rtol=0):
        raise ValueError('invalid offered-option vector')
    return dict(key=menu['key'], session=menu['session'], ordinal=menu['ordinal'], end_ordinal=menu['end_ordinal'],
                options=record['options'], chosen=chosen), None


def event_window(event, menus, config):
    origin = event['source_span_ordinal']
    before = [m for m in menus if m['ordinal'] != origin and m['end_ordinal'] <= event['ordinal']]
    after = [m for m in menus if m['ordinal'] != origin and m['ordinal'] > event['ordinal']]
    before = sorted(before, key=lambda r: (r['ordinal'], r['key']))[-config['window']:]
    after = sorted(after, key=lambda r: (r['ordinal'], r['key']))[:config['window']]
    excluded_overlap = [m['key'] for m in menus if m['ordinal'] != origin and m['ordinal'] <= event['ordinal'] < m['end_ordinal']]
    if min(len(before), len(after)) < config['minimum_menus']:
        return None, dict(reason='fewer than five eligible menus on either side', before=len(before), after=len(after), overlapping_keys=excluded_overlap)
    return dict(before=before, after=after, overlapping_keys=excluded_overlap), None


def gradient(window, anchor, vectors, shuffled=None):
    anchor = np.asarray(anchor, float)
    if anchor.shape != (384,) or not np.isfinite(anchor).all() or not np.isclose(np.linalg.norm(anchor), 1., atol=1e-5, rtol=0):
        raise ValueError('invalid deleted-span anchor')
    distances = {m['key']: np.clip(1 - vectors[m['options']] @ anchor, 0, 2) for phase in ('before', 'after') for m in window[phase]}
    low, high = np.quantile(np.concatenate(list(distances.values())), [1/3, 2/3]).tolist()
    if low >= high:
        return dict(eligible=False, reason='distance tercile boundaries coincide', boundaries=[low, high])
    rates, support = {}, {}
    for phase in ('before', 'after'):
        rates[phase], support[phase] = {}, {}
        for label in ('near', 'middle', 'far'):
            per_menu, menu_keys, offers = [], [], 0
            for menu in window[phase]:
                d = distances[menu['key']]
                mask = d <= low if label == 'near' else d >= high if label == 'far' else (d > low) & (d < high)
                if not np.any(mask):
                    continue
                chosen = menu['chosen'] if shuffled is None else shuffled[menu['key']]
                y = np.arange(len(d)) == chosen
                per_menu.append(float(y[mask].mean())); menu_keys.append(menu['key']); offers += int(mask.sum())
            rates[phase][label] = float(np.mean(per_menu)) if per_menu else None
            support[phase][label] = dict(menus=menu_keys, offers=offers)
    if any(rates[phase][label] is None for phase in ('before', 'after') for label in ('near', 'far')):
        return dict(eligible=False, reason='missing near/far support on one side', boundaries=[low, high], support=support)
    drops = {label: rates['before'][label] - rates['after'][label] if rates['before'][label] is not None and rates['after'][label] is not None else None
             for label in ('near', 'middle', 'far')}
    return dict(eligible=True, gradient=drops['near'] - drops['far'], drops=drops, acceptance=rates,
                boundaries=[low, high], support=support)


def shuffle_choices(menus, writer, seed):
    grouped = defaultdict(list)
    for menu in sorted(menus, key=lambda m: m['key']):
        grouped[len(menu['options'])].append(menu)
    rng = np.random.default_rng(stable_seed(seed, writer))
    result = {}
    for size, group in sorted(grouped.items()):
        chosen = rng.permutation([m['chosen'] for m in group])
        result.update({m['key']: int(value) for m, value in zip(group, chosen)})
    return result


def writer_support(writer, sessions, records, vectors, failures, config):
    own = sorted((s for s in sessions if s['writer'] == writer), key=lambda s: (s['timestamp'], s['session']))
    half = len(own) // 2
    phase = {s['session']: 'early' if i < half else 'late' for i, s in enumerate(own)}
    menus, menu_exclusions = {}, []
    for session in own:
        menus[session['session']] = []
        for row in session['rows']:
            item, reason = eligible_menu(row, records[row['key']], vectors)
            if reason:
                menu_exclusions.append(dict(key=row['key'], session=session['session'], reason=reason))
            else:
                menus[session['session']].append(item)
    events, exclusions = [], []
    model = [e for e in failures if e['writer'] == writer and e['kind'] == 'model']
    for event in sorted(model, key=lambda e: (e['session_index'], e['ordinal'], e['source_span_ordinal'])):
        key = f"{event['session']}:{event['ordinal']}:{event['source_span_ordinal']}"
        origin = [m for m in next(s for s in own if s['session'] == event['session'])['rows'] if m['ordinal'] == event['source_span_ordinal']]
        if len(origin) != 1 or origin[0]['handling'] not in ('accept', 'edit'):
            exclusions.append(dict(key=key, reason='missing exact originating acceptance')); continue
        if not event['deleted_text'].strip():
            exclusions.append(dict(key=key, reason='empty original accepted span')); continue
        window, excluded = event_window(event, menus[event['session']], config)
        if excluded:
            exclusions.append(dict(key=key, **excluded)); continue
        events.append(dict(key=key, session=event['session'], phase=phase[event['session']], ordinal=event['ordinal'],
            source_span_ordinal=event['source_span_ordinal'], original_codepoints=event['original_codepoints'], deleted_codepoints=event['deleted_codepoints'],
            text=event['deleted_text'], window=window))
    shuffled = shuffle_choices([m for group in menus.values() for m in group], writer, config['seed'])
    return dict(writer=writer, phase=phase, events=events, exclusions=exclusions, menu_exclusions=menu_exclusions,
                outcome_shuffle=shuffled, model_failures=len(model), own_failures=sum(e['writer'] == writer and e['kind'] == 'own' for e in failures))


def score_writer(support, anchors, scopes, vectors):
    result = {k: v for k, v in support.items() if k != 'events'}
    result['events'] = []
    if len(anchors) != len(support['events']) or len(scopes) != len(anchors):
        raise ValueError('event-anchor coverage differs')
    for event, anchor, scope in zip(support['events'], anchors, scopes):
        row = {k: v for k, v in event.items() if k != 'text'}
        row.update(text_sha256=hashlib.sha256(event['text'].encode('utf8')).hexdigest(), anchor=np.asarray(anchor).tolist(), token_scope=scope,
            primary=gradient(event['window'], anchor, vectors),
            outcome_shuffle=gradient(event['window'], anchor, vectors, support['outcome_shuffle']))
        result['events'].append(row)
    return result


def summarize(units, config):
    values, controls, rows = [], [], []
    for unit in units:
        buckets = defaultdict(list); shuffled = defaultdict(list)
        for event in unit['events']:
            if event['primary']['eligible']:
                key = (event['phase'], event['session'])
                buckets[key].append(event['primary']['gradient'])
                shuffled[key].append(event['outcome_shuffle']['gradient'])
        means = {phase: [np.mean(v) for (p, s), v in sorted(buckets.items()) if p == phase] for phase in ('early', 'late')}
        if not means['early'] or not means['late']:
            rows.append(dict(writer=unit['writer'], eligible=False, reason='missing eligible event in either session half')); continue
        effect = float(np.mean(means['late']) - np.mean(means['early']))
        control = float(np.mean([np.mean(v) for (p, s), v in sorted(shuffled.items()) if p == 'late']) -
                        np.mean([np.mean(v) for (p, s), v in sorted(shuffled.items()) if p == 'early']))
        values.append(effect); controls.append(control)
        rows.append(dict(writer=unit['writer'], eligible=True, effect=effect, outcome_shuffle=control,
                         early_sessions=len(means['early']), late_sessions=len(means['late'])))
    return dict(card='D38', primary=interval(values, config['bootstrap'], config['seed']),
        outcome_shuffle=interval(controls, config['bootstrap'], config['seed']), writer_contrasts=rows,
        events=sum(len(u['events']) for u in units), eligible_events=sum(e['primary']['eligible'] for u in units for e in u['events']),
        model_failures=sum(u['model_failures'] for u in units), own_failures=sum(u['own_failures'] for u in units),
        truncated_anchors=sum(bool(e['token_scope']['truncated']) for u in units for e in u['events']),
        event_exclusions=[dict(writer=u['writer'], **e) for u in units for e in u['exclusions']],
        bin_exclusions=[dict(writer=u['writer'], key=e['key'], **e['primary']) for u in units for e in u['events'] if not e['primary']['eligible']],
        menu_exclusions=[dict(writer=u['writer'], **e) for u in units for e in u['menu_exclusions']],
        scope='Exploratory observed writing-failure analog; not fear, trauma or causal expertise',
        method='Near-minus-far acceptance drop before-minus-after model failure; later session half minus earlier; equal menus per bin/phase, events per session and sessions per half, equal writers',
        temporal_scope='Completed pre-event menus and strictly later openings only, original acceptance excluded; up to10 each side, at least5',
        outcome_scope='Selected offer=1, other offered options=0; discard ambiguous selected menus, ignore/dismiss uptake=0',
        extension='Overall acceptance-drop difference model minus length-matched own failure, conditional and unrun', extension_run=False,
        scientific_admission=False)


def execute(output: Path, inputs: dict, config: dict) -> dict:
    if config != CONFIG or set(inputs) != INPUTS:
        raise ValueError('frozen D38 inputs/config differ')
    output = Path(output); output.mkdir(parents=True, exist_ok=True); started = time.monotonic()
    binding = dict(paths=inputs, config=config, pins=input_pins(inputs))
    if (output / 'BINDING.json').exists():
        if read(output / 'BINDING.json') != binding:
            raise ValueError('D38 resume binding differs')
        if (output / 'SUMMARY.json').exists():
            raise ValueError('D38 completed output is never rerun')
    elif any(output.iterdir()):
        raise ValueError('D38 unbound existing output')
    else:
        write(output / 'BINDING.json', binding)
    data = source(inputs); roster = sorted({s['writer'] for s in data[0]})
    encoder, units, index, elapsed = None, [], [], 0.
    for writer in roster:
        name = 'writers/' + hashlib.sha256(writer.encode()).hexdigest()[:24] + '.json'
        path = output / name
        if sealed(path):
            unit = read_sealed(path)
        else:
            clock = time.monotonic()
            support = writer_support(writer, *data, config)
            if support['events']:
                if encoder is None:
                    encoder = Encoder(inputs['content_model'], config['threads'], config['batch_size'])
                anchors, scopes = encoder.encode([e['text'] for e in support['events']])
            else:
                anchors, scopes = [], []
            unit = score_writer(support, anchors, scopes, data[2])
            unit['elapsed_seconds'] = time.monotonic() - clock
            save(path, unit)
        units.append(unit); elapsed += unit['elapsed_seconds']
        index.append(dict(writer=writer, file=name, sha256=filehash(path)))
        if len(index) == max(1, math.ceil(.1 * len(roster))) and not (output / 'FIRST_TENTH.json').exists():
            write(output / 'FIRST_TENTH.json', dict(writers=len(index), total_writers=len(roster),
                projected_cpu_seconds=elapsed * len(roster) / len(index), forecast_cpu_seconds=FORECAST))
        if (output / 'YIELD_REQUEST.json').exists():
            return dict(status='yielded', writers_saved=len(index), writers_total=len(roster))
    save(output / 'WRITER_INDEX.json', index)
    result = summarize(units, config)
    result.update(elapsed_seconds=time.monotonic() - started, saved_extraction_seconds=elapsed, forecast_cpu_seconds=FORECAST)
    write(output / 'SUMMARY.json', result)
    write(output / 'OUTPUT_HASHES.json', {p.relative_to(output).as_posix(): filehash(p) for p in output.rglob('*')
        if p.is_file() and p.name not in ('OUTPUT_HASHES.json', 'YIELD_REQUEST.json')})
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); binding = read(output / 'BINDING.json')
    if binding['paths'] != inputs or binding['config'] != config or config != CONFIG:
        raise ValueError('D38 verification binding differs')
    for path, expected in binding['pins'].items():
        if filehash(path) != expected:
            raise ValueError('D38 input changed')
    for relative, expected in read(output / 'OUTPUT_HASHES.json').items():
        if filehash(output / relative) != expected:
            raise ValueError('D38 output changed')
    data = source(inputs); units = []
    index = read_sealed(output / 'WRITER_INDEX.json')
    if [e['writer'] for e in index] != sorted({s['writer'] for s in data[0]}):
        raise ValueError('D38 writer coverage differs')
    for entry in index:
        unit = read_sealed(output / entry['file'])
        if filehash(output / entry['file']) != entry['sha256']:
            raise ValueError('D38 writer index differs')
        support = writer_support(entry['writer'], *data, config)
        rebuilt = score_writer(support, [e['anchor'] for e in unit['events']], [e['token_scope'] for e in unit['events']], data[2])
        assert_close(rebuilt, {k: unit[k] for k in rebuilt}); units.append(unit)
    result = summarize(units, config); saved = read(output / 'SUMMARY.json')
    assert_close(result, {k: saved[k] for k in result})
    return dict(verified=True, primary_recomputed=result['primary'], summary_sha256=filehash(output / 'SUMMARY.json'), scientific_admission=False)
