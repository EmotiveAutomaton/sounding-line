"""Known-answer AT token alignment, cache and exact occurrence controls."""
import math
import pytest
from runners.drive.cards.week5_at_scoring import CausalScorer,context_rows,frozen_sessions,tokenize_target
from runners.drive.cards.timing_text import replay_words


class CharacterTokenizer:
    eos_token_id=0
    bos_token_id=0
    def __call__(self,text,**kwargs):
        return dict(input_ids=[ord(c)%31+1 for c in text],offset_mapping=[(i,i+1) for i in range(len(text))])


def test_native_cache_losses_entropy_and_crop():
    import torch
    from transformers import GPT2Config,GPT2LMHeadModel
    torch.set_num_threads(1);torch.manual_seed(4)
    model=GPT2LMHeadModel(GPT2Config(vocab_size=33,n_positions=64,n_embd=16,n_layer=1,n_head=2,bos_token_id=0,eos_token_id=0)).eval()
    scorer=CausalScorer(model,CharacterTokenizer(),torch,64)
    for prefix,target in [('a ','b'),('a b ','word'),('a ','b'),('x'*70+' ','long'),('x'*70+' long ','end')]:
        score=scorer.score(prefix,target)
        assert score['surprisal_nats']==sum(score['native_token_nll'])
        assert 0<score['entropy_nats']<=math.log(33)
        assert scorer.direct_check(prefix,target,score)<1e-4
    assert scorer.forward_tokens>0


def test_deleted_and_repeated_words_keep_distinct_identity():
    events=[dict(eventName='system-initialize',eventSource='system',eventTimestamp=0,currentDoc=''),
            dict(eventName='text-insert',eventSource='user',eventTimestamp=100,textDelta={'ops':[{'insert':'cat cat '}]}),
            dict(eventName='text-delete',eventSource='user',eventTimestamp=200,textDelta={'ops':[{'delete':4}]})]
    words=replay_words(events)['words'];rows=context_rows(events,words)
    assert [r['final_supported'] for r in rows]==[False,True]
    assert rows[1]['final_prefix']==''
    assert rows[1]['at_typing_prefix']=='cat '


def test_unicode_utf16_and_immutable_subset():
    events=[dict(eventName='system-initialize',eventSource='system',eventTimestamp=0,currentDoc='\U0001f600 '),
            dict(eventName='text-insert',eventSource='user',eventTimestamp=100,textDelta={'ops':[{'retain':3},{'insert':'caf\u00e9 '} ]})]
    words=replay_words(events)['words'];rows=context_rows(events,words)
    assert rows[0]['final_prefix']=='\U0001f600 '
    assert rows[0]['target']=='caf\u00e9'
    assert frozen_sessions(list('abcdefghij'))==frozen_sessions(list('jihgfedcba'))
    assert len(frozen_sessions(list('abcdefghij')))==2


def test_target_cannot_lose_predictive_token():
    with pytest.raises(ValueError,match='does not fit'):
        tokenize_target(CharacterTokenizer(),'','x'*64,64)
