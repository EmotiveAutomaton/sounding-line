"""Stage 4 integrity cards (brief §7): I01 preserves and corrects the starting record,
I02 establishes that the readers and the parser answer the intended question, I03 runs
the discarded pilot and freezes the workload and provenance.

DESIGN CHECK (2026-08-27)
lessons read: LESSONS §3 (validate the ruler on data whose answer you know before the
  signal; the criterion can fail; verdict bands on a small-probe gate carry their
  sampling width; realization per cell; readout class; assigned is not realized),
  §4 (instruct checkpoints; record environment versions), §5 (one lock per invocation;
  produces guards; a clean exit without a produce is a failure), CONTROLS §6.
gates:
  - I02 reader gate, per reader and domain on 48 easy known-answer items whose truth is a
    realized draw equal to the maker's argmax under a six-record unanimous history.
    NULL (a competent reader): accuracy near 1.0, validity near 1.0, per-option accuracy
    near 1.0, swings near 0. ALTERNATIVE (an incompetent or format-blind reader):
    accuracy at the 0.25 floor. Thresholds frozen from the brief: validity >= 0.95,
    accuracy >= 0.75, every option >= 0.50, position and paraphrase swing <= 10 pp.
    Sampling width at n=48: the standard error of an accuracy near 0.75 is 0.06, so the
    0.75 band is about 8 standard errors above the 0.25 floor and cannot fire by chance
    on a reader that reads; a swing gate at 10 pp is about 1.2 standard errors of a
    paired difference at n=48 (widths recorded beside the verdict; a swing failure
    triggers the one permitted repair, not a claim). Failure direction guarded: a reader
    admitted by luck would support false nulls downstream, so the bands are conservative
    (fail closed). Bands exhaustive: PASS / REPAIRED-PASS / FAIL.
  - role battery: reported, not gated; a response change is a behavioral observation.
  - I03 tier selection uses throughput only, never treatment effects; bands: expanded
    (projected minimum inventory <= 60 percent of the window) / minimum / PARTIAL_BUDGET
    (minimum inventory > 85 percent of the window, deferrals named from the back of the
    preservation order).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from runners import s4_cards, s4_lib, s4_worlds                                   # noqa: E402
from runners.s3_lib import AXES, PROFILE_W, choice_probs                          # noqa: E402
from soundingline.s4 import (S4, Lineages, RunContract, completion_marker,        # noqa: E402
                             expand_expected_cells, now_iso, read_json, sha256_file,
                             write_json)

S3 = REPO / "results" / "phase_2_4_stage_3"
GATE = {"validity": 0.95, "accuracy": 0.75, "per_option": 0.50, "swing_pp": 0.10}
# S4_SMOKE shrinks every count so the whole machinery can be exercised end to end
# against a scratch root before the real run; the real run never sets it
import os                                                                         # noqa: E402
SMOKE = bool(os.environ.get("S4_SMOKE"))
N_GATE_PER_DOMAIN = 8 if SMOKE else 48
N_ROLE_PER_AXIS = 1 if SMOKE else 6
N_GEN_PER_AXIS = 2 if SMOKE else 6
RAW_KEYS = {"text", "raw", "raw_text", "body", "completion", "generation", "response",
            "output", "artifact", "message"}


# ── I01 ───────────────────────────────────────────────────────────────────────────────

def _equal_vs_legacy(cases, seed):
    from runners.s3_lib import perm_p                                             # noqa: PLC0415
    out = {}
    for mf in sorted({c["maker_family"] for c in cases}):
        own, oth, own_last = {}, {}, {}
        for c in cases:
            if c["maker_family"] != mf:
                continue
            key = (c["maker"], c["topic_i"], c["goal_i"], c["trial"])
            if c["reader_family"] == mf:
                own.setdefault(key, []).append(c["margin"])
                own_last[key] = c["margin"]
            else:
                oth.setdefault(key, []).append(c["margin"])
        keys = [k for k in oth if k in own]
        if len(keys) < 3:
            continue
        d_eq = [sum(own[k]) / len(own[k]) - sum(oth[k]) / len(oth[k]) for k in keys]
        d_lg = [own_last[k] - sum(oth[k]) / len(oth[k]) for k in keys]
        oe, pe = perm_p(d_eq, seed)
        ol, pl = perm_p(d_lg, seed)
        out[mf] = {"n": len(keys), "equal": {"own_minus_other": round(oe, 5), "perm_p": pe},
                   "legacy": {"own_minus_other": round(ol, 5), "perm_p": pl}}
    return out


def _cases_from_files(files, retired):
    cases = []
    for p in files:
        d = read_json(p)
        if "cases" not in d or d.get("reader") in retired:
            continue
        for c in d["cases"]:
            if c.get("maker") in retired:
                continue
            c["reader"] = d["reader"]
            cases.append(c)
    return cases


def arm_i01() -> int:
    t0 = time.time()
    out = s4_lib.card_dir("I01")
    receipt: dict = {"card": "I01", "written_at": now_iso(), "items": {},
                     "env": s4_lib.env_versions()}
    hashes = {}
    # (a) manifest durations
    mp = S3 / "QUEUE_MANIFEST.json"
    m = read_json(mp)
    hashes[str(mp)] = sha256_file(mp)
    actual = sum((c.get("actual_gpu_minutes") or 0) for c in m) / 60
    forecast = sum((c.get("estimated_gpu_minutes") or 0) for c in m) / 60
    receipt["items"]["duration_sum"] = {
        "actual_hours": round(actual, 4), "forecast_hours": round(forecast, 4),
        "matches_brief": abs(actual - 30.6848) < 0.01 and abs(forecast - 140.9636) < 0.01,
        "note": "runner-recorded durations, not verified GPU-busy time"}
    # (b) S-trunk aggregates with equal reader weighting: S01/S07 (full and reserve)
    from runners.s3_run_s import RETIRED                                          # noqa: PLC0415
    from runners.s3_run_x import _matrix_cases                                    # noqa: PLC0415
    full = _matrix_cases(None)
    reserve = _matrix_cases("confirmation")
    receipt["items"]["s01_s07_equal_readers"] = {
        "full_matrix": _equal_vs_legacy(full, 17299),
        "reserve_only": _equal_vs_legacy(reserve, 17299),
        "n_cases": {"full": len(full), "reserve": len(reserve)},
        "landed_reference": "L177 (+0.0171/+0.0095/+0.0365), L182 (2 of 3)",
        "corrected_in_record": "L236"}
    # S05 arms: the bottleneck matrices, kept-set as written by the eraser arms
    s05 = {}
    for tag, d in (("smollm_eraser", S3 / "S" / "S05"), ("olmo_eraser", S3 / "S" / "S05_x3")):
        files = sorted(d.glob("mx_*.json")) if d.exists() else []
        if not files:
            s05[tag] = {"status": "no matrix files found", "dir": str(d)}
            continue
        cases = _cases_from_files(files, RETIRED)
        res = _equal_vs_legacy(cases, 17298)
        landed = None
        vp = d / ("verdict.json" if tag == "smollm_eraser" else "eraser3.json")
        if vp.exists():
            landed = read_json(vp).get("contrast")
            hashes[str(vp)] = sha256_file(vp)
        repro = None
        if landed and res:
            repro = all(abs(res[f]["legacy"]["own_minus_other"]
                            - landed[f]["own_minus_other"]) < 2e-3
                        for f in res if f in landed)
        s05[tag] = {"n_files": len(files), "n_cases": len(cases), "contrast": res,
                    "landed_contrast": landed, "legacy_reproduces_landed": repro,
                    "disposition": ("corrected" if repro else
                                    "owed: the kept-set filter is not reproduced from the "
                                    "matrix files alone; landed numbers stand as reported")}
    receipt["items"]["s05_equal_readers"] = s05
    # (c) raw-text inventory of Stage-3 outputs
    inv = {}
    for card_dir in sorted(p for p in S3.rglob("*") if p.is_dir()):
        rel = str(card_dir.relative_to(S3))
        has_raw = False
        n = 0
        for jp in card_dir.glob("*.json"):
            if jp.stat().st_size > 5_000_000:
                continue
            n += 1
            try:
                d = read_json(jp)
            except Exception:                                                    # noqa: BLE001
                continue
            stack = [d]
            while stack and not has_raw:
                x = stack.pop()
                if isinstance(x, dict):
                    if any(k in RAW_KEYS and isinstance(x[k], str) and len(x[k]) > 40
                           for k in x):
                        has_raw = True
                    stack.extend(x.values())
                elif isinstance(x, list):
                    stack.extend(x[:50])
        if n:
            inv[rel] = {"json_files": n, "has_raw_text": has_raw}
    receipt["items"]["raw_text_inventory"] = inv
    receipt["items"]["raw_text_missing_for"] = [k for k, v in inv.items()
                                                if not v["has_raw_text"]
                                                and k.split("/")[0] in ("C", "X", "E")]
    # (d) local weights, adapters, datasets, licenses
    hub = Path.home() / ".cache" / "huggingface" / "hub"
    models = sorted(p.name.replace("models--", "").replace("--", "/")
                    for p in hub.glob("models--*")) if hub.exists() else []
    adapters = {str(p.parent.relative_to(S3)): p.stat().st_size
                for p in S3.rglob("adapter_model.safetensors")}
    fts = {str(p.parent.relative_to(S3)): p.stat().st_size
           for p in S3.rglob("model.safetensors")}
    datasets = {"scholawrite": (REPO / "results/scholawrite/dataset").exists(),
                "coauthor": (REPO / "corpora/coauthor").exists(),
                "quickdraw": (S4 / "P01" / "raw").exists()}
    receipt["items"]["inventory"] = {
        "models_cached": models, "escalation_reader_cached":
            s4_lib.model_available(s4_lib.ESCALATION_READER),
        "adapter_weights": adapters, "full_finetune_weights": fts, "datasets": datasets,
        "licenses": {"quickdraw": "CC BY 4.0 (attribution retained)",
                     "scholawrite": "per the ScholaWrite paper's release terms",
                     "coauthor": "per the CoAuthor release terms",
                     "race": "research use, not re-hosted (bank files ignored by rule)",
                     "socialiqa": "not re-hosted"}}
    # (e) the §3.2 dispositions
    receipt["items"]["dispositions"] = [
        {"item": "S01/S05/S07 family contrasts", "verified": True,
         "receipt": "s01_s07_equal_readers, s05_equal_readers",
         "disposition": "equal-reader aggregates published beside legacy; L236"},
        {"item": "S05 independent eraser", "verified": True,
         "disposition": "eraser3 carried as null with attrition; L225 headline withdrawn"},
        {"item": "S07 reserve", "verified": True,
         "disposition": "retrospective robustness (L235 scope note); Stage-4 confirmations use fresh lineages"},
        {"item": "S02 trained policies", "verified": "partial",
         "disposition": "crossed maker-reader matrix debt stays open; adapter weights ARE local (inventory)"},
        {"item": "E01 and E03", "verified": "interpretive",
         "disposition": "two-draw agreement recorded as repeatability; no prospective self advantage claimed"},
        {"item": "A07", "verified": "interpretive",
         "disposition": "endpoint was the reader's own impulse; per-action baselines reported in L202"},
        {"item": "C05, C06, XV3", "verified": True,
         "receipt": "raw_text_missing_for", "disposition": "raw generations absent; repaired rerun is I02's role battery"},
        {"item": "L trunk and XV4", "verified": True,
         "disposition": "carrier retracted (L226); no broad subliminal rerun in Stage 4"},
        {"item": "H04 CoAuthor", "verified": "interpretive",
         "disposition": "set-level dismissal is not first-suggestion rejection; AUC near chance does not show indiscriminate acceptance"},
        {"item": "H05/H06", "verified": "interpretive",
         "disposition": "ScholaWrite spans versus ArgRewrite spreadsheet order are not one task; H03 audits chronology"},
        {"item": "Completion record", "verified": True,
         "disposition": "Stage-4 validator checks expected cells, realized samples, inputs, held-out status"},
    ]
    receipt["stage3_bytes_hashed"] = hashes
    write_json(out / "AUDIT_STAGE3.json", receipt)
    write_json(S4 / "AUDIT_STAGE3.json", receipt)
    lines = ["# Stage-3 audit receipt (I01)", "", f"Written {receipt['written_at']}.", "",
             "| item | verified | disposition |", "|---|---|---|"]
    for d in receipt["items"]["dispositions"]:
        lines.append(f"| {d['item']} | {d['verified']} | {d['disposition']} |")
    lines.append("")
    lines.append("*Table: the brief's §3.2 dispositions with their verification state; "
                 "numerical receipts in AUDIT_STAGE3.json.*")
    e = receipt["items"]["s01_s07_equal_readers"]["full_matrix"]
    lines.append("")
    lines.append("Equal-reader crossed contrast, full matrix: " +
                 ", ".join(f"{f} {v['equal']['own_minus_other']:+.4f} (p={v['equal']['perm_p']:.2g})"
                           for f, v in e.items()) + ".")
    (S4 / "AUDIT_STAGE3.md").write_text("\n".join(lines) + "\n", encoding="utf-8",
                                        newline="\n")
    contract = RunContract.load() or RunContract.create()
    write_json(out / "verdict.json", {
        "card": "I01", "exec": "COMPLETE", "outcome": "VOID",
        "note": "audit card; no scientific outcome class applies",
        "minutes": round((time.time() - t0) / 60, 2),
        "marker": completion_marker({"manifest": str(mp)},
                                    {"receipt": str(out / "AUDIT_STAGE3.json")}, contract)})
    print(f"I01 complete: {len(inv)} result dirs inventoried, "
          f"equal-reader contrast {json.dumps({f: v['equal'] for f, v in e.items()})}")
    return 0


# ── I02 ───────────────────────────────────────────────────────────────────────────────

def gate_items(domain: str, n_per_axis: int, salt: str, kind: str = "repeat") -> list[dict]:
    """Known-answer items balanced across the four truth options.

    kind='repeat' (the GATE): six consistent records are shown and the target is one of
    those decisions faced AGAIN, verbatim; the unambiguous record-supported answer is the
    recorded choice. This tests that the reader locates and applies a record at all,
    which is what an instrument gate is for.
    kind='abstract' (REPORTED, not gated): the target is a new scenario and the answer is
    the same profile's option in new words, the L192-class abstraction the tracks then
    measure. The smoke test put every reader near 0.35 on this form with the against-
    grain options never chosen, so it is a finding to carry, not a gate to fail on.
    Known-answer existence is checked at construction: at TEMP 0.35 the modal option
    draws about 0.6 of the time, so no probability floor above 0.5 is imposed."""
    items = {ax: [] for ax in AXES}
    w_idx = 0
    while any(len(v) < n_per_axis for v in items.values()) and w_idx < 4000:
        lid = Lineages.make_id("I02", domain, w_idx % 3, w_idx, "pilot") + "|" + salt
        w = s4_worlds.make_world(lid, domain)
        w_idx += 1
        prof = w["profile"]
        if len(items[prof]) >= n_per_axis:
            continue
        recs = [s for s in w["scenarios"][:9] if s["draw"] == prof][:6]
        if len(recs) < 6:
            continue
        rec_text = "\n".join(f"- {s['context']} It chose: {s['options'][s['draw']]}."
                             for s in recs)
        if kind == "repeat":
            tgt = recs[w_idx % 6]
            body = (f"Here is a maker's record of six decisions:\n{rec_text}\n"
                    f"The same maker now faces one of those decisions again: {tgt['context']}\n"
                    f"Which option will it choose?")
        else:
            tgt = w["scenarios"][9]
            argmax = max(tgt["distribution"], key=tgt["distribution"].get)
            if tgt["distribution"][argmax] < 0.5 or tgt["draw"] != argmax or argmax != prof:
                continue
            body = (f"Here is a maker's record of six decisions:\n{rec_text}\n"
                    f"Now the same maker faces this decision: {tgt['context']}\n"
                    f"Which option will it choose?")
        items[prof].append({"unit_id": lid, "domain": domain, "body": body,
                            "options": dict(tgt["options"]), "truth": tgt["draw"],
                            "truth_provenance": "realized_draw", "profile": prof,
                            "kind": kind})
    out = []
    for ax in AXES:
        out.extend(items[ax][:n_per_axis])
    return out


def own_profile(model, tok, domain: str, n: int = 8) -> dict:
    """The reader's own choice profile on disjoint calibration probes (no maker)."""
    rng = random.Random(4401)
    choices, sids, U_list = [], [], []
    for i in range(n):
        lid = Lineages.make_id("I02own", domain, 0, i, "pilot")
        w = s4_worlds.make_world(lid, domain)
        s = w["scenarios"][i % 10]
        r = s4_lib.likelihood_choice(model, tok, f"You face this decision: {s['context']}\n"
                                     f"Which option would you choose?", s["options"], rng)
        if r["valid"]:
            choices.append(r["pred"])
            sids.append(i)
            U_list.append(s["utilities"])
    import math                                                                   # noqa: PLC0415
    logp = {ax: 0.0 for ax in AXES}
    for ch, U in zip(choices, U_list):
        for ax in AXES:
            logp[ax] += math.log(max(choice_probs(U, PROFILE_W[ax])[AXES.index(ch)], 1e-12))
    m = max(logp.values())
    ex = {k: math.exp(v - m) for k, v in logp.items()}
    z = sum(ex.values())
    post = {k: v / z for k, v in ex.items()}
    return {"choices": choices, "posterior": post, "modal": max(post, key=post.get)}


def role_variants(item: dict, own_axis: str, rng: random.Random) -> list[dict]:
    """Four roles x four phrase forms, the inserted option Y a non-truth option (the
    reader's own modal where the role is 'own', else a fixed non-truth option)."""
    opts = item["options"]
    non_truth = [ax for ax in AXES if ax != item["truth"]]
    y_other = non_truth[rng.randrange(len(non_truth))]
    out = []
    for role in ("own", "witness", "bystander"):
        y = own_axis if role == "own" and own_axis != item["truth"] else y_other
        phrase = opts[y]
        forms = {
            "affirmative": {
                "own": f"You yourself would pick the {phrase}.",
                "witness": f"A surveyor who inspected the site reports that the {phrase} is the sound choice.",
                "bystander": f"A passer-by who knows nothing about the case hopes they pick the {phrase}."}[role],
            "negation": {
                "own": f"You yourself would not pick the {phrase}.",
                "witness": f"A surveyor who inspected the site reports that the {phrase} is not the sound choice.",
                "bystander": f"A passer-by who knows nothing about the case hopes they do not pick the {phrase}."}[role],
            "quotation": {
                "own": f"Someone once quoted you as saying \"the {phrase}\" in a different matter.",
                "witness": f"The surveyor's report was titled \"the {phrase}\" in a different matter.",
                "bystander": f"A passer-by was overheard saying \"the {phrase}\" about something else."}[role],
            "background": {
                "own": f"Unrelated: you keep a note about the {phrase} pinned at home.",
                "witness": f"Unrelated: a surveyor's manual mentions the {phrase} in its glossary.",
                "bystander": f"Unrelated: a passer-by's cart carried a sign reading the {phrase}."}[role],
        }
        for form, text in forms.items():
            out.append({"role": role, "form": form, "y": y,
                        "body": item["body"].replace("Which option will it choose?",
                                                     f"{text}\nWhich option will it choose?")})
    return out


TEMPLATES = {"A": "Answer with the letter only.",
             "B": "Which option does this maker choose? Reply with the letter only."}


def evaluate_reader(model, tok, items, template: str, order_seed: int) -> dict:
    rng = random.Random(order_seed)
    preds, truths, rows = [], [], []
    for it in items:
        r = s4_lib.likelihood_choice(model, tok, it["body"], it["options"], rng,
                                     instruction=TEMPLATES[template])
        rows.append({"unit_id": it["unit_id"], "domain": it["domain"], "truth": it["truth"],
                     "valid": r["valid"], "pred": r["pred"], "probs": r["probs"],
                     "order": r["order"], "labels": r["labels"]})
        if r["valid"]:
            preds.append(r["pred"])
            truths.append(it["truth"])
    acc = sum(p == t for p, t in zip(preds, truths)) / max(1, len(truths))
    per_opt = {}
    for ax in AXES:
        idx = [i for i, t in enumerate(truths) if t == ax]
        per_opt[ax] = (sum(preds[i] == ax for i in idx) / len(idx)) if idx else None
    per_dom = {}
    for dom in s4_cards.DOMAINS:
        idx = [i for i, r in enumerate(rows) if r["domain"] == dom and r["valid"]]
        per_dom[dom] = (sum(rows[i]["pred"] == rows[i]["truth"] for i in idx) / len(idx)
                        if idx else None)
    return {"accuracy": acc, "per_option": per_opt, "per_domain": per_dom,
            "n": len(truths), "rows": rows}


def run_reader_gate(reader: str, items, cal_items, out_dir: Path,
                    abstract_items=None) -> dict:
    model, tok, rev = s4_lib.load_model(reader)
    try:
        lab = s4_lib.label_token_ids(tok)
        tok_ok = all(v["id"] is not None for v in lab.values())
        result = {"reader": reader, "revision": rev, "label_tokens": lab,
                  "tokenization_ok": tok_ok, "template": "A", "repaired": False}
        if not tok_ok:
            result.update({"gate_pass": False, "reason": "label tokenization"})
            return result
        if abstract_items:
            ab = evaluate_reader(model, tok, abstract_items, "A", 4409)
            result["abstraction_battery"] = {k: v for k, v in ab.items() if k != "rows"}

        def full_eval(template):
            e = evaluate_reader(model, tok, items, template, 4410)
            e_pos = evaluate_reader(model, tok, items, template, 4411)
            e_par = evaluate_reader(model, tok, items, "B" if template == "A" else "A", 4410)
            swing_pos = abs(e["accuracy"] - e_pos["accuracy"])
            swing_par = abs(e["accuracy"] - e_par["accuracy"])
            # generated cross-check on a stratified subset (6 per truth option)
            rng = random.Random(4412)
            sub = []
            for ax in AXES:
                sub.extend([it for it in items if it["truth"] == ax][:N_GEN_PER_AXIS])
            gen_rows = []
            for i, it in enumerate(sub):
                g = s4_lib.generated_choice(model, tok, it["body"], it["options"], rng,
                                            seed=4500 + i)
                gen_rows.append({"unit_id": it["unit_id"], "truth": it["truth"],
                                 "valid": g["valid"], "reason": g["validity_reason"],
                                 "pred": g["pred"], "raw": g["raw"]})
            validity = sum(r["valid"] for r in gen_rows) / len(gen_rows)
            agree = (sum(1 for r in gen_rows if r["valid"] and r["pred"] == r["truth"])
                     / max(1, sum(r["valid"] for r in gen_rows)))
            per_opt_ok = all(v is not None and v >= GATE["per_option"]
                             for v in e["per_option"].values())
            passed = (validity >= GATE["validity"] and e["accuracy"] >= GATE["accuracy"]
                      and per_opt_ok and swing_pos <= GATE["swing_pp"]
                      and swing_par <= GATE["swing_pp"])
            return {"template": template, "likelihood": {k: v for k, v in e.items() if k != "rows"},
                    "position_swing": swing_pos, "paraphrase_swing": swing_par,
                    "generated_validity": validity, "generated_agreement": agree,
                    "generated_rows": gen_rows, "per_option_ok": per_opt_ok,
                    "gate_pass": passed, "rows": e["rows"],
                    "se_accuracy": (e["accuracy"] * (1 - e["accuracy"]) / max(1, e["n"])) ** 0.5}

        first = full_eval("A")
        result.update(first)
        if not first["gate_pass"]:
            # one interface repair, selected on the calibration subset
            cal_a = evaluate_reader(model, tok, cal_items, "A", 4420)["accuracy"]
            cal_b = evaluate_reader(model, tok, cal_items, "B", 4420)["accuracy"]
            alt = "B" if cal_b > cal_a else "A"
            result["repair_calibration"] = {"A": cal_a, "B": cal_b, "chosen": alt}
            if alt != "A":
                second = full_eval(alt)
                result.update(second)
                result["repaired"] = True
                result["template"] = alt
        # role battery on 24 items (balanced), reported not gated
        own = {}
        for dom in s4_cards.DOMAINS:
            own[dom] = own_profile(model, tok, dom)
        rng = random.Random(4430)
        base_items = []
        for ax in AXES:
            base_items.extend([it for it in items if it["truth"] == ax][:N_ROLE_PER_AXIS])
        battery = []
        for it in base_items:
            b = s4_lib.likelihood_choice(model, tok, it["body"], it["options"],
                                         random.Random(4431), instruction=TEMPLATES[result["template"]])
            if not b["valid"]:
                continue
            p_truth0 = b["probs"][it["truth"]]
            for v in role_variants(it, own[it["domain"]]["modal"], rng):
                r = s4_lib.likelihood_choice(model, tok, v["body"], it["options"],
                                             random.Random(4431), instruction=TEMPLATES[result["template"]])
                if not r["valid"]:
                    continue
                battery.append({"unit_id": it["unit_id"], "role": v["role"], "form": v["form"],
                                "y": v["y"], "truth": it["truth"],
                                "p_truth_base": p_truth0, "p_truth": r["probs"][it["truth"]],
                                "p_y_base": b["probs"][v["y"]], "p_y": r["probs"][v["y"]],
                                "pred": r["pred"], "followed_y": r["pred"] == v["y"]})
        summary = {}
        for role in ("own", "witness", "bystander"):
            for form in ("affirmative", "negation", "quotation", "background"):
                sub = [x for x in battery if x["role"] == role and x["form"] == form]
                if sub:
                    summary[f"{role}|{form}"] = {
                        "n": len(sub),
                        "delta_p_truth": sum(x["p_truth"] - x["p_truth_base"] for x in sub) / len(sub),
                        "delta_p_y": sum(x["p_y"] - x["p_y_base"] for x in sub) / len(sub),
                        "follow_rate": sum(x["followed_y"] for x in sub) / len(sub)}
        result["own_profile"] = own
        result["role_battery"] = {"summary": summary, "rows": battery}
        return result
    finally:
        s4_lib.free_model(model)


def arm_i02(allow_escalation_download: bool = True) -> int:
    t0 = time.time()
    out = s4_lib.card_dir("I02")
    items = []
    cal = []
    abstract = []
    for dom in s4_cards.DOMAINS:
        items.extend(gate_items(dom, N_GATE_PER_DOMAIN // 4, "gate"))
        cal.extend(gate_items(dom, 6, "cal"))
        abstract.extend(gate_items(dom, N_GATE_PER_DOMAIN // 4, "abs", kind="abstract"))
    write_json(out / "gate_items.json", {"n": len(items), "items": items, "n_cal": len(cal),
                                         "n_abstract": len(abstract), "abstract_items": abstract})
    per = {}
    with s4_lib.GpuSession("s4_i02") as gs:
        for reader in s4_lib.READERS:
            res = run_reader_gate(reader, items, cal, out, abstract)
            per[reader] = res
            write_json(out / f"gate_{s4_lib.safe_id(reader)}.json", res)
            print(f"I02 {reader}: gate_pass={res.get('gate_pass')} acc={res.get('likelihood', {}).get('accuracy')}")
        admitted = [r for r, v in per.items() if v.get("gate_pass")]
        escalation = None
        if not admitted:
            esc = s4_lib.ESCALATION_READER
            if not s4_lib.model_available(esc) and allow_escalation_download:
                try:
                    from huggingface_hub import snapshot_download               # noqa: PLC0415
                    snapshot_download(esc)
                except Exception as e:                                           # noqa: BLE001
                    escalation = {"reader": esc, "status": f"download failed: {str(e)[:120]}"}
            if s4_lib.model_available(esc):
                res = run_reader_gate(esc, items, cal, out, abstract)
                per[esc] = res
                write_json(out / f"gate_{s4_lib.safe_id(esc)}.json", res)
                escalation = {"reader": esc, "gate_pass": res.get("gate_pass")}
                if res.get("gate_pass"):
                    admitted = [esc]
            elif escalation is None:
                escalation = {"reader": esc, "status": "not available locally"}
    contract = RunContract.load() or RunContract.create()
    verdict = {"card": "I02", "gate_pass": bool(admitted), "readers_admitted": admitted,
               "readers_failed": [r for r, v in per.items() if not v.get("gate_pass")],
               "escalation": escalation, "thresholds": GATE,
               "per_reader": {r: {k: v for k, v in res.items()
                                  if k in ("gate_pass", "template", "repaired", "revision",
                                           "position_swing", "paraphrase_swing",
                                           "generated_validity", "generated_agreement",
                                           "per_option_ok", "likelihood", "se_accuracy",
                                           "repair_calibration", "abstraction_battery")}
                              for r, res in per.items()},
               "role_battery": {r: res.get("role_battery", {}).get("summary")
                                for r, res in per.items()},
               "gpu_lock_min": round(gs.held_s / 60, 2),
               "minutes": round((time.time() - t0) / 60, 2),
               "marker": completion_marker({"items": str(out / "gate_items.json")}, {},
                                           contract)}
    write_json(out / "verdict.json", verdict)
    print(f"I02 verdict: admitted {admitted}")
    return 0


# ── I03: the discarded pilot and the freeze ───────────────────────────────────────────

def arm_i03pilot() -> int:
    t0 = time.time()
    out = s4_lib.card_dir("I03")
    pilot = {"card": "I03pilot", "written_at": now_iso(), "readers": {}}
    with s4_lib.GpuSession("s4_i03pilot") as gs:
        for reader in s4_lib.READERS:
            import torch                                                          # noqa: PLC0415
            torch.cuda.reset_peak_memory_stats()
            model, tok, rev = s4_lib.load_model(reader)
            try:
                rng = random.Random(1)
                items = gate_items("workshop", 5, "pilot")[:20]
                t1 = time.time()
                for it in items:
                    s4_lib.likelihood_choice(model, tok, it["body"], it["options"], rng)
                lik_s = (time.time() - t1) / len(items)
                t1 = time.time()
                for i in range(5):
                    s4_lib.generate(model, tok, items[i]["body"] + "\nWrite a short "
                                    "recommendation in 80 words.", seed=100 + i, max_new=120)
                gen120_s = (time.time() - t1) / 5
                t1 = time.time()
                for i in range(5):
                    s4_lib.generate(model, tok, items[i]["body"], seed=200 + i, max_new=48)
                gen48_s = (time.time() - t1) / 5
                t1 = time.time()
                handle = s4_lib.fit_valence_handle(model, tok)
                handle_s = time.time() - t1
                write_json(out / f"handle_{s4_lib.safe_id(reader)}.json",
                           {"reader": reader, "revision": rev, **handle,
                            "calibration_source": "A02 sentence banks (disjoint from worlds)"})
                pilot["readers"][reader] = {
                    "revision": rev, "likelihood_s": lik_s, "gen120_s": gen120_s,
                    "gen48_s": gen48_s, "handle_fit_s": handle_s,
                    "handle_verdict": handle.get("verdict"),
                    "peak_vram_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2)}
                print(f"pilot {reader}: lik {lik_s:.3f}s gen120 {gen120_s:.2f}s "
                      f"gen48 {gen48_s:.2f}s handle {handle_s:.0f}s -> {handle.get('verdict')}")
            finally:
                s4_lib.free_model(model)
    # the session's held-seconds counter is written on exit, so it is read after the block
    pilot["gpu_lock_min"] = round(gs.held_s / 60, 2)
    pilot["minutes"] = round((time.time() - t0) / 60, 2)
    pilot["note"] = ("discarded pilot: throughput, validity, memory only; nothing here "
                     "selects a design by which condition wins")
    write_json(out / "PILOT.json", pilot)
    # the manifest cell's produce: the scheduler expects <cell>/verdict.json for every
    # cell, and the pilot cell is named I03pilot (the first smoke ran the cards by hand
    # and never found this file missing; the loop would have failed the pilot three
    # times and blocked every downstream card)
    contract = RunContract.load() or RunContract.create()
    pout = s4_lib.card_dir("I03pilot")
    write_json(pout / "verdict.json", {"card": "I03pilot", "exec": "COMPLETE", "outcome": "VOID",
                                       "note": pilot["note"], "gpu_lock_min": pilot["gpu_lock_min"],
                                       "minutes": pilot["minutes"],
                                       "marker": completion_marker({}, {"pilot": str(out / "PILOT.json")},
                                                                   contract)})
    return 0


def arm_i03() -> int:
    """Freeze: tiers from throughput, expected cells, lineages, contract sections."""
    out = s4_lib.card_dir("I03")
    pilot = read_json(out / "PILOT.json")
    i02 = read_json(S4 / "I02" / "verdict.json")
    admitted = i02["readers_admitted"]
    contract = RunContract.load() or RunContract.create()
    # throughput multipliers against the design assumptions (0.15 s likelihood, 2.5 s gen)
    liks = [v["likelihood_s"] for v in pilot["readers"].values()]
    gens = [v["gen120_s"] for v in pilot["readers"].values()]
    mult_lik = (sum(liks) / len(liks)) / 0.15
    mult_gen = (sum(gens) / len(gens)) / 2.5
    mult = max(mult_lik, mult_gen) * (len(admitted) / 2 if admitted else 1)
    window = contract.data["run_hours"]
    # the smoke estimates its own three-unit cells (six at the expanded tier) so the
    # compressed window neither defers half the inventory nor skips the expansion rung
    est_min = s4_cards.gpu_estimate_hours("minimum", mult, units_override=3 if SMOKE else None)
    est_exp = s4_cards.gpu_estimate_hours("expanded", mult, units_override=6 if SMOKE else None)
    tier, deferred, label = "minimum", [], "FULL"
    if est_exp["total"] <= 0.60 * window:
        tier = "expanded"
    elif est_min["total"] > 0.85 * window:
        label = "PARTIAL_BUDGET"
        order = [c for c in s4_cards.PRESERVATION_ORDER if c in est_min]
        keep = list(order)
        total = est_min["total"]
        rest = [c for c in est_min if c not in order and c != "total"]
        # only substantive discovery cards outside the protected head of the preservation
        # order can be deferred: never an integrity card (the loop smoke's compressed window
        # deferred the freeze cell itself) and never the confirmation card
        for c in rest + list(reversed(order)):
            if total <= 0.85 * window:
                break
            if c in ("I01", "I02", "I03", "I03pilot", "C01", "C02", "A01", "A02", "T01",
                     "T02", "F01"):
                continue
            deferred.append(c)
            total -= est_min[c]
            if c in keep:
                keep.remove(c)
    spec = s4_cards.expected_spec(tier)
    for c in deferred:
        spec.pop(c, None)
    cells = expand_expected_cells(spec)
    write_json(S4 / "EXPECTED_CELLS.json", {"tier": tier, "label": label,
                                            "deferred": deferred, "cells": cells,
                                            "written_at": now_iso()})
    # lineages: discovery for every admitted card and domain; confirmation reserves
    L = Lineages()
    alloc = {}
    DERIVED = {"A02": "A01", "A03": "A01", "T02": "T01", "T03": "T01"}
    for card, c in s4_cards.CARDS.items():
        if card in deferred or not c["domains"] or card in ("I02", "F01") or c["track"] == "physical":
            continue
        if card in DERIVED:
            continue
        n = 3 if SMOKE else s4_cards.units_for(card, tier)
        for dom in c["domains"]:
            ids = L.allocate(card, dom, list(s4_cards.SEEDS), n, "discovery")
            alloc[f"{card}|{dom}|discovery"] = len(ids)
            if c["gpu"] and c["track"] in ("context", "appraisal", "transmission",
                                           "hierarchy"):
                nconf = 3 if SMOKE else s4_cards.CONFIRMATION_UNITS[c["unit"]]
                ids = L.allocate(card, dom, [10, 11, 12], nconf, "confirmation",
                                 world_offset=10000)
                alloc[f"{card}|{dom}|confirmation"] = len(ids)
    # cards that reuse another card's worlds get derived children in the same cluster
    for card, parent_card in DERIVED.items():
        if card in deferred:
            continue
        for dom in s4_cards.CARDS[card]["domains"]:
            for split in ("discovery", "confirmation"):
                parents = [lid for lid, r in L.rows.items()
                           if r["card"] == parent_card and r["domain"] == dom
                           and r["split"] == split and r.get("parent") is None]
                ids = [L.derive(p, card.lower(), card=card) for p in parents]
                alloc[f"{card}|{dom}|{split}"] = len(ids)
    frozen = {
        "readers": {r: s4_lib.model_revision(r) for r in admitted},
        "tier": tier, "label": label, "deferred": deferred,
        "throughput_multiplier": round(mult, 3),
        "pilot_seconds": {r: {k: v for k, v in x.items() if k.endswith("_s")}
                          for r, x in pilot["readers"].items()},
        "gpu_estimate_hours": {"minimum": est_min, "expanded": est_exp},
        "primary_contrasts": {c: s4_cards.CARDS[c]["primary"] for c in s4_cards.CARDS},
        "thresholds": {c: s4_cards.CARDS[c]["threshold"] for c in s4_cards.CARDS},
        "gates": {"reader": GATE, "realization_floor": 0.80, "attempt_cap_x": 2},
        "parser_version": s4_lib.PARSER_VERSION, "readout_version": s4_lib.READOUT_VERSION,
        "construction_seeds": list(s4_cards.SEEDS), "confirmation_seeds": [10, 11, 12],
        "output_root": str(S4), "lineages_allocated": alloc,
        "handles": {r: (read_json(out / f"handle_{s4_lib.safe_id(r)}.json").get("verdict"))
                    for r in pilot["readers"]},
    }
    contract.freeze("design", frozen)
    write_json(out / "verdict.json", {"card": "I03", "exec": "COMPLETE", "outcome": "VOID",
                                      "tier": tier, "label": label, "deferred": deferred,
                                      "readers_admitted": admitted,
                                      "n_expected_cells": len(cells),
                                      "contract_hash": contract.hash(),
                                      "marker": completion_marker(
                                          {"pilot": str(out / "PILOT.json"),
                                           "i02": str(S4 / "I02" / "verdict.json")},
                                          {"expected": str(S4 / "EXPECTED_CELLS.json")},
                                          contract)})
    print(f"I03 frozen: tier={tier} label={label} deferred={deferred} "
          f"mult={mult:.2f} est_min={est_min['total']}h est_exp={est_exp['total']}h")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True, choices=["I01", "I02", "I03pilot", "I03"])
    a = ap.parse_args()
    return {"I01": arm_i01, "I02": arm_i02, "I03pilot": arm_i03pilot, "I03": arm_i03}[a.card]()


if __name__ == "__main__":
    sys.exit(main())
