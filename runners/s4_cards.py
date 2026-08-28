"""Stage 4 card registry: the factorial, floors, primary estimand, threshold,
dependencies, and per-unit compute estimate of every card, in one place (brief §7,
§8.1). The freeze step expands EXPECTED_CELLS.json from here; the scheduler charges
budget from here; no runner carries its own copy of a floor.

Estimates are seconds of GPU-lock time per independent unit at the pilot's measured
throughput multipliers (filled by I03 from the discarded pilot); the numbers here are
the design's own guesses, replaced at freeze time and never quoted as measurements.
"""

from __future__ import annotations

DOMAINS = ("workshop", "civic")
SEEDS = (0, 1, 2)

CARDS: dict[str, dict] = {
    "I01": {"track": "integrity", "gpu": False, "unit": "audit", "n_units": 1,
            "domains": [], "factors": {}, "controls": [], "depends_on": [],
            "primary": "audit dispositions verified", "threshold": None,
            "est_s_per_unit": 300, "cpu": True},
    "I02": {"track": "integrity", "gpu": True, "unit": "reader", "n_units": 1,
            "domains": [], "factors": {},          # verdict-only card: no case rows
            "controls": ["position_swap", "paraphrase"], "depends_on": ["I03pilot"],
            "primary": "reader gate (validity 0.95, accuracy 0.75, per-option 0.5, swing 10pp)",
            "threshold": None, "est_s_per_unit": 900},
    "I03pilot": {"track": "integrity", "gpu": True, "unit": "pilot", "n_units": 1,
                 "domains": [], "factors": {}, "controls": [], "depends_on": [],
                 "primary": "throughput and validity only (discarded)", "threshold": None,
                 "est_s_per_unit": 600},
    "I03": {"track": "integrity", "gpu": True, "unit": "freeze", "n_units": 1,
            "domains": [], "factors": {}, "controls": [], "depends_on": ["I02"],
            "primary": "frozen contract, expected cells, lineages", "threshold": None,
            "est_s_per_unit": 60},   # no GPU work, but it runs in the serial slot so the
                                     # discovery cards' dependency on it resolves
    "C01": {"track": "context", "gpu": True, "unit": "world",
            "domains": list(DOMAINS),
            "factors": {"condition": ["none", "bundle", "facts", "incorrect_bundle",
                                      "irrelevant"],
                        "question": ["choice", "step", "unrelated"]},
            "controls": ["context_mismatched_targets"], "depends_on": ["I03"],
            "primary": "bundle minus facts, future-choice log score", "threshold": 0.03,
            "est_s_per_unit": 6.0},
    "C02": {"track": "context", "gpu": True, "unit": "world",
            "domains": list(DOMAINS),
            "factors": {"prior": ["valid", "misleading", "uninformative"],
                        "records": [0, 2, 6],
                        "route": ["direct", "self_init", "summary"]},
            "controls": ["constraint_change"], "depends_on": ["I03"],
            "primary": "misleading-prior correction, records 6 minus 0, log score",
            "threshold": 0.03, "est_s_per_unit": 30.0},
    "C03": {"track": "context", "gpu": True, "unit": "world",
            "domains": list(DOMAINS),
            "factors": {"rotation": [0, 1, 2]},
            "controls": ["random_selector", "first_listed", "exact_selector"],
            "depends_on": ["I03"],
            "primary": "fraction of the oracle's exact gain captured by the reader's selection, minus the random selector's third",
            "threshold": 0.05, "est_s_per_unit": 3.0},
    "A01": {"track": "appraisal", "gpu": True, "unit": "world",
            "domains": list(DOMAINS),
            "factors": {"source": ["ruler", "enacted"],
                        "question": ["action", "valuation", "audience", "fact"]},
            "controls": ["withheld_context"], "depends_on": ["I03"],
            "primary": "crossed valuation and audience-aim balanced accuracy over 0.25",
            "threshold": 0.05, "est_s_per_unit": 10.0},
    "A02": {"track": "appraisal", "gpu": True, "unit": "world",
            "domains": list(DOMAINS),
            "factors": {"intervention": ["pos", "neg", "random", "shuffled"],
                        "dose": ["low", "high"], "evidence": ["low", "high"]},
            "controls": ["zero_baseline", "own_choice_no_target"], "depends_on": ["A01"],
            "primary": "valuation x intervention interaction in target log score",
            "threshold": 0.03, "est_s_per_unit": 12.0},
    "A03": {"track": "appraisal", "gpu": True, "unit": "world",
            "domains": list(DOMAINS),
            "factors": {"phase": ["context", "answer", "neutral"], "sign": ["pos", "neg"]},
            "controls": [], "depends_on": ["A02"],
            "primary": "context-phase minus answer-phase target log score", "threshold": 0.03,
            "est_s_per_unit": 3.0},
    "T01": {"track": "transmission", "gpu": True, "unit": "world",
            "domains": list(DOMAINS),
            "factors": {"truth": ["true", "false"], "intent": ["benefit", "induce"],
                        "support": ["bare", "supported"]},
            "controls": [], "depends_on": ["I03"],
            "primary": "support effect on novel-case application, aligned and misaligned",
            "threshold": 0.05, "est_s_per_unit": 40.0},
    "T02": {"track": "transmission", "gpu": True, "unit": "world",
            "domains": list(DOMAINS),
            "factors": {"rule": ["representative", "benefit", "induce"],
                        "visible": ["yes", "no"],
                        "route": ["direct", "caution", "summary2", "reconstruct2"]},
            "controls": ["oracle_intention"], "depends_on": ["T01"],
            "primary": "reconstruct2 minus summary2 judgment log score, uptake preserved",
            "threshold": 0.03, "est_s_per_unit": 36.0},
    "T03": {"track": "transmission", "gpu": True, "unit": "world",
            "domains": list(DOMAINS),
            "factors": {"lesson": ["technique", "control"],
                        "claim_truth": ["true", "false"],
                        "rec_value": ["helpful", "harmful"],
                        "register": ["emotional", "dry"]},
            "controls": ["held_out_family"], "depends_on": ["T01"],
            "primary": "technique minus control AUROC on held-out family, true-advice loss <= 3pp",
            "threshold": 0.05, "est_s_per_unit": 10.0},
    "H01": {"track": "hierarchy", "gpu": True, "unit": "chain",
            "domains": list(DOMAINS),
            "factors": {"convention": ["shared", "remapped"],
                        "construction": ["director", "brief"]},   # hops 1 and 3 are
            "controls": ["constraint_flip"], "depends_on": ["I03"],    # measured within a chain
            "primary": "constraint retention at hop 3 minus hop 1, shared vs remapped",
            "threshold": 0.05, "est_s_per_unit": 60.0},
    "H02": {"track": "hierarchy", "gpu": True, "unit": "history",
            "domains": list(DOMAINS),
            "factors": {"history": ["stable", "gradual", "abrupt", "marker_removed",
                                    "fresh_final"],
                        "access": ["artifact_only", "ordered_history"]},
            "controls": ["exact_collision"], "depends_on": ["I03"],
            "primary": "history-type recovery with history minus artifact-only, balanced accuracy",
            "threshold": 0.05, "est_s_per_unit": 5.0},
    "H03": {"track": "hierarchy", "gpu": False, "unit": "project", "n_units": 5,
            "domains": [], "factors": {},          # per-project metrics are the product
            "controls": ["majority", "markov", "duration"], "depends_on": [],
            "primary": "prospective next-event score beyond duration and persistence",
            "threshold": 0.05, "est_s_per_unit": 600, "cpu": True},
    "P01": {"track": "physical", "gpu": False, "unit": "drawing", "n_units": 500,
            "domains": ["house", "tree", "bicycle", "cat"], "factors": {"input": ["raster"]},
            "controls": ["category_prior", "ink_prior", "geometry_prior", "rotation"],
            "depends_on": [], "primary": "first-stroke quadrant accuracy beyond cheap priors",
            "threshold": 0.05, "est_s_per_unit": 0.5, "cpu": True},
    "P02": {"track": "physical", "gpu": False, "unit": "drawing", "n_units": 500,
            "domains": ["all"],                   # stroke sets pool the four categories
            "factors": {"access": ["unordered_strokes", "prefix"]},
            "controls": ["geometry_heuristic", "exact_collision"], "depends_on": ["P01"],
            "primary": "learned ordering prior minus geometry heuristic at each access level",
            "threshold": 0.05, "est_s_per_unit": 0.5, "cpu": True},
    "F01": {"track": "confirmation", "gpu": True, "unit": "world",
            "domains": [], "factors": {},          # its products are the confirmation dirs
            "controls": ["severe_rival", "negative_control"], "depends_on": [],
            "primary": "untouched estimate of up to two frozen claims", "threshold": None,
            "est_s_per_unit": 20.0},
}

# GPU-work preservation order under PARTIAL_BUDGET (brief §5.2) and the CPU cards the
# scheduler runs beside the serial GPU slot; ONE home, here (the loop smoke's first
# second found the scheduler reading both from this module while they lived only in
# the schema module)
PRESERVATION_ORDER = ["I01", "I02", "I03", "C01", "C02", "A01", "A02", "T01", "T02",
                      "F01", "C03", "A03", "T03", "H01", "H02"]
CPU_CARDS = tuple(c for c, v in CARDS.items() if v.get("cpu"))

# discovery floors by unit type at the two tiers (brief §6.2)
TIERS = {"minimum": {"world": 64, "chain": 48, "history": 48},
         "expanded": {"world": 128, "chain": 96, "history": 96}}
CONFIRMATION_UNITS = {"world": 128, "chain": 64, "history": 64}
# theory-bridge ordering for F01 candidate selection (brief §8.1)
BRIDGE_ORDER = ["A02", "C02", "T02", "T03", "H01", "H02", "P01", "P02", "C01", "A01",
                "T01", "C03", "A03"]


def units_for(card: str, tier: str) -> int:
    c = CARDS[card]
    if "n_units" in c:
        return c["n_units"]
    return TIERS[tier][c["unit"]]


def expected_spec(tier: str) -> dict:
    """The EXPECTED_CELLS spec at a tier, in the shape soundingline.s4.expand_expected_cells
    consumes."""
    spec = {}
    for card, c in CARDS.items():
        if not c["domains"] and not c["factors"]:
            continue
        spec[card] = {"factors": dict(c["factors"]), "domains": list(c["domains"]) or ["all"],
                      "n_units": units_for(card, tier), "controls": list(c["controls"])}
    return spec


def gpu_estimate_hours(tier: str, multiplier: float = 1.0, cards=None,
                       units_override: int | None = None) -> dict:
    """units_override replaces the tier's per-domain unit count for the world/chain/history
    cards (the scratch-root smoke runs three units per cell and must be estimated as
    such, or a compressed window defers half the inventory)."""
    out = {}
    for card, c in CARDS.items():
        if cards is not None and card not in cards:
            continue
        if not c["gpu"]:
            continue
        per_dom = (units_override if (units_override is not None and "n_units" not in c)
                   else units_for(card, tier))
        n = per_dom * max(1, len(c["domains"]))
        out[card] = round(n * c["est_s_per_unit"] * multiplier / 3600, 2)
    out["total"] = round(sum(out.values()), 2)
    return out
