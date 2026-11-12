"""R2 April-calibrated streaming CH1 collection successor.

DESIGN CHECK: exact complete-population joins, original sorted-key summation,
fresh replay and three byte-identical scientific outputs precede admission.
SQLite bounds numeric-row memory. Optimizer/gzip interruption restarts that
unit; a row quantum is not a claim to cover five percent of total CPU work.
"""
from collections import Counter
from pathlib import Path
import gzip
import json
import math
import os
import sqlite3
import time

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp

from . import week5_ch_collection as original
from . import week5_ch_engine as engine
from . import week5_ch_pipeline_checkpoint as ck
from .week5_ch_source import digest, write_json


FILES = ('PRIVATE_ANALYTICAL_ROWS.jsonl.gz', 'TEMPERATURES.json', 'COLLECTION.json')
METADATA_CAP = 16 * 1024**2
ROW_CAP = 4 * 1024**2
TRANSACTION_ROWS = 100


def read_json(path, maximum=METADATA_CAP):
    """A resource refusal, never truncation or selection of part of a source."""
    with Path(path).open('rb') as stream:
        value = stream.read(maximum + 1)
    if len(value) > maximum:
        raise ValueError('JSON metadata exceeds the declared memory bound')
    return json.loads(value)


def identity(inputs, config):
    if set(inputs) != {'positions', 'batches'}:
        raise ValueError('Exact frozen roster and batch manifest required')
    allowed = {'nodes', 'constructed_fixture', 'max_new_draws', 'expected_positions'}
    if set(config) - allowed:
        raise ValueError('Unknown collection setting')
    count = config.get('expected_positions')
    nodes = config.get('nodes', 1000000)
    if type(count) is not int or not 1 <= count <= 400000:
        raise ValueError('Complete source-bound position denominator required')
    if type(nodes) is not int or nodes not in (300000, 1000000, 3000000):
        raise ValueError('Unregistered node count')
    return ck.binding(inputs, config, dict(
        adapter=digest(__file__), original_collection=digest(original.__file__),
        original_engine=digest(engine.__file__)))


class Control:
    """Operational completed-row quantum, honored by execute AND verify."""
    def __init__(self, output, request_root, config, operation):
        self.output = Path(output)
        self.root = Path(request_root)
        self.operation = operation
        self.quantum = config.get('max_new_draws')
        self.new = 0
        self.started = time.process_time()
        self.phase = 'authentication'
        self.done = 0
        self.total = None

    def check(self):
        if ck.requested(self.root):
            raise ck.YieldRequested('Owner request at collection boundary')
        if self.quantum is not None and self.new >= self.quantum:
            raise ck.YieldRequested('Completed collection-unit quantum reached')

    def advance(self, phase, done, total):
        self.new += 1
        self.phase, self.done, self.total = phase, done, total

    def record(self):
        write_json(self.output / 'PROGRESS.json', dict(
            operation=self.operation, phase=self.phase, completed=self.done,
            total=self.total, new_this_invocation=self.new,
            invocation_cpu_seconds=time.process_time() - self.started,
            unit='one roster/score/analytical/export row or complete target-band fit',
            five_percent_total_work_claim=False, population_complete=False), mutable=True)


def authenticate(inputs, config, check):
    roster = ck.checked(inputs['positions'], check)
    manifest = read_json(ck.checked(inputs['batches'], check))
    batches = manifest['batches']
    if not isinstance(batches, list) or not batches:
        raise ValueError('Nonempty frozen batch manifest required')
    return roster, batches, config['expected_positions'], config.get('nodes', 1000000)


def batch_files(batch, nodes, check):
    proof = read_json(ck.checked(batch['verify'], check))
    report = read_json(ck.checked(batch['report'], check))
    bindings = read_json(ck.checked(batch['score_bindings'], check))
    files = []
    for path in Path(batch['path']).glob('*.json'):
        check()
        files.append(path)
        if len(files) > 1024:
            raise ValueError('Batch exceeds frozen filler interval bound')
    files.sort()
    if not proof.get('all_scores_equal') or proof['verified_positions'] != len(files):
        raise ValueError('Unverified batch')
    if report['node_limit'] != nodes or report['new_positions'] + report['reused_positions'] != len(files):
        raise ValueError('Batch count mismatch')
    if set(bindings) != {path.name for path in files}:
        raise ValueError('Incomplete score bindings')
    return files, bindings


def create_tables(con):
    con.execute('PRAGMA journal_mode=DELETE')
    con.execute('PRAGMA synchronous=FULL')
    con.execute('PRAGMA temp_store=FILE')
    con.execute('PRAGMA cache_size=-8192')
    con.execute('CREATE TABLE IF NOT EXISTS roster(key TEXT PRIMARY KEY,payload TEXT NOT NULL,player TEXT,month TEXT,band INTEGER)')
    con.execute('CREATE INDEX IF NOT EXISTS calibration_order ON roster(month,band,key)')
    con.execute('CREATE TABLE IF NOT EXISTS scores(key TEXT PRIMARY KEY,payload TEXT NOT NULL)')
    con.execute('CREATE TABLE IF NOT EXISTS fits(month TEXT,band INTEGER,payload TEXT NOT NULL,PRIMARY KEY(month,band))')
    con.execute('CREATE TABLE IF NOT EXISTS analytical(key TEXT PRIMARY KEY,payload TEXT NOT NULL)')


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def joined(value):
    # Literal original merge, with an explicit refusal for a malformed scorer
    # that attempts to overwrite a position field. The real scorer has no such
    # fields, and no scientific row is filtered by this structural assertion.
    if set(value['position']) & set(value['engine']):
        raise ValueError('Score attempts to overwrite frozen position fields')
    return dict(value['position'], **value['engine'])


def calibration(con, donor, band, check):
    cursor = con.execute('SELECT s.payload FROM roster r JOIN scores s ON s.key=r.key '
                         'WHERE r.month=? AND r.band=? ORDER BY r.key', (donor, band))
    for (payload,) in cursor:
        check()
        row = joined(json.loads(payload))
        if row['mate_sentinel_used']:
            continue
        values = [item['cp'] for item in row['top']]
        index = next((i for i, item in enumerate(row['top']) if item['move'] == row['uci']), None)
        yield values, index


def fit_stream(con, target, donor, band, check):
    """Same optimizer and scalar summation order as engine.fit_temperature.

    A yield discards this group's unfinished optimizer, not any source rows.
    Every new objective traversal uses the identical sorted source-key order.
    No chunk reduction, vectorized reassociation or approximate fit is used.
    """
    total = supported = 0
    for _, index in calibration(con, donor, band, check):
        total += 1
        supported += index is not None
    if supported < 20:
        fit = dict(status='below floor, descriptive', temperature=100.,
                   supported=supported, fallback='fixed 100 centipawns')
    else:
        def objective(logtemp):
            temperature = math.exp(logtemp)
            # Built-in sum starts with the same integer zero as the original.
            # Each subsequent numpy scalar operation and row order is retained.
            return sum(logsumexp(values / temperature) - values[index] / temperature
                       for scores, index in calibration(con, donor, band, check)
                       if index is not None
                       for values in (np.asarray(scores, float),))
        fitted = minimize_scalar(objective, bounds=(math.log(1.), math.log(10000.)), method='bounded')
        if not fitted.success:
            raise ValueError('Temperature optimization failed')
        fit = dict(status='fitted', temperature=math.exp(fitted.x),
                   supported=supported, excluded=total-supported)
    fit.update(target_month=target, calibration_month=donor, rating_band=int(band),
               outside_top_five=total-supported)
    return fit


def next_private(root, stem, suffix=''):
    index = 1
    while True:
        path = root / (stem + f'-{index:06}' + suffix)
        if not path.exists():
            return path
        index += 1


def run(output, request_root, inputs, config, operation):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    bound = identity(inputs, config)
    control = Control(output, request_root, config, operation)
    roster, batches, total, nodes = authenticate(inputs, config, control.check)
    db = output / 'PRIVATE_COLLECTION.sqlite'
    if db.exists():
        if operation != 'execute':
            raise ValueError('Fresh verifier workspace must be empty')
        ck.copied(db, request_root, control.check)
    con = sqlite3.connect(db)
    create_tables(con)
    state = ck.initialize(con, bound, dict(
        phase='roster', roster=0, batch=0, file=0, scores=0,
        fit=0, analytical=0, last_key='', counts={}))

    def save():
        ck.put(con, 'state', state)
        con.commit()
        control.record()

    def advanced(phase, done, denominator):
        control.advance(phase, done, denominator)
        if control.new % TRANSACTION_ROWS == 0:
            save()

    try:
        if state['phase'] == 'roster':
            with gzip.open(roster, 'rb') as stream:
                index = 0
                while True:
                    control.check()
                    line = stream.readline(ROW_CAP + 1)
                    if not line:
                        break
                    if len(line) > ROW_CAP:
                        raise ValueError('Roster row exceeds memory bound')
                    index += 1
                    if index <= state['roster']:
                        continue
                    row = json.loads(line)
                    key = engine.score_key(row, nodes)
                    try:
                        con.execute('INSERT INTO roster VALUES(?,?,?,?,?)',
                                    (key, compact(row), row['player'], row['month'], row['rating']//400))
                    except sqlite3.IntegrityError as exc:
                        raise ValueError('Duplicate frozen position') from exc
                    state['roster'] = index
                    if index > total:
                        raise ValueError('Frozen roster exceeds admitted denominator')
                    advanced('roster_rows', index, total)
            if index != total:
                raise ValueError('Complete frozen roster denominator differs')
            state['phase'] = 'scores'
            save()

        if state['phase'] == 'scores':
            for batch_index, batch in enumerate(batches):
                if batch_index < state['batch']:
                    continue
                files, bindings = batch_files(batch, nodes, control.check)
                for file_index, path in enumerate(files):
                    control.check()
                    if file_index < state['file']:
                        continue
                    if ck.file_digest(path, control.check) != bindings[path.name]:
                        raise ValueError('Score changed after replay')
                    value = read_json(path, ROW_CAP)
                    key = engine.score_key(value['position'], value['node_limit'])
                    expected = con.execute('SELECT payload FROM roster WHERE key=?', (key,)).fetchone()
                    if key != path.stem or expected is None or value['position'] != json.loads(expected[0]):
                        raise ValueError('Score outside frozen roster')
                    joined(value)
                    try:
                        con.execute('INSERT INTO scores VALUES(?,?)', (key, compact(value)))
                    except sqlite3.IntegrityError as exc:
                        raise ValueError('Duplicate scored position') from exc
                    state.update(file=file_index+1, scores=state['scores']+1)
                    advanced('score_rows', state['scores'], total)
                state.update(batch=batch_index+1, file=0)
                save()
            if state['scores'] != total:
                raise ValueError('Incomplete frozen roster')
            state['phase'] = 'fits'
            save()

        if state['phase'] == 'fits':
            # Month/band metadata is bounded explicitly; raw rows stay on disk.
            groups = con.execute('SELECT DISTINCT month,band FROM roster ORDER BY month,band').fetchmany(1025)
            if len(groups) > 1024:
                raise ValueError('Calibration metadata exceeds declared resource bound')
            months = sorted({month for month, _ in groups})
            if months != ['2017-04', '2017-05', '2017-06']:
                raise ValueError('Exact R2 three-month roster required')
            for index, (target, band) in enumerate(groups):
                if index < state['fit']:
                    continue
                control.check()
                donor = '2017-04'
                fit = fit_stream(con, target, donor, band, control.check)
                con.execute('INSERT INTO fits VALUES(?,?,?)', (target, band, compact(fit)))
                state['fit'] = index+1
                advanced('complete_target_band_fits', index+1, len(groups))
                save()
            state['phase'] = 'analytical'
            save()

        if state['phase'] == 'analytical':
            counts = Counter(state['counts'])
            cursor = con.execute('SELECT key,payload FROM scores WHERE key>? ORDER BY key', (state['last_key'],))
            for key, payload in cursor:
                control.check()
                row = joined(json.loads(payload))
                fit = json.loads(con.execute('SELECT payload FROM fits WHERE month=? AND band=?',
                                             (row['month'], row['rating']//400)).fetchone()[0])
                if row['month'] == '2017-04':
                    row.update(entropy=None, entropy_fixed100=None, policy_entropy_analysis_eligible=False)
                    counts['april_calibration_only'] += 1
                elif row['mate_sentinel_used']:
                    row.update(entropy=None, entropy_fixed100=None)
                    counts['mating_entropy_excluded'] += 1
                else:
                    values = [item['cp'] for item in row['top']]
                    row.update(entropy=engine.policy_entropy(values, fit['temperature']) if fit['status']=='fitted' else None,
                               entropy_fixed100=engine.policy_entropy(values, 100.))
                    counts['fitted_entropy' if row['entropy'] is not None else 'uncalibrated_entropy'] += 1
                con.execute('INSERT INTO analytical VALUES(?,?)', (key, compact(row)))
                state.update(last_key=key, analytical=state['analytical']+1, counts=dict(counts))
                advanced('analytical_rows', state['analytical'], total)
            if state['analytical'] != total:
                raise ValueError('Incomplete analytical output')
            state['phase'] = 'gzip'
            save()

        if state['phase'] == 'gzip':
            # One gzip member with the original header/write calls is necessary
            # for exact byte parity. Interrupted members are retained and a new
            # attempt restarts publication from row zero; no prefix is credited.
            partial = next_private(output, 'PRIVATE_ANALYTICAL_ROWS.partial', '.gz')
            with partial.open('xb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0, filename='') as stream:
                for index, (payload,) in enumerate(con.execute('SELECT payload FROM analytical ORDER BY key'), 1):
                    control.check()
                    stream.write((payload+'\n').encode())
                    advanced('gzip_rows_restart_on_interrupt', index, total)
            # A completed gzip member can be published at the exact row
            # quantum. Requiring one more row credit here would restart a
            # fully written member forever when quantum == its row count.
            ck.require(request_root)
            final_check = lambda: ck.require(request_root)
            destination = output / FILES[0]
            if destination.exists():
                if ck.file_digest(destination, final_check) != ck.file_digest(partial, final_check):
                    raise ValueError('Existing analytical publication differs')
            else:
                os.replace(partial, destination)
            fits = [json.loads(row[0]) for row in con.execute('SELECT payload FROM fits ORDER BY month,band')]
            pins = [dict(verify_sha256=batch['verify']['sha256'], report_sha256=batch['report']['sha256'],
                         bindings_sha256=batch['score_bindings']['sha256']) for batch in batches]
            receipt = dict(positions=total, players=con.execute('SELECT COUNT(DISTINCT player) FROM roster').fetchone()[0],
                           node_limit=nodes, batch_pins=pins, population_complete=True,
                           policy_entropy_calibration_month='2017-04',
                           policy_entropy_analysis_months=['2017-05','2017-06'],
                           constructed_fixture=bool(config.get('constructed_fixture')),
                           roster_sha256=inputs['positions']['sha256'],
                           batches_manifest_sha256=inputs['batches']['sha256'],
                           rows_sha256=ck.file_digest(destination, final_check))
            write_json(output / 'TEMPERATURES.json', dict(fits=fits, counts=state['counts']))
            write_json(output / 'COLLECTION.json', receipt)
            state['phase'] = 'complete'
            save()
        return dict(status='complete', positions=total, population_complete=True)
    except ck.YieldRequested as exc:
        save()
        return dict(status='yielded', reason=str(exc), operation=operation,
                    phase=state['phase'], completed=control.done, total=control.total,
                    new_completed_units=control.new, population_complete=False,
                    verification_prefix_credited=False,
                    optimizer_and_gzip_partial_work_reused=False,
                    five_percent_total_work_claim=False)
    except BaseException:
        con.rollback()
        raise
    finally:
        con.close()


def _execute(output, inputs, config):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    bound = identity(inputs, config)
    check = lambda: ck.require(output)
    if ck.sealed(output, bound, check):
        return dict(status='complete', sealed_output_reused=True)
    result = run(output, output, inputs, config, 'execute')
    if result['status'] == 'complete':
        ck.seal(output, bound, FILES, check)
    return result


def _verify(output, inputs, config):
    output = Path(output)
    check = lambda: ck.require(output)
    if not ck.sealed(output, identity(inputs, config), check):
        raise ValueError('Complete collection execution required')
    independent = next_private(output, 'independent_collection')
    result = run(independent, output, inputs, config, 'verify')
    if result['status'] == 'yielded':
        return result
    for name in FILES:
        if ck.file_digest(output/name, check) != ck.file_digest(independent/name, check):
            raise ValueError('Full source collection replay differs: '+name)
    return dict(verified=True, complete_recalculation=True,
                roster_and_all_score_files_replayed=True,
                execution_rows_or_fits_reused=False,
                verification_prefix_credited=False,
                exact_scientific_files=list(FILES))


def execute(output, inputs, config):
    return ck.guarded(_execute, output, inputs, config)


def verify(output, inputs, config):
    return ck.guarded(_verify, output, inputs, config)
