"""G130 — the shared event-level recovery harness, validated on synthetic ground truth first.

The program's unit of analysis: a decision event (target, alternatives, choice, dependencies,
context). Before any real corpus is scored, the harness itself must pass known-answer gates, per
the standing rule. This runner builds synthetic decision events with a planted recoverable signal
and checks every control the harness ships:

    ORACLE      a reader with real (noisy) access to the choice must score above chance
    SHUFFLE     shuffled purpose labels must score at chance
    UNCHANGED   unchanged passages must offer no recovery
    DECOY       matched decoys must not be systematically easier than the true choice
    BLIND       a reader with no access (context stripped) must fall to chance

All five must pass or the harness may not be used on ArgRewrite (G129 runs through this code).
The synthetic world: passages assembled from template slots; each event is one slot where one of
four purpose-linked phrasings was chosen; the "artifact" preserves the phrasing, the purpose is
the hidden label; a bag-of-evidence reader scores candidates by phrasing-purpose association
learned from a disjoint training split (no author leakage by construction).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "event_harness"

PURPOSES = ("clarify", "strengthen-evidence", "reorder-logic", "hedge-claim")
# each purpose expresses through characteristic phrasing families (the recoverable signal),
# plus shared filler (the non-signal); association is probabilistic, not deterministic
MARKERS = {
    "clarify": ["in other words", "that is to say", "to be precise", "specifically"],
    "strengthen-evidence": ["studies show", "the data indicate", "for example", "as measured"],
    "reorder-logic": ["first", "consequently", "it follows that", "before turning to"],
    "hedge-claim": ["may", "in some cases", "arguably", "tends to"],
}
FILLER = ["the argument", "this essay", "the reader", "the topic", "one might note",
          "it is worth", "considering", "overall", "further", "in this section"]
N_MAKERS = 40
EVENTS_PER = 12
SIGNAL_RATE = 0.7   # P(marker actually expresses the chosen purpose) -- noisy, like real text


def main() -> None:
    import argparse                                                   # noqa: PLC0415
    import numpy as np                                                # noqa: PLC0415

    # --scale/--seed exist for the L56 eyebrow settle (unchanged arm 0.282 at 2.6 sigma,
    # inside its band; TODO's cheap-settle row): 5x the makers at fresh seeds, separate
    # output file, the validation record never clobbered. Defaults reproduce the
    # original harness exactly.
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--seed", type=int, default=17)
    args = ap.parse_args()
    global N_MAKERS
    N_MAKERS = N_MAKERS * args.scale
    rng = np.random.default_rng(args.seed)

    def make_event(purpose: str) -> str:
        words = list(rng.choice(FILLER, size=6))
        src = purpose if rng.random() < SIGNAL_RATE else str(rng.choice(PURPOSES))
        words.insert(int(rng.integers(0, len(words))), str(rng.choice(MARKERS[src])))
        return " ".join(words)

    makers = []
    for m in range(N_MAKERS):
        events = []
        for _ in range(EVENTS_PER):
            purpose = str(rng.choice(PURPOSES))
            events.append({"purpose": purpose, "text": make_event(purpose)})
        makers.append(events)

    train, test = makers[: N_MAKERS // 2], makers[N_MAKERS // 2:]   # split BY MAKER

    # the bounded reader: marker-purpose association counts from train only
    assoc: dict[str, dict[str, float]] = {}
    for events in train:
        for e in events:
            for p, ms in MARKERS.items():
                for mk in ms:
                    if mk in e["text"]:
                        assoc.setdefault(mk, {q: 0.0 for q in PURPOSES})
                        assoc[mk][e["purpose"]] += 1

    def score(text: str, candidate: str) -> float:
        s = 0.0
        for mk, counts in assoc.items():
            if mk in text:
                tot = sum(counts.values())
                if tot:
                    s += counts[candidate] / tot
        return s

    def pick(text: str) -> str:
        # ties break RANDOMLY -- a deterministic argmax hands every null-text pick to the first
        # candidate, the strict-ties fault the audit caught once already; the decoy gate below
        # exists to catch exactly this
        scores = {c: score(text, c) for c in PURPOSES}
        best = max(scores.values())
        top = [c for c, v in scores.items() if v >= best - 1e-12]
        return str(rng.choice(top))

    def run_arm(label: str, text_fn, label_fn, repeats: int = 1) -> float:
        # repeats > 1 shrinks binomial noise on arms whose expectation is chance, so the fixed
        # +-0.06 band tests the arm rather than the seed; the band itself is never widened
        hits = tot = 0
        for _ in range(repeats):
            for events in test:
                for e in events:
                    text = text_fn(e)
                    truth = label_fn(e)
                    hits += pick(text) == truth
                    tot += 1
        acc = hits / tot
        print(f"  {label:10s} accuracy {acc:.3f}  (chance 0.25, n={tot})")
        return acc

    print(f"{N_MAKERS} makers x {EVENTS_PER} events, maker-split train/test")
    perm = list(rng.permutation([e["purpose"] for ev in test for e in ev]))
    it = iter(perm)
    acc = {
        "oracle": run_arm("oracle", lambda e: e["text"], lambda e: e["purpose"]),
        "shuffle": run_arm("shuffle", lambda e: e["text"], lambda e: next(it)),
        "unchanged": run_arm("unchanged", lambda e: " ".join(rng.choice(FILLER, size=7)),
                             lambda e: e["purpose"], repeats=5),
        "blind": run_arm("blind", lambda e: "", lambda e: e["purpose"], repeats=5),
    }
    # decoy symmetry: no candidate may be structurally easier to pick. On signal-free passages
    # the reader's choices must spread ~uniformly over the candidate set. (A first version scored
    # a remapped truth instead, which with real signal present MUST land below chance -- that arm
    # re-measured signal upside down and was replaced before any real corpus was scored.)
    picks = {p: 0 for p in PURPOSES}
    n_null = 0
    for _ in range(400):
        text = " ".join(rng.choice(FILLER, size=7))
        picks[pick(text)] += 1
        n_null += 1
    acc["decoy_max_pick"] = max(picks.values()) / n_null
    print(f"  decoy symmetry: null-text pick rates "
          f"{ {k: round(v / n_null, 2) for k, v in picks.items()} }")

    gates = {
        "oracle_above_chance": acc["oracle"] > 0.40,
        "shuffle_at_chance": abs(acc["shuffle"] - 0.25) < 0.06,
        "unchanged_at_chance": abs(acc["unchanged"] - 0.25) < 0.06,
        "blind_at_chance": abs(acc["blind"] - 0.25) < 0.06,
        "decoy_symmetric": acc["decoy_max_pick"] < 0.40,
    }
    verdict = "HARNESS-VALID" if all(gates.values()) else "HARNESS-FAILED"
    print(f"  >>> {verdict}  {gates}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    dest = ("synthetic_validation.json" if (args.scale, args.seed) == (1, 17)
            else f"scale{args.scale}_seed{args.seed}.json")
    (RESULTS / dest).write_text(json.dumps(
        {"accuracies": acc, "gates": gates, "verdict": verdict,
         "n_makers": N_MAKERS, "events_per": EVENTS_PER, "signal_rate": SIGNAL_RATE,
         "seed": args.seed, "scale": args.scale},
        indent=2), encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / dest).relative_to(REPO)}")
    if verdict != "HARNESS-VALID":
        sys.exit(1)


if __name__ == "__main__":
    main()
