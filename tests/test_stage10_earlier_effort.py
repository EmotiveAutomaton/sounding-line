"""Known-answer full earlier-draft effort chains; no model service or GPU lock."""
from dataclasses import replace
from unittest.mock import patch
import pytest
from runners.stage10 import human_memory_checks as fixtures
from runners.stage10 import human_effort_checks as callback_checks
from runners.stage10 import human_effort_evaluation_checks as evaluation_checks
from runners.stage10 import earlier_effort_readers as readers, earlier_effort_queue as queue
from runners.stage10 import earlier_effort_evaluation as evaluation
from runners.stage10 import earlier_programs as programs

original_task = fixtures.task

def earlier_task(*args, **kwargs):
    task = original_task(*args, **kwargs)
    evidence = {k: task.evidence[k] for k in ('document', 'suggestions')}
    evidence['earlier_drafts'] = ['Original draft before the current version.']
    return replace(task, evidence_view='earlier-artifacts', evidence=evidence)

def test_full_callbacks_and_supported_policy(tmp_path):
    with patch.object(fixtures, 'task', earlier_task), patch.object(callback_checks, 'queue', queue), patch.object(callback_checks, 'readers', readers):
        result = callback_checks.run(tmp_path/'callbacks')
    assert result['status'] == 'PASS' and result['actual_model_calls'] == 0

def test_full_development_fit_evaluation_replay_and_refusals(tmp_path):
    with patch.object(fixtures, 'task', earlier_task), patch.object(evaluation_checks, 'queue', queue), patch.object(evaluation_checks, 'readers', readers), patch.object(evaluation_checks, 'evaluation', evaluation):
        result = evaluation_checks.run(tmp_path/'evaluation')
    assert result['status'] == 'PASS' and result['actual_model_calls'] == 0

def test_prior_changes_proposal_evidence_but_not_executed_rule():
    task = earlier_task(10, 3)
    changed = replace(task, evidence={**task.evidence, 'earlier_drafts': ['Entirely different earlier draft.']})
    rule = [{'goal_hypothesis': 'fixture', 'program': {'feature': 'draft_words', 'threshold': 6.5, 'below': 'accept', 'otherwise': 'edit'}}]
    assert programs.evaluate(task, rule) == programs.evaluate(changed, rule)
    assert readers.proposal.request_for(task) != readers.proposal.request_for(changed)
    with pytest.raises(ValueError):
        programs.features(original_task(10, 3))
