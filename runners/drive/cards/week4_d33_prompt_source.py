"""Complete source preparation for the registered D33 prompt-exclusion probe.

DESIGN CHECK: LESSONS 3-5 read November 5. NULL and ALTERNATIVE preserve the
same metadata-selected support and calibration. All original keys are retained
or explicitly excluded. Prompt/future leakage, changed sources or incomplete
replay refuse. No human fit, smaller convenient intersection or causal claim.
"""
from copy import deepcopy
from pathlib import Path
from types import MethodType, SimpleNamespace
import time

from . import timing_d33_calibrated as parent
from . import timing_d33_supported_source as sources
from . import timing_d33_supported_counts as counts
from . import timing_d33_supported_prefix as prefix
from .timing_census import read, filehash
from .timing_p6 import write_equal, gzip_equal, gzread, progress
from .batch_runtime import check_files


def configuration(mode):
    if mode not in ('constructed', 'full'):
        raise ValueError('Unknown source mode')
    return dict(card='D33.pair-calibration-supported.m-source', schema=1,
                mode=mode, variant='pair2', seed=20261018)


def authenticate(inputs):
    if set(inputs) != {'parent_completion', 'parent_landing'}:
        raise ValueError('Exact parent inputs required')
    root = Path(inputs['parent_completion']).resolve().parent
    done, plan, landing = read(root/'COMPLETE.json'), read(root/'PLAN.json'), read(inputs['parent_landing'])
    if (done['status'] != 'COMPLETE' or not done['fresh_process_verified']
            or plan['module'] != parent.__name__ or plan['config'] != parent.CONFIG
            or not landing['full_write_through']
            or landing['id'] != 'S15-D33-CALIBRATION-SUPPORTED-20261029'
            or landing['completion_sha256'] != filehash(root/'COMPLETE.json')
            or landing['plan_sha256'] != filehash(root/'PLAN.json')
            or not read(root/'VERIFIED.json')['full_matching_calibration_and_statistical_replay']):
        raise ValueError('Unverified parent')
    check_files(plan['pins'])
    for name, digest in done['outputs'].items():
        if filehash(root/name) != digest:
            raise ValueError('Parent output changed: '+name)
    return root, plan


def fixture():
    """Three writers: two matched, one too large; same-prompt and future traps."""
    lookup, by_writer, partitions, rows = {}, {}, {}, []
    for writer in ('a', 'b', 'c'):
        sessions = []
        for j in range(6):
            sid = writer+str(j)
            tokens = ['target', 'other'] * (20 if writer == 'c' else 1)
            record = dict(session=sid, writer=writer, prompt='P' if j in (1, 3, 4) else 'Q',
                          timestamp=j*10., end_at=j*10.+1,
                          training_sequences=[tokens],
                          words=[dict(index=i, token=token, context=[], is_word=True,
                                      population_probability=.05, ordinal=1)
                                 for i, token in enumerate(['target', 'other'])])
            lookup[sid] = record
            sessions.append(record)
        by_writer[writer] = sessions
        partitions[writer] = dict(calibration_sessions=[writer+'3'],
                                  evaluation_sessions=[writer+'4'], original_alpha=.5)
        rows.extend(dict(writer=writer, session=writer+'4', index=i, log_pause=float(i),
                         personal_surprise=.2, donor_surprise=.3, population_surprisal=3.,
                         length=6., log_frequency=1., sentence_start=int(i == 0),
                         after_punctuation=0) for i in range(2))
    unit = {v: {} for v in ('pair', 'pair2')}
    for writer, parts in partitions.items():
        for split in ('calibration', 'evaluation'):
            for sid in parts[split+'_sessions']:
                target = dict(writer=writer, session=sid, split=split)
                for variant in unit:
                    unit[variant][sid] = counts.unit(target, variant, by_writer, lookup)
    source = SimpleNamespace(saved=dict(rows=rows), roster=dict(writers=partitions),
                             units=unit, lookup=lookup)
    return source


def fixture_covariate(source, sid):
    return dict(session=sid, writer=source.lookup[sid]['writer'], source_hashes={},
                words={str(w['index']): dict(on_screen=0, session_surprisal=3.,
                                            in_prompt=False, in_visible_text=False,
                                            in_previous_shown_suggestion=False)
                       for w in source.lookup[sid]['words']})


def roster_for(source):
    original = sources.population_roster(source.saved, source.roster,
                                         source.units['pair2'], source.lookup, 'pair2')
    return original, parent.select_population(original, source.saved)


def prepare(output, inputs, config, verifying=False):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    def store(name, value, compressed=False):
        path = output/name
        if verifying:
            if (gzread(path) if compressed else read(path)) != value:
                raise ValueError('Complete fresh source replay differs: '+name)
        elif compressed:
            gzip_equal(path, value)
        else:
            write_equal(path, value)
    if config != configuration(config.get('mode')):
        raise ValueError('Frozen source configuration required')
    start = time.process_time()
    binding = dict(config=config, inputs={k:filehash(v) for k,v in sorted(inputs.items())})
    store('INPUTS.json', binding)
    if config['mode'] == 'constructed':
        if inputs:
            raise ValueError('No external constructed inputs')
        source = fixture()
        pair = sources.population_roster(source.saved, source.roster,
                                         source.units['pair'], source.lookup, 'pair')
        previous = parent.select_population(pair, source.saved)
        cached = {'a4': fixture_covariate(source, 'a4')}
        def covariate(sid):
            return deepcopy(cached[sid]) if sid in cached else fixture_covariate(source, sid)
    else:
        root, plan = authenticate(inputs)
        source, pair, prior = parent.load_source(plan['inputs'], parent.CONFIG)
        previous = parent.select_population(pair, source.saved)
        if previous != read(root/'output/SUPPORTED_ROSTER.json'):
            raise ValueError('Parent supported population no longer reconstructs')
        source.output, source.verifying, source.audits = output, verifying, {}
        source.raw.session = MethodType(prefix.raw_session, source.raw)
        cached = {Path(name).name.removesuffix('.json.gz'): prior/name
                  for name in read(prior/'COMPLETE.json')['outputs']
                  if name.startswith('output/sessions/') and name.endswith('.json.gz')}
        def covariate(sid):
            if sid in cached:
                return gzread(cached[sid])
            return prefix.Sources.covariates(source, sid)
    original, roster = roster_for(source)
    store('SUPPORTED_ROSTER.json', roster)
    store('MATCH_PROOFS.json', source.units['pair2'])
    tuning = sources.calibrate(original, source.units['pair2'], source.lookup)
    store('CALIBRATION.json', tuning)
    ids = sorted({sid for sid, _ in roster['retained_keys']})
    covariates = {}
    for sid in ids:
        covariates[sid] = covariate(sid)
        if covariates[sid]['session'] != sid or covariates[sid]['writer'] != source.lookup[sid]['writer']:
            raise ValueError('Covariate source identity differs')
        store('sessions/'+sid+'.json.gz', covariates[sid], True)
        progress(output/'PROGRESS.json', dict(phase='verify-source' if verifying else 'execute-source',
                                              completed=len(covariates), total=len(ids)))
    rows = sources.scientific_rows(source.saved, roster, source.units['pair2'],
                                    source.lookup, tuning, covariates)
    store('DESIGN.json.gz', rows, True)
    kept = set(map(tuple, roster['retained_keys']))
    previous_keys = set(map(tuple, previous['retained_keys']))
    summary = dict(card=config['card'], constructed=config['mode'] == 'constructed',
                   coverage=roster['coverage'], prepared_rows=len(rows),
                   parent_overlap_words=len(kept & previous_keys),
                   added_supported_words=len(kept-previous_keys),
                   removed_parent_words=len(previous_keys-kept),
                   reused_covariate_sessions=sum(s in cached for s in ids),
                   rebuilt_covariate_sessions=sum(s not in cached for s in ids),
                   empty_own_history_evaluation_sessions=sum(
                       source.units['pair2'][s]['proof']['own_tokens'] == 0 for s in ids),
                   statistical_fit_computed=False, scientific_admission=False)
    store('SUMMARY.json', summary)
    write_equal(output/('VERIFY_TIMING.json' if verifying else 'EXECUTE_TIMING.json'),
                dict(cpu_seconds=time.process_time()-start))
    return dict(verified=True, complete_source_replay=True, scientific_admission=False,
                prepared_rows=len(rows))


def execute(output, inputs, config):
    return prepare(output, inputs, config)


def verify(output, inputs, config):
    return prepare(output, inputs, config, True)
