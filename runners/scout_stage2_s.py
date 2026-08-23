"""Stage-2 Tree-S Wave 1 (discovery lane): second maker family, independent erasure, and
the source detector. Scout codes E24-S1a/S1c/S1d, E24-S2, E24-S3; statuses are scout words
only, sealed to the registry until the daily cold map.

DESIGN CHECK (2026-08-23, discovery lane). Lessons read: §3 (accept-time realization L156;
known-answer before signal; small-probe bands derived at probe count — the gate here uses a
binomial-derived band, the L163 lesson; floors follow marginals), §4 (instruct models for
multi-constraint generation — the L163 base-model lesson is why the second family enters
through instruct checkpoints), §5 (produces guards; gpulock once; manifests withheld under
90 percent; kill checklist). Failure directions: generation yield DOWN freezes a manifest;
detector accuracy at chance means erasure verification is UNINFORMATIVE (recorded, never
spun as fingerprints-absent); every erasure arm re-verifies realized() per item.

Arms:
  gen2       SmolLM2-instruct makers write the same goal corpus (chat template, no few-shot)
  normalize  mechanical normalization of all corpora (punctuation, casing, whitespace)
  para2      SmolLM2-1.7B-Instruct paraphrases all corpora (the non-Qwen eraser)
  matrix     score one corpus variant with all readers; relations extended to two families
  detector   maker-family classifier (char n-grams + function words), topic-held-out;
             applied to every variant to VERIFY erasure
  analyze    crossed-reversal and erasure summary across everything landed
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from prereg.g172 import (SEED0, TOPICS, N_GOALS, TRIALS, WORD_BAND,              # noqa: E402
                         candidate, gen_prompt, goal_entities, realized, short)

OUT = REPO / "results" / "scouts"
COR = REPO / "corpora"

MAKERS2 = ["HuggingFaceTB/SmolLM2-1.7B-Instruct", "HuggingFaceTB/SmolLM2-360M-Instruct"]
PARAPHRASER2 = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
FAMILY2 = {"HuggingFaceTB/SmolLM2-1.7B-Instruct": "smollm",
           "HuggingFaceTB/SmolLM2-360M-Instruct": "smollm"}
READERS2 = MAKERS2          # added to the original nine readers in the matrix arm
ATTEMPTS2 = 16
VARIANTS = {"orig": "g172", "fam2": "g172_family2", "norm": "g172_norm",
            "para_qwen": "g172_paraphrase", "para2": "g172_para2"}


def family_of(model: str) -> str:
    from prereg.g172 import FAMILY                                               # noqa: PLC0415
    return {**FAMILY, **FAMILY2}[model]


def load_variant(name: str) -> list[dict]:
    d = COR / VARIANTS[name]
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(d.rglob("*.json")) if p.name.startswith(("art_",)) or "_art_" in p.name]


def task_text(ti: int, gi: int) -> str:
    topic = TOPICS[ti][0]
    a, b, avoid = goal_entities(ti, gi)
    return (f"Write one short informative paragraph about {topic}. The paragraph must "
            f"mention {a} first and {b} later, and must not mention {avoid[0]} or "
            f"{avoid[1]}. Output only the paragraph, 60 to 180 words.")


def _chat_generate(model, tok, prompt: str, seed: int, max_new: int = 260) -> str:
    import torch                                                                 # noqa: PLC0415
    msgs = [{"role": "user", "content": prompt}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
    if not torch.is_tensor(ids):          # transformers 5 returns a BatchEncoding
        ids = ids["input_ids"]
    ids = ids.to("cuda")
    torch.manual_seed(seed)
    with torch.no_grad():
        out = model.generate(ids, do_sample=True, temperature=0.8, top_p=0.95,
                             max_new_tokens=max_new, pad_token_id=tok.eos_token_id)
    txt = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True).strip()
    return txt.split("\n\n")[0].strip()


def arm_gen2() -> int:
    import torch                                                                 # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                 # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    dest_root = COR / VARIANTS["fam2"]
    acquire_gpu_lock("scout_gen2")
    rows = []
    try:
        for mi, maker in enumerate(MAKERS2):
            tok = AutoTokenizer.from_pretrained(maker)
            model = AutoModelForCausalLM.from_pretrained(
                maker, dtype=torch.float16).to("cuda").eval()
            mdir = dest_root / short(maker)
            mdir.mkdir(parents=True, exist_ok=True)
            for ti in range(len(TOPICS)):
                for gi in range(N_GOALS):
                    for k in range(TRIALS):
                        dest = mdir / f"art_{ti}_{gi}_{k}.json"
                        if dest.exists():
                            rows.append(json.loads(dest.read_text(encoding="utf-8")))
                            continue
                        got = None
                        for att in range(ATTEMPTS2):
                            seed = (SEED0 + 900000 + mi * 100000 + ti * 1000
                                    + gi * 128 + k * 32 + att)
                            txt = _chat_generate(model, tok, task_text(ti, gi), seed)
                            if realized(txt, ti, gi):
                                got = {"maker": maker, "topic_i": ti, "goal_i": gi,
                                       "trial": k, "attempt": att, "text": txt}
                                break
                        if got:
                            dest.write_text(json.dumps(got, ensure_ascii=False, indent=1),
                                            encoding="utf-8", newline="\n")
                            rows.append(got)
                        else:
                            print(f"  UNFILLED {short(maker)} t{ti} g{gi} k{k}")
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    n_target = len(MAKERS2) * len(TOPICS) * N_GOALS * TRIALS
    fill = len(rows) / n_target
    print(f"family2 fill {len(rows)}/{n_target} = {fill:.3f}")
    if fill < 0.9:
        print("yield gate failed; manifest withheld")
        return 1
    (OUT / "family2_manifest.json").write_text(json.dumps(
        {"scout": "E24-S3", "n": len(rows), "fill": fill,
         "cells": [{k: r[k] for k in ("maker", "topic_i", "goal_i", "trial")}
                   for r in rows]}, indent=1), encoding="utf-8", newline="\n")
    return 0


_WS = re.compile(r"\s+")


def normalize_text(t: str) -> str:
    t = t.replace("“", '"').replace("”", '"').replace("’", "'") \
         .replace("‘", "'").replace("—", ", ").replace("–", "-") \
         .replace("…", "...")
    t = re.sub(r"[ \t]*\n[ \t]*", " ", t)
    t = re.sub(r"\s*([,;:.!?])\s*", r"\1 ", t)
    t = _WS.sub(" ", t).strip()
    sents = re.split(r"(?<=[.!?]) ", t)
    sents = [s[:1].upper() + s[1:] if s else s for s in sents]
    return " ".join(sents)


def arm_normalize() -> int:
    n_ok = n_all = 0
    for src_name in ("orig", "fam2"):
        src = COR / VARIANTS[src_name]
        if not src.exists():
            continue
        for p in sorted(src.rglob("art_*.json")):
            art = json.loads(p.read_text(encoding="utf-8"))
            dest = COR / VARIANTS["norm"] / short(art["maker"]) / p.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            n_all += 1
            txt = normalize_text(art["text"])
            if realized(txt, art["topic_i"], art["goal_i"]):
                dest.write_text(json.dumps({**art, "text": txt, "normalized": True},
                                           ensure_ascii=False, indent=1),
                                encoding="utf-8", newline="\n")
                n_ok += 1
    print(f"normalized {n_ok}/{n_all}")
    if n_all == 0 or n_ok / n_all < 0.95:
        return 1
    (OUT / "norm_manifest.json").write_text(json.dumps(
        {"scout": "E24-S1a", "n": n_ok, "of": n_all}, indent=1),
        encoding="utf-8", newline="\n")
    return 0


def arm_para2() -> int:
    import torch                                                                 # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                 # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    tok = AutoTokenizer.from_pretrained(PARAPHRASER2)
    acquire_gpu_lock("scout_para2")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            PARAPHRASER2, dtype=torch.float16).to("cuda").eval()
        n_ok = n_all = 0
        for src_name in ("orig", "fam2"):
            src = COR / VARIANTS[src_name]
            if not src.exists():
                continue
            for p in sorted(src.rglob("art_*.json")):
                art = json.loads(p.read_text(encoding="utf-8"))
                dest = COR / VARIANTS["para2"] / short(art["maker"]) / p.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                n_all += 1
                if dest.exists():
                    n_ok += 1
                    continue
                prompt = ("Rewrite the following paragraph in a completely different "
                          "style: different sentence structures, plainer and drier "
                          "register, no phrase reused. Keep every factual point and the "
                          "same order of ideas. Output only the rewritten paragraph.\n\n"
                          + art["text"])
                got = None
                import hashlib                                                   # noqa: PLC0415
                stable = int(hashlib.md5(p.name.encode()).hexdigest()[:6], 16) % 10000
                for att in range(6):
                    seed = SEED0 + 950000 + stable * 8 + att
                    txt = _chat_generate(model, tok, prompt, seed)
                    if realized(txt, art["topic_i"], art["goal_i"]):
                        got = txt
                        break
                if got:
                    dest.write_text(json.dumps({**art, "text": got, "para2": True},
                                               ensure_ascii=False, indent=1),
                                    encoding="utf-8", newline="\n")
                    n_ok += 1
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    print(f"para2 {n_ok}/{n_all}")
    if n_all == 0 or n_ok / n_all < 0.9:
        return 1
    (OUT / "para2_manifest.json").write_text(json.dumps(
        {"scout": "E24-S1c", "n": n_ok, "of": n_all,
         "paraphraser": PARAPHRASER2}, indent=1), encoding="utf-8", newline="\n")
    return 0


def arm_matrix(variant: str) -> int:
    from prereg.g172 import READERS                                              # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    from soundingline.probe.conditional_reader import (candidate_scores,         # noqa: PLC0415
                                                       free_readers, load_reader)
    arts = load_variant(variant)
    readers = READERS + READERS2
    print(f"{variant}: {len(arts)} artifacts, {len(readers)} readers")
    acquire_gpu_lock(f"scout_mx_{variant}")
    try:
        for reader in sorted(readers, key=lambda r: ("3b" in r.lower() or "2.8b" in r, r)):
            dest = OUT / f"mx_{variant}_{short(reader)}.json"
            if dest.exists():
                continue
            model, tok = load_reader(reader, device="cuda", dtype="float16")
            # known-answer echo gate per reader per variant (L139/L163 discipline):
            # the artifact's own first sentence must beat three foreign ones
            import random                                                        # noqa: PLC0415
            rng = random.Random(SEED0 + 11)
            ka = 0
            probes = rng.sample(arts, min(8, len(arts)))
            for a in probes:
                own = a["text"].split(". ")[0]
                foreign = [x["text"].split(". ")[0]
                           for x in rng.sample([x for x in arts if x is not a], 3)]
                r = candidate_scores(model, tok, [own] + foreign, a["text"])
                ka += r["order"][0] == 0
            if ka / len(probes) < 0.85:
                dest.write_text(json.dumps({"reader": reader, "gate_fail_ka": ka / len(probes)}),
                                encoding="utf-8", newline="\n")
                free_readers()
                print(f"  {short(reader)} EXCLUDED (echo {ka}/{len(probes)})")
                continue
            cases = []
            for a in arts:
                cands = [candidate(a["topic_i"], g) for g in range(4)]
                res = candidate_scores(model, tok, cands, a["text"])
                truth = a["goal_i"]
                margin = res["scores"][truth] - (sum(res["scores"])
                                                - res["scores"][truth]) / 3
                cases.append({"maker": a["maker"], "topic_i": a["topic_i"],
                              "goal_i": truth, "trial": a["trial"],
                              "maker_family": family_of(a["maker"]),
                              "reader_family": family_of(reader),
                              "margin": margin, "top1": res["order"][0] == truth})
            dest.write_text(json.dumps({"reader": reader, "cases": cases},
                                       ensure_ascii=False), encoding="utf-8", newline="\n")
            free_readers()
            print(f"  {short(reader)} done")
    finally:
        release_gpu_lock()
    (OUT / f"mx_{variant}_done.json").write_text(json.dumps(
        {"variant": variant, "n": len(arts), "readers": len(readers)}, indent=1),
        encoding="utf-8", newline="\n")
    return 0


def arm_detector() -> int:
    from sklearn.feature_extraction.text import TfidfVectorizer                  # noqa: PLC0415
    from sklearn.linear_model import LogisticRegression                          # noqa: PLC0415
    import numpy as np                                                           # noqa: PLC0415
    res = {}
    for variant in VARIANTS:
        arts = load_variant(variant) if (COR / VARIANTS[variant]).exists() else []
        fams = sorted({family_of(a["maker"]) for a in arts})
        if len(fams) < 2 or len(arts) < 60:
            res[variant] = {"skipped": True, "n": len(arts), "families": fams}
            continue
        accs = []
        for held in range(len(TOPICS)):        # topic-held-out family classification
            tr = [a for a in arts if a["topic_i"] != held]
            te = [a for a in arts if a["topic_i"] == held]
            if not te:
                continue
            vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), max_features=20000)
            X = vec.fit_transform([a["text"] for a in tr])
            lr = LogisticRegression(max_iter=2000, random_state=SEED0)
            lr.fit(X, [family_of(a["maker"]) for a in tr])
            accs.append(float(lr.score(vec.transform([a["text"] for a in te]),
                                       [family_of(a["maker"]) for a in te])))
        res[variant] = {"family_acc_mean": float(np.mean(accs)), "per_topic": accs,
                        "chance": 1 / len(fams), "n": len(arts)}
        print(f"{variant}: family detection {np.mean(accs):.3f} vs chance {1/len(fams):.3f}")
    (OUT / "s2_detector.json").write_text(json.dumps(
        {"scout": "E24-S2", "results": res}, indent=1), encoding="utf-8", newline="\n")
    return 0


def arm_analyze() -> int:
    import random                                                                # noqa: PLC0415
    summary = {}
    for variant in VARIANTS:
        chunks = sorted(OUT.glob(f"mx_{variant}_*.json"))
        chunks = [c for c in chunks if not c.name.endswith("_done.json")]
        if not chunks:
            continue
        by_cell: dict[tuple, dict] = {}
        for ch in chunks:
            rec = json.loads(ch.read_text(encoding="utf-8"))
            if "cases" not in rec:
                continue
            for c in rec["cases"]:
                key = (c["maker_family"], c["reader_family"])
                by_cell.setdefault(key, []).append(c["margin"])
        table = {f"{mk}->{rd}": {"mean_margin": sum(v) / len(v), "n": len(v)}
                 for (mk, rd), v in sorted(by_cell.items())}
        # crossed contrast per maker family: own-family readers minus other-family readers
        crossed = {}
        for mk in {k[0] for k in by_cell}:
            own = [m for (m, r), v in by_cell.items() if m == mk and r == mk for m in v]
            oth = [m for (m, r), v in by_cell.items() if m == mk and r != mk for m in v]
            if own and oth:
                crossed[mk] = sum(own) / len(own) - sum(oth) / len(oth)
        summary[variant] = {"cells": table, "own_minus_other_by_maker_family": crossed}
    det = json.loads((OUT / "s2_detector.json").read_text(encoding="utf-8")) \
        if (OUT / "s2_detector.json").exists() else None
    reversal = None
    if "fam2" in summary or "orig" in summary:
        cr = {}
        for v in summary.values():
            for mk, d in v["own_minus_other_by_maker_family"].items():
                cr.setdefault(mk, []).append(d)
        reversal = {mk: all(x > 0 for x in xs) for mk, xs in cr.items()}
    status = "PROMISING" if reversal and all(reversal.values()) and len(reversal) >= 2 \
        else ("QUIET" if reversal else "INSTRUMENT-FAILED")
    (OUT / "s_wave1.json").write_text(json.dumps(
        {"scout": "E24-S1/S2/S3 wave-1 analysis", "status": status,
         "crossed_reversal_own_gt_other": reversal, "variants": summary,
         "detector": det}, indent=1), encoding="utf-8", newline="\n")
    print(f"wave-1 status {status}; reversal {reversal}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["gen2", "normalize", "para2", "matrix", "detector", "analyze"])
    ap.add_argument("--variant", default="orig")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rc = {"gen2": arm_gen2, "normalize": arm_normalize, "para2": arm_para2,
          "detector": arm_detector, "analyze": arm_analyze,
          "matrix": lambda: arm_matrix(a.variant)}[a.arm]()
    print(f"{a.arm} in {(time.time() - t0) / 60:.0f} min")
    return rc


if __name__ == "__main__":
    sys.exit(main())
