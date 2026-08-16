"""G150 — feature channels over the PAN 2025 sentence pairs, for the layering A/B.

Phase 2's first build (the curator's showpiece direction, tentatively approved
2026-08-16): compute our instrument-derived feature channels for every consecutive-sentence
pair in the 2025 style-change task, aligned exactly to the wqd substrate's pair order, so
the preregistered A/B (substrate alone vs substrate + channels) can train the moment the
card frees.

Channels per pair (s1, s2), honestly scoped to what applies at sentence grain — the
movement instruments need windows and stay at document grain, so what rides here is the
delta family the record validated (the 19-dim string-diff block carried ArgRewrite's pair
task, L85) plus per-sentence statics:

    19  string-diff block (change_features: token Jaccard, sequence ratios,
        insert/delete/replace counts, length deltas, empty-side flags)
     2x9 per-sentence statics: length (words), mean word length, type-token ratio,
        punctuation rate, digit rate, uppercase rate, stopword rate, mean sentence-word
        rank proxy (inverse frequency by corpus rank), function-word share
     2x40 function-word profile per sentence (relative frequency over a fixed 40-word
        list), plus |delta| (40) and cosine (1)
    = 19 + 18 + 80 + 40 + 1 = 158 dims

Output: results/pan25_channels/{difficulty}_{split}.npz with X [n_pairs, 158], plus a
meta json recording problem ids and per-problem pair counts in the exact substrate order
(problems sorted as load_split sorts them, pairs in sentence order), so alignment to the
wqd predictions is positional and assertable.

CPU only; never touches the GPU lock. Usage: build_pan25_channels.py [--difficulty hard]
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runners"))

from run_arg_replication import change_features            # noqa: E402
from run_pan25_winner import PAN25, load_split             # noqa: E402

RESULTS = REPO / "results" / "pan25_channels"

FW = ("the of and a to in is that it was for on are as with his they at be this have "
      "from or had by not but what all were when we there can an your which their "
      "would could").split()
assert len(FW) == 40, len(FW)
STOP = set(FW) | set("i you he she it we they am been being do does did so no yes".split())
WORD = re.compile(r"[A-Za-z']+")


def statics(s: str, rank: dict) -> list[float]:
    words = WORD.findall(s.lower())
    n = len(words)
    chars = len(s)
    if n == 0:
        return [0.0] * 9
    return [
        float(n),
        sum(len(w) for w in words) / n,
        len(set(words)) / n,
        sum(1 for c in s if c in ".,;:!?—-\"'()") / max(chars, 1),
        sum(c.isdigit() for c in s) / max(chars, 1),
        sum(c.isupper() for c in s) / max(chars, 1),
        sum(1 for w in words if w in STOP) / n,
        sum(math.log1p(rank.get(w, len(rank))) for w in words) / n,
        sum(1 for w in words if w in FW) / n,
    ]


def fw_profile(s: str) -> list[float]:
    words = WORD.findall(s.lower())
    n = max(len(words), 1)
    return [words.count(w) / n for w in FW]


def main() -> None:
    import numpy as np                                     # noqa: PLC0415

    ap = argparse.ArgumentParser()
    ap.add_argument("--difficulty", default="hard")
    args = ap.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    # corpus word ranks from the training split only (no eval-side statistics leak into
    # the channel definitions)
    train = load_split(PAN25 / args.difficulty / "train")
    freq: dict = {}
    for p in train:
        for s in p["sents"]:
            for w in WORD.findall(s.lower()):
                freq[w] = freq.get(w, 0) + 1
    rank = {w: i for i, (w, _) in
            enumerate(sorted(freq.items(), key=lambda kv: -kv[1]))}

    for split in ("train", "validation", "test"):
        probs = load_split(PAN25 / args.difficulty / split)
        X, meta = [], []
        for p in probs:
            if not p["ok"]:
                meta.append({"id": p["id"], "n_pairs": 0, "skipped": True})
                continue
            n_pairs = 0
            for a, b in zip(p["sents"], p["sents"][1:]):
                fa, fb = fw_profile(a), fw_profile(b)
                da = [abs(x - y) for x, y in zip(fa, fb)]
                na = math.sqrt(sum(x * x for x in fa)) or 1.0
                nb = math.sqrt(sum(x * x for x in fb)) or 1.0
                cos = sum(x * y for x, y in zip(fa, fb)) / (na * nb)
                X.append(change_features(a, b) + statics(a, rank) + statics(b, rank)
                         + fa + fb + da + [cos])
                n_pairs += 1
            meta.append({"id": p["id"], "n_pairs": n_pairs, "skipped": False})
        Xa = np.asarray(X, dtype=np.float32)
        assert Xa.shape[1] == 19 + 18 + 80 + 40 + 1, Xa.shape
        np.savez_compressed(RESULTS / f"{args.difficulty}_{split}.npz", X=Xa)
        (RESULTS / f"{args.difficulty}_{split}_meta.json").write_text(
            json.dumps({"difficulty": args.difficulty, "split": split,
                        "n_pairs": int(Xa.shape[0]), "dims": int(Xa.shape[1]),
                        "problems": meta}, indent=1),
            encoding="utf-8", newline="\n")
        print(f"{split}: {Xa.shape[0]} pairs x {Xa.shape[1]} dims", flush=True)
    print("wrote results/pan25_channels/")


if __name__ == "__main__":
    main()
