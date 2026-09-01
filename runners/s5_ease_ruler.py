"""Ease-ruler validation on known-answer renderings (TODO (m), 2026-08-30). L301 found the
mean per-token log probability rating a record written in capitals, or with a mid-dot after
every word, as EASIER than the plain record, because predictable filler tokens raise a mean.
This receipt scores the plain record and its five renderings under four rulers on both
admitted readers and asks each ruler the question whose answer is known: are capitals and
mid-dots harder than plain? A ruler passes when it says so on at least 95 percent of samples
for both readers; the passing ruler and the rendering it rates hardest are handed to the
R02 and R01 re-runs (s5_r02_ease.py, s5_r01_ease.py). Writes
results/phase_2_4_stage_5r/post/EASE_RULER.json; changes nothing landed.

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (validate the ruler on data whose answer you know, before the
  signal; check that the criterion can fail: the mean ruler is kept in the set so the
  validation can show a failure; an instrument gate carries its band's definition), §5
  (produces guard; a tool run takes the GPU lock once).
expectations: under the null (no ruler separates the known-answer renderings from plain)
  every ruler's harder-fraction sits under the band and the ease arm stays unrealized;
  under the alternative at least one ruler rates both capitals and mid-dots harder than
  plain on at least 0.95 of samples for both readers. The direction guarded is adopting a
  ruler because it orders the archaic renderings plausibly while failing the two whose
  answer is certain. The archaic renderings are reported, never gated: their difficulty is
  a belief, not a known answer. Band: 0.95 of samples, both readers, both known renderings.
  Sixty-four samples (32 worlds per domain, six records each).
"""
from __future__ import annotations

import sys

from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[1]))
from runners import s5_receipts as R                                              # noqa: E402  (sets the environment first)
from runners import s5_lib, s5_worlds                                              # noqa: E402
from runners.s5_run_j import evidence_text                                         # noqa: E402
from runners.s5_run_r import RENDERINGS                                            # noqa: E402
from soundingline.s4 import now_iso                                                # noqa: E402

KNOWN = ("stilted4", "stilted5")          # capitals; a mid-dot after every word
BAND = 0.95


def validate(per_reader: dict) -> dict:
    """From {reader: {rendering: {ruler: {harder_fraction, mean_diff}}}} to the verdict:
    which rulers pass on the known-answer renderings, and which rendering the first
    passing ruler rates hardest among those it rates harder than plain on every reader."""
    verdict = {}
    for ru in R.RULER_NAMES:
        fr = [per_reader[rd][k][ru]["harder_fraction"] for rd in per_reader for k in KNOWN]
        verdict[ru] = {"passed": bool(fr) and min(fr) >= BAND, "known_answer_min_fraction": min(fr) if fr else None}
    passing = [ru for ru in R.RULER_NAMES if verdict[ru]["passed"]]
    ruler = passing[0] if passing else None
    chosen = None
    if ruler:
        cands = [k for k in RENDERINGS if all(per_reader[rd][k][ruler]["harder_fraction"] >= BAND for rd in per_reader)]
        if cands:
            chosen = min(cands, key=lambda k: sum(per_reader[rd][k][ruler]["mean_diff"] for rd in per_reader))
    return {"rulers": verdict, "passing": passing, "ruler": ruler, "rendering": chosen, "realized": chosen is not None,
            "band": BAND, "known_answer_renderings": list(KNOWN)}


def main() -> int:
    n = 3 if R.SMOKE else 32
    samples = []
    for dom in s5_worlds.DOMAINS:
        for k in range(n):
            w = s5_worlds.make_joint_world(f"EASE|{dom}|s0|w{k:04d}|ruler", dom)
            samples.append(evidence_text(w, ("contextual", "action"), n_records=6)[0])
    out = {"written_at": now_iso(), "design": "2", "n_samples": len(samples), "renderings": list(RENDERINGS),
           "rulers": list(R.RULER_NAMES), "readers": {}, "token_counts": {}}
    with s5_lib.GpuSession("s5_ease_ruler") as gs:
        for reader in s5_lib.READERS:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                per: dict = {}
                counts: dict = {"plain": []}
                for s in samples:
                    base_pieces = R.text_token_logps(model, tok, "A record:", s)
                    base = R.rulers(base_pieces)
                    counts["plain"].append(len(base_pieces))
                    for name, fn in RENDERINGS.items():
                        pieces = R.text_token_logps(model, tok, "A record:", fn(s))
                        v = R.rulers(pieces)
                        counts.setdefault(name, []).append(len(pieces))
                        for ru in base:
                            per.setdefault(name, {}).setdefault(ru, []).append(v[ru] - base[ru])
                out["readers"][reader] = {name: {ru: {"harder_fraction": sum(1 for x in d if x < 0) / len(d), "mean_diff": sum(d) / len(d)}
                                                 for ru, d in rus.items()} for name, rus in per.items()}
                out["token_counts"][reader] = {k: sum(v) / len(v) for k, v in counts.items()}
            finally:
                s5_lib.free_model(model)
        out["gpu_lock_s"] = gs.held_s
    out["verdict"] = validate(out["readers"])
    R.write("EASE_RULER.json", out)
    for rd, rep in out["readers"].items():
        print(rd)
        for name, rus in rep.items():
            print(f"  {name:9} " + "  ".join(f"{ru}:{d['harder_fraction']:.2f}" for ru, d in rus.items()))
    print("verdict", {k: v for k, v in out["verdict"].items() if k != "rulers"})
    return 0


if __name__ == "__main__":
    sys.exit(main())
