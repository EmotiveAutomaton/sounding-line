"""Stage 4 shared runner helper (brief §6, §9.1). One model loader, one readout, one
parser, one generation path with raw storage, one score module, and the steering
recipe reused from A02, so every track runner consumes the same instrument.

DESIGN CHECK (2026-08-27)
lessons read: LESSONS §3 (readout class matched to the behavior; realization gate per
  cell; known-answer existence; score the short hypothesis given the long evidence;
  criterion-can-fail; power before verdicts; denominators declared), §4 (instruct
  checkpoints only; record environment versions; assert what was set), §5 (one gpulock
  acquisition per invocation; produces guards; retries), CONTROLS §6 (construction
  beats ablation; directional gates with both expectations).
gates carried here for every consumer:
  - tokenization gate: every option label must map to exactly one vocabulary token for
    the reader; NULL: labels tokenize cleanly (gate passes trivially); ALTERNATIVE
    (a defective label set): a multi-token label would let label length, not evidence,
    move the readout; failure direction: FALSE POSITIVES for whichever label is
    cheapest; band: any label with token count != 1 fails the reader for that option
    set (no partial credit).
  - parser validity: the strict JSON parser accepts exactly one well-formed choice among
    the allowed labels; NULL (a competent reader): validity near 1.0; ALTERNATIVE (a
    reader that cannot follow the format): validity under the 0.95 gate; failure
    direction: an over-permissive parser would inflate validity and hide the second
    case, so the parser never counts a bare option phrase; band: valid / invalid with
    a named reason, exhaustive (malformed_or_absent, ambiguous_multiple, out_of_range,
    abstain).
  - steering calibration (A02 recipe): NULL (no valence locus): no block decodes at
    0.9 across both fit seeds and the validation seed, verdict INSTRUMENT-FAILED;
    ALTERNATIVE: a consensus locus exists and the sign pair moves with random and
    shuffled controls quiet; failure direction guarded: a dose that damages fact
    recall (capability tolerance 15 percent) is refused before any effect is read,
    because a lesioned model moves every readout; bands: ANCHOR-STANDS /
    INSTRUMENT-FAILED, with the null-effect case of the ratio-shaped control gate
    written out (controls are compared to the larger of the primary effect and a floor
    of 0.05 nats so a near-zero primary cannot pass its controls by default, L162).
"""

from __future__ import annotations

import json
import math
import random
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners.s3_lib import hash_stable, perm_p                                    # noqa: E402
from soundingline.s4 import S4, now_iso                                            # noqa: E402

PARSER_VERSION = "s4-parser-1.0"
READOUT_VERSION = "s4-label-likelihood-1.0"
READERS = ["Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct"]
ESCALATION_READER = "Qwen/Qwen2.5-3B-Instruct"
LETTERS = "ABCDEF"      # up to six options; the balanced gate uses four by construction
SEED0 = 44000


# ── environment and model handling ───────────────────────────────────────────────────

def env_versions() -> dict:
    out = {}
    for m in ("torch", "transformers", "datasets", "peft", "numpy", "sklearn"):
        try:
            mod = __import__(m)
            out[m] = getattr(mod, "__version__", "?")
        except Exception:                                                        # noqa: BLE001
            out[m] = None
    return out


def model_revision(name: str) -> str:
    """The pinned revision is the commit hash of the local snapshot; recorded, never
    a shortened prefix used as an id."""
    hub = Path.home() / ".cache" / "huggingface" / "hub"
    d = hub / ("models--" + name.replace("/", "--"))
    ref = d / "refs" / "main"
    if ref.exists():
        return ref.read_text(encoding="utf-8").strip()
    snaps = d / "snapshots"
    if snaps.exists():
        names = sorted(p.name for p in snaps.iterdir())
        if names:
            return names[-1]
    return "unknown"


def model_available(name: str) -> bool:
    hub = Path.home() / ".cache" / "huggingface" / "hub"
    d = hub / ("models--" + name.replace("/", "--")) / "snapshots"
    return d.exists() and any(d.iterdir())


def safe_id(name: str) -> str:
    """Full model identifier as a file-safe token (never a truncated prefix)."""
    return name.replace("/", "__")


def load_model(name: str):
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    tok = AutoTokenizer.from_pretrained(name)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float16).to("cuda").eval()
    return model, tok, model_revision(name)


def free_model(model) -> None:
    import torch                                                                  # noqa: PLC0415
    del model
    torch.cuda.empty_cache()


class GpuSession:
    """One gpulock acquisition per runner invocation (LESSONS §5), metered."""

    def __init__(self, tag: str):
        self.tag = tag
        self.held_s = 0.0
        self._t0 = None

    def __enter__(self):
        from soundingline.gpulock import acquire_gpu_lock                          # noqa: PLC0415
        acquire_gpu_lock(self.tag)
        self._t0 = time.time()
        return self

    def __exit__(self, *exc):
        from soundingline.gpulock import release_gpu_lock                          # noqa: PLC0415
        self.held_s += time.time() - self._t0
        release_gpu_lock()
        return False


def is_oom(exc: BaseException) -> bool:
    return "out of memory" in str(exc).lower() or "CUDA" in str(exc) and "alloc" in str(exc)


# ── prompts and the label readout ────────────────────────────────────────────────────

def chat_prefix_ids(tok, user_text: str):
    """Chat-templated prompt ids with the assistant turn opened."""
    import torch                                                                  # noqa: PLC0415
    ids = tok.apply_chat_template([{"role": "user", "content": user_text}],
                                  add_generation_prompt=True, return_tensors="pt")
    if not torch.is_tensor(ids):
        ids = ids["input_ids"]
    return ids


def label_token_ids(tok, letters: str = LETTERS) -> dict:
    """Each letter must be exactly one token in the form the model will emit after
    'Answer:' (a leading space is tried first, then the bare letter). Records the form
    used; a letter that needs more than one token fails the gate for this reader."""
    out = {}
    for L in letters:
        for form in (" " + L, L):
            ids = tok(form, add_special_tokens=False).input_ids
            if len(ids) == 1:
                out[L] = {"form": form, "id": ids[0]}
                break
        else:
            out[L] = {"form": None, "id": None}
    return out


def build_listing(options: dict, rng: random.Random, shuffle: bool = True) -> tuple[list, dict, str]:
    """Randomize option order; return (order, label_for_key, listing_text). With
    shuffle=False the caller's own order is displayed verbatim (C03's rotations), so the
    returned order is always the order the reader actually saw."""
    order = list(options)
    if shuffle:
        rng.shuffle(order)
    labels = {k: LETTERS[i] for i, k in enumerate(order)}
    listing = "\n".join(f"{labels[k]}) {options[k]}" for k in order)
    return order, labels, listing


def likelihood_choice(model, tok, body: str, options: dict, rng: random.Random,
                      instruction: str = "Answer with the letter only.",
                      shuffle: bool = True) -> dict:
    """Primary readout: normalized next-token likelihood over the balanced letter labels
    after the listed options. Option order is randomized per call and the mapping is
    returned; a label that does not tokenize to one token marks the row invalid."""
    import torch                                                                  # noqa: PLC0415
    order, labels, listing = build_listing(options, rng, shuffle)
    lab_ids = label_token_ids(tok, LETTERS[:len(order)])
    if any(v["id"] is None for v in lab_ids.values()):
        return {"valid": False, "validity_reason": "label_tokenization",
                "order": order, "labels": labels, "probs": None, "pred": None}
    user = f"{body}\nOptions:\n{listing}\n{instruction}"
    ids = chat_prefix_ids(tok, user)
    tail = tok("Answer:", add_special_tokens=False, return_tensors="pt").input_ids
    full = torch.cat([ids, tail], dim=1).to("cuda")
    with torch.no_grad():
        logits = model(full).logits[0, -1].float()
    lps = torch.log_softmax(logits, dim=-1)
    raw = {k: float(lps[lab_ids[labels[k]]["id"]]) for k in order}
    m = max(raw.values())
    z = sum(math.exp(v - m) for v in raw.values())
    probs = {k: math.exp(raw[k] - m) / z for k in order}
    pred = max(probs, key=probs.get)
    ent = -sum(p * math.log(max(p, 1e-12)) for p in probs.values())
    return {"valid": True, "validity_reason": "ok", "order": order, "labels": labels,
            "label_forms": {L: lab_ids[L]["form"] for L in lab_ids},
            "label_logits": {labels[k]: raw[k] for k in order},
            "probs": probs, "pred": pred, "entropy": ent, "readout": READOUT_VERSION,
            "n_prompt_tokens": int(full.shape[1])}


def option_text_logprobs(model, tok, body: str, options: dict) -> dict:
    """Secondary readout: mean per-token log-prob of each option's full text as the
    assistant's answer (short hypothesis scored given the long evidence)."""
    import torch                                                                  # noqa: PLC0415
    ids = chat_prefix_ids(tok, body)
    out = {}
    for k, text in options.items():
        cont = tok(text, add_special_tokens=False, return_tensors="pt").input_ids
        full = torch.cat([ids, cont], dim=1).to("cuda")
        with torch.no_grad():
            logits = model(full).logits[0].float()
        lp = torch.log_softmax(logits[:-1], dim=-1)
        tgt = full[0, 1:]
        span = range(ids.shape[1] - 1, full.shape[1] - 1)
        vals = [float(lp[i, tgt[i]]) for i in span]
        out[k] = sum(vals) / len(vals)
    return out


# ── the strict parser ────────────────────────────────────────────────────────────────

_JSON_OBJ = re.compile(r"\{[^{}]*\}")


def parse_choice(text: str, allowed) -> tuple[str | None, str]:
    """Accept exactly one well-formed {"choice": "<label>"} whose value is an allowed
    label. Prose mentions of options never count. Reasons are exhaustive:
    malformed_or_absent, ambiguous_multiple, out_of_range, abstain, ok."""
    allowed = [a.upper() for a in allowed]
    found = []
    for m in _JSON_OBJ.finditer(text or ""):
        try:
            obj = json.loads(m.group(0))
        except Exception:                                                        # noqa: BLE001
            continue
        if isinstance(obj, dict) and "choice" in obj:
            v = obj["choice"]
            found.append(str(v).strip().upper() if v is not None else "")
    if not found:
        return None, "malformed_or_absent"
    abst = {"", "NONE", "NULL", "ABSTAIN", "N/A", "UNKNOWN"}
    answers = [v for v in found if v in allowed]
    others = [v for v in found if v not in allowed and v not in abst]
    if not answers:
        if any(v in abst for v in found) and not others:
            return None, "abstain"
        return None, "out_of_range"
    if len(set(answers)) > 1:
        return None, "ambiguous_multiple"
    return answers[0], "ok"


PARSER_FIXTURES = [
    ('{"choice": "B"}', "AB CD", "B", "ok"),
    ('I would not pick A. {"choice":"B"}', "ABCD", "B", "ok"),
    ('"A" is what a novice would say; {"choice": "C"}', "ABCD", "C", "ok"),
    ('Format example: {"choice":"X"} ... my answer: {"choice":"D"}', "ABCD", "D", "ok"),
    ('{"choice": "A"} {"choice": "B"}', "ABCD", None, "ambiguous_multiple"),
    ('{"choice": "B"} and again {"choice": "B"}', "ABCD", "B", "ok"),
    ('The answer is B.', "ABCD", None, "malformed_or_absent"),
    ('{"choice": B}', "ABCD", None, "malformed_or_absent"),
    ('{"choice": ""}', "ABCD", None, "abstain"),
    ('{"choice": "E"}', "ABCD", None, "out_of_range"),
    ('Option A is tempting but wrong. Final: {"choice": "A"}', "ABCD", "A", "ok"),
    ('{"choice": "b"}', "ABCD", "B", "ok"),
]


def run_parser_fixtures() -> list[str]:
    fails = []
    for text, allowed, want, reason in PARSER_FIXTURES:
        got, why = parse_choice(text, allowed.replace(" ", ""))
        if got != want or why != reason:
            fails.append(f"{text!r}: got {got!r}/{why} want {want!r}/{reason}")
    return fails


# ── generation with raw storage ──────────────────────────────────────────────────────

def generate(model, tok, user_text: str, seed: int, max_new: int = 200,
             greedy: bool = False) -> dict:
    """Chat generation; returns the raw text and the output token ids (raw storage)."""
    import torch                                                                  # noqa: PLC0415
    ids = chat_prefix_ids(tok, user_text).to("cuda")
    torch.manual_seed(seed)
    with torch.no_grad():
        if greedy:
            out = model.generate(ids, do_sample=False, max_new_tokens=max_new,
                                 pad_token_id=tok.pad_token_id)
        else:
            out = model.generate(ids, do_sample=True, temperature=0.8, top_p=0.95,
                                 max_new_tokens=max_new, pad_token_id=tok.pad_token_id)
    new_ids = out[0][ids.shape[1]:].tolist()
    text = tok.decode(new_ids, skip_special_tokens=True).strip()
    return {"text": text, "token_ids": new_ids, "seed": seed, "greedy": greedy,
            "n_prompt_tokens": int(ids.shape[1])}


def generated_choice(model, tok, body: str, options: dict, rng: random.Random,
                     seed: int) -> dict:
    """The strict generated cross-check: the model must answer with a JSON object."""
    order, labels, listing = build_listing(options, rng)
    user = (f"{body}\nOptions:\n{listing}\nReply with exactly one JSON object of the form "
            f'{{"choice": "<letter>"}} and nothing else.')
    g = generate(model, tok, user, seed, max_new=24, greedy=True)
    letter, reason = parse_choice(g["text"], LETTERS[:len(order)])
    inv = {v: k for k, v in labels.items()}
    return {"valid": letter is not None, "validity_reason": reason, "order": order,
            "labels": labels, "pred": inv.get(letter) if letter else None,
            "raw": g["text"], "token_ids": g["token_ids"], "parser": PARSER_VERSION}


def raw_output_row(card: str, cell_id: str, unit_id: str, model_id: str, revision: str,
                   prompt: str, gen: dict, parser_version: str = PARSER_VERSION,
                   validity_reason: str = "ok", extra: dict | None = None) -> dict:
    return {"card": card, "cell_id": cell_id, "unit_id": unit_id, "model_id": model_id,
            "model_revision": revision, "prompt": prompt, "raw_text": gen.get("text"),
            "token_ids": gen.get("token_ids"), "seed": gen.get("seed"),
            "parser_version": parser_version, "validity_reason": validity_reason,
            "at": now_iso(), **(extra or {})}


# ── scores and statistics ────────────────────────────────────────────────────────────

def log_score(probs: dict, truth) -> float:
    return math.log(max(float(probs.get(truth, 0.0)), 1e-9))


def brier(probs: dict, truth) -> float:
    return sum((p - (1.0 if k == truth else 0.0)) ** 2 for k, p in probs.items())


def balanced_accuracy(preds, truths, labels) -> float:
    per = []
    for lab in labels:
        idx = [i for i, t in enumerate(truths) if t == lab]
        if idx:
            per.append(sum(1 for i in idx if preds[i] == lab) / len(idx))
    return sum(per) / len(per) if per else float("nan")


def per_unit_means(rows, unit_key: str, value_key: str) -> dict:
    acc: dict = {}
    for r in rows:
        acc.setdefault(r[unit_key], []).append(float(r[value_key]))
    return {u: sum(v) / len(v) for u, v in acc.items()}


def cluster_bootstrap_ci(unit_values: dict, seed: int, n: int = 2000,
                         alpha: float = 0.05) -> dict:
    """Resample independent units with replacement; the estimate is the mean of unit
    means. Returns point, lo, hi, n_units."""
    units = sorted(unit_values)
    vals = [unit_values[u] for u in units]
    if not vals:
        return {"point": None, "lo": None, "hi": None, "n_units": 0}
    rng = random.Random(seed)
    point = sum(vals) / len(vals)
    boots = []
    for _ in range(n):
        s = [vals[rng.randrange(len(vals))] for _ in vals]
        boots.append(sum(s) / len(s))
    boots.sort()
    lo = boots[int(alpha / 2 * n)]
    hi = boots[min(n - 1, int((1 - alpha / 2) * n))]
    return {"point": point, "lo": lo, "hi": hi, "n_units": len(vals), "n_boot": n}


def paired_contrast(rows_a, rows_b, unit_key: str, value_key: str, seed: int) -> dict:
    """Per-unit mean(a) - mean(b) over units present in both; bootstrap CI and the
    sign-flip permutation p on the unit diffs."""
    ma = per_unit_means(rows_a, unit_key, value_key)
    mb = per_unit_means(rows_b, unit_key, value_key)
    common = sorted(set(ma) & set(mb))
    diffs = {u: ma[u] - mb[u] for u in common}
    ci = cluster_bootstrap_ci(diffs, seed)
    p = perm_p([diffs[u] for u in common], seed + 1)[1] if len(common) >= 2 else None
    return {**ci, "perm_p": p, "n_a": len(ma), "n_b": len(mb)}


def stratum_balanced(unit_values: dict, unit_stratum: dict) -> dict:
    """Reweight per-unit values so every stratum carries equal total weight: the mean of
    the returned values equals the mean of the stratum means. An interaction estimated
    as mean(sign x delta) leaks a main effect whenever the signs are unbalanced (a third
    of the appraisal worlds carry a negative valuation), so the aligned-benefit
    estimands (A02, A03, F01) pass through here before any interval is taken. Units
    without a stratum are dropped."""
    strata: dict = {}
    for u, v in unit_values.items():
        s = unit_stratum.get(u)
        if s is None:
            continue
        strata.setdefault(s, []).append(u)
    if not strata:
        return {}
    n_total = sum(len(us) for us in strata.values())
    k = len(strata)
    out = {}
    for s, us in strata.items():
        w = n_total / (k * len(us))
        for u in us:
            out[u] = unit_values[u] * w
    return out


def auroc(scores_pos, scores_neg) -> float | None:
    if not scores_pos or not scores_neg:
        return None
    wins = 0.0
    for p in scores_pos:
        for q in scores_neg:
            wins += 1.0 if p > q else (0.5 if p == q else 0.0)
    return wins / (len(scores_pos) * len(scores_neg))


def world_rng(lineage_id: str, salt: str = "") -> random.Random:
    return random.Random(hash_stable(lineage_id + "|" + salt))


def collision_leak_check(X, y, seed: int = 0) -> float:
    """Verification 8: cross-validated accuracy of a small classifier. On an exact
    collision fixture (identical inputs, balanced hidden labels) it must sit at chance;
    any lift means the features or metadata leak the hidden label."""
    import numpy as np                                                            # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression                           # noqa: PLC0415
    from sklearn.model_selection import StratifiedKFold, cross_val_score          # noqa: PLC0415
    Xa, ya = np.asarray(X, dtype=float), np.asarray(y)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    clf = LogisticRegression(max_iter=500)
    return float(cross_val_score(clf, Xa, ya, cv=cv).mean())


# ── steering: the A02 recipe as a calibration function ───────────────────────────────

def fit_valence_handle(model, tok, seeds=(1, 2), val_seed: int = 3) -> dict:
    """Reproduce the Stage-3 A02 recipe on its calibration sentences (disjoint from any
    Stage-4 world): cross-seed consensus locus at 0.9 held-out decode, middle-third
    steer locus, random and shuffled control directions, dose ladder under a fact-recall
    tolerance, and the sign-pair anchor check on neutral contexts. Calibrated for THIS
    model; nothing is transplanted across residual spaces."""
    import torch                                                                  # noqa: PLC0415
    from runners.s3_run_a import (FACT_CONT, NEG_CONT, NEG_SENTS, NEUTRAL_CTX,   # noqa: PLC0415
                                  POS_CONT, POS_SENTS, _mean_logp, additive_steer)
    from soundingline.probe.interventions import capture_block_states             # noqa: PLC0415
    states = {}
    for label, bank in (("pos", POS_SENTS), ("neg", NEG_SENTS)):
        for i, s in enumerate(bank):
            hs = capture_block_states(model, tok, s, device="cuda")
            states[(label, i)] = [h[-1] for h in hs]
    n_blocks = len(states[("pos", 0)])
    n_items = len(POS_SENTS)

    from runners.s3_run_a import SEED0 as A02_SEED0                              # noqa: PLC0415

    def fit_and_decode(seed: int):
        rng = random.Random(A02_SEED0 + seed)      # Stage 3's fit splits, reproduced
        idx = list(range(n_items))
        rng.shuffle(idx)
        cut = int(n_items * 2 / 3)
        fit, held = idx[:cut], idx[cut:]
        per_block = []
        for b in range(n_blocks):
            mp = torch.stack([states[("pos", i)][b] for i in fit]).mean(0)
            mn = torch.stack([states[("neg", i)][b] for i in fit]).mean(0)
            d = mp - mn
            d = d / d.norm()
            thr = ((mp + mn) / 2) @ d
            hits = 0
            for i in held:
                hits += (states[("pos", i)][b] @ d > thr).item()
                hits += (states[("neg", i)][b] @ d <= thr).item()
            per_block.append({"acc": hits / (2 * len(held)), "dir": d})
        return per_block

    fits = [fit_and_decode(s) for s in seeds]
    val = fit_and_decode(val_seed)
    consensus = [b for b in range(3, n_blocks)
                 if all(f[b]["acc"] >= 0.9 for f in fits) and val[b]["acc"] >= 0.9]
    result = {"n_blocks": n_blocks, "consensus_blocks": consensus, "verdict": None}
    if not consensus:
        result["verdict"] = "INSTRUMENT-FAILED"
        result["reason"] = "no cross-seed consensus locus decodes valence at 0.9"
        return result
    consensus.sort()
    locus = consensus[len(consensus) // 3: len(consensus) // 3 + max(1, len(consensus) // 3)]
    dirs = {b: fits[0][b]["dir"] for b in locus}
    g = torch.Generator().manual_seed(SEED0)
    rng = random.Random(SEED0 + 9)
    lab = ["pos"] * n_items + ["neg"] * n_items
    rng.shuffle(lab)
    rand_dirs, shuf_dirs = {}, {}
    for b in locus:
        r = torch.randn(dirs[b].shape[0], generator=g)
        r = r - (r @ dirs[b]) * dirs[b]
        rand_dirs[b] = r / r.norm()
        mp = torch.stack([states[(l0, i % n_items)][b]
                          for i, l0 in enumerate(lab[:n_items])]).mean(0)
        mn = torch.stack([states[(l0, i % n_items)][b]
                          for i, l0 in enumerate(lab[n_items:], start=n_items)]).mean(0)
        d2 = mp - mn
        shuf_dirs[b] = d2 / d2.norm()

    def battery(cond_dirs, alpha):
        from contextlib import ExitStack                                          # noqa: PLC0415
        deltas, fact = [], []

        def run():
            for ctx in NEUTRAL_CTX:
                deltas.append(_mean_logp(model, tok, ctx, POS_CONT)
                              - _mean_logp(model, tok, ctx, NEG_CONT))
            for f in FACT_CONT:
                fact.append(_mean_logp(model, tok, "A plain fact: ", f))
        if cond_dirs is None or alpha == 0.0:
            run()
        else:
            with ExitStack() as stack:
                for b, d in cond_dirs.items():
                    stack.enter_context(additive_steer(model, [b], d, alpha))
                run()
        return deltas, sum(fact) / len(fact)

    base_deltas, base_fact = battery(None, 0.0)
    mean_norm = float(torch.stack([states[("pos", i)][locus[0]]
                                   for i in range(n_items)]).norm(dim=1).mean())
    # The dose is part of the instrument (LESSONS §3): every rung of the fixed ladder is
    # scored on capability, the sign pair, AND both controls, on calibration sentences
    # only; the largest rung passing all of them is the handle. The smoke test showed
    # why: at a dose three times Stage 3's, a shuffled-label direction moved valence
    # almost as far as the fitted one while capability still passed.
    chosen, ladder = None, {}
    for frac in (0.20, 0.10, 0.05):
        alpha = frac * mean_norm
        pd, pf = battery(dirs, alpha)
        ok = pf >= base_fact - 0.15 * abs(base_fact)
        rung = {"alpha": alpha, "fact_logp": pf, "base_fact_logp": base_fact,
                "capability_ok": ok}
        if ok:
            nd, _ = battery(dirs, -alpha)
            rd, _ = battery(rand_dirs, alpha)
            sd_, _ = battery(shuf_dirs, alpha)
            pos_shift = [p - b for p, b in zip(pd, base_deltas)]
            neg_shift = [n - b for n, b in zip(nd, base_deltas)]
            rand_shift = [r - b for r, b in zip(rd, base_deltas)]
            shuf_shift = [s0 - b for s0, b in zip(sd_, base_deltas)]
            obs_p, p_pos = perm_p(pos_shift, SEED0 + 11)
            obs_n, p_neg = perm_p(neg_shift, SEED0 + 12)
            sign_pair = obs_p > 0 and obs_n < 0 and p_pos < 0.05 and p_neg < 0.05
            floor = max(abs(obs_p) / 2, 0.05)      # the null-effect case of the ratio gate
            rand_quiet = abs(sum(rand_shift) / len(rand_shift)) < floor
            shuf_quiet = abs(sum(shuf_shift) / len(shuf_shift)) < floor
            rung.update({"pos_shift_mean": obs_p, "p_pos": p_pos, "neg_shift_mean": obs_n,
                         "p_neg": p_neg, "rand_shift_mean": sum(rand_shift) / len(rand_shift),
                         "shuf_shift_mean": sum(shuf_shift) / len(shuf_shift),
                         "sign_pair": sign_pair, "rand_quiet": rand_quiet,
                         "shuf_quiet": shuf_quiet,
                         "passes": sign_pair and rand_quiet and shuf_quiet})
            if rung["passes"] and chosen is None:
                chosen = (frac, alpha, rung)
        ladder[str(frac)] = rung
    if chosen is None:
        result.update({"verdict": "INSTRUMENT-FAILED", "steer_locus": locus,
                       "dose_ladder": ladder, "mean_norm": mean_norm,
                       "reason": "no rung of the dose ladder passes capability, the sign "
                                 "pair, and both controls together"})
        return result
    frac, alpha, rung = chosen
    verdict = "ANCHOR-STANDS"
    result.update({"verdict": verdict, "steer_locus": locus, "dose_frac": frac,
                   "alpha": alpha, "mean_norm": mean_norm, "dose_ladder": ladder,
                   "pos_shift_mean": rung["pos_shift_mean"], "p_pos": rung["p_pos"],
                   "neg_shift_mean": rung["neg_shift_mean"], "p_neg": rung["p_neg"],
                   "rand_shift_mean": rung["rand_shift_mean"],
                   "shuf_shift_mean": rung["shuf_shift_mean"],
                   "validation_decode": val[locus[0]]["acc"], "n_contexts": len(NEUTRAL_CTX),
                   "directions": {str(b): dirs[b].cpu().tolist() for b in locus},
                   "random_directions": {str(b): rand_dirs[b].cpu().tolist() for b in locus},
                   "shuffled_directions": {str(b): shuf_dirs[b].cpu().tolist() for b in locus}})
    return result


def handle_from_json(d: dict):
    """Rebuild direction tensors from a stored handle dict."""
    import torch                                                                  # noqa: PLC0415
    return ({int(b): torch.tensor(v) for b, v in d["directions"].items()},
            {int(b): torch.tensor(v) for b, v in d["random_directions"].items()},
            {int(b): torch.tensor(v) for b, v in d["shuffled_directions"].items()})


from contextlib import contextmanager                                             # noqa: E402


@contextmanager
def steer_positions(model, block_ids, direction, alpha: float, start: int, end: int):
    """Additive steering restricted to token positions [start, end) at the chosen blocks
    (A03's phase contrast). Same hook tag and guaranteed removal as additive_steer;
    shape, dtype, device asserted. Full forward passes only (no cached keys/values are
    reused across steered and unsteered calls)."""
    import torch                                                                  # noqa: PLC0415
    from soundingline.probe.interventions import get_blocks                       # noqa: PLC0415
    blocks = get_blocks(model)
    handles = []

    def make_hook():
        def hook(_m, _i, output):
            hs = output[0] if isinstance(output, tuple) else output
            shape, dtype, device = hs.shape, hs.dtype, hs.device
            s, e = max(0, start), min(end, hs.shape[1])
            if alpha == 0.0 or s >= e:
                return None
            d = direction.to(device=device, dtype=torch.float32)
            seg = hs[:, s:e, :].to(torch.float32) + alpha * d
            out = torch.cat([hs[:, :s, :], seg.to(dtype), hs[:, e:, :]], dim=1)
            assert out.shape == shape and out.dtype == dtype and out.device == device
            if isinstance(output, tuple):
                return (out,) + tuple(output[1:])
            return out
        hook._p24_intervention = True
        return hook

    try:
        for i in block_ids:
            handles.append(blocks[i].register_forward_hook(make_hook()))
        yield
    finally:
        for h in handles:
            h.remove()


def hooks_present(model) -> int:
    """Count our tagged forward hooks still installed (cleanup audit)."""
    from soundingline.probe.interventions import get_blocks                       # noqa: PLC0415
    n = 0
    for b in get_blocks(model):
        for h in b._forward_hooks.values():
            if getattr(h, "_p24_intervention", False):
                n += 1
    return n


def card_dir(card: str) -> Path:
    p = S4 / card
    p.mkdir(parents=True, exist_ok=True)
    return p
