"""G117 — the no-maker control that specification recovery never had.

The LAYERS afterword has said it plainly for a day: *"L10 has not yet been given the no-maker
control that made L12 credible."* And after the echo restriction fired (L19), the question is
sharper: does the logprob contest read *specifications*, or does it hand wins to whatever scores
well against maker-less text too?

── THE TEST ──────────────────────────────────────────────────────────────────────────────────

Every no-maker artifact gets a randomly assigned pseudo-true specification set (rung 2, 6 or 10,
cycled) plus 96 disjoint decoys — exactly a ladder item's contest, except **no candidate is true**:
the text has no maker and honoured nothing.

    CLEAN         win rate within 3x of the 1/97 chance rate and mean bits near zero
    READS-STYLE   wins far above chance on maker-less text — the contest scores something
                  other than executed specifications, and every L10/L19 number inherits it
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
PSEUDO_RUNGS = (2, 6, 10)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--decoys", type=int, default=96)
    ap.add_argument("--max-words", type=int, default=700)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    import torch                                                      # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer      # noqa: PLC0415

    from runners.make_intent_ladder import SPECS as POOL              # noqa: PLC0415
    from soundingline.probe.activations import DEFAULT_MODEL          # noqa: PLC0415

    print(f"loading {DEFAULT_MODEL} ...", flush=True)
    tok = AutoTokenizer.from_pretrained(DEFAULT_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        DEFAULT_MODEL, dtype=torch.float16).to(args.device).eval()

    @torch.no_grad()
    def logprob(prompt: str, text: str) -> float:
        p_ids = tok(prompt + "\n\n", return_tensors="pt").input_ids
        t_ids = tok(text, return_tensors="pt").input_ids
        ids = torch.cat([p_ids, t_ids], dim=1)[:, -4096:].to(args.device)
        n_text = min(t_ids.shape[1], ids.shape[1] - 1)
        out = model(ids).logits[0, :-1].log_softmax(-1)
        tgt = ids[0, 1:]
        lp = out.gather(-1, tgt.unsqueeze(-1)).squeeze(-1)
        return float(lp[-n_text:].mean())

    man = json.loads((REPO / "corpora" / "nomaker" / "manifest.json").read_text(encoding="utf-8"))
    rng_global = random.Random(20260808)
    rows = []
    for i, it in enumerate(man["items"]):
        p = REPO / "corpora" / "nomaker" / f"{it['id']}.txt"
        if not p.exists():
            continue
        text = " ".join(p.read_text(encoding="utf-8").split()[: args.max_words])
        rung = PSEUDO_RUNGS[i % len(PSEUDO_RUNGS)]
        pool = list(POOL)
        pseudo_true = rng_global.sample(pool, rung)
        others = [s for s in pool if s not in pseudo_true]
        decoys = [random.Random(rng_global.randrange(1 << 30)).sample(others, rung)
                  for _ in range(args.decoys)]

        def prompt_for(specs):
            return f"Write about the topic at hand, {', '.join(specs)}."

        s_true = logprob(prompt_for(pseudo_true), text)
        s_dec = [logprob(prompt_for(dd), text) for dd in decoys]
        scores = [s_true] + s_dec
        m = max(scores)
        exps = [math.exp((x - m) * len(text.split())) for x in scores]
        post = exps[0] / sum(exps) if sum(exps) > 0 else 1.0 / len(scores)
        bits = max(math.log2(len(scores)) + math.log2(max(post, 1e-12)), 0.0)
        rows.append({"id": it["id"], "pseudo_rung": rung, "bits": bits,
                     "won": s_true > max(s_dec)})
        if len(rows) % 10 == 0:
            print(f"  {len(rows)} scored", flush=True)

    import statistics                                                 # noqa: PLC0415
    won = statistics.fmean(r["won"] for r in rows)
    bits = statistics.fmean(r["bits"] for r in rows)
    chance = 1.0 / (args.decoys + 1)
    print(f"\nnomaker: {len(rows)} artifacts, {args.decoys} decoys each")
    print(f"  pseudo-true wins   {won:.1%}   (chance {chance:.1%})")
    print(f"  mean bits          {bits:.3f}  (a true-less contest should sit near zero)")
    verdict = "CLEAN" if won <= 3 * chance else "READS-STYLE"
    print(f"\n  >>> {verdict}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "nomaker_control.json").write_text(json.dumps(
        {"n": len(rows), "decoys": args.decoys, "win_rate": won, "chance": chance,
         "mean_bits": bits, "verdict": verdict, "rows": rows}, indent=2),
        encoding="utf-8", newline="\n")
    print(f"wrote {(RESULTS / 'nomaker_control.json').relative_to(REPO)}")


if __name__ == "__main__":
    main()
