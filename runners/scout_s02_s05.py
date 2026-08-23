"""Discovery-lane scouts E24-S05 (capacity asymmetry, analysis-only) and E24-S02
(fingerprint destruction). DISCOVERY DATA; outputs use scout status words only
(PROMISING / QUIET / RIVAL-FAVORED / INSTRUMENT-FAILED), never trunk verdicts, and stay
sealed from the curator-facing report until the walkthrough (addendum §12).

E24-S05: from the landed matrix records alone — does reader parameter count predict margin
better than family relation? No new compute.

E24-S02: paraphrase every corpus artifact with the local model under aggressive restyling,
re-verify the mechanical goals survive (the entity-order construction is paraphrase-stable
by design), then re-run the seven gate-passing readers. If the similarity gradient
collapses, the trunk's graded pattern was dialect (RIVAL-FAVORED); if it survives, the
organization reading strengthens (PROMISING). RECORDED CONFOUND: the only local
paraphraser is itself Qwen-family, which biases toward preserving Qwen dialect — i.e.,
AGAINST erasure — so a collapse is strong evidence and a survival is weak evidence, and
the scout's own record says so.

DESIGN CHECK (2026-08-22, discovery lane). Lessons: §3 (known answers — the paraphrase arm
keeps the mechanical realized() check as its per-item acceptance), §5 (produces guards;
ollama retries with backoff; manifests withheld under 90 percent yield). Failure
directions: paraphrase yield DOWN freezes the scout (INSTRUMENT-FAILED), never a thin
manifest; gradient movement is reported with both contrasts and their permutation p, no
band promotion — routing words only.
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

from prereg.g172 import SEED0, candidate, goal_entities, realized, short         # noqa: E402

OUT = REPO / "results" / "scouts"
PARA = REPO / "corpora" / "g172_paraphrase"
MANIFEST = REPO / "results" / "g172" / "corpus_manifest.json"
PARA_MANIFEST = OUT / "s02_paraphrase_manifest.json"

PARAM_B = {"qwen25_05b": 0.5, "qwen25_15b": 1.5, "qwen25_15b_instruct": 1.5,
           "qwen25_3b": 3.0, "pythia_410m": 0.41, "pythia_14b": 1.4,
           "pythia_28b": 2.8, "gpt2_large": 0.77, "smollm2_17b": 1.7}


def arm_s05() -> int:
    rows = []
    for p in (REPO / "results" / "g172").glob("read_*.json"):
        r = json.loads(p.read_text(encoding="utf-8"))
        if not r["gates"]["pass"]:
            continue
        name = short(r["reader"])
        fam = "qwen" if name.startswith("qwen") else "cross"
        m = sum(c["margin"] for c in r["cases"]) / len(r["cases"])
        rows.append({"reader": name, "family_side": fam, "params_b": PARAM_B[name],
                     "mean_margin": m})
    rows.sort(key=lambda x: -x["mean_margin"])
    # rank correlation of margin with params, and the family split
    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        rk = [0.0] * len(vals)
        for pos, i in enumerate(order):
            rk[i] = pos
        return rk
    ms = [r["mean_margin"] for r in rows]
    ps = [r["params_b"] for r in rows]
    rm, rp = rank(ms), rank(ps)
    n = len(rows)
    mr, mp = sum(rm) / n, sum(rp) / n
    num = sum((a - mr) * (b - mp) for a, b in zip(rm, rp))
    den = (sum((a - mr) ** 2 for a in rm) * sum((b - mp) ** 2 for b in rp)) ** 0.5
    rho = num / den if den else 0.0
    qwen_min = min(r["mean_margin"] for r in rows if r["family_side"] == "qwen")
    cross_max = max(r["mean_margin"] for r in rows if r["family_side"] == "cross")
    separated = qwen_min > cross_max
    status = "PROMISING" if (separated and abs(rho) < 0.6) else \
        ("RIVAL-FAVORED" if rho >= 0.6 and not separated else "QUIET")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "s05_capacity.json").write_text(json.dumps({
        "scout": "E24-S05", "status": status, "spearman_margin_vs_params": rho,
        "family_separation_complete": separated, "readers": rows,
        "reading": "separation with weak capacity correlation favors relation over "
                   "capacity; a strong capacity correlation without separation favors "
                   "the capacity account"}, indent=1), encoding="utf-8", newline="\n")
    print(f"S05: {status}, rho {rho:.3f}, complete family separation {separated}")
    return 0


_PARA_PROMPT = (
    "Rewrite the following paragraph in a completely different style: different sentence "
    "structures, different rhythm, plainer and drier register, no phrase reused. Keep every "
    "factual point and keep the same overall order of ideas. Output only the rewritten "
    "paragraph.\n\nParagraph:\n{text}\n\nRewritten paragraph:")


def arm_paraphrase() -> int:
    from soundingline.probe.client import LocalClient                            # noqa: PLC0415
    client = LocalClient()
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    PARA.mkdir(parents=True, exist_ok=True)
    ok = 0
    cells = man["cells"]
    for c in cells:
        src = (REPO / "corpora" / "g172" / short(c["maker"])
               / f"art_{c['topic_i']}_{c['goal_i']}_{c['trial']}.json")
        dest = PARA / f"{short(c['maker'])}_art_{c['topic_i']}_{c['goal_i']}_{c['trial']}.json"
        if dest.exists():
            ok += 1
            continue
        art = json.loads(src.read_text(encoding="utf-8"))
        got = None
        for attempt in range(6):
            try:
                txt = client.read_text(
                    "You rewrite text precisely as instructed.",
                    _PARA_PROMPT.format(text=art["text"])).strip()
            except Exception as e:                                               # noqa: BLE001
                print(f"  paraphrase error attempt {attempt}: {e}")
                time.sleep(5 * (attempt + 1))
                continue
            txt = re.sub(r"^(rewritten paragraph:?\s*)", "", txt, flags=re.I).strip()
            txt = txt.split("\n\n")[0].strip()
            if realized(txt, c["topic_i"], c["goal_i"]):
                got = txt
                break
        if got:
            dest.write_text(json.dumps({**art, "text": got, "paraphrased": True},
                                       ensure_ascii=False, indent=1),
                            encoding="utf-8", newline="\n")
            ok += 1
        else:
            print(f"  PARAPHRASE UNFILLED {short(c['maker'])} "
                  f"t{c['topic_i']} g{c['goal_i']} k{c['trial']}")
    yield_frac = ok / len(cells)
    print(f"paraphrase yield {ok}/{len(cells)} = {yield_frac:.3f}")
    if yield_frac < 0.9:
        print("scout INSTRUMENT-FAILED on yield; manifest withheld")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    PARA_MANIFEST.write_text(json.dumps({
        "scout": "E24-S02", "n": ok, "yield": yield_frac,
        "paraphraser": "qwen3.5:9b (Qwen-family; confound recorded: biases against "
                       "erasure, so collapse is strong evidence, survival weak)"},
        indent=1), encoding="utf-8", newline="\n")
    return 0


def arm_matrix() -> int:
    from runners.run_g172_matrix import contrasts                                # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    from soundingline.probe.conditional_reader import (candidate_scores,         # noqa: PLC0415
                                                       free_readers, load_reader)
    from prereg.g172 import READERS, relation                                    # noqa: PLC0415

    arts = []
    for p in sorted(PARA.glob("*.json")):
        arts.append(json.loads(p.read_text(encoding="utf-8")))
    passing = [json.loads((REPO / "results" / "g172" / f"read_{short(r)}.json")
                          .read_text(encoding="utf-8"))
               for r in READERS]
    keep = [r["reader"] for r in passing if r["gates"]["pass"]]
    print(f"{len(arts)} paraphrased artifacts, {len(keep)} gate-passing readers")
    records = []
    acquire_gpu_lock("scout_s02_matrix")
    try:
        for reader in sorted(keep, key=lambda r: ("3b" in r.lower() or "2.8b" in r, r)):
            dest = OUT / f"s02_read_{short(reader)}.json"
            if dest.exists():
                records.append(json.loads(dest.read_text(encoding="utf-8")))
                continue
            print(f"== reader {short(reader)} ==")
            model, tok = load_reader(reader, device="cuda", dtype="float16")
            cases = []
            for a in arts:
                cands = [candidate(a["topic_i"], g) for g in range(4)]
                res = candidate_scores(model, tok, cands, a["text"])
                truth = a["goal_i"]
                margin = res["scores"][truth] - (sum(res["scores"])
                                                - res["scores"][truth]) / 3
                cases.append({"maker": a["maker"], "topic_i": a["topic_i"],
                              "goal_i": truth, "trial": a["trial"],
                              "relation": relation(a["maker"], reader),
                              "margin": margin, "top1": res["order"][0] == truth})
            rec = {"reader": reader, "gates": {"pass": True}, "cases": cases}
            dest.write_text(json.dumps(rec, ensure_ascii=False),
                            encoding="utf-8", newline="\n")
            free_readers()
            records.append(rec)
    finally:
        release_gpu_lock()
    result = contrasts(records)
    orig = json.loads((REPO / "results" / "g172" / "verdict.json")
                      .read_text(encoding="utf-8"))["contrasts"]
    survived = result["c1_mean"] > 0 and result["c1_p"] < 0.05 \
        and result["c2_mean"] > 0 and result["c2_p"] < 0.05
    status = "PROMISING" if survived else "RIVAL-FAVORED"
    (OUT / "s02_erasure.json").write_text(json.dumps({
        "scout": "E24-S02", "status": status,
        "paraphrased_contrasts": result, "original_contrasts": orig,
        "confound": "Qwen-family paraphraser biases against erasure; survival is weak "
                    "evidence, collapse strong",
        "reading": "survival keeps shared-organization live alongside its confound; "
                   "collapse means the trunk's graded pattern was dialect"},
        indent=1), encoding="utf-8", newline="\n")
    print(f"S02: {status}; paraphrased c1 {result['c1_mean']:.4f} (p {result['c1_p']:.5f}), "
          f"c2 {result['c2_mean']:.4f} (p {result['c2_p']:.5f})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["s05", "paraphrase", "matrix"])
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    return {"s05": arm_s05, "paraphrase": arm_paraphrase, "matrix": arm_matrix}[a.arm]()


if __name__ == "__main__":
    sys.exit(main())
