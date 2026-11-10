"""Metadata/projection fixture over an ACTUAL completed constructed LA chain.

No model calls. The positive projection adapter is explicitly constructed;
the public production validator must reject it as a human guarded producer.
"""
from pathlib import Path
from types import FunctionType
import json
import shutil

from . import week5_la_pipeline_v3 as original
from . import week5_la_pipeline_v4 as old
from . import week5_la_collect_v5 as new
from . import week5_la_admission_prepare_v3 as admission
from . import week5_la_native_evidence as native
from .week5_la_pipeline_v4_fixture import seal
from .timing_census import read, filehash
from .timing_p6 import gzread, write_equal


def refuse(call):
    try:
        call()
    except (ValueError, KeyError, FileNotFoundError):
        return
    raise ValueError('Changed provenance or missing qualification was accepted')


def copy_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if filehash(source) != filehash(target):
            raise ValueError('Constructed copied source/oracle bytes differ')
    else:
        shutil.copyfile(source, target)


def changed_output(source, target, relative, change):
    if not target.exists():
        shutil.copytree(source / 'output', target / 'output')
        p = target / relative
        p.write_text(json.dumps(change(read(p)), sort_keys=True) + '\n', encoding='utf8')
    return target


def run(output, inputs, config, verifying=False):
    if set(inputs) != {'paired_fixture_root', 'chain_a_root', 'chain_b_root', 'chain_c_root'} or config:
        raise ValueError('Actual completed paired qualification and exact three-attempt chain required')
    requested = dict(fixture_root=inputs['paired_fixture_root'],
                     chain_roots=[inputs['chain_a_root'], inputs['chain_b_root'], inputs['chain_c_root']])
    qualification = admission.paired_qualification(requested)
    if not qualification['counted_chain_complete']:
        raise ValueError('Actual native paired chain is incomplete')
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    if (root / 'YIELD_REQUEST.json').exists():
        return dict(status='yielded', reason='before bounded metadata/projection qualification')
    prior, c = Path(inputs['paired_fixture_root']).resolve(), Path(inputs['chain_c_root']).resolve()
    items = native.chain(c, 'LA', admission.PAIR_CHAIN)
    records = [r for item in items for r in item['records']]
    actual_plan, done = items[-1]['plan'], items[-1]['terminal']
    args, options = read(prior / 'output/CHAIN_INPUTS.json'), read(prior / 'output/CHAIN_CONFIG.json')
    numerical_plan = dict(actual_plan, module=new.guarded.__name__, inputs=args, config=options)
    prepared = root / 'constructed-prepared'
    batch = prepared / 'output/batches/acts-000000.json.gz'
    copy_file(Path(args['rows']), batch)
    index = [dict(file='batches/acts-000000.json.gz', rows=1, sha256=filehash(batch))]
    write_equal(prepared / 'output/BATCHES.json', index)
    seal(prepared, 'constructed_prepared_source', {}, {})
    oracle = root / 'constructed-original-oracle'
    original_output = prior / 'output/chain-original-v3'
    for filename in ('act-000.json', 'INDEX.json', 'SUMMARY.json', 'COST.json'):
        copy_file(original_output / filename, oracle / 'output' / filename)
    seal(oracle, original.__name__, args, options)
    write_equal(root / 'ORACLE_BANK.json', {'batches/acts-000000.json.gz': str(oracle)})
    write_equal(root / 'CONSTRUCTED_CHAIN_BANK.json', {'batches/acts-000000.json.gz': str(c)})
    oracle_inputs = dict(prepared_root=str(prepared), score_bank=str(root / 'ORACLE_BANK.json'))
    operation = dict(operation='collect')
    original.collect(root / 'original-collection', oracle_inputs, operation, verifying)
    new.collect(root / 'public-legacy-collection', oracle_inputs, operation, verifying)

    def scoped_read(path):
        return numerical_plan if Path(path).resolve() == c / 'PLAN.json' else read(path)
    def constructed_projection(producer_root, plan):
        if Path(producer_root).resolve() != c or plan != numerical_plan:
            raise ValueError('Constructed adapter escaped its actual native fixture')
        return dict(constructed_projection_only=True, actual_native_chain_sha256=filehash(c / 'COMPLETE.json'),
                    checkpoints=new.checkpoint_proof(c, numerical_plan),
                    guards=new.guard_proof(c, done, records), human_bank_admission=False)
    fn = FunctionType(old.collect.__code__, dict(old.collect.__globals__, read=scoped_read, producer=constructed_projection),
                      old.collect.__name__, old.collect.__defaults__, old.collect.__closure__)
    fn(root / 'constructed-guarded-collection', dict(prepared_root=str(prepared),
       score_bank=str(root / 'CONSTRUCTED_CHAIN_BANK.json')), operation, verifying)
    for filename in ('ROWS.json.gz', 'UNSUPPORTED.json.gz', 'SUMMARY.json'):
        expected = filehash(root / 'original-collection' / filename)
        if any(filehash(root / name / filename) != expected for name in ('public-legacy-collection', 'constructed-guarded-collection')):
            raise ValueError('Original collection output changed')

    # A real constructed native chain is still not a production guarded score
    # plan; do not silently normalize it in the public acceptance path.
    refuse(lambda: new.producer(c, numerical_plan))
    refuse(lambda: native.completed(oracle, 'LA', new.guarded.__name__))
    refuse(lambda: admission.paired_qualification(dict(ready=True, owner_reviewed=True)))
    refuse(lambda: admission.paired_qualification(dict(fixture_root=str(root / 'missing-native'))))
    refuse(lambda: admission.collector_qualification(str(c), qualification))
    refuse(lambda: native.native(dict(pid=1, creation_time=1, executable='constructed')))
    refuse(lambda: new.producer(c, dict(actual_plan, module='unknown_unreviewed_producer')))
    missing_pin = dict(numerical_plan, pins={k: v for k, v in actual_plan['pins'].items()
                                           if not k.replace('\\', '/').endswith('/week5_la_scoring_guard_v1.py')})
    refuse(lambda: new.required_pins(missing_pin))

    guard_names = [n for n in done['outputs'] if 'guard_invocations' in Path(n).parts and Path(n).name.startswith('GUARD_')
                   and read(c / n).get('status') == 'returned']
    load_names = [n for n in done['outputs'] if Path(n).parent.as_posix() == 'output/load_admissions' and read(c / n).get('action') == 'admit']
    if not guard_names or not load_names:
        raise ValueError('Actual native chain lacks guard/load controls')
    changes = [
        ('wrong-identity', guard_names[0], lambda v: dict(v, identity=dict(v['identity'], creation_time=v['identity']['creation_time'] + 1))),
        ('wrong-phase', guard_names[0], lambda v: dict(v, phase='verify' if v['phase'] == 'execute' else 'execute')),
        ('wrong-limits', guard_names[0], lambda v: dict(v, limits=dict(v['limits'], start_commit_bytes=1))),
        ('underfloor-load', load_names[0], lambda v: dict(v, snapshot=dict(v['snapshot'], commit_headroom_bytes=1))),
    ]
    for name, filename, change in changes:
        target = changed_output(c, root / name, filename, change)
        edited = dict(done, outputs=dict(done['outputs'], **{filename: filehash(target / filename)}))
        scoped_records = [dict(r, root=str(target)) if Path(r['root']).resolve() == c else r for r in records]
        refuse(lambda: new.guard_proof(target, edited, scoped_records))
    no_loads = dict(done, outputs={k: v for k, v in done['outputs'].items() if k not in load_names})
    refuse(lambda: new.guard_proof(c, no_loads, records))
    changed = changed_output(c, root / 'wrong-replay', 'output/verified_acts/act-000.seal.json',
                             lambda v: dict(v, sha256='0' * 64))
    refuse(lambda: new.checkpoint_proof(changed, numerical_plan))
    changed_model = dict(numerical_plan, inputs=dict(args, masked_manifest=str(root / 'missing-model-manifest')))
    refuse(lambda: new.checkpoint_proof(c, changed_model))
    request = admission.request_review(dict(stage='paired_first_block', paired_qualification=requested))
    if not request['nonlaunchable'] or request['ready'] or request['owner_reviewed'] or request['forecast_cpu_seconds'] is not None:
        raise ValueError('Constructed qualification became model/resource admission')
    if request['target_module'] != new.guarded.__name__ or not request['remaining_prerequisites']:
        raise ValueError('New guarded route or remaining reader/resource gates disappeared')
    result = dict(fixture_only=True, actual_completed_paired_chain_required=True,
        paired_chain_complete_sha256=filehash(c / 'COMPLETE.json'), original_collection_outputs_equal=True,
        native_identity_guard_replay_refusals=True, templates_and_nested_completions_refused=True,
        admission_remains_nonlaunchable=True, constructed_projection_is_not_production_admission=True,
        no_model_or_human_source_execution=True, numeric_statistical_definition_changed=False)
    if verifying:
        if read(root / 'FIXTURE.json') != result:
            raise ValueError('Collector/admission refusal qualification differs')
        return dict(verified=True, collector_and_admission_refusals=True)
    write_equal(root / 'FIXTURE.json', result)
    return dict(status='complete', fixture_only=True)


def execute(output, inputs, config):
    return run(output, inputs, config)


def verify(output, inputs, config):
    return run(output, inputs, config, True)
