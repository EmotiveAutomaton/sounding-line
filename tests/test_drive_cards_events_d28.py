import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
from runners.drive.cards import events_d28 as card


def row(key, distance, count, session='s', writer='w', order=0):
    return dict(key=key, writer=writer, session=session, session_order=order, menu_size=2,
        handling='accept', switches=count, dissimilarity=distance, visible_seconds=count + 1,
        hover_events=count + 1, keyboard_events=0)


@pytest.mark.parametrize('sign,state', [(0, 'null'), (1, 'positive'), (-1, 'negative')])
def test_known_null_positive_reverse(sign, state):
    units = []
    for w in range(8):
        rows = [row(str(i), i / 9, 5 if sign == 0 else 11 - i if sign == 1 else i,
                    session=f's{i//3}', writer=f'w{w}', order=i//3) for i in range(12)]
        units.append(dict(writer=f'w{w}', rows=rows, exclusions=[]))
    result = card.summarize(units, card.CONFIG)
    assert result['primary']['state'] == state
    if sign == 0:
        assert result['primary']['effect'] == 0
    else:
        assert result['primary']['effect'] * sign > 0


def test_ties_missing_support_and_equal_session_weight():
    constant = [row(str(i), 1., i) for i in range(10)]
    assert card.tail_contrast(constant)['reason'] == 'quintile boundaries coincide'
    assert not card.tail_contrast([row(str(i), float(i), i) for i in range(4)])['eligible']
    assert card.mean_sessions([row(str(i), 0, 10, session='a') for i in range(20)] + [row('last', 0, 0, session='b')], 'switches') == 5
    assert card.summarize([], card.CONFIG)['primary']['state'] == 'invalid'


def test_exact_hover_switches_reopen_and_unknown_pointer():
    event = dict(menu_size=2, hover_sequence=[dict(ordinal=o, position=p) for o, p in [(2,0),(3,0),(4,1),(12,0),(13,1)]],
        visible_episodes=[dict(start=1,end=5),dict(start=11,end=15)])
    assert card.switches(event) == 2
    assert card.switches(dict(event, hover_sequence=[])) == 0
    bad = copy.deepcopy(event); bad['hover_sequence'][0]['position'] = 4
    with pytest.raises(ValueError, match='invalid hover target'):
        card.switches(bad)
    bad = copy.deepcopy(event); bad['hover_sequence'].append(dict(ordinal=20, position=1))
    with pytest.raises(ValueError, match='outside'):
        card.switches(bad)


def test_cosine_distance_and_reliability_known_answers():
    assert card.dissimilarity([[1,0],[-1,0]]) == 2
    assert card.dissimilarity([[1,0],[1,0]]) == 0
    assert card.dissimilarity([[1,0],[0,1]]) == 1
    with pytest.raises(ValueError, match='invalid content'):
        card.dissimilarity([[2,0],[0,1]])
    for sign, state in ((1,'positive'),(-1,'negative')):
        result = card.reliability([[i, sign * i] for i in range(12)], card.CONFIG)
        assert result['state'] == state
        assert result['effect'] == pytest.approx(sign)
    assert card.reliability([[i,1] for i in range(12)], card.CONFIG)['state'] == 'invalid'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf8')


def full_fixture(root, writers=8):
    sessions, records, hover, vectors = [], [], [], []
    for wi in range(writers):
        for si in range(4):
            menus = []
            for mi in range(5):
                number = si * 5 + mi
                key, session, writer = f'w{wi}s{si}m{mi}', f'w{wi}s{si}', f'w{wi}'
                angle = .01 + number * np.pi / 20
                a, b = np.zeros(384), np.zeros(384)
                a[0] = 1; b[0] = np.cos(angle); b[1] = np.sin(angle)
                position = len(vectors); vectors.extend([a,b])
                records.append(dict(key=key, session=session, writer=writer, options=[position,position+1]))
                menus.append(dict(key=key, session=session, writer=writer, menu=['a','b'], handling='accept', open_at=number*100))
                count = 5 - number//4 + wi
                events = [dict(ordinal=j+2, position=j%2, seconds=j+1) for j in range(count+1)]
                hover.append(dict(key=key, session=session, writer=writer, menu_size=2, handling='accept',
                    hover_target_complete=True, dwell_observed=True, dwell_seconds=count+2,
                    hover_sequence=events, keyboard_sequence=[], visible_episodes=[dict(start=1,end=count+4,observed_end=True)]))
            sessions.append(dict(session=f'w{wi}s{si}',writer=f'w{wi}',timestamp=si*1000,end_at=si*1000+999,rows=menus))
    paths = dict(sessions=str(root/'SESSIONS.json'),content_records=str(root/'content/RECORDS.json'),
        content_vectors=str(root/'content/VECTORS.npy'),content_complete=str(root/'content/COMPLETE.json'),
        d6_rows=str(root/'d6/output/ROWS.json'),d6_inputs=str(root/'d6/output/INPUTS.json'),d6_completion=str(root/'d6/COMPLETE.json'))
    write(Path(paths['sessions']),sessions); write(Path(paths['content_records']),records)
    np.save(paths['content_vectors'],np.asarray(vectors))
    write(Path(paths['content_complete']),dict(status='COMPLETE',outputs={Path(paths[k]).name:card.filehash(paths[k]) for k in ('content_records','content_vectors')}))
    write(Path(paths['d6_rows']),hover)
    write(Path(paths['d6_inputs']),dict(paths={'sessions':paths['sessions']},pins={paths['sessions']:card.filehash(paths['sessions'])}))
    write(Path(paths['d6_completion']),dict(status='COMPLETE',fresh_process_verified=True,
        outputs={Path(paths[k]).relative_to(root/'d6').as_posix():card.filehash(paths[k]) for k in ('d6_rows','d6_inputs')}))
    return paths


def test_source_exclusion_census(tmp_path):
    inputs = full_fixture(tmp_path)
    data = card.source(inputs)
    first = next(iter(data[3].values()))
    first['hover_target_complete'] = False
    second = list(data[3].values())[1]; second['dwell_observed'] = False
    third = list(data[3].values())[2]; third['handling'] = 'ignore'; data[1][third['key']]['handling']='ignore'
    unit = card.extract_writer('w0', *data)
    assert len(unit['rows']) == 17 and len(unit['exclusions']) == 3
    assert {r['reason'] for r in unit['exclusions']} == {'unknown hover target','censored visible episode','no observed handling decision'}


def test_actual_handler_resume_and_fresh_source_replay(tmp_path, monkeypatch):
    inputs = full_fixture(tmp_path/'source')
    output = tmp_path/'output'
    original = card.extract_writer
    calls = []
    def extract(*args):
        calls.append(args[0])
        result = original(*args)
        if len(calls)==1:
            write(output/'YIELD_REQUEST.json',{})
        return result
    monkeypatch.setattr(card,'extract_writer',extract)
    assert card.execute(output,inputs,card.CONFIG)['status']=='yielded'
    (output/'YIELD_REQUEST.json').unlink()
    result=card.execute(output,inputs,card.CONFIG)
    assert len(calls)==8 and result['primary']['state']=='positive'
    assert card.verify(output,inputs,card.CONFIG)['verified']
    args=tmp_path/'args.json'; write(args,dict(output=str(output),inputs=inputs,config=card.CONFIG))
    script="import json,sys; from pathlib import Path; from runners.drive.cards.events_d28 import verify; a=json.load(open(sys.argv[1])); print(json.dumps(verify(Path(a['output']),a['inputs'],a['config'])))"
    child=subprocess.run([sys.executable,'-B','-c',script,str(args)],capture_output=True,text=True,env=dict(os.environ,PYTHONHASHSEED='994'),check=True)
    assert json.loads(child.stdout)['verified']
    with pytest.raises(ValueError,match='never rerun'):
        card.execute(output,inputs,card.CONFIG)
    Path(inputs['d6_rows']).write_text('[]',encoding='utf8')
    with pytest.raises(ValueError,match='input changed'):
        card.verify(output,inputs,card.CONFIG)

