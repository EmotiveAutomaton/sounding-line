"""Known-answer path/normalization diagnostics; no native model/corpus call."""
import math
import pytest

from runners.drive.cards import timing_word_paths as paths
from runners.drive.cards.timing_p6 import KneserNey
from runners.drive.cards.timing_d33 import cache,cache_probability


def test_all_byte_segmentations_independent_count():
    index=paths.BytePaths({0:b'a',1:b'b',2:b'ab',3:b'aba',4:b'ba'})
    value=index.describe(b'aba',limit=20)
    assert value['path_count']==4
    assert {tuple(p) for p in value['paths']}=={(0,1,0),(2,0),(0,4),(3,)}
    assert value['enumeration_complete']


def test_partial_enumeration_keeps_exact_count():
    value=paths.BytePaths({0:b'a',1:b'aa',2:b'aaa'}).describe(b'a'*10,limit=3)
    independent=[1]
    for n in range(1,11):independent.append(sum(independent[n-k] for k in (1,2,3) if n>=k))
    assert value['path_count']==independent[10] and len(value['paths'])==3
    assert not value['enumeration_complete']


def test_casefold_multi_character_and_apostrophes():
    inverse={'s':['S','s'],'ss':['\u00df','\u1e9e'],"'":["'"],'a':['A','a'],
        'i':['I','i'],'i\u0307':['\u0130']}
    assert set(paths.casefold_aliases('ss',inverse)['aliases'])=={'SS','Ss','sS','ss','\u00df','\u1e9e'}
    assert paths.casefold_aliases('i\u0307',inverse)['aliases']==['\u0130']
    assert paths.casefold_aliases("'a",inverse)['total_aliases']==0
    assert paths.casefold_aliases("a''a",inverse)['total_aliases']==0
    assert paths.casefold_aliases("a'a",inverse)['total_aliases']==4


def test_casefold_bound_does_not_drop_aliases_from_count():
    result=paths.casefold_aliases('a'*12,{'a':['A','a']},limit=5)
    assert result['total_aliases']==4096 and len(result['aliases'])==5
    assert not result['enumeration_complete']


def test_utf8_partial_tokens_are_kept_until_complete_byte_path():
    index=paths.BytePaths({0:b'\xc3',1:b'\xa9',2:'\u00e9'.encode('utf8')})
    r=index.describe('\u00e9'.encode('utf8'))
    assert r['path_count']==2 and {tuple(p) for p in r['paths']}=={(0,1),(2,)}


def test_empty_token_or_non_word_refuses():
    with pytest.raises(ValueError,match='empty'):paths.BytePaths({0:b''})
    with pytest.raises(ValueError,match='one original'):paths.describe_word('two words',paths.BytePaths({0:b'a'}),{'a':['a']})


def test_native_byte_alphabet_roundtrip_including_space_and_utf8():
    vocab={'a':0,'\u0120':1,'\u00c3':2,'\u00a9':3,'<|endoftext|>':4}
    assert paths.byte_vocabulary(vocab,eos=4)=={0:b'a',1:b' ',2:b'\xc3',3:b'\xa9'}


def test_population_unknown_event_differs_from_personal_literal_event():
    model=KneserNey([['common','common','rarealpha'],['common','rarebeta']])
    assert model.lookup('rarealpha')==model.lookup('rarebeta')=='<unk>'
    p=model.score('rarealpha',[])
    assert p==model.score('rarebeta',[]) and p>0
    own=cache([dict(end_at=0,training_sequences=[['rarealpha','rarealpha']])],1)
    a=cache_probability(dict(token='rarealpha',context=[]),own,p)
    b=cache_probability(dict(token='rarebeta',context=[]),own,p)
    assert a>b
    # This is a retained mismatch witness, never permission to replace events.


def test_native_path_cost_uniform_known_answer_and_overflow():
    import torch
    from types import SimpleNamespace
    torch.set_num_threads(1)
    class Uniform:
        def __call__(self,input_ids,use_cache):
            return SimpleNamespace(logits=torch.zeros((1,input_ids.shape[1],4),dtype=torch.float32))
    result=paths.native_path_cost(Uniform(),torch,[0,1],[[2],[1,2]])
    assert result['forwards']==2 and result['forward_tokens']==7
    assert all(v==pytest.approx(math.log(4),abs=1e-7) for r in result['paths'] for v in r['native_token_nll'])
    assert result['scientific_word_scores'] is False
    with pytest.raises(ValueError,match='overflow'):paths.native_path_cost(Uniform(),torch,[0]*1024,[[1]])


def test_cost_design_retains_exact_context_overlap_and_overflow(monkeypatch):
    from runners.drive.cards import timing_word_event_native as native
    pieces={0:b' ',1:b'a',2:b'b',3:b' ab'};index=paths.BytePaths(pieces)
    monkeypatch.setattr(native,'prepare',lambda *_:dict(ids=[99]*1023+[3],positions=[1023],dropped=7))
    row=dict(prefix='unchanged',target='ab',expected=dict(native_token_nll=[.5]))
    design=native.cost_design(row,None,index,pieces,native.CONFIG)
    assert design['prefix_ids']==[99]*1023 and design['original_prefix_tokens_dropped']==7
    assert design['paths']==[[3]] and design['overflow_paths']==[[0,1,2]]
    assert design['total_exact_spelling_paths']==2 and design['sample_complete']
    native.check_cost(dict(paths=[dict(tokens=[3],native_token_nll=[.50001])]),design)
    with pytest.raises(ValueError,match='canonical native loss'):native.check_cost(dict(paths=[dict(tokens=[3],native_token_nll=[.501])]),design)


def test_fixed_native_selection_does_not_consult_values():
    from runners.drive.cards import timing_word_event_native as native
    rows=[dict(domain=d,is_word=w,loss=-999) for d in ('typed','jester') for w in (False,True,True,True,False)]
    assert native.native_selection(rows)==[6,8,1,3]
    for row in rows:row['loss']=1e9
    assert native.native_selection(rows)==[6,8,1,3]


def test_independent_native_decoder_agreement_and_refusal():
    from runners.drive.cards import timing_word_event_native as native
    pieces={0:b' a',1:b'\xc3',2:b'\xa9'}
    class Decoder:
        def decode(self,ids,**kwargs):return b''.join(pieces[i] for i in ids).decode('utf8',errors='replace')
    assert native.validate_decoder(Decoder(),pieces)==3
    with pytest.raises(ValueError,match='decoder'):native.validate_decoder(Decoder(),{**pieces,0:b'wrong'})
