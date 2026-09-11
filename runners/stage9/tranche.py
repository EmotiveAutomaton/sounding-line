"""Explicit, bounded Stage 9 execution coverage; the full-stage path is unchanged.

DESIGN CHECK: execution recovery addendum sections 3--7; LESSONS 3/5.
NULL: dropping a dependency, losing arm, source identity, reserve protection or
resource charge must refuse, even with an adopted tranche. ALTERNATIVE: a complete
existing branch can run while unrelated work has an explicit deferred disposition.
Bands: scope-valid discovery tranche or refusal. No training-factorial, seed,
confirmation, full-generation or full-stage claim is licensed by this amendment.
Scientific meaning and compatibility remain explicit, evidence-bound operator reviews.
"""
from copy import deepcopy
from pathlib import Path

from .common import REPO, ROOT, digest, file_hash, read

POLICY = 'stage9-execution-recovery-20260910-v1'
CLAIM_SCOPES = {'instrument_validation', 'package_specific_discovery', 'exposed_corpus_discovery'}
DEFER_REASONS = {'budget', 'instrument_failure', 'unavailable_data', 'unselected_prerequisite'}
UNSELECTABLE = {'training_jobs', 'recipe_selection', 'selected_recipe', 'confirmation_freeze',
                'confirmation_summary', 'confirmation_neural', 'confirmation_baselines',
                'confirmation_human', 'confirmation_execution'}
SUPPORTED = {'closure_probe', 'series_jobs', 'package_calibration', 'neural_operations',
             'calibration_check', 'operation_analysis', 'revision_cases', 'revision_predictions',
             'revision_analysis', 'closure_ledger', 'final_packet'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pointer(value):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}, 'scope evidence needs path and hash')
    relative = Path(value['path']); path = REPO / relative
    require(not relative.is_absolute() and '..' not in relative.parts and path.is_file()
            and path.resolve().is_relative_to(REPO) and not path.is_symlink(), 'scope evidence escaped repository')
    require(file_hash(path) == value['sha256'], 'scope evidence changed')
    return path


def scope(plan):
    """Check the selected manifest against the original commissioned job objects."""
    value = plan.get('execution_scope')
    if value is None:
        return None
    from .launch import CARDS
    fields = {'policy', 'adoption', 'original_jobs', 'original_cards', 'selected_jobs',
              'cards', 'permitted_claims', 'manifest_path', 'queue_root', 'review_path',
              'required_split_roles', 'package_kinds', 'source_corpora', 'deferred_jobs'}
    require(isinstance(value, dict) and set(value) == fields and value['policy'] == POLICY,
            'unknown or incomplete adopted tranche policy')
    adoption = read(pointer(value['adoption']))
    require(adoption.get('policy') == POLICY and adoption.get('adopted') is True
            and adoption.get('authority') == 'curator' and adoption.get('adopted_at')
            and adoption.get('gpu_cap_hours') == 92 and adoption.get('horizon_extended') is False,
            'tranche needs explicit adoption without budget or horizon extension')
    pointer(adoption['addendum'])
    require(plan['campaign_start'] == adoption['campaign_start'] and plan['horizon_epoch'] == adoption['horizon_epoch'],
            'tranche cannot reset campaign clock')
    original = read(pointer(value['original_jobs'])); roster = read(pointer(value['original_cards']))
    require(isinstance(original, list) and isinstance(roster, dict) and set(roster) <= CARDS,
            'original commissioned inventory required')
    by_id = {j['id']: j for j in original}; selected = [j['id'] for j in plan['jobs']]
    require(len(by_id) == len(original) and selected == value['selected_jobs']
            and selected == [j['id'] for j in original if j['id'] in set(selected)],
            'tranche must retain original distinct job identities and order')
    require(value['deferred_jobs'] == [j['id'] for j in original if j['id'] not in set(selected)],
            'every excluded job needs a deferred disposition')
    require(isinstance(value['cards'], dict) and set(value['cards']) == CARDS, 'scope ledger must retain all 42 cards')
    for card, row in value['cards'].items():
        require(isinstance(row, dict) and set(row) == {'selected', 'deferred', 'status', 'reason', 'deferral_kind'},
                'card needs separate selected and deferred coverage')
        old = roster.get(card, [])
        require(row['selected'] == [k for k in old if k in selected]
                and row['deferred'] == [k for k in old if k not in selected], 'card coverage changes original assignments')
        expected = 'partial' if row['selected'] and row['deferred'] else 'selected' if row['selected'] else 'deferred'
        if not old and row['status'] == 'preparation':
            expected = 'preparation'
        require(row['status'] == expected and isinstance(row['reason'], str) and row['reason'].strip(),
                'deferral is not failure, completion or counterevidence')
        require(row['deferral_kind'] in DEFER_REASONS if row['deferred'] or expected == 'deferred'
                else row['deferral_kind'] is None, 'deferred work needs its actual reason class')
    required_preparations = {'I01', 'I05'} | ({'I02'} if value['source_corpora'] else set())
    require(all(value['cards'][c]['status'] == 'preparation' for c in required_preparations),
            'selected source, inherited-failure and borrowed-operation preparation cannot be deferred')
    for job in plan['jobs']:
        module = job['module'].split('.')[-1]
        require(module not in UNSELECTABLE and not module.startswith('confirmation_'),
                'recovery tranche excludes training, recipe selection and confirmation consumers')
        require(module in SUPPORTED, 'operation is outside this bounded recovery implementation')
        if module == 'neural_operations':
            args = job['arguments']
            require('--operation' in args and args[args.index('--operation') + 1] == 'supplied_kernel',
                    'only the complete supplied-information operation is reviewed for recovery')
        require('--training' not in job['arguments'] and '--selection' not in job['arguments']
                or module == 'revision_analysis', 'partial recipe grid cannot supply selected fits')
        expected = deepcopy(by_id[job['id']]); expected['estimated_gpu_seconds'] = job['estimated_gpu_seconds']
        if module in ('closure_ledger', 'final_packet'):
            expected['after'] = [k for k in expected['after'] if k in selected]
        args = expected['arguments']
        for flag, key in (('--manifest', 'manifest_path'), ('--queue', 'queue_root'), ('--review', 'review_path')):
            if flag in args:
                require(args.count(flag) == 1, 'ambiguous operational path')
                args[args.index(flag) + 1] = value[key]
        require(job == expected, 'selected scientific settings, arms or prerequisites changed: ' + job['id'])
        require(set(job['after']) <= set(selected) and all(r['job'] in selected for r in job['requires']),
                'selected job has a deferred prerequisite')
    claims = value['permitted_claims']
    require(isinstance(claims, dict) and claims, 'tranche needs an explicit permitted-claim ceiling')
    for name, claim in claims.items():
        require(isinstance(name, str) and name and isinstance(claim, dict)
                and set(claim) == {'scope', 'ceiling', 'jobs'} and claim['scope'] in CLAIM_SCOPES
                and isinstance(claim['ceiling'], str) and claim['ceiling'].strip()
                and claim['jobs'] and set(claim['jobs']) <= set(selected), 'invalid tranche claim ceiling')
    require(value['required_split_roles'] and set(value['required_split_roles']) <=
            {'training', 'pilot', 'development', 'discovery', 'reserve'}, 'explicit applicable split roles required')
    require(isinstance(value['package_kinds'], dict)
            and all(f in ('qwen', 'smollm') and kinds and set(kinds) <= {'base', 'archive'}
                    for f, kinds in value['package_kinds'].items()), 'only existing eligible reader packages supported')
    require(isinstance(value['source_corpora'], list) and len(value['source_corpora']) == len(set(value['source_corpora'])),
            'distinct applicable corpus roster required')
    require(set(value['source_corpora']) == ({'argrewrite'} if any(j['module'].endswith('.revision_cases')
            for j in plan['jobs']) else set()), 'selected corpus inventory omits its actual loader')
    actual_packages = {}
    for job in plan['jobs']:
        args = job['arguments']
        if '--family' in args:
            family = args[args.index('--family') + 1]
            require('--package-kind' in args, 'selected reader must name its actual existing package')
            kind = args[args.index('--package-kind') + 1]
            actual_packages.setdefault(family, set()).add(kind)
    require(actual_packages == {k: set(v) for k, v in value['package_kinds'].items()},
            'reader inventory differs from actual selected invocations')
    return value


def compatibility(old_sources, current_sources, review):
    """Unchanged dependencies reuse their receipts; each changed file needs a review."""
    require(isinstance(review, dict) and set(review) == {'changes', 'checks', 'basis'},
            'rehearsal compatibility needs exact source changes and relevant checks')
    changed = {k: {'old': v, 'current': current_sources['files'].get(k)}
               for k, v in old_sources['files'].items() if current_sources['files'].get(k) != v}
    require(review['changes'] == changed and all(v['current'] for v in changed.values()),
            'rehearsal source difference not explicitly reviewed')
    require(isinstance(review['basis'], str) and review['basis'].strip(), 'rehearsal operation compatibility has no basis')
    require(isinstance(review['checks'], list) and (not changed or review['checks']),
            'changed rehearsal sources need applicable validation evidence')
    for evidence in review['checks']:
        pointer(evidence)


def rehearsal(plan, value):
    """Verify each actual prior queue commit, with explicit operation/source compatibility."""
    from .launch import checked, handler_operation
    from .queue import verify_committed
    require(set(value) == {'job_mapping'} and set(value['job_mapping']) == {j['id'] for j in plan['jobs']},
            'rehearsal must map every selected job')
    for job in plan['jobs']:
        row = value['job_mapping'][job['id']]
        old = checked(row['plan']); jobs = {j['id']: j for j in old['jobs']}
        require(old['kind'] == 'prelaunch_rehearsal' and row['job'] in jobs
                and handler_operation(job) == handler_operation(jobs[row['job']]),
                'rehearsal substituted operation, partition, family or package')
        queue = (REPO / row['queue_root']).resolve()
        require(queue.is_relative_to(ROOT) and read(queue / 'MANIFEST.json') == old,
                'rehearsal must retain its original queue manifest')
        done = read(queue / 'COMPLETE.json')
        require(done['jobs'][row['job']]['status'] == 'COMPLETE', 'selected handler rehearsal did not complete')
        verify_committed(queue, jobs[row['job']], old, digest(old))
        compatibility(old['sources'], plan['sources'], row['compatibility'])


def packet_claims(review, plan):
    value = scope(plan)
    if value is None:
        return
    require(review.get('scope') == 'scientific_tranche' and review.get('full_stage_complete') is False
            and review.get('execution_scope_sha256') == digest(value), 'tranche packet cannot claim full-stage completion')
    for claim in review['claims']:
        allowed = value['permitted_claims'].get(claim['id'])
        require(allowed and claim['scope'] == allowed['scope'], 'claim exceeds adopted tranche scope')
        require(claim.get('disposition') != 'CONFIRMED WITHIN SCOPE', 'discovery tranche cannot claim confirmation')
        producers = {review['evidence'][key]['job'] for key in claim['evidence']}
        require(set(allowed['jobs']) <= producers, 'claim omits an assigned comparator or failure')


def claim_gates(review, plan, ledger):
    """Scientific interpretation cannot bypass a selected failed instrument."""
    value = scope(plan); jobs = {j['id']: j for j in plan['jobs']}
    for claim in review['claims']:
        for key in value['permitted_claims'][claim['id']]['jobs']:
            valid = ledger['jobs'][key]['status'] == 'COMPLETE'
            if valid and jobs[key]['module'] == 'runners.stage9.calibration_check':
                valid = read(REPO / jobs[key]['produces']).get('instrument_accepted') is True
            require(valid or claim['disposition'] in ('IMPLEMENTATION INVALID', 'NOT RUN WITH REASON'),
                    'claim relies on a failed selected prerequisite or calibration')


def final_integrity(plan, ledger):
    """A scoped packet needs complete current validation of its own observations."""
    value = scope(plan)
    require(value is not None, 'explicit tranche identity required')
    coverage = ledger['coverage_audit']
    require(coverage['status'] == 'RECONCILED' and coverage['execution_scope_sha256'] == digest(value)
            and coverage['all_commissioned_cards_mapped'] and coverage['all_commissioned_attacks_mapped'],
            'tranche coverage does not reconcile')
    for job in ledger['capsule_audits']['jobs'].values():
        if job['status'] != 'INSPECTED':
            continue  # Failed/unrun jobs remain reportable failures, never accepted calls.
        require(not job['storage']['uncached_capsules'] and
                all(call['inspection']['status'] in ('VERIFIED', 'FAILED_RETAINED')
                    and not call['inspection']['missing_execution_outputs'] for call in job['calls']),
                'selected capsule provenance or isolation remains unresolved')
    for job in ledger['resident_service_audits']['jobs'].values():
        require(job['all_recorded_services_reconciled'] is True, 'selected model service provenance remains unresolved')
    require(not ledger.get('historical_service_audits', {}).get('lineages'),
            'recovery tranche does not import unrelated historical service claims')
    return {'scope_sha256': digest(value), 'tranche_integrity_complete': True,
            'full_stage_complete': False, 'scientific_claims_inferred': False}
