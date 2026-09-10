"""Coverage omissions, failed cells and completed not-run handlers stay distinct."""
import copy
from pathlib import Path

import pytest

from runners.stage9 import closure_coverage as subject, common, launch, queue as queue_module
from runners.stage9.common import closure, digest, file_hash, read, write


def fixture(tmp_path, monkeypatch, science=False):
    for module in (subject, common, launch, queue_module): monkeypatch.setattr(module, 'REPO', tmp_path)
    monkeypatch.setattr(subject, 'verify_committed', lambda *a: None)
    jobs = [{'id': key, 'module': 'runners.stage9.rehearsal_job', 'role': 'work',
             'arguments': [], 'produces': key + '/COMPLETE.json'} for key in ('work', 'failed', 'unrun')]
    jobs += [{'id': 'audit', 'module': subject.AUDIT, 'role': 'closure'},
             {'id': 'packet', 'module': subject.PACKET, 'role': 'closure'}]
    cards = {'I01': ['work', 'failed', 'unrun'], 'B03': ['audit'], 'B04': ['packet']}
    attacks = {'X12': {'jobs': ['work', 'failed', 'unrun'], 'null_expected': 'lost counts refuse',
                       'alternative_expected': 'original failed work remains counted', 'not_applicable_reason': None}}
    if science:
        cards.update({c: ['work'] for c in subject.CARDS - set(cards)})
        attacks.update({a: {'jobs': [], 'null_expected': 'bounded fixture', 'alternative_expected': 'bounded fixture',
                           'not_applicable_reason': 'No applicable condition in this unit fixture.'}
                        for a in subject.ATTACKS - set(attacks)})
    plan = {'kind': 'science' if science else 'prelaunch_rehearsal', 'jobs': jobs,
            'sources': {'files': {}, 'sha256': digest({})},
            'final_coverage': {'version': 1, 'cards': cards, 'attacks': attacks}}
    queue = tmp_path / 'queue'
    write(tmp_path / 'work/COMPLETE.json', {'execution_complete': True, 'accepted': False})
    states = {'work': {'status': 'COMPLETE'}, 'audit': {'status': 'RUNNING'}, 'packet': {'status': 'PENDING'}}
    def seal():
        for key, status in [('failed', 'FAILED'), ('unrun', 'NOT_RUN')]:
            value = {'status': status, 'cell_identity': digest({'manifest_sha256': digest(plan), 'job': jobs[1 if key == 'failed' else 2]}),
                     'reason': 'Original fixture condition', 'disposition': 'IMPLEMENTATION INVALID' if key == 'failed' else 'NOT RUN WITH REASON'}
            path = queue / 'dispositions' / (key + '.json'); write(path, value)
            states[key] = {'status': status, 'reason': value['reason'], 'disposition_path': 'dispositions/' + key + '.json',
                           'disposition_sha256': file_hash(path)}
            if key == 'unrun':
                write(tmp_path / jobs[2]['produces'], value)
                states[key]['produce_sha256'] = file_hash(tmp_path / jobs[2]['produces'])
        write(queue / 'MANIFEST.json', plan)
        write(queue / 'STATUS.json', {'manifest_sha256': digest(plan), 'jobs': states})
    seal()
    return plan, queue, {j['id']: j for j in jobs[:3]}, states, seal


def test_every_actual_cell_retains_its_own_status_without_inflating_closure_counts(tmp_path, monkeypatch):
    plan, queue, prior, *_ = fixture(tmp_path, monkeypatch, science=True)
    before = closure([tmp_path]); result = subject.inspect(plan, queue, prior)
    assert closure([tmp_path]) == before
    assert result['scheduled_cells'] == 5 and result['terminal_cells'] == 3
    assert result['cards']['I01']['terminal_counts'] == {'COMPLETE': 1, 'FAILED': 1, 'NOT_RUN': 1}
    assert result['cards']['B03']['terminal_counts'] == {} and result['cards']['B04']['closure_tail'] == ['packet']
    assert result['cards']['I01']['explicit_not_run_studies'] == 1
    assert result['all_commissioned_cards_mapped'] and result['all_commissioned_attacks_mapped']
    assert result['attacks']['X12']['accounting']['terminal_counts']['FAILED'] == 1
    assert not result['scientific_outcomes_inferred'] and not result['scientific_admission']


@pytest.mark.parametrize('fault', ['missing_map', 'missing_card', 'unknown_card', 'duplicate_job', 'unmapped_job',
    'unknown_job', 'tail_substitution', 'missing_attack', 'unknown_attack', 'tail_attack', 'empty_attack',
    'contradictory_applicability', 'missing_expectation', 'wrong_version', 'extra_audit', 'late_work'])
def test_missing_or_false_manual_coverage_refuses(tmp_path, monkeypatch, fault):
    plan, *_ = fixture(tmp_path, monkeypatch, science=True)
    review = plan['final_coverage']; cards = review['cards']; attack = review['attacks']['X12']
    if fault == 'missing_map': plan.pop('final_coverage')
    elif fault == 'missing_card': cards.pop('C05')
    elif fault == 'unknown_card': cards['C99'] = ['work']
    elif fault == 'duplicate_job': cards['I01'].append('work')
    elif fault == 'unmapped_job': cards['I01'].remove('failed')
    elif fault == 'unknown_job': cards['I01'].append('absent')
    elif fault == 'tail_substitution': cards['C05'] = ['audit']
    elif fault == 'missing_attack': review['attacks'].pop('X11')
    elif fault == 'unknown_attack': review['attacks']['X13'] = copy.deepcopy(attack)
    elif fault == 'tail_attack': attack['jobs'] = ['audit']
    elif fault == 'empty_attack': attack['jobs'] = []
    elif fault == 'contradictory_applicability': attack['not_applicable_reason'] = 'does not apply'
    elif fault == 'missing_expectation': attack['alternative_expected'] = ''
    elif fault == 'wrong_version': review['version'] = True
    elif fault == 'extra_audit': plan['jobs'].append({'id': 'again', 'module': subject.AUDIT, 'role': 'closure'})
    elif fault == 'late_work': plan['jobs'][-1]['module'] = 'runners.stage9.training_jobs'
    with pytest.raises(ValueError): subject.validate_mapping(plan)


@pytest.mark.parametrize('fault', ['running_prior', 'missing_prior', 'changed_manifest', 'changed_disposition'])
def test_actual_coverage_refuses_incomplete_or_changed_execution(tmp_path, monkeypatch, fault):
    plan, queue, prior, states, seal = fixture(tmp_path, monkeypatch)
    if fault == 'running_prior': states['work']['status'] = 'RUNNING'; seal()
    elif fault == 'missing_prior': prior.pop('failed')
    elif fault == 'changed_manifest': write(queue / 'MANIFEST.json', {})
    elif fault == 'changed_disposition': write(queue / 'dispositions/failed.json', {})
    with pytest.raises(ValueError): subject.inspect(plan, queue, prior)


def not_run_fixture(tmp_path, monkeypatch):
    from runners.stage9.disposition_jobs import validate_decision
    plan, queue, prior, states, seal = fixture(tmp_path, monkeypatch)
    directory = tmp_path / 'work'; path = tmp_path / 'decision.json'
    evidence = tmp_path / 'evidence.json'; write(evidence, {'original_limit': True})
    decision = {'card': 'T05', 'kind': 'unsupported_measurement', 'scope': 'discarded fixture',
        'reason': 'Independent policy is absent.', 'evidence': {'limit': {'path': 'evidence.json', 'sha256': file_hash(evidence)}},
        'retained_failures': [], 'finding': 'No actual policy contrast can execute.', 'next_obligation': 'Retain unsupported scope.'}
    write(path, decision)
    job = plan['jobs'][0]; job.update(module='runners.stage9.disposition_jobs', arguments=[
        '--output', str(directory), '--decision', str(path), '--card', 'T05', '--scope', 'pilot'])
    plan['final_coverage']['cards']['T05'] = ['work']; seal()
    identity = {'cell_identity': digest({'manifest_sha256': digest(plan), 'job': job}), 'operation': 'not-run-T05',
        'scope': 'pilot', 'source': plan['sources'], 'card': 'T05', 'decision_path': 'decision.json',
        'decision_sha256': file_hash(path), 'evidence': decision['evidence']}
    write(directory / 'IDENTITY.json', identity); write(directory / 'DISPOSITION.json', validate_decision(decision, 'T05'))
    done = {'identity_sha256': digest(identity), 'outputs': closure([directory / 'IDENTITY.json', directory / 'DISPOSITION.json']),
            'scientific_execution': False, 'scored_units': 0}
    write(directory / 'COMPLETE.json', done)
    return plan, queue, prior, directory, identity, done


def test_completed_not_run_handler_does_not_count_as_a_completed_study(tmp_path, monkeypatch):
    plan, queue, prior, *_ = not_run_fixture(tmp_path, monkeypatch)
    result = subject.inspect(plan, queue, prior)['cards']['T05']
    assert result['terminal_counts'] == {'COMPLETE': 1} and result['explicit_not_run_studies'] == 1
    assert result['jobs']['work']['study_disposition'] == 'NOT RUN WITH REASON'


@pytest.mark.parametrize('fault', ['promoted_execution', 'changed_decision', 'changed_evidence', 'changed_source', 'missing_committed_disposition'])
def test_rehashed_not_run_promotion_or_lineage_change_refuses(tmp_path, monkeypatch, fault):
    plan, queue, prior, directory, identity, done = not_run_fixture(tmp_path, monkeypatch)
    if fault == 'promoted_execution': done['scientific_execution'] = True
    elif fault == 'changed_decision': write(tmp_path / 'decision.json', {})
    elif fault == 'changed_evidence': write(tmp_path / 'evidence.json', {'original_limit': False})
    elif fault == 'changed_source':
        identity['source'] = {}; write(directory / 'IDENTITY.json', identity); done['identity_sha256'] = digest(identity)
        done['outputs'] = closure([directory / 'IDENTITY.json', directory / 'DISPOSITION.json'])
    elif fault == 'missing_committed_disposition': done['outputs'] = closure([directory / 'IDENTITY.json'])
    write(directory / 'COMPLETE.json', done)
    with pytest.raises(ValueError): subject.inspect(plan, queue, prior)


def test_older_component_pilot_reports_unconfigured_coverage_without_reading_outputs():
    assert subject.inspect({'kind': 'prelaunch_rehearsal'}, Path('unused'), {})['status'] == 'NOT_CONFIGURED'
