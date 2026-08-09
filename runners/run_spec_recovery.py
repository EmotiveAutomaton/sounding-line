"""Spec recovery in BITS — how much of the maker's specification is recoverable from the artifact.

── WHY THIS IS DIFFERENT FROM EVERYTHING THAT HAS DIED ───────────────────────────────────────

Ten measures and a 342-feature sweep have died here, almost all to length, register, topic or prompt
echo. This is the first instrument that is **the project's own question written as a quantity**:

    depth  =  how many of the maker's decisions a reader can recover
             =  I(specification ; artifact | topic)          -- in bits

**The estimator.** For each artifact we know the specifications it was actually generated from. Build
N decoys — same count, same pool, same topic — and ask a reading model to score the artifact against
each. The InfoNCE bound turns "how often does the true specification win, and by how much" into a
number of bits. The optimal critic for this bound is the pointwise mutual information between
specification and text, which is exactly the thing we want to measure.

── WHY THE USUAL KILLERS DO NOT APPLY ────────────────────────────────────────────────────────

    length      every comparison is WITHIN one artifact -- the text is identical across the true
                specification and all decoys, so length cannot move the score
    topic       decoys carry the same topic sentence, so the estimate is CONDITIONAL on topic
    register    same -- the decoys differ only in which situational specifications they name
    echo        echo helps the true specification win, so it must be controlled rather than
                assumed away. `--no-echo` restricts scoring to specifications whose content words
                do not appear in the artifact, which is the honest version
    provenance  irrelevant. Every rung is machine-written; the comparison is within-item

**This is the first measure in the project whose controls are built into the estimator rather than
bolted on afterwards**, which is why it is worth building before anything else on the list.

── TWO STATISTICS, AND THEY ANSWER DIFFERENT QUESTIONS ───────────────────────────────────────

    bits_total     how much specification information the artifact carries.
                   Rises with rung if more specified intent really is more recoverable.
    bits_per_spec  recovery efficiency. May FALL with rung -- more constraints, each less
                   distinctly expressed. A falling curve here with a rising total is the
                   interesting result, not a contradiction.

── PRE-REGISTERED ────────────────────────────────────────────────────────────────────────────

    PASS       bits_total rises with rung, correlation above 0.3 at p < 0.01, AND survives the
               echo restriction
    FAIL       no relationship with rung, or the effect disappears once echoed specifications
               are excluded
    CEILING    accuracy at or near 1.0 everywhere -- the task is too easy and the decoys are
               badly matched

Rung 0 has no specifications and is excluded from the estimate by construction; it is the floor.

Method credit: InfoNCE / contrastive predictive coding (van den Oord et al.), suggested by a
literature scout after ten hand-built measures failed.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

RESULTS = REPO / "results" / "spec_recovery"

LADDERS = {
    "ladder":  {"seed": 70000,  "per_rung": 10, "topic_off": 0, "pool": "base"},
    "ladder2": {"seed": 90000,  "per_rung": 20, "topic_off": 5, "pool": "base"},
    "ladder3": {"seed": 110000, "per_rung": 15, "topic_off": 3, "pool": "extended"},
}
STOP = set("the a an and or of to for with without in on at by is are be as that this it you your "
           "they their who whom what which not no so if then than about into over under more most "
           "less least very can could would should may might will shall do does did done".split())


def content_words(s: str) -> set[str]:
    return {w.strip(".,;:!?").lower() for w in s.split()} - STOP


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="ladder2")
    ap.add_argument("--decoys", type=int, default=8)
    ap.add_argument("--max-words", type=int, default=700, help="score the opening N words")
    ap.add_argument("--no-echo", action="store_true",
                    help="the pre-registered echo restriction: score only specifications whose "
                         "content words are absent from the artifact")
    ap.add_argument("--echo-threshold", type=float, default=None,
                    help="G113 graded restriction: keep specifications whose content-word overlap "
                         "fraction with the artifact is <= this (0.0 == --no-echo, 1.0 == keep all)")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--shuffle-specs", action="store_true",
                    help="CONTROL: give each artifact another artifact's specification. Destroys the "
                         "artifact-specification link and keeps everything else. Win rate must "
                         "collapse to chance, 1/(decoys+1). This is the analogue of the no-maker "
                         "control, which cannot be run here because no-maker text has no "
                         "specification to recover.")
    args = ap.parse_args()

    import torch                                                      # noqa: PLC0415
    from scipy import stats                                           # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer      # noqa: PLC0415

    from runners.make_intent_ladder import SPECS as BASE, TOPICS      # noqa: PLC0415
    from soundingline.probe.activations import DEFAULT_MODEL          # noqa: PLC0415

    cfg = LADDERS[args.corpus]
    if cfg["pool"] == "extended":
        from runners.make_ladder3 import SPECS as POOL, build         # noqa: PLC0415
    else:
        from runners.make_intent_ladder import build                  # noqa: PLC0415
        POOL = BASE

    print(f"loading {DEFAULT_MODEL} ...", flush=True)
    tok = AutoTokenizer.from_pretrained(DEFAULT_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        DEFAULT_MODEL, dtype=torch.float16).to(args.device).eval()

    @torch.no_grad()
    def logprob(prompt: str, text: str) -> float:
        """Mean log-probability of `text` continuing `prompt`. Prompt tokens are not scored."""
        p_ids = tok(prompt, return_tensors="pt").input_ids.to(args.device)
        t_ids = tok(text, return_tensors="pt", truncation=True,
                    max_length=1024).input_ids.to(args.device)
        ids = torch.cat([p_ids, t_ids], dim=1)[:, :2048]
        out = model(ids).logits[:, :-1].float().log_softmax(-1)
        tgt = ids[:, 1:]
        lp = out.gather(-1, tgt.unsqueeze(-1)).squeeze(-1)
        start = p_ids.shape[1] - 1
        return lp[0, start:].mean().item()

    d = REPO / "corpora" / args.corpus
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    rng_global = random.Random(7)

    rows = []
    for it in man["items"]:
        rung = it["rung"]
        if rung == 0:
            continue                       # nothing specified: no bits to recover, by construction
        p = d / f"{it['id']}.txt"
        if not p.exists():
            continue
        idx = int(it["id"].split("_")[1])
        topic = TOPICS[(idx + cfg["topic_off"]) % len(TOPICS)]
        rng = random.Random(cfg["seed"] + rung * 1000 + idx)
        true_specs = rng.sample(POOL, rung)
        text = " ".join(p.read_text(encoding="utf-8").split()[: args.max_words])

        # decoys: same topic, same count, disjoint from the true draw where the pool allows
        others = [s for s in POOL if s not in true_specs]
        decoys = []
        for k in range(args.decoys):
            r2 = random.Random(rng_global.randrange(1 << 30))
            decoys.append(r2.sample(others, min(rung, len(others))))
        # decoy-pool exhaustion (audit L26): when rung >= len(others), every decoy is the same
        # complement set reordered — or empty — and the contest is no longer (decoys+1)-way.
        distinct_sets = len({tuple(sorted(d)) for d in decoys})

        def prompt_for(specs):
            r = random.Random(0)
            _ = r
            return (f"Write about {topic}, " + ", ".join(specs) + "."
                    if cfg["pool"] == "base" else
                    f"Write about {topic}. Every one of the following must be honoured, and they "
                    f"are all simultaneously true of your situation: " + "; ".join(specs) + ".")

        if args.no_echo or args.echo_threshold is not None:
            # The pre-registered echo restriction (strict at 0 overlap) and its graded form (G113):
            # the strict version removes every honoured specification too, since honouring shares
            # words. Thresholds separate echo-carried from echo-inevitable.
            thr = 0.0 if args.no_echo else args.echo_threshold
            tw_early = content_words(text)

            def overlap_frac(s):
                cw = content_words(s)
                return len(cw & tw_early) / max(len(cw), 1)

            keep = [s for s in true_specs if overlap_frac(s) <= thr]
            if rung > 0 and not keep:
                continue
            true_specs = keep
            decoys = [dd[: len(true_specs)] for dd in decoys]   # size-matched prompts
        if args.shuffle_specs:
            true_specs = decoys[0]        # a real specification, but not this artifact's
            decoys = decoys[1:]
        s_true = logprob(prompt_for(true_specs), text)
        s_dec = [logprob(prompt_for(dd), text) for dd in decoys]

        # InfoNCE: softmax over the true score against decoys; bits = log2(N+1) - H
        scores = [s_true] + s_dec
        m = max(scores)
        exps = [math.exp((x - m) * len(text.split())) for x in scores]   # de-normalise per token
        post = exps[0] / sum(exps) if sum(exps) > 0 else 1.0 / len(scores)
        bits = math.log2(len(scores)) + math.log2(max(post, 1e-12))
        bits = max(bits, 0.0)

        # echo: how much of the true specification's content actually appears in the artifact
        tw = content_words(text)
        overlap = (sum(len(content_words(s) & tw) / max(len(content_words(s)), 1)
                       for s in true_specs) / len(true_specs)) if true_specs else 0.0

        # strict >: an exact tie must not count as a win — with degenerate decoys every
        # candidate can be the identical prompt, and >= scored those as 100% wins (audit L26)
        rows.append({"id": it["id"], "rung": rung, "bits": bits,
                     "won": s_true > max(s_dec), "margin": s_true - max(s_dec),
                     "distinct_decoy_sets": distinct_sets,
                     "echo_overlap": overlap, "words": it["n_words"]})
        if len(rows) % 15 == 0:
            print(f"  {len(rows)} scored", flush=True)

    import statistics                                                 # noqa: PLC0415
    rungs = sorted({r["rung"] for r in rows})
    print(f"\n{args.corpus}: {len(rows)} artifacts, {args.decoys} decoys each\n")
    print(f"{'rung':>5}{'bits':>9}{'per spec':>10}{'won':>8}{'echo':>8}")
    for g in rungs:
        v = [r for r in rows if r["rung"] == g]
        print(f"{g:>5}{statistics.fmean(r['bits'] for r in v):>9.3f}"
              f"{statistics.fmean(r['bits'] / r['rung'] for r in v):>10.4f}"
              f"{statistics.fmean(r['won'] for r in v):>8.0%}"
              f"{statistics.fmean(r['echo_overlap'] for r in v):>8.2f}")

    rung = [r["rung"] for r in rows]
    rho_b, p_b = stats.spearmanr(rung, [r["bits"] for r in rows])
    rho_e, _ = stats.spearmanr(rung, [r["echo_overlap"] for r in rows])
    rho_l, _ = stats.spearmanr([r["words"] for r in rows], [r["bits"] for r in rows])
    won = statistics.fmean(r["won"] for r in rows)
    print(f"\n  rung vs bits        {rho_b:+.3f}  p={p_b:.4f}")
    print(f"  rung vs echo        {rho_e:+.3f}   (if high, echo is doing the work)")
    print(f"  length vs bits      {rho_l:+.3f}   (should be ~0 — same text in every comparison)")
    print(f"  true spec wins      {won:.0%}  (chance {1 / (args.decoys + 1):.0%})")

    verdict = ("CEILING" if won > 0.97 else
               "PASS" if rho_b > 0.3 and p_b < 0.01 else
               "FAIL" if abs(rho_b) < 0.15 else "AMBIGUOUS")
    degen = [g for g in rungs if g > 0 and statistics.fmean(
        r["distinct_decoy_sets"] for r in rows if r["rung"] == g) < args.decoys / 2]
    if degen:
        verdict += "-DEGENERATE-RUNGS"
        clean = [r for r in rows if r["rung"] not in degen]
        if len({r["rung"] for r in clean}) >= 2:
            rc, pc = stats.spearmanr([r["rung"] for r in clean], [r["bits"] for r in clean])
            print(f"\n  WARNING: decoy pool exhausted at rungs {degen} — those contests are not "
                  f"{args.decoys + 1}-way (audit L26).")
            print(f"  clean rungs only: rung vs bits {rc:+.3f}  p={pc:.4f}  (n={len(clean)})")
    print(f"\n  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    _suffix = ("_shuffled" if args.shuffle_specs else
               "_noecho" if args.no_echo else
               f"_echo{int(args.echo_threshold * 100)}" if args.echo_threshold is not None else "")
    # non-default decoy counts get their own file — the untagged name is how L16's raw files died
    # (ladder3.json remains the historical 96-decoy record; new runs are always tagged)
    if args.decoys != 48 and not _suffix:
        _suffix = f"_d{args.decoys}"
    (RESULTS / f"{args.corpus}{_suffix}.json").write_text(json.dumps(
        {"corpus": args.corpus, "decoys": args.decoys, "n": len(rows),
         "shuffled_specs": args.shuffle_specs,
         "rho_bits": float(rho_b), "p": float(p_b), "rho_echo": float(rho_e),
         "rho_length": float(rho_l), "win_rate": won, "verdict": verdict,
         "by_rung": {str(g): {"bits": statistics.fmean(r["bits"] for r in rows if r["rung"] == g),
                              "won": statistics.fmean(r["won"] for r in rows if r["rung"] == g)}
                     for g in rungs},
         "rows": rows}, indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {(RESULTS / f'{args.corpus}.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
