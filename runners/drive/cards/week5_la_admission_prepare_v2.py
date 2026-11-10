"""Immutable LA request successor binding bounded source qualification.

Only receipt inspection and private nonlaunchable request writing. The old
selection, paired numerical, cost and resource gates remain unchanged. A
template, nested constructed completion, or local copy is not native proof.
"""
from pathlib import Path
from types import FunctionType
import argparse
import gzip
import json

from . import week5_la_admission_prepare as old

PREDECESSOR_SHA = '90efc6fe76293fe8153d0d4d4e28d0d8bb0e0f8da5bd5932f4f198bafd210fdd'
PREPARED = old.PRIVATE / 'la-bounded-preparation-prepared.json'
PREPARED_SHA = '9e8657ec4580fb76f0b482133ea77d895e7de1e961b380fb7dbf8e75ebfcc931'
PREPARER = 'runners.drive.cards.week5_la_prepare_v1'
FIXTURE = 'runners.drive.cards.week5_la_prepare_v1_fixture'
CHAIN_CONFIG = dict(card='LA1', operation='prepare', max_new_blocks=5, max_wall_seconds=600)
ORIGINAL_MISSING = 'Original prepare has no cooperative quantum; exact bounded successor/native proof or measured full-stage bound is required.'
require, read, sha, path, ref = old.require, old.read, old.sha, old.path, old.ref


def frozen_successor():
    require(sha(old.__file__) == PREDECESSOR_SHA and sha(PREPARED) == PREPARED_SHA,
            'Delivered LA admission or bounded-preparation identity changed')
    value = read(PREPARED)
    old.pins(value['files'])
    old.pins(value['source_closure'])
    require(value['module'] == PREPARER and value['fixture_module'] == FIXTURE,
            'Unknown bounded preparation producer or fixture')
    return value


def required_pins(plan, frozen):
    actual = old.pins(plan['pins'])
    for name, expected in frozen['source_closure'].items():
        require(actual.get(str(path(name)).casefold()) == expected,
                'Native qualification omitted a frozen bounded-pipeline dependency')
    require(plan.get('owner_reviewed') is True and plan.get('fixture_passed') is True and
            plan.get('reviewed_design_commit'), 'Native plan lacks owner/design/qualification declarations')
    require(plan.get('numerical_threads') == 2 and plan.get('gpu') is False and
            plan.get('paid') is False and plan.get('ollama') is False, 'Qualification allocation differs')


def state_at(root, phase):
    """Read sealed state only; never invoke the producer or decode source data."""
    binding = read(root / 'output/PREPARATION_BINDING.json')
    directory = root / 'output/checkpoints' / phase
    seals = sorted(directory.glob('*.seal.json'))
    require(seals, 'Actual native phase has no sealed source checkpoint')
    previous = None
    state = None
    for i, seal_path in enumerate(seals):
        require(seal_path.name == f'{i:06d}.seal.json', 'Source checkpoint chain has a gap')
        data_path = directory / f'{i:06d}.json.gz'
        seal = read(seal_path)
        require(seal == dict(file=data_path.name, sha256=sha(data_path),
                             previous_seal_sha256=previous, binding=old.digest(binding)),
                'Source checkpoint hash or predecessor binding differs')
        value = json.loads(gzip.decompress(data_path.read_bytes()))
        require(value['binding'] == binding and value['phase'] == phase,
                'Wrong source checkpoint operation or binding')
        current = value['state']
        if state is not None:
            require(tuple(current['cursor']) >= tuple(state['cursor']) and
                    current['batches'][:len(state['batches'])] == state['batches'],
                    'Source checkpoint replaced earlier completed work')
        state, previous = current, sha(seal_path)
    for i, item in enumerate(state['batches']):
        require(item['file'] == f'batches/acts-{i:06d}.json.gz' and
                sha(root / 'output' / item['file']) == item['sha256'], 'Retained source bank differs')
    return state


def paused(value, operation, frozen):
    root = path(value, old.BASE)
    require(not any((root / n).exists() for n in ('COMPLETE.json', 'FAILED.json', 'MONITOR_FAILED.json')),
            'Ambiguous or failed attempt is not a source pause')
    plan, receipt = read(root / 'PLAN.json'), read(root / 'PAUSED.json')
    require(plan.get('campaign') == 'S15-WEEK5' and plan.get('family') == 'LA' and
            plan.get('module') == PREPARER, 'Wrong source continuation identity')
    require(receipt.get('status') == 'PAUSED' and receipt.get('checkpoint_validation_required') is True and
            receipt.get('paused_operation') == operation, 'Different or unverified paused phase')
    required_pins(plan, frozen)
    old.exited(root, sha(root / 'PLAN.json'))
    outputs = receipt['checkpoint_outputs']
    require(isinstance(outputs, dict) and outputs, 'Actual native checkpoint manifest absent')
    # Mirror the immutable native resume manifest's exclusions, without copying
    # any files or changing its root, leases or process identity.
    actual = {p.relative_to(root / 'output').as_posix(): sha(p)
              for p in sorted((root / 'output').rglob('*'))
              if p.is_file() and p.name not in {'YIELD_REQUEST.json', 'PROGRESS.json'} and
              not p.name.endswith('.tmp') and '.tmp.' not in p.name}
    require(actual == outputs, 'Native paused output manifest is incomplete or changed')
    phases = ('EXECUTE',) if operation == 'execute' else ('EXECUTE', 'VERIFY')
    measured = 0.
    for phase in phases:
        usage = read(root / (phase + '_JOB_USAGE.json'))
        require(usage.get('exit_code') == 0 and usage.get('includes_all_descendants_and_exited_processes') is True,
                'Paused phase lacks successful native descendant accounting')
        measured += old.positive(usage['cpu_seconds'])
    require(old.positive(receipt['cpu_seconds']) + 1e-9 >= measured, 'Paused terminal undercounts native phases')
    return root, plan, receipt


def linked_copy(prior, successor, prior_plan, successor_plan):
    spec = successor_plan.get('resume')
    require(isinstance(spec, dict) and path(spec['root']) == prior and
            spec.get('plan_sha256') == sha(prior / 'PLAN.json') and
            spec.get('paused_sha256') == sha(prior / 'PAUSED.json'), 'Native resume points to another predecessor')
    for key in ('module', 'inputs', 'config', 'family', 'campaign'):
        require(prior_plan[key] == successor_plan[key], 'Qualification chain changed the frozen ' + key)
    old_pins, new_pins = old.pins(prior_plan['pins']), old.pins(successor_plan['pins'])
    require(all(new_pins.get(k) == v for k, v in old_pins.items()), 'Continuation dropped predecessor pins')
    copied = read(successor / 'RESUMED_FROM.json')
    expected = read(prior / 'PAUSED.json')['checkpoint_outputs']
    require(copied.get('adapter') == 'week5_resume_v2' and copied.get('module') == PREPARER and
            path(copied['predecessor']) == prior and copied.get('plan_sha256') == spec['plan_sha256'] and
            copied.get('paused_sha256') == spec['paused_sha256'] and copied.get('copied') == expected,
            'Actual native copy receipt is absent or incompatible')
    for name, digest in expected.items():
        target = (successor / 'output' / name).resolve()
        target.relative_to(successor / 'output')
        require(sha(target) == digest, 'Copied immutable predecessor byte changed')


def native_fixture(value, frozen):
    root, plan, done = old.completed(value, 'LA', FIXTURE)
    required_pins(plan, frozen)
    proof = read(root / 'output/FIXTURE.json')
    for key in ('fixture_only', 'no_human_input', 'no_model_or_selected_reader',
                'independently_replayed_original_and_bounded_handlers'):
        require(proof.get(key) is True, 'Source fixture lacks ' + key)
    require(proof.get('actual_stopped_native_checkpoint_chain_still_requires_owner_admission') is True,
            'Local copy fixture incorrectly claims native continuation')
    records = proof['original_v3_byte_identical_source_banks']
    require(proof.get('declared_variant_count') == 11 and len(records) == 11 and
            [r['case'] for r in records] == list(range(11)), 'Declared source variant proof is incomplete')
    for record in records:
        for name, expected in record['source_bank'].items():
            for producer in ('original', 'bounded'):
                p = root / 'output' / f'case-{record["case"]:02d}' / producer / name
                require(sha(p) == expected, 'Actual original/bounded source bytes differ')
    controls = proof['controls']
    for key in ('partial_buffer_copied_exactly', 'completed_execute_reentry', 'pre_source_yield',
                'modified_batch_checkpoint_cursor_config_source_refused',
                'unexpected_batch_and_extra_reader_input_refused', 'local_copy_control_only_not_a_native_resume'):
        require(controls.get(key) is True, 'Source continuation/refusal proof lacks ' + key)
    return root, done


def qualification(value, frozen):
    if not value:
        return dict(fixture_complete=False, counted_chain_complete=False,
                    missing=['Actual completed bounded-source native fixture', 'Actual execute-pause/verify-pause/complete counted chain'])
    require(set(value) <= {'fixture_root', 'chain_roots'}, 'Unknown qualification payload; templates are not receipts')
    require(value.get('fixture_root'), 'Qualification must name an actual native fixture root')
    fixture, receipt = native_fixture(value['fixture_root'], frozen)
    result = dict(fixture_complete=True, fixture=ref(fixture / 'COMPLETE.json'),
                  native_fixture_cpu_seconds=receipt['cpu_seconds'], counted_chain_complete=False,
                  missing=['Actual execute-pause/verify-pause/complete counted chain'])
    if not value.get('chain_roots'):
        return result
    roots = [path(p, old.BASE) for p in value['chain_roots']]
    require(len(roots) == 3 and len(set(roots)) == 3, 'Three distinct actual native attempts required')
    a, ap, ar = paused(roots[0], 'execute', frozen)
    b, bp, br = paused(roots[1], 'verify', frozen)
    c, cp, cr = old.completed(roots[2], 'LA', PREPARER)
    required_pins(cp, frozen)
    source = fixture / 'output/constructed-source'
    identities = []
    for root, plan in ((a, ap), (b, bp), (c, cp)):
        require(plan['config'] == CHAIN_CONFIG and set(plan['inputs']) == {'source_root'} and
                path(plan['inputs']['source_root']) == source, 'Native chain changed its exact constructed source or quantum')
        bound = old.pins(plan['pins'])
        require(bound.get(str(fixture / 'COMPLETE.json').casefold()) == sha(fixture / 'COMPLETE.json'),
                'Native chain does not pin the actual completed oracle fixture')
        native = read(root / 'OWNER.json')['native']
        identities.append((native['pid'], native['creation_time']))
    require(len(set(identities)) == 3, 'Copied metadata is not three native owners')
    linked_copy(a, b, ap, bp)
    linked_copy(b, c, bp, cp)
    sa, sb, sc = state_at(a, 'execute'), state_at(b, 'verify'), state_at(c, 'verify')
    for state in (sa, sb):
        require(len(state['batches']) == 5 and state['counts'].get('supported_history') == 40 and not state['buffer'],
                'Native chain paused at a different source boundary')
    require(sc['cursor'] == [3, 0] and sc['counts'] == dict(acts=84, insufficient_prior_history=15, supported_history=69) and
            len(sc['batches']) == 9 and sc['batches'][-1]['rows'] == 5 and not sc['buffer'],
            'Complete native source replay did not retain the known population')
    expected = read(fixture / 'output/FIXTURE.json')['original_v3_byte_identical_source_banks'][0]['source_bank']
    for name, digest in expected.items():
        require(sha(c / 'output' / name) == digest, 'Counted native continuation differs from the complete original oracle')
    require(read(c / 'VERIFIED.json').get('independent_checkpointed_replay') is True,
            'Native final verification lacks independent source replay')
    result.update(counted_chain_complete=True, missing=[], chain=[ref(a / 'PAUSED.json'), ref(b / 'PAUSED.json'), ref(c / 'COMPLETE.json')],
                  chain_native_cpu_seconds=sum(old.positive(r['cpu_seconds']) for r in (ar, br, cr)),
                  real_source_cost_or_peak_admission=False)
    return result


def semantic_primary(config):
    require(set(config) <= set(old.PRIMARY) | {'others_only', 'max_new_blocks', 'max_wall_seconds'},
            'Unknown bounded primary source configuration')
    supplied = dict(operation=config.get('operation', 'prepare'), card=config.get('card'),
                    corpus=config.get('corpus', 'both'), history_acts=config.get('history_acts', 5),
                    window=config.get('window', 2.), left=config.get('left', 1.), label=config.get('label', 'vocal'),
                    laugh_scope=config.get('laugh_scope', 'others' if config.get('others_only', False) else 'all'))
    require(supplied == old.PRIMARY, 'Different primary source meaning or scope')


def prepared(value, source, proof, frozen):
    root = path(value, old.BASE)
    module = read(root / 'PLAN.json').get('module')
    if module == old.PIPELINE:
        return old.prepared(value, source)
    require(module == PREPARER and proof.get('counted_chain_complete') is True,
            'Unknown or not-natively-qualified bounded preparer')
    root, plan, _ = old.completed(root, 'LA', PREPARER)
    required_pins(plan, frozen)
    require(set(plan['inputs']) == {'source_root'} and path(plan['inputs']['source_root']) == source,
            'Prepared source is not the retained full LA population')
    semantic_primary(plan['config'])
    summary = read(root / 'output/SUMMARY.json')
    require(summary['source_sha256'] == sha(source / 'COMPLETE.json'), 'Bounded preparation source pin differs')
    index = read(root / 'output/BATCHES.json')
    require(index and len({x['file'] for x in index}) == len(index), 'Empty or duplicated bounded preparation bank')
    for i, row in enumerate(index):
        require(row['file'] == f'batches/acts-{i:06d}.json.gz' and 0 < row['rows'] <= 8 and
                (i == len(index) - 1 or row['rows'] == 8) and sha(root / 'output' / row['file']) == row['sha256'],
                'Bounded source block order, size or bytes differ')
    require(sum(row['rows'] for row in index) == summary['counts']['supported_history'], 'Bounded source work denominator differs')
    state = state_at(root, 'verify')
    require(state['batches'] == index and state['counts'] == summary['counts'] and not state['buffer'] and
            read(root / 'VERIFIED.json').get('independent_checkpointed_replay') is True,
            'Full independent bounded-source replay is absent')
    return root, index


def request_review(request):
    frozen = frozen_successor()
    proof = qualification(request.get('bounded_qualification'), frozen)
    bounded_resume = request.get('stage') == 'checkpoint_continuation' and request.get('continuation_kind') == 'bounded_source'
    def inspect_prepared(value, source):
        return prepared(value, source, proof, frozen)
    def inspect_continuation(value):
        if not bounded_resume:
            return old.continuation(value)
        require(proof.get('counted_chain_complete') is True, 'Bounded-source native continuation remains unqualified')
        root = path(value, old.BASE)
        operation = read(root / 'PAUSED.json').get('paused_operation')
        require(operation in ('execute', 'verify'), 'Unknown source pause phase')
        root, plan, paused_receipt = paused(root, operation, frozen)
        semantic_primary(plan['config'])
        require(path(plan['inputs']['source_root']) == path(read(old.SNAPSHOT)['native_receipts']['LA-source']['root']),
                'Source continuation changed full population')
        return dict(predecessor=ref(root / 'PAUSED.json'), original_plan=ref(root / 'PLAN.json'),
                    operation=operation, checkpoint_outputs=paused_receipt['checkpoint_outputs'],
                    previous_native_cpu_seconds=old.positive(paused_receipt['cpu_seconds']),
                    immutable_copy_and_new_native_attempt_owner_review_required=True)
    fn = FunctionType(old.request_review.__code__, dict(old.request_review.__globals__,
                      prepared=inspect_prepared, continuation=inspect_continuation),
                      old.request_review.__name__, old.request_review.__defaults__, old.request_review.__closure__)
    result = fn(request)
    result['schema'] = 'LA-REVIEW-REQUEST-2'
    result['bounded_preparer'] = dict(module=PREPARER, prepared_handoff=ref(PREPARED), qualification=proof)
    if request['stage'] == 'source_preparation':
        require(ORIGINAL_MISSING in result['remaining_prerequisites'], 'Original source gate unexpectedly changed')
        result['remaining_prerequisites'].remove(ORIGINAL_MISSING)
        result['remaining_prerequisites'].extend(proof['missing'])
        result['remaining_prerequisites'].append('Real source decode/group/meeting/checkpoint timing and peak remain unmeasured; counted cost/resource admission is separate.')
        result['target_module'] = PREPARER
        result['target_config'] = dict(old.PRIMARY, max_new_blocks=32, max_wall_seconds=600)
    if bounded_resume:
        result['target_module'] = PREPARER
        result['target_operation'] = 'prepare'
    result['remaining_prerequisites'].append('This successor request checker still needs its own owner-reviewed constructed refusal qualification.')
    # These flags never become readiness or authorization, even after a chain
    # is supplied. Real budgets, resources, scientific scope and models stay gated.
    require(result['nonlaunchable'] and not result['ready'] and not result['owner_reviewed'], 'A request became an admission')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    destination = path(args.output, old.PRIVATE / 'la-human-admission-v2/review-requests')
    require(destination.suffix == '.json' and destination.name.upper() != 'PLAN.JSON', 'Private non-PLAN request required')
    result = request_review(read(path(args.request, old.PRIVATE)))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x', encoding='utf8', newline='\n') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
