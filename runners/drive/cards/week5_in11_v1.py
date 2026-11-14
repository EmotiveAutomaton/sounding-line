"""IN11 two-day ordinal-duration source and fixed crossover consumer.

DESIGN CHECK: preserve categorical meaning, no invented seconds; two outcomes
and two indices standardized within prompt. Six-item style excludes both indices.
Only authorized duration fields and private keys extend the qualified source.
"""
from pathlib import Path
import hashlib
import json
import os
import time
import zipfile
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '2'
import numpy as np
import pandas as pd
from . import week5_in as original
from . import week5_in11_math_v1 as math
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io

MODULE = 'runners.drive.cards.week5_in11_v1'
TABLE_PIN = '196fe2a4f72b36ae91516ee5caf762cb3ba04f7d69b6da4e53958587d44c1638'
SOURCE_COLUMNS = ['text_id', 'prolific_id', 'event_duration', 'emotion_duration']
APPRAISALS = [*math.JUMP, *math.NO_REMEDY, *math.STYLE, 'unpleasantness']


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def dependencies():
    return {Path(m.__file__).as_posix(): io.sha(m.__file__) for m in (original, math, seal, io)} | {Path(__file__).as_posix(): io.sha(__file__)}


def settings(config):
    if set(config)-{'phase', 'draws', 'max_new_draws', 'max_wall_seconds'} or config.get('phase') not in ('IN11-prepare', 'IN11'):
        raise ValueError('Exact declared IN11 phases only')
    if config.get('draws', 2000) != 2000 or type(config.get('max_new_draws', 100)) is not int or config.get('max_new_draws', 100) < 1:
        raise ValueError('Complete 2000 draws and positive whole-unit quantum required')
    if not np.isfinite(config.get('max_wall_seconds', 900)) or config.get('max_wall_seconds', 900) <= 0:
        raise ValueError('Finite positive wall bound required')
    return {'phase': config['phase'], 'draws': 2000, 'duration_ranks': math.RANKS,
        'I_had_none': 'excluded from ordered-duration primary and counted; no elapsed zero',
        'outcomes': 'both standardized within prompt; fixed source scales',
        'indices': 'within-prompt z of raw JUMP and NO_REMEDY differences',
        'event_duration_control': 'same ordered category rank', 'style': list(math.STYLE)}


def load_source(inputs):
    if set(inputs) != {'source_run'}:
        raise ValueError('Qualified original IN source required')
    root, plan, _ = seal.complete(inputs['source_run'], 'runners.drive.cards.week5_in')
    if plan['config'].get('phase') != 'prepare':
        raise ValueError('Original source preparation required')
    archive_path = Path(plan['inputs']['source']); salt_path = Path(plan['inputs']['salt'])
    if io.sha(archive_path) != original.SOURCE_SHA or io.sha(salt_path) != plan['pins'].get(str(salt_path)):
        raise ValueError('Pinned archive or private salt changed')
    if io.sha(root/'output/generation.parquet') != TABLE_PIN:
        raise ValueError('Qualified numeric generation table changed')
    salt = salt_path.read_bytes()
    if len(salt) != 32:
        raise ValueError('Private salt length differs')
    frame = pd.read_parquet(root/'output/generation.parquet', columns=['text_id', 'prolific_id', 'emotion', 'intensity', *APPRAISALS])
    with zipfile.ZipFile(archive_path) as archive:
        with archive.open('corpus/crowd-enVent_generation.tsv') as stream:
            extra = pd.read_csv(stream, sep='\t', usecols=SOURCE_COLUMNS, dtype=str, keep_default_na=False)
    if len(extra) != 6600 or extra.text_id.duplicated().any():
        raise ValueError('Source row cardinality or uniqueness differs')
    for column, namespace in [('text_id', 'crowd-text'), ('prolific_id', 'crowd-person')]:
        extra[column] = extra[column].map(lambda v: original.salted(v, salt, namespace))
    identity = {'source_complete': io.sha(root/'COMPLETE.json'), 'source_plan': io.sha(root/'PLAN.json'),
        'archive': original.SOURCE_SHA, 'salt_sha256': io.sha(salt_path), 'qualified_table': TABLE_PIN,
        'new_columns': ['event_duration', 'emotion_duration'], 'demographic_or_personality_columns_loaded': False}
    return frame, extra, identity


def project(base, extra, independent=False):
    look = extra.set_index('text_id'); rows = []; counts = {'I_had_none': 0, 'missing_duration': 0, 'eligible_negative': 0}
    for row in base.sort_values('text_id').to_dict('records'):
        item = look.loc[row['text_id']]
        if item.prolific_id != row['prolific_id']:
            raise ValueError('Private source writer/text join changed')
        event, emotion = item.event_duration, item.emotion_duration
        if independent:
            options = ['seconds', 'minutes', 'hours', 'days', 'weeks']
            if event not in options+['', '--'] or emotion not in options+['', '--', 'I had none']:
                raise ValueError('Undocumented ordinal duration category')
            er = options.index(event)+1 if event in options else None
            dr = options.index(emotion)+1 if emotion in options else None
        else:
            er, dr = math.rank(event), math.rank(emotion, True)
        none = emotion == 'I had none'; missing = er is None or (dr is None and not none)
        eligible = er is not None and dr is not None and row['emotion'] in math.NEGATIVE
        counts['I_had_none'] += int(none); counts['missing_duration'] += int(missing)
        counts['eligible_negative'] += int(eligible)
        row.update(event_duration_rank=er, emotion_duration_rank=dr, no_emotion_reported=none,
                   missing_duration=missing, model_eligible=eligible)
        rows.append(row)
    return rows, counts


def should_yield(output, start, config, added):
    root = Path(output).parent if Path(output).name == 'independent-replay' else Path(output)
    return (added >= config.get('max_new_draws', 100) or time.monotonic()-start >= config.get('max_wall_seconds', 900)
            or any((root/name).exists() for name in ('YIELD_REQUEST.json', 'STOP_REQUEST.json')))


def prepare(output, inputs, config, independent=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True); semantic = settings(config)
    base, extra, identity = load_source(inputs)
    if base.text_id.duplicated().any() or not set(base.text_id).issubset(set(extra.text_id)):
        raise ValueError('Complete exact source join required')
    binding = digest({'source': identity, 'semantic': semantic, 'modules': dependencies(), 'independent': independent})
    groups = dict(tuple(base.groupby('prolific_id', sort=True))); keys = sorted(groups)
    extra_people = dict(tuple(extra.groupby('prolific_id', sort=True)))
    collected = []; totals = {'I_had_none': 0, 'missing_duration': 0, 'eligible_negative': 0}
    started = time.monotonic(); added = 0
    for index, key in enumerate(keys):
        path = output/'writers'/f'{index:06}.json'
        if path.exists():
            block = seal.state(path, binding, {})
            if block['ordinal'] != index or block['person'] != key:
                raise ValueError('Checkpoint writer ordering differs')
        else:
            if should_yield(output, started, config, added):
                return {'status': 'yielded', 'verified': False, 'phase': 'IN11_source_writers', 'completed': index, 'total': len(keys)}
            rows, counts = project(groups[key], extra_people[key], independent)
            block = {'binding': binding, 'ordinal': index, 'person': key, 'rows': rows, 'counts': counts}
            seal.checkpoint(path, block); added += 1
        collected.extend(block['rows'])
        for name in totals:
            totals[name] += block['counts'][name]
    collected.sort(key=lambda r: r['text_id'])
    seal.checkpoint(output/'TABLE.json', {'rows': collected, 'source_identity': identity, 'counts': totals})
    result = {'card': 'IN11-source', 'record_kind': 'run', 'theory_tags': [], 'by_construction': False, 'activation': [],
        'complete_preparation': True, 'rows': len(collected), 'writers': len(keys), 'counts': totals,
        'source_identity': identity, 'duration_kind': 'ordered category; not elapsed time',
        'qualified_appraisal_rows_preserved': True}
    io.write_json(output/'RESULT.json', result); return result


def load_prepared(inputs):
    if set(inputs) != {'prepared_run'}:
        raise ValueError('Complete IN11 source projection required')
    root, plan, _ = seal.complete(inputs['prepared_run'], MODULE)
    if plan['config'].get('phase') != 'IN11-prepare' or seal.read(root/'output/RESULT.json').get('complete_preparation') is not True:
        raise ValueError('Complete exact IN11 source phase required')
    table = seal.read(root/'output/TABLE.json')
    return pd.DataFrame(table['rows']), {'source_complete': io.sha(root/'COMPLETE.json'),
        'table_sha256': io.sha(root/'output/TABLE.json'), 'source_identity': table['source_identity'], 'counts': table['counts']}


def summarize(point, draws, writers, independent=False):
    failed = [i for i, value in enumerate(draws) if 'failure' in value]
    if 'failure' in point:
        return {'status': 'unsupported', 'reason': point['failure'], 'failed_draws': failed}
    if len(draws) != 2000:
        raise ValueError('Full 2000 writer draws required')
    if failed:
        return {'status': 'invalid_uncertainty', 'estimate': point['value'][0], 'failed_draws': failed,
                'reason': 'all failures retained; no redraw or selected valid subset'}
    intervals, errors = math.interval_se([d['value'] for d in draws], independent)
    primary = {'estimate': point['value'][0], 'interval': intervals[0], 'bootstrap_SE': errors[0],
        'bar': .1, 'sees': 2.8*errors[0], 'supports_at': .1+2.8*errors[0], 'limited_sensitivity': 2.8*errors[0] > .1,
        'approximation': 'normal; slightly optimistic; fixed source scales'}
    if writers >= 20:
        lo, hi = intervals[0]
        primary['outcome'] = ('supports' if lo > .1 else 'against' if hi < -.1 else
            'band-null' if lo >= -.1 and hi <= .1 else 'inconclusive')
    names = ['JUMP_intensity', 'JUMP_duration', 'NO_REMEDY_intensity', 'NO_REMEDY_duration']
    components = {name: {'estimate': point['value'][i+1], 'interval': intervals[i+1], 'bootstrap_SE': errors[i+1]}
                  for i, name in enumerate(names)}
    return {'status': 'complete' if writers >= 20 else 'below floor, descriptive', 'primary': primary,
            'components': components, 'draws': 2000, 'failed_draws': [], 'writers': writers}


def calculate(frame, output, identity, config, independent=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True); semantic = settings(config)
    common = {'card': 'IN11', 'record_kind': 'claim', 'theory_tags': ['H14-rate-level', 'H15-Q2'],
        'by_construction': False, 'activation': [], 'source_identity': identity, 'semantic': semantic,
        'scope': 'prompted adult recollection; standardized ordered duration, not elapsed time',
        'source_gap': 'R13-R15 supporting handoffs absent; explicit packet and ordinal ruling govern'}
    try:
        prepared = math.prepare(frame, independent)
    except ValueError as error:
        return {**common, 'status': 'unsupported', 'complete_card': True, 'reason': str(error)}
    if prepared is None or len(prepared['keys']) < 2:
        return {**common, 'status': 'unsupported', 'complete_card': True, 'reason': 'fewer than two complete writers'}
    binding = digest({'source': identity, 'semantic': semantic, 'modules': dependencies(),
                      'frame': frame.to_json(orient='split'), 'independent': independent})
    saved = seal.state(output/'DRAWS.json', binding, {'point': None, 'draws': []})
    if saved['point'] is None:
        saved['point'] = math.evaluate(prepared, np.ones(len(prepared['keys'])), independent)
        seal.checkpoint(output/'DRAWS.json', saved)
    start = time.monotonic(); cpu = time.process_time(); added = 0
    while len(saved['draws']) < 2000:
        if should_yield(output, start, config, added):
            seal.checkpoint(output/'DRAWS.json', saved)
            return {'status': 'yielded', 'verified': False, 'phase': 'IN11_writer_draws', 'completed': len(saved['draws']), 'total': 2000}
        saved['draws'].append(math.evaluate(prepared, math.draw(len(prepared['keys']), len(saved['draws'])), independent)); added += 1
        if added == 1 and not (output/'COST_PREFIX.json').exists():
            io.write_json(output/'COST_PREFIX.json', {'first_draw_CPU_seconds': time.process_time()-cpu,
                'excludes_source_IO_point_and_complete_replay': True})
        if len(saved['draws']) % 10 == 0:
            seal.checkpoint(output/'DRAWS.json', saved)
            io.write_json(output/'PROGRESS.json', {'phase': 'IN11_writer_draws', 'completed': len(saved['draws']), 'total': 2000})
    seal.checkpoint(output/'DRAWS.json', saved)
    result = {**common, **summarize(saved['point'], saved['draws'], len(prepared['keys']), independent),
        'complete_card': True, 'prompt_counts': prepared['counts'], 'all_failed_draws_retained': True,
        'by_construction_control': 'event duration category included in both fits; long events permit long emotions',
        'strongest_rivals': ['retrospective prompt fitting', 'ordinal scale spacing', 'shared self-report style'],
        'not_tested': 'instantaneous rate of a biological channel or elapsed emotional persistence'}
    if set(prepared['prompts']) != set(math.NEGATIVE):
        result['status'] = 'missing negative prompts, descriptive'
        result.get('primary', {}).pop('outcome', None)
    return result


def execute(output, inputs, config):
    settings(config)
    if config['phase'] == 'IN11-prepare':
        return prepare(output, inputs, config)
    frame, identity = load_prepared(inputs); result = calculate(frame, output, identity, config)
    if result.get('status') != 'yielded':
        io.write_json(Path(output)/'RESULT.json', result)
    return result


def compare(a, b):
    if isinstance(a, dict):
        if not isinstance(b, dict) or set(a) != set(b):
            raise ValueError('Independent field inventory differs')
        for key in a:
            compare(a[key], b[key])
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            raise ValueError('Independent list inventory differs')
        for x, y in zip(a, b, strict=True):
            compare(x, y)
    elif isinstance(a, (int, float)) and not isinstance(a, bool):
        if not isinstance(b, (int, float)) or not np.isclose(a, b, atol=1e-7, rtol=0):
            raise ValueError('Independent numerical formula differs')
    elif a != b:
        raise ValueError('Independent value differs')


def verify(output, inputs, config):
    settings(config); output = Path(output); replay = output/'independent-replay'
    if config['phase'] == 'IN11-prepare':
        result = prepare(replay, inputs, config, True)
        if result.get('status') == 'yielded':
            return {**result, 'verified': False}
        compare(seal.read(output/'TABLE.json'), seal.read(replay/'TABLE.json'))
    else:
        frame, identity = load_prepared(inputs); result = calculate(frame, replay, identity, config, True)
        if result.get('status') == 'yielded':
            return {**result, 'verified': False}
        if (output/'DRAWS.json').exists():
            a, b = seal.read(output/'DRAWS.json'), seal.read(replay/'DRAWS.json')
            if len(a['draws']) != 2000 or len(b['draws']) != 2000:
                raise ValueError('Full intended original/replay draw banks required')
            compare(a['point'], b['point']); compare(a['draws'], b['draws'])
    compare(seal.read(output/'RESULT.json'), result); io.write_json(replay/'RESULT.json', result)
    return {'verified': True, 'independent_all_values_and_source_projection': True,
            'independent_row_level_solver': config['phase'] == 'IN11', 'ordinal_not_elapsed': True}
