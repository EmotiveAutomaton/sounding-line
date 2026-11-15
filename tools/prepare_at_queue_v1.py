"""Nonlaunching owner freezer; metadata only, no model or participant-row decode.

DESIGN CHECK: LESSONS 3-5. Complete-prefix review and actual fixed source pins
are required for either scientific direction. An incomplete or altered prefix
refuses; a forecast is not a new scientific gate. No live PLAN or charge is made.
Run only after the owner has admitted the code and assigned preparation cost.
"""
from pathlib import Path
import argparse
import hashlib
import json


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''): value.update(block)
    return value.hexdigest()


def read(path): return json.loads(Path(path).read_text(encoding='utf8'))


def need(value, message):
    if not value: raise ValueError(message)


def emit(path, value):
    with Path(path).open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def build(request, destination):
    # These imports are used only by the future, counted owner preparation.
    from runners.drive.cards import week5_at_queue_v1 as queue
    from runners.drive.cards import week5_policy_pin_migration as migration
    from runners.drive.cards.week5_at_admission_prepare_v3 import closure
    root = Path.cwd().resolve(); destination = Path(destination).resolve()
    destination.relative_to(root/'.agent-state')
    need(not destination.exists(), 'Fresh private destination required')
    review = read(request['prefix_review']['path'])
    need(sha(request['prefix_review']['path']) == request['prefix_review']['sha256'] and
         review.get('status') == 'OWNER_AUTHENTICATED_COMPLETE_PREFIX' and
         review.get('completed_ordinals') == list(range(133)) and review.get('next_ordinal') == 133 and
         review.get('source_order_unchanged') is True, 'Actual owner complete-prefix review absent')
    for key in ('original_request', 'original_proposal'):
        ref = request[key]
        review_key = 'request_sha256' if key == 'original_request' else 'proposal_sha256'
        need(sha(ref['path']) == ref['sha256'] and review[review_key] == ref['sha256'],
             'Owner review does not bind exact original preparer evidence')
    for key, review_key in [('historical_exit_proofs','historical_exit_proofs_sha256'),
                            ('prefix_preparation_usage','preparation_usage_sha256')]:
        ref=request[key]
        need(sha(ref['path'])==ref['sha256'] and review[review_key]==ref['sha256'],
             'Owner prefix ancillary receipt mismatch')
    original = read(request['original_request']['path'])
    proposal = read(request['original_proposal']['path'])
    plan = proposal['plan_template']
    roots = [Path(p).resolve() for p in original['completed_chunks']]
    need(len(roots) == 133 and original['stage'] == 'pilot_chunk', 'Owner-fixed 133-chunk prefix required')
    source = root/'.agent-state/drive-20261107/at-corrected-bank-proposals/model-00-pilot.json'
    need(sha(source) == queue.MODEL_PROPOSAL_SHA, 'Original m00 proposal changed')
    model = read(source)
    need(Path(plan['inputs']['rows']).resolve() == Path(model['pilot_batches'][133]['input_rows']).resolve(),
         'Reviewed next ordinal is not 133')
    all_pins = {}; historical_roots = set(); chunks = []; attempts = {}
    migration.qualify()
    def translate(pins):
        # The owner original preparer already authenticated every old pin. Build
        # a deduplicated map without repeating its full read for every ancestor;
        # queue entry authenticates the resulting map once. This retains only
        # the exact already reviewed historical policy translation.
        out = {}
        for name,digest in pins.items():
            p = Path(name).resolve(); p.relative_to(root)
            if p == migration.POLICY.resolve() and digest == migration.OLD:
                out[str(p)] = migration.CURRENT
                out[str(migration.ARCHIVE.resolve())] = migration.OLD
            else: out[str(p)] = digest
        return out
    def add(path, digest):
        path = str(Path(path).resolve())
        previous = next((v for k,v in all_pins.items() if k.casefold() == path.casefold()), None)
        need(previous is None or previous == digest, 'Conflicting historical path aliases')
        all_pins[path] = digest
    for ordinal, path in enumerate(roots):
        top = path
        done = read(path/'COMPLETE.json')
        need(done.get('status') == 'COMPLETE' and done.get('fresh_process_verified') is True,
             'Unverified original prefix chunk')
        need(done['outputs']['PLAN.json'] == sha(path/'PLAN.json'), 'Original completion does not seal plan')
        chunks.append(dict(ordinal=ordinal, root=str(path), complete_sha256=sha(path/'COMPLETE.json')))
        local_seen = set()
        while True:
            need(path not in local_seen, 'Cyclic historical resume'); local_seen.add(path)
            historical_roots.add(path)
            terms = [n for n in ('COMPLETE.json','PAUSED.json','FAILED.json') if (path/n).is_file()]
            need(len(terms) == 1 and terms[0] != 'FAILED.json', 'Ambiguous prefix ancestry')
            p = read(path/'PLAN.json'); t = read(path/terms[0])
            need(p['module'] == queue.SCORER and p['family'] == 'AT' and p['campaign'] == 'S15-WEEK5',
                 'Foreign producer in original prefix')
            for name in ('PLAN.json', 'OWNER.json', terms[0]): add(path/name, sha(path/name))
            # COMPLETE seals native phase receipts. PAUSED seals output checkpoints;
            # preserve its additional native receipts with independently pinned bytes.
            for name,digest in t.get('outputs', {}).items():
                target = (path/name).resolve(); target.relative_to(path); add(target,digest)
            for name,digest in t.get('checkpoint_outputs', {}).items():
                target = (path/'output'/name).resolve(); target.relative_to(path/'output'); add(target,digest)
            for extra in ('EXECUTE_JOB_USAGE.json','VERIFY_JOB_USAGE.json','EXECUTE_NATIVE.json','VERIFY_NATIVE.json'):
                if (path/extra).is_file(): add(path/extra,sha(path/extra))
            for name,digest in translate(p['pins']).items(): add(name,digest)
            attempts[str(path)] = dict(root=str(path), terminal=terms[0],
                  terminal_sha256=sha(path/terms[0]), cpu_seconds=t['cpu_seconds'], supervisor_envelope_cpu_seconds=30)
            resume = p.get('resume')
            if not resume: break
            old = Path(resume['root']).resolve()
            need(sha(old/'PLAN.json') == resume['plan_sha256'] and sha(old/'PAUSED.json') == resume['paused_sha256'],
                 'Historical resume identity changed')
            prior = read(old/'PLAN.json')
            need(all(p[k] == prior[k] for k in ('module','inputs','family','campaign')), 'Resume changed source')
            path = old
    add(request['prefix_review']['path'], request['prefix_review']['sha256'])
    for key in ('original_request','original_proposal','historical_exit_proofs','prefix_preparation_usage'):
        add(request[key]['path'],request[key]['sha256'])
    prefix = dict(count=133, owner_reviewed=True, chunks=chunks, attempts=list(attempts.values()),
                  file_pins=all_pins, owner_review=request['prefix_review'],
                  all_prior_AT_failure_and_pause_cost_inventory=request['original_proposal'])
    prefix['manifest_sha256'] = canonical(prefix)
    # Do not copy per-chunk historical references into children: that is the
    # old quadratic validation defect. Static qualification receipts remain.
    def historical(path):
        p = Path(path).resolve()
        return any(p == r or r in p.parents for r in historical_roots)
    child_pins = {p:s for p,s in translate(plan['pins']).items() if not historical(p)}
    # The single-chunk source pin is replaced for each exact frozen ordinal.
    child_pins = {p:s for p,s in child_pins.items() if Path(p).resolve() != Path(plan['inputs']['rows']).resolve()}
    child_pins.update(closure([queue.SCORER, queue.CHILD]))
    need(set(request['premortem'])=={'case_and_check','smaller_route'} and
         all(request['premortem'].values()),'Exact launcher pre-mortem fields required')
    cap = request['caps']
    need(cap['queue_cpu_seconds'] <= 230400 and cap['queue_wall_seconds'] <= 43200,
         'Provisional remaining-pilot envelope exceeded')
    spec = dict(schema='AT_QUEUE_V1', owner_bound=True,
        original_roster=dict(path=str(root/'.agent-state/drive-20261107/at-corrected-bank-proposals/ROSTER.json'),sha256=queue.ROSTER_SHA),
        model_proposal=dict(path=str(source),sha256=queue.MODEL_PROPOSAL_SHA),
        model_ordinal=0, model=model['model'], model_revision=model['model_revision'],
        model_manifest=model['model_manifest'], model_manifest_sha256=model['model_manifest_sha256'],
        numerical_spec=queue.NUMERIC, native_limits=queue.LIMITS, scorer=queue.SCORER,
        numerical_threads=2, start_ordinal=133, end_ordinal_exclusive=165,
        batches=model['pilot_batches'], score_config=dict(context='final',context_length=1024,max_wall_seconds=900),
        prefix=prefix, child_pins=child_pins, caps=cap)
    queue.validate_manifest(spec)
    destination.mkdir(parents=True)
    emit(destination/'QUEUE_MANIFEST.json', spec)
    module_pins = closure([queue.MODULE, 'runners.drive.week5_launch_v10',
                           'runners.drive.cards.week5_runtime_v12', 'runners.drive.cards.week5_policy_v3'])
    module_pins[str(destination/'QUEUE_MANIFEST.json')] = sha(destination/'QUEUE_MANIFEST.json')
    qualification = request['qualification']
    need(qualification['native_fixture_and_actual_launcher_reviewed'] is True,
         'Native nested-job and actual launcher qualification must precede owner binding')
    for ref in qualification['receipts']:
        need(sha(ref['path']) == ref['sha256'], 'Qualification receipt changed')
        module_pins[ref['path']] = ref['sha256']
    # Private proposal only: owner must separately review remaining charges,
    # frozen campaign clocks, queue-slot availability and then admit it.
    result = dict(campaign='S15-WEEK5', card='AT2-m00-original-pilot-queue-v1', family='AT',
        module=queue.MODULE, inputs=dict(queue_manifest=str(destination/'QUEUE_MANIFEST.json')), config={},
        pins=module_pins, owner_reviewed=False, fixture_passed=True, gpu=False, paid=False, ollama=False,
        numerical_threads=2, max_cpu_seconds=cap['queue_cpu_seconds'], max_wall_seconds=cap['queue_wall_seconds'],
        projected_peak_ram_GiB=cap['projected_peak_ram_GiB'], max_output_bytes=cap['output_bytes'],
        accounting_runtime='week5-v11', design=request['design'],
        reviewed_design_commit=request['reviewed_design_commit'], validation_receipts=[r['path'] for r in qualification['receipts']],
        premortem=request['premortem'], pilot_fraction=.05, template_only=True,
        original_AT_family_ceiling_cpu_seconds=750000, original_campaign_ceiling_cpu_seconds=6000000,
        actual_remaining_allowance_and_campaign_clock_review_required=True)
    emit(destination/'PLAN_CANDIDATE.json', result)
    emit(destination/'PREPARATION_RECEIPT.json', dict(nonlaunchable=True,
        original_prefix_chunks=133, remaining_chunks=32, unique_historical_pins=len(all_pins),
        old_history_not_copied_into_child_pins=True, human_rows_decoded=False,
        complete_prefix_data_rehash_deferred_to_one_counted_queue_entry=True,
        prep_cpu_charge=request['preparation_charge_receipt']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('request',type=Path);parser.add_argument('destination',type=Path)
    args = parser.parse_args();build(read(args.request),args.destination)
