"""Constructed fit-scope controls, unexecuted until counted owner qualification.

DESIGN CHECK: LESSONS 3/4/5. A singular secondary leaves a valid primary
unchanged; invalid primary/base fits retain denominator and withhold inference.
Every original draw is retained. No tolerance, roster, model or bar changes.
"""
import copy
import math
import numpy as np
import pytest
from runners.drive.cards import week6_ch14_math_v1 as original
from runners.drive.cards import week6_ch14_math_v3 as fixed
from runners.drive.cards import week6_ch_riders_fixture_v3 as fixture


def controlled(monkeypatch, statuses, module=fixed, players=24):
    """Literal per-choice log scores isolate status propagation from fitting."""
    prepared=dict(names=[f'constructed-{i}' for i in range(players)],census={})
    sets={}
    for name in ('count','hours','games'):
        data=dict(name=name,person=np.arange(players),week=np.ones(players,bool),
                  starts=np.arange(players),x=np.zeros((players,1)))
        sets[name]=(data,data)
    def fit(data,weights,reference=False,check=lambda:None):
        status=statuses.get(data['name'],'complete')
        return dict(status=status,beta=[0.]) if status=='complete' else dict(status=status,reason='Literal refusal')
    def likelihood(data,beta,weights,reference=False):
        return np.full(players,dict(count=-1.,hours=-.99,games=-.98)[data['name']]),None,None
    monkeypatch.setattr(module,'fit',fit)
    monkeypatch.setattr(module,'likelihood',likelihood)
    return prepared,sets


@pytest.mark.parametrize('reference',[False,True])
def test_invalid_secondary_retains_primary_and_both_support_counts(monkeypatch,reference):
    prepared,sets=controlled(monkeypatch,{'games':'invalid'})
    point=fixed.draw(prepared,sets,np.ones(24),reference)
    assert point['gains']['hours']['point']==pytest.approx(.01)
    assert point['gains']['hours_week_break']['point']==pytest.approx(.01)
    assert point['gains']['games']['point'] is None
    assert point['gains']['games']['comparison_status']=='invalid'
    assert all(row['players']==24 and row['choices']==24 for row in point['gains'].values())
    result=fixed.result(prepared,point,[point]*20)
    assert result['gains']['hours']['classification']=='gain beyond bar'
    assert result['gains']['games']['interval'] is None


def test_frozen_v1_exposes_the_specific_secondary_gate_defect(monkeypatch):
    prepared,sets=controlled(monkeypatch,{'games':'invalid'},original)
    point=original.draw(prepared,sets,np.ones(24))
    assert point['gains']=={}
    assert original.result(prepared,point,[point]*20)['gains']['hours']['players']==0


@pytest.mark.parametrize('invalid_arm',['hours','count'])
def test_invalid_primary_or_shared_baseline_is_not_below_floor(monkeypatch,invalid_arm):
    prepared,sets=controlled(monkeypatch,{invalid_arm:'invalid'})
    point=fixed.draw(prepared,sets,np.ones(24))
    summary=fixed.result(prepared,point,[point]*20)['gains']['hours']
    assert summary['players']==24 and summary['choices']==24
    assert summary['classification']=='invalid fit'
    assert summary['point'] is None and summary['interval'] is None
    assert summary['invalid_draws']==20
    assert (point['gains']['games']['point'] is None)==(invalid_arm=='count')


def test_invalid_point_never_gets_interval_from_valid_resampled_fits(monkeypatch):
    prepared,sets=controlled(monkeypatch,{})
    good=fixed.draw(prepared,sets,np.ones(24));bad=copy.deepcopy(good)
    bad['gains']['hours'].update(point=None,comparison_status='invalid')
    bad['fits']['hours']=dict(status='invalid',reason='Literal full-roster rank failure')
    summary=fixed.result(prepared,bad,[good]*20)['gains']['hours']
    assert summary['interval'] is None and summary['classification']=='invalid fit'
    assert summary['valid_draws']==20


def test_one_invalid_primary_draw_holds_interval_without_redraw(monkeypatch):
    prepared,sets=controlled(monkeypatch,{})
    good=fixed.draw(prepared,sets,np.ones(24));bad=copy.deepcopy(good)
    bad['gains']['hours'].update(point=None,comparison_status='invalid')
    summary=fixed.result(prepared,good,[good]*19+[bad])['gains']['hours']
    assert summary['interval'] is None and summary['classification']=='uncertainty unavailable'
    assert summary['valid_draws']==19 and summary['invalid_draws']==1


def test_unsupported_training_is_explicit_and_keeps_observed_denominator(monkeypatch):
    prepared,sets=controlled(monkeypatch,{'hours':'unsupported'})
    point=fixed.draw(prepared,sets,np.ones(24))
    summary=fixed.result(prepared,point,[point]*20)['gains']['hours']
    assert summary['players']==24 and summary['point'] is None
    assert summary['classification']=='unsupported training comparison'


def test_true_empty_support_still_has_descriptive_fallback(monkeypatch):
    prepared,sets=controlled(monkeypatch,dict.fromkeys(('count','hours','games'),'unsupported'),players=0)
    point=fixed.draw(prepared,sets,np.zeros(0))
    summary=fixed.result(prepared,point,[point]*20)['gains']['hours']
    assert summary['players']==0 and summary['classification']=='below floor, descriptive'
    assert summary['interval'] is None


def test_unknown_fit_status_is_refused(monkeypatch):
    prepared,sets=controlled(monkeypatch,{'games':'mystery'})
    with pytest.raises(ValueError,match='Unknown conditional fit status'):
        fixed.draw(prepared,sets,np.ones(24))


@pytest.mark.parametrize('reference',[False,True])
def test_actual_singular_game_recency_preserves_analytic_hours_gain(reference):
    prepared=fixture.literal_menus('recency_at_bar')
    prepared['x'][:,2]=0.  # Exactly singular secondary, hours/count unchanged.
    point=fixed.draw(prepared,fixed.model_sets(prepared),np.ones(len(prepared['names'])),reference)
    expected=.54*math.log(.54/.5)+.46*math.log(.46/.5)
    assert point['fits']['games']['status']=='invalid'
    assert point['fits']['count']['status']==point['fits']['hours']['status']=='complete'
    assert point['gains']['hours']['point']==pytest.approx(expected,abs=1e-7)
    assert point['gains']['games']['point'] is None
