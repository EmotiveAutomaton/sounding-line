"""Constructed raw-screen, support/calibration and joint-inference checks."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time
import numpy as np
import pytest

from runners.drive.cards import timing_d33_supported as card
from runners.drive.cards import timing_d33_supported_source as source
from runners.drive.cards import timing_d33_supported_stats as stats
from runners.drive.cards.timing_census import read,write,filehash
from runners.drive.cards.timing_stats import sufficient

REPO=Path(__file__).resolve().parents[1]


def word(index,token,ordinal,p=.05):
    return dict(index=index,token=token,ordinal=ordinal,population_probability=p,context=[],is_word=True)


def test_screen_prompt_visible_api_and_shown_have_strict_first_insertion_clock():
    events=[dict(eventName='system-initialize',eventTimestamp=0,currentDoc='prompt '),
        dict(eventName='suggestion-open',eventTimestamp=1,currentSuggestions=[dict(index=8,original='hidden',trimmed='shown')]),
        dict(eventName='insert',eventTimestamp=2,eventSource='api',textDelta={'ops':[{'retain':7},{'insert':'accepted '}]}),
        dict(eventName='insert',eventTimestamp=3,eventSource='user',textDelta={'ops':[{'retain':16},{'insert':'future '}]}),
        dict(eventName='suggestion-open',eventTimestamp=4,currentSuggestions=[dict(index=1,original='later',trimmed='later')])]
    words=[word(0,'prompt',3),word(1,'accepted',3),word(2,'shown',3),word(3,'future',3),word(4,'later',3),word(5,'hidden',3)]
    values=source.screen_covariates(events,words)
    assert [values[i]['on_screen'] for i in range(6)]==[1,1,1,0,0,0]
    assert values[0]['in_prompt'] and values[1]['in_visible_text'] and values[2]['in_previous_shown_suggestion']
    assert all(v['prior_visible_tokens']==1 for v in values.values())


def test_deleted_text_not_present_prompt_boundary_and_utf16_are_preserved():
    events=[dict(eventName='system-initialize',eventTimestamp=0,currentDoc='P '),
        dict(eventName='insert',eventTimestamp=1,eventSource='user',textDelta={'ops':[{'retain':2},{'insert':'😀 old '}]}),
        dict(eventName='delete',eventTimestamp=2,eventSource='user',textDelta={'ops':[{'retain':2},{'delete':7}]}),
        dict(eventName='insert',eventTimestamp=3,eventSource='user',textDelta={'ops':[{'retain':2},{'insert':'new '} ]})]
    actual=source.screen_covariates(events,[word(0,'old',3),word(1,'new',3)])
    assert actual[0]['on_screen']==actual[1]['on_screen']==0 and actual[0]['prior_visible_tokens']==0
    assert source.visible_sequences([ord('a'),ord('P'),ord('b')],['typed','prompt','api'])==[['a'],['b']]
    events[2]['textDelta']['ops'][1]['delete']=1
    with pytest.raises(UnicodeDecodeError):source.screen_covariates(events,[word(0,'old',3)])


def test_roster_support_is_independent_and_partitions_all_original_rows():
    saved=dict(rows=[dict(writer='w',session='e1',index=0,log_pause=999),dict(writer='w',session='e2',index=0,log_pause=-999)])
    original=dict(writers={'w':dict(calibration_sessions=['c1','c2'],evaluation_sessions=['e1','e2'],original_alpha=.9)})
    lookup={sid:dict(words=[word(0,'a',1)]) for sid in ['c1','c2','e1','e2']}
    units={sid:dict(proof=dict(supported=sid in ('c2','e1'))) for sid in lookup}
    value=source.population_roster(saved,original,units,lookup,'pair')
    assert value['retained_keys']==[['e1',0]] and value['unsupported_keys']==[['e2',0]]
    assert value['writers']['w']['calibration_keys']==[['c2',0]]
    assert value['coverage']['unsupported_calibration_words']==1
    saved['rows'][0]['log_pause']=-1e8
    assert source.population_roster(saved,original,units,lookup,'pair')==value


def make_design(beta=.8):
    rng=np.random.default_rng(31);rows=[]
    for wi in range(6):
        for j in range(32):
            own,donor,pop,length,freq,session=rng.normal(size=6)
            start,punct,screen=rng.integers(0,2,size=3)
            y=beta*own+.35*donor+.15*pop+.02*length-.03*freq+.1*start-.05*punct+.04*screen+.12*session+wi*.15+rng.normal(scale=.12)
            rows.append(dict(writer=str(wi),session=f'w{wi}_s',index=j,own_surprise=float(own),donor_surprise=float(donor),
                original_personal_surprise=float(own*1.1),population_surprisal=float(pop),length=float(length),log_frequency=float(freq),
                sentence_start=int(start),after_punctuation=int(punct),on_screen=int(screen),session_surprisal=float(session),log_pause=float(y)))
    return rows


@pytest.mark.parametrize('beta',[-.8,0.,.8])
def test_joint_known_signs_and_direct_dense_gls_agree(beta):
    rows=make_design(beta);x,y,w=stats.design(rows);fit=stats.fit(sufficient(x,y,w))
    assert fit['own']==pytest.approx(beta,abs=.04) and fit['donor']==pytest.approx(.35,abs=.04)
    v=np.eye(len(y))
    for writer in sorted(set(w)):
        ix=np.flatnonzero(w==writer);v[np.ix_(ix,ix)]+=fit['variance_ratio']
    inverse=np.linalg.inv(v);expected=np.linalg.solve(x.T@inverse@x,x.T@inverse@y)
    assert fit['own']==pytest.approx(expected[0],abs=1e-8)
    assert fit['own_minus_donor']==pytest.approx(expected[0]-expected[1],abs=1e-8)


def test_collinear_focal_refuses_and_redundant_nuisance_preserves_span():
    rows=make_design();x,y,w=stats.design(rows)
    x[:,1]=x[:,0]
    with pytest.raises(ValueError,match='not separately identifiable'):stats.fit(sufficient(x,y,w))
    x,y,w=stats.design(rows);x[:,8]=1.
    result=stats.fit(sufficient(x,y,w));assert 'on_screen' in result['omitted_columns'] and abs(result['own']-.8)<.04


def test_invalid_and_zero_range_controls_have_no_division_or_successful_only_p():
    result=stats.null_summary([0.]*199+[None],.5)
    assert result['state']=='invalid' and result['one_sided_p'] is None
    assert result['sd']==0 and not result['bias_flag']
    assert stats.null_summary([.1]*200,.5)['bias_flag']
    assert stats.interval(.1,[.1]*2000)['z'] is None


def test_exact_production_configuration_refuses_small_draws():
    with pytest.raises(ValueError,match='exact supported'):
        card.validate({k:'' for k in source.INPUTS},dict(card.configuration('pair'),bootstrap_draws=25))


@pytest.mark.parametrize('failure',[dict(success=False,x=0.,fun=1.),dict(success=True,x=float('nan'),fun=1.),dict(success=True,x=0.,fun=float('inf'))])
def test_failed_or_nonfinite_optimizer_cannot_become_zero_variance(monkeypatch,failure):
    from types import SimpleNamespace
    rows=make_design();groups=sufficient(*stats.design(rows))
    expected=stats.fit(groups)
    assert expected['own']==pytest.approx(.8,abs=.04)
    monkeypatch.setattr(stats,'minimize_scalar',lambda *args,**kwargs:SimpleNamespace(**failure))
    with pytest.raises(ValueError,match='optimization failed or was nonfinite'):stats.fit(groups)


def test_serialized_full_inference_checkpoint_resume_and_fresh_process(tmp_path):
    start=time.perf_counter();rows=make_design();path=tmp_path/'rows.json';write(path,rows)
    checkpoints=tmp_path/'inference';calls=[]
    yielded=stats.run(rows,checkpoint=checkpoints,checkpoint_callback=lambda r:calls.append(r) or True)
    assert yielded['status']=='yielded' and calls[0]['completed_draws']==200 and calls[0]['completed_permutations']==20
    first=checkpoints/'block-00.json';original=(first.read_bytes(),first.stat().st_mtime_ns)
    result=stats.run(rows,checkpoint=checkpoints)
    assert result['primary']['own']['state']=='positive' and result['primary']['own_minus_donor']['state']=='positive'
    assert result['controls']['own_surprise']['attempted']==200 and result['controls']['outcome']['attempted']==200
    assert (first.read_bytes(),first.stat().st_mtime_ns)==original
    expected=tmp_path/'RESULT.json';write(expected,result)
    code="import json,sys;from runners.drive.cards.timing_d33_supported_stats import run;r=json.load(open(sys.argv[1],encoding='utf8'));expected=json.load(open(sys.argv[2],encoding='utf8'));assert run(r)==expected"
    child=subprocess.run([sys.executable,'-c',code,str(path),str(expected)],cwd=REPO,capture_output=True,text=True,timeout=120,
        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name=='nt' else 0)
    assert child.returncode==0,child.stderr
    write(tmp_path/'SMOKE.json',dict(seconds=time.perf_counter()-start,fresh_exit=child.returncode,
        bytes=sum(p.stat().st_size for p in tmp_path.rglob('*') if p.is_file())))
