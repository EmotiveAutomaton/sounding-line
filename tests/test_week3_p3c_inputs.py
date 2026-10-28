import copy
import json
import pytest
from runners.drive.cards import week3_p3c_inputs as m


def fixture():
    units = []
    for s in range(3):
        edits = []
        for n in range(80):
            origin = ['model', 'own', 'other'][n % 3]
            edits.append(dict(ordinal=n, before='Caf\u00e9 \U0001f642 '+str(n), after='A changed sentence '+str(n),
                changed_before='Caf\u00e9', changed_after='A changed sentence', origin=origin,
                deleted_origin_counts={'accepted':1, 'typed':1} if origin=='model' else {'typed':2} if origin=='own' else {},
                accepted_owners_touched=[0] if origin=='model' else [],
                split='old-label', cosine_distance=999))
        units.append(dict(session='s'+str(s), writer='w'+str(s), prompt='p', edits=edits))
    return dict(sessions=units)


def handler(tmp_path, f=None):
    p=tmp_path/'fixture.json';p.write_text(json.dumps(f or fixture()),encoding='utf8')
    inputs=dict(fixture=str(p));config=dict(m.CONFIG,mode='constructed');out=tmp_path/'out'
    m.execute(out,inputs,config)
    return out,inputs,config


def test_preserves_all_origins_empty_unchanged_unicode():
    u=fixture()['sessions'][0];u['edits'][0]['before']='';u['edits'][1]['after']=''
    u['edits'][2]['after']=u['edits'][2]['before']
    rows=m.pairs(u)
    assert len(rows)==80 and {r['origin'] for r in rows}=={'model','own','other'}
    assert rows[0]['before']=='' and rows[1]['after']=='' and rows[2]['after']==rows[2]['before']
    assert '\u00e9' in rows[3]['before'] and '\U0001f642' in rows[3]['before']
    assert 'split' not in rows[3] and 'cosine_distance' not in rows[3]
    u['edits'].reverse();assert m.pairs(u)==rows


@pytest.mark.parametrize('bad',['duplicate','ordinal','origin','count','owner','text'])
def test_refuses_invalid_event_schema(bad):
    u=fixture()['sessions'][0]
    if bad=='duplicate':u['edits'].append(copy.deepcopy(u['edits'][0]))
    elif bad=='ordinal':u['edits'][0]['ordinal']=True
    elif bad=='origin':u['edits'][0]['origin']='own'
    elif bad=='count':u['edits'][0]['deleted_origin_counts']['typed']=-1
    elif bad=='owner':u['edits'][0]['accepted_owners_touched']=[0,0]
    else:u['edits'][0]['before']=None
    with pytest.raises(ValueError):m.pairs(u)


def test_full_handler_selection_blinding_reentry_and_replay(tmp_path):
    out,inputs,config=handler(tmp_path)
    summary=m.read(out/'SUMMARY.json');order=m.read(out/'SAMPLE_ORDER.json');blind=m.read(out/'BLIND_CALIBRATION.json')
    assert summary['counts']['pairs']==240 and summary['sessions']==3
    assert summary['calibration_pairs']==200 and summary['unique_pair_contents']==80
    assert len(set(order))==240 and all(set(r)=={'pair_id','before','after'} for r in blind)
    assert summary['labels_computed'] is False and summary['agreement_computed'] is False
    before=(out/'BLIND_CALIBRATION.json').read_bytes()
    assert m.verify(out,inputs,config)['complete_input_replay']
    m.execute(out,inputs,config);assert (out/'BLIND_CALIBRATION.json').read_bytes()==before
    f=fixture();f['sessions'].reverse()
    for u in f['sessions']:
        u['edits'].reverse()
        for e in u['edits']:e['split']='changed-legacy-label';e['cosine_distance']=-500
    other=tmp_path/'other';other.mkdir();o,_,_=handler(other,f)
    assert m.read(o/'SAMPLE_ORDER.json')==order and (o/'BLIND_CALIBRATION.json').read_bytes()==before
    blind[0]['after']='mutated';(out/'BLIND_CALIBRATION.json').write_text(json.dumps(blind))
    with pytest.raises(ValueError,match='replay'):m.verify(out,inputs,config)


def test_source_mutation_and_duplicate_session_refused(tmp_path):
    out,inputs,config=handler(tmp_path)
    f=fixture();f['sessions'][0]['edits'][0]['before']='changed'
    __import__('pathlib').Path(inputs['fixture']).write_text(json.dumps(f))
    with pytest.raises(ValueError,match='binding'):m.execute(out,inputs,config)
    f=fixture();f['sessions'].append(copy.deepcopy(f['sessions'][0]))
    p=tmp_path/'duplicate';p.mkdir()
    with pytest.raises(ValueError,match='duplicate source session'):handler(p,f)


def test_authentication_refuses_forgery_and_escape(tmp_path):
    p=tmp_path/'x';p.write_text('source')
    c=dict(status='COMPLETE',fresh_process_verified=True,outputs={'x':m.filehash(p)})
    cp=tmp_path/'COMPLETE.json';cp.write_text(json.dumps(c))
    assert m.authenticated(m.terminal(cp),'x')==p.resolve()
    with pytest.raises(ValueError):m.authenticated(m.terminal(cp),'../x')
    p.write_text('modified')
    with pytest.raises(ValueError,match='bytes'):m.authenticated(m.terminal(cp),'x')
    c['fresh_process_verified']=False;cp.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='verified'):m.terminal(cp)


def test_too_small_or_duplicate_selection_refused():
    with pytest.raises(ValueError):m.selection(['a']*240)
    with pytest.raises(ValueError):m.selection([str(n) for n in range(199)])
