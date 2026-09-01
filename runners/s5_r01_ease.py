"""R01 with ease crossed WITHIN a route type (TODO (l), 2026-08-30). L270 and L300 could not
separate reading information from reading genre: under every rendering tried, the same
route's description was the most fluent in every world (the note under design 2), so the
"easiest route" selector was a constant. Here each world is asked three times: both the
action record's and the note's descriptions plain; the record's description in the hard
rendering with the note plain; the note's in the hard rendering with the record plain. The
rendering and the ease ruler come from EASE_RULER.json (s5_ease_ruler.py). The within-route
contrast is the probability of choosing the record when its description is plain and the
note's hard, minus when its own is hard and the note's plain, paired at the world: a
fluency policy moves it, an information policy does not. Writes
results/phase_2_4_stage_5r/post/R01_EASE.json; VOID if no ruler passed; changes nothing
landed.

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (the C03 lesson: a model-choice card is void under the divergence
  floor; fluency is not accuracy, so ease and information are crossed by construction;
  a manipulation check needs dynamic range: the crossing is verified per world under the
  ruler before the contrast; a gate dependency is the gate's verdict), §5.
expectations: primary as R01 (the chosen route's exact information minus a random
  selector's, both-plain cell, worlds past the floor; band 0.03). The within-route ease
  contrast under the null (information read, not ease) sits inside the 0.03 band on the
  probability scale; under the alternative (a fluency policy) it clears it. The
  manipulation is realized when, under the ruler, the record's description is easier than
  the note's in at least 0.9 of worlds in the record-plain cell and harder in at least 0.9
  in the note-plain cell (the forensic description, plain in every cell, is a third menu
  item and may be the easiest of the three; the three-way easiest is the fluency selector).
  A description's ease is a per-reader constant, so the rendering is chosen per reader
  among the validated ones by the margin with which it flips the pair; a reader with no
  flipping rendering is unrealized and excluded from the pooled contrast, named as such. The direction guarded is a "reads information" claim from a selector
  that never varied. Clusters at the world, both readers pooled and apart; 128 worlds per
  domain per reader.
"""
from __future__ import annotations

import random
import sys

from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[1]))
from runners import s5_receipts as R                                              # noqa: E402  (sets the environment first)
from runners import s5_lib, s5_worlds                                              # noqa: E402
from runners.s5_run_r import RENDERINGS, ROUTE_DESC                                # noqa: E402
from soundingline.s4 import now_iso                                                # noqa: E402

SEED = s5_lib.SEED0 + 470
THRESHOLD = 0.03
CELLS = {"both_plain": {"action": "plain", "semantic": "plain"},
         "record_plain_note_hard": {"action": "plain", "semantic": "hard"},
         "record_hard_note_plain": {"action": "hard", "semantic": "plain"}}


def main() -> int:
    ruler_rep = R.read_ruler()
    v = (ruler_rep or {}).get("verdict") or {}
    out = {"written_at": now_iso(), "design": "2", "ruler_receipt": ruler_rep.get("written_at") if ruler_rep else None,
           "ruler": v.get("ruler"), "rendering": v.get("rendering")}
    if not v.get("realized"):
        out["verdict"] = {"outcome": "VOID", "reason": "no ease ruler passed the known-answer validation (EASE_RULER.json); ease cannot be crossed within a route"}
        R.write("R01_EASE.json", out)
        print("VOID:", out["verdict"]["reason"])
        return 0
    ruler, band = v["ruler"], v.get("band", 0.95)
    # the renderings the validated ruler rates harder than plain on every reader
    cand_names = [k for k in RENDERINGS if all(((ruler_rep["readers"][rd].get(k) or {}).get(ruler) or {}).get("harder_fraction", 0) >= band
                                               for rd in ruler_rep["readers"])] or [v["rendering"]]
    out["candidate_renderings"] = cand_names
    out["render_by_reader"] = {}
    n = 3 if R.SMOKE else 128
    rows = []
    with s5_lib.GpuSession("s5_r01_ease") as gs:
        for reader in s5_lib.READERS:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                ease_cache = {}
                # a description's ease is a per-reader constant (the texts do not vary by world),
                # so the rendering is chosen per reader: the validated one with the largest margin
                # by which it flips the record/note order in both crossed cells
                ez = lambda text: R.rulers(R.text_token_logps(model, tok, "A source:", text))[ruler]     # noqa: E731
                e_plain = {r: ez(ROUTE_DESC[r]) for r in ("action", "semantic")}
                best = None
                for k in cand_names:
                    e_hard = {r: ez(RENDERINGS[k](ROUTE_DESC[r])) for r in ("action", "semantic")}
                    margin = min(e_plain["action"] - e_hard["semantic"], e_plain["semantic"] - e_hard["action"])
                    if best is None or margin > best[1]:
                        best = (k, margin, e_hard)
                render_name, margin, e_hard = best
                render_fn = RENDERINGS[render_name]
                out["render_by_reader"][reader] = {"rendering": render_name, "margin": margin, "realized": margin > 0,
                                                   "ease_plain": e_plain, "ease_hard": e_hard}
                print(reader, "rendering", render_name, "margin", round(margin, 2), "realized", margin > 0, flush=True)
                i = 0
                for domain in s5_worlds.DOMAINS:
                    for k in range(n):
                        i += 1
                        lid = f"R01E|{domain}|s0|w{k:04d}|ease"
                        w = s5_worlds.make_joint_world(lid, domain)
                        info = s5_worlds.route_information(w)
                        passes = bool(info.get("passes_floor", info["divergence"] >= 0.05))
                        rt = s5_worlds.route_texts(w)
                        kl = {r: info[r]["kl_from_prior"] for r in ROUTE_DESC}
                        rand = sum(kl.values()) / 3
                        body = (f"About a maker and one of its pieces you already know this:\n{rt['contextual']['text']}\n"
                                f"You may consult ONE more source before predicting the maker's next decision. Which would tell you most?")
                        for cell, spec in CELLS.items():
                            desc = {r: (render_fn(ROUTE_DESC[r]) if spec.get(r) == "hard" else ROUTE_DESC[r]) for r in ROUTE_DESC}
                            ease = {}
                            for r, text in desc.items():
                                if text not in ease_cache:
                                    ease_cache[text] = R.rulers(R.text_token_logps(model, tok, "A source:", text))[ruler]
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
        floor = [r for r in rs if r["passes_floor"] and r["chosen_info"] is not None]
        sel = lambda rows_, **k: [r for r in rows_ if all(r[a] == b for a, b in k.items())]   # noqa: E731
        bp = sel(floor, cell="both_plain")
        primary = s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means([dict(r, primary_score=r["chosen_info"]) for r in bp], "unit_id", "primary_score"), SEED + 11)
        easiest = {cell: s5_lib.paired_contrast([dict(r, primary_score=r["chosen_info"]) for r in sel(floor, cell=cell)],
                                                [dict(r, primary_score=r["easiest_info"]) for r in sel(floor, cell=cell)], "unit_id", "primary_score", SEED + 12)
                   for cell in CELLS}
        # the manipulation: the crossed pair's ease order per cell (the forensic description is
        # a third menu item, plain in every cell, and may be the easiest of the three; the
        # three-way easiest is the fluency selector, the pair is the manipulation check)
        share = {cell: {r: sum(1 for x in sel(rs, cell=cell) if x["easiest"] == r) / max(1, len(sel(rs, cell=cell))) for r in ROUTE_DESC} for cell in CELLS}
        pair = {cell: sum(1 for x in sel(rs, cell=cell) if x["ease"]["action"] > x["ease"]["semantic"]) / max(1, len(sel(rs, cell=cell))) for cell in CELLS}
        realized = pair["record_plain_note_hard"] >= 0.9 and pair["record_hard_note_plain"] <= 0.1
        # the within-route ease contrast, paired at the world
        a = [dict(r, primary_score=r["p_action"]) for r in sel(rs, cell="record_plain_note_hard")]
        b = [dict(r, primary_score=r["p_action"]) for r in sel(rs, cell="record_hard_note_plain")]
        ease_record = s5_lib.paired_contrast(a, b, "unit_id", "primary_score", SEED + 13)
        a2 = [dict(r, primary_score=r["p_semantic"]) for r in sel(rs, cell="record_hard_note_plain")]
        b2 = [dict(r, primary_score=r["p_semantic"]) for r in sel(rs, cell="record_plain_note_hard")]
        ease_note = s5_lib.paired_contrast(a2, b2, "unit_id", "primary_score", SEED + 14)
        choose = {cell: {r: sum(1 for x in sel(rs, cell=cell) if x["chosen"] == r) / max(1, len(sel(rs, cell=cell))) for r in ROUTE_DESC} for cell in CELLS}
        tracking = {cell: {"chose_best": sum(1 for x in sel(floor, cell=cell) if x["chosen"] == x["best"]) / max(1, len(sel(floor, cell=cell)))} for cell in CELLS}
        verdict = R.classify(primary, THRESHOLD)
        if not realized:
            verdict = {"outcome": "INSTRUMENT_FAILED", "reason": f"the crossing is unrealized under the ruler (record easier than note by cell: {pair})", **{k: verdict.get(k) for k in ("point", "ci", "n_units")}}
        verdict["worlds_void_under_floor"] = sum(1 for r in sel(rs, cell="both_plain") if not r["passes_floor"])
        return {"crossing_realized": realized, "record_easier_than_note_by_cell": pair, "easiest_share_by_cell": share, "primary_chosen_minus_random_nats": primary,
                "reader_minus_easiest_by_cell": easiest, "choice_rate_by_cell": choose, "chose_best_rate_by_cell": tracking,
                "ease_effect_record_p_choose": ease_record, "ease_effect_record_band": R.classify(ease_record, THRESHOLD),
                "ease_effect_note_p_choose": ease_note, "ease_effect_note_band": R.classify(ease_note, THRESHOLD), "verdict": verdict}

    realized_readers = [rd for rd, x in out["render_by_reader"].items() if x["realized"]]
    out["realized_readers"] = realized_readers
    out["pooled"] = analyze([r for r in rows if r["reader"] in realized_readers]) if realized_readers else None
    out["by_reader"] = {rd: analyze([r for r in rows if r["reader"] == rd]) for rd in s5_lib.READERS}
    out["verdict"] = out["pooled"]["verdict"] if out["pooled"] else {"outcome": "INSTRUMENT_FAILED", "reason": "no reader's record/note ease order flips under any validated rendering"}
    out["verdict"]["realized_readers"] = realized_readers
    out["rows"] = rows
    R.write("R01_EASE.json", out)
    p = out["pooled"] or out["by_reader"][s5_lib.READERS[0]]
    print("realized readers", realized_readers, "primary", p["primary_chosen_minus_random_nats"].get("point"),
          "ease record", p["ease_effect_record_p_choose"].get("point"), "ease note", p["ease_effect_note_p_choose"].get("point"), out["verdict"]["outcome"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
