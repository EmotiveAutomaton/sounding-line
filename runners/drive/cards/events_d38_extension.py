"""D38's single conditional model-minus-own overall acceptance-drop extension.

DESIGN CHECK: LESSONS 3-5. Equal model/own drops produce zero; larger/smaller
model drops preserve their signs. Source-valid events need >=5 eligible menus
on both sides and finite matching covariates; missing support is counted, not
an outcome. Length/time-since-request/session-index matching never reads drops.
Completed, independently verified positive/marginal D38 alone opens this arm.
Original D38 and D39 sources/results stay immutable. No causal trust claim.
"""
import hashlib
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from . import events_d38 as primary
from .events_p5 import read, write, filehash
from .events_d4 import save, read_sealed, sealed, assert_close
from .events_d4_sources import bind_completed
from .events_d4_stats import interval

CONFIG = dict(threads=2, bootstrap=2000, seed=20261017, window=10, minimum_menus=5, length_ratio=1.25)
EXTRA_INPUTS = {'d38_summary', 'd38_binding', 'd38_completion'}
INPUTS = primary.INPUTS | EXTRA_INPUTS
FORECAST = 600


def source(inputs):
    for key in ('d38_summary', 'd38_binding'):
        bind_completed(inputs['d38_completion'], inputs[key])
    summary, binding = read(inputs['d38_summary']), read(inputs['d38_binding'])
    if summary['card'] != 'D38' or summary['primary']['state'] not in ('positive', 'marginal') or summary.get('extension_run'):
        raise ValueError('D38 does not open its single extension')
    if binding['config'] != primary.CONFIG:
        raise ValueError('original D38 config differs')
    for key in primary.INPUTS:
        if Path(binding['paths'][key]).resolve() != Path(inputs[key]).resolve() or binding['pins'][str(Path(inputs[key]))] != filehash(inputs[key]):
            raise ValueError('D38 extension source differs from primary')
    data = primary.source({k: inputs[k] for k in primary.INPUTS})
    if summary['model_failures'] != sum(e['kind'] == 'model' for e in data[3]) or summary['own_failures'] != sum(e['kind'] == 'own' for e in data[3]):
        raise ValueError('D38 failure census differs')
    return data


def overall_drop(window, shuffled=None):
    values, binary, counts = {}, {}, {}
    for phase in ('before', 'after'):
        menus = window[phase]
        if not menus:
            raise ValueError('empty acceptance-drop window')
        chosen = [m['chosen'] if shuffled is None else shuffled[m['key']] for m in menus]
        if any(type(c) not in (int, np.int64, np.int32) or not -1 <= c < len(m['options']) for c, m in zip(chosen, menus)):
            raise ValueError('chosen outcome outside offered support')
        values[phase] = float(np.mean([int(c >= 0) / len(m['options']) for c, m in zip(chosen, menus)]))
        binary[phase] = float(np.mean([c >= 0 for c in chosen]))
        counts[phase] = dict(menus=len(menus), offered_options=sum(len(m['options']) for m in menus),
            accepted_menus=sum(c >= 0 for c in chosen))
    return dict(drop=values['before'] - values['after'], acceptance=values,
        binary_drop=binary['before'] - binary['after'], binary_acceptance=binary, counts=counts)


def extract_writer(writer, sessions, records, vectors, failures, config):
    own = sorted((s for s in sessions if s['writer'] == writer), key=lambda s: (s['timestamp'], s['session']))
    session_map = {s['session']: s for s in own}
    order = {s['session']: i for i, s in enumerate(own)}
    menus, menu_exclusions = {}, []
    for session in own:
        menus[session['session']] = []
        for row in session['rows']:
            menu, reason = primary.eligible_menu(row, records[row['key']], vectors)
            if reason:
                menu_exclusions.append(dict(key=row['key'], session=session['session'], reason=reason))
            else:
                menus[session['session']].append(menu)
    shuffled = primary.shuffle_choices([m for group in menus.values() for m in group], writer, config['seed'])
    events, exclusions = [], []
    source_events = sorted((e for e in failures if e['writer'] == writer),
        key=lambda e: (e['session_index'], e['ordinal'], e['kind'], e['source_span_ordinal']))
    for event in source_events:
        key = f"{event['session']}:{event['ordinal']}:{event['kind']}:{event['source_span_ordinal']}"
        if event['session_index'] != order[event['session']]:
            raise ValueError('D39 failure session chronology differs')
        if event['kind'] not in ('model', 'own'):
            raise ValueError('unknown failure source')
        if event['kind'] == 'model':
            origin = [m for m in session_map[event['session']]['rows'] if m['ordinal'] == event['source_span_ordinal']]
            if len(origin) != 1 or origin[0]['handling'] not in ('accept', 'edit'):
                exclusions.append(dict(key=key, kind=event['kind'], reason='missing exact originating acceptance')); continue
        if not event['deleted_text'].strip():
            exclusions.append(dict(key=key, kind=event['kind'], reason='empty deleted source text')); continue
        if (not event.get('next_menus') or event.get('request_gap_seconds') is None or event['deleted_codepoints'] <= 0
                or not math.isfinite(event['request_gap_seconds']) or event['request_gap_seconds'] < 0):
            exclusions.append(dict(key=key, kind=event['kind'], reason='missing next menu or finite matching covariates')); continue
        definition = event if event['kind'] == 'model' else dict(event, source_span_ordinal=-1)
        window, excluded = primary.event_window(definition, menus[event['session']], config)
        if excluded:
            exclusions.append(dict(key=key, kind=event['kind'], **excluded)); continue
        events.append(dict(key=key, writer=writer, kind=event['kind'], session=event['session'],
            session_index=event['session_index'], ordinal=event['ordinal'], source_span_ordinal=event['source_span_ordinal'],
            deleted_codepoints=event['deleted_codepoints'], request_gap_seconds=event['request_gap_seconds'],
            window=window, observed=overall_drop(window), outcome_shuffle=overall_drop(window, shuffled)))
    return dict(writer=writer, events=events, exclusions=exclusions, menu_exclusions=menu_exclusions,
        failures=dict(Counter(e['kind'] for e in source_events)))


def match(events, config):
    """D39's covariates, scale, caliper and replacement rule on supported events."""
    matched, exclusions = [], []
    for writer in sorted({e['writer'] for e in events}):
        rows = [e for e in events if e['writer'] == writer]
        def features(row):
            return np.asarray([math.log(row['deleted_codepoints']), math.log1p(row['request_gap_seconds']), row['session_index']])
        scale = np.std([features(r) for r in rows], axis=0)
        scale = np.where(scale > 1e-12, scale, 1.)
        own = [e for e in rows if e['kind'] == 'own']
        for model in sorted((e for e in rows if e['kind'] == 'model'), key=lambda e: (e['session_index'], e['ordinal'], e['key'])):
            options = [e for e in own if 1 / config['length_ratio'] <= e['deleted_codepoints'] / model['deleted_codepoints'] <= config['length_ratio']]
            if not options:
                exclusions.append(dict(writer=writer, key=model['key'], reason='no length-matched supported own failure')); continue
            def distance(other):
                return (float(np.sum(((features(model) - features(other)) / scale) ** 2)), other['session_index'], other['ordinal'], other['key'])
            control = min(options, key=distance)
            matched.append(dict(writer=writer, model=model['key'], own=control['key'], model_session=model['session'],
                own_session=control['session'], length_ratio=control['deleted_codepoints'] / model['deleted_codepoints'],
                request_gap_difference=model['request_gap_seconds'] - control['request_gap_seconds'],
                session_index_difference=model['session_index'] - control['session_index'], match_distance=distance(control)[0],
                matching_scale=scale.tolist(),
                difference=model['observed']['drop'] - control['observed']['drop'],
                binary_difference=model['observed']['binary_drop'] - control['observed']['binary_drop'],
                outcome_shuffle=model['outcome_shuffle']['drop'] - control['outcome_shuffle']['drop']))
        used = {p['own'] for p in matched if p['writer'] == writer}
        exclusions.extend(dict(writer=writer, key=e['key'], reason='supported own failure not used as match') for e in own if e['key'] not in used)
    return matched, exclusions


def summarize(units, config):
    events = [e for u in sorted(units, key=lambda u: u['writer']) for e in u['events']]
    pairs, exclusions = match(events, config)
    by_writer = defaultdict(list)
    for pair in pairs:
        by_writer[pair['writer']].append(pair)
    values = {k: [] for k in ('difference', 'binary_difference', 'outcome_shuffle')}; per_writer = []
    for writer, rows in sorted(by_writer.items()):
        result = dict(writer=writer, pairs=len(rows), model_sessions=len({r['model_session'] for r in rows}),
            own_sessions=len({r['own_session'] for r in rows}), unique_own_failures=len({r['own'] for r in rows}))
        for key in values:
            grouped = defaultdict(list)
            for row in rows:
                grouped[row['model_session']].append(row[key])
            result[key] = float(np.mean([np.mean(v) for _, v in sorted(grouped.items())])); values[key].append(result[key])
        per_writer.append(result)
    return dict(card='D38-extension', primary=interval(values['difference'], config['bootstrap'], config['seed']),
        binary_menu_uptake_specification=interval(values['binary_difference'], config['bootstrap'], config['seed']),
        outcome_shuffle=interval(values['outcome_shuffle'], config['bootstrap'], config['seed']),
        matching_exclusions=exclusions, pairs=pairs, writer_contrasts=per_writer,
        event_exclusions=[dict(writer=u['writer'], **e) for u in units for e in u['exclusions']],
        menu_exclusions=[dict(writer=u['writer'], **e) for u in units for e in u['menu_exclusions']],
        failures=dict(sum((Counter(u['failures']) for u in units), Counter())),
        supported_events=dict(Counter(e['kind'] for e in events)), writers_total=len(units),
        writer_exclusions=[dict(writer=u['writer'], reason='no matched supported model/own pair') for u in units if u['writer'] not in by_writer],
        method='Overall offered-option acceptance drop before-minus-after model failure, minus matched own failure; equal menus, matched events within model session, model sessions within writer and writers',
        overall_acceptance='Mean over eligible menus of selected-offer fraction: 1/menu size if accepted or edited, zero if dismissed or ignored; binary menu uptake separately retained',
        matching='Within writer with replacement; length ratio <=1.25, nearest standardized log deleted length/log1p time since last request/session index; scale fitted to supported events only',
        windows='Same-session completed pre-event menus and strictly later openings, up to10 per side and >=5 each; model originating acceptance excluded; overlapping menus excluded',
        control='Original within-writer/menu-size chosen-position permutation including no uptake; event selection/windows/matching held fixed',
        limitations=['Conditional exploratory extension; interval is not adjusted for primary-based selection',
            'Deletion is an observed writing event, not established regret, fear or causal trust loss',
            'Matching support is restricted to events with both-side menus and finite covariates',
            'With-replacement controls and overlapping windows remain; uncertainty clusters writers',
            'Offered-option rate depends on menu size; binary menu-uptake sensitivity is separate'],
        extension_run=True, further_extension=None, scientific_admission=False)


def execute(output: Path, inputs: dict, config: dict) -> dict:
    if config != CONFIG or set(inputs) != INPUTS:
        raise ValueError('frozen D38 extension inputs/config differ')
    output = Path(output); output.mkdir(parents=True, exist_ok=True); started = time.monotonic()
    binding = dict(paths=inputs, config=config, pins=primary.input_pins(inputs))
    if (output / 'BINDING.json').exists():
        if read(output / 'BINDING.json') != binding:
            raise ValueError('D38 extension resume binding differs')
        if (output / 'SUMMARY.json').exists():
            raise ValueError('D38 extension completed output is never rerun')
    elif any(output.iterdir()):
        raise ValueError('D38 extension unbound output')
    else:
        write(output / 'BINDING.json', binding)
    data = source(inputs); roster = sorted({s['writer'] for s in data[0]}); units, index = [], []; elapsed = 0.
    for writer in roster:
        name = 'writers/' + hashlib.sha256(writer.encode()).hexdigest()[:24] + '.json'; path = output / name
        if sealed(path):
            unit = read_sealed(path)
            if unit['writer'] != writer:
                raise ValueError('D38 extension checkpoint writer differs')
        else:
            clock = time.monotonic(); unit = extract_writer(writer, *data, config)
            unit['elapsed_seconds'] = time.monotonic() - clock; save(path, unit)
        units.append(unit); elapsed += unit['elapsed_seconds']; index.append(dict(writer=writer, file=name, sha256=filehash(path)))
        if len(index) == max(1, math.ceil(.1 * len(roster))) and not (output / 'FIRST_TENTH.json').exists():
            write(output / 'FIRST_TENTH.json', dict(writers=len(index), total_writers=len(roster),
                projected_cpu_seconds=2 * elapsed * len(roster) / len(index), forecast_cpu_seconds=FORECAST))
        if (output / 'YIELD_REQUEST.json').exists():
            return dict(status='yielded', writers_saved=len(index), writers_total=len(roster))
    save(output / 'WRITER_INDEX.json', index)
    result = summarize(units, config); result.update(elapsed_seconds=time.monotonic() - started,
        saved_extraction_seconds=elapsed, forecast_cpu_seconds=FORECAST)
    write(output / 'SUMMARY.json', result)
    write(output / 'OUTPUT_HASHES.json', {p.relative_to(output).as_posix(): filehash(p) for p in output.rglob('*')
        if p.is_file() and p.name not in ('OUTPUT_HASHES.json', 'YIELD_REQUEST.json')})
    return result


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output); binding = read(output / 'BINDING.json')
    if binding['paths'] != inputs or binding['config'] != config or config != CONFIG or set(inputs) != INPUTS:
        raise ValueError('D38 extension verification binding differs')
    for path, expected in binding['pins'].items():
        if filehash(path) != expected:
            raise ValueError('D38 extension input changed')
    for relative, expected in read(output / 'OUTPUT_HASHES.json').items():
        if filehash(output / relative) != expected:
            raise ValueError('D38 extension output changed')
    data = source(inputs); index = read_sealed(output / 'WRITER_INDEX.json'); units = []
    if [e['writer'] for e in index] != sorted({s['writer'] for s in data[0]}):
        raise ValueError('D38 extension writer coverage differs')
    for entry in index:
        unit = read_sealed(output / entry['file'])
        if filehash(output / entry['file']) != entry['sha256']:
            raise ValueError('D38 extension index differs')
        rebuilt = extract_writer(entry['writer'], *data, config)
        assert_close(rebuilt, {k: unit[k] for k in rebuilt}); units.append(unit)
    result = summarize(units, config); saved = read(output / 'SUMMARY.json')
    assert_close(result, {k: saved[k] for k in result})
    return dict(verified=True, primary_recomputed=result['primary'], summary_sha256=filehash(output / 'SUMMARY.json'), scientific_admission=False)
