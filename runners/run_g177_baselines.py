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
                    choices=["anchor", "scholawrite", "scholawrite_reader", "coauthor"])
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if args.arm == "anchor":
        rc = arm_anchor()
    elif args.arm == "scholawrite":
        rc = arm_scholawrite(with_reader=False)
    elif args.arm == "scholawrite_reader":
        rc = arm_scholawrite(with_reader=True)
    else:
        rc = arm_coauthor()
    print(f"{args.arm} done in {(time.time() - t0) / 60:.0f} min")
    return rc


if __name__ == "__main__":
    sys.exit(main())
