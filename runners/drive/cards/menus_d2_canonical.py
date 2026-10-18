"""Canonical successor of the original D2 primary, with whole-pipeline controls.

DESIGN CHECK 2026-10-18: lessons read: LESSONS 3-5 and CONTROLS.
NULL: identical balanced choices yield zero gain. ALTERNATIVE: larger option
differences under a planted choice rule yield positive gain; the reversed rule
is negative. Original exhaustive bands and failure directions remain. Correct targets only;
population, chronology, features, optimization and conditional bootstrap stay
frozen. Repeated outcomes permute within writer and offer count, before fitting
and calibration, with one global mapping per draw. No person-identification
claim or hierarchical extension. A failed fit/source is invalid, never a null.
The bias warning is abs(control mean) > .25 * sample SD; it is not a p-value.
Outcome-independent preprocessing is cached, with exact original-fit parity.
"""
from collections import defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
from threadpoolctl import threadpool_limits

from . import menus_d2 as old
from . import menus_d2_recovery as stable
from . import menus_d2_diagnostic_source as source
from .menus_io import read, write, sha256, assert_equal, canonical, input_hashes

CONFIG = dict(mode='pilot', fit=old.CONFIG, permutations=200,
              permutation_seed=20261018, threads=1)
EXTRA = {'pilot_plan', 'pilot_complete', 'pilot_summary'}


def prepare(split, cases, config):
    groups = [[cases[r['key']] for s in split[k] for r in s['rows'] if r['key'] in cases]
              for k in ('train', 'calibration', 'test')]
    if any(not g for g in groups):
        raise ValueError('Empty canonical D2 partition')
    train, calibration, test = groups
    pca = old.PCA(n_components=min(config['pca_components'],
        len(np.concatenate([c['embeddings'] for c in train])), train[0]['embeddings'].shape[1]),
        svd_solver='full')
    pca.fit(np.concatenate([c['embeddings'] for c in train]))
    tr, scale = old.transformed(train, pca)
    ca, _ = old.transformed(calibration, pca, scale)
    te, _ = old.transformed(test, pca, scale)
    edges = np.quantile([c['dissimilarity'] for c in train], [.2, .4, .6, .8])
    metadata = dict(edges=edges.tolist(), train_count=len(train), calibration_count=len(calibration),
        test_count=len(test), cutoff=split['cutoff'], test_cutoff=split['test_cutoff'],
        preprocessing=dict(scale=scale.tolist(), pca_mean=pca.mean_.tolist(),
                           pca_components=pca.components_.tolist()))
    return groups, (tr, ca, te), metadata


def fit_arm(prepared, targets, config):
    groups, matrices, metadata = prepared
    train, calibration, test = matrices
    ty, cy, ey = [[targets[c['key']] for c in group] for group in groups]
    fits = []
    for penalty in config['penalties']:
        beta, certificate = old.fit(old.pack(train, ty), penalty)
        loss = float(-old.log_scores(beta, calibration, cy).mean())
        fits.append((loss, penalty, beta, certificate))
    loss, penalty, beta, certificate = min(fits, key=lambda v: (v[0], v[1]))
    scores = old.log_scores(beta, test, ey)
    return dict(beta=beta.tolist(), penalty=penalty,
        calibration_losses=[dict(penalty=p, loss=l) for l, p, _, _ in fits], certificate=certificate,
        predictions=[dict(key=c['key'], session=c['session'], writer=c['writer'], truth=y,
            size=len(c['x']), quintile=int(np.searchsorted(metadata['edges'], c['dissimilarity'], side='right')),
            log_probability=float(lp), gain=float(lp+math.log(len(c['x']))))
            for c, y, lp in zip(groups[2], ey, scores)])


def targets(cases, arm, config):
    keys = sorted(cases)
    if arm in ('primary', 'uniform_control'):
        return dict(zip(keys, old.labels([cases[k] for k in keys], arm, config['fit']['seed'])))
    if not isinstance(arm, int) or isinstance(arm, bool) or not 0 <= arm < config['permutations']:
        raise ValueError('Unknown outcome permutation')
    groups = defaultdict(list)
    for key in keys:
        case = cases[key]; groups[(case['writer'], len(case['x']))].append(key)
    rng = np.random.default_rng(config['permutation_seed']+arm)
    result = {}
    for group in sorted(groups):
        members = groups[group]
        result.update(zip(members, map(int, rng.permutation([cases[k]['truth'] for k in members]))))
    return result


def load(inputs, config):
    if config.get('mode') not in ('pilot', 'full', 'validation') or dict(config, mode='pilot') != CONFIG:
        raise ValueError('Frozen D2 canonical configuration differs')
    if set(inputs) != source.INPUTS | (EXTRA if config['mode']=='full' else set()):
        raise ValueError('Canonical input roster differs')
    if config['mode']=='validation' and not read(inputs['original_complete']).get('synthetic_metadata_fixture_only'):
        raise ValueError('Validation mode is constructed-data only')
    data = source.load({k: inputs[k] for k in source.INPUTS})
    if not data['splits']:
        raise ValueError('No eligible canonical recipients')
    return data


def binding(data, config):
    return dict(inputs=data['identity'], config={k: v for k, v in config.items() if k!='mode'},
        code={str(Path(m.__file__).resolve()): sha256(m.__file__) for m in (old, stable, source)},
        runner_sha256=sha256(__file__))


def immutable(path, value):
    if path.exists(): assert_equal(read(path), value)
    else: write(path, value)


def name(writer):
    return hashlib.sha256(writer.encode()).hexdigest()[:24]


def read_unit(path, bind):
    seal = read(path.with_suffix('.seal.json'))
    assert_equal(seal, dict(binding_sha256=hashlib.sha256(canonical(bind).encode()).hexdigest(), sha256=sha256(path)))
    with gzip.open(path, 'rt', encoding='utf8') as stream: return json.load(stream)


def unit(path, bind, compute, verify):
    if path.exists():
        saved = read_unit(path, bind)
        if verify: assert_equal(saved, compute())
        return saved
    if verify: raise ValueError('Missing saved fit')
    value = compute(); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', mtime=0, filename='') as stream:
            stream.write((canonical(value)+'\n').encode())
    write(path.with_suffix('.seal.json'), dict(binding_sha256=hashlib.sha256(canonical(bind).encode()).hexdigest(), sha256=sha256(path)))
    return value


def work(data, writer):
    return sum(len(data['cases'][r['key']]['x']) for s in data['splits'][writer]['train']
               for r in s['rows'] if r['key'] in data['cases'])


def pilot_report(data, timing):
    writer = sorted(data['splits'])[0]
    multiple = max(len(data['splits']), sum(work(data, w) for w in data['splits'])/work(data, writer))
    return dict(card='D2-canonical-pilot', execution_only=True, primary=None,
        scientific_admission=False, eligible_recipients=len(data['splits']),
        selected_recipient=writer, timing=timing, extrapolation_multiplier=multiple,
        full_projected_seconds=2*(timing['source_seconds']+timing['fit_seconds']*multiple),
        full_projected_bytes=int(timing['recipient_bytes']*multiple+timing['source_bytes']),
        forecast='Twice measured source plus first-recipient complete202-arm cost times larger of recipient-count/training-option ratios; includes fresh refit.',
        source_census=data['census'], original_primary_not_completed=True)


def pilot_reuse(output, inputs, data, bind, verify):
    plan, complete, report = (read(inputs[k]) for k in ('pilot_plan', 'pilot_complete', 'pilot_summary'))
    root = Path(inputs['pilot_complete']).parent.resolve(); oldout = root/'output'
    if (Path(inputs['pilot_plan']).resolve()!=root/'PLAN.json' or Path(inputs['pilot_summary']).resolve()!=oldout/'SUMMARY.json'
        or complete.get('status')!='COMPLETE' or not complete.get('fresh_process_verified')
        or plan['module']!='runners.drive.cards.menus_d2_canonical' or plan['config']!=CONFIG):
        raise ValueError('Complete canonical pilot required')
    for key in ('pilot_plan', 'pilot_summary'):
        path=Path(inputs[key]); relative=path.resolve().relative_to(root).as_posix()
        if complete['outputs'].get(relative)!=sha256(path): raise ValueError('Pilot artifact changed')
    assert_equal(read(oldout/'BINDING.json'), bind)
    assert_equal(report, pilot_report(data, read(oldout/'TIMING.json')))
    for relative, expected in sorted(complete['outputs'].items()):
        if not relative.startswith('output/') or relative in ('output/SUMMARY.json', 'output/TIMING.json'): continue
        path = root/relative; dest = output/path.relative_to(oldout)
        if sha256(path)!=expected: raise ValueError('Pilot retained checkpoint changed')
        if dest.exists():
            if sha256(dest)!=expected: raise ValueError('Reused pilot bytes changed')
        elif verify: raise ValueError('Missing reused pilot checkpoint')
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as stream: stream.write(path.read_bytes())
    receipt=dict(byte_exact=True, inputs=input_hashes({k:inputs[k] for k in EXTRA}))
    if verify: assert_equal(read(output/'PILOT_REUSE.json'),receipt)
    else: immutable(output/'PILOT_REUSE.json',receipt)


def compute(output, inputs, config, verify=False):
    output = Path(output); output.mkdir(parents=True, exist_ok=True); started=time.perf_counter()
    data=load(inputs, config); source_seconds=time.perf_counter()-started; bind=binding(data, config)
    if config['mode']=='full': pilot_reuse(output, inputs, data, bind, verify)
    for filename, value in [('BINDING.json', bind), ('SOURCE_AUDIT.json', dict(rows=data['rows'], census=data['census'], scope=data['scope'])),
                            ('PARTITIONS.json', data['partitions'])]:
        if verify: assert_equal(read(output/filename), value)
        else: immutable(output/filename, value)
    writers=sorted(data['splits']); requested=writers[:1] if config['mode']=='pilot' else writers
    arms=['primary', 'uniform_control']+list(range(config['permutations']))
    mappings={arm:targets(data['cases'], arm, config) for arm in arms}
    predictions={arm:[] for arm in arms}; fit_started=time.perf_counter()
    for number,writer in enumerate(requested,1):
        prepared=prepare(data['splits'][writer], data['cases'], config['fit'])
        folder=output/'recipients'/name(writer)
        if verify: assert_equal(read(folder/'PREPROCESSING.json'), prepared[2])
        else: immutable(folder/'PREPROCESSING.json', prepared[2])
        for arm in arms:
            if not verify and (output/'YIELD_REQUEST.json').exists():
                return dict(status='yielded', writer=writer, next_arm=arm)
            filename=f'p{arm:03d}' if isinstance(arm, int) else arm
            value=unit(folder/(filename+'.json.gz'), bind, lambda:fit_arm(prepared, mappings[arm], config['fit']), verify)
            predictions[arm].extend(value['predictions'])
        marker=output/'FIRST_TENTH.json'
        if not verify and config['mode']=='full' and number>=max(1,math.ceil(.1*len(writers))) and not marker.exists():
            ratio=max(len(writers)/number,sum(work(data,w) for w in writers)/sum(work(data,w) for w in writers[:number]))
            # The retained pilot's fit timing is added because its receipts skip
            # computation during main execution; do not undercount that work.
            retained=read(inputs['pilot_summary'])['timing']['fit_seconds']
            write(marker,dict(projected_seconds=2*(source_seconds+(time.perf_counter()-fit_started+retained)*ratio),
                recipients=number,total_recipients=len(writers),includes_fresh_refit=True))
    if config['mode']=='pilot':
        timingpath=output/'TIMING.json'
        if timingpath.exists(): timing=read(timingpath)
        else:
            if verify: raise ValueError('Missing pilot telemetry')
            timing=dict(source_seconds=source_seconds, fit_seconds=time.perf_counter()-fit_started,
                recipient_bytes=sum(p.stat().st_size for p in (output/'recipients').rglob('*') if p.is_file()),
                source_bytes=sum((output/n).stat().st_size for n in ('BINDING.json','SOURCE_AUDIT.json','PARTITIONS.json')))
            write(timingpath, timing)
        if any(not math.isfinite(v) or v<0 for v in timing.values()): raise ValueError('Invalid pilot telemetry')
        result=pilot_report(data,timing)
    else:
        summaries={arm:stable.summarize(predictions[arm], config['fit']) for arm in arms}
        values=[summaries[i]['primary']['effect'] for i in range(config['permutations'])]
        mean, sd=float(np.mean(values)), float(np.std(values,ddof=1))
        controls=dict(total=len(values),finite=len(values),invalid=0,mean=mean,sd=sd,bias_flag=abs(mean)>.25*sd,
            construction='Global selected-position permutations within writer and offer count; refit and recalibrate every recipient. Singleton/constant groups retained.',
            effects=values)
        result=dict(card='D2-canonical',primary=summaries['primary'],uniform_control=summaries['uniform_control'],
            repeated_outcome_control=controls, source_census=data['census'], source_scope=data['scope'], exclusions=data['exclusions'],
            original_preserved=True,extension_computed=False,extension_closed=True,scientific_admission=False,descriptive=True,
            fake_writer_control='Not applicable to a pooled population choice contrast with no writer feature or identification claim; writers remain bootstrap clusters.',
            input_hashes=data['identity'],config={k:v for k,v in config.items() if k!='mode'})
    if verify: assert_equal(read(output/'SUMMARY.json'), result)
    else: immutable(output/'SUMMARY.json', result)
    return result


def execute(output, inputs, config):
    with threadpool_limits(limits=1): return compute(output, inputs, config)


def verify(output, inputs, config):
    with threadpool_limits(limits=1): result=compute(output, inputs, config, verify=True)
    return dict(verified=True,canonical_source_replayed=True,all_fits_recomputed=True,
                complete_permutations=200,execution_only=config['mode']=='pilot')
