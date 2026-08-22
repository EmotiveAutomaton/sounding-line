"""Phase 2.4 conditional-likelihood reader — the non-generative inversion score.

The design lesson this instrument encodes (Phase 2.3, Wing G, L151/L153): asking a reader to
GENERATE its route costs accuracy and induces fabrication; direct reading wins. So the common
Phase 2.4 reader never narrates. For a candidate process description p and artifact O it scores

    s(p, O) = mean over artifact tokens of [ log P(O | p) - log P(O | p0) ]

where p0 is a neutral, candidate-independent conditioning string (context §7.3). Softmax into a
posterior only after temperature calibration on development data; raw scores and ranks are the
primary record.

Token discipline:
  - condition and artifact are tokenized SEPARATELY and concatenated as ids, so the boundary is
    exact and no token merges across it; the same split is applied to every candidate, so any
    tokenization loss cancels within a case;
  - only artifact-token log-probabilities are summed;
  - the boundary index is what SubspaceIntervention receives, so an intervention can never act
    while the candidate description is being read (context §8.3).

Raw log-likelihoods are never compared across tokenizers (context §7.4): every quantity leaving
this module is a within-reader difference, rank, or per-token mean.
"""

from __future__ import annotations

import torch

NEUTRAL_CONDITION = "The following is a passage of text."

_CACHE: dict[tuple, tuple] = {}


def load_reader(name: str, device: str = "cuda", dtype: str = "float16"):
    """Load (model, tokenizer) once per process; eval mode, no grad anywhere downstream."""
    key = (name, device, dtype)
    if key not in _CACHE:
        from transformers import AutoModelForCausalLM, AutoTokenizer     # noqa: PLC0415
        tok = AutoTokenizer.from_pretrained(name)
        model = AutoModelForCausalLM.from_pretrained(
            name, torch_dtype=getattr(torch, dtype) if device == "cuda" else torch.float32)
        model.to(device).eval()
        _CACHE[key] = (model, tok)
    return _CACHE[key]


def free_readers():
    """Drop every cached reader and release VRAM (called between matrix readers)."""
    _CACHE.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def artifact_logprob(model, tok, condition: str, artifact: str,
                     intervention=None) -> tuple[float, int, int]:
    """Mean log P(artifact | condition) per artifact token. Returns (mean_lp, n_tokens, boundary).

    The sequence is [bos?] + ids(condition + "\\n\\n") + ids(artifact); boundary is the index of
    the first artifact token. If an intervention is supplied, its boundary is set here and its
    hooks live only for this forward pass.
    """
    device = next(model.parameters()).device
    ids_c = tok(condition + "\n\n", add_special_tokens=False).input_ids
    ids_a = tok(artifact, add_special_tokens=False).input_ids
    if tok.bos_token_id is not None:
        ids_c = [tok.bos_token_id] + ids_c
    boundary = len(ids_c)
    ids = torch.tensor([ids_c + ids_a], device=device)
    with torch.no_grad():
        if intervention is not None:
            intervention.boundary = boundary
            with intervention.applied(model):
                logits = model(ids).logits
        else:
            logits = model(ids).logits
    # position j predicts token j+1; artifact tokens occupy boundary .. end
    lp = torch.log_softmax(logits[0, boundary - 1: -1, :].to(torch.float32), dim=-1)
    tgt = ids[0, boundary:]
    tok_lp = lp[torch.arange(tgt.shape[0]), tgt]
    return float(tok_lp.mean()), int(tgt.shape[0]), boundary


def candidate_scores(model, tok, candidates: list[str], artifact: str,
                     neutral: str = NEUTRAL_CONDITION,
                     intervention=None) -> dict:
    """Score every candidate against one artifact, neutral-subtracted.

    Returns {"scores": [s_i], "neutral_lp": float, "n_tokens": int, "rank_of": fn-free list
    sorted descending by score as indices}. The intervention (if any) is applied identically
    to every candidate AND to the neutral arm, so the subtraction stays fair.
    """
    n_lp, n_tok, _ = artifact_logprob(model, tok, neutral, artifact, intervention)
    scores = []
    for c in candidates:
        c_lp, _, _ = artifact_logprob(model, tok, c, artifact, intervention)
        scores.append(c_lp - n_lp)
    order = sorted(range(len(candidates)), key=lambda i: -scores[i])
    return {"scores": scores, "neutral_lp": n_lp, "n_tokens": n_tok, "order": order}
