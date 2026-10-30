"""Reference support, invariants and real producer boundary without scores."""
from collections import Counter
from pathlib import Path
import pytest
from runners.stage14.common import read,freeze
from runners.drive.cards.timing_p6 import gzread,gzip_equal
from runners.drive.cards import week3_d5_reference_plans as card


def fixture():
    rows=[]
    for w in range(6):
        for p in range(8):
            support={c:True for c in card.CHANNELS if c!='process'};support['human1024']=False
            rows.append(dict(session=f'w{w}p{p}',writer=f'w{w}',prompt=f'p{p}',timestamp=float(p),model_share=(p%4+.5)/4,
                model_share_missing_reason=None,share_bin=str(p%4),support=support))
    return dict(constructed=True,rows=rows,writer_folds={f'w{w}':w%3 for w in range(6)})


def test_label_draws_preserve_prompt_counts_and_roles():
    f=fixture();rows=f['rows'];folds=f['writer_folds']
    for roles in [False,True]:
        a=card.label_draw(rows,folds,3,20261026,roles)
        assert a==card.label_draw(rows,folds,3,20261026,roles)
        assert any(a[r['session']]!=r['writer'] for r in rows)
        assert Counter((r['prompt'],r['writer']) for r in rows)==Counter((r['prompt'],a[r['session']]) for r in rows)
        if roles:assert all(folds[r['writer']]==folds[a[r['session']]] for r in rows)


def test_share_draw_preserves_each_full_writer_multiset():
    f=fixture();rows=f['rows'];a=card.share_draw(rows,7,20261026)
    assert a==card.share_draw(rows,7,20261026)
    assert Counter((r['writer'],r['share_bin']) for r in rows)==Counter((r['writer'],b) for r,b in zip(rows,a))
    assert any(r['share_bin']!=b for r,b in zip(rows,a))


def test_prompt_halves_and_missing_fixed_candidates():
    f=fixture();rows=f['rows'];roster=sorted(f['writer_folds']);l=card.layout(rows,roster);byid={r['session']:r for r in rows}
    for a,b in l['halves'].values():assert not ({byid[s]['prompt'] for s in a}&{byid[s]['prompt'] for s in b})
    assert l['missing_profile_writers']['human1024']==roster and not l['missing_profile_writers']['human128']
    for r in rows:
        if r['writer']=='w0' and int(r['prompt'][1:])%2:r['support']['human128']=False
    assert card.layout(rows,roster)['missing_profile_writers']['human128']==['w0']
    assert len(card.layout(rows,roster)['halves'])==6


def test_complete_handler_reentry_and_every_draw_retained(tmp_path):
    p=tmp_path/'fixture.json';freeze(p,fixture());inputs=dict(fixture=str(p));o=tmp_path/'out'
    assert card.execute(o,inputs,card.CONSTRUCTED)['status']=='complete'
    before={p.name:p.read_bytes() for p in o.iterdir() if p.name!='PROGRESS.json'}
    assert card.verify(o,inputs,card.CONSTRUCTED)['full_fresh_reference_replay'];card.execute(o,inputs,card.CONSTRUCTED)
    assert before=={p.name:p.read_bytes() for p in o.iterdir() if p.name!='PROGRESS.json'}
    s=read(o/'SUMMARY.json');assert not s['effect_computed'] and not s['scientific_admission']
    for name in ['literal','independent']:
        b=gzread(o/(name+'-BANK.json.gz'));assert len(b['assignments'])==24 and len(b['missing_profile_writers'])==24
        assert s['invalid_reference_draws'][name]['human1024']==24
        assert s['invalid_reference_draws'][name]['human128']==0


def test_saved_bank_tamper_and_boundary_yield(tmp_path):
    p=tmp_path/'fixture.json';freeze(p,fixture());inputs=dict(fixture=str(p));o=tmp_path/'out';card.execute(o,inputs,card.CONSTRUCTED)
    p=o/'literal-BANK.json.gz';b=gzread(p);b['assignments'][0][0]=99;p.unlink();gzip_equal(p,b)
    with pytest.raises(ValueError,match='replay differs'):card.verify(o,inputs,card.CONSTRUCTED)
    o=tmp_path/'yield';o.mkdir();freeze(o/'YIELD_REQUEST.json',{'why':'fixture'})
    assert card.execute(o,inputs,card.CONSTRUCTED)['status']=='yielded' and not (o/'SUMMARY.json').exists()


def test_actual_completed_producer_and_changed_plan_refusal(tmp_path):
    repo=Path(__file__).resolve().parents[1];terminal=repo/'results/phase_2_4_stage_15/raw/drive-week3-20261025/D5-gallery-support/COMPLETE.json'
    rows,folds,pins=card.load(dict(support_complete=str(terminal)),card.CONFIG)
    assert len(rows)==1399 and len(folds)==61 and len(pins)>2800
    halves,_=card.split_sessions(rows);assert len(halves)==45
    assert not card.layout(rows,sorted(halves))['missing_profile_writers']['human128']
    plan=read(terminal.parent/'PLAN.json');plan['module']='wrong';freeze(tmp_path/'PLAN.json',plan);freeze(tmp_path/'COMPLETE.json',read(terminal))
    with pytest.raises(ValueError,match='source bytes'):card.load(dict(support_complete=str(tmp_path/'COMPLETE.json')),card.CONFIG)
