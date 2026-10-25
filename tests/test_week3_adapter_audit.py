"""Retained adapters: exact label separation, legal plants and original rules."""
import copy
import json

import numpy as np
import pytest

from runners.drive.cards import week3_adapter_audit as card
from runners.drive.cards import week3_adapter_inputs as source
from runners.stage14.uncertainty_v2 import contrast
from tests.test_week3_adapter_inputs import fixture as source_fixture


def fixture():
    f=source_fixture()
    for writer,phases in f['cases'].items():
        for c in phases['evaluation']:c['prompt']='prompt-'+writer
    for r in f['predictions']:r['prompt']='prompt-'+r['writer']
    one=source.prepare_cell(**f);two=copy.deepcopy(one);two['cell']='fixture-copy'
    return [one,two]


def writer_rows(n=8,advantage=0.):
    rows=[]
    for i in range(n):
        p=[.45+.01*(i%3),.55-.01*(i%3)];own=card.loss(p,0)
        rows.append(dict(writer=f'w{i:03}',prompt=f'p{i%3}',observations=1,own_probabilities=[p],truths=[0],
            losses={'canonical_recalibrated':dict(own=own,base=own+advantage,pooled=own+advantage,donor=own+advantage)}))
    return rows


def test_canonical_calibration_changes_temperature_without_evaluation_leak():
    c=fixture()[0];rows,details=card.calibrated(c)
    assert any(d['canonical_temperatures']!=d['old_temperatures'] for d in details)
    changed=copy.deepcopy(c)
    for w in changed['writers']:
        for r in w['cases']['evaluation']:r['canonical_truth']=1-r['canonical_truth']
    _,details2=card.calibrated(changed)
    assert [d['canonical_temperatures'] for d in details]==[d['canonical_temperatures'] for d in details2]


def test_original_writer_and_crossed_bootstrap_parity_with_prompt_gating():
    rows=[]
    for i in range(9):
        for j in range(i%3+1):
            rows.append(dict(writer=f'w{i}',prompt=f'p{i%4}',scores={
                'own':dict(half_brier=.2+.013*i+.001*j),'rival':dict(half_brier=.3-.007*i)}))
    original=contrast(rows,'own','rival',4000)
    writers=sorted({r['writer'] for r in rows})
    differences=[np.mean([r['scores']['own']['half_brier']-r['scores']['rival']['half_brier'] for r in rows if r['writer']==w]) for w in writers]
    prompts=[next(r['prompt'] for r in rows if r['writer']==w) for w in writers]
    actual=card.intervals(differences,prompts,4000)
    np.testing.assert_allclose(actual['writer_interval'],original['interval'],atol=5e-16,rtol=0)
    np.testing.assert_allclose(actual['crossed_writer_prompt_interval'],original['crossed_writer_prompt_interval'],atol=5e-16,rtol=0)
    assert actual['passes']==(original['interval'][1]<-.01 and original['crossed_writer_prompt_interval'][1]<-.01)


def test_exact_writer_plant_is_legal_and_respects_different_choice_counts():
    probabilities=[[.2,.3,.5],[.65,.35],[.15,.25,.2,.4]];truths=[2,0,1]
    for delta in card.CONFIG['plants']:
        result=card.plant(probabilities,truths,delta)
        assert result is not None
        assert result['achieved_improvement']==pytest.approx(delta,abs=5e-14)
        for old,new,y in zip(probabilities,result['probabilities'],truths):
            assert min(new)>=0 and sum(new)==pytest.approx(1)
            assert new[y]>old[y]
            for i in range(len(new)):
                if i!=y:assert new[i]/old[i]==pytest.approx(1-result['alpha'])
    assert card.plant([[1.,0.]],[0],.01) is None


def test_null_at_margin_fails_while_true_larger_improvement_passes_all_rivals():
    result=card.power_group([('null',writer_rows())],dict(card.CONSTRUCTED,worlds=12))['null']
    assert result['grid'][0]['recovery_rate']==0
    assert all(r['recovery_rate']==1 for r in result['grid'][1:])
    assert result['minimum_detectable_added_improvement']==.02
    assert not result['total_advantage_exclusion_licensed']
    bad=writer_rows();bad[0]['own_probabilities']=[[1.,0.]];bad[0]['losses']['canonical_recalibrated']['own']=0
    unsupported=card.power_group([('bad',bad)],dict(card.CONSTRUCTED,worlds=2))['bad']
    assert all(not r['supported'] and r['unsupported_writers']==1 for r in unsupported['grid'])
    assert unsupported['minimum_detectable_label']=='unsupported'


def test_rival_deficits_remain_explicit_in_power_and_one_stronger_rival_blocks():
    rows=writer_rows()
    for r in rows:r['losses']['canonical_recalibrated']['donor']-=.045
    result=card.power_group([('deficit',rows)],dict(card.CONSTRUCTED,worlds=8))['deficit']
    assert all(r['recovery_rate']==0 for r in result['grid'])
    assert result['grid'][1]['actual_post_plant_advantage']['donor']['equal_writer_mean']==pytest.approx(-.025)
    assert result['minimum_detectable_label']=='more than 0.05'


def test_grouped_power_is_identical_to_separate_cells():
    one=writer_rows();two=writer_rows(advantage=-.003)
    config=dict(card.CONSTRUCTED,worlds=12)
    grouped=card.power_group([('one',one),('two',two)],config)
    assert grouped['one']==card.power_group([('one',one)],config)['one']
    assert grouped['two']==card.power_group([('two',two)],config)['two']


@pytest.mark.parametrize('defect',['prompt','overlap','duplicate','population'])
def test_no_silent_population_or_partition_change(defect):
    cells=fixture()
    if defect=='prompt':cells[0]['writers'][0]['cases']['evaluation'][1]['prompt']='second-prompt'
    if defect=='overlap':cells[0]['writers'][0]['cases']['evaluation'][0]['key']=cells[0]['writers'][0]['cases']['calibration'][0]['key']
    if defect=='duplicate':cells[0]['writers'].append(cells[0]['writers'][0])
    if defect=='population':cells.pop()
    with pytest.raises(ValueError):card.analyze(cells,card.CONSTRUCTED)


def test_complete_constructed_analysis_and_source_mutation(tmp_path):
    path=tmp_path/'fixture.json';path.write_text(json.dumps(fixture()),encoding='utf8')
    inputs=dict(fixture=str(path));out=tmp_path/'out'
    assert card.execute(out,inputs,card.CONSTRUCTED)['cells']==2
    assert card.verify(out,inputs,card.CONSTRUCTED)['verified']
    path.write_text(path.read_text()+' ',encoding='utf8')
    with pytest.raises(ValueError,match='changed'):card.verify(out,inputs,card.CONSTRUCTED)
