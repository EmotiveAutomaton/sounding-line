"""Stage 3 Trunk M runners: M01 activation patching — where in depth does a standing
policy live while it is shaping a choice? Card E24-S3-M01.

Method: for a scenario, two prompts — WITH a policy line and WITHOUT. Capture the
with-policy residual state at every block's final prompt token; re-score the four
committed answers under the WITHOUT prompt while patching one block's final-prompt-token
state from the WITH run; the per-block transfer curve is the localization.

DESIGN CHECK (2026-08-24). Lessons applied: known-positive gate first — the full prompt
condition must itself shift choice mass toward the policy's option, else patching has
nothing to localize and the cell is INSTRUMENT_FAILED (L139); identity patch (without ->
without) and mismatched-scenario patch are the paired nulls, written before the run;
readout is likelihood mass over the four anchor-committed answers, mechanical (L156);
per-block cells reported, not just the best block (L168); hooks carry the
`_p24_intervention` tag and are removed in finally (transformers-5 recorder hooks);
patching one position only — the final prompt token — so sequence-length mismatch
between conditions never aliases position (the prompts differ in length by design).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners.s3_lib import (AXES, POLICY_LINES, episode_prompt, scenarios)        # noqa: E402
from soundingline.s3 import S3, set_status                                        # noqa: E402

SEED0 = 80000
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
OUT_M = S3 / "M" / "M01"
DOMAIN = "infra"
POLICIES = ("robust", "cheap")
N_SCEN = 12
BLOCK_STRIDE = 2


def committed_answer(si: int, ax: str) -> str:
    _, _, opts = scenarios(DOMAIN)[si]
    return f"I recommend the {opts[ax]}."


@contextmanager
def patch_block(model, block_i: int, pos: int, state):
    """Replace the block's output hidden state at one position with `state`."""
    import torch                                                                  # noqa: PLC0415
    from soundingline.probe.interventions import get_blocks                       # noqa: PLC0415

    def hook(_m, _i, output):
        hs = output[0] if isinstance(output, tuple) else output
        if pos >= hs.shape[1]:
            return None
        out = hs.clone()
        out[:, pos, :] = state.to(device=hs.device, dtype=hs.dtype)
        if isinstance(output, tuple):
            return (out,) + tuple(output[1:])
        return out
    hook._p24_intervention = True
    h = get_blocks(model)[block_i].register_forward_hook(hook)
    try:
        yield
    finally:
        h.remove()


def choice_mass(model, tok, prompt_ids, si: int):
    """Softmax over summed candidate logprobs for the four committed answers,
    scored in one batch continuation each (prompt cached implicitly per call)."""
    import math                                                                   # noqa: PLC0415
    import torch                                                                  # noqa: PLC0415
    scores = []
    n_p = prompt_ids.shape[1]
    for ax in AXES:
        cand = tok(committed_answer(si, ax), return_tensors="pt",
                   add_special_tokens=False).input_ids.to("cuda")
        full = torch.cat([prompt_ids, cand], dim=1)
        with torch.no_grad():
            logits = model(full).logits.float()
        lp = torch.log_softmax(logits[0, :-1], dim=-1)
        tgt = full[0, 1:]
        s = sum(lp[i, tgt[i]].item() for i in range(n_p - 1, full.shape[1] - 1))
        scores.append(s / cand.shape[1])
    m = max(scores)
    exps = [math.exp(s - m) for s in scores]
    z = sum(exps)
    return [e / z for e in exps]


def build_prompt_ids(tok, si: int, policy: str | None):
    import torch                                                                  # noqa: PLC0415
    text = episode_prompt(si, DOMAIN, POLICY_LINES[policy] if policy else "")
    msgs = [{"role": "user", "content": text}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                  return_tensors="pt")
    if not torch.is_tensor(ids):
        ids = ids["input_ids"]
    return ids.to("cuda")


def arm_m01(model_name: str = MODEL, out_dir=None, cell: str = "E24-S3-M01") -> int:
    t0 = time.time()
    out_m = out_dir or OUT_M
    out_m.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.probe.interventions import get_blocks                       # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415

    acquire_gpu_lock(f"s3_{cell[-3:].lower()}")
    try:
        tok = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name, dtype=torch.float16).to("cuda").eval()
        n_blocks = len(get_blocks(model))
        blocks = list(range(1, n_blocks, BLOCK_STRIDE))

        # per (scenario, policy): the prompted shift (known-positive gate material)
        gate_rows = []
        curves = {b: [] for b in blocks}
        identity_ctl, mismatch_ctl = [], []
        for si in range(N_SCEN):
            for pol in POLICIES:
                tgt = None
                # target option under this policy = argmax of env utilities
                from runners.s3_lib import choice_probs, utilities, PROFILE_W     # noqa: PLC0415
                probs = choice_probs(utilities(si, 1, DOMAIN), PROFILE_W[pol])
                tgt = max(range(4), key=lambda j: probs[j])
                ids_p = build_prompt_ids(tok, si, pol)
                ids_0 = build_prompt_ids(tok, si, None)
                mass_p = choice_mass(model, tok, ids_p, si)
                mass_0 = choice_mass(model, tok, ids_0, si)
                gate_rows.append({"si": si, "policy": pol,
                                  "prompted": mass_p[tgt], "bare": mass_0[tgt]})
                # capture with-policy states at every block's final prompt token
                with torch.no_grad():
                    hp = model(ids_p, output_hidden_states=True).hidden_states
                pos0 = ids_0.shape[1] - 1
                for b in blocks:
                    state = hp[b + 1][0, -1]      # hidden_states[0] is embeddings
                    with patch_block(model, b, pos0, state):
                        mass_b = choice_mass(model, tok, ids_0, si)
                    curves[b].append({"si": si, "policy": pol,
                                      "patched": mass_b[tgt],
                                      "bare": mass_0[tgt],
                                      "prompted": mass_p[tgt]})
                # identity control at a mid block: patch bare state into bare run
                with torch.no_grad():
                    h0 = model(ids_0, output_hidden_states=True).hidden_states
                bmid = blocks[len(blocks) // 2]
                with patch_block(model, bmid, pos0, h0[bmid + 1][0, -1]):
                    mass_id = choice_mass(model, tok, ids_0, si)
                identity_ctl.append(abs(mass_id[tgt] - mass_0[tgt]))
                # mismatched-scenario control: policy state from a different scenario
                sj = (si + 5) % N_SCEN
                ids_pj = build_prompt_ids(tok, sj, pol)
                with torch.no_grad():
                    hpj = model(ids_pj, output_hidden_states=True).hidden_states
                with patch_block(model, bmid, pos0, hpj[bmid + 1][0, -1]):
                    mass_mm = choice_mass(model, tok, ids_0, si)
                mismatch_ctl.append(mass_mm[tgt] - mass_0[tgt])
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()

    prompted_shift = sum(r["prompted"] - r["bare"] for r in gate_rows) / len(gate_rows)
    gate_pass = prompted_shift > 0.1
    curve_out = {}
    for b, rows in curves.items():
        transfer = [(r["patched"] - r["bare"])
                    / max(r["prompted"] - r["bare"], 1e-6) for r in rows
                    if r["prompted"] - r["bare"] > 0.02]
        curve_out[str(b)] = {
            "n_valid": len(transfer),
            "mean_transfer": sum(transfer) / len(transfer) if transfer else None,
            "mean_patched_minus_bare": sum(r["patched"] - r["bare"]
                                           for r in rows) / len(rows)}
    (out_m / "verdict.json").write_text(json.dumps(
        {"cell": cell, "model": model_name,
         "gate_pass": gate_pass, "prompted_shift": prompted_shift,
         "per_block": curve_out,
         "identity_ctl_mean_abs": sum(identity_ctl) / len(identity_ctl),
         "mismatch_ctl_mean": sum(mismatch_ctl) / len(mismatch_ctl),
         "blocks": blocks, "n_scenarios": N_SCEN, "policies": POLICIES},
        indent=1), encoding="utf-8", newline="\n")
    set_status(cell, "LANDED" if gate_pass else "INSTRUMENT_FAILED",
               closure_reason=None if gate_pass else
               f"prompted policy shift {prompted_shift:.3f} too small to localize",
               actual_gpu_minutes=(time.time() - t0) / 60)
    best = max((v["mean_transfer"] or -9, k) for k, v in curve_out.items())
    print(f"M01 gate_pass={gate_pass} (prompted shift {prompted_shift:.3f}); "
          f"best block {best[1]} transfer {best[0]:.3f}; identity ctl "
          f"{sum(identity_ctl) / len(identity_ctl):.4f}")
    return 0


# ── M02: interchange intervention (card E24-S3-M02) ─────────────────────────────────
# The question in plain language: at the depth M01 localized, does swapping the policy
# state between two prompted policies EXCHANGE the behavior — robust-state into a
# cheap-prompted run making it choose the robust option, and vice versa? Interchange is
# a stronger causal claim than transfer-into-bare.
# DESIGN CHECK: block choice comes from M01's landed curve, read from its verdict file,
# never re-fitted here (no double-dipping); both swap directions run (sign pair);
# the low-transfer control block from the same curve is the null; per-scenario cells.

def arm_m02() -> int:
    cell = "E24-S3-M02"
    t0 = time.time()
    out = S3 / "M" / "M02"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from runners.s3_lib import choice_probs, utilities, PROFILE_W                 # noqa: PLC0415
    m01 = json.loads((S3 / "M" / "M01" / "verdict.json"
                      ).read_text(encoding="utf-8"))
    if not m01.get("gate_pass"):
        set_status(cell, "INSTRUMENT_FAILED",
                   closure_reason="M01 gate failed; no localized depth to test",
                   actual_gpu_minutes=0.0)
        print("M02 blocked: M01 gate failed")
        return 0
    curve = {int(k): v["mean_transfer"] for k, v in m01["per_block"].items()
             if v["mean_transfer"] is not None}
    best_b = max(curve, key=curve.get)
    low_b = min(curve, key=lambda k: abs(curve[k]))
    acquire_gpu_lock("s3_m02")
    rows = []
    try:
        tok = AutoTokenizer.from_pretrained(MODEL)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL, dtype=torch.float16).to("cuda").eval()
        for si in range(N_SCEN):
            tgt = {}
            for pol in POLICIES:
                probs = choice_probs(utilities(si, 1, DOMAIN), PROFILE_W[pol])
                tgt[pol] = max(range(4), key=lambda j: probs[j])
            if tgt["robust"] == tgt["cheap"]:
                continue
            ids = {pol: build_prompt_ids(tok, si, pol) for pol in POLICIES}
            caps = {}
            for pol in POLICIES:
                with torch.no_grad():
                    caps[pol] = model(ids[pol],
                                      output_hidden_states=True).hidden_states
            for src, dst in (("robust", "cheap"), ("cheap", "robust")):
                base_mass = choice_mass(model, tok, ids[dst], si)
                for b, tag in ((best_b, "best"), (low_b, "control")):
                    pos = ids[dst].shape[1] - 1
                    with patch_block(model, b, pos, caps[src][b + 1][0, -1]):
                        m = choice_mass(model, tok, ids[dst], si)
                    rows.append({
                        "si": si, "src": src, "dst": dst, "block_tag": tag,
                        "block": b,
                        "src_opt_mass_before": base_mass[tgt[src]],
                        "src_opt_mass_after": m[tgt[src]],
                        "dst_opt_mass_before": base_mass[tgt[dst]],
                        "dst_opt_mass_after": m[tgt[dst]],
                        "flipped": int(max(range(4), key=lambda j: m[j])
                                       == tgt[src])})
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    cells = {}
    for tag in ("best", "control"):
        sub = [r for r in rows if r["block_tag"] == tag]
        cells[tag] = {
            "n": len(sub),
            "flip_rate": sum(r["flipped"] for r in sub) / len(sub)
            if sub else None,
            "src_mass_gain": sum(r["src_opt_mass_after"]
                                 - r["src_opt_mass_before"]
                                 for r in sub) / len(sub) if sub else None}
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "best_block": best_b, "control_block": low_b,
         "cells": cells, "rows": rows}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"M02 landed: best-block flip {cells['best']['flip_rate']}, "
          f"control flip {cells['control']['flip_rate']}")
    return 0


# ── M03: cross-model causal roles (card E24-S3-M03) ─────────────────────────────────
# The question in plain language: is "where the policy lives" a shared architectural
# fact — the same relative depth in a different family — or idiosyncratic to one model?
# The M01 procedure verbatim on the second instruct family; the comparison is the two
# transfer curves on NORMALIZED depth.
# DESIGN CHECK: identical procedure and nulls as M01 (only the model changes); curves
# compared at normalized depth because block counts differ; per-block cells retained.

def arm_m03() -> int:
    cell = "E24-S3-M03"
    out = S3 / "M" / "M03"
    rc = arm_m01(model_name="HuggingFaceTB/SmolLM2-1.7B-Instruct",
                 out_dir=out, cell=cell)
    # comparative summary against M01, at normalized depth
    try:
        m1 = json.loads((S3 / "M" / "M01" / "verdict.json"
                         ).read_text(encoding="utf-8"))
        m3 = json.loads((out / "verdict.json").read_text(encoding="utf-8"))
        def norm_curve(d):
            blocks = sorted(int(k) for k in d["per_block"])
            top = max(blocks) or 1
            return {round(b / top, 2): d["per_block"][str(b)]["mean_transfer"]
                    for b in blocks}
        (out / "comparison.json").write_text(json.dumps(
            {"qwen_curve_normdepth": norm_curve(m1),
             "smollm_curve_normdepth": norm_curve(m3)}, indent=1),
            encoding="utf-8", newline="\n")
    except Exception as e:                                                        # noqa: BLE001
        print(f"  comparison deferred: {e}")
    return rc


# ── M04: prompt / activation / adapter equivalence (card E24-S3-M04) ─────────────────
# The question in plain language: the same standing policy delivered three ways — as a
# prompt line, as a patched activation, as trained LoRA weights — does it bend the
# choice distribution the same way? The metric is agreement of per-scenario SHIFT
# vectors (condition minus bare), pairwise across routes.
# DESIGN CHECK: needs M01 (best block) and the S02 adapters — queue-enforced; all
# three routes measured on the SAME scenarios with the same readout (choice mass over
# committed answers); cells per scenario; cosine and top-option agreement both reported
# (a cosine can be high while the argmax disagrees, L168 spirit).

def arm_m04() -> int:
    cell = "E24-S3-M04"
    t0 = time.time()
    out = S3 / "M" / "M04"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from peft import PeftModel                                                    # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from runners.s3_lib import choice_probs, utilities, PROFILE_W                 # noqa: PLC0415
    m01 = json.loads((S3 / "M" / "M01" / "verdict.json"
                      ).read_text(encoding="utf-8"))
    curve = {int(k): v["mean_transfer"] for k, v in m01["per_block"].items()
             if v["mean_transfer"] is not None}
    best_b = max(curve, key=curve.get)
    adapter_dir = (S3 / "S" / "S02" / "adapter_Qwen2.5-_robust_c1")
    pol = "robust"
    rows = []
    acquire_gpu_lock("s3_m04")
    try:
        tok = AutoTokenizer.from_pretrained(MODEL)
        base = AutoModelForCausalLM.from_pretrained(
            MODEL, dtype=torch.float16).to("cuda").eval()
        for si in range(N_SCEN):
            probs = choice_probs(utilities(si, 1, DOMAIN), PROFILE_W[pol])
            tgt = max(range(4), key=lambda j: probs[j])
            ids_0 = build_prompt_ids(tok, si, None)
            ids_p = build_prompt_ids(tok, si, pol)
            bare = choice_mass(base, tok, ids_0, si)
            prompt_m = choice_mass(base, tok, ids_p, si)
            with torch.no_grad():
                hp = base(ids_p, output_hidden_states=True).hidden_states
            with patch_block(base, best_b, ids_0.shape[1] - 1,
                             hp[best_b + 1][0, -1]):
                act_m = choice_mass(base, tok, ids_0, si)
            adapted = PeftModel.from_pretrained(base, str(adapter_dir)).eval()
            adapt_m = choice_mass(adapted, tok, ids_0, si)
            adapted.unload()
            rows.append({"si": si, "tgt": tgt, "bare": bare,
                         "prompt": prompt_m, "activation": act_m,
                         "adapter": adapt_m})
        del base
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()

    import math                                                                   # noqa: PLC0415
    def shift(v, r):
        return [v[r][k] - v["bare"][k] for k in range(4)]
    def cos(a, b):
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return (sum(x * y for x, y in zip(a, b)) / (na * nb)
                if na > 1e-9 and nb > 1e-9 else None)
    routes = ("prompt", "activation", "adapter")
    agree = {}
    for i in range(len(routes)):
        for j in range(i + 1, len(routes)):
            r1, r2 = routes[i], routes[j]
            cs = [cos(shift(v, r1), shift(v, r2)) for v in rows]
            cs = [c for c in cs if c is not None]
            tops = [int(max(range(4), key=lambda k: v[r1][k])
                        == max(range(4), key=lambda k: v[r2][k]))
                    for v in rows]
            agree[f"{r1}|{r2}"] = {
                "mean_shift_cosine": sum(cs) / len(cs) if cs else None,
                "top_option_agreement": sum(tops) / len(tops)}
    per_route = {r: {"mean_gain_on_target": sum(
        v[r][v["tgt"]] - v["bare"][v["tgt"]] for v in rows) / len(rows)}
        for r in routes}
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "policy": pol, "best_block": best_b,
         "pairwise": agree, "per_route": per_route,
         "n_scenarios": len(rows)}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"M04 landed: {json.dumps(agree)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["m01", "m02", "m03", "m04"])
    a = ap.parse_args()
    return {"m01": arm_m01, "m02": arm_m02, "m03": arm_m03,
            "m04": arm_m04}[a.arm]()


if __name__ == "__main__":
    sys.exit(main())
