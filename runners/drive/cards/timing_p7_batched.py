"""Causal-prefix batching for P7; frozen scalar scorer remains unchanged.

DESIGN CHECK: LESSONS 3-5 reread 2026-10-18. Scientific NULL/ALTERNATIVE
have no bearing on this engineering gate. Only identical native causal prefixes
share a forward; edits, token-boundary changes and shifted context windows split.
Every target keeps the original positions, 1024-token crop and summed losses.
Nonfinite/negative losses or any >1e-4 difference refuse, never widen tolerance.
This module alone does not admit a corpus run.
"""
from __future__ import annotations

import math


def prepare(tokenizer, prefix, target):
    encoded = tokenizer(prefix + target, add_special_tokens=False, return_offsets_mapping=True)
    full = [tokenizer.eos_token_id] + encoded["input_ids"]
    dropped = max(0, len(full) - 1024)
    positions = [i + 1 - dropped for i, (a, b) in enumerate(encoded["offset_mapping"])
                 if b > len(prefix) and a < len(prefix + target)]
    if not positions or min(positions) <= 0:
        raise ValueError("P7 target missing or exceeds context")
    return dict(ids=full[dropped:], positions=positions, dropped=dropped)


def groups(prepared):
    """Consecutive chains only; identical IDs imply identical position IDs.

    The largest sequence is only a computational carrier. Causal masking means
    no later token enters an earlier target's conditional distribution. A shifted
    window is never credited as the old prefix, even if source text overlaps.
    """
    result = []
    for number, row in enumerate(prepared):
        ids = row["ids"]
        if result:
            previous = result[-1]["ids"]
            common = min(len(previous), len(ids))
            if previous[:common] == ids[:common]:
                result[-1]["members"].append(number)
                if len(ids) > len(previous):
                    result[-1]["ids"] = ids
                continue
        result.append(dict(ids=ids, members=[number]))
    return result


def score_many(model, tokenizer, torch, rows):
    prepared = [prepare(tokenizer, row["prefix"], row["target"]) for row in rows]
    batches = groups(prepared)
    scores = [None] * len(rows)
    for batch in batches:
        tensor = torch.tensor([batch["ids"]], dtype=torch.long, device="cpu")
        with torch.inference_mode():
            output = model(input_ids=tensor, use_cache=False)
            losses = torch.nn.functional.cross_entropy(
                output.logits[0, :-1].float(), tensor[0, 1:], reduction="none").tolist()
        for member in batch["members"]:
            item = prepared[member]
            native = [losses[p - 1] for p in item["positions"]]
            if any(not math.isfinite(x) or x < 0 for x in native):
                raise ValueError("Invalid batched P7 loss")
            scores[member] = dict(native_token_nll=native, surprisal_nats=sum(native),
                                  native_token_ids=[item["ids"][p] for p in item["positions"]],
                                  prefix_tokens_dropped=item["dropped"])
    return scores, dict(targets=len(rows), forwards=len(batches),
                        forward_tokens=sum(len(b["ids"]) for b in batches),
                        cropped_targets=sum(p["dropped"] > 0 for p in prepared))


def compare(actual, expected):
    if (actual["native_token_ids"] != expected["native_token_ids"]
            or actual["prefix_tokens_dropped"] != expected["prefix_tokens_dropped"]
            or len(actual["native_token_nll"]) != len(expected["native_token_nll"])):
        raise ValueError("P7 batched/reference identity mismatch")
    for value in (actual, expected):
        losses = value["native_token_nll"]
        if (not losses or any(not math.isfinite(x) or x < 0 for x in losses)
                or value["surprisal_nats"] != sum(losses)):
            raise ValueError("P7 batched/reference invalid losses")
    error = max(abs(a - b) for a, b in zip(actual["native_token_nll"], expected["native_token_nll"]))
    if error > 1e-4:
        raise ValueError("P7 batched/reference numerical mismatch")
    return error
