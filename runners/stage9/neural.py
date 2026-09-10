"""Complete continuation scoring, shared by training validation and model service.

DESIGN CHECK: LESSONS sections 3, 4 and 5; CONTROLS section 6.
NULL: equal continuation log probabilities normalize uniformly; absent components fail.
ALTERNATIVE: a late winning option wins at all supported counts and input permutations.
gates: no input truncation or invalid-component fallback; bands: complete or invalid.
Only the inference server/trainer imports this module; capsules use a restricted client.
"""
import math


def sequence_scores(model, tok, prefix, continuations, batch_size=4, max_context=8192, max_support=128):
    import torch
    if not continuations or len(continuations) > max_support:
        raise ValueError("support outside frozen envelope")
    pre = tok(prefix, add_special_tokens=True, return_tensors="pt").input_ids[0]
    if len(pre) == 0:
        raise ValueError("causal scoring requires a nonempty prefix")
    tails = [tok(c, add_special_tokens=False, return_tensors="pt").input_ids[0] for c in continuations]
    if any(len(c) == 0 or len(pre) + len(c) > max_context for c in tails):
        raise ValueError("empty continuation or context outside frozen envelope; no truncation")
    device = next(model.parameters()).device
    result = []
    index = 0
    effective_batch = batch_size
    while index < len(tails):
        chunk = tails[index:index + effective_batch]
        length = len(pre) + max(map(len, chunk))
        ids = torch.full((len(chunk), length), tok.pad_token_id, dtype=torch.long, device=device)
        attention = torch.zeros_like(ids)
        for i, tail in enumerate(chunk):
            seq = torch.cat([pre, tail]).to(device)
            ids[i, :len(seq)] = seq
            attention[i, :len(seq)] = 1
        try:
            with torch.no_grad():
                keep = length - len(pre) + 1
                logits = model(input_ids=ids, attention_mask=attention, logits_to_keep=keep).logits.float()
                log_probs = torch.log_softmax(logits[:, :-1], dim=-1)
                actual = ids[:, len(pre):]
                selected = log_probs.gather(2, actual.unsqueeze(-1)).squeeze(-1)
                values = [float(selected[i, :len(tail)].sum()) for i, tail in enumerate(chunk)]
            if any(not math.isfinite(v) or v > 0 for v in values):
                raise ValueError("invalid continuation likelihood")
            result.extend(values)
            index += len(chunk)
        except torch.cuda.OutOfMemoryError:
            if effective_batch == 1:
                raise
            effective_batch = max(1, effective_batch // 2)
            torch.cuda.empty_cache()
    return {"logprobs": result, "prompt_tokens": len(pre), "continuation_tokens": [len(t) for t in tails],
            "effective_batch": effective_batch, "semantics": "sum_log_probability"}


def choice_validation(model, tok, rows):
    scores = []
    model.eval()
    for row in rows:
        options = row["options"]
        if row["truth"] not in options:
            raise ValueError("validation truth outside candidate support")
        keys = sorted(options)
        values = sequence_scores(model, tok, row["prefix"], [options[k] for k in keys])["logprobs"]
        maximum = max(values)
        logz = maximum + math.log(math.fsum(math.exp(v - maximum) for v in values))
        scores.append(values[keys.index(row["truth"])] - logz)
    if not scores:
        raise ValueError("empty next-action validation")
    return {"n": len(scores), "mean_next_action_log_score": math.fsum(scores) / len(scores)}
