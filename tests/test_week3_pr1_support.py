import copy
import json
import pytest
from runners.drive.cards import week3_pr1_support as m


def fixture(writers=2):
    f = dict(dwell=[], sessions={})
    for i in range(writers):
        sid, writer = f's{i}', f'w{i}'
        f['sessions'][sid] = dict(rows=[])
        for j in range(30):
            key = f'{sid}-{j:02d}'
            f['dwell'].append(dict(key=key, session=sid, writer=writer, handling='dismiss', menu_size=1,
                hovered=[False], hover_target_complete=True, dwell_seconds=j+1, dwell_observed=True,
                visible_episodes=[dict(seconds=j+1, observed_end=True)]))
            f['sessions'][sid]['rows'].append(dict(key=key, session=sid, writer=writer, prompt='p',
                handling='dismiss', options=['offer'], resolution_ordinal=0,
                window='word '*50, window_indices=list(range(50)), window_ordinals=[[k+1, k+2] for k in range(50)]))
    return f


def joined(f):
    return sum([m.join_session([r for r in f['dwell'] if r['session'] == sid], u['rows']) for sid, u in f['sessions'].items()], [])


def test_known_support_boundary_and_invariance():
    f=fixture(25); rows=joined(f); v=m.assemble(rows,False)
    assert v['summary']['literal_minimum_met'] and v['summary']['disjoint_minimum_met']
    assert v['summary']['counts']['examined_with_window']==250
    assert v['summary']['counts']['fast_with_window']==250
    assert v==m.assemble(list(reversed(rows)),False)
    assert not m.assemble(joined(fixture(24)),False)['summary']['literal_minimum_met']


def test_hover_overlap_censoring_and_missing_window_retained():
    f=fixture(1);f['dwell'][0]['hover_target_complete']=False
    f['dwell'][29].update(dwell_observed=False,visible_episodes=[dict(seconds=30,observed_end=False)])
    f['sessions']['s0']['rows'][1].update(window=None,window_indices=None,window_ordinals=None)
    v=m.assemble(joined(f),False);r={x['key']:x for x in v['rows']}
    assert r['s0-00']['logged_hover'] and r['s0-00']['overlap_with_window']
    assert not r['s0-29']['upper_tercile'] and not r['s0-01']['fast_with_window']
    assert v['summary']['menus']==30


def test_ties_not_broken_by_identifier():
    f=fixture(1)
    for d in f['dwell']:d.update(dwell_seconds=1,visible_episodes=[dict(seconds=1,observed_end=True)])
    v=m.assemble(joined(f),False)
    assert v['summary']['counts']['tercile_tie_overlap']==30
    assert v['summary']['counts']['overlap_with_window']==30
    assert v['writers'][0]['literal_support'] and not v['writers'][0]['disjoint_support']


@pytest.mark.parametrize('mutation',['missing','duplicate','identity','duration','clock','window'])
def test_join_refuses_defects(mutation):
    f=fixture(1);a=f['dwell'];b=f['sessions']['s0']['rows']
    if mutation=='missing':b.pop()
    elif mutation=='duplicate':a.append(copy.deepcopy(a[0]))
    elif mutation=='identity':b[0]['writer']='wrong'
    elif mutation=='duration':a[0]['dwell_seconds']=float('nan')
    elif mutation=='clock':b[0]['window_ordinals'][0][0]=0
    else:b[0]['window_indices'].pop()
    with pytest.raises(ValueError):m.join_session(a,b)


def test_handler_replay_reentry_and_mutation(tmp_path):
    p=tmp_path/'fixture.json';p.write_text(json.dumps(fixture()),encoding='utf8')
    output=tmp_path/'out';inputs=dict(fixture=str(p));config=dict(m.CONFIG,mode='constructed')
    m.execute(output,inputs,config); before=(output/'CENSUS.json').read_bytes()
    assert m.verify(output,inputs,config)['complete_input_replay']
    m.execute(output,inputs,config);assert (output/'CENSUS.json').read_bytes()==before
    p.write_text(json.dumps(fixture(3)),encoding='utf8')
    with pytest.raises(ValueError,match='binding'):m.execute(output,inputs,config)
    p.write_text(json.dumps(fixture()),encoding='utf8')
    v=json.loads(before);v['summary']['menus']+=1;(output/'CENSUS.json').write_text(json.dumps(v),encoding='utf8')
    with pytest.raises(ValueError,match='replay'):m.verify(output,inputs,config)


def test_completion_authentication(tmp_path):
    p=tmp_path/'x';p.write_text('source');c=dict(status='COMPLETE',fresh_process_verified=True,outputs={'x':m.filehash(p)})
    cp=tmp_path/'COMPLETE.json';cp.write_text(json.dumps(c))
    assert m.authenticated(m.terminal(cp),'x')==p.resolve()
    p.write_text('changed')
    with pytest.raises(ValueError,match='bytes'):m.authenticated(m.terminal(cp),'x')
    c['fresh_process_verified']=False;cp.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='verified'):m.terminal(cp)
