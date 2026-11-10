"""Nonlaunching LA v5 guard/checkpoint/collector admission successor.

Actual completed native qualifications are mandatory evidence. Templates and
source hashes alone never clear a qualification, resource or reader gate.
"""
from pathlib import Path
from types import FunctionType, SimpleNamespace
import argparse
import json
from . import week5_la_admission_prepare as base
from . import week5_la_admission_prepare_v2 as bounded
from . import week5_la_native_evidence as native
from . import week5_la_collect_v5 as collector
from . import week5_la_scoring_guard_v1 as guarded

BOUNDED_SHA = 'f8747c5e9eea846de05c3fd8902518e3434944b127525511d6765216618ef91c'
PAIRED = base.PRIVATE / 'la-paired-checkpoints-prepared.json'
PAIRED_SHA = 'bd59d780ec959907a0022121cbdc1a15d71577c3fb9667339505420434809f8c'
PAIR_FIXTURE = 'runners.drive.cards.week5_la_pipeline_v5_fixture'
PAIR_CHAIN = 'runners.drive.cards.week5_la_paired_chain_fixture'
COLLECT_FIXTURE = 'runners.drive.cards.week5_la_collect_v5_fixture'
require, read, sha, path, ref = base.require, base.read, base.sha, base.path, base.ref


def clone_module(module, replacements):
    namespace = dict(module.__dict__)
    for name, value in module.__dict__.items():
        if isinstance(value, FunctionType) and value.__module__ == module.__name__:
            fn = FunctionType(value.__code__, namespace, value.__name__, value.__defaults__, value.__closure__)
            fn.__kwdefaults__ = value.__kwdefaults__
            namespace[name] = fn
    namespace.update(replacements)
    return SimpleNamespace(**namespace)


def bounded_qualification(value, frozen, api):
    """Original known-source chain checks with exact native FILETIME identity."""
    if not value:
        return dict(fixture_complete=False, counted_chain_complete=False,
                    missing=['Actual completed bounded-source native fixture', 'Actual execute-pause/verify-pause/complete counted chain'])
    require(set(value) <= {'fixture_root', 'chain_roots'} and value.get('fixture_root'),
            'Actual bounded-source fixture required; templates are not receipts')
    fixture, receipt = api.native_fixture(value['fixture_root'], frozen)
    result = dict(fixture_complete=True, fixture=ref(fixture / 'COMPLETE.json'), native_fixture_cpu_seconds=receipt['cpu_seconds'],
                  counted_chain_complete=False, missing=['Actual execute-pause/verify-pause/complete counted chain'])
    if not value.get('chain_roots'):
        return result
    roots = [path(p, base.BASE) for p in value['chain_roots']]
    require(len(roots) == 3 and len(set(roots)) == 3, 'Three distinct actual bounded-source attempts required')
    a, ap, ar = api.paused(roots[0], 'execute', frozen)
    b, bp, br = api.paused(roots[1], 'verify', frozen)
    c, cp, cr = native.completed(roots[2], 'LA', bounded.PREPARER)
    api.required_pins(cp, frozen)
    identities = []
    for root, plan in ((a, ap), (b, bp), (c, cp)):
        require(plan['config'] == bounded.CHAIN_CONFIG and set(plan['inputs']) == {'source_root'} and
                path(plan['inputs']['source_root']) == fixture / 'output/constructed-source', 'Bounded-source chain input/quantum changed')
        require(base.pins(plan['pins']).get(str(fixture / 'COMPLETE.json').casefold()) == sha(fixture / 'COMPLETE.json'),
                'Source chain lacks the actual native oracle fixture pin')
        identities.append(native.key(read(root / 'OWNER.json')['native']))
    require(len(set(identities)) == 3, 'Copied metadata is not three actual source owners')
    native.linked_copy(a, b, ap, bp)
    native.linked_copy(b, c, bp, cp)
    sa, sb, sc = api.state_at(a, 'execute'), api.state_at(b, 'verify'), api.state_at(c, 'verify')
    for state in (sa, sb):
        require(len(state['batches']) == 5 and state['counts'].get('supported_history') == 40 and not state['buffer'],
                'Different original source pause boundary')
    require(sc['cursor'] == [3, 0] and sc['counts'] == dict(acts=84, insufficient_prior_history=15, supported_history=69) and
            len(sc['batches']) == 9 and sc['batches'][-1]['rows'] == 5 and not sc['buffer'], 'Known original source population differs')
    expected = read(fixture / 'output/FIXTURE.json')['original_v3_byte_identical_source_banks'][0]['source_bank']
    for name, expected_sha in expected.items():
        require(sha(c / 'output' / name) == expected_sha, 'Native source continuation differs from original oracle')
    require(read(c / 'VERIFIED.json').get('independent_checkpointed_replay') is True, 'Fresh source replay absent')
    result.update(counted_chain_complete=True, missing=[], chain=[ref(a / 'PAUSED.json'), ref(b / 'PAUSED.json'), ref(c / 'COMPLETE.json')],
                  chain_native_cpu_seconds=sum(base.positive(r['cpu_seconds']) for r in (ar, br, cr)), real_source_cost_or_peak_admission=False)
    return result


def paired_frozen():
    require(sha(bounded.__file__) == BOUNDED_SHA and sha(PAIRED) == PAIRED_SHA, 'Delivered admission/paired identity changed')
    value = read(PAIRED)
    base.pins(value['files'])
    base.pins(value['source_closure'])
    return value


def qualification_pins(plan, frozen):
    actual = base.pins(plan['pins'])
    for name, expected in frozen['source_closure'].items():
        require(actual.get(str(path(name)).casefold()) == expected, 'Actual native proof omitted a frozen paired dependency')
    require(plan.get('owner_reviewed') is True and plan.get('fixture_passed') is True and
            plan.get('reviewed_design_commit') and plan.get('numerical_threads') == 2 and
            plan.get('gpu') is False and plan.get('paid') is False and plan.get('ollama') is False,
            'Native qualification lacks reviewed CPU-only declarations')


def paired_qualification(value, frozen=None):
    frozen = paired_frozen() if frozen is None else frozen
    absent = ['Actual completed paired original-output/refusal fixture', 'Actual paired execute-pause/verify-pause/complete native chain']
    if not value:
        return dict(fixture_complete=False, counted_chain_complete=False, missing=absent)
    require(set(value) <= {'fixture_root', 'chain_roots'} and value.get('fixture_root'), 'Only actual paired fixture/chain roots accepted')
    fixture, fp, fd = native.completed(value['fixture_root'], 'LA', PAIR_FIXTURE)
    qualification_pins(fp, frozen)
    proof = read(fixture / 'output/FIXTURE.json')
    for name in ('fixture_only', 'no_human_input', 'actual_tiny_paired_models', 'original_numeric_bytes_equal',
                 'within_act_execute_and_verify_pause', 'retained_causal_and_masked_checkpoints', 'complete_cost_reentry',
                 'original_support_refusal_unchanged', 'changed_input_and_checkpoint_refusals',
                 'missing_selection_unknown_config_unguarded_refusals', 'old_collector_refuses_new_producer',
                 'before_and_between_load_refusal', 'synthetic_guard_control_not_memory_measurement',
                 'local_copy_not_native_continuation_proof', 'every_outer_verify_reforwards_all_masks'):
        require(proof.get(name) is True, 'Actual paired fixture lacks ' + name)
    require(proof.get('human_paired_load_or_latency_qualified') is False and proof.get('collector_admission') is False,
            'Constructed qualification incorrectly claims real-pair admission')
    require(read(fixture / 'VERIFIED.json').get('complete_constructed_paired_checkpoint_integration') is True,
            'Actual native paired integration replay absent')
    result = dict(fixture_complete=True, fixture=ref(fixture / 'COMPLETE.json'), counted_chain_complete=False,
                  missing=absent[1:], native_fixture_cpu_seconds=fd['cpu_seconds'], real_paired_peak_or_cost_admission=False)
    if not value.get('chain_roots'):
        return result
    roots = [path(p, base.BASE) for p in value['chain_roots']]
    require(len(roots) == 3 and len(set(roots)) == 3, 'Three distinct actual paired attempts required')
    items = native.chain(roots[-1], 'LA', PAIR_CHAIN)
    require([item['root'] for item in items] == roots and items[0]['terminal'].get('paused_operation') == 'execute' and
            items[1]['terminal'].get('paused_operation') == 'verify', 'Different actual paired A/B/C continuation chain')
    for item in items:
        plan = item['plan']
        qualification_pins(plan, frozen)
        require(plan['config'] == {} and set(plan['inputs']) == {'constructed_fixture_root'} and
                path(plan['inputs']['constructed_fixture_root']) == fixture, 'Paired native chain changed constructed oracle source')
        require(base.pins(plan['pins']).get(str(fixture / 'COMPLETE.json').casefold()) == sha(fixture / 'COMPLETE.json'),
                'Paired native chain lacks actual oracle completion pin')
    a, b, c = roots
    require(not (a / 'output/act-000.json').exists() and not (a / 'output/COST.json').exists(), 'Execute pause has falsely completed an act')
    require((b / 'output/act-000.json').is_file() and not (b / 'output/verified_acts/act-000.json').exists(),
            'Verify pause is not the complete-execute/partial-replay boundary')
    for root, phase in ((a, 'execute'), (b, 'verify')):
        for arm in ('before', 'after'):
            require([p.name for p in (root / 'output/within_act/act-000/masked' / phase / arm).glob('*.seal.json')] == ['000000.seal.json'],
                    'Different original two-mask native pause boundary')
    source = fixture / 'output'
    score_plan = dict(inputs=read(source / 'CHAIN_INPUTS.json'), config=read(source / 'CHAIN_CONFIG.json'))
    collector.checkpoint_proof(c, score_plan)
    collector.guard_proof(c, items[-1]['terminal'], [r for item in items for r in item['records']])
    for name in ('act-000.json', 'INDEX.json', 'SUMMARY.json'):
        require(sha(c / 'output' / name) == sha(source / 'chain-original-v3' / name), 'Native paired chain differs from original numeric bytes')
    require(read(c / 'VERIFIED.json').get('constructed_paired_continuation') is True, 'Actual final paired native replay absent')
    result.update(counted_chain_complete=True, missing=[], chain=[ref(a / 'PAUSED.json'), ref(b / 'PAUSED.json'), ref(c / 'COMPLETE.json')],
                  chain_native_cpu_seconds=sum(item['terminal']['cpu_seconds'] for item in items))
    return result


def collector_qualification(value, pair_proof):
    if not value:
        return dict(complete=False, missing=['Actual completed native collector original-output/provenance refusal fixture'])
    require(pair_proof.get('counted_chain_complete') is True, 'Collector proof cannot replace missing paired native qualification')
    root, plan, done = native.completed(value, 'LA', COLLECT_FIXTURE)
    proof = read(root / 'output/FIXTURE.json')
    require(read(root / 'VERIFIED.json').get('collector_and_admission_refusals') is True,
            'Actual collector independent verification absent')
    for name in ('fixture_only', 'actual_completed_paired_chain_required', 'original_collection_outputs_equal',
                 'native_identity_guard_replay_refusals', 'templates_and_nested_completions_refused',
                 'admission_remains_nonlaunchable', 'constructed_projection_is_not_production_admission'):
        require(proof.get(name) is True, 'Actual collector fixture lacks ' + name)
    require(proof['paired_chain_complete_sha256'] == pair_proof['chain'][-1]['sha256'], 'Collector proof used another paired native chain')
    pinned = base.pins(plan['pins'])
    for file in (collector.__file__, native.__file__, __file__):
        require(pinned.get(str(Path(file).resolve()).casefold()) == sha(file), 'Unpinned exact collector/admission/native evidence code')
    return dict(complete=True, missing=[], fixture=ref(root / 'COMPLETE.json'), native_cpu_seconds=done['cpu_seconds'])


def request_review(request):
    frozen = paired_frozen()
    pair_proof = paired_qualification(request.get('paired_qualification'), frozen)
    collect_proof = collector_qualification(request.get('collector_qualification_root'), pair_proof)
    old = native.corrected_legacy()
    paired_resume = request.get('stage') == 'checkpoint_continuation' and request.get('continuation_kind') == 'paired_v5'
    if paired_resume:
        def continuation(value):
            require(pair_proof.get('counted_chain_complete') is True, 'Actual paired native chain is not qualified')
            root, plan, receipt, _ = native.paused(value, 'LA', guarded.__name__)
            collector.required_pins(plan)
            return dict(predecessor=ref(root / 'PAUSED.json'), original_plan=ref(root / 'PLAN.json'),
                        operation=receipt['paused_operation'], checkpoint_outputs=receipt['checkpoint_outputs'],
                        previous_native_cpu_seconds=base.positive(receipt['cpu_seconds']),
                        immutable_copy_and_new_native_attempt_owner_review_required=True)
        old.request_review.__globals__['continuation'] = continuation
        old.continuation = continuation
    api = clone_module(bounded, dict(old=old))
    # All functions share only this private namespace. Legacy modules remain
    # immutable, including the known unexecuted FILETIME compatibility defect.
    api.request_review.__globals__['qualification'] = lambda value, source_frozen: bounded_qualification(value, source_frozen, api)
    result = api.request_review(request)
    result['schema'] = 'LA-REVIEW-REQUEST-3'
    result['paired_checkpoint_qualification'] = pair_proof
    result['guarded_collector_qualification'] = collect_proof
    result['paired_handoff'] = ref(PAIRED)
    result['remaining_prerequisites'].extend(pair_proof['missing'] + collect_proof['missing'])
    stage = request['stage']
    if stage in ('paired_first_block', 'paired_pilot') or paired_resume:
        result['target_module'] = guarded.__name__
        result['target_operation'] = 'score'
        result['target_config'] = dict(operation='score', max_new_mask_batches=32, max_wall_seconds=600)
    if stage == 'collection':
        result['target_module'] = collector.__name__
    if pair_proof.get('counted_chain_complete'):
        obsolete = {'Paired native resource guard and largest-act safe yield latency need a separately reviewed constructed proof.',
                    'An entire act is currently atomic; eight-act blocks do not prove compliance with resource-yield grace.'}
        result['remaining_prerequisites'] = [g for g in result['remaining_prerequisites'] if g not in obsolete]
    result['remaining_prerequisites'].append('Actual paired cold-load/transient-commit peak, atomic causal/eight-mask latency, checkpoint-authentication latency and complete pilot/replay cost remain separate measured admission gates.')
    if request.get('score_bank'):
        require(request.get('prepared_root') and stage in ('collection', 'primary'), 'Full declared prepared bank required for score inspection')
        source = path(request['prepared_root'], base.BASE)
        index = read(source / 'output/BATCHES.json')
        bank = read(path(request['score_bank']))
        require(set(bank) == {r['file'] for r in index}, 'Incomplete declared guarded score bank')
        producers = []
        for row in index:
            root = path(bank[row['file']], base.BASE)
            plan = read(root / 'PLAN.json')
            require(plan.get('module') == guarded.__name__ and sha(path(plan['inputs']['rows'])) == row['sha256'],
                    'Human admission route requires exact guarded producer and source block')
            producers.append(collector.producer(root, plan))
        result['evidence']['complete_guarded_bank'] = dict(bank=ref(request['score_bank']), blocks=len(producers), producers=producers)
    require(result['nonlaunchable'] and not result['ready'] and not result['owner_reviewed'], 'Request became an executable admission')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    destination = path(args.output, base.PRIVATE / 'la-human-admission-v3/review-requests')
    require(destination.suffix == '.json' and destination.name.upper() != 'PLAN.JSON', 'Private non-PLAN request required')
    value = request_review(read(path(args.request, base.PRIVATE)))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
