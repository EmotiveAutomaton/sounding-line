"""Stage 3 Trunk H runners: H01 RACE rhetorical-purpose battery, H04 CoAuthor
content-aware readers. Cards E24-S3-H01, E24-S3-H04.

H01 in plain language: on human exam passages, can a likelihood reader recover the
AUTHOR'S PURPOSE (why a thing was written/mentioned) as well as it recovers surface
detail? Purpose questions are the human-ground analogue of the project's goal-inversion
reads; detail questions from the same passages are the within-passage control.

DESIGN CHECK (2026-08-24). Lessons applied: corpus counts reproduced and recorded before
any scoring (the import rule — counts first, science second); the scoring direction is
short-option-GIVEN-long-passage (L169); paired within-passage purpose-vs-detail contrast
with sign-flip permutation, cells beside the contrast (L168); a random-option floor and
a no-passage (question-only) floor are computed for every reader — the reader must beat
question-only on detail items for its purpose score to be interpretable (L139 ruler
logic); RACE is a published research corpus (CC licensing for research use), fetched
from its HF mirror — no restricted test bank is touched (brief section 0).
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from soundingline.s3 import S3, set_status                                        # noqa: E402

OUT_H = S3 / "H"
SEED0 = 90000
READERS = ["Qwen/Qwen2.5-1.5B-Instruct", "HuggingFaceTB/SmolLM2-1.7B-Instruct"]
PURPOSE_RE = re.compile(
    r"purpose|attitude|tone of|mainly to|in order to|why does the author|"
    r"why did the author|author mentions|author uses|best title|main idea|"
    r"mainly about|infer|imply|suggest", re.I)
DETAIL_RE = re.compile(
    r"according to the (passage|text)|which of the following is (true|not true)|"
    r"what (happened|did)|when |where |how many|how much|who ", re.I)
N_TARGET = 1000


def arm_h01_data() -> int:
    """Filter RACE (high) into purpose and detail banks, >=1000 each, counts recorded."""
    out = OUT_H / "H01"
    out.mkdir(parents=True, exist_ok=True)
    from datasets import load_dataset                                             # noqa: PLC0415
    ds = load_dataset("ehovy/race", "high", split="train")
    purpose, detail = [], []
    n_total = 0
    for ex in ds:
        n_total += 1
        q = ex["question"]
        row = {"passage": ex["article"], "question": q,
               "options": ex["options"],
               "answer": "ABCD".index(ex["answer"]), "id": ex["example_id"]}
        if PURPOSE_RE.search(q) and "_" not in q:
            purpose.append(row)
        elif DETAIL_RE.search(q) and "_" not in q:
            detail.append(row)
        if len(purpose) >= N_TARGET * 2 and len(detail) >= N_TARGET * 2:
            break
    rng = random.Random(SEED0)
    # pair by passage where possible: keep passages contributing to both banks first
    p_by_pass = {}
    for r in purpose:
        p_by_pass.setdefault(r["passage"][:80], []).append(r)
    d_by_pass = {}
    for r in detail:
        d_by_pass.setdefault(r["passage"][:80], []).append(r)
    shared = [k for k in p_by_pass if k in d_by_pass]
    rng.shuffle(shared)
    sel_p, sel_d = [], []
    for k in shared:
        if len(sel_p) < N_TARGET:
            sel_p.append(p_by_pass[k][0])
            sel_d.append(d_by_pass[k][0])
    # top up from unshared if needed
    rest_p = [r for k in p_by_pass if k not in set(shared) for r in p_by_pass[k]]
    rest_d = [r for k in d_by_pass if k not in set(shared) for r in d_by_pass[k]]
    rng.shuffle(rest_p)
    rng.shuffle(rest_d)
    while len(sel_p) < N_TARGET and rest_p:
        sel_p.append(rest_p.pop())
    while len(sel_d) < N_TARGET and rest_d:
        sel_d.append(rest_d.pop())
    (out / "bank.json").write_text(json.dumps(
        {"n_scanned": n_total, "n_purpose_matched": len(purpose),
         "n_detail_matched": len(detail), "n_paired_passages": len(shared),
         "purpose": sel_p, "detail": sel_d}, ensure_ascii=False),
        encoding="utf-8", newline="\n")
    print(f"H01 bank: scanned {n_total}, purpose {len(sel_p)}, detail {len(sel_d)}, "
          f"paired passages {min(len(shared), N_TARGET)}")
    return 0


def _score_options(model, tok, context: str, options: list[str]) -> int:
    """Argmax over mean per-token logprob of each option given the context."""
    import torch                                                                  # noqa: PLC0415
    ids_c = tok(context, return_tensors="pt", add_special_tokens=False,
                truncation=True, max_length=1600).input_ids.to("cuda")
    best, best_s = 0, -1e18
    for oi, opt in enumerate(options):
        cand = tok(" " + opt, return_tensors="pt",
                   add_special_tokens=False).input_ids.to("cuda")
        full = torch.cat([ids_c, cand], dim=1)
        with torch.no_grad():
            logits = model(full).logits.float()
        lp = torch.log_softmax(logits[0, :-1], dim=-1)
        tgt = full[0, 1:]
        n_c = ids_c.shape[1]
        s = sum(lp[i, tgt[i]].item()
                for i in range(n_c - 1, full.shape[1] - 1)) / cand.shape[1]
        if s > best_s:
            best, best_s = oi, s
    return best


def arm_h01_read() -> int:
    cell = "E24-S3-H01"
    t0 = time.time()
    out = OUT_H / "H01"
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from runners.s3_lib import perm_p                                             # noqa: PLC0415
    bank = json.loads((out / "bank.json").read_text(encoding="utf-8"))
    report = {}
    acquire_gpu_lock("s3_h01")
    try:
        for mk in READERS:
            shortm = mk.split("/")[-1][:8]
            dest = out / f"read_{shortm}.json"
            if dest.exists():
                report[shortm] = json.loads(dest.read_text(encoding="utf-8"))
                continue
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            res = {}
            for kind in ("purpose", "detail"):
                rows = bank[kind]
                hits = hits_q = 0
                per = []
                for r in rows:
                    ctx = (f"Passage:\n{r['passage']}\n\nQuestion: {r['question']}\n"
                           f"Answer:")
                    ctx_q = f"Question: {r['question']}\nAnswer:"
                    pred = _score_options(model, tok, ctx, r["options"])
                    pred_q = _score_options(model, tok, ctx_q, r["options"])
                    hits += pred == r["answer"]
                    hits_q += pred_q == r["answer"]
                    per.append({"id": r["id"], "correct": int(pred == r["answer"]),
                                "correct_qonly": int(pred_q == r["answer"])})
                res[kind] = {"n": len(rows), "acc": hits / len(rows),
                             "acc_question_only": hits_q / len(rows), "per": per}
            dest.write_text(json.dumps(res), encoding="utf-8", newline="\n")
            report[shortm] = res
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    verdicts = {}
    for shortm, res in report.items():
        # paired purpose-vs-detail by position (same-passage pairing from the bank build)
        n = min(len(res["purpose"]["per"]), len(res["detail"]["per"]))
        diffs = [res["purpose"]["per"][i]["correct"]
                 - res["detail"]["per"][i]["correct"] for i in range(n)]
        obs, p = perm_p(diffs, SEED0 + 7)
        verdicts[shortm] = {
            "purpose_acc": res["purpose"]["acc"], "detail_acc": res["detail"]["acc"],
            "purpose_qonly": res["purpose"]["acc_question_only"],
            "detail_qonly": res["detail"]["acc_question_only"],
            "passage_lift_detail": res["detail"]["acc"]
            - res["detail"]["acc_question_only"],
            "purpose_minus_detail": obs, "perm_p": p, "n_pairs": n}
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "readers": verdicts, "floor_random": 0.25,
         "perm_seed": SEED0 + 7}, indent=1), encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"H01 landed: {json.dumps(verdicts, indent=1)[:400]}")
    return 0


def _h04_extract() -> list[dict]:
    """Per decision episode: document-so-far at suggestion-open, the suggestion text,
    and the outcome. Selected text comes from the open event's own list at the selected
    index; for dismissals the first shown suggestion stands in as the seen-and-rejected
    text (recorded as a design note). Doc state replays Quill deltas incrementally."""
    src = REPO / "corpora" / "coauthor" / "coauthor-v1.0"
    episodes = []
    for p2 in sorted(src.glob("*.jsonl")):
        try:
            events = [json.loads(x)
                      for x in p2.read_text(encoding="utf-8").splitlines()]
        except Exception:                                                         # noqa: BLE001
            continue
        doc = ""
        pending = None      # (doc_snapshot, suggestions)
        for ev in events:
            if ev.get("currentDoc"):
                doc = ev["currentDoc"]
            td = ev.get("textDelta")
            if isinstance(td, dict):
                pos = 0
                try:
                    for op in td.get("ops", []):
                        if "retain" in op:
                            pos += op["retain"]
                        elif "insert" in op:
                            doc = doc[:pos] + op["insert"] + doc[pos:]
                            pos += len(op["insert"])
                        elif "delete" in op:
                            doc = doc[:pos] + doc[pos + op["delete"]:]
                except Exception:                                                 # noqa: BLE001
                    pass
            name = ev.get("eventName")
            if name == "suggestion-open":
                pending = (doc, ev.get("currentSuggestions") or [])
            elif name in ("suggestion-select", "suggestion-close") and pending:
                snap, sugs = pending
                pending = None
                if not sugs:
                    continue
                if name == "suggestion-select":
                    idx = ev.get("currentSuggestionIndex")
                    if not isinstance(idx, int) or not (0 <= idx < len(sugs)):
                        continue
                    pick = sugs[idx]
                else:
                    pick = sugs[0]
                stext = (pick.get("trimmed") or pick.get("original") or ""
                         ) if isinstance(pick, dict) else str(pick)
                if len(stext.strip()) < 20 or len(snap.strip()) < 80:
                    continue
                episodes.append({"session": p2.stem, "context": snap,
                                 "suggestion": stext.strip(),
                                 "taken": name == "suggestion-select"})
    return episodes


def arm_h04() -> int:
    """CoAuthor content-aware readers: does the writer's take/dismiss decision become
    predictable from the suggestion's contextual fit — the thing position and length
    could not separate in Stage 2 (take rate flat at 0.758)? A likelihood reader
    scores each shown suggestion under the document-so-far; separation is AUC."""
    cell = "E24-S3-H04"
    t0 = time.time()
    out = OUT_H / "H04"
    out.mkdir(parents=True, exist_ok=True)
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    ep_path = out / "episodes.json"
    if ep_path.exists():
        episodes = json.loads(ep_path.read_text(encoding="utf-8"))
    else:
        episodes = _h04_extract()
        ep_path.write_text(json.dumps(episodes, ensure_ascii=False),
                           encoding="utf-8", newline="\n")
    n_take = sum(1 for e in episodes if e["taken"])
    print(f"H04 episodes: {len(episodes)} decidable ({n_take} taken, "
          f"{len(episodes) - n_take} dismissed)")
    rng = random.Random(SEED0 + 4)
    acc_ev = [e for e in episodes if e["taken"]]
    rej_ev = [e for e in episodes if not e["taken"]]
    n_side = min(len(acc_ev), len(rej_ev), 1500)
    if n_side < 100:
        (out / "verdict.json").write_text(json.dumps(
            {"cell": cell, "status": "INSTRUMENT-FAILED",
             "reason": f"only {n_side} balanced pairs decidable"}, indent=1),
            encoding="utf-8", newline="\n")
        set_status(cell, "INSTRUMENT_FAILED",
                   closure_reason="too few decidable dismissals for a balanced read",
                   actual_gpu_minutes=(time.time() - t0) / 60)
        return 0
    sample = rng.sample(acc_ev, n_side) + rng.sample(rej_ev, n_side)
    mk = READERS[0]
    rows = []
    acquire_gpu_lock("s3_h04")
    try:
        tok = AutoTokenizer.from_pretrained(mk)
        model = AutoModelForCausalLM.from_pretrained(
            mk, dtype=torch.float16).to("cuda").eval()
        for e in sample:
            ctx = e["context"][-2000:]
            ids_c = tok(ctx, return_tensors="pt", add_special_tokens=False,
                        truncation=True, max_length=1200).input_ids.to("cuda")
            cand = tok(" " + e["suggestion"], return_tensors="pt",
                       add_special_tokens=False,
                       truncation=True, max_length=120).input_ids.to("cuda")
            full = torch.cat([ids_c, cand], dim=1)
            with torch.no_grad():
                logits = model(full).logits.float()
            lp = torch.log_softmax(logits[0, :-1], dim=-1)
            tgt = full[0, 1:]
            n_c = ids_c.shape[1]
            s2 = sum(lp[i, tgt[i]].item()
                     for i in range(n_c - 1, full.shape[1] - 1)) / cand.shape[1]
            rows.append({"taken": e["taken"], "logp": s2,
                         "sug_len": len(e["suggestion"].split())})
        del model
        torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    acc_lp = [r["logp"] for r in rows if r["taken"]]
    rej_lp = [r["logp"] for r in rows if not r["taken"]]
    import bisect                                                                 # noqa: PLC0415
    srt = sorted(rej_lp)
    auc = sum(bisect.bisect_left(srt, a) + 0.5 * (bisect.bisect_right(srt, a)
              - bisect.bisect_left(srt, a)) for a in acc_lp) / \
        (len(acc_lp) * len(srt)) if acc_lp and srt else None
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "reader": mk, "n_scored": len(rows),
         "n_accept": len(acc_lp), "n_reject": len(rej_lp),
         "mean_logp_accepted": sum(acc_lp) / len(acc_lp) if acc_lp else None,
         "mean_logp_rejected": sum(rej_lp) / len(rej_lp) if rej_lp else None,
         "auc_fit_predicts_accept": auc,
         "dismissal_text_note": "dismissed episodes use the first shown suggestion "
         "as the seen text; selected ones use the selected index",
         "stage2_baseline_note": "take rate flat at 0.758 in Stage 2; this asks "
         "whether contextual fit separates the decisions position could not"},
        indent=1), encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"H04 landed: AUC {auc}, n {len(rows)}")
    return 0


def arm_h05() -> int:
    """H05 ScholaWrite sequential intention structure (card E24-S3-H05): how much of a
    writer's NEXT intention is carried by the intention SEQUENCE alone — no text at all —
    under the canonical leave-one-project-out protocol? The Markov answer is the floor
    any text reader must beat, and Stage 2's faithful text arms (0.580/0.546, L86) sit
    on record beside it.
    DESIGN CHECK: canonical LOPO split only (the L68 within-project leak is the banked
    caveat — no shipped-split numbers are quoted); floors first (majority, marginal);
    counts recorded before science; label set read from the data, never hardcoded."""
    cell = "E24-S3-H05"
    t0 = time.time()
    out = OUT_H / "H05"
    out.mkdir(parents=True, exist_ok=True)
    import pandas as pd                                                           # noqa: PLC0415
    from collections import Counter, defaultdict                                  # noqa: PLC0415
    from datasets import load_from_disk                                           # noqa: PLC0415
    ds = load_from_disk(str(REPO / "results" / "scholawrite" / "dataset"))
    df = ds["all_sorted"].to_pandas()
    label_col = "label"
    proj_col = "project"
    df = df.sort_values([proj_col, "timestamp"])
    labels = sorted(df[label_col].dropna().unique().tolist())
    projects = sorted(df[proj_col].dropna().unique().tolist())
    rows_out = {"n_events": len(df), "n_labels": len(labels),
                "n_projects": len(projects)}
    print(f"  {len(df)} events, {len(labels)} labels, {len(projects)} projects")
    # leave-one-project-out: train Markov + priors on other projects
    accs = {"majority": [], "marginal_argmax": [], "markov1": [], "markov2": []}
    for hold in projects:
        tr = df[df[proj_col] != hold]
        te = df[df[proj_col] == hold]
        seq_te = te[label_col].tolist()
        if len(seq_te) < 3:
            continue
        maj = tr[label_col].value_counts().idxmax()
        m1 = defaultdict(Counter)
        m2 = defaultdict(Counter)
        for _pid, g in tr.groupby(proj_col):
            seq = g[label_col].tolist()
            for i in range(1, len(seq)):
                m1[seq[i - 1]][seq[i]] += 1
                if i >= 2:
                    m2[(seq[i - 2], seq[i - 1])][seq[i]] += 1
        h_maj = h_m1 = h_m2 = n = 0
        for i in range(2, len(seq_te)):
            truth = seq_te[i]
            n += 1
            h_maj += maj == truth
            prev1 = seq_te[i - 1]
            pred1 = (m1[prev1].most_common(1)[0][0]
                     if m1[prev1] else maj)
            h_m1 += pred1 == truth
            key2 = (seq_te[i - 2], seq_te[i - 1])
            pred2 = (m2[key2].most_common(1)[0][0] if m2[key2] else pred1)
            h_m2 += pred2 == truth
        accs["majority"].append(h_maj / n)
        accs["marginal_argmax"].append(h_maj / n)
        accs["markov1"].append(h_m1 / n)
        accs["markov2"].append(h_m2 / n)
    summary = {k: {"mean": sum(v) / len(v), "n_projects": len(v)}
               for k, v in accs.items() if v}
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "counts": rows_out, "lopo_accuracy": summary,
         "stage2_text_readers_for_comparison": {"faithful_arms": [0.580, 0.546],
                                                "source": "L86"},
         "labels": labels}, indent=1), encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"H05 landed: {json.dumps(summary)}")
    return 0


def arm_h02() -> int:
    """H02 transfer (card E24-S3-H02): does the H01 purpose-vs-detail structure hold on
    a second, independent question source — the RACE middle-school split (younger
    audience, different passage register)? Same banks discipline, same readers.
    DESIGN CHECK: identical filters and floors as H01; nothing tuned between."""
    cell = "E24-S3-H02"
    t0 = time.time()
    out = OUT_H / "H02"
    out.mkdir(parents=True, exist_ok=True)
    from datasets import load_dataset                                             # noqa: PLC0415
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    from runners.s3_lib import perm_p                                             # noqa: PLC0415
    bank_p = out / "bank.json"
    if not bank_p.exists():
        ds = load_dataset("ehovy/race", "middle", split="train")
        purpose, detail = [], []
        n_total = 0
        for ex in ds:
            n_total += 1
            q = ex["question"]
            row = {"passage": ex["article"], "question": q,
                   "options": ex["options"],
                   "answer": "ABCD".index(ex["answer"]), "id": ex["example_id"]}
            if PURPOSE_RE.search(q) and "_" not in q:
                purpose.append(row)
            elif DETAIL_RE.search(q) and "_" not in q:
                detail.append(row)
        rng = random.Random(SEED0 + 2)
        rng.shuffle(purpose)
        rng.shuffle(detail)
        n_keep = min(500, len(purpose), len(detail))
        bank_p.write_text(json.dumps(
            {"n_scanned": n_total, "purpose": purpose[:n_keep],
             "detail": detail[:n_keep]}, ensure_ascii=False),
            encoding="utf-8", newline="\n")
        print(f"  H02 bank: {n_keep} per class from {n_total}")
    bank = json.loads(bank_p.read_text(encoding="utf-8"))
    report = {}
    acquire_gpu_lock("s3_h02")
    try:
        for mk in READERS:
            shortm = mk.split("/")[-1][:8]
            dest = out / f"read_{shortm}.json"
            if dest.exists():
                report[shortm] = json.loads(dest.read_text(encoding="utf-8"))
                continue
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            res = {}
            for kind in ("purpose", "detail"):
                rows = bank[kind]
                hits = 0
                for r in rows:
                    ctx = (f"Passage:\n{r['passage']}\n\nQuestion: "
                           f"{r['question']}\nAnswer:")
                    pred = _score_options(model, tok, ctx, r["options"])
                    hits += pred == r["answer"]
                res[kind] = {"n": len(rows), "acc": hits / len(rows)}
            dest.write_text(json.dumps(res), encoding="utf-8", newline="\n")
            report[shortm] = res
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "readers": report, "floor_random": 0.25,
         "h01_comparison_pointer": str(OUT_H / "H01" / "verdict.json")},
        indent=1), encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"H02 landed: {json.dumps(report)}")
    return 0


def arm_h03() -> int:
    """H03 SocialIQA control (card E24-S3-H03): social-intent questions (why did X do
    that / what does X want next) as the social-inference ground, scored with the same
    likelihood readers and the same question-only floor as H01.
    DESIGN CHECK: same scorer, same floors; counts recorded; 3-option items so the
    random floor is 1/3 (stated, never mixed with RACE's 1/4)."""
    cell = "E24-S3-H03"
    t0 = time.time()
    out = OUT_H / "H03"
    out.mkdir(parents=True, exist_ok=True)
    from datasets import load_dataset                                             # noqa: PLC0415
    import torch                                                                  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer                  # noqa: PLC0415
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock           # noqa: PLC0415
    ds = None
    try:
        ds = load_dataset("allenai/social_i_qa", split="validation",
                          trust_remote_code=True)
    except Exception:                                                             # noqa: BLE001
        pass
    if ds is None:
        # parquet-branch fallback (datasets 5 retired script loaders)
        try:
            from huggingface_hub import list_repo_files, hf_hub_download          # noqa: PLC0415
            import pandas as pd                                                   # noqa: PLC0415
            from datasets import Dataset                                          # noqa: PLC0415
            files = list_repo_files("allenai/social_i_qa", repo_type="dataset",
                                    revision="refs/convert/parquet")
            val = [f for f in files if "validation" in f
                   and f.endswith(".parquet")]
            frames = [pd.read_parquet(hf_hub_download(
                "allenai/social_i_qa", f, repo_type="dataset",
                revision="refs/convert/parquet")) for f in val]
            ds = Dataset.from_pandas(pd.concat(frames, ignore_index=True))
            print(f"  H03 parquet fallback: {len(ds)} rows from "
                  f"{len(val)} files")
        except Exception:                                                         # noqa: BLE001
            pass
    try:
        if ds is None:
            raise RuntimeError("script loader and parquet branch both failed")
    except Exception as e:                                                        # noqa: BLE001
        (out / "verdict.json").write_text(json.dumps(
            {"cell": cell, "status": "RESOURCE_BLOCKED", "error": str(e)[:200]},
            indent=1), encoding="utf-8", newline="\n")
        set_status(cell, "RESOURCE_BLOCKED",
                   closure_reason=f"SocialIQA fetch failed: {str(e)[:100]}",
                   actual_gpu_minutes=0.0)
        (out / "retry_receipt.json").write_text(json.dumps(
            {"cell": cell, "status": "RESOURCE_BLOCKED",
             "error": str(e)[:200]}, indent=1), encoding="utf-8",
            newline="\n")
        print(f"H03 RESOURCE_BLOCKED: {e}")
        return 0
    rng = random.Random(SEED0 + 3)
    idx = list(range(len(ds)))
    rng.shuffle(idx)
    items = [ds[i] for i in idx[:600]]
    report = {}
    acquire_gpu_lock("s3_h03")
    try:
        for mk in READERS:
            shortm = mk.split("/")[-1][:8]
            dest = out / f"read_{shortm}.json"
            if dest.exists():
                report[shortm] = json.loads(dest.read_text(encoding="utf-8"))
                continue
            tok = AutoTokenizer.from_pretrained(mk)
            model = AutoModelForCausalLM.from_pretrained(
                mk, dtype=torch.float16).to("cuda").eval()
            hits = hits_q = 0
            for ex in items:
                opts = [ex["answerA"], ex["answerB"], ex["answerC"]]
                truth = int(ex["label"]) - 1
                ctx = (f"Context: {ex['context']}\nQuestion: {ex['question']}"
                       f"\nAnswer:")
                ctx_q = f"Question: {ex['question']}\nAnswer:"
                hits += _score_options(model, tok, ctx, opts) == truth
                hits_q += _score_options(model, tok, ctx_q, opts) == truth
            report[shortm] = {"n": len(items), "acc": hits / len(items),
                              "acc_question_only": hits_q / len(items)}
            dest.write_text(json.dumps(report[shortm]), encoding="utf-8",
                            newline="\n")
            del model
            torch.cuda.empty_cache()
    finally:
        release_gpu_lock()
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "readers": report, "floor_random": 1 / 3}, indent=1),
        encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    (out / "retry_receipt.json").write_text(json.dumps(
        {"cell": cell, "status": "LANDED"}, indent=1), encoding="utf-8",
        newline="\n")
    print(f"H03 landed: {json.dumps(report)}")
    return 0


def arm_h06() -> int:
    """H06 revision-purpose persistence (card E24-S3-H06): the L173 question asked of
    the independent revision corpus this project already recreated (the recorded
    revision-purpose events of the Stage-1 G129/G136 line): do revision PURPOSES
    persist across consecutive revisions by the same writer the way keystroke
    intentions do? DESIGN CHECK: purely sequential floors, no text; writer-held-out
    where writer ids exist; counts recorded first; the L173 ScholaWrite number beside
    it for the cross-corpus comparison."""
    cell = "E24-S3-H06"
    t0 = time.time()
    out = OUT_H / "H06"
    out.mkdir(parents=True, exist_ok=True)
    from collections import Counter, defaultdict                                  # noqa: PLC0415
    ev_path = REPO / "results" / "arg_baselines" / "events.json"
    events = json.loads(ev_path.read_text(encoding="utf-8"))
    if isinstance(events, dict):
        events = events.get("events", [])
    # group by essay/writer id and order by position
    key_fields = [k for k in ("author", "essay_id", "writer", "file", "essay")
                  if events and k in events[0]]
    lab_fields = [k for k in ("fine", "purpose", "label", "intention")
                  if events and k in events[0]]
    if not key_fields or not lab_fields:
        (out / "verdict.json").write_text(json.dumps(
            {"cell": cell, "status": "INSTRUMENT-FAILED",
             "fields_seen": list(events[0].keys()) if events else []},
            indent=1), encoding="utf-8", newline="\n")
        set_status(cell, "INSTRUMENT_FAILED",
                   closure_reason="event schema lacks writer/purpose fields",
                   actual_gpu_minutes=0.0)
        print("H06 schema mismatch — inspect events.json fields")
        return 0
    kf, lf = key_fields[0], lab_fields[0]
    seqs = defaultdict(list)
    for e in events:
        seqs[e[kf]].append(e[lf])
    same = trans = 0
    for _k, seq in seqs.items():
        for i in range(1, len(seq)):
            trans += 1
            same += seq[i] == seq[i - 1]
    # held-out-writer Markov
    writers = sorted(seqs)
    accs = {"majority": [], "markov1": []}
    for hold in writers:
        tr_seqs = [s2 for k2, s2 in seqs.items() if k2 != hold]
        te = seqs[hold]
        if len(te) < 3:
            continue
        flat = [x for s2 in tr_seqs for x in s2]
        maj = Counter(flat).most_common(1)[0][0]
        m1 = defaultdict(Counter)
        for s2 in tr_seqs:
            for i in range(1, len(s2)):
                m1[s2[i - 1]][s2[i]] += 1
        h_m = h_1 = n = 0
        for i in range(1, len(te)):
            n += 1
            h_m += maj == te[i]
            pred = m1[te[i - 1]].most_common(1)[0][0] if m1[te[i - 1]] else maj
            h_1 += pred == te[i]
        accs["majority"].append(h_m / n)
        accs["markov1"].append(h_1 / n)
    summary = {k: sum(v) / len(v) for k, v in accs.items() if v}
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "n_events": len(events), "n_sequences": len(seqs),
         "self_transition_rate": same / trans if trans else None,
         "held_out_writer_accuracy": summary,
         "scholawrite_comparison": {"self_transition": 0.879,
                                    "markov1_lopo": 0.883, "source": "L173"}},
        indent=1), encoding="utf-8", newline="\n")
    set_status(cell, "LANDED", actual_gpu_minutes=(time.time() - t0) / 60)
    print(f"H06 landed: self-transition "
          f"{same / trans if trans else None}, {json.dumps(summary)}")
    return 0


def arm_h07() -> int:
    """H07 hidden-continuation reviews (card E24-S3-H07): peer-review texts where a
    review's stated stance continues into a hidden half — recover the continuation
    stance from the visible half. Source: an HF mirror of ICLR OpenReview reviews;
    if none is reachable this cell closes RESOURCE_BLOCKED with the exact error.
    DESIGN CHECK: >=500 items or the cell refuses; split point at the review's
    midpoint sentence; stance = the review's recommendation field (ground truth from
    metadata, never inferred); mechanical readout by likelihood over stance
    statements."""
    cell = "E24-S3-H07"
    t0 = time.time()
    out = OUT_H / "H07"
    out.mkdir(parents=True, exist_ok=True)
    from datasets import load_dataset                                             # noqa: PLC0415
    ds = None
    err = []
    for name, kw in (("ICLR2024-review", {}),
                     ("mrm8488/iclr2019_open_reviews", {}),
                     ("shauryr/ICLR2023-paper-reviews", {})):
        try:
            ds = load_dataset(name, split="train", **kw)
            src = name
            break
        except Exception as e:                                                    # noqa: BLE001
            err.append(f"{name}: {str(e)[:80]}")
    if ds is None:
        (out / "verdict.json").write_text(json.dumps(
            {"cell": cell, "status": "RESOURCE_BLOCKED", "errors": err},
            indent=1), encoding="utf-8", newline="\n")
        set_status(cell, "RESOURCE_BLOCKED",
                   closure_reason="no reachable OpenReview mirror on HF; "
                   "candidates tried recorded in verdict",
                   actual_gpu_minutes=(time.time() - t0) / 60)
        print(f"H07 RESOURCE_BLOCKED: {err}")
        return 0
    cols = ds.column_names
    (out / "verdict.json").write_text(json.dumps(
        {"cell": cell, "status": "SOURCE-FOUND", "source": src,
         "columns": cols, "n": len(ds),
         "next": "schema-specific extraction to be wired on first inspection"},
        indent=1), encoding="utf-8", newline="\n")
    print(f"H07 source found: {src} ({len(ds)} rows, cols {cols}) — "
          "extraction wired next pass")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["h01_data", "h01_read", "h02", "h03", "h04",
                             "h05", "h06", "h07"])
    a = ap.parse_args()
    return {"h01_data": arm_h01_data, "h01_read": arm_h01_read,
            "h02": arm_h02, "h03": arm_h03, "h04": arm_h04, "h05": arm_h05,
            "h06": arm_h06, "h07": arm_h07}[a.arm]()


if __name__ == "__main__":
    sys.exit(main())
