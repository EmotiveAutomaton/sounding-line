"""Narrow branch/design binding checks; no source/statistical/native execution."""
import pytest
from runners.drive.cards import week5_qualification_driver_v2 as driver


@pytest.mark.parametrize('card,names', [
    ('IN3.ic', ('IN.md', 'IN-followups.md', 'IN-sensitivity-qualification.md')),
    ('IN4.ic', ('IN.md', 'IN-followups.md', 'IN-sensitivity-qualification.md')),
    ('SP3.ic', ('SP.md', 'SP-companion-addendum.md', 'SP3-ic.md')),
    ('MD3.s', ('MD1-3.md', 'MD3.s.md', 'MD3-followup-implementation.md')),
    ('MD3.m', ('MD1-3.md', 'MD3.m.md', 'MD3-followup-implementation.md')),
    ('MD3.p', ('MD1-3.md', 'MD3.p.md', 'MD3-followup-implementation.md')),
])
def test_exact_branch_design_bindings(card, names):
    paths = driver.branch_designs(card)
    assert tuple(path.name for path in paths) == names
    assert all(path.parent == driver.REPO / 'docs/design/stage-15/week5' for path in paths)
    assert all(path.is_file() for path in paths)


def test_other_committed_note_cannot_replace_staging_design():
    module = driver.SPECS['IN3.ic'][3]
    wrong_design = driver.REPO / 'docs/design/stage-15/week5/IN.md'
    receipt = dict(
        reviewed=True, attempt='constructed-refusal-only', card='IN3.ic', operation='qualification',
        module=module, module_sha256=driver.filehash(driver.REPO / (module.replace('.', '/') + '.py')),
        inputs={}, input_sha256={}, config={}, design=str(wrong_design),
        design_sha256=driver.filehash(wrong_design), design_commit='constructed-no-launch',
        evidence=[], expected_terminal='PAUSED', expected_operation='execute', cpu_seconds=1,
        wall_seconds=60, ram_GiB=1, card_charged_cpu_seconds=0, family_charged_cpu_seconds=0,
        cost_evidence=[], resume=None,
    )
    with pytest.raises(ValueError, match='staging design'):
        driver.check_admission(receipt)
