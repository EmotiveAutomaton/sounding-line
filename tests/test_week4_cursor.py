from runners.drive.cards.week4_cursor import motion,geometry,extract,near_edit,shift_boundary,assemble
from runners.stage9.coauthor import units

def test_word_steps_paragraph_jumps_and_unicode():
    doc=units('A 😀 word.\nNext sentence.');s,w,p=geometry(doc)
    assert motion(0,1,w,p)=='step'
    assert motion(1,5,w,p)=='step'
    assert motion(10,11,w,p)=='jump'
    assert motion(0,41,[],[])=='jump'

def event(name,t,cursor,**kw):return dict(eventName=name,eventTimestamp=t*1000,currentCursor=cursor,eventSource='user',**kw)
def test_step_runs_and_pass_through_jumps():
    text='One sentence in the opening paragraph.\nAnother sentence in paragraph two.\nThird final sentence.'
    events=[event('system-initialize',0,len(text),currentDoc=text),event('cursor-backward',1,0),event('cursor-forward',2,1),
        event('cursor-forward',3,2),event('cursor-forward',6,45),event('cursor-backward',7,0),
        event('cursor-forward',8,40,eventSource_override='unused')]
    # Last jump traverses a paragraph and suppresses the preceding jump.
    result=extract(events)
    assert result['census']['inside_step_run']==1
    assert all(x['ordinal']!=2 for x in result['landings'])
    assert result['census']['pass_through_jump']>=1

def test_edit_distance_window_and_boundary_mapping():
    landing=dict(ordinal=1,time=0,near_start=20,near_end=30)
    far=dict(ordinal=2,time=1,ops=[{'insert':'xxxxx'}],user=True)
    near=dict(ordinal=3,time=30,ops=[{'retain':25},{'insert':'!'}],user=True)
    assert near_edit(landing,[far,near])
    assert not near_edit(landing,[far,dict(near,time=30.001)])
    assert not near_edit(landing,[dict(near,user=False)])
    assert shift_boundary(20,[{'retain':5},{'delete':3}])==17

def test_api_cursor_and_open_hover_snapshot_are_not_user_moves():
    init=event('system-initialize',0,0,currentDoc='One sentence. Next sentence.')
    api=event('cursor-forward',1,20);api['eventSource']='api'
    result=extract([init,api,event('suggestion-open',2,20,currentHoverIndex=0),event('suggestion-down',3,20),event('suggestion-close',4,20)])
    assert result['census']['api_cursor_excluded']==1 and result['menu_census']=={'keyboard':1}

def test_support_does_not_match_different_distance_bins():
    sessions=[dict(writer='a',census={'step':20,'jump':20},menu_census={},landings=[dict(bin='1',kind='step')]*20+[dict(bin='2',kind='jump')]*20)]
    summary,support=assemble(sessions)
    assert summary['separable_groups'] and summary['supported_writers']==0 and not summary['case_supported']

def test_missing_followup_is_censored_not_a_nonedit():
    text='First sentence. Second sentence. Third sentence.'
    init=event('system-initialize',0,len(text),currentDoc=text)
    move=event('cursor-backward',1,0)
    short=extract([init,move,event('system-finish',20,0)])
    full=extract([init,move,event('system-finish',31,0)])
    assert short['census']['followup_window_censored']==1 and not short['landings']
    assert len(full['landings'])==1 and not full['landings'][0]['edit_near']

def test_complete_source_fixture_replays(tmp_path):
    from runners.drive.cards.week4_cursor_source import execute,verify,configuration
    execute(tmp_path,{},configuration('constructed'))
    assert verify(tmp_path,{},configuration('constructed'))['complete_source_replay']
