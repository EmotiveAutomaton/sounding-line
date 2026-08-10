"""G136-exact — recreate the ArgRewrite paper's classification numbers, not its conclusions.

THE CAPABILITY PASS. The published sentential baselines (Table 6/7, fetched and read 2026-08-10):

    binary   Majority .37/.58   Features .90/.90   USE .92/.92   Features+USE .93/.93
    fine     Majority .05/.29   Features .44/.58   USE .49/.62   Features+USE .51/.63
                                                   (avg unweighted F1 / accuracy, 5-fold CV)

Their exact recipe, reproduced: features = sentence length, sentence position, POS-tag term
frequencies (spaCy), transition-word term frequencies; embeddings = Universal Sentence Encoder
(transformer variant) on the <old, new> pair; classifier = XGBoost, grid n_estimators in
{250,500,750,1000} x max_depth in {3,4,5} x lr in {.1,.05,.01}; 5-fold CV, average unweighted
F-score and accuracy. No author grouping is mentioned in the paper, so the folds here are plain
shuffled KFold, matching their protocol rather than improving on it.

PASS = the Features+USE cells match the published numbers at two decimals. Anything further off
implies our modeling of their pipeline is wrong somewhere, and the deltas table is the search map.

Known underdeterminations, resolved to the most standard reading and recorded: the USE pair
combination (concatenation of the two 512-d vectors), POS/transition features computed on old and
new and concatenated, multi-purpose cells split into one example per purpose, grid selected on
the same 5-fold mean (the common practice when no nested tuning is described).
"""

from __future__ import annotations

import json
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "arg_baselines"
ANNOT = REPO / "corpora" / "public" / "argrewrite" / "annotations"

TARGETS = {
    "binary": {"majority": (0.37, 0.58), "features": (0.90, 0.90),
               "use": (0.92, 0.92), "features_use": (0.93, 0.93)},
    "fine": {"majority": (0.05, 0.29), "features": (0.44, 0.58),
             "use": (0.49, 0.62), "features_use": (0.51, 0.63)},
}
FINE9 = {
    "word-usage/clarity": "word_usage", "conventions/grammar/spelling": "grammar_spelling",
    "organization": "organization", "claims/ideas": "claim",
    "warrant/reasoning/backing": "reasoning", "evidence": "evidence",
    "rebuttal/reservation": "rebuttal", "precision": "precision",
    "general content development": "general_content",
}
SURFACE9 = {"word_usage", "grammar_spelling", "organization"}
TRANSITIONS = ("however", "therefore", "moreover", "furthermore", "consequently", "although",
               "because", "since", "thus", "hence", "meanwhile", "nevertheless", "instead",
               "additionally", "also", "finally", "first", "second", "third", "then", "next",
               "for example", "for instance", "in addition", "in conclusion", "in contrast",
               "on the other hand", "as a result", "in fact", "indeed", "overall", "similarly",
               "specifically", "accordingly", "besides", "still", "yet", "so", "but", "and")


def extract_v2():
    from openpyxl import load_workbook                                # noqa: PLC0415

    events = []
    for wb_path in sorted(ANNOT.rglob("*.xlsx")):
        m = re.search(r"[\\/](12|23)[\\/]", str(wb_path))
        cyc = m.group(1) if m else "??"
        am = re.search(r"argrewrite_(\d+)", wb_path.stem)
        author = am.group(1) if am else wb_path.stem
        try:
            wb = load_workbook(wb_path, read_only=True, data_only=True)
        except Exception:
            continue

        def table(ws):
            ws.reset_dimensions()
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                return None
            hdr = [str(c).strip().lower() if c is not None else "" for c in rows[0]]

            def col(nm):
                return next((i for i, h in enumerate(hdr) if nm in h), None)

            ix = {"i": col("sentence index"), "txt": col("sentence content"),
                  "al": col("aligned index"), "p1": col("purpose level 1"),
                  "p0": col("purpose level 0")}
            if ix["i"] is None or ix["txt"] is None:
                return None
            out = []
            for r in rows[1:]:
                out.append({k: (r[v] if v is not None and v < len(r) else None)
                            for k, v in ix.items()})
            return out

        sheets = {ws.title.lower(): table(ws) for ws in wb.worksheets}
        wb.close()
        old = next((v for k, v in sheets.items() if "old" in k and v), None) or []
        new = next((v for k, v in sheets.items() if "new" in k and v), None) or []

        def as_int(v):
            try:
                return int(float(str(v).split(",")[0]))
            except (TypeError, ValueError):
                return None

        old_by_i = {}
        for r in old:
            i = as_int(r["i"])
            if i is not None:
                old_by_i[i] = r

        def purposes(*rows_):
            out = []
            for r in rows_:
                if not r:
                    continue
                raw = r["p1"] or r["p0"]
                if not raw:
                    continue
                for piece in str(raw).lower().split(","):
                    piece = piece.strip()
                    if piece and piece not in ("none", "nan"):
                        out.append(piece)
            seen, uniq = set(), []
            for p in out:
                if p not in seen:
                    seen.add(p)
                    uniq.append(p)
            return uniq

        consumed_old = set()
        for r in new:
            al = as_int(r["al"])
            o = old_by_i.get(al)
            if o is not None:
                consumed_old.add(al)
            for p in purposes(r, o):
                events.append({"author": author, "cycle": cyc, "raw": p,
                               "old": str((o or {}).get("txt") or "").strip()[:600],
                               "new": str(r["txt"] or "").strip()[:600],
                               "pos_idx": as_int(r["i"]) or 0})
        for i, r in old_by_i.items():
            if i in consumed_old:
                continue
            for p in purposes(r):
                events.append({"author": author, "cycle": cyc, "raw": p,
                               "old": str(r["txt"] or "").strip()[:600], "new": "",
                               "pos_idx": i})
    for e in events:
        e["fine"] = FINE9.get(e["raw"])
    events = [e for e in events if e["fine"]]
    # v3: one purpose per revision pair. v2's comma-splitting produced label-conflicting
    # duplicates of the same (old, new) pair, which is the prime suspect for the fine-task
    # collapse (0.27 vs the published 0.44+) -- the paper's n is 3,238 and the split gave 3,365.
    seen: set = set()
    first_only = []
    for e in events:
        key = (e["author"], e["cycle"], e["old"], e["new"])
        if key in seen:
            continue
        seen.add(key)
        first_only.append(e)
    events = first_only
    for e in events:
        e["binary"] = "surface" if e["fine"] in SURFACE9 else "content"
    from collections import Counter                                   # noqa: PLC0415
    cyc = Counter(e["cycle"] for e in events)
    print(f"v3 per-cycle n: {dict(cyc)} (total {len(events)}; paper sentential 3,238)")
    return events


def main() -> None:
    import numpy as np                                                # noqa: PLC0415
    from sklearn.model_selection import KFold                         # noqa: PLC0415
    from sklearn.metrics import f1_score, accuracy_score              # noqa: PLC0415
    from xgboost import XGBClassifier                                 # noqa: PLC0415

    events = extract_v2()
    print(f"extract v2: {len(events)} examples "
          f"(paper sentential n = 3,238), {len({e['author'] for e in events})} authors")

    # ── traditional features: length, position, POS tag TFs, transition TFs (old and new)
    import spacy                                                      # noqa: PLC0415
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner", "lemmatizer"])
    tagset = sorted({"ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM",
                     "PART", "PRON", "PROPN", "PUNCT", "SCONJ", "SYM", "VERB", "X"})

    def trad(e):
        row = [len(e["old"].split()), len(e["new"].split()), e["pos_idx"]]
        for txt in (e["old"], e["new"]):
            doc = nlp(txt) if txt else []
            counts = {t: 0 for t in tagset}
            for tok in doc:
                if tok.pos_ in counts:
                    counts[tok.pos_] += 1
            row.extend(counts[t] for t in tagset)
            low = " " + txt.lower() + " "
            row.extend(low.count(" " + w + " ") for w in TRANSITIONS)
        return row

    print("featurizing (spaCy POS + transitions)...", flush=True)
    X_trad = np.array([trad(e) for e in events], float)

    # ── USE embeddings of the <old, new> pair, concatenated
    print("loading Universal Sentence Encoder (transformer variant)...", flush=True)
    import os                                                         # noqa: PLC0415
    os.environ.setdefault("TFHUB_CACHE_DIR", str(REPO / "results" / "use_cache"))
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"   # TF on CPU; the card belongs to torch and ollama
    import tensorflow_hub as hub                                      # noqa: PLC0415
    use = hub.load("https://tfhub.dev/google/universal-sentence-encoder-large/5")

    def embed(texts):
        out = []
        for i in range(0, len(texts), 256):
            out.append(use(texts[i:i + 256]).numpy())
        return np.vstack(out)

    print("embedding old/new sentences...", flush=True)
    E_old = embed([e["old"] or " " for e in events])
    E_new = embed([e["new"] or " " for e in events])
    X_use = np.hstack([E_old, E_new])

    GRID = [{"n_estimators": n, "max_depth": d, "learning_rate": lr}
            for n in (250, 500, 750, 1000) for d in (3, 4, 5) for lr in (.1, .05, .01)]

    def evaluate(task):
        y_raw = [e[task] for e in events]
        classes = sorted(set(y_raw))
        y = np.array([classes.index(v) for v in y_raw])
        arms = {"majority": None, "features": X_trad, "use": X_use,
                "features_use": np.hstack([X_trad, X_use])}
        res = {}
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        for arm, X in arms.items():
            if arm == "majority":
                maj = np.bincount(y).argmax()
                preds = np.full_like(y, maj)
                res[arm] = {"f1": float(f1_score(y, preds, average="macro")),
                            "acc": float(accuracy_score(y, preds))}
                continue
            best = None
            for g in GRID:
                f1s, accs = [], []
                for tr, te in kf.split(X):
                    clf = XGBClassifier(**g, tree_method="hist", n_jobs=-1,
                                        eval_metric="mlogloss", verbosity=0)
                    clf.fit(X[tr], y[tr])
                    p = clf.predict(X[te])
                    f1s.append(f1_score(y[te], p, average="macro"))
                    accs.append(accuracy_score(y[te], p))
                cand = {"f1": float(np.mean(f1s)), "acc": float(np.mean(accs)), "grid": g}
                if best is None or cand["f1"] > best["f1"]:
                    best = cand
            res[arm] = best
            print(f"  {task}/{arm}: F1 {best['f1']:.3f} acc {best['acc']:.3f} "
                  f"(target {TARGETS[task][arm]})", flush=True)
        return res

    out = {"n": len(events), "targets": TARGETS, "results": {}}
    for task in ("binary", "fine"):
        print(f"== {task}", flush=True)
        out["results"][task] = evaluate(task)

    deltas, passed = {}, True
    for task in TARGETS:
        for arm, (tf1, tacc) in TARGETS[task].items():
            r = out["results"][task][arm]
            deltas[f"{task}/{arm}"] = {"f1": round(r["f1"] - tf1, 3),
                                       "acc": round(r["acc"] - tacc, 3)}
            if arm == "features_use" and (abs(round(r["f1"], 2) - tf1) > 0.005 or
                                          abs(round(r["acc"], 2) - tacc) > 0.005):
                passed = False
    out["deltas"] = deltas
    out["verdict"] = "CAPABILITY-PASS" if passed else "NOT-MATCHED"
    print(f"\n  >>> {out['verdict']}\n  deltas: {json.dumps(deltas, indent=1)}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "replication.json").write_text(json.dumps(out, indent=1),
                                              encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'replication.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
