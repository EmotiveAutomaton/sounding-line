import copy
import numpy as np
import pytest
from runners.drive.cards import week3_fic1_galleries as m
from runners.drive.cards.timing_pmap_stats import identify


def fixture():
    rows=[];groups=[];prefixes=[]
    dictionary=dict(words=['a','b'],punctuation=['.'],character_bigrams=['ab'])
    for w in range(6):
        for g in m.GENRES:
            for h in (0,1):
                ids=[]
                for j in range(2):
                    sid=f'w{w}-{g}-{h}-{j}';ids.append(sid)
                    wc={'a':1,'b':2} if j==0 else {'a':4,'b':1};pc={'.':1} if j==0 else {}
                    rows.append(dict(session=sid,writer=f'w{w}',genre=g,half=h,
                        timestamp=h*2+j,prompt=f'{g}-{h}-{j}',typed_words=3,
                        final_words=sum(wc.values()),final_characters=80,final_accepted_characters=10,
                        final_counts=dict(word_counts=wc,punctuation_counts=pc)))
                groups.append(dict(writer=f'w{w}',genre=g,half=h,sessions=ids,full_typed_words=6))
                levels={}
                for level in m.CONSTRUCTED['levels']:
                    n=6 if level=='full' else int(level)
                    levels[level]=dict(state='prepared' if n<=6 else 'unsupported',available_words=6,
                        requested_words=None if level=='full' else n,selected_words=n if n<=6 else 0,
                        members=[dict(session=ids[0],typed_words=min(3,n))]+([dict(session=ids[1],typed_words=n-3)] if n>3 else []) if n<=6 else [],
                        features=dict(style=[(w+1)/10,1-(w+1)/10,0.],rhythm=[w+1.,w+2.,None]) if n<=6 else None)
                prefixes.append(dict(writer=f'w{w}',genre=g,half=h,levels=levels))
    return dict(rows=rows,profiles=groups,prefixes=prefixes,dictionary=dictionary)


def test_length_only_signal_removed_and_probe_does_not_fit():
    qb=np.arange(6.)[:,None];qa=qb+10
    b=3+2*qb;a=3+2*qa
    z=m.adjust(a,b,qa,qb)
    assert z['A']==z['B']==[[0.]]*6
    assert np.allclose(z['fits'][0]['coefficients'],[3,2])
    altered=m.adjust(a+7,b,qa,qb)
    assert altered['fits']==z['fits'] and np.allclose(altered['A'],7.)
    assert identify(z['A'],z['B'])['accuracy']==pytest.approx(1/6)


def test_orthogonal_person_component_survives_projection():
    q=np.arange(6.)[:,None];design=np.column_stack([np.ones(6),q])
    person=np.eye(6)-design@np.linalg.pinv(design)
    b=person+4+q*.7
    result=m.adjust(b,b,q,q)
    assert np.allclose(result['A'],person) and np.allclose(result['B'],person)
    assert identify(result['A'],result['B'])['accuracy']==1.


def test_two_nuisances_and_missing_values():
    q=np.column_stack([np.arange(8.),np.arange(8.)%2])
    b=(2+3*q[:,0]-5*q[:,1])[:,None];a=b.copy();a[0]=np.nan
    result=m.adjust(a,b,q,q)
    assert result['A'][0]==[None] and np.allclose(result['B'],0.)
    assert np.allclose(result['fits'][0]['coefficients'],[2,3,-5])
    q[1]=np.nan
    result=m.adjust(a,b,q,q)
    assert result['A'][1]==result['B'][1]==[None]
    assert result['fits'][0]['n']==7


def test_no_data_and_rank_exhausted_fits_remain_unsupported():
    q=np.arange(2.)[:,None];b=np.column_stack([q[:,0],np.full(2,np.nan)])
    result=m.adjust(b,b,q,q)
    assert result['A']==result['B']==[[None,None],[None,None]]
    assert all(f['state']=='unsupported' for f in result['fits'])


def test_constant_length_is_intercept_only_and_preserves_contrast():
    b=np.arange(6.)[:,None];q=np.ones((6,1))*10
    result=m.adjust(b,b,q,q)
    assert result['fits'][0]['rank']==1 and result['fits'][0]['residual_df']==5
    assert np.allclose(result['B'],b-b.mean())


def test_pool_final_counts_and_character_share_not_session_rates():
    f=fixture();r=m.pooled_final(f['rows'][:2],f['dictionary'])
    assert r['features']==[5/9,3/9,1/9] and r['words']==8
    assert r['log_words']==3 and r['accepted_share']==.125


def test_preparation_keeps_unsupported_lengths_and_original_population():
    r=m.prepare(fixture(),m.CONSTRUCTED)
    assert r['support']['style.full']['supported_writers']==6
    assert r['support']['style.8']['supported_writers']==0
    assert len(r['support']['style.8']['unsupported'])==6
    assert r['length_curve_common_writers']==dict(style=[],rhythm=[])
    assert not r['identification_computed'] and not r['scientific_admission']
    assert r['variants']['style.8']['creative']['state']=='unsupported'


def test_order_invariance():
    f=fixture();expected=m.prepare(f,m.CONSTRUCTED)
    for k in ('rows','profiles','prefixes'): f[k].reverse()
    assert m.prepare(f,m.CONSTRUCTED)==expected


@pytest.mark.parametrize('bad',['duplicate','missing','member','chronology','count','prefix_count','prefix_member','prompt','levels','final_count'])
def test_refuse_corruption(bad):
    f=fixture()
    if bad=='duplicate': f['rows'][0]=copy.deepcopy(f['rows'][1])
    elif bad=='missing': f['rows'].pop()
    elif bad=='member': f['profiles'][0]['sessions'][0]='absent'
    elif bad=='chronology': f['profiles'][0]['sessions'].reverse()
    elif bad=='count': f['profiles'][0]['full_typed_words']=7
    elif bad=='prefix_count': f['prefixes'][0]['levels']['2']['selected_words']=1
    elif bad=='prefix_member': f['prefixes'][0]['levels']['2']['members'][0]['session']='absent'
    elif bad=='prompt': f['rows'][2]['prompt']=f['rows'][0]['prompt']
    elif bad=='levels': del f['prefixes'][0]['levels']['2']
    elif bad=='final_count': f['rows'][0]['final_words']=99
    with pytest.raises(ValueError):m.prepare(f,m.CONSTRUCTED)


def test_infinite_and_wrong_shapes_refused():
    with pytest.raises(ValueError):m.adjust([[float('inf')]],[[1]],[[1]],[[1]])
    with pytest.raises(ValueError):m.adjust([[1]],[[1]],[[1],[2]],[[1],[2]])


def test_handler_reentry_replay_and_output_mutation(tmp_path):
    fp=tmp_path/'fixture.json';m.freeze(fp,fixture());out=tmp_path/'output';inputs=dict(fixture=str(fp))
    m.execute(out,inputs,m.CONSTRUCTED)
    hashes={p.name:m.filehash(p) for p in out.iterdir()}
    assert m.verify(out,inputs,m.CONSTRUCTED)['all_galleries_recomputed']
    m.execute(out,inputs,m.CONSTRUCTED)
    assert hashes=={p.name:m.filehash(p) for p in out.iterdir()}
    r=m.read(out/'GALLERIES.json');r['identification_computed']=True;m.atomic(out/'GALLERIES.json',r)
    with pytest.raises(ValueError,match='replay differs'):m.verify(out,inputs,m.CONSTRUCTED)
