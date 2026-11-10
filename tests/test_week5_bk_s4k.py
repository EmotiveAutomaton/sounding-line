import pytest
from runners.drive.cards import week5_bk_s4k_navigation as nav
from runners.drive.cards import week5_bk_s4k_source as source
from runners.drive.cards import week5_bk_s4k_analysis as analysis
from runners.drive.cards.week5_bk_s4k_fixture import Writer, writing_fixture, numeric_rows


def test_text_decoder_keeps_unicode_and_literal_slash_n_distinct():
    assert nav.logged_text('😀\\n\\\\n')=='😀\n\\n'
    with pytest.raises(ValueError):nav.logged_text('\\q')


def test_final_export_removes_one_record_terminator_only():
    assert nav.canonical_final('a \r\r\n\r\r\n')=='a \n'
    with pytest.raises(ValueError):nav.canonical_final('a')


def test_replacement_and_deletion_fail_closed():
    w=Writer();w.add(0,'Paste',3,'Paste','abc')
    with pytest.raises(ValueError):w.add(1,'Backspace',2,'Remove/Cut','z')
    with pytest.raises(ValueError):w.add(1,'x',2,'Replace','a => b => c')


def test_navigation_device_arm_is_not_displacement():
    record=writing_fixture();data=nav.extract(record)
    arrow=[r for r in data['landings'] if r['kind']=='arrow']
    assert len(arrow)==20 and all(r['displacement']==-1 for r in arrow)
    assert data['census']['inside_arrow_run']==20
    assert {r['kind'] for r in data['landings']}=={'click','arrow'}


def test_final_text_corruption_is_retained_failure():
    record=writing_fixture();record['final_text']='wrong\n'
    assert source.project(record)['status']=='reconstruction_failed'


def test_below_floor_runs_pooled_and_empty_is_not_zero():
    one,_=analysis.analyze(numeric_rows()[:1]);empty,_=analysis.analyze([])
    assert one['state']=='below floor, descriptive' and one['estimate']==.4
    assert empty['estimate'] is None and empty['interval'] is None


def test_exact_identical_rates_are_null():
    summary,_=analysis.analyze(numeric_rows('null'),draws=200,permutations=200)
    assert summary['estimate']==0 and summary['state']=='null'


def test_degenerate_nonzero_cluster_effect_blocks_claim():
    rows=numeric_rows()
    for item in rows:item['landings']=rows[0]['landings']
    summary,_=analysis.analyze(rows,draws=200,permutations=200)
    assert summary['estimate']>.3 and not summary['inference_eligible']
