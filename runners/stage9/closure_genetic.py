"""Read-only final reconstruction of genetic-edition prediction jobs.

DESIGN CHECK: B03/H04/X01/X02/X06/X07/X11/X12; LESSONS 3--5,
CONTROLS 6--7. NULL: changed source, package, local evidence, saved request,
unit, export or omitted failed call refuses reconstruction. ALTERNATIVE: the
original shared input constructor and sequence/copy readout recover every
assigned prediction, including failures. No model, writer, fit or new reserve
opening occurs. This is execution integrity, not historical-intention evidence,
population inference, complete isolation validation or scientific admission.
"""
import hashlib
from pathlib import Path

from runners.stage7.runtime import BOOTSTRAP
from . import genetic_jobs as genetic
from .common import REPO, closure, digest, file_hash, read
from .live_status import read as read_status
from .queue import inside, verify_committed, verify_disposition
from .train import BASES

MODULE = 'runners.stage9.genetic_jobs'
COPIES = {'reader/worker.py': 'runners/stage9/reader.py',
          'reader/readout.py': 'runners/readout_repair.py',
          'reader/features.py': 'runners/stage9/features.py'}


def inspect_completed(job, plan, queue_path):
    if job['module'] != MODULE:
        raise ValueError('genetic audit requires its original dispatcher')
    args = genetic.argument_parser().parse_args(job['arguments'])
    kind = args.operation
    if kind not in ('controls', 'neural'):
        raise ValueError('genetic prediction audit cannot substitute preparation or analysis')
    directory = inside(REPO / args.output)
    if (REPO / job['produces']).resolve() != directory / 'COMPLETE.json':
        raise ValueError('genetic audit output differs from its original producer')
    verify_committed(queue_path, job, plan, digest(plan))
    before = closure([directory])
    cell = digest({'manifest_sha256': digest(plan), 'job': job})
    identity, cases, _ = genetic.prediction_context(directory, inside(REPO / args.cases), args.scope, kind,
        cell=cell, source=plan['sources'], family=args.family, training=args.training, package_kind=args.package_kind)
    if read(directory / 'IDENTITY.json') != identity:
        raise ValueError('genetic original input, source or package selection differs')
    rows, original, _ = genetic.verified_predictions(directory, args.scope, kind)
    if original != identity or not rows:
        raise ValueError('genetic original prediction identity or nonempty assignment differs')
    done = read(directory / 'COMPLETE.json')
    names = ['IDENTITY.json', 'units', 'calls', 'capsules', 'PREDICTIONS.json']
    if kind == 'neural':
        names.extend(['services', 'PACKAGE.json'])
        package = read(directory / 'PACKAGE.json'); family = BASES[identity['family']]
        expected = {'model': family['model'], 'revision': family['revision'],
            **{k: identity[k] for k in ('adapter_sha256','precision','max_context','max_support','max_new_tokens')},
            'batch_size': 4, 'device': 'cuda'}
        scorer = package['scorer_sources']
        if (any(package.get(k) != v for k,v in expected.items())
                or package['generation']['requested'] != identity['generation']
                or not scorer['files'] or scorer['sha256'] != digest(scorer['files'])
                or package['scorer_sha256'] != scorer['sha256']
                or any(plan['sources']['files'].get(p) != sha for p,sha in scorer['files'].items())):
            raise ValueError('genetic saved reader package differs from original selected package')
    if done['outputs'] != closure([directory / n for n in names]):
        raise ValueError('genetic completion omits or changes original output storage')
    copies = {p: plan['sources']['files'][origin] for p,origin in COPIES.items()}
    copies.update({'reader/__init__.py': hashlib.sha256(b'').hexdigest(),
                   'bootstrap.py': hashlib.sha256(BOOTSTRAP.encode('utf-8')).hexdigest()})
    expected_loaded = {('reader' if p=='reader/__init__.py' else p[:-3].replace('/','.')):sha
                       for p,sha in copies.items() if p.startswith('reader/')}
    calls = set(); caps = set(); units = set()
    for case, row in zip(cases, rows):
        result = row['call']; cap = Path(result['capsule']).resolve()
        path = directory / 'calls' / (case['key']+'.json')
        copied = result['copied_sources']
        if (path in calls or cap in caps or cap.parent != directory/'capsules'
                or type(result.get('accepted')) is not bool
                or copied['files'] != copies or copied['sha256'] != digest(copies)
                or copied['bootstrap_owner'] != 'runners/stage7/runtime.py'
                or copied['bootstrap_owner_sha256'] != plan['sources']['files']['runners/stage7/runtime.py']
                or file_hash(REPO/'runners/stage7/runtime.py') != copied['bootstrap_owner_sha256']
                or read(directory/'capsules/closures'/(cap.name+'.json')) != copied):
            raise ValueError('genetic request substitutes a capsule, runtime or validity field')
        for name in ('prediction','receipt','access'):
            output = cap/'out'/(name+'.json')
            if output.exists() or result.get(name) is not None or result['accepted']:
                if read(output) != result.get(name):
                    raise ValueError('genetic call lacks its actual capsule output')
        accepted = (result['rc']==0 and (result.get('prediction') or {}).get('valid') is True
            and (result.get('receipt') or {}).get('loaded_sources')==expected_loaded and result.get('access') is not None)
        if result['accepted'] != accepted or result.get('inputs_and_sources_unchanged') is not True:
            raise ValueError('genetic saved validity differs from original runtime acceptance')
        path_unit = directory/'units'/(digest(case['key'])+'.json')
        saved = read(path_unit)
        if (path_unit in units or saved.get('complete') is not True
                or saved != {'identity':digest(identity),'key':case['key'],'complete':True,'row':row}):
            raise ValueError('genetic saved unit differs from original complete reconstruction')
        calls.add(path); caps.add(cap); units.add(path_unit)
    if ({p.resolve() for p in (directory/'calls').rglob('*.json')} != calls
            or {p.resolve() for p in (directory/'units').rglob('*.json')} != units
            or {p.resolve() for p in (directory/'capsules').iterdir() if p.name!='closures'} != caps
            or {p.resolve() for p in (directory/'capsules/closures').iterdir()}
                != {directory/'capsules/closures'/(p.name+'.json') for p in caps}):
        raise ValueError('genetic prediction has extra or missing saved calls, units or capsules')
    counts = {'assigned':len(cases),'invalid':sum(not r['valid'] for r in rows),'scored':False,
        'scientific_admission':False,'execution_complete':True,'scope':args.scope,'cell_identity':cell}
    if any(type(done.get(k)) is not type(v) or done[k]!=v for k,v in counts.items()):
        raise ValueError('genetic completion loses assigned units or promotes execution')
    if closure([directory]) != before:
        raise ValueError('genetic final reconstruction changed original evidence')
    return {'status':'RECONSTRUCTED','operation':kind,'units':len(rows),'calls':len(calls),
        'invalid_calls_retained':counts['invalid'],'predictions_sha256':digest(rows),
        'complete_sha256':file_hash(directory/'COMPLETE.json'),'new_reader_calls':0,
        'new_reserve_openings':0,'scientific_admission':False}


def queue_audits(plan, queue_path, prior):
    state = read_status(queue_path/'STATUS.json'); result = {}
    for key, job in prior.items():
        if job['module'] != MODULE or job['arguments'][:1] not in (['controls'],['neural']):
            continue
        own = state['jobs'][key]
        if own['status'] == 'COMPLETE':
            result[key] = inspect_completed(job,plan,queue_path)
        elif own['status'] in ('FAILED','NOT_RUN'):
            verify_disposition(queue_path,job,own)
            result[key] = {k:own[k] for k in ('status','reason','disposition_sha256')}
        else:
            raise ValueError('genetic final reconstruction requires terminal predictions')
    return {'jobs':result,'scientific_admission':False,
        'scope':'Original genetic-edition prediction inputs, packages, saved calls and units; no historical-intention or population claim'}
