import copy
import hashlib
import runpy
from pathlib import Path
import pytest
from runners.drive.cards import week3_fic1_features as m


def fixture():
    f=runpy.run_path(str(Path(__file__).with_name('test_week3_fic1_inputs.py')))['fixture']()
    units,profiles,_,_=m.source.prepare(f['words'],f['documents'],f['matches'],m.source.CONSTRUCTED)
    rows=[]
    for w in f['words']:
        rows.append(dict(**{k:w[k] for k in m.IDENTITY},typed_words=3,
            word_counts={'caf\u00e9':1,'one':1,'extra':1},punctuation_counts={'.':1},
            within_intervals=[0.,2.,4.],onset_intervals=[1.,3.],
            bigram_intervals={'ca':[.5,1.5],'outside':[8.]},tc_timing_mode='valid'))
    return dict(units=units,profiles=profiles,pmap_rows=rows,
                dictionary=dict(words=['caf\u00e9','extra'],punctuation=['.'],character_bigrams=['ca','missing']))


def prepare(f): return m.prepare(f['units'],f['profiles'],f['pmap_rows'],f['dictionary'],m.CONSTRUCTED)


def test_exact_features_and_untrimmed_denominators():
    rows,profiles=prepare(fixture());r=rows[0]
    assert r['typed_words']==3 and r['matched_typed_words']==2
    assert r['features']['style']==[.25,.25,.25]  # Outside-dictionary 'one' stays in denominator.
    assert r['features']['rhythm']==[2.,2.,1.,None]
    assert r['features']['final_style']==[.25,0.,.25]  # Mixed prompt/AI words stay.
    assert r['final_words']==3 and r['accepted_share']==2/10
    assert r['production']['bigram_intervals']['outside']==[8.]
    assert len(rows)==len(profiles)==12
    # Independently implemented historical complete-session feature functions.
    from runners.drive.cards.week_genre_compare import profile
    from runners.drive.cards.week3_identification_inputs import final_style
    f=fixture()
    assert profile([f['pmap_rows'][0]],f['dictionary'])=={k:r['features'][k] for k in ('style','rhythm')}
    assert final_style(f['units'][0]['final_document'],f['dictionary'])==r['features']['final_style']


def test_missing_timing_is_not_zero_and_original_intervals_remain():
    f=fixture();f['pmap_rows'][0]['tc_timing_mode']='invalid'
    r=prepare(f)[0][0];assert r['features']['rhythm']==[None]*4
    assert r['production']['within_intervals']==[0.,2.,4.]
    f['pmap_rows'][0]['tc_timing_mode']='valid';f['pmap_rows'][0]['within_intervals']=[]
    assert prepare(f)[0][0]['features']['rhythm'][0] is None


def test_empty_final_document_remains_missing():
    f=fixture();u=f['units'][0];u['final_document']=dict(text='',textSha256=hashlib.sha256(b'').hexdigest(),provenance=[])
    u['final_characters']=u['final_accepted_characters']=0
    next(g for g in f['profiles'] if g['sessions']==[u['session']])['final_characters']=0
    r=prepare(f)[0][0];assert r['features']['final_style']==[None]*3 and r['accepted_share'] is None


@pytest.mark.parametrize('bad',['duplicate','missing','identity','count','timing','nonfinite','profile','duplicate_profile','half','dictionary','hash','provenance'])
def test_refuses_corruption(bad):
    f=fixture()
    if bad=='duplicate': f['pmap_rows'].append(copy.deepcopy(f['pmap_rows'][0]))
    elif bad=='missing': f['units'].pop()
    elif bad=='identity': f['pmap_rows'][0]['writer']='wrong'
    elif bad=='count': f['pmap_rows'][0]['word_counts']['extra']=0
    elif bad=='timing': f['pmap_rows'][0]['within_intervals']=[-1.]
    elif bad=='nonfinite': f['pmap_rows'][0]['onset_intervals']=[float('nan')]
    elif bad=='profile': f['profiles'][0]['full_typed_words']=999
    elif bad=='duplicate_profile': f['profiles'].append(copy.deepcopy(f['profiles'][0]))
    elif bad=='half': f['profiles'][0]['half']=True
    elif bad=='dictionary': f['dictionary']['words'].append('extra')
    elif bad=='hash': f['units'][0]['final_document']['text']+='x'
    elif bad=='provenance': f['units'][0]['final_accepted_characters']=0
    with pytest.raises(ValueError): prepare(f)


def test_order_invariance():
    f=fixture();expected=prepare(f)
    for name in ('units','profiles','pmap_rows'): f[name].reverse()
    assert prepare(f)==expected


def test_full_handler_reentry_fresh_replay_and_output_mutation(tmp_path):
    f=tmp_path/'fixture.json';m.freeze(f,fixture());inputs=dict(fixture=str(f));out=tmp_path/'output'
    m.execute(out,inputs,m.CONSTRUCTED)
    hashes={str(p.relative_to(out)):m.filehash(p) for p in out.rglob('*') if p.is_file()}
    assert m.verify(out,inputs,m.CONSTRUCTED)['all_features_recomputed']
    m.execute(out,inputs,m.CONSTRUCTED)
    assert hashes=={str(p.relative_to(out)):m.filehash(p) for p in out.rglob('*') if p.is_file()}
    names=m.read(out/'FEATURE_NAMES.json');names['style'][0]='wrong';m.atomic(out/'FEATURE_NAMES.json',names)
    with pytest.raises(ValueError,match='replay differs'):m.verify(out,inputs,m.CONSTRUCTED)


def test_changed_fixture_and_unknown_config_refused(tmp_path):
    f=tmp_path/'fixture.json';m.freeze(f,fixture());inputs=dict(fixture=str(f));out=tmp_path/'output'
    m.execute(out,inputs,m.CONSTRUCTED);changed=m.read(f);changed['pmap_rows'][0]['within_intervals']=[0.,9.];m.atomic(f,changed)
    with pytest.raises(ValueError,match='replay differs'):m.verify(out,inputs,m.CONSTRUCTED)
    with pytest.raises(ValueError):m.load(inputs,m.CONFIG)
    with pytest.raises(ValueError):m.load({},dict(m.CONFIG,writers=23))


def test_sealed_corpus_adapter_and_tamper_refusal(tmp_path):
    f=fixture();sr=tmp_path/'source';pr=tmp_path/'pmap'
    def seal(root):
        m.freeze(root/'COMPLETE.json',dict(status='COMPLETE',fresh_process_verified=True,
            outputs={p.relative_to(root).as_posix():m.filehash(p) for p in root.rglob('*') if p.is_file()}))
    m.freeze(pr/'PLAN.json',dict(module='runners.drive.cards.timing_pmap_recovery'))
    for r in f['pmap_rows']:m.gzip_equal(pr/'output/sessions'/(r['session']+'.json.gz'),r)
    m.freeze(pr/'output/STYLE_DICTIONARY.json',f['dictionary']);seal(pr)
    m.freeze(sr/'PLAN.json',dict(module='runners.drive.cards.week3_fic1_inputs',config=m.source.CONFIG,
        inputs=dict(pmap_completion=str(pr/'COMPLETE.json'))))
    index=[]
    for u in f['units']:
        rel='sessions/'+u['session']+'.json';m.freeze(sr/'output'/rel,u)
        index.append(dict(session=u['session'],file=rel,sha256=m.filehash(sr/'output'/rel)))
    m.freeze(sr/'output/SESSION_INDEX.json',index);m.freeze(sr/'output/PROFILES.json',f['profiles'])
    m.freeze(sr/'output/SUMMARY.json',dict(unchanged_cohort_and_prompt_halves=True,all_selected_occurrences_retained=True));seal(sr)
    inputs=dict(source_completion=str(sr/'COMPLETE.json'),pmap_completion=str(pr/'COMPLETE.json'))
    uu,gg,pp,dd,_=m.load(inputs,m.CONFIG)
    assert sorted(u['session'] for u in uu)==sorted(u['session'] for u in f['units']) and dd==f['dictionary']
    assert m.prepare(uu,gg,pp,dd,m.CONSTRUCTED)==prepare(f)
    m.atomic(sr/'output/SUMMARY.json',dict(unchanged_cohort_and_prompt_halves=False))
    with pytest.raises(ValueError,match='dependency changed'):m.load(inputs,m.CONFIG)
