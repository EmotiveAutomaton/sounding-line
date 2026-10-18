"""D28 observed hover alternation versus within-menu content dissimilarity.

DESIGN CHECK: LESSONS 3-5. Constant switch counts give exact zero tail contrast;
planted/reversed counts preserve their sign. Unknown targets, censored episodes
and overlapping tied quintile boundaries are explicit exclusions. Empty support
is invalid, never evidence of absent alternation. A logged hover switch is not
proof of reading, indecision, a near-tie, or an unlogged keyboard action.
"""
import hashlib
import math
import time
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.stats import rankdata
from .events_p5 import read, write, filehash
from .events_d4 import save, read_sealed, sealed, assert_close
from .events_d4_stats import interval, stable_seed
from . import states_v2 as states

CONFIG = dict(threads=2, bootstrap=2000, seed=20261017, minimum_tail_menus=2)
INPUTS = {'sessions', 'content_records', 'content_vectors', 'content_complete', 'd6_rows', 'd6_inputs', 'd6_completion'}
FORECAST = 1800


def source(inputs):
    if set(inputs) != INPUTS:
        raise ValueError('explicit D28 inputs differ')
    complete = read(inputs['d6_completion'])
    if complete.get('status') != 'COMPLETE' or not complete.get('fresh_process_verified'):
        raise ValueError('D6 source is not complete and verified')
    for key in ('d6_rows', 'd6_inputs'):
        relative = Path(inputs[key]).resolve().relative_to(Path(inputs['d6_completion']).resolve().parent).as_posix()
        if complete['outputs'].get(relative) != filehash(inputs[key]):
            raise ValueError('D6 completion artifact differs')
    d6 = read(inputs['d6_inputs'])
    if Path(d6['paths']['sessions']).resolve() != Path(inputs['sessions']).resolve():
        raise ValueError('D6 session source differs')
    # D6 INPUTS stores both ordinary file pins and audited interface pins.
    if d6['pins'].get(str(Path(inputs['sessions']))) != filehash(inputs['sessions']):
        raise ValueError('D6 session hash differs')
    content = read(inputs['content_complete'])
    if content.get('status') != 'COMPLETE':
        raise ValueError('CONTENT_V2 incomplete')
    for key in ('content_records', 'content_vectors'):
        matches = [v for k, v in content['outputs'].items() if Path(k).name == Path(inputs[key]).name]
        if matches != [filehash(inputs[key])]:
            raise ValueError('CONTENT_V2 binding differs')
    sessions, records, rows = read(inputs['sessions']), read(inputs['content_records']), read(inputs['d6_rows'])
    menus = {r['key']: r for s in sessions for r in s['rows']}
    record_map = {r['key']: r for r in records}
    row_map = {r['key']: r for r in rows}
    if len(menus) != sum(len(s['rows']) for s in sessions) or len(record_map) != len(records) or len(row_map) != len(rows) or set(menus) != set(record_map) or set(menus) != set(row_map):
        raise ValueError('D28 source decision coverage differs')
    if len({s['session'] for s in sessions}) != len(sessions):
        raise ValueError('duplicate source session')
    vectors = np.load(inputs['content_vectors'], mmap_mode='r', allow_pickle=False)
    return sessions, menus, record_map, row_map, vectors


def switches(row):
    """Do not manufacture a cross-episode transition when a menu reopens."""
    sequence = row['hover_sequence']
    if [e['ordinal'] for e in sequence] != sorted({e['ordinal'] for e in sequence}):
        raise ValueError('hover sequence chronology differs')
    count, covered = 0, set()
    for episode in row['visible_episodes']:
        previous = None
        for i, event in enumerate(sequence):
            if episode['start'] < event['ordinal'] <= episode['end']:
                if i in covered or not 0 <= event['position'] < row['menu_size']:
                    raise ValueError('overlapping episode or invalid hover target')
                count += int(previous is not None and event['position'] != previous)
                previous = event['position']
                covered.add(i)
    if len(covered) != len(sequence):
        raise ValueError('hover outside saved visible episodes')
    return count


def dissimilarity(options):
    options = np.asarray(options, float)
    if options.ndim != 2 or len(options) < 2 or not np.isfinite(options).all() or not np.allclose(np.linalg.norm(options, axis=1), 1, atol=1e-5, rtol=0):
        raise ValueError('invalid content menu vectors')
    values = (1 - options @ options.T)[np.triu_indices(len(options), 1)]
    return float(np.clip(values, 0, 2).mean())


def extract_writer(writer, sessions, menus, records, hover, vectors):
    own = sorted([s for s in sessions if s['writer'] == writer], key=lambda s: (s['timestamp'], s['session']))
    rows, exclusions = [], []
    for order, session in enumerate(own):
        for menu in sorted(session['rows'], key=lambda r: (r['open_at'], r['key'])):
            event, record = hover[menu['key']], records[menu['key']]
            if any(event[k] != menu[k] or record[k] != menu[k] for k in ('writer', 'session')) or event['handling'] != menu['handling'] or event['menu_size'] != len(menu['menu']) or len(record['options']) != event['menu_size']:
                raise ValueError('D28 menu join differs')
            reason = None
            if event['menu_size'] < 2:
                reason = 'fewer than two displayed options'
            elif not event['hover_target_complete']:
                reason = 'unknown hover target'
            elif not event['dwell_observed']:
                reason = 'censored visible episode'
            elif event['handling'] not in ('accept', 'edit', 'dismiss'):
                reason = 'no observed handling decision'
            if reason:
                exclusions.append(dict(key=menu['key'], session=session['session'], reason=reason))
                continue
            if not math.isfinite(event['dwell_seconds']) or event['dwell_seconds'] < 0:
                raise ValueError('invalid observed visible duration')
            rows.append(dict(key=menu['key'], writer=writer, session=session['session'], session_order=order,
                menu_size=event['menu_size'], handling=event['handling'], switches=switches(event),
                dissimilarity=dissimilarity(vectors[record['options']]), visible_seconds=event['dwell_seconds'],
                hover_events=len(event['hover_sequence']), keyboard_events=len(event['keyboard_sequence'])))
    return dict(writer=writer, rows=rows, exclusions=exclusions)


def mean_sessions(rows, field):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['session']].append(row[field])
    return float(np.mean([np.mean(grouped[s]) for s in sorted(grouped)])) if grouped else None


def tail_contrast(rows, minimum=2):
    if not rows:
        return dict(eligible=False, reason='no eligible observed menus')
    low, high = np.quantile([r['dissimilarity'] for r in rows], [.2, .8]).tolist()
    if low >= high:
        return dict(eligible=False, reason='quintile boundaries coincide', boundaries=[low, high])
    near = [r for r in rows if r['dissimilarity'] <= low]
    far = [r for r in rows if r['dissimilarity'] >= high]
    if min(len(near), len(far)) < minimum:
        return dict(eligible=False, reason='fewer than two menus in a tail', boundaries=[low, high], near=len(near), far=len(far))
    nm, fm = mean_sessions(near, 'switches'), mean_sessions(far, 'switches')
    return dict(eligible=True, effect=nm - fm, near_mean=nm, far_mean=fm, boundaries=[low, high],
                near_keys=[r['key'] for r in near], far_keys=[r['key'] for r in far])


def correlation(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    x, y = x - x.mean(), y - y.mean()
    denominator = float(np.linalg.norm(x) * np.linalg.norm(y))
    return float(np.clip((x @ y) / denominator, -1, 1)) if denominator > 1e-12 else None


def reliability(pairs, config):
    if len(pairs) < 4:
        return dict(effect=None, ci95=None, state='invalid', writers=len(pairs), reason='fewer than four split-half writers')
    values = np.asarray(pairs, float)
    point = correlation(values[:, 0], values[:, 1])
    if point is None:
        return dict(effect=None, ci95=None, state='invalid', writers=len(pairs), reason='constant split half')
    rng = np.random.default_rng(config['seed'])
    draws = []
    for indices in rng.integers(len(pairs), size=(config['bootstrap'], len(pairs))):
        sample = values[indices]
        draws.append(correlation(sample[:, 0], sample[:, 1]))
    invalid = sum(x is None for x in draws)
    if invalid:
        return dict(effect=point, ci95=None, state='invalid', writers=len(pairs), invalid_bootstrap=invalid)
    low, high = np.quantile(draws, [.025, .975]).tolist()
    se = float(np.std(draws, ddof=1))
    return dict(effect=point, ci95=[low, high], standard_error=se, writers=len(pairs),
                state=states.contrast_state(point, low, high), invalid_bootstrap=0)


def summarize(units, config):
    contrasts, controls, fixed_five, durations, pairs = [], [], [], [], []
    per_writer = []
    for unit in units:
        rows = unit['rows']
        contrast = tail_contrast(rows, config['minimum_tail_menus'])
        five = tail_contrast([r for r in rows if r['menu_size'] == 5], config['minimum_tail_menus'])
        rng = np.random.default_rng(stable_seed(config['seed'], unit['writer']))
        changed = rng.permutation([r['switches'] for r in rows])
        shuffled = tail_contrast([dict(r, switches=int(v)) for r, v in zip(rows, changed)], config['minimum_tail_menus'])
        if contrast['eligible']:
            contrasts.append(contrast['effect']); controls.append(shuffled['effect'])
        if five['eligible']:
            fixed_five.append(five['effect'])
        duration = correlation(rankdata([r['switches'] for r in rows]), rankdata([r['visible_seconds'] for r in rows])) if len(rows) >= 3 else None
        if duration is not None:
            durations.append(duration)
        halves = [[r for r in rows if r['session_order'] % 2 == half] for half in (0, 1)]
        pair = [mean_sessions(half, 'switches') for half in halves] if all(len({r['session'] for r in half}) >= 2 for half in halves) else None
        if pair:
            pairs.append(pair)
        per_writer.append(dict(writer=unit['writer'], primary=contrast, fixed_five=five,
            shuffled=shuffled, duration_spearman=duration, odd_even_session_means=pair))
    return dict(card='D28', primary=interval(contrasts, config['bootstrap'], config['seed']),
        outcome_shuffle=interval(controls, config['bootstrap'], config['seed']),
        fixed_five_specification=interval(fixed_five, config['bootstrap'], config['seed']),
        visible_duration_association=interval(durations, config['bootstrap'], config['seed']),
        odd_even_session_reliability=reliability(pairs, config), per_writer=per_writer,
        exclusions=[dict(writer=u['writer'], **r) for u in units for r in u['exclusions']],
        rows=sum(len(u['rows']) for u in units), writers=len(units),
        weighting='Within-writer distance quintiles, equal sessions within each tail, equal writers; tied boundaries excluded',
        scope='Observed explicit hover targets within visible episodes before observed accept/edit/dismiss; no cross-reopen switch and no keyboard inference',
        extension='Alternation predicts later reversal; not run', extension_run=False,
        reader_spread='not measured; P1-dependent measure remains open', scientific_admission=False)


def execute(output: Path, inputs: dict, config: dict) -> dict:
    if config != CONFIG or set(inputs) != INPUTS:
        raise ValueError('frozen D28 inputs/config differ')
    output = Path(output); output.mkdir(parents=True, exist_ok=True); started = time.monotonic()
    binding = dict(paths=inputs, config=config, pins={str(Path(p)): filehash(p) for p in inputs.values()})
    if (output / 'BINDING.json').exists():
        if read(output / 'BINDING.json') != binding:
            raise ValueError('D28 resume binding differs')
        if (output / 'SUMMARY.json').exists():
            raise ValueError('D28 completed output is never rerun')
    elif any(output.iterdir()):
        raise ValueError('D28 unbound existing output')
    else:
        write(output / 'BINDING.json', binding)
    data = source(inputs)
    roster = sorted({s['writer'] for s in data[0]})
    units, index, elapsed = [], [], 0.
    for writer in roster:
        name = 'writers/' + hashlib.sha256(writer.encode()).hexdigest()[:24] + '.json'
        path = output / name
        if sealed(path):
            unit = read_sealed(path)
        else:
            clock = time.monotonic()
            unit = extract_writer(writer, *data)
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
        raise ValueError('D28 verification binding differs')
    for path, expected in binding['pins'].items():
        if filehash(path) != expected:
            raise ValueError('D28 input changed')
    for relative, expected in read(output / 'OUTPUT_HASHES.json').items():
        if filehash(output / relative) != expected:
            raise ValueError('D28 output changed')
    data = source(inputs); units = []
    index = read_sealed(output / 'WRITER_INDEX.json')
    if [r['writer'] for r in index] != sorted({s['writer'] for s in data[0]}):
        raise ValueError('D28 writer coverage differs')
    for entry in index:
        unit = read_sealed(output / entry['file'])
        if filehash(output / entry['file']) != entry['sha256']:
            raise ValueError('D28 index differs')
        rebuilt = extract_writer(entry['writer'], *data)
        assert_close(rebuilt, {k: unit[k] for k in rebuilt}); units.append(unit)
    result = summarize(units, config); saved = read(output / 'SUMMARY.json')
    assert_close(result, {k: saved[k] for k in result})
    return dict(verified=True, primary_recomputed=result['primary'], summary_sha256=filehash(output / 'SUMMARY.json'))
