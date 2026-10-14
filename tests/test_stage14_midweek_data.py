import copy
from runners.stage14_midweek.data import effort,construct,render_history

def event(name,t,insert=None,source='user'):
    return dict(eventName=name,eventTimestamp=t,eventSource=source,
                textDelta={'ops':[] if insert is None else [{'insert':insert}]})

def test_utf16_cost_and_latency_stop_before_next_menu():
    es=[event('suggestion-open',0),event('suggestion-select',1500),
        event('text-insert',1600,'model','api'),event('text-insert',2000,'a😀'),
        event('suggestion-open',3000),event('text-insert',4000,'not historical')]
    r=effort(es,0,4,'accept')
    assert r['chars_typed_after']==3 and r['decide_seconds']==1.5

def test_ignore_no_insertion_is_missing_not_zero():
    assert effort([event('suggestion-open',0),event('cursor',50)],0,2,'ignore')['decide_seconds'] is None

def test_reopen_does_not_count_later_typing_twice():
    es=[event('suggestion-open',0),event('suggestion-close',100),event('text-insert',200,'x'),
        event('suggestion-open',300),event('suggestion-select',400),event('text-insert',500,'later')]
    assert effort(es,0,6,'accept')['chars_typed_after']==1

def test_negative_time_refuses():
    import pytest
    with pytest.raises(ValueError):effort([event('suggestion-open',100),event('suggestion-select',0)],0,2,'accept')

def test_history_render_allowlist():
    r=dict(prompt='p',document='d',menu=['a'],handling='accept',inserted='a',
           effort=dict(chars_typed_after=3,decide_seconds=1),secret='poison',writer='private')
    s=render_history([r])[0]
    assert set(s)=={'prompt','draft_end','menu','decision','inserted'}
    assert 'effort' in render_history([r],True)[0]
