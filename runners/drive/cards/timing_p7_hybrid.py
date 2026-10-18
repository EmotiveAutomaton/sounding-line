"""P7 causal batching with the frozen scalar scorer's exact prefix cache.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-18. NULL/ALTERNATIVE science remains
irrelevant to admission. The original grouping, identity, finite-loss and 1e-4
comparison gates remain. The prior uncached batching pilot is preserved. Cache
reuse is only across identical native causal prefixes; every target retains its
original context crop and position. Corpus execution needs separate admission.
"""
import math

from .timing_p7 import CachedScorer
from .timing_p7_batched import prepare, groups, compare


def score_many(model, tokenizer, torch, rows):
    prepared = [prepare(tokenizer, row["prefix"], row["target"]) for row in rows]
    batches = groups(prepared)
    scores = [None] * len(rows)
    scorer = CachedScorer(model, tokenizer, torch)
    for batch in batches:
        representative = next(i for i in batch["members"] if prepared[i]["ids"] == batch["ids"])
        row = rows[representative]
        scorer.score(row["prefix"], row["target"])
        if scorer.ids != batch["ids"] or len(scorer.losses) != len(batch["ids"]):
            raise ValueError("P7 hybrid cache identity mismatch")
        for member in batch["members"]:
            item = prepared[member]
            native = [scorer.losses[p] for p in item["positions"]]
            if any(x is None or not math.isfinite(x) or x < 0 for x in native):
                raise ValueError("Invalid hybrid P7 loss")
            scores[member] = dict(native_token_nll=native, surprisal_nats=sum(native),
                native_token_ids=[item["ids"][p] for p in item["positions"]],
                prefix_tokens_dropped=item["dropped"])
    return scores, dict(targets=len(rows), forwards=len(batches),
        forward_tokens=scorer.forward_tokens,
        cropped_targets=sum(p["dropped"] > 0 for p in prepared))
