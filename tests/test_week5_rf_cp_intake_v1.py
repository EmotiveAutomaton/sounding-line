"""Constructed-only intake tests; exact hand answers, no public source reads."""
import gzip
import json
import pytest
from runners.drive.cards import week5_rf_cp_markers_v1 as m
from runners.drive.cards import week5_rf_cp_source_v1 as s
from runners.drive.cards import week5_rf_cp_fixture_v1 as f
from runners.drive.cards import week5_rf_cp_instrument_v1 as gate


def config(root, family, repeat=1):
    archive, salt, n = f.prepare(root, family, repeat)
    return {'archive': str(archive), 'identity_salt': str(salt)}, {
        'family': family, 'constructed_fixture': True,
        'fixture_archive_sha256': s.sha(archive), 'fixture_expected_records': n}


def test_rf_twelve_literal_hand_answers():
    for text, expected in f.RF_CASES:
        got = m.rf_counts(text)['counts']
        assert tuple(got[k][polarity] for k in m.RF for polarity in ('for','against')) == expected


def test_cp_ten_pairs_literal_hand_answers():
    for pair in f.CP_PAIRS:
        for text, tokens, expected in pair:
            got = m.cp_counts(text)
            assert got['tokens'] == tokens
            assert tuple(got['counts'][k] for k in m.CP) == expected
            assert tuple(got['per_100_tokens'][k] for k in m.CP) == tuple(100*v/tokens for v in expected)


def test_lexical_boundaries_do_not_claim_semantics():
    assert m.rf_counts('Untrustworthy and unfriendly.')['counts']['trust'] == {'for':0, 'against':1}
    assert m.rf_counts('Not competent.')['counts']['respect']['for'] == 1
    assert m.cp_counts('Thanksful perhapsness clearlyish.')['counts'] == dict(warmth=0,deference=0,assertion=0)
    assert m.cp_counts(': Thanks.\n* Please.')['counts'] == dict(warmth=1,deference=1,assertion=0)


@pytest.mark.parametrize('family', ['RF1','CP1'])
def test_complete_actual_source_handler_reentry_and_replay(tmp_path, family):
    inputs, cfg = config(tmp_path/'source', family)
    out = tmp_path/'run'; result = s.execute(out, inputs, cfg)
    assert result['records'] == (12 if family == 'RF1' else 20)
    assert result['source_gate'] is True and result['scientific_admission'] is False
    if family == 'RF1':
        assert result['election_identity_qualified'] is False
    first = {p.name: p.read_bytes() for p in out.iterdir() if p.is_file()}
    assert s.execute(out, inputs, cfg) == result
    assert first == {p.name: p.read_bytes() for p in out.iterdir() if p.is_file()}
    assert s.verify(out, inputs, cfg)['verified'] is True
    data = gzip.decompress((out/'block-000000.json.gz').read_bytes())
    assert b'constructed-a' not in data and b'constructed-voter' not in data
    assert b'Experienced' not in data and b'alpha beta' not in data


def test_checkpoint_resume_and_changed_block_refusal(tmp_path):
    inputs, cfg = config(tmp_path/'source', 'RF1', 50)
    out = tmp_path/'run'
    assert s.execute(out, inputs, dict(cfg,max_new_blocks=1))['status'] == 'yielded'
    chunk = out/'block-000000.json.gz'; original = chunk.read_bytes()
    assert s.execute(out, inputs, cfg)['records'] == 600
    assert chunk.read_bytes() == original
    assert s.verify(out, inputs, cfg)['verified'] is True
    row = json.loads(gzip.decompress(original)); row['rows'][0]['vote'] = -1
    chunk.write_bytes(gzip.compress(s.canonical(row),mtime=0))
    with pytest.raises(ValueError, match='Sealed source block changed'):
        s.execute(out, inputs, cfg)


def test_changed_source_and_incomplete_verification_refusal(tmp_path):
    inputs, cfg = config(tmp_path/'source', 'CP1')
    out = tmp_path/'run'; out.mkdir()
    with pytest.raises(ValueError, match='incomplete'):
        s.verify(out, inputs, cfg)
    bad = dict(cfg, fixture_archive_sha256='0'*64)
    with pytest.raises(ValueError, match='pin changed'):
        s.execute(out, inputs, bad)
    (out/'YIELD_REQUEST.json').write_text('{}')
    assert s.execute(out, inputs, cfg)['status'] == 'yielded'


def test_instrument_exact_gates_and_incomplete_review_refusal():
    summary = {'family':'CP1','records':1000,'family_hits':{k:30 for k in m.CP},'source_gate':True,'by_construction':True}
    sample = [{'family':k,'id':str(i)} for k in m.CP for i in range(100)]
    annotations = [dict(x,correct=int(x['id'])<80) for x in sample]
    assert m.instrument_gate(summary,sample,annotations)['admitted'] is True
    annotations[79]['correct'] = False
    assert m.instrument_gate(summary,sample,annotations)['admitted'] is False
    with pytest.raises(ValueError, match='incomplete'):
        m.instrument_gate(summary,sample,annotations[:-1])
    with pytest.raises(ValueError, match='Duplicate'):
        m.instrument_gate(summary,sample,annotations+[annotations[0]])
    annotations[79]['correct'] = True
    summary['family_hits']['warmth'] = 29
    assert m.instrument_gate(summary,sample,annotations)['admitted'] is False


def test_changed_summary_refused_by_complete_replay(tmp_path):
    inputs, cfg = config(tmp_path/'source','RF1'); out=tmp_path/'run'
    s.execute(out,inputs,cfg)
    summary=json.loads((out/'SUMMARY.json').read_text('utf8'))
    summary['family_hits']['respect'] += 1
    (out/'SUMMARY.json').write_text(json.dumps(summary))
    with pytest.raises(ValueError,match='receipt differs'):
        s.verify(out,inputs,cfg)


def test_complete_manual_gate_handler_and_provenance_refusal(tmp_path):
    inputs,cfg=config(tmp_path/'source','CP1',60); out=tmp_path/'source-run'
    s.execute(out,inputs,cfg); s.verify(out,inputs,cfg)
    gin,gcfg=f.constructed_native_receipt(tmp_path/'constructed-native',out)
    result=gate.execute(tmp_path/'gate',gin,gcfg)
    assert result['admitted'] is True and result['scientific_admission'] is False
    assert gate.verify(tmp_path/'gate',gin,gcfg)['verified'] is True
    with pytest.raises(ValueError,match='annotations changed'):
        gate.execute(tmp_path/'wrong-annotation',gin,dict(gcfg,annotations_sha256='0'*64))
    with pytest.raises(ValueError,match='Constructed versus human'):
        gate.execute(tmp_path/'wrong-scope',gin,dict(gcfg,constructed_fixture=False))
