"""Shared plumbing for the Stage-5 post-run receipt runners built 2026-08-30 (TODO (m), (l),
(o), (j)/(p), (b)): the design-2 environment, the receipt directory, the ease rulers over a
text's token probabilities, and an unpaired bootstrap. Every receipt writes under
results/phase_2_4_stage_5r/post/ (or S5_RECEIPT_OUT for a smoke) and changes nothing landed.

The environment is set at import so that every world, source, and readout module reads the
second contract's constants; a runner imports this module before any other Stage-5 module.
"""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.environ.setdefault("S5_DESIGN", "2")
os.environ.setdefault("S5_STAGE", "phase_2_4_stage_5r")
os.environ.setdefault("S5_ROOT", str(REPO / "results" / "phase_2_4_stage_5r"))

SMOKE = bool(os.environ.get("S5_SMOKE"))
OUT = Path(os.environ["S5_RECEIPT_OUT"]) if os.environ.get("S5_RECEIPT_OUT") else REPO / "results" / "phase_2_4_stage_5r" / "post"

# ease rulers, every one signed so that HIGHER MEANS EASIER; the first is the ruler L301 found
# invalid (it rewards predictable filler tokens), kept so the validation can show it failing
RULER_NAMES = ("content_total_logp", "total_logp", "neg_token_count", "mean_token_logp")


def text_token_logps(model, tok, body: str, text: str) -> list[tuple[str, float]]:
    """Per-token (decoded piece, log probability) of `text` as the assistant's answer to
    `body`; the same scoring path as the option-text readout, kept per token."""
    import torch                                                                  # noqa: PLC0415
    from runners.s4_lib import chat_prefix_ids                                    # noqa: PLC0415
    ids = chat_prefix_ids(tok, body)
    cont = tok(text, add_special_tokens=False, return_tensors="pt").input_ids
    full = torch.cat([ids, cont], dim=1).to("cuda")
    with torch.no_grad():
        logits = model(full).logits[0].float()
    lp = torch.log_softmax(logits[:-1], dim=-1)
    tgt = full[0, 1:]
    out = []
    for i in range(ids.shape[1] - 1, full.shape[1] - 1):
        out.append((tok.decode([int(tgt[i])]), float(lp[i, tgt[i]])))
    return out


def rulers(pieces: list[tuple[str, float]]) -> dict:
    """The four ease rulers from one token list. content_total_logp sums only the tokens that
    carry a letter or digit (a mid-dot or a bare space contributes nothing); total_logp sums
    every token; neg_token_count is the negated token count; mean_token_logp is L301's ruler."""
    n = max(1, len(pieces))
    tot = sum(lp for _, lp in pieces)
    content = sum(lp for p, lp in pieces if any(ch.isalnum() for ch in p))
    return {"content_total_logp": content, "total_logp": tot, "neg_token_count": -float(len(pieces)), "mean_token_logp": tot / n}


def diff_bootstrap(a: dict, b: dict, seed: int, n: int = 2000, alpha: float = 0.05) -> dict:
    """Unpaired difference of means, mean(a) - mean(b), over two dicts unit -> value; each
    group's units resampled with replacement. Returns point, lo, hi, n_units (a and b)."""
    ua, ub = sorted(a), sorted(b)
    if not ua or not ub:
        return {"point": None, "lo": None, "hi": None, "n_units": [len(ua), len(ub)]}
    rng = random.Random(seed)
    va, vb = [a[u] for u in ua], [b[u] for u in ub]
    point = sum(va) / len(va) - sum(vb) / len(vb)
    draws = []
    for _ in range(n):
        ra = [va[rng.randrange(len(va))] for _ in va]
        rb = [vb[rng.randrange(len(vb))] for _ in vb]
        draws.append(sum(ra) / len(ra) - sum(rb) / len(rb))
    draws.sort()
    lo = draws[int(alpha / 2 * n)]
    hi = draws[min(n - 1, int((1 - alpha / 2) * n))]
    return {"point": point, "lo": min(lo, point), "hi": max(hi, point), "n_units": [len(ua), len(ub)]}


def classify(contrast: dict, threshold: float) -> dict:
    """The shared exhaustive band classifier on a contrast dict (point, lo, hi)."""
    from soundingline.s4 import classify_outcome                                  # noqa: PLC0415
    if contrast.get("point") is None:
        return {"outcome": "VOID", "reason": "no units"}
    oc, why = classify_outcome(contrast["point"], contrast["lo"], contrast["hi"], threshold)
    return {"outcome": oc, "reason": why, "point": contrast["point"], "ci": [contrast["lo"], contrast["hi"]],
            "n_units": contrast.get("n_units"), "threshold": threshold, "perm_p": contrast.get("perm_p")}


def write(name: str, obj: dict) -> Path:
    from soundingline.s4 import write_json                                        # noqa: PLC0415
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / name
    write_json(dest, obj)
    print("wrote", dest)
    return dest


def read_ruler() -> dict | None:
    """The ease-ruler receipt (EASE_RULER.json) beside this receipt's output, or None."""
    import json                                                                   # noqa: PLC0415
    p = OUT / "EASE_RULER.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
