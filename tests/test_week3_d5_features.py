from copy import deepcopy
from pathlib import Path
import math

import pytest

from runners.drive.cards import week3_d5_features as card
from runners.stage14.common import freeze, read, filehash


def fixture():
    dictionary = dict(words=['a', 'b', 'can', 'not', 'caf\u00e9'], punctuation=['!', ','], character_bigrams=['ab'])
    rows = []
    for i in range(4):
        process = dict(session='s'+str(i), writer='w'+str(i%2), prompt='p'+str(i), timestamp=i,
            word_counts={'a':2, 'deleted':1}, punctuation_counts={'!':1}, typed_words=3,
            handling={'accept':2,'edit':1,'dismiss':1,'ignore':0}, tc_timing_mode='valid',
            within_intervals=[1.,3.], onset_intervals=[2.,4.], bigram_intervals={'ab':[4.,8.]})
        rows.append(dict(**{k:process[k] for k in ('session','writer','prompt','timestamp')},end_at=i+1,
            model_share=.25, model_share_missing_reason=None, codepoints_by_origin={'typed':120},
            final_document='prompt '+('a b! '*40),
            final_typed_groups=[{'text':'can'},{'text':'not '+('a b! '*40)}],
            production_tokens=[dict(token='a',is_word=True),dict(token='deleted',is_word=True),
                               dict(token='a',is_word=True),dict(token='!',is_word=False)],process=process))
    return dict(constructed=True, units=rows, dictionary=dictionary)


def test_human_groups_do_not_join_and_production_is_distinct():
    f=fixture(); row=card.prepare(f['units'][0],f['dictionary'])
    assert row['human']['word_counts']['can']==row['human']['word_counts']['not']==1
    assert 'cannot' not in row['human']['word_counts']
    assert row['production']['word_counts']['deleted']==1 and 'deleted' not in row['human']['word_counts']
    assert row['final']['word_counts']['prompt']==1 and 'prompt' not in row['human']['word_counts']


def test_prefix_exact_length_boundary_and_missing_support():
    f=fixture(); row=card.prepare(f['units'][0],f['dictionary'])
    for n in ('32','64'): assert row['human_prefixes'][n]['words']==int(n)
    assert not row['human_prefixes']['128']['supported']
    assert card.prefix(['!', 'a', ',', 'b', '!'],2)==['!', 'a', ',', 'b']


def test_denominator_unicode_and_out_of_dictionary():
    f=fixture(); r=card.representation(['caf\u00e9','outside','!','\U0001f600'],f['dictionary'])
    assert r['words']==2 and r['punctuation']==1
    assert r['features'][4]==r['features'][5]==1/3


def test_empty_text_and_no_choices_do_not_become_zero_profiles():
    f=fixture(); u=f['units'][0]; u['final_typed_groups']=[];u['process']['handling']={}
    row=card.prepare(u,f['dictionary'])
    assert all(x is None for x in row['human']['features'])
    assert all(x is None for x in row['process']['selection'])
    assert not any(p['supported'] for p in row['human_prefixes'].values())


def test_canonical_handling_and_timing_values():
    f=fixture();row=card.prepare(f['units'][0],f['dictionary'])
    assert row['process']['selection']==[.5,.25,.25,0.]
    assert row['process']['rhythm']==[2.,3.,6.]
    f['units'][0]['process']['tc_timing_mode']='invalid'
    assert card.prepare(f['units'][0],f['dictionary'])['process']['rhythm']==[None,None,None]


@pytest.mark.parametrize('mutation', ['join','production','timing','dictionary'])
def test_bad_sources_refused(mutation):
    f=fixture();u=f['units'][0]
    if mutation=='join':u['process']['writer']='wrong'
    elif mutation=='production':u['process']['typed_words']=99
    elif mutation=='timing':u['process']['within_intervals']=[math.nan]
    else:f['dictionary']['words'].append('a')
    with pytest.raises(ValueError):card.prepare(u,f['dictionary'])


def test_handler_full_reentry_and_fresh_replay(tmp_path):
    path=tmp_path/'fixture.json';freeze(path,fixture());out=tmp_path/'output'
    inputs={'fixture':str(path)}
    card.execute(out,inputs,card.CONSTRUCTED)
    hashes={str(p):filehash(p) for p in out.rglob('*') if p.is_file()}
    card.execute(out,inputs,card.CONSTRUCTED)
    assert hashes=={str(p):filehash(p) for p in out.rglob('*') if p.is_file()}
    assert card.verify(out,inputs,card.CONSTRUCTED)['full_fresh_feature_replay']
    assert read(out/'SUMMARY.json')['sessions']==4


def test_mutated_fixture_and_duplicate_census_refused(tmp_path):
    f=fixture();f['units'][1]['session']=f['units'][0]['session']
    path=tmp_path/'fixture.json';freeze(path,f)
    with pytest.raises(ValueError, match='census'):card.execute(tmp_path/'out',{'fixture':str(path)},card.CONSTRUCTED)


def test_yield_before_any_feature(tmp_path):
    path=tmp_path/'fixture.json';freeze(path,fixture());out=tmp_path/'out';out.mkdir()
    freeze(out/'YIELD_REQUEST.json',{'reason':'test'})
    assert card.execute(out,{'fixture':str(path)},card.CONSTRUCTED)['status']=='yielded'
    assert not (out/'SUMMARY.json').exists()


def test_actual_completed_producer_and_corrupted_plan(tmp_path,monkeypatch):
    root=Path(__file__).resolve().parents[1]
    inputs=dict(source_complete=str(root/'results/phase_2_4_stage_15/raw/drive-week3-20261025/D5-inputs-h1-v2/COMPLETE.json'),
                pmap_complete=str(root/'results/phase_2_4_stage_15/raw/drive-wave-20261017-w1/PMAP-recovery/COMPLETE.json'))
    if not Path(inputs['source_complete']).exists():pytest.skip('private completed producer unavailable')
    units,dictionary,bindings=card.load(inputs,card.CONFIG)
    assert len(units)==1399 and len({u['writer'] for u in units})==61
    row=card.prepare(units[0],dictionary)
    assert row['production']['word_counts']==units[0]['process']['word_counts']
    assert row['model_share']==units[0]['model_share']
    # Corrupt only an isolated receipt; retained real source bytes are untouched.
    bad=tmp_path/'COMPLETE.json';receipt=read(inputs['source_complete'])
    receipt['outputs']['PLAN.json']='0'*64;freeze(bad,receipt)
    (tmp_path/'PLAN.json').write_bytes((Path(inputs['source_complete']).parent/'PLAN.json').read_bytes())
    with pytest.raises(ValueError):card.load(dict(inputs,source_complete=str(bad)),card.CONFIG)
