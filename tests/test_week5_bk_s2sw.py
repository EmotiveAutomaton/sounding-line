"""Meaningful S2.sw source, timing and identifiability regressions."""
import copy
import numpy as np
from threadpoolctl import threadpool_limits
from runners.drive.cards import week5_bk_s2sw_source as s
from runners.drive.cards import week5_bk_s2sw_analysis as a
from runners.drive.cards.week5_bk_s2sw_fixture import checks, numerical_records, row


def test_source_and_statistic_known_answers():
    with threadpool_limits(limits=1):assert all(checks().values())


def test_timing_exact_break_and_first_onset():
    rows=[];text=''
    for i in range(45):
        after=text+' word';rows.append(dict(row(text,after,1000+i*60000),ordinal=i,timestamp_count=1));text=after
    with threadpool_limits(limits=1):result=s.project_author('p','a',rows)
    assert len(result['units'])==1 and max(result['units'][0]['gaps_seconds'])==60
    assert 'over sixty' not in result['units'][0]['timing_state']
    rows[1]['timestamp']+=1
    with threadpool_limits(limits=1):result=s.project_author('p','a',rows)
    assert result['units'][0]['timing_state']=='internal gap over sixty seconds'


def test_right_censoring_and_finite_horizon():
    data=numerical_records()
    data[0]['units'][0]['observed_later_rows']=0
    data[0]['units'][1]['remaining_seconds']=119.999
    rows,counts,_=a.select(data,'within_two_minutes')
    assert counts['right_censored_no_later_row']==1 and counts['right_censored_before_two_minutes']==1
    assert len(rows)==318


def test_project_author_scope_and_empty_support():
    rows,bundle,result=a.initial([],'overlap')
    assert bundle is None and result['pooled_unadjusted_risk_difference'] is None
    _,bundle,one=a.initial(numerical_records(authors=1),'overlap')
    assert len(bundle['writers'])==1 and one['support_gate'] is False
    missing=numerical_records()
    for author in missing:
        for unit in author['units']:unit['timing_state']='unavailable author timing mixture'
    _,bundle,result=a.initial(missing,'overlap');assert bundle is None and result['counts']['analytical_spans']==0


def test_own_prior_frequency_ignores_future_revisions():
    data=[dict(author='a',units=[dict(words=['alpha'],sentence_boundary=True,paragraph_boundary=True,time_on_segment_minutes=0.,segment_order=0,start_distance=0,remaining_seconds=2),
                               dict(words=['alpha'],sentence_boundary=False,paragraph_boundary=False,time_on_segment_minutes=1.,segment_order=0,start_distance=0,remaining_seconds=1)])]
    output=s.controls(copy.deepcopy(data))
    assert output[0]['units'][0]['controls']['own_prior_log_frequency']==0
    assert all(np.isfinite(v) for u in output[0]['units'] for v in u['controls'].values())
