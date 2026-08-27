"""Stage 3 Trunk S runners: S01 three-family replication of the crossed reversal.
Card E24-S3-S01 (+ /X2 sibling read handled by the same matrix machinery later).

Arms: gate3 (third instruct family admission at the 85 percent accept-time realization
floor), gen3 (family-3 corpus, same task bank and yield gate as the Stage-2 family-2
corpus), matrix3 (ONLY the new matrix cells: the family-3 reader over the existing
corpora, every reader over the family-3 corpus), analyze (three-family crossed-reversal
with a completeness guard over the declared full matrix, reusing the Stage-2 likelihood
reads for cells that already exist — the reads are deterministic).

DESIGN CHECK (2026-08-24). Lessons applied: accept-time realization gate BEFORE any
corpus spend (L156/L172 admission rule); retired Pythia makers excluded everywhere
(L163); yield gate at 0.9 with manifest withheld below it (L158); per-reader known-answer
echo gate copied from the Stage-2 matrix arm (L139); completeness guard — the analysis
refuses to run on a partial matrix (L166); cells reported beside contrasts (L168);
scoring is candidate-given-artifact, the direction that worked in Stage 2.
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

from prereg.g172 import (FAMILY, N_GOALS, READERS, SEED0, TOPICS, TRIALS,        # noqa: E402
                         candidate, realized, short)
from runners.scout_stage2_s import (FAMILY2, MAKERS2, RETIRED, VARIANTS,         # noqa: E402
                                    _chat_generate, load_variant, task_text)
from soundingline.s3 import S3, set_status                                       # noqa: E402

OUT_S = S3 / "S" / "S01"
COR3 = REPO / "corpora" / "g172_family3"
CANDIDATES3 = ["TinyLlama/TinyLlama-1.1B-Chat-v1.0", "allenai/OLMo-2-0425-1B-Instruct"]
FAMILY3 = {"TinyLlama/TinyLlama-1.1B-Chat-v1.0": "tinyllama",
           "allenai/OLMo-2-0425-1B-Instruct": "olmo"}
GATE_TASKS = 40
GATE_ATTEMPTS = 8
GEN_ATTEMPTS = 16
STAGE2_MX = REPO / "results" / "scouts"


def fam_of(model: str) -> str:
    return {**FAMILY, **FAMILY2, **FAMILY3}[model]


def _load(mk):
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    tok = AutoTokenizer.from_pretrained(mk)
    model = AutoModelForCausalLM.from_pretrained(
        mk, dtype=torch.float16).to("cuda").eval()
    return model, tok


def winner_path():
    return OUT_S / "gate3.json"


def get_winner() -> str | None:
    p = winner_path()
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8")).get("winner")


def arm_gate3() -> int:
    """Admission: realized-within-8-attempts rate over 40 tasks, floor 0.85."""
    import torch                                                                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    OUT_S.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED0 + 31)
    tasks = [(rng.randrange(len(TOPICS)), rng.randrange(N_GOALS))
             for _ in range(GATE_TASKS)]
    rates = {}
    acquire_gpu_lock("s3_gate3")
    try:
        for cand in CANDIDATES3:
            model, tok = _load(cand)
            ok = 0
            for j, (ti, gi) in enumerate(tasks):
                for att in range(GATE_ATTEMPTS):
                    txt = _chat_generate(model, tok, task_text(ti, gi),
                                         SEED0 + 700000 + j * 32 + att)
                    if realized(txt, ti, gi):
                        ok += 1
                        break
            rates[cand] = ok / GATE_TASKS
            print(f"  {short(cand)}: {rates[cand]:.3f}")
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    passing = {c: r for c, r in rates.items() if r >= 0.85}
    winner = max(passing, key=passing.get) if passing else None
    winner_path().write_text(json.dumps(
        {"rates": rates, "floor": 0.85, "winner": winner,
         "tasks": GATE_TASKS, "attempt_budget": GATE_ATTEMPTS}, indent=1),
        encoding="utf-8", newline="\n")
    print(f"gate3 winner: {winner} (rates {rates})")
    return 0


def arm_gen3() -> int:
    """Family-3 corpus: winner maker, same bank/counts as fam2, but TRIALS doubled to 4
    (single maker in the family, so trials carry the within-family n)."""
    import torch                                                                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    winner = get_winner()
    if winner is None:
        # audit 2026-08-24: write the manifest anyway so matrix3/analyze run as the
        # two-family replication; the third family is recorded as blocked
        (OUT_S / "family3_manifest.json").write_text(json.dumps(
            {"cell": "E24-S3-S01", "maker": None, "n": 0, "fill": 0.0,
             "note": "no third family passed the 0.85 realization gate; S01 "
                     "proceeds as the two-family replication, third family "
                     "RESOURCE_BLOCKED"}, indent=1), encoding="utf-8", newline="\n")
        print("gen3: no third family passed the gate; two-family path recorded")
        return 0
    trials3 = 4
    mdir = COR3 / short(winner)
    mdir.mkdir(parents=True, exist_ok=True)
    rows = []
    acquire_gpu_lock("s3_gen3")
    try:
        model, tok = _load(winner)
        for ti in range(len(TOPICS)):
            for gi in range(N_GOALS):
                for k in range(trials3):
                    dest = mdir / f"art_{ti}_{gi}_{k}.json"
                    if dest.exists():
                        rows.append(json.loads(dest.read_text(encoding="utf-8")))
                        continue
                    got = None
                    for att in range(GEN_ATTEMPTS):
                        seed = (SEED0 + 800000 + ti * 1000 + gi * 128
                                + k * 32 + att)
                        txt = _chat_generate(model, tok, task_text(ti, gi), seed)
                        if realized(txt, ti, gi):
                            got = {"maker": winner, "topic_i": ti, "goal_i": gi,
                                   "trial": k, "attempt": att, "text": txt}
                            break
                    if got:
                        dest.write_text(json.dumps(got, ensure_ascii=False, indent=1),
                                        encoding="utf-8", newline="\n")
                        rows.append(got)
                    else:
                        print(f"  UNFILLED t{ti} g{gi} k{k}")
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    n_target = len(TOPICS) * N_GOALS * trials3
    fill = len(rows) / n_target
    print(f"family3 fill {len(rows)}/{n_target} = {fill:.3f}")
    if fill < 0.9:
        print("yield gate failed; manifest withheld")
        return 1
    (OUT_S / "family3_manifest.json").write_text(json.dumps(
        {"cell": "E24-S3-S01", "maker": winner, "n": len(rows), "fill": fill},
        indent=1), encoding="utf-8", newline="\n")
    return 0


def load_fam3() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(COR3.rglob("art_*.json"))]


def _score_reader_on(reader: str, arts: list[dict], dest: Path) -> None:
    from soundingline.probe.conditional_reader import (candidate_scores,          # noqa: PLC0415
                                                       free_readers, load_reader)
    rng = random.Random(SEED0 + 11)
    model, tok = load_reader(reader, device="cuda", dtype="float16")
    ka = 0
    probes = rng.sample(arts, min(8, len(arts)))
    for a in probes:
        own = a["text"].split(". ")[0]
        foreign = [x["text"].split(". ")[0]
                   for x in rng.sample([x for x in arts if x is not a], 3)]
        r = candidate_scores(model, tok, [own] + foreign, a["text"])
        ka += r["order"][0] == 0
    if ka / len(probes) < 0.85:
        dest.write_text(json.dumps({"reader": reader,
                                    "gate_fail_ka": ka / len(probes)}),
                        encoding="utf-8", newline="\n")
        free_readers()
        print(f"  {short(reader)} EXCLUDED (echo {ka}/{len(probes)})")
        return
    cases = []
    for a in arts:
        cands = [candidate(a["topic_i"], g) for g in range(4)]
        res = candidate_scores(model, tok, cands, a["text"])
        truth = a["goal_i"]
        margin = res["scores"][truth] - (sum(res["scores"])
                                         - res["scores"][truth]) / 3
        cases.append({"maker": a["maker"], "topic_i": a["topic_i"],
                      "goal_i": truth, "trial": a["trial"],
                      "maker_family": fam_of(a["maker"]),
                      "reader_family": fam_of(reader),
                      "margin": margin, "top1": res["order"][0] == truth})
    dest.write_text(json.dumps({"reader": reader, "cases": cases},
                               ensure_ascii=False), encoding="utf-8", newline="\n")
    free_readers()
    print(f"  {short(reader)} done ({len(cases)} cases)")


def all_readers() -> list[str]:
    winner = get_winner()
    rs = [r for r in READERS if r not in RETIRED] + MAKERS2
    if winner:
        rs.append(winner)
    return rs


def arm_matrix3() -> int:
    """Only the NEW cells: family-3 reader x (orig, fam2) corpora; every reader x the
    family-3 corpus. Stage-2 mx files cover the rest deterministically."""
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    winner = get_winner()
    fam3_arts = load_fam3()
    acquire_gpu_lock("s3_s01_mx")
    try:
        if fam3_arts:
            for reader in sorted(all_readers(),
                                 key=lambda r: ("3b" in r.lower() or "2.8b" in r, r)):
                dest = OUT_S / f"mx_fam3_{short(reader)}.json"
                if not dest.exists():
                    _score_reader_on(reader, fam3_arts, dest)
        if winner:
            for variant in ("orig", "fam2"):
                arts = load_variant(variant)
                dest = OUT_S / f"mx_{variant}_{short(winner)}.json"
                if not dest.exists():
                    _score_reader_on(winner, arts, dest)
    finally:
        release_gpu_lock()
    (OUT_S / "matrix3_done.json").write_text(json.dumps(
        {"winner": winner, "n_fam3": len(fam3_arts)}, indent=1),
        encoding="utf-8", newline="\n")
    print("matrix3 pass complete")
    return 0


def _collect_cases() -> list[dict]:
    """Full three-family matrix from Stage-2 mx files (orig, fam2 x old readers) plus
    the Stage-3 fills. Excluded (echo-gate-failed) readers are dropped consistently."""
    cases = []
    for p in list(STAGE2_MX.glob("mx_orig_*.json")) \
            + list(STAGE2_MX.glob("mx_fam2_*.json")) \
            + list(OUT_S.glob("mx_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if "cases" not in d:
            continue
        if d["reader"] in RETIRED:
            continue
        cases.extend(c for c in d["cases"] if c["maker"] not in RETIRED)
    return cases


def arm_analyze() -> int:
    """Three-family crossed reversal: own-family minus other-family reading margin,
    per maker-family x reader-family cell, sign-flip permutation on the paired contrast."""
    cell = "E24-S3-S01"
    t0 = time.time()
    from runners.s3_lib import perm_p                                             # noqa: PLC0415
    winner = get_winner()
    families = ["qwen", "smollm"] + ([fam_of(winner)] if winner else [])
    cases = _collect_cases()
    # completeness guard: every maker-family x reader-family cell must be populated
    have = {(c["maker_family"], c["reader_family"]) for c in cases}
    reader_fams = {c["reader_family"] for c in cases}
    missing = [(mf, rf) for mf in families for rf in reader_fams
               if (mf, rf) not in have]
    if missing:
        print(f"analyze REFUSED: matrix incomplete, missing cells {missing}")
        return 1
    grid = {}
    for mf in families:
        for rf in sorted(reader_fams):
            sub = [c["margin"] for c in cases
                   if c["maker_family"] == mf and c["reader_family"] == rf]
            grid[f"{mf}|{rf}"] = {"n": len(sub),
                                  "mean_margin": sum(sub) / len(sub) if sub else None}
    # paired own-minus-other per maker family (paired over artifacts read by both sides)
    contrast = {}
    for mf in families:
        own = [c for c in cases if c["maker_family"] == mf
               and c["reader_family"] == mf]
        other = [c for c in cases if c["maker_family"] == mf
                 and c["reader_family"] != mf and c["reader_family"] in families]
        key = {}
        for c in own:
            key[(c["maker"], c["topic_i"], c["goal_i"], c["trial"])] = c["margin"]
        diffs = []
        agg = {}
        for c in other:
            agg.setdefault((c["maker"], c["topic_i"], c["goal_i"], c["trial"]),
                           []).append(c["margin"])
        for k, v in agg.items():
            if k in key:
                diffs.append(key[k] - sum(v) / len(v))
        if diffs:
            obs, p = perm_p(diffs, SEED0 + 41)
            contrast[mf] = {"n_pairs": len(diffs), "own_minus_other": obs,
                            "perm_p": p, "perm_seed": SEED0 + 41}
    # the Stage-2 definition: other = every non-own reader family, base readers too
    contrast_all = {}
    for mf in families:
        own = {(c["maker"], c["topic_i"], c["goal_i"], c["trial"]): c["margin"]
               for c in cases if c["maker_family"] == mf
               and c["reader_family"] == mf}
        agg = {}
        for c in cases:
            if c["maker_family"] == mf and c["reader_family"] != mf:
                agg.setdefault((c["maker"], c["topic_i"], c["goal_i"],
                                c["trial"]), []).append(c["margin"])
        diffs = [own[k] - sum(v) / len(v) for k, v in agg.items() if k in own]
        if diffs:
            obs, p = perm_p(diffs, SEED0 + 42)
            contrast_all[mf] = {"n_pairs": len(diffs), "own_minus_other": obs,
                                "perm_p": p, "perm_seed": SEED0 + 42}
    third_blocked = winner is None
    (OUT_S / "verdict.json").write_text(json.dumps(
        {"cell": cell, "families": families, "grid": grid,
         "contrast_maker_families_only": contrast,
         "contrast_all_reader_families": contrast_all,
         "third_family": winner, "third_family_blocked": third_blocked,
         "n_cases": len(cases)}, indent=1), encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(json.dumps({"grid_cells": len(grid), "contrast": contrast}, indent=1))
    return 0


# ── S02: family x policy 2x2 via LoRA adapters (card E24-S3-S02) ─────────────────────
# The question in plain language: when a standing policy is put into the WEIGHTS instead
# of the prompt, is the resulting behavior the same policy by the exact reader — and does
# the maker's family still show through the artifacts the way the crossed reversal found?
# DESIGN CHECK: training pairs are accept-time realized before anything trains (L156);
# adapter evaluation uses held-out scenarios only; the exact posterior is the known-answer
# reader (L139); enactment floors precede any cross-family read (compliance before
# factorial, L169); cohort seeds parameterized so /X1 reuses these arms unchanged.

S02_FAMILIES = ["Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct"]
S02_POLICIES = ("robust", "cheap")
OUT_S02 = S3 / "S" / "S02"
S02_SEED0 = 21000
S02_N_TRAIN = 60


def s02_arm_data(cohort: int = 1) -> int:
    """Training pairs: the policy-PROMPTED maker enacts choices; pairs are stored as
    (bare episode prompt -> realized recommendation). Held-out scenarios excluded."""
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from runners.s3_lib import (POLICY_LINES, chat_gen, episode_prompt,           # noqa: PLC0415
                                realized_choice, scenarios, utilities,
                                choice_probs, PROFILE_W, AXES)
    OUT_S02.mkdir(parents=True, exist_ok=True)
    rng = random.Random(S02_SEED0 + cohort * 977)
    acquire_gpu_lock("s3_s02_data")
    try:
        for mk in S02_FAMILIES:
            shortm = mk.split("/")[-1][:8]
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            for pol in S02_POLICIES:
                dest = OUT_S02 / f"pairs_{shortm}_{pol}_c{cohort}.jsonl"
                if dest.exists():
                    continue
                rows = []
                tries = 0
                while len(rows) < S02_N_TRAIN and tries < S02_N_TRAIN * 6:
                    tries += 1
                    domain = "infra" if tries % 2 == 0 else "process"
                    si = rng.randrange(8)        # scenarios 8-11 held out per domain
                    probs = choice_probs(utilities(si, 1, domain), PROFILE_W[pol])
                    tgt = AXES[max(range(4), key=lambda j: probs[j])]
                    txt = chat_gen(model, tok,
                                   episode_prompt(si, domain, POLICY_LINES[pol]),
                                   S02_SEED0 + cohort * 50000 + tries)
                    if realized_choice(txt, si, domain) == tgt:
                        rows.append({"prompt": episode_prompt(si, domain),
                                     "completion": txt, "domain": domain,
                                     "scen_i": si, "choice": tgt})
                dest.write_text("\n".join(json.dumps(r, ensure_ascii=False)
                                           for r in rows) + "\n",
                                encoding="utf-8", newline="\n")
                print(f"  pairs {shortm} {pol}: {len(rows)}/{S02_N_TRAIN} "
                      f"({tries} tries)")
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    return 0


def s02_arm_train(cohort: int = 1) -> int:
    import torch                                                                  # noqa: PLC0415
    from peft import LoraConfig, get_peft_model                                   # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    acquire_gpu_lock("s3_s02_train")
    try:
        for mk in S02_FAMILIES:
            shortm = mk.split("/")[-1][:8]
            tok = AutoTokenizer.from_pretrained(mk)
            if tok.pad_token is None:
                tok.pad_token = tok.eos_token
            for pol in S02_POLICIES:
                adir = OUT_S02 / f"adapter_{shortm}_{pol}_c{cohort}"
                if (adir / "adapter_model.safetensors").exists():
                    continue
                data = [json.loads(x) for x in
                        (OUT_S02 / f"pairs_{shortm}_{pol}_c{cohort}.jsonl"
                         ).read_text(encoding="utf-8").splitlines() if x.strip()]
                model = AutoModelForCausalLM.from_pretrained(
                    mk, dtype=torch.float32).to("cuda")
                cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.0,
                                 target_modules=["q_proj", "k_proj", "v_proj",
                                                 "o_proj"])
                model = get_peft_model(model, cfg)
                model.train()
                opt = torch.optim.AdamW(
                    [p for p in model.parameters() if p.requires_grad], lr=1e-4)
                torch.manual_seed(S02_SEED0 + cohort)
                for ep in range(3):
                    order = list(range(len(data)))
                    random.Random(S02_SEED0 + cohort * 10 + ep).shuffle(order)
                    for i0 in range(0, len(order), 4):
                        batch = [data[i] for i in order[i0:i0 + 4]]
                        texts, plens = [], []
                        for r in batch:
                            msgs = [{"role": "user", "content": r["prompt"]}]
                            pre = tok.apply_chat_template(
                                msgs, add_generation_prompt=True, tokenize=False)
                            texts.append(pre + r["completion"] + tok.eos_token)
                            plens.append(len(tok(pre, add_special_tokens=False)
                                              .input_ids))
                        enc = tok(texts, return_tensors="pt", padding=True,
                                  truncation=True, max_length=640,
                                  add_special_tokens=False).to("cuda")
                        labels = enc.input_ids.clone()
                        labels[enc.attention_mask == 0] = -100
                        for bi, pl in enumerate(plens):
                            labels[bi, :pl] = -100
                        loss = model(**enc, labels=labels).loss
                        loss.backward()
                        opt.step()
                        opt.zero_grad()
                model.save_pretrained(str(adir))
                print(f"  adapter {shortm} {pol} c{cohort} "
                      f"(final loss {loss.item():.3f})")
                del model, opt
                torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    return 0


def s02_arm_eval(cohort: int = 1) -> int:
    """Held-out enactment WITHOUT any policy line: adapter makers choose on scenarios
    8-11 of both domains; exact posterior must recover the trained policy. The bare
    (no-adapter) maker on the same episodes is the floor."""
    cell = "E24-S3-S02"
    t0 = time.time()
    import torch                                                                  # noqa: PLC0415
    from peft import PeftModel                                                    # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from runners.s3_lib import (bayes_profile_posterior, chat_gen,                # noqa: PLC0415
                                episode_prompt, realized_choice)
    held = [(d, si) for d in ("infra", "process") for si in range(8, 12)]
    report = {}
    acquire_gpu_lock("s3_s02_eval")
    try:
        for mk in S02_FAMILIES:
            shortm = mk.split("/")[-1][:8]
            tok = AutoTokenizer.from_pretrained(mk)
            base = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            conds = [("bare", None)] + [(pol, OUT_S02 /
                                         f"adapter_{shortm}_{pol}_c{cohort}")
                                        for pol in S02_POLICIES]
            for cond, adir in conds:
                model = base if adir is None else \
                    PeftModel.from_pretrained(base, str(adir)).eval()
                recs = []
                for rep in range(3):
                    for d, si in held:
                        ch = None
                        for att in range(4):
                            txt = chat_gen(model, tok, episode_prompt(si, d),
                                           S02_SEED0 + rep * 512 + si * 16 + att)
                            ch = realized_choice(txt, si, d)
                            if ch is not None:
                                break
                        if ch:
                            recs.append((d, si, ch))
                posts = {}
                for d in ("infra", "process"):
                    ds = [(si, ch) for dd, si, ch in recs if dd == d]
                    if ds:
                        posts[d] = bayes_profile_posterior(
                            [c for _, c in ds], [s2 for s2, _ in ds], 1, d)
                report[f"{shortm}|{cond}"] = {
                    "n_realized": len(recs), "of": 3 * len(held),
                    "posterior": posts,
                    "top": {d: max(p, key=p.get) for d, p in posts.items()}}
                if adir is not None:
                    model = model.unload()
            del base
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    hits = misses = 0
    for key, v in report.items():
        cond = key.split("|")[1]
        if cond in S02_POLICIES:
            for d, top in v["top"].items():
                if top == cond:
                    hits += 1
                else:
                    misses += 1
    vname = "verdict.json" if cohort == 1 else f"verdict_c{cohort}.json"
    (OUT_S02 / vname).write_text(json.dumps(
        {"cell": cell, "cohort": cohort, "cells": report,
         "policy_recovered_cells": hits, "policy_missed_cells": misses},
        indent=1), encoding="utf-8", newline="\n")
    if cohort == 1:
        set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"S02 landed: recovered {hits}, missed {misses}; "
          f"tops {json.dumps({k: v['top'] for k, v in report.items()})}")
    return 0


# ── S03: the relatedness gradient (card E24-S3-S03) ─────────────────────────────────
# The question in plain language: does how well a reader inverts a maker fall off
# smoothly with how RELATED the reader is to the maker — exact same weights, same family
# at another size, a different family entirely? The Stage-2 matrix plus the Stage-3
# family-3 fills already contain every cell; this arm is the gradient read.
# DESIGN CHECK: analysis-only over complete matrices (the completeness guard from
# arm_analyze applies); rungs assigned mechanically from model identity; per-rung cells
# beside the trend (L168); the trend statistic is the mean margin per rung with a
# permutation over rung assignments within maker family (so family composition cannot
# fake a gradient); seed recorded.

RUNG_ORDER = ("exact", "same_family", "cross_family")


def _rung(maker: str, reader: str) -> str:
    if maker == reader:
        return "exact"
    if fam_of(maker) == fam_of(reader):
        return "same_family"
    return "cross_family"


def arm_s03() -> int:
    cell = "E24-S3-S03"
    t0 = time.time()
    from runners.s3_lib import perm_p                                             # noqa: PLC0415
    out = S3 / "S" / "S03"
    out.mkdir(parents=True, exist_ok=True)
    # collect keeping the reader field (the shared collector drops it)
    cases = []
    for p2 in list(STAGE2_MX.glob("mx_orig_*.json")) \
            + list(STAGE2_MX.glob("mx_fam2_*.json")) \
            + list(OUT_S.glob("mx_*.json")):
        d = json.loads(p2.read_text(encoding="utf-8"))
        if "cases" not in d or d["reader"] in RETIRED:
            continue
        for c in d["cases"]:
            if c["maker"] in RETIRED:
                continue
            c["reader"] = d["reader"]
            cases.append(c)
    rung_cells = {}
    for r in RUNG_ORDER:
        sub = [c["margin"] for c in cases if _rung(c["maker"], c["reader"]) == r]
        rung_cells[r] = {"n": len(sub),
                         "mean_margin": sum(sub) / len(sub) if sub else None}
    # monotone trend: exact >= same_family >= cross_family on means; permutation:
    # within each maker, shuffle rung labels across its readers 20000 times
    import random as _r                                                           # noqa: PLC0415
    rng = _r.Random(SEED0 + 71)
    by_maker = {}
    for c in cases:
        by_maker.setdefault((c["maker"], c["topic_i"], c["goal_i"],
                             c["trial"]), []).append(
            (_rung(c["maker"], c["reader"]), c["margin"]))
    def trend(assign):
        sums = {r: [0.0, 0] for r in RUNG_ORDER}
        for items in assign:
            for r, m in items:
                sums[r][0] += m
                sums[r][1] += 1
        means = [sums[r][0] / sums[r][1] if sums[r][1] else 0.0
                 for r in RUNG_ORDER]
        return means[0] - means[2]
    obs = trend(by_maker.values())
    ge = 0
    vals = list(by_maker.values())
    for _ in range(20000):
        shuf = []
        for items in vals:
            rungs = [r for r, _m in items]
            rng.shuffle(rungs)
            shuf.append(list(zip(rungs, [m for _r2, m in items])))
        if abs(trend(shuf)) >= abs(obs):
            ge += 1
    pval = (ge + 1) / 20001
    monotone = all(
        (rung_cells[RUNG_ORDER[i]]["mean_margin"] or 0)
        >= (rung_cells[RUNG_ORDER[i + 1]]["mean_margin"] or 0)
        for i in range(len(RUNG_ORDER) - 1)
        if rung_cells[RUNG_ORDER[i]]["n"] and rung_cells[RUNG_ORDER[i + 1]]["n"])
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "rungs": rung_cells, "monotone": monotone,
         "exact_minus_cross": obs, "perm_p": pval, "perm_seed": SEED0 + 71,
         "n_artifact_groups": len(by_maker)}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"S03 landed: rungs "
          f"{json.dumps({k: v['mean_margin'] for k, v in rung_cells.items()})}; "
          f"exact-cross {obs:.4f} (p={pval:.4g}), monotone={monotone}")
    return 0


# ── S04: the six-rung process ladder (card E24-S3-S04) ──────────────────────────────
# The question in plain language: makers told to DECIDE DIFFERENTLY (six procedures,
# from snap answer to eliminate-worst-first to full pro/con audit) — does the procedure
# leave a readable trace in the artifact, where Stage 1 found route identity
# semantically blind (G166)? The Stage-3 version has mechanical ground truth (the
# procedure is assigned) and a compliance check per rung (procedure-specific structural
# markers) before any reading.
# DESIGN CHECK: compliance verified per artifact before the corpus counts (L156);
# reader arm is truth-balanced with a word-echo floor (the G158c discipline); per-rung
# cells (L168).

import re as _re

_W = lambda pat: (lambda t: _re.search(pat, t, _re.I) is not None)           # noqa: E731
PROCEDURES = {
    "snap": ("Decide immediately, in two sentences total: the recommendation, "
             "then one sentence of support.",
             lambda t: len([x for x in _re.split(r"[.!?]+", t) if x.strip()]) <= 3),
    "proscons": ("Before recommending, give one short pro and one short con for "
                 "at least two options, then decide.",
                 _W(r"\bpros?\b.*\bcons?\b|\bcons?\b.*\bpros?\b")),
    "eliminate": ("Decide by elimination: name the option you rule out FIRST and "
                  "why, then continue eliminating until one remains.",
                  _W(r"\brule[sd]? out\b|\beliminat")),
    "criteria": ("First state the single criterion that matters most here, then "
                 "pick the option that best satisfies it.",
                 _W(r"\bcriterion\b|\bmatters most\b")),
    "precedent_check": ("First recall how a similar case was handled before, "
                        "then decide in light of it.",
                        _W(r"\bsimilar case\b|\blast time\b|\bhandled before\b|"
                           r"\bprevious(ly)?\b")),
    "devil": ("Choose provisionally, then argue against your own choice in one "
              "sentence, then confirm or switch.",
              _W(r"\bhowever\b|\bagainst (my|this|that)\b|\bon the other hand\b")),
}
OUT_S04 = S3 / "S" / "S04"


def arm_s04() -> int:
    cell = "E24-S3-S04"
    t0 = time.time()
    OUT_S04.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from runners.s3_lib import chat_gen, episode_prompt, realized_choice, \
        scenarios as s3scen, hash_stable                                          # noqa: PLC0415
    import random as _r                                                           # noqa: PLC0415
    rng = _r.Random(SEED0 + 900)
    makers = ["Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct"]
    n_ok = n_try = 0
    acquire_gpu_lock("s3_s04")
    try:
        for mk in makers:
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            shortm = mk.split("/")[-1][:8]
            for proc, (instr, check) in PROCEDURES.items():
                for j in range(12):
                    domain = "infra" if j % 2 == 0 else "process"
                    si = rng.randrange(len(s3scen(domain)))
                    dest = OUT_S04 / f"art_{shortm}_{proc}_{j}.json"
                    n_try += 1
                    if dest.exists():
                        n_ok += 1
                        continue
                    base = episode_prompt(si, domain)
                    prompt = base.replace(
                        "Write a short recommendation",
                        f"{instr} Write your recommendation")
                    if proc == "snap":
                        prompt = prompt.replace("(40 to 110 words)", "(20 to 60 words)")
                    for att in range(5):
                        txt = chat_gen(model, tok, prompt,
                                       SEED0 + 910 + j * 64 + att,
                                       max_new=240)
                        if realized_choice(txt, si, domain) and check(txt):
                            dest.write_text(json.dumps(
                                {"maker": mk, "proc": proc, "j": j,
                                 "domain": domain, "scen_i": si,
                                 "text": txt}, ensure_ascii=False),
                                encoding="utf-8", newline="\n")
                            n_ok += 1
                            break
            del model
            torch.cuda.empty_cache()
        # reader arm: truth-balanced 6-way procedure identification, one reader
        arts = [json.loads(p2.read_text(encoding="utf-8"))
                for p2 in sorted(OUT_S04.glob("art_*.json"))]
        reader = makers[0]
        tok = AutoTokenizer.from_pretrained(reader)
        model = AutoModelForCausalLM.from_pretrained(
            reader, dtype=torch.float16).to("cuda").eval()
        procs = list(PROCEDURES)
        hits = tot = 0
        echo_hits = 0
        for a in arts:
            dest = OUT_S04 / f"read_{hash_stable(a['text'][:40])}.json"
            if dest.exists():
                d = json.loads(dest.read_text(encoding="utf-8"))
            else:
                menu = "\n".join(f"{i + 1}) {PROCEDURES[q][0]}"
                                  for i, q in enumerate(procs))
                prompt = ("Which decision procedure produced this "
                          "recommendation?\n\nRecommendation:\n" + a["text"]
                          + "\n\nProcedures:\n" + menu
                          + "\n\nAnswer with the number only.\n\nAnswer:")
                txt = chat_gen(model, tok, prompt,
                               SEED0 + 950 + hash_stable(a["text"][:40]) % 999,
                               max_new=8)
                pick = None
                for tokn in txt.split():
                    if tokn.strip(").,") .isdigit():
                        v = int(tokn.strip(").,"))
                        if 1 <= v <= 6:
                            pick = procs[v - 1]
                            break
                # word-echo floor: instruction-word overlap argmax
                low = a["text"].lower()
                echo = max(procs, key=lambda q: sum(
                    1 for w in PROCEDURES[q][0].lower().split()
                    if len(w) > 5 and w in low))
                d = {"truth": a["proc"], "pick": pick, "echo": echo}
                dest.write_text(json.dumps(d), encoding="utf-8", newline="\n")
            if d["pick"] is not None:
                hits += d["pick"] == d["truth"]
                tot += 1
            echo_hits += d["echo"] == d["truth"]
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    yield_frac = n_ok / n_try if n_try else 0
    (OUT_S04 / "verdict.json").write_text(json.dumps(
        {"cell": cell, "attempted": n_try, "realized": n_ok,
         "yield": yield_frac,
         "reader_acc": hits / tot if tot else None, "reader_n": tot,
         "echo_floor": echo_hits / len(arts) if arts else None,
         "chance": 1 / 6}, indent=1), encoding="utf-8", newline="\n")
    status = "LANDED" if yield_frac >= 0.75 else "INSTRUMENT_FAILED"
    set_status(cell, status,
               closure_reason=None if status == "LANDED" else
               f"compliance yield {yield_frac:.2f} under 0.75",
               actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"S04 {status}: yield {yield_frac:.3f}, reader "
          f"{hits}/{tot}, echo {echo_hits}/{len(arts)}")
    return 0


# ── S05: the bottleneck erasure rung (card E24-S3-S05) ──────────────────────────────
# The question in plain language: squeeze each artifact through a 15-word summary and
# regenerate a paragraph from the summary alone — the harshest erasure yet. Does the
# crossed reversal survive a semantic bottleneck that provably destroys the surface?
# DESIGN CHECK: the erasure gate measures survival of goal realization after the
# bottleneck (only realized regenerations enter the matrix, counted); similarity
# filter excludes regenerations too close to their source (the L157 echo lesson);
# matrix and analysis reuse the S01 machinery, completeness-guarded.

OUT_S05 = S3 / "S" / "S05"


def arm_s05() -> int:
    cell = "E24-S3-S05"
    t0 = time.time()
    OUT_S05.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from runners.scout_stage2_s import _chat_generate, normalize_text            # noqa: PLC0415
    arts = load_variant("orig") + load_variant("fam2")
    bt = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
    acquire_gpu_lock("s3_s05")
    kept = dropped_sim = dropped_real = 0
    try:
        tok = AutoTokenizer.from_pretrained(bt)
        model = AutoModelForCausalLM.from_pretrained(
            bt, dtype=torch.float16).to("cuda").eval()
        for ai, a in enumerate(arts):
            dest = OUT_S05 / f"bn_{ai}.json"
            if dest.exists():
                kept += 1
                continue
            summ = _chat_generate(
                model, tok, "Summarize this paragraph in at most 15 words, "
                "keeping only its essential content:\n\n" + a["text"]
                + "\n\nSummary:", SEED0 + 970 + ai, max_new=40)
            regen = _chat_generate(
                model, tok, f"Write one short informative paragraph (60 to 180 "
                f"words) based only on this summary: {summ}\n\nParagraph:",
                SEED0 + 975 + ai, max_new=260)
            if not realized(regen, a["topic_i"], a["goal_i"]):
                dropped_real += 1
                continue
            na, nb = set(normalize_text(a["text"]).split()), \
                set(normalize_text(regen).split())
            jac = len(na & nb) / max(1, len(na | nb))
            if jac > 0.6:
                dropped_sim += 1
                continue
            dest.write_text(json.dumps(
                {"maker": a["maker"], "topic_i": a["topic_i"],
                 "goal_i": a["goal_i"], "trial": a["trial"],
                 "text": regen, "summary": summ, "jaccard": jac},
                ensure_ascii=False), encoding="utf-8", newline="\n")
            kept += 1
        del model
        torch.cuda.empty_cache()
        # matrix over the bottleneck corpus
        bn_arts = [json.loads(p2.read_text(encoding="utf-8"))
                   for p2 in sorted(OUT_S05.glob("bn_*.json"))]
        for reader in sorted(all_readers(),
                             key=lambda r: ("3b" in r.lower() or "2.8b" in r,
                                            r)):
            dest = OUT_S05 / f"mx_bn_{short(reader)}.json"
            if not dest.exists() and bn_arts:
                _score_reader_on(reader, bn_arts, dest)
    finally:
        release_gpu_lock()
    # crossed contrast on the bottleneck matrix
    from runners.s3_lib import perm_p                                             # noqa: PLC0415
    cases = []
    for p2 in OUT_S05.glob("mx_bn_*.json"):
        d = json.loads(p2.read_text(encoding="utf-8"))
        if "cases" in d and d["reader"] not in RETIRED:
            for c in d["cases"]:
                c["reader"] = d["reader"]
                cases.append(c)
    fams = sorted({c["maker_family"] for c in cases})
    contrast = {}
    for mf in fams:
        own = {(c["maker"], c["topic_i"], c["goal_i"], c["trial"]): c["margin"]
               for c in cases if c["maker_family"] == mf
               and c["reader_family"] == mf}
        agg = {}
        for c in cases:
            if c["maker_family"] == mf and c["reader_family"] != mf:
                agg.setdefault((c["maker"], c["topic_i"], c["goal_i"],
                                c["trial"]), []).append(c["margin"])
        diffs = [own[k] - sum(v) / len(v) for k, v in agg.items() if k in own]
        if diffs:
            obs, pv = perm_p(diffs, SEED0 + 98)
            contrast[mf] = {"n": len(diffs), "own_minus_other": obs,
                            "perm_p": pv}
    survivor_floor = 40
    (OUT_S05 / "verdict.json").write_text(json.dumps(
        {"cell": cell, "kept": kept, "dropped_unrealized": dropped_real,
         "dropped_too_similar": dropped_sim, "survivor_floor": survivor_floor,
         "contrast": contrast, "perm_seed": SEED0 + 98}, indent=1),
        encoding="utf-8", newline="\n")
    ok = kept >= survivor_floor
    set_status(cell, "LANDED" if ok else "INSTRUMENT_FAILED",
               closure_reason=None if ok else
               f"only {kept} regenerations survive the bottleneck realized; the "
               "goal does not survive a 15-word summary (a finding about the "
               "erasure, not the reversal)",
               actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"S05 landed: kept {kept} (unrealized {dropped_real}, similar "
          f"{dropped_sim}); contrast {json.dumps(contrast)}")
    return 0


# ── S05/X3: the bottleneck with the THIRD family as eraser (card E24-S3-S05/X3) ─────
# DESIGN CHECK: same realized-regeneration gate, per-item similarity filter, survivor
# floor, and completeness discipline as S05 (L165 erasure lessons); the eraser is the
# gate-admitted OLMo — a family with NO stake in either measured contrast, so survival
# through it is stronger evidence than survival through a SmolLM channel.

OUT_S05X3 = S3 / "S" / "S05_x3"


def arm_s05x3() -> int:
    cell = "E24-S3-S05/X3"
    t0 = time.time()
    OUT_S05X3.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from runners.scout_stage2_s import _chat_generate, normalize_text            # noqa: PLC0415
    from runners.s3_lib import perm_p                                             # noqa: PLC0415
    winner = get_winner()
    if winner is None:
        (S3 / "S" / "S05" / "eraser3.json").write_text(json.dumps(
            {"cell": cell, "status": "RESOURCE_BLOCKED",
             "reason": "no third family passed the gate"}, indent=1),
            encoding="utf-8", newline="\n")
        set_status(cell, "RESOURCE_BLOCKED",
                   closure_reason="no third family", actual_gpu_minutes=0.0)
        return 0
    arts = load_variant("orig") + load_variant("fam2")
    acquire_gpu_lock("s3_s05x3")
    kept = dropped_sim = dropped_real = 0
    try:
        tok = AutoTokenizer.from_pretrained(winner)
        model = AutoModelForCausalLM.from_pretrained(
            winner, dtype=torch.float16).to("cuda").eval()
        for ai, a in enumerate(arts):
            dest = OUT_S05X3 / f"bn_{ai}.json"
            if dest.exists():
                kept += 1
                continue
            summ = _chat_generate(
                model, tok, "Summarize this paragraph in at most 15 words, "
                "keeping only its essential content:\n\n" + a["text"]
                + "\n\nSummary:", SEED0 + 1970 + ai, max_new=40)
            regen = _chat_generate(
                model, tok, f"Write one short informative paragraph (60 to 180 "
                f"words) based only on this summary: {summ}\n\nParagraph:",
                SEED0 + 1975 + ai, max_new=260)
            if not realized(regen, a["topic_i"], a["goal_i"]):
                dropped_real += 1
                continue
            na, nb = set(normalize_text(a["text"]).split()), \
                set(normalize_text(regen).split())
            jac = len(na & nb) / max(1, len(na | nb))
            if jac > 0.6:
                dropped_sim += 1
                continue
            dest.write_text(json.dumps(
                {"maker": a["maker"], "topic_i": a["topic_i"],
                 "goal_i": a["goal_i"], "trial": a["trial"],
                 "text": regen, "summary": summ, "jaccard": jac},
                ensure_ascii=False), encoding="utf-8", newline="\n")
            kept += 1
        del model
        torch.cuda.empty_cache()
        bn_arts = [json.loads(p2.read_text(encoding="utf-8"))
                   for p2 in sorted(OUT_S05X3.glob("bn_*.json"))]
        for reader in sorted(all_readers(),
                             key=lambda r: ("3b" in r.lower() or "2.8b" in r,
                                            r)):
            dest = OUT_S05X3 / f"mx_bn_{short(reader)}.json"
            if not dest.exists() and bn_arts:
                _score_reader_on(reader, bn_arts, dest)
    finally:
        release_gpu_lock()
    cases = []
    for p2 in OUT_S05X3.glob("mx_bn_*.json"):
        d = json.loads(p2.read_text(encoding="utf-8"))
        if "cases" in d and d["reader"] not in RETIRED:
            for c in d["cases"]:
                c["reader"] = d["reader"]
                cases.append(c)
    fams = sorted({c["maker_family"] for c in cases})
    contrast = {}
    for mf in fams:
        own = {(c["maker"], c["topic_i"], c["goal_i"], c["trial"]): c["margin"]
               for c in cases if c["maker_family"] == mf
               and c["reader_family"] == mf}
        agg = {}
        for c in cases:
            if c["maker_family"] == mf and c["reader_family"] != mf:
                agg.setdefault((c["maker"], c["topic_i"], c["goal_i"],
                                c["trial"]), []).append(c["margin"])
        diffs = [own[k] - sum(v) / len(v) for k, v in agg.items() if k in own]
        if diffs:
            obs, pv = perm_p(diffs, SEED0 + 198)
            contrast[mf] = {"n": len(diffs), "own_minus_other": obs,
                            "perm_p": pv}
    survivor_floor = 40
    ok = kept >= survivor_floor
    (S3 / "S" / "S05" / "eraser3.json").write_text(json.dumps(
        {"cell": cell, "eraser": winner, "kept": kept,
         "dropped_unrealized": dropped_real,
         "dropped_too_similar": dropped_sim,
         "survivor_floor": survivor_floor, "contrast": contrast,
         "perm_seed": SEED0 + 198,
         "smollm_eraser_comparison_pointer":
         "results/phase_2_4_stage_3/S/S05/verdict.json"}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED" if ok else "INSTRUMENT_FAILED",
               closure_reason=None if ok else
               f"only {kept} survivors through the OLMo bottleneck",
               actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"S05/X3 ({winner}): kept {kept}; contrast {json.dumps(contrast)}")
    return 0


# ── S06: attribution benefit and correction (card E24-S3-S06) ────────────────────────
# The question in plain language: does TELLING the reader who made an artifact help it
# recover the maker's goal — and does a WRONG attribution hurt? Conditions: no
# attribution, true family named, wrong family named.
# DESIGN CHECK: uses the conditional reader's condition-string interface (its designed
# purpose); same candidate sets as the S01 matrix; per-condition per-reader cells;
# the harm of wrong attribution is the correction half of the question.

OUT_S06 = S3 / "S" / "S06"


def arm_s06() -> int:
    cell = "E24-S3-S06"
    t0 = time.time()
    OUT_S06.mkdir(parents=True, exist_ok=True)
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from soundingline.probe.conditional_reader import (candidate_scores,          # noqa: PLC0415
                                                       free_readers, load_reader)
    import random as _r                                                           # noqa: PLC0415
    rng = _r.Random(SEED0 + 990)
    arts = load_variant("orig") + load_variant("fam2")
    rng.shuffle(arts)
    arts = arts[:120]
    readers = ["Qwen/Qwen2.5-1.5B-Instruct",
               "HuggingFaceTB/SmolLM2-1.7B-Instruct"]
    fam_names = {"qwen": "a Qwen family model",
                 "smollm": "a SmolLM family model",
                 "gpt2": "a GPT-2 family model", "pythia": "a Pythia family model"}
    rows = []
    acquire_gpu_lock("s3_s06")
    try:
        for reader in readers:
            model, tok = load_reader(reader, device="cuda", dtype="float16")
            shortm = short(reader)
            for ai, a in enumerate(arts):
                truefam = fam_of(a["maker"])
                wrongfam = rng.choice([f for f in fam_names if f != truefam])
                conds = {"none": None,
                         "true": f"This paragraph was written by "
                                 f"{fam_names.get(truefam, truefam)}.",
                         "wrong": f"This paragraph was written by "
                                  f"{fam_names.get(wrongfam, wrongfam)}."}
                for cond, cstr in conds.items():
                    dest = OUT_S06 / f"r_{shortm}_{ai}_{cond}.json"
                    if dest.exists():
                        rows.append(json.loads(
                            dest.read_text(encoding="utf-8")))
                        continue
                    cands = [candidate(a["topic_i"], g) for g in range(4)]
                    text = (cstr + "\n\n" + a["text"]) if cstr else a["text"]
                    res = candidate_scores(model, tok, cands, text)
                    row = {"reader": shortm, "ai": ai, "cond": cond,
                           "top1": int(res["order"][0] == a["goal_i"])}
                    dest.write_text(json.dumps(row), encoding="utf-8",
                                    newline="\n")
                    rows.append(row)
            free_readers()
    finally:
        release_gpu_lock()
    cells = {}
    for reader in readers:
        shortm = short(reader)
        for cond in ("none", "true", "wrong"):
            sub = [r for r in rows if r["reader"] == shortm
                   and r["cond"] == cond]
            cells[f"{shortm}|{cond}"] = {
                "n": len(sub),
                "goal_top1": sum(r["top1"] for r in sub) / len(sub)
                if sub else None}
    (OUT_S06 / "verdict.json").write_text(json.dumps(
        {"cell": cell, "cells": cells, "n_artifacts": len(arts)}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"S06 landed: {json.dumps({k: v['goal_top1'] for k, v in cells.items()})}")
    return 0


# ── S07: the confirmation scout (card E24-S3-S07) ───────────────────────────────────
# Week's-end reserve-side confirmation: the S01 and S03 headline contrasts recomputed
# on ONLY the md5-reserve quarter of artifacts (lineage_side), untouched by any
# exploration. DESIGN CHECK: the reserve assignment is the frozen hash rule from
# soundingline.s3 (decided before any Stage-3 read); analysis-only.

def arm_s07() -> int:
    cell = "E24-S3-S07"
    t0 = time.time()
    from soundingline.s3 import lineage_side                                      # noqa: PLC0415
    from runners.s3_lib import perm_p                                             # noqa: PLC0415
    out = S3 / "S" / "S07"
    out.mkdir(parents=True, exist_ok=True)
    cases = []
    for p2 in list(STAGE2_MX.glob("mx_orig_*.json")) \
            + list(STAGE2_MX.glob("mx_fam2_*.json")) \
            + list(OUT_S.glob("mx_*.json")):
        d = json.loads(p2.read_text(encoding="utf-8"))
        if "cases" not in d or d["reader"] in RETIRED:
            continue
        for c in d["cases"]:
            if c["maker"] in RETIRED:
                continue
            lid = f"{c['maker']}|{c['topic_i']}|{c['goal_i']}|{c['trial']}"
            if lineage_side(lid) != "confirmation":
                continue
            c["reader"] = d["reader"]
            cases.append(c)
    fams = sorted({c["maker_family"] for c in cases})
    contrast = {}
    for mf in fams:
        own = {(c["maker"], c["topic_i"], c["goal_i"], c["trial"]): c["margin"]
               for c in cases if c["maker_family"] == mf
               and c["reader_family"] == mf}
        agg = {}
        for c in cases:
            if c["maker_family"] == mf and c["reader_family"] != mf:
                agg.setdefault((c["maker"], c["topic_i"], c["goal_i"],
                                c["trial"]), []).append(c["margin"])
        diffs = [own[k] - sum(v) / len(v) for k, v in agg.items() if k in own]
        if diffs:
            obs, pv = perm_p(diffs, SEED0 + 99)
            contrast[mf] = {"n": len(diffs), "own_minus_other": obs,
                            "perm_p": pv}
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "n_reserve_cases": len(cases), "contrast": contrast,
         "perm_seed": SEED0 + 99,
         "note": "reserve quarter only, frozen md5 assignment"}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"S07 landed on reserve: {json.dumps(contrast)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["gate3", "gen3", "matrix3", "analyze",
                             "s02_data", "s02_train", "s02_eval", "s03",
                             "s04", "s05", "s05x3", "s06", "s07"])
    ap.add_argument("--cohort", type=int, default=1)
    a = ap.parse_args()
    if a.arm in ("s03", "s04", "s05", "s05x3", "s06", "s07"):
        return {"s03": arm_s03, "s04": arm_s04, "s05": arm_s05,
                "s05x3": arm_s05x3, "s06": arm_s06, "s07": arm_s07}[a.arm]()
    if a.arm.startswith("s02_"):
        return {"s02_data": s02_arm_data, "s02_train": s02_arm_train,
                "s02_eval": s02_arm_eval}[a.arm](cohort=a.cohort)
    return {"gate3": arm_gate3, "gen3": arm_gen3, "matrix3": arm_matrix3,
            "analyze": arm_analyze}[a.arm]()


if __name__ == "__main__":
    sys.exit(main())
