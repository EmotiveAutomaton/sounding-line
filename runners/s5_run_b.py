"""Stage 5 bridge cards (brief §6 B01-B03): the unmet floor on L255/A07b, the only Stage-4
causal-use-during-inversion result.

DESIGN CHECK (2026-08-29; option order fixed per artifact across arms after L283, the same day)
lessons read: LESSONS §3 (steering with the true class's direction is an oracle
  intervention: the claim lives in the controls; read the baseline marginal before
  steering deltas; report per-tendency cells; a dev-selected locus and dose are part of
  the instrument), §4 (record measured values; hooks removed and replay verified).
gates and bands:
  - B01 primary: congruent minus zero on the held-out maker's tendency log score at a
    second checkpoint (Qwen2.5-3B-Instruct, same family; SmolLM2-1.7B-Instruct, second
    family), directions fit on the other maker's artifacts, two folds; NULL: 0;
    ALTERNATIVE: at or above the 0.03-nat threshold with the random and incongruent arms
    quiet (each under half the congruent effect or under 0.02 nats); the nearest-centroid
    decode of the same directions is reported and a fold with decode under chance is
    marked void for the steering read. Failure direction guarded: a generic activation
    effect shows as a loud random arm and reads as affect steering, not causal use.
  - B02: the same signature on a second artifact domain (fresh scenes, artifacts written
    by the two makers under the four tendencies with accept-time realization), at the
    anchor and the second checkpoint; the checkpoint x domain x steering cells are
    reported before any pooling; a domain-bound result stays bounded.
  - B03: specificity of the congruent effect at the anchor: coordinate (frozen locus,
    shifted locus, random blocks of the same count), dose (half, frozen, double of the
    capability-passing alpha; a dose failing the capability tolerance is recorded and
    not read), sign (a reversed sign must not help), directions fit on permuted labels
    (must be quiet), and the own-answer control (the reader's own impulse choice under
    congruent steering on a neutral scene; a target gain no larger than the own-answer
    shift is answer bias). NULL for specificity: shifted, random, permuted, and reversed
    arms all quiet; ALTERNATIVE: any of them matching the frozen congruent effect, which
    narrows or closes the bridge.
  the contrast is signed in the predicted direction. under the null the congruent arm
  equals the zero arm (0 nats) and the random and incongruent arms equal it too; under
  the alternative the congruent arm exceeds zero by at least the threshold while the
  control arms stay quiet, and the failure direction guarded is upward drift in the
  control arms (a steering effect that any direction produces is not causal use of the
  tendency), reported as a rival before any support is named.
verdict bands per card, exhaustive (no silent interval), from the shared classifier on
  the primary's point and its cluster-bootstrap interval against the frozen threshold:
  COUNTEREVIDENCE when the whole interval sits below zero; SUPPORT_CANDIDATE when the
  interval excludes zero and the point reaches the threshold; INCONCLUSIVE when the
  interval excludes zero but the point falls short, or includes zero without excluding
  the threshold; VALID_NULL when the interval includes zero and excludes the threshold;
  every real interval lands in exactly one. Before any interval exists the cell carries
  VOID (no units, or every reader excluded by the gate), INSTRUMENT_FAILED (a validity
  or manipulation gate failed, named in the reason), or NOT_RUN (a dependency died);
  those three are states of the instrument, never evidence about the hypothesis.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from contextlib import ExitStack
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s5_lib                                                        # noqa: E402
from runners.s3_run_a import (ANCHOR_MODEL, FACT_CONT, SCENES2, TENDENCIES,        # noqa: E402
                              _a03_strip, _mean_logp, a01_prompt, a01_realized,
                              additive_steer)
from runners.s3_lib import perm_p                                                 # noqa: E402
from runners.s5_run_common import SMOKE, CardRun                                  # noqa: E402
from soundingline.stage5 import S5, read_json, write_json                          # noqa: E402

SEED = s5_lib.SEED0 + 100
MAKERS = ["Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct"]
CYCLE = {"anger": "care", "care": "curiosity", "curiosity": "fear", "fear": "anger"}
CHECKPOINTS = {"anchor": ANCHOR_MODEL, "qwen3b": s5_lib.CHECKPOINT2, "smollm": "HuggingFaceTB/SmolLM2-1.7B-Instruct"}
A01_DIR = REPO / "results" / "phase_2_4_stage_3" / "A" / "A01"


def load_scene_artifacts(domain: str) -> list[dict]:
    if domain == "scenes":
        src = sorted(A01_DIR.glob("art_*.json"))
    else:
        src = sorted((S5 / "B02" / "corpus").glob("art_*.json"))
    arts = []
    for p in src:
        d = json.loads(p.read_text(encoding="utf-8"))
        body = _a03_strip(d["body"])
        if len(body) > 80 and d["tendency"] in TENDENCIES:
            arts.append({"tend": d["tendency"], "body": body, "maker": d["maker"],
                         "fam": "qwen" if "qwen" in d["maker"].lower() else "smollm", "file": p.name})
    if SMOKE:
        # the smoke keeps both maker families (the folds fit on one and test on the other)
        arts = [a for a in arts if a["fam"] == "qwen"][:12] + [a for a in arts if a["fam"] == "smollm"][:12]
    return arts


def build_corpus_scenes2(run: CardRun) -> dict:
    """B02's second artifact domain: the two makers write under the four tendencies on
    the twelve fresh scenes (A06/X4's bank), accept-time realization, twins by scene."""
    out = S5 / "B02" / "corpus"
    out.mkdir(parents=True, exist_ok=True)
    n_ok = n_try = 0
    scenes = SCENES2[:3] if SMOKE else SCENES2
    for mk in MAKERS:
        short = mk.split("/")[-1][:8]
        model, tok, _ = s5_lib.load_model(mk)
        try:
            for si, scene in enumerate(scenes):
                for tend in TENDENCIES:
                    for trial in range(1 if SMOKE else 2):
                        dest = out / f"art_{short}_{si}_{tend}_{trial}.json"
                        n_try += 1
                        if dest.exists():
                            n_ok += 1
                            continue
                        for att in range(5):
                            g = s5_lib.generate(model, tok, a01_prompt(scene, tend), seed=SEED + si * 128 + trial * 16 + att, max_new=200)
                            txt = g["text"]
                            if a01_realized(txt) == tend:
                                body = txt[:txt.lower().find("next:")].strip() if "next:" in txt.lower() else txt
                                write_json(dest, {"maker": mk, "scene_i": si, "tendency": tend, "trial": trial, "body": body, "full": txt})
                                n_ok += 1
                                break
        finally:
            s5_lib.free_model(model)
    rep = {"attempted": n_try, "realized": n_ok, "yield": n_ok / max(1, n_try), "scenes": len(scenes)}
    write_json(S5 / "B02" / "corpus.json", rep)
    return rep


def _fold_directions(states, arts, fit_idx, locus, tends):
    import torch                                                                  # noqa: PLC0415
    cents, dirs = {}, {}
    for b in locus:
        cb = {}
        for t in tends:
            idx = [i for i in fit_idx if arts[i]["tend"] == t]
            cb[t] = torch.stack([states[i][b] for i in idx]).mean(0)
        cents[b] = cb
        allm = torch.stack(list(cb.values())).mean(0)
        dirs[b] = {t: (cb[t] - allm) / (cb[t] - allm).norm() for t in tends}
    return cents, dirs


def _steer_ctx(model, locus, dmap, alpha):
    stack = ExitStack()
    if dmap is None or alpha == 0.0:
        return stack
    for b in locus:
        stack.enter_context(additive_steer(model, [b], dmap[b], alpha))
    return stack


def _dose_ladder(model, tok, locus, dirs, tends, mean_norm, fracs=(0.12, 0.08, 0.04)):
    def fact_logp(dmap, alpha):
        with _steer_ctx(model, locus, dmap, alpha):
            vals = [_mean_logp(model, tok, "A plain fact: ", f) for f in FACT_CONT]
        return sum(vals) / len(vals)
    base = fact_logp(None, 0.0)
    ladder, alpha, chosen = {}, None, None
    for frac in fracs:
        a_try = frac * mean_norm
        worst = min(fact_logp({b: dirs[b][t] for b in locus}, a_try) for t in tends)
        ok = worst >= base - 0.15 * abs(base)
        ladder[str(frac)] = {"alpha": a_try, "worst_fact_logp": worst, "capability_ok": ok}
        if ok and alpha is None:
            alpha, chosen = a_try, frac
    return ladder, alpha, chosen


def _score(model, tok, body: str, tends, rng) -> dict:
    return s5_lib.candidate_likelihood(model, tok, body, {t: TENDENCIES[t] for t in tends}, rng, unknown=False)


def run_bridge(run: CardRun, checkpoint_key: str, domain: str, arts: list[dict], conditions: list[str],
               extra_arms: dict | None = None) -> list[dict]:
    """The A07b procedure on one checkpoint and one artifact domain: two maker folds,
    nearest-centroid decode, the prompted inference under zero / congruent / incongruent
    / random steering at the largest capability-passing dose; extra arms (B03) add
    coordinate, dose, sign, and permuted-label conditions."""
    import torch                                                                  # noqa: PLC0415
    from soundingline.probe.interventions import capture_block_states             # noqa: PLC0415
    reader = CHECKPOINTS[checkpoint_key]
    tends = sorted(TENDENCIES)
    rows = []
    model, tok, _ = s5_lib.load_model(reader)
    try:
        states = [[h.mean(0) for h in capture_block_states(model, tok, a["body"], device="cuda")] for a in arts]
        n_blocks = len(states[0])
        third = n_blocks // 3
        locus = list(range(third, 2 * third, 2))
        folds = [("smollm", "qwen"), ("qwen", "smollm")]
        for fit_fam, test_fam in folds:
            fit_idx = [i for i, a in enumerate(arts) if a["fam"] == fit_fam]
            test_idx = [i for i, a in enumerate(arts) if a["fam"] == test_fam]
            if len(fit_idx) < 8 or not test_idx:
                continue
            cents, dirs = _fold_directions(states, arts, fit_idx, locus, tends)
            mean_norm = float(torch.stack([states[i][locus[0]] for i in fit_idx]).norm(dim=1).mean())
            ladder, alpha, frac = _dose_ladder(model, tok, locus, dirs, tends, mean_norm)
            fold = f"{fit_fam}->{test_fam}"
            # permuted-label directions (B03 control): fit with shuffled tendency labels
            perm_dirs = None
            if extra_arms and "permuted" in extra_arms:
                lab = [arts[i]["tend"] for i in fit_idx]
                random.Random(SEED + 9).shuffle(lab)
                fake = [dict(arts[i], tend=lab[j]) for j, i in enumerate(fit_idx)]
                fake_states = [states[i] for i in fit_idx]
                _, perm_dirs = _fold_directions(fake_states, fake, list(range(len(fake))), locus, tends)
            shifted = [min(n_blocks - 1, b + 3) for b in locus]
            rnd_blocks = random.Random(SEED + 11).sample([b for b in range(2, n_blocks - 1) if b not in locus], len(locus))
            for i in test_idx:
                a = arts[i]
                uid = f"{checkpoint_key}|{domain}|{a['file']}"
                if run.is_done(reader, uid):
                    continue
                dist = {t: sum(float((states[i][b] - cents[b][t]).norm()) for b in locus) for t in tends}
                decode_pred = min(dist, key=dist.get)
                body = (f"Someone wrote this short passage about a situation they were in:\n\"{a['body']}\"\n\n"
                        f"Which impulse was driving the writer?")
                g = torch.Generator().manual_seed(SEED + 7100 + i)
                rand_dirs = {}
                for b in locus:
                    d = dirs[b][a["tend"]]
                    r = torch.randn(d.shape[0], generator=g)
                    r = r - (r @ d) * d
                    rand_dirs[b] = r / r.norm()
                arms = {"zero": (None, 0.0, locus)}
                if alpha is not None:
                    cong = {b: dirs[b][a["tend"]] for b in locus}
                    arms["congruent"] = (cong, alpha, locus)
                    arms["incongruent"] = ({b: dirs[b][CYCLE[a["tend"]]] for b in locus}, alpha, locus)
                    arms["random"] = (rand_dirs, alpha, locus)
                    if extra_arms:
                        if "coordinate" in extra_arms:
                            # the same direction vectors applied at shifted or random blocks
                            arms["shifted"] = ({sb: dirs[b][a["tend"]] for sb, b in zip(shifted, locus)}, alpha, shifted)
                            arms["random_blocks"] = ({rb: dirs[b][a["tend"]] for rb, b in zip(rnd_blocks, locus)}, alpha, rnd_blocks)
                        if "dose" in extra_arms:
                            arms["half"] = (cong, alpha / 2, locus)
                            arms["double"] = (cong, alpha * 2, locus)
                        if "sign" in extra_arms:
                            arms["reversed"] = (cong, -alpha, locus)
                        if "permuted" in extra_arms and perm_dirs is not None:
                            arms["permuted"] = ({b: perm_dirs[b][a["tend"]] for b in locus}, alpha, locus)
                for cond in conditions + list(extra_arms or {}):
                    key = {"coordinate": None, "dose": None, "sign": None, "permuted": "permuted"}.get(cond, cond)
                    names = {"coordinate": ["shifted", "random_blocks"], "dose": ["half", "double"], "sign": ["reversed"]}.get(cond, [key] if key else [])
                    for name in names:
                        if name not in arms:
                            continue
                        dmap, al, blocks = arms[name]
                        # every arm of an artifact is asked under the SAME option order (L283:
                        # the readout's letter effect is two nats, so differing orders unpair
                        # the contrast); the shared generator's draw was the 2026-08-29 defect
                        with _steer_ctx(model, blocks, dmap, al):
                            r = _score(model, tok, body, tends, random.Random(SEED + 7000 + i))
                        ls = s5_lib.log_score(r["probs"], a["tend"]) if r["valid"] else None
                        run.row(reader, uid, uid, f"{checkpoint_key}|{domain}|{name}",
                                {"checkpoint": checkpoint_key, "domain": domain, "steer": name, "fold": fold},
                                a["tend"], "construction", "artifact_only", r, ls,
                                intervention={"arm": name, "alpha": al, "blocks": blocks},
                                extra={"decode_pred": decode_pred, "maker": a["maker"], "artifact": a["file"],
                                       "dose_frac": frac, "capability_ladder": ladder if name == "zero" else None})
                        rows.append({"fold": fold, "cond": name, "truth": a["tend"], "ls": ls, "uid": uid,
                                     "decode_pred": decode_pred, "valid": r["valid"]})
                # own-answer control (B03): the reader's own impulse on a neutral scene under congruent steering
                if extra_arms and "own_answer" in extra_arms and alpha is not None:
                    scene = "You find the workshop door standing open at dawn."
                    own_body = f"Situation: {scene}\nWhich impulse is yours right now?"
                    r0 = _score(model, tok, own_body, tends, random.Random(SEED + 7500 + i))
                    with _steer_ctx(model, locus, {b: dirs[b][a["tend"]] for b in locus}, alpha):
                        r1 = _score(model, tok, own_body, tends, random.Random(SEED + 7500 + i))
                    if r0["valid"] and r1["valid"]:
                        shift = r1["probs"][a["tend"]] - r0["probs"][a["tend"]]
                        run.row(reader, uid, uid, f"{checkpoint_key}|{domain}|own_answer",
                                {"checkpoint": checkpoint_key, "domain": domain, "steer": "own_answer", "fold": fold},
                                a["tend"], "construction", "artifact_only", r1, None,
                                extra={"own_answer_shift": shift, "control": "own_answer"})
                run.unit_complete(reader, uid)
    finally:
        s5_lib.free_model(model)
    return rows


def _analyze(run: CardRun, primary_ckpt: str, domain: str) -> dict:
    rows = [r for r in run.rows() if r["valid"] and r["primary_score"] is not None and r["factors"].get("steer") != "own_answer"]
    out = {"cells": {}, "per_fold": {}}
    zero = {(r["factors"]["checkpoint"], r["factors"]["domain"], r["unit_id"]): r["primary_score"] for r in rows if r["factors"]["steer"] == "zero"}
    contrasts = {}
    for ck in sorted({r["factors"]["checkpoint"] for r in rows}):
        for cond in sorted({r["factors"]["steer"] for r in rows} - {"zero"}):
            sub = [r for r in rows if r["factors"]["checkpoint"] == ck and r["factors"]["steer"] == cond and (ck, r["factors"]["domain"], r["unit_id"]) in zero]
            diffs = {r["unit_id"]: r["primary_score"] - zero[(ck, r["factors"]["domain"], r["unit_id"])] for r in sub}
            if len(diffs) >= 2:
                ci = s5_lib.cluster_bootstrap_ci(diffs, SEED + 3)
                obs, pv = perm_p(list(diffs.values()), SEED + 4)
                contrasts[f"{ck}|{cond}"] = {**ci, "perm_p": pv}
        # decode balanced accuracy per checkpoint
        zr = [r for r in rows if r["factors"]["checkpoint"] == ck and r["factors"]["steer"] == "zero"]
        tends = sorted(TENDENCIES)
        out["cells"][ck] = {"decode_balanced": s5_lib.balanced_accuracy([r["extra"]["decode_pred"] for r in zr], [r["truth"] for r in zr], tends),
                            "prompted_balanced_zero": s5_lib.balanced_accuracy([r["pred"] for r in zr], [r["truth"] for r in zr], tends),
                            "n": len(zr)}
        for fold in sorted({r["factors"]["fold"] for r in zr}):
            fr = [r for r in zr if r["factors"]["fold"] == fold]
            out["per_fold"][f"{ck}|{fold}"] = {"decode_balanced": s5_lib.balanced_accuracy([r["extra"]["decode_pred"] for r in fr], [r["truth"] for r in fr], tends),
                                              "n": len(fr)}
    own = [r["extra"]["own_answer_shift"] for r in run.rows() if r["factors"].get("steer") == "own_answer"]
    out["own_answer_shift"] = (sum(own) / len(own)) if own else None
    out["contrasts"] = contrasts
    prim = contrasts.get(f"{primary_ckpt}|congruent")
    if prim is None:
        return {**out, "verdict": {"outcome": "VOID", "reason": "no congruent arm (no capability-passing dose or no rows)"}}
    quiet = {}
    for cond in ("incongruent", "random", "shifted", "random_blocks", "permuted", "reversed"):
        c = contrasts.get(f"{primary_ckpt}|{cond}")
        if c is not None:
            quiet[cond] = (abs(c["point"]) < max(0.02, abs(prim["point"]) / 2)) or (cond in ("incongruent", "reversed") and c["point"] < 0)
    verdict = run.classify(prim, run.threshold(0.03))
    out["controls_quiet"] = quiet
    if verdict["outcome"] == "SUPPORT_CANDIDATE" and not all(quiet.values()):
        verdict["outcome"] = "INCONCLUSIVE"
        verdict["reason"] += "; a control arm is not quiet (" + ", ".join(k for k, v in quiet.items() if not v) + ")"
    decode_ok = out["cells"].get(primary_ckpt, {}).get("decode_balanced", 0) >= 0.25
    if not decode_ok:
        verdict["note"] = "the directions' own decode sits under chance; the steering read is marked void for that reason"
        verdict["decode_void"] = True
    return {**out, "verdict": verdict}


def arm_b01() -> int:
    run = CardRun("B01", "s5_run_b.py")
    arts = load_scene_artifacts("scenes")
    with s5_lib.GpuSession("s5_b01") as gs:
        for ck in ("qwen3b", "smollm"):
            if ck == "qwen3b" and not run.design.get("checkpoint2", {}).get("admitted", True):
                continue
            run_bridge(run, ck, "scenes", arts, ["zero", "congruent", "incongruent", "random"])
    res = _analyze(run, "qwen3b", "scenes")
    res2 = _analyze(run, "smollm", "scenes")
    ck2_admitted = bool(run.design.get("checkpoint2", {}).get("admitted", True))
    # the primary is the second checkpoint that passed the reader gate: the same-family 3B
    # when admitted, else the second family carries the primary and the 3B is recorded absent
    verdict = dict(res["verdict"]) if ck2_admitted else dict(res2["verdict"])
    verdict["primary_checkpoint"] = "qwen3b" if ck2_admitted else "smollm (Qwen2.5-3B refused by the I02 gate)"
    verdict["second_family_verdict"] = res2["verdict"]
    verdict["qwen3b_verdict"] = res["verdict"] if ck2_admitted else {"outcome": "VOID", "reason": "checkpoint refused by the I02 reader gate"}
    verdict["l255_pointer"] = "results/phase_2_4_stage_3/A/A07/verdict_b.json"
    run.finish({"analysis_qwen3b": res, "analysis_smollm": res2, "n_artifacts": len(arts)},
               {"exec": "COMPLETE", "primary": "congruent minus zero, second checkpoint, controls quiet", **verdict}, gs.held_s,
               rival="a generic activation effect (the random arm) or answer bias (own-answer shift, B03)")
    return 0


def arm_b02() -> int:
    run = CardRun("B02", "s5_run_b.py")
    with s5_lib.GpuSession("s5_b02") as gs:
        corpus = build_corpus_scenes2(run)
        arts = load_scene_artifacts("scenes2")
        if corpus["yield"] < 0.8 or len(arts) < 16:
            run.finish({"corpus": corpus}, {"exec": "COMPLETE", "outcome": "INSTRUMENT_FAILED",
                                            "reason": f"second-domain corpus yield {corpus['yield']:.2f} or size {len(arts)} under floor"}, gs.held_s)
            return 0
        for ck in ("anchor", "qwen3b"):
            if ck == "qwen3b" and not run.design.get("checkpoint2", {}).get("admitted", True):
                continue
            run_bridge(run, ck, "scenes2", arts, ["zero", "congruent", "incongruent", "random"])
    res = _analyze(run, "anchor", "scenes2")
    res2 = _analyze(run, "qwen3b", "scenes2")
    b01 = read_json(S5 / "B01" / "verdict.json") if (S5 / "B01" / "verdict.json").exists() else {}
    interaction = {"domain2_anchor_congruent": res["contrasts"].get("anchor|congruent"),
                   "domain2_qwen3b_congruent": res2["contrasts"].get("qwen3b|congruent"),
                   "domain1_qwen3b_congruent": (b01.get("point"), b01.get("ci")),
                   "domain1_anchor_congruent_L255": "results/phase_2_4_stage_3/A/A07/verdict_b.json"}
    verdict = res["verdict"]
    verdict["checkpoint2_verdict"] = res2["verdict"]
    verdict["interaction_cells"] = interaction
    run.finish({"corpus": corpus, "analysis_anchor": res, "analysis_qwen3b": res2, "n_artifacts": len(arts)},
               {"exec": "COMPLETE", "primary": "checkpoint x domain x steering on the second artifact domain", **verdict}, gs.held_s,
               rival="a domain-bound effect (reported as bounded, never pooled away)")
    return 0


def arm_b03() -> int:
    run = CardRun("B03", "s5_run_b.py")
    arts = load_scene_artifacts("scenes")
    with s5_lib.GpuSession("s5_b03") as gs:
        run_bridge(run, "anchor", "scenes", arts, ["zero", "congruent", "incongruent", "random"],
                   extra_arms={"coordinate": True, "dose": True, "sign": True, "permuted": True, "own_answer": True})
    res = _analyze(run, "anchor", "scenes")
    verdict = res["verdict"]
    prim = res["contrasts"].get("anchor|congruent", {})
    own = res.get("own_answer_shift")
    verdict["own_answer_control"] = {"shift": own, "target_gain": prim.get("point"),
                                     "answer_bias_suspected": (own is not None and prim.get("point") is not None and abs(own) >= abs(prim["point"]))}
    dose = {k: res["contrasts"].get(f"anchor|{k}") for k in ("half", "congruent", "double")}
    verdict["dose_response"] = {k: (v or {}).get("point") for k, v in dose.items()}
    run.finish({"analysis": res}, {"exec": "COMPLETE", "primary": "coordinate, dose, sign, permuted-label, and own-answer specificity of the congruent effect", **verdict}, gs.held_s,
               rival="a generic or answer-bias effect: shifted, random-block, permuted, reversed, or own-answer arms as loud as the congruent one")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=["B01", "B02", "B03"])
    a = ap.parse_args()
    return {"B01": arm_b01, "B02": arm_b02, "B03": arm_b03}[a.card]()


if __name__ == "__main__":
    sys.exit(main())
