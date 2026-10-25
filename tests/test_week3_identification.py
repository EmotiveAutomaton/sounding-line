"""Frozen gallery, empirical null, context contamination and paired power checks."""
import copy
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import week3_identification as card
from runners.drive.cards import week3_identification_inputs as source
from tests.test_week3_identification_inputs import fixture,source_fixture,write,seal


def rows(kind='null',writers=6):
    rr=[]
    for w in range(writers):
        for s in range(8):
            v=[1.,2.] if kind=='null' else [float(w),float(w*w)] if kind=='identity' else [float(s//2),float((s//2)**2)]
            rr.append(dict(session=f'w{w}-s{s}',writer=f'w{w}',prompt=f'p{s//2}',timestamp=float(s),features={'x':v}))
    return rr


def test_null_identical_profiles_exact_chance_no_positive():
    r,d=card.analyze_group(rows(),card.CONSTRUCTED)
    x=r['x'];assert x['real']['accuracy']==pytest.approx(1/6)
    assert x['real_minus_context']['effect']==0
    assert x['real_minus_context']['ci_low']==x['real_minus_context']['ci_high']==0
    assert x['permutation']['one_sided_p']==1 and not x['pass_both']
    assert len(d['assignments'])==card.CONSTRUCTED['permutations']


def test_prompt_only_features_equal_context_and_cannot_pass():
    rr=rows('prompt');r,_=card.analyze_group(rr,card.CONSTRUCTED)
    assert r['x']['real_minus_context']['effect']==0 and not r['x']['pass_both']
    x,_=card.feature_matrix(rr)
    assert np.array_equal(card.context_rows(rr,x),x)


def test_literal_leave_writer_out_context_contains_omission_fingerprint():
    # This is a design warning, not a repaired reference: excluding the writer
    # can encode their negative fingerprint when the writer/prompt grid is balanced.
    rr=rows('identity');r,_=card.analyze_group(rr,card.CONSTRUCTED)
    assert r['x']['real']['accuracy']==r['x']['context']['accuracy']==1
    assert r['x']['real_minus_context']['effect']==0 and not r['x']['pass_both']


def test_shuffle_preserves_each_prompt_writer_count_and_determinism():
    rr=rows('identity');a=card.assignment(rr,np.random.default_rng(9))
    for p in {r['prompt'] for r in rr}:
        assert Counter(r['writer'] for r in rr if r['prompt']==p)==Counter(a[r['session']] for r in rr if r['prompt']==p)
    assert a==card.assignment(list(reversed(rr)),np.random.default_rng(9))
    ww,g,halves,_=card.split(rr,a);lookup={r['session']:r for r in rr}
    for parts in halves.values():
        assert not ({lookup[s]['prompt'] for s in parts[0]}&{lookup[s]['prompt'] for s in parts[1]})


def test_means_are_same_session_unit_in_every_arm_and_gallery_is_fixed():
    rr=rows('identity');x,ss=card.feature_matrix(rr);ww,g,_,_=card.split(rr)
    pp=card.means(x,g,ww);cx=card.context_rows(rr,x);cc=card.means(cx,g,ww)
    for i,w in enumerate(ww):
        for h in (0,1):
            assert np.array_equal(pp[i,h],x[g==2*i+h].mean(0))
            assert np.array_equal(cc[i,h],cx[g==2*i+h].mean(0))
    p=card.identify(pp,ww,ww,ss['x'])
    assert p['accuracy']==1
    assert card.pmap.identify(pp[:,0],np.roll(pp[:,1],1,axis=0))['accuracy']==0


def test_missing_context_is_unsupported_never_redrawn_or_shrunk():
    rr=rows('identity')
    for r in rr:r['prompt']=r['writer']+'-'+r['prompt']
    result,detail=card.analyze_group(rr,card.CONSTRUCTED)
    assert result['x']['state']=='unsupported' and result['x']['writers']==6
    assert len(detail['assignments'])==card.CONSTRUCTED['permutations']
    assert card.null_summary([.1,None,.2],.3)['one_sided_p'] is None


def test_residualization_uses_gallery_only_and_removes_known_linear_ai_share():
    rr=rows();ww,g,_,_=card.split(rr);share=np.linspace(0,1,len(rr))
    x=np.column_stack([3+2*share,5-7*share])
    y,coef=card.residualize(x,share,g,{'EV3.final':slice(0,2)})
    assert np.array_equal(y,np.zeros_like(y))
    contaminated=x.copy();contaminated[g%2==0]+=1000
    yy,new=card.residualize(contaminated,share,g,{'EV3.final':slice(0,2)})
    assert coef==new and np.allclose(yy[g%2==0],1000)
    assert all(c['gallery_sessions']==int((g%2==1).sum()) for c in coef['EV3.final'])


def test_paired_table_uses_joint_scores_not_marginal_difference():
    # Equal marginal totals can have either zero or all writers discordant.
    a=[1]*12+[0]*12;b=[0]*12+[1]*12
    t=card.paired_table(a,b);assert t['discordant']==24 and t['exact_two_sided_mcnemar_p']==1
    assert card.paired_table(a,a)['discordant']==0
    t=card.paired_table([1]*6+[0]*18,[0]*24)
    assert t['exact_two_sided_mcnemar_p']==.03125
    assert card.paired_table([.5,1,0],[1,0,1])['state']=='unsupported'


def test_power_exact_bounds_and_infeasible_dependence_not_clipped():
    assert card.mcnemar_power(24,0,0)==0
    assert card.mcnemar_power(24,1,0)==1
    assert card.mcnemar_power(24,.25,0)==pytest.approx(1-card.binom.cdf(5,24,.25))
    table=card.paired_table([1]*12+[0]*12,[1]*12+[0]*12)
    curve=card.power_curve(table)
    assert curve['phi']==1
    assert all(r['power'] is None for r in curve['grid'] if not r['feasible'])
    assert any(not r['feasible'] for r in curve['grid'])
    assert card.power_curve(card.paired_table([1]*24,[1]*24))['state']=='unsupported'


def test_full_constructed_handler_fresh_replay_mutation_and_scoped_audit(tmp_path):
    inputs=source_fixture(tmp_path/'source');prepared=tmp_path/'prepared'
    source.execute(prepared/'output',inputs,source.CONSTRUCTED)
    source.verify(prepared/'output',inputs,source.CONSTRUCTED)
    write(prepared/'PLAN.json',dict(module='runners.drive.cards.week3_identification_inputs',inputs=inputs,config=source.CONSTRUCTED))
    analysis_inputs=dict(source_completion=seal(prepared));out=tmp_path/'analysis'
    assert card.execute(out,analysis_inputs,card.CONSTRUCTED)['status']=='complete'
    assert card.verify(out,analysis_inputs,card.CONSTRUCTED)['verified']
    result=card.read(out/'SUMMARY.json');detail=card.gzread(out/'DETAIL.json.gz')
    assert len(result['channels'])==11 and set(result['genres'])=={'creative','argumentative'}
    assert len(detail['original_pooled_audit'])==10
    assert not any(result['badge_licenses'].values())
    bad=copy.deepcopy(result);bad['badge_licenses']['habit']=True
    (out/'SUMMARY.json').write_text(json.dumps(bad),encoding='utf8')
    with pytest.raises(ValueError,match='changed'):card.verify(out,analysis_inputs,card.CONSTRUCTED)
