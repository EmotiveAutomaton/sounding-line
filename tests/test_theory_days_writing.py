from runners.theory_days.writing_support import support

def test_exact_positive_floor_and_literal_consumer(tmp_path):
    from runners.theory_days.validate_writing import fixture as positive,execute,verify
    summary,matches,writers=support(*positive())
    assert summary['support_pass'] and summary['writers_with_ten_pairs']==20
    assert len(matches)==200 and len(writers)==20
    keys=[k for pair in matches for event in pair.values() for k in event['future']]
    assert len(keys)==1200 and len(set(keys))==1200
    assert not support(*positive(19))[0]['support_pass']
    execute(tmp_path,{},{});assert verify(tmp_path,{}, {})['verified']

def fixture():
    sessions=[];nav=[]
    for sid in range(2):
        menus=[]
        for j in range(12):
            m=dict(key=f'{sid}-{j}',session=str(sid),writer='w',ordinal=j,
                open_at=sid*1000+j*10,resolved_at=sid*1000+j*10+1,
                handling='dismiss' if j%2==0 else 'accept',choice=2 if j%2==0 else 0)
            menus.append(m)
            nav.append(dict(key=m['key'],session=str(sid),writer='w',canonical_choice=m['choice'],
                            navigation=dict(hover_ordinals=[j])))
        sessions.append(dict(session=str(sid),timestamp=sid*1000,end_at=sid*1000+120,menus=menus))
    return sessions,nav

def test_windows_are_disjoint_and_do_not_cross_sessions():
    sessions,nav=fixture();summary,matches,writers=support(sessions,nav)
    assert summary['status']=='design cannot test'
    assert summary['clauses']['overlap_with_earlier_event']>0
    used=[]
    for pair in matches:
        for event in pair.values():
            assert len(event['future'])==3
            assert all(k.startswith(event['session']+'-') for k in event['future'])
            used+=event['future']
    assert len(used)==len(set(used))

def test_ignored_menus_are_skipped_not_dismissed():
    sessions,nav=fixture()
    for sid in range(2):
        sessions[sid]['menus'][1].update(handling='ignore',choice=None)
        nav[sid*12+1]['canonical_choice']=None
    summary,matches,writers=support(sessions,nav)
    assert summary['opened_menus']==24
    assert all(event['key']!=f"{event['session']}-1" for pair in matches for event in pair.values())

def test_missing_navigation_refuses():
    import pytest
    sessions,nav=fixture()
    with pytest.raises(ValueError):support(sessions,nav[:-1])
