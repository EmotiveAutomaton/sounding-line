"""Nonlaunching LA human-bank admission requests, never a runtime PLAN.

DESIGN CHECK: unchanged LA estimand, source and paired numerical cores. A
constructed lifecycle pass is not measured human-model cost or memory. This
module reads receipts and writes private review requests only. No model,
scoring, sampling, fixture, launcher, lease, ACK or publication is invoked.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math

REPO = Path(__file__).resolve().parents[3]
PRIVATE = REPO / '.agent-state/drive-20261107'
BASE = REPO / 'results/phase_2_4_stage_15/raw/drive-week5-20261107'
SNAPSHOT = PRIVATE / 'la-human-admission/SNAPSHOT.json'
SNAPSHOT_SHA = '745ff3f9e99594b6d7a2047b5787d731f10ea9b8a6a9d3f890f5af4b0540bc47'
PIPELINE = 'runners.drive.cards.week5_la_pipeline_v4'
SOURCE = 'runners.drive.cards.week5_la_source'
FIXTURE = 'runners.drive.cards.week5_la_pipeline_v4_fixture'
SELECTIONS = {
    'runners.drive.cards.week5_at_analysis_v3': 'runners.drive.cards.week5_at_collect_v4',
    'runners.drive.cards.week5_at_analysis_v4': 'runners.drive.cards.week5_at_collect_v5',
}
NUMERIC = dict(version='AT-FP64-1', model_computation='float64_from_pinned_float32',
               log_softmax_and_entropy='float32', cache_fresh_tolerance_nats=1e-4,
               attention_backend='original_model_default')
PRIMARY = dict(operation='prepare', card='LA1', corpus='both', history_acts=5,
               window=2., left=1., label='vocal', laugh_scope='all')
STAGES = {'source_preparation', 'selected_reader', 'paired_first_block',
          'paired_pilot', 'collection', 'primary', 'checkpoint_continuation'}


class Refusal(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Refusal(reason)


def read(p):
    return json.loads(Path(p).read_text(encoding='utf8'))


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                    ensure_ascii=False).encode()).hexdigest()


def path(value, within=REPO):
    p = Path(value)
    if not p.is_absolute():
        p = REPO / p
    p = p.resolve()
    p.relative_to(Path(within).resolve())
    return p


def positive(value):
    require(type(value) in (int, float) and math.isfinite(value) and value > 0,
            'Positive measured quantity required; an unknown is not zero')
    return float(value)


def ref(p):
    p = path(p)
    return dict(path=p.relative_to(REPO).as_posix(), sha256=sha(p))


def pins(values):
    normalized = {}
    for name, value in values.items():
        p = path(name)
        key = str(p).casefold()
        require(key not in normalized or normalized[key] == value, 'Conflicting pin aliases')
        require(sha(p) == value, 'Changed frozen dependency: ' + str(p))
        normalized[key] = value
    return normalized


def exited(root, plan_sha):
    # Read-only native identity query. No process is discovered or terminated.
    from runners.stage9.process_identity import is_same_live_process
    owner = read(root / 'OWNER.json')
    require(owner.get('plan_sha256') == plan_sha, 'Native owner is bound to another plan')
    native = owner['native']
    require(type(native.get('pid')) is int and native['pid'] > 0 and
            native.get('creation_time') and native.get('executable'), 'Native identity absent')
    require(not is_same_live_process(native), 'Native owner is still running')


def completed(value, family, module):
    root = path(value, BASE)
    require(not any((root / n).exists() for n in ('PAUSED.json', 'FAILED.json', 'MONITOR_FAILED.json')),
            'Ambiguous or unsuccessful native terminal')
    done, plan = read(root / 'COMPLETE.json'), read(root / 'PLAN.json')
    require(done.get('status') == 'COMPLETE' and done.get('fresh_process_verified') is True,
            'Complete independent native verification required')
    require(not done.get('constructed_dependency_fixture') and
            not done.get('not_a_production_runtime_admission'), 'Nested fixture is not a native admission')
    require(plan.get('campaign') == 'S15-WEEK5' and plan.get('family') == family and
            plan.get('module') == module, 'Wrong campaign, family or exact handler')
    require(done['outputs'].get('PLAN.json') == sha(root / 'PLAN.json'), 'Unsealed native plan')
    for name, value in done['outputs'].items():
        p = (root / name).resolve()
        p.relative_to(root)
        require(sha(p) == value, 'Changed completed output')
    bound = pins(plan['pins'])
    handler = path(module.replace('.', '/') + '.py')
    require(bound.get(str(handler).casefold()) == sha(handler), 'Unpinned exact handler')
    require(read(root / 'VERIFIED.json').get('verified') is True, 'Actual verified=True is missing')
    measured = 0.
    for phase in ('EXECUTE', 'VERIFY'):
        u = read(root / (phase + '_JOB_USAGE.json'))
        require(u.get('exit_code') == 0 and u.get('includes_all_descendants_and_exited_processes') is True,
                'Complete successful descendant accounting required')
        measured += positive(u['cpu_seconds'])
    require(positive(done['cpu_seconds']) + 1e-9 >= measured, 'Terminal undercounts its native phases')
    exited(root, sha(root / 'PLAN.json'))
    return root, plan, done


def frozen():
    require(sha(SNAPSHOT) == SNAPSHOT_SHA, 'LA source/admission snapshot changed')
    value = read(SNAPSHOT)
    pins(value['pins'])
    for record in value['native_receipts'].values():
        require(sha(path(record['complete']['path'])) == record['complete']['sha256'],
                'Frozen source or lifecycle completion changed')
    for record in value['legacy_constructed_proofs']:
        require(sha(path(record['path'])) == record['sha256'], 'Historical fixture changed')
    for model in value['eligible_causal_models']:
        require(sha(path(model['manifest'])) == model['manifest_sha256'], 'Causal model manifest changed')
    mask = value['masked_model']['manifest']
    require(sha(path(mask['path'])) == mask['sha256'], 'Masked model manifest changed')
    prior = value['isolated_AT_resource_evidence_not_LA_admission']
    require(sha(path(prior['path'])) == prior['sha256'], 'Retained isolated-reader resource evidence changed')
    for attempt in value['retained_native_costs']:
        records = [attempt['plan'], *attempt['native_usage']]
        if attempt['terminal']:
            records.append(attempt['terminal'])
        for record in records:
            require(sha(path(record['path'])) == record['sha256'], 'Retained LA accounting receipt changed')
    return value


def source_and_lifecycle(snapshot):
    source, _, _ = completed(snapshot['native_receipts']['LA-source']['root'], 'LA', SOURCE)
    fixture, _, _ = completed(snapshot['native_receipts']['LA-idempotent-completion-native']['root'], 'LA', FIXTURE)
    proof = read(fixture / 'output/FIXTURE.json')
    for key in ('fixture_only', 'no_human_input', 'actual_constructed_causal_fp64_masked_fp32',
                'partial_act_yield_and_continue', 'complete_execute_pause_before_verify_reentry',
                'original_cost_and_numeric_bytes_preserved', 'every_invocation_cost_retained',
                'v3_v4_numeric_bytes_equal', 'mixed_exact_producer_collection_equals_original',
                'unknown_producer_missing_pin_bad_cost_refused'):
        require(proof.get(key) is True, 'Paired lifecycle qualification lacks ' + key)
    return source, fixture


def selected(value, snapshot):
    root = path(value, BASE)
    module = read(root / 'PLAN.json').get('module')
    require(module in SELECTIONS, 'Unreviewed selected-reader producer')
    root, plan, _ = completed(root, 'AT', module)
    config = plan['config']
    require(config.get('card') == 'AT2' and config.get('draws') == 2000 and
            config.get('context', 'final') == 'final' and config.get('context_length', 1024) == 1024,
            'Primary final-context 1024-token reader selection with 2000 draws required')
    models = {m['model']: m for m in snapshot['eligible_causal_models']}
    require(sorted(config['models']) == sorted(models), 'Incomplete or substituted ten-reader selection')
    result = read(root / 'output/RESULT.json')
    binding = read(root / 'output/READER_BINDING.json')
    require(result.get('selection_admissible') is True and not result.get('screening_only') and
            result.get('card') == 'AT2', 'Partial or screening AT2 cannot select an LA reader')
    model = models[result['selected_model']]
    manifest = read(path(model['manifest']))
    require(binding.get('model') == model['model'] and binding.get('revision') == model['revision'] and
            binding.get('manifest_sha256') == digest(manifest) and binding.get('numerical_spec') == NUMERIC and
            binding.get('context') == 'final' and binding.get('context_length') == 1024,
            'Selected model/tokenizer/numerical/context binding differs')
    collection, cp, _ = completed(plan['inputs']['collection_root'], 'AT', SELECTIONS[module])
    require(binding.get('complete_collection_sha256') == sha(collection / 'COMPLETE.json'),
            'Selection points to another complete collection')
    require(cp['config'].get('context', 'final') == 'final' and cp['config'].get('context_length', 1024) == 1024,
            'Selected collection context differs')
    require(read(collection / 'output/NUMERICAL_SPEC.json') == NUMERIC,
            'Selected collection is not the corrected common numerical bank')
    bank = read(path(cp['inputs']['bank_manifest']))
    require(sorted(bank) == sorted(models), 'Selected collection omits a declared reader')
    # The actual scored source (full or an admitted measured whole-writer scope)
    # remains explicit; a four-writer timing pilot is never silently relabelled.
    return dict(selection=ref(root / 'COMPLETE.json'), reader_binding=ref(root / 'output/READER_BINDING.json'),
                collection=ref(collection / 'COMPLETE.json'), selected_manifest=ref(model['manifest']),
                model=model['model'], revision=model['revision'], source_root=cp['inputs']['source_root'],
                scientific_scope_review_required=True)


def prepared(value, source):
    root, plan, _ = completed(value, 'LA', PIPELINE)
    require(path(plan['inputs']['source_root']) == source and plan['config'] == PRIMARY,
            'Different LA source cohort, history, laugh window or preparation condition')
    summary = read(root / 'output/SUMMARY.json')
    require(summary['source_sha256'] == sha(source / 'COMPLETE.json'), 'Prepared source provenance differs')
    index = read(root / 'output/BATCHES.json')
    require(index and len({r['file'] for r in index}) == len(index), 'Empty or duplicated source blocks')
    for i, item in enumerate(index):
        require(item['file'] == f'batches/acts-{i:06d}.json.gz' and 0 < item['rows'] <= 8,
                'Changed eight-act block order or size')
        require(sha(root / 'output' / item['file']) == item['sha256'], 'Prepared act block changed')
    require(sum(i['rows'] for i in index) == summary['counts']['supported_history'],
            'Source work denominator differs from complete prepared census')
    return root, index


def continuation(value):
    root = path(value, BASE)
    require(not any((root / n).exists() for n in ('COMPLETE.json', 'FAILED.json', 'MONITOR_FAILED.json')),
            'Only an authenticated environmental/quantum pause is resumable')
    paused, plan = read(root / 'PAUSED.json'), read(root / 'PLAN.json')
    require(plan.get('campaign') == 'S15-WEEK5' and plan.get('family') == 'LA' and
            plan.get('module') == PIPELINE and plan['config'].get('operation') == 'score',
            'This continuation template covers only the frozen paired v4 scorer')
    require(paused.get('checkpoint_validation_required') is True and paused.get('paused_operation') in ('execute', 'verify'),
            'Explicit checkpointed phase required')
    pins(plan['pins'])
    require(paused.get('checkpoint_outputs'), 'No sealed checkpoint map')
    for name, value in paused['checkpoint_outputs'].items():
        p = (root / 'output' / name).resolve()
        p.relative_to(root / 'output')
        require(sha(p) == value, 'Paused output changed')
    exited(root, sha(root / 'PLAN.json'))
    return dict(predecessor=ref(root / 'PAUSED.json'), original_plan=ref(root / 'PLAN.json'),
                operation=paused['paused_operation'], checkpoint_outputs=paused['checkpoint_outputs'],
                previous_native_cpu_seconds=positive(paused['cpu_seconds']),
                exact_input_config_and_source_pins_must_be_retained=True,
                immutable_copy_and_new_native_attempt_owner_review_required=True)


def request_review(request):
    """Return exact evidence and remaining gates, never a runnable admission."""
    stage = request.get('stage')
    require(stage in STAGES, 'Unregistered LA admission stage')
    snapshot = frozen()
    source, fixture = source_and_lifecycle(snapshot)
    evidence = dict(source=ref(source / 'COMPLETE.json'), lifecycle_fixture=ref(fixture / 'COMPLETE.json'))
    gates = ['Owner must review a separately committed design and native qualification before launch.',
             'Owner must reconcile all LA attempts and current family/campaign room, counted slots and live resources.']
    selection = request.get('selection_root')
    if selection:
        evidence['selected_reader'] = selected(selection, snapshot)
    elif stage not in ('source_preparation', 'checkpoint_continuation'):
        gates.append('Completed primary corrected ten-reader AT2 selection is absent; no substitute reader.')
    prepared_root = request.get('prepared_root')
    if prepared_root:
        root, index = prepared(prepared_root, source)
        evidence['prepared'] = dict(complete=ref(root / 'COMPLETE.json'), blocks=len(index),
                                   work_acts=sum(r['rows'] for r in index))
        if stage in ('paired_first_block', 'paired_pilot'):
            ordinal = request.get('block_ordinal', 0)
            require(type(ordinal) is int and 0 <= ordinal < len(index), 'Invalid source block ordinal')
            if stage == 'paired_first_block':
                require(ordinal == 0, 'First-block qualification cannot skip the first frozen source block')
            evidence['next_block'] = dict(ordinal=ordinal, **index[ordinal],
                                         path=str(root / 'output' / index[ordinal]['file']))
    elif stage in ('paired_first_block', 'paired_pilot', 'collection', 'primary'):
        gates.append('Complete independently verified primary LA1 preparation and work denominator are absent.')
    if stage == 'source_preparation':
        gates.append('Original prepare has no cooperative quantum; exact bounded successor/native proof or measured full-stage bound is required.')
    if stage in ('paired_first_block', 'paired_pilot'):
        gates.extend([
            'Real paired cold-load/execute/verify peak and CPU are unmeasured; explicit qualification caps are not forecasts.',
            'Paired native resource guard and largest-act safe yield latency need a separately reviewed constructed proof.',
            'An entire act is currently atomic; eight-act blocks do not prove compliance with resource-yield grace.',
            'First-5%-of-work prefix must be frozen from the complete denominator; whole-meeting sample count is not yet finalized.',
            'No prior float32 AT bank, partial selected-reader fixture or tiny masked fixture qualifies this human pair.'])
    if stage in ('collection', 'primary'):
        gates.append('Every declared source block must have complete paired independent replay under identical selected-reader and masked bindings.')
        gates.append('Collection/primary cost and independent replay need measured bounded admission; the code target is not a forecast.')
    if stage == 'checkpoint_continuation':
        require(request.get('predecessor_root'), 'Paused predecessor required')
        evidence['continuation'] = continuation(request['predecessor_root'])
        gates.append('Resume needs current memory/slot/budget admission, unchanged sealed copies and all previous charges; nothing is copied here.')
    return dict(schema='LA-REVIEW-REQUEST-1', at=datetime.now(timezone.utc).isoformat(), stage=stage,
                snapshot=ref(SNAPSHOT), evidence=evidence, remaining_prerequisites=gates,
                source_config=PRIMARY, numerical_spec=NUMERIC, masked_precision='float32_original',
                target_module=PIPELINE if stage != 'primary' else 'runners.drive.cards.week5_la',
                target_operation={'source_preparation':'prepare', 'paired_first_block':'score',
                                  'paired_pilot':'score', 'collection':'collect'}.get(stage),
                max_cpu_seconds=None, max_wall_seconds=None, projected_peak_ram_GiB=None,
                measured_paired_peak_bytes=None, forecast_cpu_seconds=None,
                owner_reviewed=False, fixture_for_this_scaffold_passed=False,
                nonlaunchable=True, ready=False, scientific_admission=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    destination = path(args.output, PRIVATE / 'la-human-admission/review-requests')
    require(destination.suffix == '.json' and destination.name.upper() != 'PLAN.JSON',
            'Only a private non-PLAN JSON request can be written')
    result = request_review(read(path(args.request, PRIVATE)))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x', encoding='utf8', newline='\n') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
