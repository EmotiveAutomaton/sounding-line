"""TODO (l2), opened by L311 (2026-08-30): the R01 ease cross repeated with an ARCHAIC
rendering of the route descriptions, harder by the validated ruler but not visually
deviant (no capitals, no mid-dots, ordinary punctuation). L311 found both readers taking
the mid-dotted description a quarter MORE often than the plain one beside it, killing the
fluency policy; but a mid-dotted text is both harder and anomalous, so that result cannot
say whether difficulty or visual anomaly attracts. This receipt separates them: if the
archaic description is also taken more, difficulty attracts; if it is not, the L311 effect
was visual anomaly. Writes results/phase_2_4_stage_5r/post/R01_ARCHAIC.json; changes
nothing landed.

DESIGN CHECK (2026-09-01)
lessons read: LESSONS §3 (a harder rendering is also an anomalous one, and a menu whose
  options differ in surface form carries an attraction bias: this is the surface-matched
  cell that lesson asks for; validate the ruler on data whose answer you know: the archaic
  rendering is validated as HARDER under the validated ruler on the 64 known-answer samples
  before the cross runs, and the run is VOID if it is not; a gate dependency is the gate's
  verdict: EASE_RULER.json's verdict is read at start; assigned is not realized: the
  per-reader flip of the record/note ease order is checked and written before the
  contrast), §5 (produces guard; GPU lock inside the runner).
expectations: the within-route ease contrast is P(take the record | record archaic, note
  plain) subtracted from P(take the record | record plain, note archaic), the L311 sign
  convention (positive = the plain text taken more, the fluency direction). Under the null
  (neither difficulty nor form matters) it sits inside ±0.03. Under alternative A
  (difficulty attracts, whatever the form) it is at or below −0.03, like the mid-dots'
  −0.25. Under alternative B (fluency) it is at or above +0.03. The direction guarded:
  attributing the mid-dots effect to difficulty when it was visual anomaly, so the null
  here is the informative outcome and is reported as such, never as a failure. Bands
  exhaustive: R.classify at 0.03 on both readers pooled and each apart; the archaic
  validation band is the ruler receipt's 0.95 on both readers; the crossing realization
  check is the L311 rule (record easier than note in at least 0.9 of worlds in the one
  cell and at most 0.1 in the other). 128 worlds per domain per reader.
"""
from __future__ import annotations

import random
import sys

from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[1]))
from runners import s5_receipts as R                                              # noqa: E402  (sets the environment first)
from runners import s5_lib, s5_worlds                                              # noqa: E402
from runners.s5_run_j import evidence_text                                         # noqa: E402
from runners.s5_run_r import ROUTE_DESC                                            # noqa: E402
from runners.s5_r01_ease import CELLS                                              # noqa: E402
from soundingline.s4 import now_iso                                                # noqa: E402

SEED = s5_lib.SEED0 + 475
THRESHOLD = 0.03
BAND = 0.95
OUT = "R01_ARCHAIC.json"


def archaic(text: str) -> str:
    """The same facts in archaic diction: rarer words, ordinary case and punctuation. Works
    on the route descriptions (what R01 renders) and on record text (what the validation
    samples are), so the one function is validated and used."""
    pairs = [("the maker's", "the said maker's"), ("earlier decisions", "decisions made aforetime"),
             ("what it chose", "that which it did choose"), ("what it emphasized", "that which it did lay stress upon"),
             ("finished piece", "piece when finished"), ("record of", "ledger of"), ("note on", "note upon"),
             ("close inspection of the piece", "close inspection of the said piece"),
             ("establishing which step", "whereby it is established which step"),
             ("Faced with", "Being faced withal by"), ("It chose:", "Whereupon it did choose:")]
    for a, b in pairs:
        text = text.replace(a, b)
    return text


def main() -> int:
    ruler_rep = R.read_ruler()
    v = (ruler_rep or {}).get("verdict") or {}
    out = {"written_at": now_iso(), "design": "2", "todo": "l2", "ruler_receipt": ruler_rep.get("written_at") if ruler_rep else None,
           "ruler": v.get("ruler"), "rendering": "archaic"}
    if not v.get("realized"):
        out["verdict"] = {"outcome": "VOID", "reason": "no ease ruler passed the known-answer validation (EASE_RULER.json); the archaic cross has no ruler"}
        R.write(OUT, out)
        print("VOID:", out["verdict"]["reason"])
        return 0
    ruler = v["ruler"]
    n_val = 3 if R.SMOKE else 32
    samples = []
    for dom in s5_worlds.DOMAINS:
        for k in range(n_val):
            w = s5_worlds.make_joint_world(f"EASE|{dom}|s0|w{k:04d}|ruler", dom)
            samples.append(evidence_text(w, ("contextual", "action"), n_records=6)[0])
    n = 3 if R.SMOKE else 128
    rows = []
    out["archaic_validation"] = {}
    out["render_by_reader"] = {}
    with s5_lib.GpuSession("s5_r01_archaic") as gs:
        for reader in s5_lib.READERS:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                ez = lambda body, text: R.rulers(R.text_token_logps(model, tok, body, text))[ruler]      # noqa: E731
                # the known-answer validation: archaic must be HARDER than plain under the
                # validated ruler on the same 64 samples the ruler was validated on
                diffs = [ez("A record:", archaic(s)) - ez("A record:", s) for s in samples]
                harder = sum(1 for d in diffs if d < 0) / len(diffs)
                out["archaic_validation"][reader] = {"harder_fraction": harder, "mean_diff": sum(diffs) / len(diffs), "band": BAND,
                                                     "realized": harder >= BAND, "n_samples": len(samples)}
                print(reader, "archaic harder fraction", round(harder, 3), "realized", harder >= BAND, flush=True)
                if harder < BAND:
                    continue
                e_plain = {r: ez("A source:", ROUTE_DESC[r]) for r in ("action", "semantic")}
                e_hard = {r: ez("A source:", archaic(ROUTE_DESC[r])) for r in ("action", "semantic")}
                margin = min(e_plain["action"] - e_hard["semantic"], e_plain["semantic"] - e_hard["action"])
                out["render_by_reader"][reader] = {"rendering": "archaic", "margin": margin, "realized": margin > 0,
                                                   "ease_plain": e_plain, "ease_hard": e_hard}
                print(reader, "flip margin", round(margin, 2), "realized", margin > 0, flush=True)
                ease_cache = {}
                i = 0
                for domain in s5_worlds.DOMAINS:
                    for k in range(n):
                        i += 1
                        lid = f"R01A|{domain}|s0|w{k:04d}|archaic"
                        w = s5_worlds.make_joint_world(lid, domain)
                        info = s5_worlds.route_information(w)
                        passes = bool(info.get("passes_floor", info["divergence"] >= 0.05))
                        rt = s5_worlds.route_texts(w)
                        kl = {r: info[r]["kl_from_prior"] for r in ROUTE_DESC}
                        rand = sum(kl.values()) / 3
                        body = (f"About a maker and one of its pieces you already know this:\n{rt['contextual']['text']}\n"
                                f"You may consult ONE more source before predicting the maker's next decision. Which would tell you most?")
                        for cell, spec in CELLS.items():
                            desc = {r: (archaic(ROUTE_DESC[r]) if spec.get(r) == "hard" else ROUTE_DESC[r]) for r in ROUTE_DESC}
                            ease = {}
                            for r, text in desc.items():
                                if text not in ease_cache:
                                    ease_cache[text] = ez("A source:", text)
                                ease[r] = ease_cache[text]
                            rng = random.Random(SEED + 1000 * list(CELLS).index(cell) + i)
                            rr = s5_lib.candidate_likelihood(model, tok, body, desc, rng, unknown=False)
                            chosen = rr["pred"] if rr["valid"] else None
                            rows.append({"reader": reader, "unit_id": lid, "domain": domain, "cell": cell, "valid": rr["valid"], "passes_floor": passes,
                                         "chosen": chosen, "p_action": rr["probs"].get("action") if rr["valid"] else None,
                                         "p_semantic": rr["probs"].get("semantic") if rr["valid"] else None,
                                         "kl": kl, "random_info": rand, "best": info["best"], "easiest": max(ease, key=ease.get), "ease": ease,
                                         "chosen_info": (kl[chosen] - rand) if chosen else None,
                                         "easiest_info": kl[max(ease, key=ease.get)] - rand, "divergence": info["divergence"]})
            finally:
                s5_lib.free_model(model)
        out["gpu_lock_s"] = gs.held_s

    def analyze(rs: list[dict]) -> dict:
        rs = [r for r in rs if r["valid"]]
        sel = lambda rows_, **k: [r for r in rows_ if all(r[a] == b for a, b in k.items())]   # noqa: E731
        pair = {cell: sum(1 for x in sel(rs, cell=cell) if x["ease"]["action"] > x["ease"]["semantic"]) / max(1, len(sel(rs, cell=cell))) for cell in CELLS}
        realized = pair["record_plain_note_hard"] >= 0.9 and pair["record_hard_note_plain"] <= 0.1
        a = [dict(r, primary_score=r["p_action"]) for r in sel(rs, cell="record_plain_note_hard")]
        b = [dict(r, primary_score=r["p_action"]) for r in sel(rs, cell="record_hard_note_plain")]
        ease_record = s5_lib.paired_contrast(a, b, "unit_id", "primary_score", SEED + 13)
        a2 = [dict(r, primary_score=r["p_semantic"]) for r in sel(rs, cell="record_hard_note_plain")]
        b2 = [dict(r, primary_score=r["p_semantic"]) for r in sel(rs, cell="record_plain_note_hard")]
        ease_note = s5_lib.paired_contrast(a2, b2, "unit_id", "primary_score", SEED + 14)
        choose = {cell: {r: sum(1 for x in sel(rs, cell=cell) if x["chosen"] == r) / max(1, len(sel(rs, cell=cell))) for r in ROUTE_DESC} for cell in CELLS}
        verdict = R.classify(ease_record, THRESHOLD)
        if not realized:
            verdict = {"outcome": "INSTRUMENT_FAILED", "reason": f"the crossing is unrealized under the ruler (record easier than note by cell: {pair})",
                       **{k: verdict.get(k) for k in ("point", "ci", "n_units")}}
        else:
            verdict["reading"] = ("difficulty attracts (the archaic text taken MORE, like the mid-dots)" if verdict["outcome"] == "COUNTEREVIDENCE"
                                  else "fluency (the plain text taken more)" if verdict["outcome"] == "SUPPORT_CANDIDATE"
                                  else "neither: the L311 mid-dot effect was visual anomaly, not difficulty")
        return {"crossing_realized": realized, "record_easier_than_note_by_cell": pair, "choice_rate_by_cell": choose,
                "ease_effect_record_p_choose": ease_record, "ease_effect_record_band": R.classify(ease_record, THRESHOLD),
                "ease_effect_note_p_choose": ease_note, "ease_effect_note_band": R.classify(ease_note, THRESHOLD), "verdict": verdict}

    realized_readers = [rd for rd, x in out["render_by_reader"].items() if x["realized"]]
    out["realized_readers"] = realized_readers
    out["pooled"] = analyze([r for r in rows if r["reader"] in realized_readers]) if realized_readers else None
    out["by_reader"] = {rd: analyze([r for r in rows if r["reader"] == rd]) for rd in realized_readers}
    if not any(x["realized"] for x in out["archaic_validation"].values()):
        out["verdict"] = {"outcome": "VOID", "reason": "the archaic rendering is not harder than plain under the validated ruler on either reader; the premise of (l2) is unrealized"}
    elif out["pooled"]:
        out["verdict"] = out["pooled"]["verdict"]
    else:
        out["verdict"] = {"outcome": "INSTRUMENT_FAILED", "reason": "the archaic rendering never flips the record/note ease order on a reader it is harder for"}
    out["verdict"]["realized_readers"] = realized_readers
    out["rows"] = rows
    R.write(OUT, out)
    print("realized readers", realized_readers, "verdict", out["verdict"].get("outcome"), out["verdict"].get("reading") or out["verdict"].get("reason"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
