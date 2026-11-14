"""Two-day IN12: two permitted personality items and fixed-scale appraisal fits.

DESIGN CHECK: LESSONS 2-5, CONTROLS 6-7. Only anxious/calm plus private
join keys are projected from the archive. The qualified appraisal source is
reused unchanged; no demographics, other personality items or text are loaded.
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
from . import week5_in12_math_v1 as math
from . import week5_engine_export_io as seal
from . import week5_qualification_io as io

MODULE = 'runners.drive.cards.week5_in12_v1'
TABLE_PIN = '196fe2a4f72b36ae91516ee5caf762cb3ba04f7d69b6da4e53958587d44c1638'
QUESTIONNAIRE = 'questionnaires/generation/round-2/strategy1_free/anger.pdf'
QUESTIONNAIRE_PIN = '51df6525820fc973d2e45019d316ed56d35198f5804491c31ee05d93b372a068'
SOURCE_COLUMNS = ['text_id', 'prolific_id', 'anxious', 'calm']


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def dependencies():
    return {Path(m.__file__).as_posix(): io.sha(m.__file__) for m in (original, math, seal, io)} | {Path(__file__).as_posix(): io.sha(__file__)}


def settings(config):
    if set(config)-{'phase', 'draws', 'max_new_draws', 'max_wall_seconds'}:
        raise ValueError('Undeclared IN12 settings')
    if config.get('phase') not in ('IN12-prepare', 'IN12') or config.get('draws', 2000) != 2000:
        raise ValueError('Exact IN12 source or complete 2000 writer draws required')
    if type(config.get('max_new_draws', 100)) is not int or config.get('max_new_draws', 100) < 1:
        raise ValueError('Positive whole-unit quantum required')
    if not np.isfinite(config.get('max_wall_seconds', 900)) or config.get('max_wall_seconds', 900) <= 0:
        raise ValueError('Positive finite wall bound required')
    return {'phase': config['phase'], 'draws': 2000, 'N': '(anxious+8-calm)/2; raw 1-to-7 points',
        'intensity_scale': 'fixed within-prompt sample SD among complete two-item writers',
        'style': list(math.STYLE), 'spread': 'RMS of six negative prompt slopes around pooled slope',
        'pairs': 'equal-writer weighted prompt-mean pairs; ordered distinct-negative versus negative-positive'}


def load_source(inputs):
    if set(inputs) != {'source_run'}:
        raise ValueError('Qualified original IN source run required')
    root, plan, _ = seal.complete(inputs['source_run'], 'runners.drive.cards.week5_in')
    if plan['config'].get('phase') != 'prepare':
        raise ValueError('Qualified original preparation phase required')
    source = Path(plan['inputs']['source']); salt_path = Path(plan['inputs']['salt'])
    if io.sha(source) != original.SOURCE_SHA or io.sha(salt_path) != plan['pins'].get(str(salt_path)):
        raise ValueError('Original archive or private join salt differs')
    salt = salt_path.read_bytes()
    if len(salt) != 32 or io.sha(root/'output/generation.parquet') != TABLE_PIN:
        raise ValueError('Original qualified generation or salt shape differs')
    columns = ['text_id', 'prolific_id', 'emotion', 'intensity', 'confidence', *math.STYLE]
    frame = pd.read_parquet(root/'output/generation.parquet', columns=columns)
    with zipfile.ZipFile(source) as archive:
        readme = archive.read('readme.txt').decode('utf8')
        if 'Gosling et al.' not in readme or '`1-to-7` scale' not in readme:
            raise ValueError('Required short-form inventory documentation unavailable')
        if hashlib.sha256(archive.read(QUESTIONNAIRE)).hexdigest() != QUESTIONNAIRE_PIN:
            raise ValueError('Blank inventory wording changed')
        with archive.open('corpus/crowd-enVent_generation.tsv') as stream:
            extra = pd.read_csv(stream, sep='\t', usecols=SOURCE_COLUMNS, dtype=str, keep_default_na=False)
    if len(extra) != 6600 or extra.text_id.duplicated().any():
        raise ValueError('Original source cardinality/key uniqueness differs')
    for column, namespace in [('text_id', 'crowd-text'), ('prolific_id', 'crowd-person')]:
        extra[column] = extra[column].map(lambda v: original.salted(v, salt, namespace))
    for column in ('anxious', 'calm'):
        missing = extra[column].isin(['', '--'])
        extra[column] = pd.to_numeric(extra[column].mask(missing), errors='raise')
        present = extra[column].notna()
        if not extra.loc[present, column].between(1, 7).all():
            raise ValueError('Undocumented personality scale or missing-value marker')
    identity = {'source_complete': io.sha(root/'COMPLETE.json'), 'source_plan': io.sha(root/'PLAN.json'),
        'source_archive': original.SOURCE_SHA, 'qualified_table': TABLE_PIN,
        'salt_sha256': io.sha(salt_path), 'blank_questionnaire_sha256': QUESTIONNAIRE_PIN,
        'projected_new_columns': ['anxious', 'calm'], 'demographic_columns_loaded': False}
    return frame, extra, identity


def project_person(base, extra, independent=False):
    pair_rows = extra[['anxious', 'calm']].dropna()
    if independent:
        pairs = sorted(set((float(r.anxious), float(r.calm)) for r in pair_rows.itertuples()))
    else:
        pairs = list(pair_rows.drop_duplicates().itertuples(index=False, name=None))
    status = 'available' if len(pairs) == 1 else ('missing' if not pairs else 'conflicting_source_items')
    n = None
    if status == 'available':
        a, c = pairs[0]
        n = float((a+(8-c))/2) if independent else float(math.item_score(a, c))
    output = base.sort_values('text_id').to_dict('records')
    for row in output:
        row.update(N=n, personality_support=status)
    return output, status


def should_yield(output, start, config, added):
    root = Path(output).parent if Path(output).name == 'independent-replay' else Path(output)
    return (added >= config.get('max_new_draws', 100) or time.monotonic()-start >= config.get('max_wall_seconds', 900)
            or any((root/name).exists() for name in ('YIELD_REQUEST.json', 'STOP_REQUEST.json')))


def prepare(output, inputs, config, independent=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    semantic = settings(config); base, extra, identity = load_source(inputs)
    if base.text_id.duplicated().any() or not set(base.text_id).issubset(set(extra.text_id)):
        raise ValueError('Qualified source cannot be joined exactly')
    joined = base[['text_id', 'prolific_id']].merge(extra[['text_id', 'prolific_id']], on='text_id', suffixes=('_base', '_extra'), validate='one_to_one')
    if not joined.prolific_id_base.eq(joined.prolific_id_extra).all():
        raise ValueError('Private writer/text linkage differs')
    binding = digest({'source': identity, 'semantic': semantic, 'modules': dependencies(), 'independent': independent})
    keys = sorted(base.prolific_id.unique()); source_people = {k: v for k, v in extra.groupby('prolific_id', sort=True)}
    qualified = {k: v for k, v in base.groupby('prolific_id', sort=True)}
    output_rows = []; counts = {'available': 0, 'missing': 0, 'conflicting_source_items': 0}
    started = time.monotonic(); added = 0
    for index, key in enumerate(keys):
        path = output/'writers'/f'{index:06}.json'
        if path.exists():
            block = seal.state(path, binding, {})
            if block['ordinal'] != index or block['person'] != key:
                raise ValueError('Writer checkpoint ordering differs')
        else:
            if should_yield(output, started, config, added):
                return {'status': 'yielded', 'verified': False, 'phase': 'IN12_source_writers', 'completed': index, 'total': len(keys)}
            rows, status = project_person(qualified[key], source_people[key], independent)
            block = {'binding': binding, 'ordinal': index, 'person': key, 'status': status, 'rows': rows}
            seal.checkpoint(path, block); added += 1
        output_rows.extend(block['rows']); counts[block['status']] += 1
    output_rows.sort(key=lambda r: r['text_id'])
    table = {'source_identity': identity, 'rows': output_rows, 'personality_writer_counts': counts}
    seal.checkpoint(output/'TABLE.json', table)
    result = {'card': 'IN12-source', 'complete_preparation': True, 'record_kind': 'run', 'theory_tags': [],
        'by_construction': False, 'activation': [], 'rows': len(output_rows), 'writers': len(keys),
        'personality_writer_counts': counts, 'source_identity': identity,
        'new_columns': ['anxious', 'calm'], 'output_measure': 'N only; no individual personality output is public',
        'demographics_read': False, 'qualified_appraisal_rows_preserved': True}
    io.write_json(output/'RESULT.json', result)
    return result


def load_prepared(inputs):
    if set(inputs) != {'prepared_run'}:
        raise ValueError('Complete IN12 two-item projection required')
    root, plan, _ = seal.complete(inputs['prepared_run'], MODULE)
    if plan['config'].get('phase') != 'IN12-prepare':
        raise ValueError('IN12 source phase required')
    result = seal.read(root/'output/RESULT.json')
    if result.get('complete_preparation') is not True:
        raise ValueError('Complete IN12 source projection required')
    table = seal.read(root/'output/TABLE.json')
    return pd.DataFrame(table['rows']), {'source_complete': io.sha(root/'COMPLETE.json'),
        'prepared_table': io.sha(root/'output/TABLE.json'), 'source_identity': table['source_identity'],
        'personality_writer_counts': table['personality_writer_counts']}


def summarize(name, point, draws, writers, independent=False):
    bad = [i for i, d in enumerate(draws) if d['value'].get(name) is None]
    base = {'draws': len(draws), 'failed_draws': bad, 'writers': writers}
    if point['value'].get(name) is None:
        return {**base, 'status': 'unsupported', 'reason': point['failures'].get(name)}
    if len(draws) != 2000:
        raise ValueError('Complete 2000-draw bank required')
    if bad:
        return {**base, 'status': 'invalid_uncertainty', 'estimate': point['value'][name],
                'reason': 'all failed draws retained; no redraw or selected valid subset'}
    interval, se = math.interval_se([d['value'][name] for d in draws], independent)
    result = {**base, 'status': 'complete' if writers >= 20 else 'below floor, descriptive',
        'estimate': point['value'][name], 'interval': interval, 'bootstrap_SE': se}
    if name == 'pooled':
        result.update(bar=.1, sees=2.8*se, supports_at=.1+2.8*se, limited_sensitivity=2.8*se > .1,
                      approximation='normal; slightly optimistic; fixed source scales')
        if writers >= 20:
            result['outcome'] = ('supports' if interval[0] > .1 else 'against' if interval[1] < -.1 else
                'band-null' if interval[0] >= -.1 and interval[1] <= .1 else 'inconclusive')
    return result


def calculate(frame, output, identity, config, independent=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True); semantic = settings(config)
    prepared = math.prepare(frame, independent); keys = prepared['keys']
    common = {'card': 'IN12', 'record_kind': 'claim', 'theory_tags': ['H15-T11', 'DISAGREE-6'],
        'by_construction': False, 'activation': [], 'scope': 'adult prompted self-report; lowercase evidence',
        'source_identity': identity, 'source_gap': 'R13-R15 supporting handoffs absent; explicit packet governs',
        'semantic': semantic, 'prompt_counts': frame.groupby('emotion').size().to_dict(),
        'units': 'within-prompt intensity SD per one raw N item point',
        'scale_scope': 'fixed full eligible source scales; refit every regression in each whole-writer resample'}
    if len(keys) < 2:
        return {**common, 'status': 'unsupported', 'complete_card': True, 'reason': 'fewer than two eligible writers'}
    binding = digest({'source': identity, 'semantic': semantic, 'modules': dependencies(),
                      'frame': frame.to_json(orient='split'), 'independent': independent})
    saved = seal.state(output/'DRAWS.json', binding, {'point': None, 'draws': []})
    if saved['point'] is None:
        saved['point'] = math.evaluate(prepared, dict.fromkeys(keys, 1), independent)
        seal.checkpoint(output/'DRAWS.json', saved)
    started = time.monotonic(); cpu = time.process_time(); added = 0
    while len(saved['draws']) < 2000:
        if should_yield(output, started, config, added):
            seal.checkpoint(output/'DRAWS.json', saved)
            return {'status': 'yielded', 'verified': False, 'phase': 'IN12_writer_draws', 'completed': len(saved['draws']), 'total': 2000}
        saved['draws'].append(math.evaluate(prepared, math.resample(keys, len(saved['draws'])), independent)); added += 1
        if added == 1 and not (output/'COST_PREFIX.json').exists():
            io.write_json(output/'COST_PREFIX.json', {'first_draw_CPU_seconds': time.process_time()-cpu,
                'excludes_source_IO_point_and_complete_independent_replay': True})
        if len(saved['draws']) % 10 == 0:
            seal.checkpoint(output/'DRAWS.json', saved)
            io.write_json(output/'PROGRESS.json', {'phase': 'IN12_writer_draws', 'completed': len(saved['draws']), 'total': 2000})
    seal.checkpoint(output/'DRAWS.json', saved)
    answers = {}
    for name in saved['point']['value']:
        panel = prepared['panels'].get(name)
        writers = len(panel['keys']) if panel else len(keys)
        if name == 'within_writer_correlation_difference':
            writers = min(len({r[0] for r in rows}) for rows in prepared['pairs'][:2])
        answers[name] = summarize(name, saved['point'], saved['draws'], writers, independent)
    pooled = answers.pop('pooled')
    if prepared['panels']['pooled'] and set(prepared['panels']['pooled']['prompts']) != set(math.NEGATIVE):
        pooled.pop('outcome', None); pooled['status'] = 'missing negative prompts, descriptive'
    pair_eligible = prepared['pairs'][2]
    if pair_eligible < 300:
        answers['within_writer_correlation_difference'] = {'status': 'unsupported', 'eligible_writers': pair_eligible,
            'required': 300, 'reason': 'fewer than 300 writers with at least two distinct negative prompts'}
    result = {**common, 'status': 'complete', 'complete_card': True, 'primary': pooled, 'secondary': answers,
        'paired_support': {'eligible_writers': pair_eligible, 'negative_pairs': len(prepared['pairs'][0]),
                           'negative_positive_pairs': len(prepared['pairs'][1]),
                           'negative_pair_writers': len({r[0] for r in prepared['pairs'][0]}),
                           'negative_positive_pair_writers': len({r[0] for r in prepared['pairs'][1]}),
                           'interpretation': 'cross-prompt paired-report association, not within-person time-series correlation'},
        'scales': prepared['scales'], 'failed_draws_never_removed': True,
        'strongest_rivals': ['shared self-report style', 'prompted recollection', 'neuroticism item wording overlaps distress'],
        'does_not_identify': 'one biological cause versus several systems; personality is adult self-report'}
    result['activation'] = [{'channel': k, 'set_point': 'common stress-band proposal awaiting ruling',
        'what_moved': 'two-item adult self-report N', 'what_could_be_done': 'not measured',
        'observed': {'pooled_negative_slope': pooled.get('estimate'), 'status': pooled['status']},
        'relation': 'prompted report association does not identify a neural channel'} for k in ('FEAR', 'PANIC/GRIEF', 'RAGE')]
    return result


def execute(output, inputs, config):
    settings(config)
    if config['phase'] == 'IN12-prepare':
        return prepare(output, inputs, config)
    frame, identity = load_prepared(inputs)
    result = calculate(frame, output, identity, config)
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
            raise ValueError('Independent list coverage differs')
        for x, y in zip(a, b, strict=True):
            compare(x, y)
    elif isinstance(a, (float, int)) and not isinstance(a, bool):
        if not isinstance(b, (float, int)) or not np.isclose(a, b, atol=1e-7, rtol=0):
            raise ValueError('Independent numerical formula differs')
    elif a != b:
        raise ValueError('Independent value differs')


def verify(output, inputs, config):
    settings(config); output = Path(output); replay = output/'independent-replay'
    if config['phase'] == 'IN12-prepare':
        answer = prepare(replay, inputs, config, True)
        if answer.get('status') == 'yielded':
            return {**answer, 'verified': False}
        compare(seal.read(output/'TABLE.json'), seal.read(replay/'TABLE.json'))
    else:
        frame, identity = load_prepared(inputs)
        answer = calculate(frame, replay, identity, config, True)
        if answer.get('status') == 'yielded':
            return {**answer, 'verified': False}
        if (output/'DRAWS.json').exists():
            left, right = seal.read(output/'DRAWS.json'), seal.read(replay/'DRAWS.json')
            if len(left['draws']) != 2000 or len(right['draws']) != 2000:
                raise ValueError('Complete original and replay draw banks required')
            compare(left['point'], right['point']); compare(left['draws'], right['draws'])
    compare(seal.read(output/'RESULT.json'), answer)
    io.write_json(replay/'RESULT.json', answer)
    return {'verified': True, 'all_values_independently_replayed': True,
            'independent_row_level_solver': config['phase'] == 'IN12', 'no_demographics_read': True}
