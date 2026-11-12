"""Navigation safety tests: preserve evidence and refuse misleading/stale views."""
import copy
import json
from pathlib import Path

import pytest

from tools import record_views as v


def write(root, name, value):
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(v.encode(value) if not isinstance(value, (str, bytes)) else value.encode() if isinstance(value, str) else value)


def read(root, name):
    return json.loads((root / name).read_text())


@pytest.fixture
def repo(tmp_path):
    source = b"# Findings\n\n### A\nPrimary evidence.\n### B\nOperations.\n### C\nUnknown historical result.\n"
    write(tmp_path, "FINDINGS.md", source)
    rows = []
    for ident, n in [("A", 3), ("B", 5), ("C", 7)]:
        write(tmp_path, f"{v.STAGE}/{ident}.md", f"# {ident}\nComplete retained report.\n")
        rows.append(dict(id=ident, card=ident, at="2026-11-11", outcome="infrastructure",
            public_wording=f"Scoped record {ident}", control_status="passes", scope="Retained scope",
            scope_qualifiers={"substrate": "original detail"}, correction_class="scope" if ident == "A" else None,
            supersedes=["historical-A"] if ident == "A" else [], superseded_by=[], detail=f"{ident}.md",
            source=dict(file="FINDINGS.md", line=n, anchor=f"### {ident}", source_sha256=v.digest(source))))
    write(tmp_path, v.LEDGER, {"rows": rows})
    entries = []
    for row in rows[:2]:
        a = row["id"] == "A"
        name = f"{v.STAGE}/{row['id']}.md"
        entries.append(dict(id=row["id"], row_sha256=v.semantic(row), source_locator={k:row['source'][k] for k in ('file','anchor')}, review_state="reviewed",
            reason="Read the full retained source", record_kind="run", purpose="calibration" if a else "operations",
            population="mixed" if a else "not_applicable", readout="exact program",
            evidence_validity="limited" if a else "valid", by_construction=False if a else "unreviewed",
            construction_reason="Measured, not guaranteed" if a else None, theory_tags=["gate"], theory_ids=[],
            sources=[dict(file=name, sha256=v.digest((tmp_path/name).read_bytes()))]))
    write(tmp_path, f"{v.SHELF}/ANNOTATIONS.json", dict(schema_version=1, entries=entries))
    claims = [dict(id=c, family="same family", statement=c, standing="existing limited standing",
        scope="conditional design", standing_source="A", standing_quote="Scoped record A",
        last_standing_change=None, reviewed_at="2026-11-11") for c in ["C1", "C2"]]
    links = [dict(claim_id=c, evidence_id="A", bearing=b, scope=c, reason="Different scoped claim", basis=True)
             for c, b in [("C1", "supports"), ("C2", "against")]]
    write(tmp_path, f"{v.SHELF}/CLAIM_REGISTER.json", dict(schema_version=1, claims=claims, links=links))
    write(tmp_path, f"{v.SHELF}/CONFIG.json", dict(schema_version=1, theory_files=[], queries=[dict(
        name="mixed", question="Mixed calibration?", filters={"population": "mixed"}, expected_ids=["A"], limit="Bounded only")]))
    write(tmp_path, f"{v.SHELF}/MIGRATION_INVENTORY.json", dict(records=[dict(id=r["id"]) for r in rows]))
    write(tmp_path, f"{v.SHELF}/README.md", "# Test contract\n")
    write(tmp_path, f"{v.SHELF}/REVIEW_QUEUE.md", "# Bounded review\n")
    write(tmp_path, "tools/record_views.py", Path(v.__file__).read_bytes())
    return tmp_path


def test_deterministic_additive_generation_and_complete_id_coverage(repo):
    before = {p.relative_to(repo): p.read_bytes() for p in repo.rglob('*') if p.is_file()}
    counts = v.run(repo, "build")
    first = (repo / f"{v.SHELF}/MANIFEST.json").read_bytes()
    assert counts["records"] == 3 and counts["unreviewed"] == 1
    v.run(repo, "build")
    assert (repo / f"{v.SHELF}/MANIFEST.json").read_bytes() == first
    assert all((repo / p).read_bytes() == data for p, data in before.items())
    assert v.run(repo, "check") == counts
    assert len((repo / "docs/START_HERE_FOR_AGENTS.md").read_text().splitlines()) < 300


def test_mixed_calibration_is_science_and_unknown_is_not_false(repo):
    _, records, register, _, _ = v.load(repo)
    a, b, c = records
    assert a["annotation"]["population"] == "mixed"
    assert a["annotation"]["by_construction"] is False
    assert b["annotation"]["population"] == "not_applicable"
    assert c["annotation"]["by_construction"] == "unreviewed"
    assert c["annotation"]["population"] == "unknown"
    _, outputs = v.render(repo)
    assert b'[A]' in outputs[f"{v.SHELF}/SCIENCE.md"]
    assert b'[B]' in outputs[f"{v.SHELF}/OPERATIONS.md"]
    assert b'[C]' in outputs[f"{v.SHELF}/UNCLASSIFIED.md"]
    assert a["correction_class"] == "scope" and a["supersedes"] == ["historical-A"]
    assert len(v.query(records, register, {"claim": "C1"})) == 1
    assert len(v.query(records, register, {"claim": "C2"})) == 1
    assert {e["bearing"] for e in register["links"]} == {"supports", "against"}


def test_validity_can_be_withdrawn_without_new_run_or_standing_change(repo):
    path = f"{v.SHELF}/ANNOTATIONS.json"
    annotation = read(repo, path)
    annotation["entries"][0]["evidence_validity"] = "invalid"
    write(repo, path, annotation)
    _, outputs = v.render(repo)
    score = outputs['SCOREBOARD.md'].decode()
    assert "REVIEW REQUIRED" in score and "no positive claim licensed" in score
    assert "existing limited standing" in score


def test_appending_operational_row_cannot_promote_claim(repo):
    _, old = v.render(repo)
    ledger = read(repo, v.LEDGER)
    extra = copy.deepcopy(ledger["rows"][1]);extra["id"] = "B2"
    ledger["rows"].append(extra)
    write(repo, v.LEDGER, ledger)
    _, new = v.render(repo)
    claim_lines = lambda data: [s for s in data.decode().splitlines() if s.startswith("| C")]
    assert claim_lines(old['SCOREBOARD.md']) == claim_lines(new['SCOREBOARD.md'])


@pytest.mark.parametrize("fault", ["duplicate", "missing_source", "bad_anchor", "reviewed_change", "removed_id", "dangling_link", "invented_standing"])
def test_bad_sources_and_identity_fail_closed(repo, fault):
    ledger = read(repo, v.LEDGER)
    if fault == "duplicate":
        ledger["rows"].append(ledger["rows"][0])
    elif fault == "missing_source":
        (repo / "FINDINGS.md").unlink()
    elif fault == "bad_anchor":
        ledger["rows"][0]["source"]["line"] = 4
    elif fault == "reviewed_change":
        ledger["rows"][0]["control_status"] = "invalid"
    elif fault == "removed_id":
        ledger["rows"] = ledger["rows"][:2]
    else:
        name = f"{v.SHELF}/CLAIM_REGISTER.json";reg = read(repo, name)
        if fault == "dangling_link":reg["links"][0]["evidence_id"] = "ABSENT"
        else:reg["claims"][0]["standing_quote"] = "Invented improvement"
        write(repo, name, reg)
    write(repo, v.LEDGER, ledger)
    with pytest.raises(v.Invalid):v.render(repo)


def test_stale_outputs_refused_and_rebuilt(repo):
    v.run(repo, 'build')
    write(repo, 'SCOREBOARD.md', 'Stale or manually edited\n')
    with pytest.raises(v.Invalid, match='Stale/missing'):v.run(repo, 'check')
    v.run(repo, 'build');v.run(repo, 'check')
    (repo/f'{v.SHELF}/SCIENCE.md').unlink()
    with pytest.raises(v.Invalid, match='Stale/missing'):v.run(repo, 'check')


def test_changed_review_document_requires_review(repo):
    write(repo, f'{v.STAGE}/A.md', 'Changed report\n')
    with pytest.raises(v.Invalid, match='Review document changed'):v.render(repo)


def test_source_change_during_generation_detected(repo):
    src = v.Sources(repo);src.read('FINDINGS.md')
    write(repo, 'FINDINGS.md', 'Changed concurrently\n')
    with pytest.raises(v.Invalid, match='Concurrent source change'):src.verify_unchanged()


def test_quote_inventory_preserves_exact_text_and_does_not_invent_authority(repo):
    name = 'docs/theory/example.md'
    raw = '# Example dated 2026-01-01\r\n```md\r\n> not a quotation\r\n```\r\n> Exact [repair] — words.\r\n> And uncertainty?\r\n\r\n> Exact [repair] — words.\r\n> And uncertainty?\r\n'
    write(repo, name, raw.encode('utf8'))
    items = v.quotes(v.Sources(repo), [name])
    assert len(items) == 2 and items[0]['id'] != items[1]['id']
    assert items[0]['raw_markdown'] == '> Exact [repair] — words.\r\n> And uncertainty?\r\n'
    assert all(q['source_date'] is None and q['filing_date'] is None and q['status'] == 'unreviewed' and not q['transcript_verified'] for q in items)
    assert items[0]['text_sha256'] == v.digest(items[0]['raw_markdown'].encode())


def test_source_path_cannot_escape_repository(repo):
    with pytest.raises(v.Invalid, match='Outside repository'):
        v.Sources(repo).read('../private.txt')


def test_unknown_filter_and_claim_are_not_silent_empty_answers(repo):
    _, records, register, _, _ = v.load(repo)
    with pytest.raises(v.Invalid, match='Unknown query filter'):
        v.query(records, register, {'populaton': 'people'})
    with pytest.raises(v.Invalid, match='Unknown query claim'):
        v.query(records, register, {'claim': 'absent'})


def test_literal_substrate_does_not_guess_mixed_sources_or_review(repo):
    ledger = read(repo, v.LEDGER)
    row = ledger['rows'][2]
    row['scope_qualifiers']['substrate'] = 'Human typing process records'
    write(repo, v.LEDGER, ledger)
    _, records, _, _, _ = v.load(repo)
    assert records[2]['annotation']['population'] == 'people'
    assert records[2]['annotation']['review_state'] == 'unreviewed'
    row['scope_qualifiers']['substrate'] = 'Constructed outcomes on a human design'
    write(repo, v.LEDGER, ledger)
    _, records, _, _, _ = v.load(repo)
    assert records[2]['annotation']['population'] == 'unknown'


def test_obsolete_output_cannot_silently_remain_current(repo):
    v.run(repo, 'build')
    name = f'{v.SHELF}/MANIFEST.json'
    manifest = read(repo, name)
    manifest['outputs'][f'{v.SHELF}/old-texture.md'] = 'old digest'
    write(repo, name, manifest)
    with pytest.raises(v.Invalid, match='Obsolete generated artifacts'):
        v.run(repo, 'build')


def test_writer_marks_views_pending_until_full_finalization(repo):
    v.run(repo, 'build')
    v.mark_pending(repo, 'new-receipt')
    with pytest.raises(v.Invalid, match='Landing pending'):v.run(repo, 'check')
    v.run(repo, 'build')
    assert not (repo/v.PENDING).exists()
    v.run(repo, 'check')


def test_new_writer_during_build_cannot_clear_its_marker(repo, monkeypatch):
    original = v.Sources.verify_unchanged
    calls = []
    def changing(src):
        original(src)
        calls.append(1)
        if len(calls) == 2:v.mark_pending(repo, 'concurrent-new-landing')
    monkeypatch.setattr(v.Sources, 'verify_unchanged', changing)
    with pytest.raises(v.Invalid, match='Another writer started'):v.run(repo, 'build')
    assert (repo/v.PENDING).exists()


def test_rebinding_reviewed_record_to_other_valid_heading_requires_review(repo):
    ledger = read(repo, v.LEDGER)
    ledger['rows'][0]['source'] = copy.deepcopy(ledger['rows'][1]['source'])
    write(repo, v.LEDGER, ledger)
    with pytest.raises(v.Invalid, match='source locator changed'):v.render(repo)


def test_all_legacy_fields_survive_projection(repo):
    _, records, _, _, _ = v.load(repo)
    original = read(repo, v.LEDGER)['rows']
    for row in original:
        projected = next(r for r in records if r['id'] == row['id'])
        assert all(projected[k] == value for k, value in row.items())
