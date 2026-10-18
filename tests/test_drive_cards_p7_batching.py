import copy

import pytest

from runners.drive.cards import timing_p7_batched as batch
from runners.drive.cards.timing_p7 import CachedScorer


class Tokenizer:
    eos_token_id = 0

    def __call__(self, text, **kwargs):
        # A boundary-sensitive token merge plus one-codepoint Unicode offsets.
        ids, offsets, i = [], [], 0
        while i < len(text):
            n = 2 if text[i:i+2] == "ab" else 1
            ids.append(127 if n == 2 else ord(text[i]) % 126 + 1)
            offsets.append((i, i+n))
            i += n
        return dict(input_ids=ids, offset_mapping=offsets)


def test_real_causal_model_matches_every_scalar_target():
    import torch
    from transformers import GPT2Config, GPT2LMHeadModel
    torch.set_num_threads(2)
    torch.manual_seed(44)
    model = GPT2LMHeadModel(GPT2Config(vocab_size=128, n_positions=1024,
                            n_embd=16, n_layer=2, n_head=2)).eval()
    pairs = [("cat ", "sat"), ("cat sat ", "here"), ("cat ", "sat"),
             ("dog ", "sat"), ("dog ", "sat"), ("A café 😀 ", "opens"),
             ("", "a"), ("a", "b"), ("ab ", "again"),
             ("xy"*550, "abc"), ("xy"*550+"abc ", "next")]
    rows = [dict(prefix=p, target=t) for p,t in pairs]
    actual, cost = batch.score_many(model, Tokenizer(), torch, rows)
    scalar = CachedScorer(model, Tokenizer(), torch)
    for row, saved in zip(rows, actual):
        expected = scalar.score(row["prefix"], row["target"])
        assert batch.compare(saved, expected) < 1e-4
        assert scalar.direct_check(row["prefix"], row["target"], saved) < 1e-4
    assert cost["forwards"] < len(rows)
    assert cost["cropped_targets"] == 2
    prepared = [batch.prepare(Tokenizer(), r["prefix"], r["target"]) for r in rows]
    membership = [b["members"] for b in batch.groups(prepared)]
    assert [0, 1, 2] in membership  # short reentry keeps its original positions
    assert not any(6 in group and 7 in group for group in membership)  # retokenization
    assert not any(9 in group and 10 in group for group in membership)  # window shifts


@pytest.mark.parametrize("change", ["id", "crop", "finite", "negative", "sum", "error", "length"])
def test_comparison_can_refuse_mutated_result(change):
    expected = dict(native_token_ids=[5,6], native_token_nll=[1.,2.],
                    surprisal_nats=3., prefix_tokens_dropped=0)
    actual = copy.deepcopy(expected)
    if change == "id": actual["native_token_ids"][0] = 7
    if change == "crop": actual["prefix_tokens_dropped"] = 1
    if change == "finite": actual["native_token_nll"][0] = float("nan")
    if change == "negative": actual["native_token_nll"][0] = -1.
    if change == "sum": actual["surprisal_nats"] = 4.
    if change == "error":
        actual["native_token_nll"][0] += .001
        actual["surprisal_nats"] = sum(actual["native_token_nll"])
    if change == "length": actual["native_token_nll"].pop()
    with pytest.raises(ValueError): batch.compare(actual, expected)


def test_missing_or_oversized_targets_refuse():
    for prefix, target in [("abc", ""), ("", "x"*1024)]:
        with pytest.raises(ValueError): batch.prepare(Tokenizer(), prefix, target)
