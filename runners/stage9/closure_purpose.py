"""Read-only B03 reconstruction of the purpose/context reader dispatcher.

DESIGN CHECK: B03/M02/M03/S02/T02/X01/X02/X05/X06/X11/X12;
LESSONS 3--5, CONTROLS 6--7. NULL: substituted source/fit, hidden input,
task, saved call, unit, export or lost failure refuses reconstruction.
ALTERNATIVE: the original shared constructor and forecast dispatcher recover
every assigned unit from actual saved capsules, including invalid components.
An explicit context intercepts requests before capsule creation; no inference,
writer, refit or new reserve opening occurs. Unknown historical protocols
refuse. Capsule isolation and complete scientific acceptance remain separate.
"""
import hashlib
from pathlib import Path

from runners.stage7.runtime import BOOTSTRAP
from . import purpose_jobs
from .artifact_comparisons import audit_execution
from .common import REPO, closure, digest, file_hash, read
from .live_status import read as read_status
from .queue import inside, verify_committed, verify_disposition
from .saved_replay import replaying

MODULE = 'runners.stage9.purpose_jobs'

# Reviewed original runtime archives: the task constructor/defaults are unchanged;
# these exact versions copied successively introduced reader modules. Never infer
# an old protocol by dropping whichever files happen to be missing from a record.
ADDITIONS = ('proposal_reader', 'context_reader', 'goal_reader', 'cue_reader',
             'ambiguity_reader', 'constraint_reader', 'familiarity_reader',
             'selection_reader', 'information_selection')
HISTORICAL_COMPARISON = {
    '8cebf2f3735fe78e8454303b1552ae3a6b4507b9579f92af74df5dc83a8aa7aa': 0,
    'b259cd6f4b7c5a84d2736cf7686c51b0db2740bbd26fb8422579152fe877675c': 1,
    '20aebd03def23837aa9263506ca25721486fa3f2d58e4a55bb39d2d07220d6f7': 2,
    '8b5733b31ed238596733b0c9588045369b0d92a8777c5ce47cb9bf9044be0c52': 3,
    '5310e21e89e457b9b4359b55586a6172114135d85789866acc29a85de96093e2': 4,
    'ae0a82b4c087367591252dfe4209efaf18f95ba91cef207c5af1b19af1c8c3c3': 5,
    'ddea74a146bc364b4b586146e443df352ec62b295640006669aa582bb10c972f': 6,
    '7e1c133c8cd91a21a90ddc1066bb4fbc0f79d532e5fb3e14e0df4963c161942d': 7,
    '3c41324449609c89e55788aaaf0463e21d6f6b22d4c38c62d3e90e56c8bbac02': 9,
    'ce1d8513e2b292bb3192838859ee9edd378a4139589e84a2e19df884b651dd49': 9,
}
SELECTION_SCOPE_SOURCE = 'dd43226720ecfe997431138fd5c144291adeb083504085a2978e7db28b15fe66'
CURRENT_SELECTION_SCOPE = 'charged common previews; fixed budgets and costed future-gain stopping; no scientific promotion'
ORIGINAL_SELECTION_SCOPE = 'seven charged previews; fixed budgets and costed future-gain stopping; no scientific promotion'
PURPOSE_IDENTITY_SOURCE = '6c3d430c019e059efbfa566a133e6307777724e5abfdfa02e1b1cbd504e5312c'


def original_identity(identity, source, consumer):
    # The original purpose-only producer used this field name before dispatch
    # generalization. Its inputs and forecast function are AST-identical. Keep
    # its exact identity without changing the budget or any other field.
    if source['files'].get('runners/stage9/purpose_jobs.py') == PURPOSE_IDENTITY_SOURCE:
        budget = identity.get('budget_per_evaluation_call')
        if (consumer != 'purpose' or type(budget) is not int or budget != 800000
                or 'budget_per_purpose_call' in identity):
            raise ValueError('unreviewed original purpose identity protocol')
        identity = dict(identity)
        identity['budget_per_purpose_call'] = identity.pop('budget_per_evaluation_call')
    return identity


def original_annotation(row, source, consumer):
    # The original S02 source predates the shared T02 executor. Only its exact
    # outer scope sentence differs; all inputs, traces, costs and predictions
    # must still reconstruct unchanged. No numeric or validity field is adapted.
    if (consumer == 'selection' and source['files'].get('runners/stage9/selection_jobs.py') == SELECTION_SCOPE_SOURCE):
        if row.get('scope') != CURRENT_SELECTION_SCOPE:
            raise ValueError('unreviewed selection scope annotation')
        return {**row, 'scope': ORIGINAL_SELECTION_SCOPE}
    return row


def source_map(sources, original, runtime):
    if runtime == 'comparison_runtime':
        count = HISTORICAL_COMPARISON.get(original['files'].get('runners/stage9/comparison_runtime.py'))
        if count is not None:
            excluded = {'reader/' + n + '.py' for n in ADDITIONS[count:]}
            sources = {p: origin for p, origin in sources.items() if p not in excluded}
    if not set(sources.values()) <= set(original['files']):
        raise ValueError('unreviewed historical purpose runtime source protocol')
    return {p: original['files'][origin] for p, origin in sources.items()}


class SavedRequests:
    """Read an existing checkpoint through its original runtime constructor."""
    def __init__(self, directory, source, *, storage='calls'):
        if storage not in ('calls', 'capsules'):
            raise ValueError('saved replay requires a declared capsule storage location')
        self.directory = directory
        self.storage = storage
        self.source = source
        self.calls = {}
        self.capsules = {}
        self.roots = set()
        self.pending = None
        self.request_count = 0

    def checkpoint(self, path, inputs, invoke, *, resume_only=False):
        path = Path(path).resolve()
        if (resume_only is not True or self.pending is not None or invoke is None
                or not path.is_relative_to(self.directory / 'calls')):
            raise ValueError('purpose replay requires an original read-only checkpoint')
        saved = read(path)
        if set(saved) != {'input_sha256', 'result'} or saved['input_sha256'] != digest(inputs):
            raise ValueError('purpose checkpoint differs from reconstructed reader input')
        self.pending = (path, saved['result'])
        before = self.request_count
        try:
            result = invoke()
        finally:
            self.pending = None
        if self.request_count != before + 1 or result != saved['result']:
            raise ValueError('purpose checkpoint did not reconstruct exactly one actual request')
        self.calls[path] = result
        return result

    def request(self, evidence, task, root, sources, *, runtime):
        if self.pending is None:
            raise ValueError('purpose request lacks its original saved checkpoint')
        path, result = self.pending
        root = Path(root).resolve()
        cap = Path(result['capsule']).resolve()
        if (not root.is_relative_to(self.directory / self.storage) or cap.parent != root
                or cap in self.capsules and self.capsules[cap] != path
                or type(result.get('accepted')) is not bool):
            raise ValueError('purpose request substitutes a capsule or validity field')
        expected = source_map(sources, self.source, runtime)
        expected.update({'reader/__init__.py': hashlib.sha256(b'').hexdigest(),
                         'bootstrap.py': hashlib.sha256(BOOTSTRAP.encode('utf-8')).hexdigest()})
        copied = result['copied_sources']
        if (copied['files'] != expected or copied['sha256'] != digest(expected)
                or copied['bootstrap_owner_sha256'] != self.source['files']['runners/stage7/runtime.py']
                or file_hash(REPO / 'runners/stage7/runtime.py') != copied['bootstrap_owner_sha256']
                or read(root / 'closures' / (cap.name + '.json')) != copied
                or read(cap / 'evidence.json') != evidence or read(cap / 'task.json') != task):
            raise ValueError('purpose runtime, copied source, task or evidence differs')
        for name in ('prediction', 'receipt', 'access'):
            p = cap / 'out' / (name + '.json')
            if p.exists() or result.get(name) is not None or result['accepted']:
                if read(p) != result.get(name):
                    raise ValueError('purpose result lacks its actual capsule output')
        audit_execution(result)
        loaded = {('reader' if p == 'reader/__init__.py' else p[:-3].replace('/', '.')): sha
                  for p, sha in expected.items() if p.startswith('reader/')}
        valid = ((result.get('prediction') or {}).get('valid') is True
                 and (result.get('receipt') or {}).get('loaded_sources') == loaded)
        accepted = result['rc'] == 0 and valid and result.get('access') is not None
        if result['accepted'] != accepted or result.get('inputs_and_sources_unchanged') is not True:
            raise ValueError('purpose completion changes the original runtime validity decision')
        self.request_count += 1
        self.capsules[cap] = path
        self.roots.add(root)
        return result

    def verify_inventory(self):
        call_files = {p.resolve() for p in (self.directory / 'calls').rglob('*.json')
                      if not any(p.resolve().is_relative_to(root) for root in self.roots)}
        if call_files != set(self.calls):
            raise ValueError('purpose replay has extra or missing saved calls')
        for root in self.roots:
            expected = {p for p in self.capsules if p.parent == root}
            if ({p.resolve() for p in root.iterdir() if p.name != 'closures'} != expected
                    or {p.resolve() for p in (root / 'closures').iterdir()}
                    != {root / 'closures' / (p.name + '.json') for p in expected}):
                raise ValueError('purpose replay has extra or missing capsule storage')


def inspect_completed(job, plan, queue_path):
    if job['module'] != MODULE:
        raise ValueError('purpose audit requires the original prediction dispatcher')
    args = vars(purpose_jobs.argument_parser().parse_args(job['arguments']))
    directory = inside(REPO / args.pop('root'))
    args['cases_path'] = inside(REPO / args.pop('cases'))
    args['models_path'] = inside(REPO / args.pop('models'))
    if (REPO / job['produces']).resolve() != directory / 'COMPLETE.json':
        raise ValueError('purpose audit output differs from its actual producer')
    verify_committed(queue_path, job, plan, digest(plan))
    before = closure([directory])
    cell = digest({'manifest_sha256': digest(plan), 'job': job})
    identity, cases, package, purposes, forecast = purpose_jobs.context(
        directory, cell=cell, source=plan['sources'], **args)
    identity = original_identity(identity, plan['sources'], args['consumer'])
    if read(directory / 'IDENTITY.json') != identity:
        raise ValueError('purpose input, fitting package or original execution identity differs')
    done = read(directory / 'COMPLETE.json')
    outputs = closure([directory / n for n in ('PREDICTIONS.json', 'units', 'calls')])
    if done['identity_sha256'] != digest(identity) or done['outputs'] != outputs:
        raise ValueError('purpose completion identity or output closure changed')
    requests = SavedRequests(directory, plan['sources'])
    rows = []; units = set()
    with replaying(requests):
        for case in cases:
            key = {'unit': case['unit']}
            row = forecast(case, package, purposes, directory / 'calls' / digest(key)[:12], resume_only=True)
            row = original_annotation(row, plan['sources'], args['consumer'])
            path = directory / 'units' / (digest(key) + '.json')
            saved = read(path)
            if (path in units or saved.get('complete') is not True or
                    saved != {'identity': digest(identity), 'key': key, 'complete': True, 'row': row}):
                raise ValueError('purpose unit differs from complete saved-request reconstruction')
            units.add(path); rows.append(row)
    requests.verify_inventory()
    if (not rows or not requests.calls or read(directory / 'PREDICTIONS.json') != rows
            or {p.resolve() for p in (directory / 'units').rglob('*.json')} != units):
        raise ValueError('purpose export has missing, extra or substituted units')
    expected = {'cell_identity': cell, 'source': identity['source'], 'role': args['role'],
                'execution_complete': True, 'assigned_units': len(cases), 'completed_units': len(rows),
                'gpu_seconds': 0, 'cpu_scope': 'parent excludes restricted readers', 'scientific_promotion': False}
    if any(type(done.get(k)) is not type(v) or done[k] != v for k, v in expected.items()):
        raise ValueError('purpose completion loses assigned work or promotes execution')
    if closure([directory]) != before:
        raise ValueError('read-only purpose audit changed original evidence')
    return {'status': 'RECONSTRUCTED', 'consumer': args['consumer'], 'units': len(rows),
            'calls': len(requests.calls), 'invalid_calls_retained': sum(not r['accepted'] for r in requests.calls.values()),
            'complete_sha256': file_hash(directory / 'COMPLETE.json'), 'predictions_sha256': digest(rows),
            'new_reader_calls': 0, 'new_reserve_openings': 0, 'scientific_admission': False}


def queue_audits(plan, queue_path, prior):
    state = read_status(queue_path / 'STATUS.json'); result = {}
    for key, job in prior.items():
        if job['module'] != MODULE:
            continue
        current = state['jobs'][key]
        if current['status'] == 'COMPLETE':
            result[key] = inspect_completed(job, plan, queue_path)
        elif current['status'] in ('FAILED', 'NOT_RUN'):
            verify_disposition(queue_path, job, current)
            result[key] = {k: current[k] for k in ('status', 'reason', 'disposition_sha256')}
        else:
            raise ValueError('unfinished purpose execution cannot enter final reconstruction')
    return {'jobs': result, 'scope': 'original purpose/context dispatcher and saved requests; no inference',
            'scientific_admission': False}
