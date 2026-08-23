"""G177 natural human-process baselines. Card: prereg/g177.py (frozen).

Arms (run separately; interfaces never pooled):
  --arm anchor       conditional-likelihood reader on the G159 realized-revision cases (GPU)
  --arm scholawrite  LOPO next-intention baselines: frequency, Markov, local reader (ollama)
  --arm coauthor     fetch + inventory of the CoAuthor session logs (network, no GPU)

Outputs: results/g177/anchor.json · scholawrite_lopo.json · coauthor_import.json
"""

from __future__ import annotations

import argparse
import io
import json
import random
import re
import sys
import time
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from prereg.g177 import (ANCHOR_CONDITION, ANCHOR_FLOOR, ANCHOR_READER,          # noqa: E402
                         COAUTHOR_MIN_WRITERS, COAUTHOR_URLS, KNOWN_ANSWER_FLOOR,
                         SEED0, SW_CITATION_MARKERS, SW_HUB_ID,
                         SW_READER_KA_FLOOR, SW_READER_MODEL,
                         SW_SAMPLE_PER_PROJECT)

OUT = REPO / "results" / "g177"

_LF = chr(10)
_SW_PROMPT = (
    "A scholar is writing a document. The current draft ends:" + _LF +
    "...{before}" + _LF + _LF +
    "What is the writer's most likely next writing intention? "
    "Answer with exactly one label from:" + _LF + "{opts}" + _LF + "Label:")


# ── anchor ────────────────────────────────────────────────────────────────────────────────────

def arm_anchor() -> int:
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    from soundingline.probe.conditional_reader import (candidate_scores,         # noqa: PLC0415
                                                       load_reader)
    from runners.run_g159_recovery import load_arts                              # noqa: PLC0415

    man = json.loads((REPO / "results" / "g159" / "manifest.json").read_text(encoding="utf-8"))
    arts = load_arts()
    cases = man["p_plus"]
    acquire_gpu_lock("g177_anchor")
    try:
        model, tok = load_reader(ANCHOR_READER, device="cuda", dtype="float16")
        rng = random.Random(SEED0)

        texts = [arts[(c["family"], c["artifact_id"])]["text"] for c in cases]
        ka_hits, probes = 0, rng.sample(range(len(cases)), 16)
        for i in probes:
            own = texts[i].split(". ")[0]
            foreign = [texts[j].split(". ")[0]
                       for j in rng.sample([x for x in range(len(cases)) if x != i], 3)]
            res = candidate_scores(model, tok, [own] + foreign, texts[i])
            ka_hits += res["order"][0] == 0
        ka = ka_hits / len(probes)
        print(f"known-answer {ka:.3f}")
        if ka < KNOWN_ANSWER_FLOOR:
            band, rows = "INSTRUMENT-FAIL", []
        else:
            rows = []
            for c, text in zip(cases, texts):
                cands = [ANCHOR_CONDITION.format(cand=x) for x in c["cands"]]
                res = candidate_scores(model, tok, cands, text)
                rows.append({"artifact_id": c["artifact_id"], "family": c["family"],
                             "top1": res["order"][0] == c["truth_idx"],
                             "rank": res["order"].index(c["truth_idx"]) + 1})
            acc = sum(r["top1"] for r in rows) / len(rows)
            from math import comb                                                # noqa: PLC0415
            k = sum(r["top1"] for r in rows)
            n = len(rows)
            p = sum(comb(n, i) * ANCHOR_FLOOR ** i * (1 - ANCHOR_FLOOR) ** (n - i)
                    for i in range(k, n + 1))
            band = "READS" if (acc > ANCHOR_FLOOR and p < 0.05) else "BLIND"
            print(f"top-1 {acc:.3f} vs floor {ANCHOR_FLOOR}, binomial p {p:.2e} -> {band}")
    finally:
        release_gpu_lock()
    payload = {"prereg": "prereg/g177.py", "reader": ANCHOR_READER, "known_answer": ka,
               "band": band, "n": len(rows),
               "top1": (sum(r["top1"] for r in rows) / len(rows)) if rows else None,
               "binomial_p": (p if rows else None), "rows": rows,
               "reference_line": "direct-prompted reader 0.86 (L146), different reader"}
    (OUT / "anchor.json").write_text(json.dumps(payload, indent=1),
                                     encoding="utf-8", newline="\n")
    return 0


# ── scholawrite ───────────────────────────────────────────────────────────────────────────────

def _sw_load():
    from datasets import load_dataset                                            # noqa: PLC0415
    ds = load_dataset(SW_HUB_ID)
    # the release ships overlapping splits (train/test are subsets of all_sorted); use the
    # full sorted split alone when present, else the union
    splits = [s for s in ds if s.startswith("all")] or list(ds)
    rows = []
    for split in splits:
        d = ds[split]
        cols = d.column_names
        lab = next(c for c in cols if re.search(r"intention|label", c, re.I))
        txt = next(c for c in cols if re.search(r"before", c, re.I))
        proj = next(c for c in cols if re.search(r"project", c, re.I))
        after = next((c for c in cols if re.search(r"after", c, re.I)), None)
        for r in d:
            rows.append({"project": str(r[proj]), "label": r[lab],
                         "before": (r[txt] or "")[-1200:],
                         "after": (r[after] or "")[-1200:] if after else ""})
    return rows


def arm_sw_validation() -> int:
    """H1: the powered known-answer validation the L161 gate could not deliver.

    The random 600-event sample drew exactly ONE mechanically decidable case, so the reader
    arm's numbers were descriptive only. This stratifies TOWARD decidable edits: events whose
    delta contains a citation command and whose label is the citation class (positives), and
    events whose delta contains no citation command and whose label is not the citation class
    (negatives, sampled to match). Per LESSONS section 4, validation is stratified toward the
    NEGATIVE class and runs BEFORE the arms it licenses; per L163, the pass band is derived at
    the actual sample size rather than guessed.
    """
    from soundingline.probe.client import LocalClient                            # noqa: PLC0415
    rows = _sw_load()
    labels = sorted({r["label"] for r in rows})
    cit = next((x for x in labels if "citation" in x.lower()), None)
    if cit is None:
        print("no citation class in the label set; validation cannot be built")
        return 1

    def delta(r):
        a, b = r["before"], r["after"]
        return b[len(a):] if b.startswith(a) else b

    pos, neg = [], []
    for r in rows:
        d = delta(r)
        has = any(m in d for m in SW_CITATION_MARKERS)
        if has and r["label"] == cit:
            pos.append(r)
        elif not has and r["label"] != cit:
            neg.append(r)
    rng = random.Random(SEED0 + 5)
    n = min(len(pos), 120)
    if n < 30:
        print(f"only {len(pos)} decidable positives; validation stays underpowered")
        return 1
    pos_s = rng.sample(pos, n)
    neg_s = rng.sample(neg, n)          # matched, so the floor is analytic at 0.5
    print(f"validation set: {n} decidable positives, {n} matched negatives")

    client = LocalClient(model=SW_READER_MODEL)
    opts = _LF.join(f"- {x}" for x in labels)
    hits = {"pos": 0, "neg": 0}
    for tag, sample in (("pos", pos_s), ("neg", neg_s)):
        for r in sample:
            prompt = (_SW_PROMPT.replace("{before}", r["before"])
                                .replace("{opts}", opts))
            try:
                ans = client.read_text(
                    "You classify a writer's next writing intention. "
                    "Answer with exactly one label.", prompt).strip().lower()
            except Exception as e:                                               # noqa: BLE001
                print(f"  reader error: {e}")
                continue
            said_cit = cit.lower() in ans
            hits[tag] += said_cit if tag == "pos" else (not said_cit)
    sens = hits["pos"] / n
    spec = hits["neg"] / n
    bal = (sens + spec) / 2
    # pass band derived at this sample size: the two-sided 95 percent interval for a
    # balanced-accuracy estimate on 2n items is about 1.96 * sqrt(0.25/n) wide per arm
    half = 1.96 * (0.25 / n) ** 0.5
    band_low = 0.5 + half
    verdict = "VALIDATED" if bal > max(SW_READER_KA_FLOOR, band_low) else (
        "UNVALIDATED-ABOVE-CHANCE" if bal > band_low else "UNVALIDATED-AT-CHANCE")
    print(f"sensitivity {sens:.3f}, specificity {spec:.3f}, balanced {bal:.3f}; "
          f"chance band top {band_low:.3f}; floor {SW_READER_KA_FLOOR} -> {verdict}")
    (OUT / "scholawrite_validation.json").write_text(json.dumps({
        "prereg": "prereg/g177.py (H1 repair, Stage 2)", "verdict": verdict,
        "n_per_class": n, "sensitivity": sens, "specificity": spec,
        "balanced_accuracy": bal, "chance_band_top": band_low,
        "floor": SW_READER_KA_FLOOR, "decidable_positives_available": len(pos),
        "note": "matched negatives make the floor analytic at 0.5; the band is derived at "
                "this sample size rather than assumed"}, indent=1),
        encoding="utf-8", newline=_LF)
    return 0


_INTENT_TEMPLATE = "Next, the writer will work on {label}."
_NEUTRAL_DRAFT = "The following describes what a writer does next."


def arm_sw_nongen() -> int:
    """The routed alternative after the prompted reader failed its powered gate: a
    non-generative prospective reader.

    Instead of asking a model to name the next intention, this asks how much the draft state
    RAISES the likelihood of each intention statement, scoring
    log P(statement | draft) minus log P(statement | neutral) for all fifteen labels. The
    subtraction removes each label's own prior, so a frequent label cannot win on frequency.
    Nothing is generated, so nothing can be fabricated.

    Validation runs FIRST on the same stratified citation subset the prompted reader failed,
    with matched negatives and a band derived at the sample size. Leave-one-project-out
    numbers are computed but count only if validation passes.
    """
    from soundingline.gpulock import acquire_gpu_lock, release_gpu_lock          # noqa: PLC0415
    from soundingline.probe.conditional_reader import (artifact_logprob,         # noqa: PLC0415
                                                       load_reader)
    rows = _sw_load()
    labels = sorted({r["label"] for r in rows})
    cit = next(x for x in labels if "citation" in x.lower())
    stmts = [_INTENT_TEMPLATE.format(label=x) for x in labels]

    def delta(r):
        a, b = r["before"], r["after"]
        return b[len(a):] if b.startswith(a) else b

    pos, neg = [], []
    for r in rows:
        has = any(m in delta(r) for m in SW_CITATION_MARKERS)
        if has and r["label"] == cit:
            pos.append(r)
        elif not has and r["label"] != cit:
            neg.append(r)
    rng = random.Random(SEED0 + 6)
    n = min(len(pos), 120)
    pos_s, neg_s = rng.sample(pos, n), rng.sample(neg, n)

    acquire_gpu_lock("g177_sw_nongen")
    try:
        model, tok = load_reader(ANCHOR_READER, device="cuda", dtype="float16")
        base = [artifact_logprob(model, tok, _NEUTRAL_DRAFT, st)[0] for st in stmts]

        def predict(draft: str) -> str:
            draft = draft[-800:]
            scores = [artifact_logprob(model, tok, draft, st)[0] - b
                      for st, b in zip(stmts, base)]
            return labels[max(range(len(labels)), key=lambda i: scores[i])]

        sens = sum(predict(r["before"]) == cit for r in pos_s) / n
        spec = sum(predict(r["before"]) != cit for r in neg_s) / n
        bal = (sens + spec) / 2
        half = 1.96 * (0.25 / n) ** 0.5
        band_low = 0.5 + half
        verdict = "VALIDATED" if bal > max(SW_READER_KA_FLOOR, band_low) else (
            "UNVALIDATED-ABOVE-CHANCE" if bal > band_low else "UNVALIDATED-AT-CHANCE")
        print(f"validation: sens {sens:.3f}, spec {spec:.3f}, balanced {bal:.3f} "
              f"vs band top {band_low:.3f} -> {verdict}")

        per_project = {}
        if verdict == "VALIDATED":
            projects = sorted({r["project"] for r in rows})
            for held in projects:
                ev_all = [r for r in rows if r["project"] == held]
                ev = (ev_all if len(ev_all) <= SW_SAMPLE_PER_PROJECT
                      else rng.sample(ev_all, SW_SAMPLE_PER_PROJECT))
                pairs = [(r["label"], predict(r["before"])) for r in ev]
                f1s = []
                for lab in labels:
                    tp = sum(1 for t, q in pairs if t == lab and q == lab)
                    fp = sum(1 for t, q in pairs if t != lab and q == lab)
                    fn = sum(1 for t, q in pairs if t == lab and q != lab)
                    f1s.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
                per_project[held] = {"n": len(ev), "macro_f1": sum(f1s) / len(f1s)}
                print(f"  {held}: {per_project[held]}")
    finally:
        release_gpu_lock()

    (OUT / "scholawrite_nongen.json").write_text(json.dumps({
        "prereg": "prereg/g177.py (routed alternative, Stage 2)", "verdict": verdict,
        "reader": ANCHOR_READER, "n_per_class": n, "sensitivity": sens,
        "specificity": spec, "balanced_accuracy": bal, "chance_band_top": band_low,
        "floor": SW_READER_KA_FLOOR, "per_project": per_project,
        "note": "leave-one-project-out numbers computed only if validation passes; if this "
                "reader also fails, the prospective interface has no validated reader of "
                "any form and that is the boundary"}, indent=1),
        encoding="utf-8", newline=_LF)
    return 0


def arm_scholawrite(with_reader: bool) -> int:
    rows = _sw_load()
    projects = sorted({r["project"] for r in rows})
    labels = sorted({r["label"] for r in rows})
    print(f"{len(rows)} events, {len(projects)} projects, {len(labels)} labels")
    rng = random.Random(SEED0 + 1)

    client = None
    if with_reader:
        from soundingline.probe.client import LocalClient                        # noqa: PLC0415
        client = LocalClient(model=SW_READER_MODEL)

    def macro_f1(pairs: list[tuple[str, str]]) -> float:
        f1s = []
        for lab in labels:                       # label set FIXED (L108)
            tp = sum(1 for t, p in pairs if t == lab and p == lab)
            fp = sum(1 for t, p in pairs if t != lab and p == lab)
            fn = sum(1 for t, p in pairs if t == lab and p != lab)
            f1s.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
        return sum(f1s) / len(f1s)

    per_project = {}
    ka_pairs = []
    for held in projects:
        train = [r for r in rows if r["project"] != held]
        ev_all = [r for r in rows if r["project"] == held]
        assert not any(r["project"] != held for r in ev_all)     # leak assertion
        ev = ev_all if len(ev_all) <= SW_SAMPLE_PER_PROJECT \
            else rng.sample(ev_all, SW_SAMPLE_PER_PROJECT)
        majority = Counter(r["label"] for r in train).most_common(1)[0][0]
        trans: dict[str, Counter] = {}
        for a, b in zip(train, train[1:]):
            if a["project"] == b["project"]:
                trans.setdefault(a["label"], Counter())[b["label"]] += 1
        res = {"n": len(ev)}
        res["frequency"] = macro_f1([(r["label"], majority) for r in ev])
        mk = []
        for prev, cur in zip(ev, ev[1:]):
            guess = trans.get(prev["label"], Counter()).most_common(1)
            mk.append((cur["label"], guess[0][0] if guess else majority))
        res["markov"] = macro_f1(mk) if mk else None
        if client is not None:
            opts = "\n".join(f"- {x}" for x in labels)
            pairs = []
            for r in ev:
                prompt = (f"A scholar is writing a document. The current draft ends:\n"
                          f"...{r['before']}\n\nWhat is the writer's most likely next "
                          f"writing intention? Answer with exactly one label from:\n{opts}\n"
                          f"Label:")
                try:
                    ans = client.read_text(
                        "You classify a writer's next writing intention. "
                        "Answer with exactly one label.", prompt).strip().lower()
                except Exception as e:                                           # noqa: BLE001
                    print(f"  reader error, skipping event: {e}")
                    continue
                got = next((x for x in labels if x.lower() in ans), majority)
                pairs.append((r["label"], got))
                delta = r["after"][len(r["before"]):] if r["after"].startswith(r["before"]) \
                    else r["after"]
                if any(m in delta for m in SW_CITATION_MARKERS) \
                        and "citation" in r["label"].lower():
                    ka_pairs.append((r["label"], got))
            res["reader"] = macro_f1(pairs) if pairs else None
        per_project[held] = res
        print(f"  {held}: {res}")

    reader_ka = (sum(1 for t, p in ka_pairs if t == p) / len(ka_pairs)) if ka_pairs else None
    band = "INTERFACE-MAPPED" if len(per_project) >= 5 else "INCOMPLETE"
    # two stages must never share a produces path (LESSONS §5): the baseline arm and the
    # reader arm write distinct files
    dest_name = "scholawrite_reader.json" if with_reader else "scholawrite_lopo.json"
    (OUT / dest_name).write_text(json.dumps({
        "prereg": "prereg/g177.py", "band": band, "labels": labels,
        "reader_model": SW_READER_MODEL if with_reader else None,
        "reader_known_answer": reader_ka, "reader_ka_floor": SW_READER_KA_FLOOR,
        "reader_ka_n": len(ka_pairs), "per_project": per_project,
    }, indent=1), encoding="utf-8", newline="\n")
    return 0


# ── coauthor ──────────────────────────────────────────────────────────────────────────────────

def arm_coauthor() -> int:
    dest = REPO / "corpora" / "coauthor"
    dest.mkdir(parents=True, exist_ok=True)
    blob = None
    for url in COAUTHOR_URLS:
        try:
            print(f"fetching {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "sounding-line/2.4"})
            with urllib.request.urlopen(req, timeout=600) as r:
                blob = r.read()
            break
        except Exception as e:                                                   # noqa: BLE001
            print(f"  failed: {e}")
    if blob is None:
        print("COAUTHOR FETCH UNREACHABLE — no manifest, stage retries")
        return 1
    zf = zipfile.ZipFile(io.BytesIO(blob))
    names = zf.namelist()
    sessions = [n for n in names if n.endswith(".jsonl") or n.endswith(".json")]
    zf.extractall(dest)
    writers = set()
    n_events = 0
    for n in sessions[:2000]:
        p = dest / n
        if not p.exists():
            continue
        try:
            for line in p.read_text(encoding="utf-8").splitlines()[:5000]:
                ev = json.loads(line)
                n_events += 1
                for k in ("worker_id", "author_id", "writer_id", "session_id"):
                    if k in ev:
                        writers.add(str(ev[k]))
                        break
        except Exception:                                                        # noqa: BLE001
            continue
    n_writers = len(writers) or len(sessions)   # some releases key writers by session file
    if n_writers < COAUTHOR_MIN_WRITERS:
        print(f"thin import ({n_writers} writers) — manifest withheld")
        return 1
    (OUT / "coauthor_import.json").write_text(json.dumps({
        "prereg": "prereg/g177.py", "band": "IMPORTED", "n_files": len(sessions),
        "n_events_sampled": n_events, "n_writers_or_sessions": n_writers,
    }, indent=1), encoding="utf-8", newline="\n")
    print(f"IMPORTED: {len(sessions)} session files, {n_writers} writers/sessions")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["anchor", "scholawrite", "scholawrite_reader", "coauthor",
                             "sw_validation", "sw_nongen"])
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if args.arm == "anchor":
        rc = arm_anchor()
    elif args.arm == "scholawrite":
        rc = arm_scholawrite(with_reader=False)
    elif args.arm == "scholawrite_reader":
        rc = arm_scholawrite(with_reader=True)
    elif args.arm == "sw_validation":
        rc = arm_sw_validation()
    elif args.arm == "sw_nongen":
        rc = arm_sw_nongen()
    else:
        rc = arm_coauthor()
    print(f"{args.arm} done in {(time.time() - t0) / 60:.0f} min")
    return rc


if __name__ == "__main__":
    sys.exit(main())
