"""P02 under the echo rule (TODO (o), 2026-08-30). L304 found the comma format parsing every
reply while two replies in three merely repeated the listing (1, 2, 3, 4), so the card's
support candidate pooled an echo population with a genuine one. Here an echo counts as no
proposal; a second turn shows the reader its echo and asks again; the genuine proposals
(first-turn genuine, or second-turn genuine after an echo) are the measured population,
scored against the blind rate over the twenty-three non-listing orders. Writes
results/phase_2_4_stage_5r/post/P02_ECHO.json; changes nothing landed.

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3 (denominators are declared opportunities, never words: the
  proposal population is declared by the echo rule before the run; blind floors follow
  the truth's label marginal; the two scores cannot alias), §4 (a model adjudicator is a
  ruler: the echo test is a string test, no reader judges it).
expectations: under the null (the genuine proposals are guesses) enactability minus the
  echo-excluded blind rate sits at zero; under the alternative it clears 0.05 on the genuine
  population with historical correspondence among enactable reported apart. The direction
  guarded is a support made of echoes (they are excluded) and a support made of a second
  turn that steers away from one order (the two turns are reported apart, and the second
  turn's blind rate is the same twenty-three-order rate). Band: the P02 threshold 0.05;
  clusters at the drawing, both readers pooled and apart; 240 drawings per reader.
"""
from __future__ import annotations

import itertools
import random
import sys

from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[1]))
from runners import s5_receipts as R                                              # noqa: E402  (sets the environment first)
from runners import s5_lib                                                        # noqa: E402
from runners.s4_run_p import stroke_features                                      # noqa: E402
from runners.s5_run_p import _data, _stroke_desc, parse_order_lenient             # noqa: E402
from soundingline.s4 import now_iso                                                # noqa: E402

SEED = s5_lib.SEED0 + 520
THRESHOLD = 0.05
LISTING = [1, 2, 3, 4]


def is_echo(proposal) -> bool:
    return proposal == LISTING


def blind_rate_excluding_echo(valid_orders: list) -> float:
    """The blind valid rate over the orders a genuine proposal can be: all twenty-four
    permutations less the listing order."""
    return sum(1 for o in valid_orders if o != LISTING) / 23


def second_turn(body: str) -> str:
    return (body + "\nYour previous reply was: 1, 2, 3, 4. That is the listing order, not a proposal. "
            "Propose the order in which the strokes were actually drawn, which may differ from the listing: "
            "reply with the four stroke numbers in order, separated by commas, and nothing else.")


def main() -> int:
    data = _data()
    rng = random.Random(SEED + 2)
    pool = [d for cat in data for d in data[cat] if len(d["strokes"]) >= 4]
    rng.shuffle(pool)
    n = 6 if R.SMOKE else 240
    items = pool[:n]
    out = {"written_at": now_iso(), "design": "2", "n_items": len(items), "rule": "an echo of the listing is no proposal; one second turn", "rows": []}
    with s5_lib.GpuSession("s5_p02_echo") as gs:
        for reader in s5_lib.READERS:
            model, tok, _ = s5_lib.load_model(reader)
            try:
                for i, d in enumerate(items):
                    uid = f"P02|{d['cat']}|{d['key_id']}"
                    F = stroke_features(d["strokes"][:4])
                    shown = list(range(4))
                    rng2 = random.Random(SEED + 3 + i)
                    rng2.shuffle(shown)
                    listing = "\n".join(_stroke_desc(F, i_) for i_ in shown)
                    early = [shown.index(k) + 1 for k in (0, 1)]
                    late = [shown.index(k) + 1 for k in (2, 3)]
                    constraint = f"It is known that strokes {early[0]} and {early[1]} (as listed) were both made before strokes {late[0]} and {late[1]}."
                    body = (f"A {d['cat']} was drawn in four strokes, listed here in NO particular order:\n{listing}\n{constraint}\n"
                            "Propose an order in which it was drawn: reply with the four stroke numbers in order, separated by commas, and nothing else.")
                    g1 = s5_lib.generate(model, tok, body, seed=SEED + 10 + i, max_new=40, greedy=True)
                    p1 = parse_order_lenient(g1["text"])
                    turn, proposal, reply2 = 1, p1, None
                    if is_echo(p1):
                        g2 = s5_lib.generate(model, tok, second_turn(body), seed=SEED + 10 + i, max_new=40, greedy=True)
                        reply2 = g2["text"]
                        p2 = parse_order_lenient(g2["text"])
                        turn, proposal = 2, (None if is_echo(p2) else p2)
                    valid_orders = [list(p) + list(q) for p in itertools.permutations(early) for q in itertools.permutations(late)]
                    true_order = [shown.index(k) + 1 for k in range(4)]
                    genuine = proposal is not None
                    enactable = genuine and proposal in valid_orders
                    historical = genuine and proposal == true_order
                    r = s5_lib.candidate_likelihood(model, tok, body.split("Propose")[0] + "Can the exact order be determined from what is given?",
                                                    {"yes": "yes, it can", "no": "no, more than one order fits"}, rng2, unknown=False)
                    out["rows"].append({"reader": reader, "unit_id": uid, "category": d["cat"], "turn1": g1["text"][:60], "turn1_parsed": p1,
                                        "turn1_echo": is_echo(p1), "turn2": (reply2 or "")[:60], "turn_of_proposal": turn if genuine else None,
                                        "proposal": proposal, "genuine": genuine, "enactable": enactable, "historical": historical,
                                        "blind_excl": blind_rate_excluding_echo(valid_orders), "n_valid_orders": len(valid_orders),
                                        "true_order_is_listing": true_order == LISTING,
                                        "abstained": r["valid"] and r["pred"] == "no", "p_determinable": r["probs"]["yes"] if r["valid"] else None})
            finally:
                s5_lib.free_model(model)
        out["gpu_lock_s"] = gs.held_s

    def analyze(rs: list[dict]) -> dict:
        gen = [r for r in rs if r["genuine"]]
        primary = s5_lib.cluster_bootstrap_ci(s5_lib.per_unit_means([dict(r, primary_score=float(r["enactable"]) - r["blind_excl"]) for r in gen], "unit_id", "primary_score"), SEED + 21)
        by_turn = {}
        for t in (1, 2):
            sub = [r for r in gen if r["turn_of_proposal"] == t]
            en = [r for r in sub if r["enactable"]]
            by_turn[f"turn{t}"] = {"proposals": len(sub), "enactable": (len(en) / len(sub)) if sub else None,
                                   "historical_among_enactable": (sum(1 for r in en if r["historical"]) / len(en)) if en else None,
                                   "blind_excl_mean": (sum(r["blind_excl"] for r in sub) / len(sub)) if sub else None}
        en = [r for r in gen if r["enactable"]]
        return {"n": len(rs), "turn1_echo_rate": sum(1 for r in rs if r["turn1_echo"]) / max(1, len(rs)),
                "turn1_malformed_rate": sum(1 for r in rs if r["turn1_parsed"] is None) / max(1, len(rs)),
                "echo_twice_rate": sum(1 for r in rs if r["turn1_echo"] and not r["genuine"]) / max(1, len(rs)),
                "genuine_rate": len(gen) / max(1, len(rs)), "genuine_enactable": (len(en) / len(gen)) if gen else None,
                "genuine_historical_among_enactable": (sum(1 for r in en if r["historical"]) / len(en)) if en else None,
                "by_turn": by_turn, "abstention_rate": sum(1 for r in rs if r["abstained"]) / max(1, len(rs)),
                "primary_enactability_minus_blind_genuine": primary, "verdict": R.classify(primary, THRESHOLD)}

    out["pooled"] = analyze(out["rows"])
    out["by_reader"] = {rd: analyze([r for r in out["rows"] if r["reader"] == rd]) for rd in s5_lib.READERS}
    out["verdict"] = out["pooled"]["verdict"]
    R.write("P02_ECHO.json", out)
    p = out["pooled"]
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in p.items() if k not in ("by_turn", "primary_enactability_minus_blind_genuine", "verdict")})
    print("primary", p["primary_enactability_minus_blind_genuine"], out["verdict"]["outcome"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
