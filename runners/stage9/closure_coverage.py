"""B03 component: reconcile the manual card/attack map with actual terminal jobs.

DESIGN CHECK: B03/B04/X11/X12; LESSONS 3--5, CONTROLS 6--7.
NULL: omitted cells, duplicate assignments, false terminal states, changed not-run
evidence or counting the active closure tail as finished refuse reconciliation.
ALTERNATIVE: every scheduled cell has its reviewed place and actual disposition;
failed and unrun branches stay in every applicable denominator. Constructed
omissions must refuse; complete mappings must retain failures without promoting
them. Bands: reconciled accounting or explicit refusal. Counts do not determine
scientific outcomes, attack success, public claims or complete B03 acceptance.
Preparation evidence has separate reviewed requirements and byte identities. An
unresolved requirement refuses scientific launch; rehearsal may retain the gap.
Evidence checks do not execute studies or independently certify review meaning.
"""
from .live_status import read as read_status
from collections import Counter
from pathlib import Path

from .common import REPO, closure, digest, file_hash, read
from .launch import CARDS
from .queue import verify_committed, verify_disposition

ATTACKS = {f'X{i:02d}' for i in range(1, 13)}
AUDIT = 'runners.stage9.closure_ledger'
PACKET = 'runners.stage9.final_packet'

# These are the preparation obligations in brief sections 3--6, not new study
# assignments. Each requires a source-bound manual review of the actual evidence.
PREPARATION_REQUIREMENTS = {
    'I01': {'campaign_and_current_state', 'source_identities', 'inherited_failures', 'dependency_scope'},
    'I02': {'checkout_and_access_inventory', 'schema_and_count_reconciliation',
            'loader_and_baseline_dispositions', 'workload_and_split_binding'},
    'I04': {'population_and_individual_predictors', 'no_individuality_and_noise',
            'predictable_signatures_and_equifinality', 'attribution_scope_and_lineage'},
    'I05': {'borrowed_component_register', 'defining_operations_and_exact_fixtures',
            'disabled_operation_rivals_and_consumers', 'reproduction_and_adaptation_limits'},
}


def preparation_evidence(plan, card, row):
    """Check pinned review inputs opaquely; never parse unused corpus payloads."""
    if (card not in PREPARATION_REQUIREMENTS or not isinstance(row, dict)
            or set(row) != {'source_sha256', 'jobs_sha256', 'requirements', 'limitations'}
            or row['source_sha256'] != plan['sources']['sha256']
            or row['jobs_sha256'] != digest(plan['jobs'])
            or not isinstance(row['limitations'], str) or not row['limitations'].strip()):
        raise ValueError('preparation review must bind its card, source, jobs and limits')
    requirements = row['requirements']
    if not isinstance(requirements, dict) or set(requirements) != PREPARATION_REQUIREMENTS[card]:
        raise ValueError('preparation review omits a required obligation')
    produced = {(REPO / j['produces']).resolve() for j in plan['jobs'] if 'produces' in j}
    verified = []; unresolved = []; evidence = {}
    for name, value in sorted(requirements.items()):
        if (not isinstance(value, dict) or set(value) != {'status', 'basis', 'evidence'}
                or value['status'] not in ('verified', 'unresolved')
                or not isinstance(value['basis'], str) or not value['basis'].strip()
                or not isinstance(value['evidence'], list)
                or value['status'] == 'verified' and not value['evidence']):
            raise ValueError('preparation obligation needs a scoped review and actual evidence')
        seen = set()
        for pointer in value['evidence']:
            if (not isinstance(pointer, dict) or set(pointer) != {'path', 'sha256'}
                    or not isinstance(pointer['path'], str) or not pointer['path']
                    or not isinstance(pointer['sha256'], str) or len(pointer['sha256']) != 64
                    or any(c not in '0123456789abcdef' for c in pointer['sha256'])):
                raise ValueError('preparation evidence needs an explicit path and checksum')
            relative = Path(pointer['path'])
            path = REPO / relative
            if (relative.is_absolute() or '..' in relative.parts
                    or not path.resolve().is_relative_to(REPO)
                    or any(p.is_symlink() or p.is_junction() for p in (path, *path.parents) if p != REPO and p.is_relative_to(REPO))
                    or not path.is_file() or path.resolve() in produced):
                raise ValueError('preparation evidence must be a prior regular repository file')
            key = path.resolve().relative_to(REPO).as_posix()
            if key in seen or file_hash(path) != pointer['sha256']:
                raise ValueError('preparation evidence duplicated or changed')
            seen.add(key); evidence[key] = pointer['sha256']
        (verified if value['status'] == 'verified' else unresolved).append(name)
    if unresolved and plan['kind'] == 'science':
        raise ValueError('scientific preparation remains unresolved: ' + card + ': ' + ', '.join(unresolved))
    return {'review_sha256': digest(row), 'verified_requirements': verified,
            'unresolved_requirements': unresolved, 'evidence': {'files': evidence, 'sha256': digest(evidence)},
            'limitations': row['limitations'], 'scientific_execution': False,
            'scope': 'source-bound manual preparation review; byte verification does not certify scientific meaning'}


def names(value, allowed, *, empty=False):
    if (not isinstance(value, list) or not empty and not value
            or any(not isinstance(v, str) for v in value)
            or len(value) != len(set(value)) or not set(value) <= set(allowed)):
        raise ValueError('coverage needs distinct explicitly scheduled job names')
    return value


def validate_mapping(plan):
    """Validate the original plan at launch and again at final inspection."""
    review = plan.get('final_coverage')
    from .tranche import scope as tranche_scope
    tranche = tranche_scope(plan)
    if review is None and plan['kind'] == 'prelaunch_rehearsal':
        return None  # Retained older component rehearsals did not exercise coverage.
    if (not isinstance(review, dict) or type(review.get('version')) is not int
            or review['version'] not in (1, 2)
            or set(review) != ({'version', 'cards', 'attacks'} |
                               ({'preparations'} if review['version'] == 2 else set()))):
        raise ValueError('original manifest needs an explicit final coverage map')
    cards, attacks = review['cards'], review['attacks']
    if (not isinstance(cards, dict) or not cards or not set(cards) <= CARDS
            or not isinstance(attacks, dict) or not set(attacks) <= ATTACKS):
        raise ValueError('unknown or empty commissioned coverage inventory')
    if plan['kind'] == 'science' and (set(cards) != CARDS or set(attacks) != ATTACKS):
        raise ValueError('scientific coverage must retain all 42 cards and 12 attacks')
    jobs = {j['id']: j for j in plan['jobs']}
    if len(jobs) != len(plan['jobs']):
        raise ValueError('duplicate scheduled cell identity')
    preparations = review.get('preparations', {})
    if (not isinstance(preparations, dict) or not set(preparations) <= set(cards)
            or not set(preparations) <= set(PREPARATION_REQUIREMENTS)
            or review['version'] == 2 and not preparations):
        raise ValueError('preparation coverage needs explicitly reviewed preparation cards')
    for card, row in preparations.items():
        preparation_evidence(plan, card, row)
    if tranche:
        if set(preparations) != {c for c, r in tranche['cards'].items() if r['status'] == 'preparation'}:
            raise ValueError('tranche preparation obligations differ from adopted scope')
        if any(keys != tranche['cards'][card]['selected'] for card, keys in cards.items()):
            raise ValueError('coverage differs from selected and deferred card ledger')
    audits = [i for i, j in enumerate(plan['jobs']) if j['module'] == AUDIT]
    if len(audits) != 1:
        raise ValueError('coverage needs one actual final audit')
    index = audits[0]; prior = {j['id'] for j in plan['jobs'][:index]}
    tail = plan['jobs'][index:]
    if any(j['role'] != 'closure' or j['module'] != PACKET for j in tail[1:]):
        raise ValueError('only the final packet may follow the audit')
    mapped = set()
    for card, keys in cards.items():
        mapped.update(names(keys, jobs, empty=card in preparations or
                            bool(tranche and tranche['cards'][card]['status'] == 'deferred')))
        for key in set(keys) - prior:
            expected = 'B03' if jobs[key]['module'] == AUDIT else 'B04'
            if card != expected:
                raise ValueError('closure tail cannot stand in for an unfinished study')
    if mapped != set(jobs):
        raise ValueError('card map omits a scheduled cell')
    if plan['kind'] == 'science' and (len(tail) != 2 or cards['B04'] != [tail[1]['id']]):
        raise ValueError('scientific closure requires its separately accounted final packet')
    for row in attacks.values():
        if not isinstance(row, dict) or set(row) != {'jobs', 'null_expected', 'alternative_expected', 'not_applicable_reason'}:
            raise ValueError('attack needs its complete reviewed applicability contract')
        names(row['jobs'], prior, empty=True)
        if any(not isinstance(row[k], str) or not row[k].strip() for k in ('null_expected', 'alternative_expected')):
            raise ValueError('attack requires both expected responses')
        reason = row['not_applicable_reason']
        if row['jobs'] and reason is not None or not row['jobs'] and (not isinstance(reason, str) or not reason.strip()):
            raise ValueError('attack needs actual assigned jobs or an explicit nonapplicability reason')
    return review


def inspect(plan, queue_path, prior):
    review = validate_mapping(plan)
    if review is None:
        return {'status': 'NOT_CONFIGURED', 'reason': 'historical component rehearsal', 'scientific_admission': False}
    state = read_status(queue_path / 'STATUS.json'); jobs = {j['id']: j for j in plan['jobs']}
    index = next(i for i, j in enumerate(plan['jobs']) if j['module'] == AUDIT)
    expected = {j['id']: j for j in plan['jobs'][:index]}
    if (prior != expected or read(queue_path / 'MANIFEST.json') != plan
            or state['manifest_sha256'] != digest(plan) or set(state['jobs']) != set(jobs)):
        raise ValueError('coverage differs from the complete original queue')
    rows = {}
    for key, job in prior.items():
        status = state['jobs'][key]; kind = status['status']
        if kind not in ('COMPLETE', 'FAILED', 'NOT_RUN'):
            raise ValueError('coverage cannot close on an unfinished prior cell')
        row = {'queue_status': kind, 'study_disposition': None}
        if kind == 'COMPLETE':
            verify_committed(queue_path, job, plan, digest(plan))
            row['produce_sha256'] = file_hash(REPO / job['produces'])
            if job['module'] == 'runners.stage9.disposition_jobs':
                from .confirmation_summary import arguments
                from .disposition_jobs import validate_decision
                directory = (REPO / job['produces']).parent
                identity = read(directory / 'IDENTITY.json'); done = read(directory / 'COMPLETE.json')
                decision_path = (REPO / arguments(job, '--decision')).resolve()
                card = arguments(job, '--card'); decision = read(decision_path)
                value = validate_decision(decision, card)
                expected_identity = {'cell_identity': digest({'manifest_sha256': digest(plan), 'job': job}),
                    'operation': 'not-run-' + card, 'scope': arguments(job, '--scope'), 'source': plan['sources'],
                    'card': card, 'decision_path': str(decision_path.relative_to(REPO)),
                    'decision_sha256': file_hash(decision_path), 'evidence': decision['evidence']}
                if (card not in review['cards'] or key not in review['cards'][card]
                        or identity != expected_identity
                        or directory != Path(arguments(job, '--output')).resolve()
                        or done['identity_sha256'] != digest(identity)
                        or done['outputs'] != closure([REPO / p for p in done['outputs']['files']])
                        or any((p.relative_to(REPO).as_posix() not in done['outputs']['files'])
                               for p in (directory / 'IDENTITY.json', directory / 'DISPOSITION.json'))
                        or read(directory / 'DISPOSITION.json') != value
                        or done.get('scientific_execution') is not False
                        or type(done.get('scored_units')) is not int or done['scored_units'] != 0):
                    raise ValueError('completed disposition handler cannot become scientific execution')
                row.update(study_disposition='NOT RUN WITH REASON', reason=value['reason'],
                           disposition_sha256=file_hash(directory / 'DISPOSITION.json'))
        else:
            verify_disposition(queue_path, job, status)
            value = read(queue_path / status['disposition_path'])
            if value['cell_identity'] != digest({'manifest_sha256': digest(plan), 'job': job}) or value['reason'] != status['reason']:
                raise ValueError('original failed/unrun disposition identity differs')
            row.update(study_disposition=value['disposition'], reason=status['reason'],
                       disposition_sha256=status['disposition_sha256'])
        rows[key] = row
    def counted(keys):
        terminal = {key: rows[key] for key in keys if key in prior}
        return {'jobs': terminal, 'terminal_counts': dict(sorted(Counter(r['queue_status'] for r in terminal.values()).items())),
                'closure_tail': [key for key in keys if key not in prior],
                'explicit_not_run_studies': sum(r['study_disposition'] == 'NOT RUN WITH REASON' for r in terminal.values())}
    result = {'status': 'RECONCILED', 'mapping_sha256': digest(review), 'scheduled_cells': len(jobs),
            'terminal_cells': len(prior), 'closure_tail': [j['id'] for j in plan['jobs'][index:]],
            'cards': {card: counted(keys) | ({'preparation': preparation_evidence(plan, card, review['preparations'][card])}
                      if card in review.get('preparations', {}) else {}) for card, keys in review['cards'].items()},
            'attacks': {key: {**row, 'accounting': counted(row['jobs'])} for key, row in review['attacks'].items()},
            'all_commissioned_cards_mapped': set(review['cards']) == CARDS,
            'all_commissioned_attacks_mapped': set(review['attacks']) == ATTACKS,
            'scientific_outcomes_inferred': False, 'scientific_admission': False,
            'scope': 'manual applicability and actual execution accounting; no attack verdict or public-claim inference'}
    if plan.get('execution_scope'):
        result.update(execution_scope_sha256=digest(plan['execution_scope']),
                      deferred_cards={c: r for c, r in plan['execution_scope']['cards'].items()
                                      if r['status'] in ('deferred', 'partial')},
                      deferred_jobs=plan['execution_scope']['deferred_jobs'], full_stage_complete=False)
    return result
