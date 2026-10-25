"""Exact parent parity, no-signal controls, attribution plants and new-reader oracle."""
import copy,json,math
from pathlib import Path

import numpy as np
import pytest

from runners.drive.cards import week3_identification_followups as card
from runners.drive.cards import week3_identification_followup_timing as timing
from tests.test_week3_identification_crossfit import prepared_fixture


def data(kind='null',signal_block=None):
    value=prepared_fixture();ww=sorted({r['writer'] for r in value['rows']})
    pp=sorted({r['prompt'] for r in value['rows']})
    for row in value['rows']:
        w=ww.index(row['writer']);p=pp.index(row['prompt'])
        row['accepted_share']=0.25
        for name,features in row['features'].items():
            size=len(features)
            if kind=='null':x=[1.]*size
            elif kind=='prompt':x=[float((p+1)*(j+1)) for j in range(size)]
            else:x=[math.sin((w+1)*(j+1))+math.cos((w+1)*(j+2)) for j in range(size)]
            if signal_block and name=='EV3.final':
                x=[v if j in card.BLOCKS[signal_block] else 1. for j,v in enumerate(x)]
            row['features'][name]=x
    return value


def small(kind):return dict(card.CONSTRUCTED[kind],permutations=24,bootstrap_draws=100)


def test_baseline_is_exact_parent_and_source_is_immutable():
    value=data('identity');before=copy.deepcopy(value);config=small('p')
    original,_=card.parent.analyze_group(value['rows'],config,card.rosters(value))
    result,_=card.analyze(value,config)
    assert result['members']['baseline']==original
    assert value==before and card.base.identify is not card.correlation_identify
    assert result['members']['correlation'][card.PRIMARY]['real']['accuracy']==1


@pytest.mark.parametrize('kind',['null','prompt'])
def test_every_specification_and_correlation_rejects_no_person_signal(kind):
    value=data(kind)
    for followup in ('s','p'):
        result,_=card.analyze(value,small(followup))
        for members in result['members'].values():
            for outcome in members.values():
                assert not outcome['pass_both']
                assert outcome['real_minus_context']['effect']==0
                assert outcome['real_minus_context']['ci_low']==outcome['real_minus_context']['ci_high']==0


def test_rotations_are_balanced_and_every_writer_is_probed_once_per_specification():
    value=data('identity');result,detail=card.analyze(value,small('s'))
    writers=sorted({r['writer'] for r in value['rows']})
    assert len(result['members'])==5
    for name,member in detail['members'].items():
        assert member['variants'][card.PRIMARY]['writers']==writers
        assert member['writer_folds']==card.parent.writer_folds(value['rows'],20261026 if name=='baseline' else int(name.rsplit('_',1)[1]))
        assert sorted(list(member['writer_folds'].values()).count(i) for i in range(3))==[4,4,4]
        probes=[]
        for f in member['folds']:
            assert not set(f['donor_writers'])&set(f['gallery_writers']['EV3.final'])
            probes+=f['probe_writers']['EV3.final']
        assert sorted(probes)==writers
    assert result['specification_curve'][card.PRIMARY]['all_pass']
    assert 'one_sided_p' not in result['specification_curve'][card.PRIMARY]


def test_planted_single_block_disappears_only_when_that_block_is_removed():
    value=data('identity',signal_block='connectives')
    result,_=card.analyze(value,small('m'))
    assert result['members']['baseline'][card.PRIMARY]['pass_both']
    removed=result['members']['without_connectives'][card.PRIMARY]
    assert not removed['pass_both'] and removed['real_minus_context']['effect']==0
    for block in ('punctuation','sentence_length','quoted_share'):
        assert result['members']['without_'+block][card.PRIMARY]['pass_both']
    assert result['paired_changes']['without_connectives'][card.PRIMARY]['baseline_minus_variant_accuracy']['ci_low']>0
    assert set().union(*map(set,card.BLOCKS.values()))==set(range(17))
    assert sum(map(len,card.BLOCKS.values()))==17


def test_missing_original_support_never_shrinks_gallery_or_selects_only_good_specs():
    value=data('identity')
    for row in value['rows']:row['prompt']=row['writer']+'-'+row['prompt']
    result,_=card.analyze(value,small('s'))
    assert result['specification_curve'][card.PRIMARY]['all_supported'] is False
    assert result['specification_curve'][card.PRIMARY]['accuracy_range'] is None
    assert all(m[card.PRIMARY]['state']=='unsupported' and m[card.PRIMARY]['writers']==12 for m in result['members'].values())


def test_correlation_reader_matches_independent_scalar_pearson_oracle():
    rng=np.random.default_rng(11);b=rng.normal(size=(7,5));a=b+rng.normal(size=b.shape)*.8
    a[0,2]=np.nan;b[1,4]=np.nan
    mean=np.nanmean(b,axis=0);bb=np.where(np.isfinite(b),b,mean);aa=np.where(np.isfinite(a),a,mean)
    sd=bb.std(0);aa=(aa-mean)/sd;bb=(bb-mean)/sd
    scores=[]
    for i,row in enumerate(aa):
        sims=np.array([np.corrcoef(row,x)[0,1] for x in bb])
        ties=np.isclose(sims,sims.max(),atol=1e-12,rtol=1e-12)
        scores.append(float(ties[i]/ties.sum()))
    assert card.correlation(a,b)['scores']==scores


def test_correlation_zero_shape_and_reversed_identity_have_known_answers():
    zero=card.correlation(np.ones((8,4)),np.ones((8,4)))
    assert zero['scores']==[.125]*8 and zero['neutral_shape_A']==8
    x=np.eye(8)
    assert card.correlation(x,x)['accuracy']==1
    assert card.correlation(x,np.roll(x,1,axis=0))['accuracy']==0
    assert card.correlation(x+4,x+4)['scores']==card.correlation(x,x)['scores']


def test_scoped_reader_restores_original_on_failure_and_unknown_kind_refuses():
    old=card.base.identify
    with pytest.raises(RuntimeError):
        with card.reader('correlation'):
            assert card.base.identify is card.correlation_identify
            raise RuntimeError('fixture')
    assert card.base.identify is old
    with pytest.raises(ValueError):
        with card.reader('other'):pass


def test_complete_baseline_binding_checks_more_than_point_levels():
    original={'x':dict(writers=3,real={'accuracy':1.},context={'accuracy':0.},
        fold_gallery_sizes=[2,2,2],permutation={'one_sided_p':.01})}
    card.expected_points(original,copy.deepcopy(original),exact=True)
    altered=copy.deepcopy(original);altered['x']['permutation']['one_sided_p']=.9
    card.expected_points(altered,original,exact=False)  # Cost pilot has fewer null draws.
    with pytest.raises(ValueError,match='complete original parent baseline'):
        card.expected_points(altered,original,exact=True)


@pytest.mark.parametrize('kind',['s','m','p'])
def test_full_handler_reentry_fresh_replay_and_source_mutation(kind,tmp_path):
    f=tmp_path/'fixture.json';f.write_text(json.dumps(data('identity')),encoding='utf8')
    inputs={'fixture':str(f)};out=tmp_path/'out';config=card.CONSTRUCTED[kind]
    assert card.execute(out,inputs,config)['status']=='complete'
    assert card.verify(out,inputs,config)['verified']
    assert not card.read(out/'SUMMARY.json')['followups_authorized']
    f.write_text(f.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):card.verify(out,inputs,config)


@pytest.mark.parametrize('kind',['s','m','p'])
def test_cost_pilot_runs_all_fixed_members_but_persists_no_scores(kind,tmp_path):
    f=tmp_path/'fixture.json';f.write_text(json.dumps(data('identity')),encoding='utf8')
    inputs={'fixture':str(f)};out=tmp_path/'cost';config=timing.CONSTRUCTED[kind]
    assert timing.execute(out,inputs,config)['cost_only']
    assert timing.verify(out,inputs,config)['verified']
    work=card.read(out/'WORK.json');forecast=card.read(out/'FORECAST.json')
    assert len(work['work_counts']['members'])==(2 if kind=='p' else 5)
    assert work['work_counts']['draws_per_fold']==8
    assert not work['scientific_admission'] and not (out/'SUMMARY.json').exists()
    assert forecast['projected_execute_plus_verify']['cpu_seconds']>forecast['pilot_charged_cpu_seconds']
    assert forecast['cpu_ceiling_seconds']==5400
