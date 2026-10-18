import math

import pytest

from runners.drive.cards.timing_p7 import visible_prefixes, CachedScorer
from runners.drive.cards.timing_text import replay_words


def test_full_prefix_replay_matches_repeated_and_revised_words():
    events = [dict(eventName="system-initialize", eventTimestamp=0, currentDoc=""),
              dict(eventName="text-insert", eventTimestamp=100, eventSource="user", textDelta={"ops": [{"insert": "red red cat "}]}),
              dict(eventName="text-insert", eventTimestamp=200, eventSource="user", textDelta={"ops": [{"retain": 8}, {"delete": 3}, {"insert": "dog"}]})]
    words = replay_words(events)["words"]
    prefixes = visible_prefixes(events, words)
    assert prefixes[0] == dict(prefix="", target="red")
    assert prefixes[1] == dict(prefix="red ", target="red")
    assert any(value == dict(prefix="red red ", target="cat") for value in prefixes.values())
    assert any(value == dict(prefix="red red ", target="dog") for value in prefixes.values())


def test_real_transformer_cached_forward_matches_fresh_after_edit_and_reentry():
    import torch
    from transformers import GPT2Config, GPT2LMHeadModel
    torch.set_num_threads(2)
    torch.manual_seed(44)
    model = GPT2LMHeadModel(GPT2Config(vocab_size=128, n_positions=1024, n_embd=16, n_layer=2, n_head=2)).eval()
    class CharacterTokenizer:
        eos_token_id = 0
        def __call__(self, text, **kwargs):
            return dict(input_ids=[ord(char) for char in text], offset_mapping=[(i, i + 1) for i in range(len(text))])
    scorer = CachedScorer(model, CharacterTokenizer(), torch)
    for prefix, target in [("cat ", "sat"), ("cat sat ", "here"), ("dog ", "sat"), ("dog ", "sat")]:
        actual = scorer.score(prefix, target)
        ids = torch.tensor([[0] + [ord(char) for char in prefix + target]])
        with torch.inference_mode():
            logits = model(ids, use_cache=False).logits[0, :-1]
            losses = torch.nn.functional.cross_entropy(logits, ids[0, 1:], reduction="none").tolist()
        expected = losses[len(prefix):]
        assert actual["native_token_nll"] == pytest.approx(expected, abs=1e-6)
        assert scorer.direct_check(prefix, target, actual) < 1e-6
    overflow = scorer.score("x" * 1100, "abc")
    assert overflow["prefix_tokens_dropped"] > 0
    assert scorer.direct_check("x" * 1100, "abc", overflow) < 1e-4


def test_missing_produced_token_refuses_prefix_guess():
    events = [dict(eventName="system-initialize", eventTimestamp=0, currentDoc="not typed")]
    with pytest.raises(ValueError, match="locate"):
        visible_prefixes(events, [dict(index=0, token="missing", ordinal=0, completed_ordinal=0, length=7)])


def test_repeated_word_finished_in_later_delta_uses_second_occurrence():
    events = [dict(eventName="system-initialize", eventTimestamp=0, currentDoc="\n"),
              dict(eventName="text-insert", eventTimestamp=100, eventSource="user", textDelta={"ops": [{"insert": "red re"}]}),
              dict(eventName="text-insert", eventTimestamp=200, eventSource="user", textDelta={"ops": [{"retain": 6}, {"insert": "d "}]})]
    words = replay_words(events)["words"]
    prefixes = visible_prefixes(events, words)
    assert len(words) == 2
    assert prefixes[1] == dict(prefix="red ", target="red")
