"""A failed evidence-view check leaves a study open for a clean retry."""
import pytest

from runners.stage14.common import atomic, read
from tools import week8_filing as filing


def test_failed_view_check_keeps_return_pending(tmp_path, monkeypatch):
    stage = tmp_path / 'results/phase_2_4_stage_15'
    public = stage / 'WEEK8'
    state = tmp_path / '.agent-state/week8'
    for key, path in dict(ROOT=tmp_path, STAGE=stage, PUBLIC=public, STATE=state).items():
        monkeypatch.setattr(filing, key, path)
    filing.write(tmp_path/'docs/theory/THREE_COGNITIVE_LAYERS.md', '# Fixture theory\n')
    filing.write(tmp_path/'docs/TOOLS.md', '# Tools\n\n## The instrument ledger\n')
    filing.write(tmp_path/'results/EVIDENCE_LEDGER.jsonl', '')
    atomic(stage/'CLAIM_LEDGER.json', {'rows': []})
    atomic(state/'dispositions.json', {'ADM2': {'status': 'running'}})
    coverage = tmp_path/'.agent-state/work-coverage.json'
    atomic(coverage, {'work': [{'card': 'ADM2', 'state': 'running'}]})
    result = dict(
        id='OPS-ADM2-FIXTURE', date='2026-11-27', question='Are the source headers consistent?',
        data='Constructed source header.', estimate=None, interval=None, bar='Exact replay',
        verdict='One source admitted.', limit='Constructed fixture.', claims=['Source admission'], family='ADM')
    receipt = dict(terminal_at='2026-11-27T18:00:00Z', terminal_sha256='terminal-fixture',
                   bindings={'example': {'status': 'admitted'}}, replay_sha256='replay-fixture',
                   instrument='Original header comparison.', warrant='Two reads agree.', operations='Verified.')
    args = dict(card='ADM2', stem='SOURCES', title='Source binding', body='The fixture source bound.',
                receipt=receipt, evidence=result, theory_anchor=None, theory_note=None, after_anchor=None,
                afterword='The header was read twice.', opposition=None, outcome='source admission',
                rival='Repeated metadata.', scope={'analysis': 'Operational'}, next_step='Use the bound source.',
                return_line='Source admitted.')

    # Both generation and the independent freshness check must succeed.
    monkeypatch.setattr(filing.views, 'run', lambda root, action: {'records': 1 if action == 'build' else 0})
    with pytest.raises(ValueError, match='Generated view validation differs'):
        filing.land(**args)
    assert not (public/'SOURCES.json').exists()
    assert read(state/'dispositions.json')['ADM2']['status'] == 'running'
    assert read(coverage)['work'][0]['state'] == 'running'

    monkeypatch.setattr(filing.views, 'run', lambda root, action: {'records': 1})
    filing.land(**args)
    assert read(public/'SOURCES.json')['local_write_through']
    assert not read(public/'SOURCES.json')['full_write_through']
    disposition = read(state/'dispositions.json')['ADM2']
    assert disposition['status'] == 'awaiting report'
    assert disposition['pending_r48_receipt'] == 'SOURCES'
    assert read(coverage)['work'][0]['state'] == 'build'
    assert len(read(stage/'CLAIM_LEDGER.json')['rows']) == 1
    assert len((tmp_path/'results/EVIDENCE_LEDGER.jsonl').read_text().splitlines()) == 1
