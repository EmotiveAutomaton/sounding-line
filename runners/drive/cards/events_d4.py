"""D4 prior correction directions predict held-out conditional menu choices.

DESIGN CHECK: LESSONS 3-5. Exact frozen P5 classes; only directly linked model
corrections train the primary. Chronological 60/20/20 with >=3/1/1 sessions,
strict completed-session cutoffs, five corrections over two training sessions
in EACH class. Exclusions are saved before fitting. Failed fits remain failures,
never a selected successful-only sample. Fresh verification rechecks original
choice vectors, fitted objectives, calibration selection, scores and bootstrap.
"""
import hashlib
import math
import time
from pathlib import Path
import numpy as np
from .events_p5 import read, write, filehash
from . import events_d4_sources as sources
from . import events_d4_stats as stats

CONFIG = dict(threads=2, bootstrap=2000, seed=20261017, minimum_corrections=5,
              minimum_training_sessions=2, penalties=list(stats.PENALTIES))
FORECAST = 3600


def sealed(path):
    return path.exists() and path.with_name(path.name + '.sha256').exists()


def read_sealed(path):
    if not sealed(path) or path.with_name(path.name + '.sha256').read_text(encoding='ascii').strip() != filehash(path):
        raise ValueError('D4 checkpoint hash differs')
    return np.load(path, allow_pickle=False) if path.suffix == '.npy' else read(path)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if sealed(path):
        old = read_sealed(path)
        equal = np.array_equal(old, value) if isinstance(value, np.ndarray) else old == value
        if not equal:
            raise ValueError('D4 immutable checkpoint differs')
        return
    if path.exists():
        retained = path.with_name(path.name + '.incomplete')
        if retained.exists():
            raise ValueError('D4 second incomplete checkpoint refused')
        path.rename(retained)
    if isinstance(value, np.ndarray):
        with path.open('xb') as f:
            np.save(f, value, allow_pickle=False)
    else:
        write(path, value)
    with path.with_name(path.name + '.sha256').open('x', encoding='ascii', newline='\n') as f:
        f.write(filehash(path) + '\n')


def fit_writer(data, units, vectors, config):
    result = dict(writer=data['writer'], exclusion=data['exclusion'], arms={}, models={}, cohesion={})
    if data['exclusion']:
        return result
    for origin in ('model', 'own'):
        if not all(v['eligible'] for v in data['support'][origin].values()):
            continue
        models = {}
        for split in ('content', 'housekeeping'):
            indices = data['support'][origin][split]['indices']
            own_units = units[indices]
            models[split] = [stats.fit_votes(own_units, penalty) for penalty in stats.PENALTIES]
            result['cohesion'][origin + '_' + split] = stats.cross_session_cohesion([data['corrections'][i] for i in indices], own_units)
        result['models'][origin] = models
        result['arms'][origin] = stats.score_pair(models, data['calibration'], data['test'], vectors)
        if origin == 'model':
            calibration, ca = stats.permuted_choices(data['calibration'], stats.stable_seed(config['seed'], data['writer'] + ':calibration'))
            test, te = stats.permuted_choices(data['test'], stats.stable_seed(config['seed'], data['writer'] + ':test'))
            result['arms']['model_outcome_shuffle'] = stats.score_pair(models, calibration, test, vectors)
            result['shuffle_audit'] = dict(calibration=ca, test=te)
        else:
            result['arms']['model_on_own_support'] = result['arms']['model']
    return result


def final_summary(writers, data, config):
    result = stats.summarize(writers, config)
    failures = [dict(writer=r['writer'], reason=r['fit_failure']) for r in writers if 'fit_failure' in r]
    if failures:
        result['primary'] = dict(effect=None, ci95=None, state='invalid', reason='at least one required fit failed', failures=failures)
        result['state'] = 'invalid'
    result.update(card='D4', writers=len(writers), eligible_writers=sum('model' in r['arms'] for r in writers),
        exclusions=[dict(writer=r['writer'], reason=r['exclusion']) for r in writers if r['exclusion']],
        fit_failures=failures, support={r['writer']: r['support'] for r in data},
        penalties=list(stats.PENALTIES), minimum_corrections=5, minimum_training_sessions=2,
        bootstrap_scope='Writer resampling of fixed held-out scores; fits are independently writer-specific, no shared fitted parameter to refit',
        origin_comparison='Own-text and model-text score arms reported on identical subset with both own classes supported; separate specification',
        scientific_admission=False)
    return result


def execute(output: Path, inputs: dict, config: dict) -> dict:
    if config != CONFIG:
        raise ValueError('frozen D4 configuration differs')
    if set(inputs) != sources.INPUTS:
        raise ValueError('explicit D4 input set differs')
    started = time.monotonic()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    binding = dict(paths=inputs, config=config, pins={str(Path(p)): filehash(p) for p in inputs.values()})
    if (output / 'BINDING.json').exists():
        if read(output / 'BINDING.json') != binding:
            raise ValueError('D4 resume input/config differs')
        if (output / 'SUMMARY.json').exists():
            raise ValueError('D4 completed output is never rerun')
    elif any(output.iterdir()):
        raise ValueError('D4 unbound existing output')
    else:
        write(output / 'BINDING.json', binding)
    source = sources.source(inputs)
    save(output / 'CHRONOLOGY_EXCLUSIONS.json', source['excluded'])
    roster = sorted(source['splits'])
    save(output / 'WRITER_ROSTER.json', roster)
    writers, data_rows, index = [], [], []
    elapsed = 0.
    for writer in roster:
        token = hashlib.sha256(writer.encode()).hexdigest()[:24]
        folder = output / 'writers' / token
        path = folder / 'RESULT.json'
        if sealed(path):
            saved = read_sealed(path)
            data = read_sealed(folder / 'DATA.json')
            read_sealed(folder / 'UNITS.npy')
            for original, expected in data['source_pins'].items():
                if filehash(original) != expected:
                    raise ValueError('D4 training source changed during resume')
        else:
            clock = time.monotonic()
            if sealed(folder / 'DATA.json') and sealed(folder / 'UNITS.npy'):
                data, units = read_sealed(folder / 'DATA.json'), read_sealed(folder / 'UNITS.npy')
                for original, expected in data['source_pins'].items():
                    if filehash(original) != expected:
                        raise ValueError('D4 saved training source changed')
            else:
                data, units = sources.writer_data(writer, source, config)
                save(folder / 'UNITS.npy', units)
                save(folder / 'DATA.json', data)
            # Source support and every exclusion are committed locally before fit.
            try:
                saved = fit_writer(data, units, source['vectors'], config)
            except ValueError as exc:
                saved = dict(writer=writer, exclusion=None, arms={}, models={}, cohesion={}, fit_failure=str(exc))
            saved['elapsed_seconds'] = time.monotonic() - clock
            save(path, saved)
        writers.append(saved); data_rows.append(data); elapsed += saved['elapsed_seconds']
        index.append(dict(writer=writer, folder=folder.relative_to(output).as_posix(), sha256=filehash(path)))
        if len(writers) == max(1, math.ceil(.1 * len(roster))) and not (output / 'FIRST_TENTH.json').exists():
            write(output / 'FIRST_TENTH.json', dict(writers=len(writers), total_writers=len(roster), elapsed_seconds=elapsed,
                projected_cpu_seconds=elapsed * len(roster) / len(writers), forecast_cpu_seconds=FORECAST))
        if (output / 'YIELD_REQUEST.json').exists():
            return dict(status='yielded', card='D4', writers_saved=len(writers), writers_total=len(roster))
    result = final_summary(writers, data_rows, config)
    result.update(chronology_exclusions=source['excluded'], elapsed_seconds_saved=elapsed,
        elapsed_seconds_this_invocation=time.monotonic() - started, forecast_cpu_seconds=FORECAST)
    save(output / 'WRITER_INDEX.json', index)
    write(output / 'SUMMARY.json', result)
    write(output / 'OUTPUT_HASHES.json', {p.relative_to(output).as_posix(): filehash(p) for p in output.rglob('*')
        if p.is_file() and p.name not in ('OUTPUT_HASHES.json', 'YIELD_REQUEST.json')})
    return result


def assert_close(actual, expected):
    if isinstance(actual, dict):
        if set(actual) != set(expected):
            raise ValueError('D4 replay fields differ')
        for key in actual:
            assert_close(actual[key], expected[key])
    elif isinstance(actual, list):
        if len(actual) != len(expected):
            raise ValueError('D4 replay length differs')
        for a, e in zip(actual, expected):
            assert_close(a, e)
    elif isinstance(actual, (float, np.floating)):
        if not np.isclose(actual, expected, atol=1e-12, rtol=1e-10):
            raise ValueError('D4 replay number differs')
    elif actual != expected:
        raise ValueError('D4 replay value differs')


def verify(output: Path, inputs: dict, config: dict) -> dict:
    output = Path(output)
    binding = read(output / 'BINDING.json')
    if binding['paths'] != inputs or binding['config'] != config or config != CONFIG:
        raise ValueError('D4 verification binding differs')
    for path, expected in binding['pins'].items():
        if filehash(path) != expected:
            raise ValueError('D4 input changed')
    for relative, expected in read(output / 'OUTPUT_HASHES.json').items():
        if filehash(output / relative) != expected:
            raise ValueError('D4 output changed')
    source = sources.source(inputs)
    assert_close(read_sealed(output / 'CHRONOLOGY_EXCLUSIONS.json'), source['excluded'])
    assert_close(read_sealed(output / 'WRITER_ROSTER.json'), sorted(source['splits']))
    writers, data_rows = [], []
    for entry in read_sealed(output / 'WRITER_INDEX.json'):
        folder = output / entry['folder']
        if filehash(folder / 'RESULT.json') != entry['sha256']:
            raise ValueError('D4 writer index hash differs')
        saved, data, units = read_sealed(folder / 'RESULT.json'), read_sealed(folder / 'DATA.json'), read_sealed(folder / 'UNITS.npy')
        for original, expected in data['source_pins'].items():
            if filehash(original) != expected:
                raise ValueError('D4 training source changed')
        partition = sources.recipient_split(data['writer'], source['splits'])
        for phase in ('own_train', 'calibration', 'test'):
            assert_close(data['partition'][phase], [s['session'] for s in partition[phase]])
        if not partition['reason']:
            for phase in ('calibration', 'test'):
                rebuilt, _ = sources.choices(partition[phase], source['records'], source['vectors'])
                assert_close(rebuilt, data[phase])
        if 'fit_failure' not in saved and not data['exclusion']:
            # Refit cheap writer-local objectives from authenticated saved unit
            # vectors, avoiding another gzip/raw corpus scan; rescore SOURCE menus.
            rebuilt = fit_writer(data, units, source['vectors'], config)
            assert_close(rebuilt, {k: saved[k] for k in rebuilt})
        writers.append(saved); data_rows.append(data)
    result = final_summary(writers, data_rows, config)
    saved = read(output / 'SUMMARY.json')
    assert_close(result, {k: saved[k] for k in result})
    return dict(verified=True, primary_recomputed=result['primary'], summary_sha256=filehash(output / 'SUMMARY.json'),
                scientific_admission=False)
