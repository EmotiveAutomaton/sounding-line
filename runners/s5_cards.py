"""Stage 5 card registry (brief §6): the twenty-nine mandatory cards with their tracks,
units, factors, controls, dependencies, primaries, thresholds, and per-unit time
assumptions; the preservation order the scheduler runs; the confirmation selection order
(§7.4); the tiers and the GPU estimate. ONE home for all of it.

DESIGN CHECK (2026-08-29)
lessons read: LESSONS §3, §5 (a library carries no gate of its own).
gates: none in the card registry; every gate and its expectation under the null and the alternative,
  with the failure direction it guards, lives in the card runner that uses it.
bands: none here; the card runners' verdict bands are exhaustive (no silent interval) and
  are stated there.
"""

from __future__ import annotations

from soundingline.stage5 import ALLOCATION_HOURS, TRACK_OF

DOMAINS = ("workshop", "civic")
SOURCE_DOMAINS = ("notice", "memo")
SEEDS = (0, 1, 2)
CONFIRMATION_SEEDS = (10, 11, 12)
TRANSFER_SEEDS = (20, 21, 22)

CARDS: dict[str, dict] = {
    # ── I: integrity and calibration ────────────────────────────────────────────────
    "I01": {"gpu": False, "unit": "receipt", "n_units": 1, "domains": [], "factors": {}, "controls": [],
            "depends_on": [], "primary": "Stage-4 anchors and L255 rows regenerated from committed inputs, hash receipt",
            "threshold": None, "est_s_per_unit": 60.0},
    "I02": {"gpu": True, "unit": "reader", "n_units": 1, "domains": [], "factors": {}, "controls": [],
            "depends_on": [], "primary": "structured parser fixtures and reader gate (validity, accuracy, invariance)",
            "threshold": None, "est_s_per_unit": 600.0},
    "I03": {"gpu": False, "unit": "audit", "n_units": 1, "domains": [], "factors": {}, "controls": [],
            "depends_on": ["I02"], "primary": "factor liveness, surface matching, leakage baselines, collision registry, lineage audit",
            "threshold": None, "est_s_per_unit": 120.0},
    "I04": {"gpu": False, "unit": "audit", "n_units": 1, "domains": [], "factors": {}, "controls": [],
            "depends_on": ["I03"], "primary": "route information matrix and regime confusion floor; dead contrasts void",
            "threshold": None, "est_s_per_unit": 120.0},
    # ── B: the owed causal bridge ───────────────────────────────────────────────────
    "B01": {"gpu": True, "unit": "artifact", "n_units": 135, "domains": ["scenes"], "factors": {"checkpoint": ["qwen3b", "smollm"], "steer": ["zero", "congruent", "incongruent", "random"]},
            "controls": ["incongruent", "random", "decode"], "depends_on": ["I02"],
            "primary": "congruent minus zero held-out-maker log score at a second checkpoint, random and incongruent quiet",
            "threshold": 0.03, "est_s_per_unit": 6.0},
    "B02": {"gpu": True, "unit": "artifact", "n_units": 96, "domains": ["scenes2"], "factors": {"checkpoint": ["anchor", "qwen3b"], "steer": ["zero", "congruent", "incongruent", "random"]},
            "controls": ["incongruent", "random", "decode"], "depends_on": ["B01"],
            "primary": "checkpoint x domain x steering interaction on a second artifact domain",
            "threshold": 0.03, "est_s_per_unit": 8.0},
    "B03": {"gpu": True, "unit": "artifact", "n_units": 96, "domains": ["scenes"], "factors": {"coordinate": ["locus", "shifted", "random_blocks"], "dose": ["half", "frozen", "double"], "sign": ["plus", "minus"]},
            "controls": ["label_permutation", "own_answer"], "depends_on": ["B01"],
            "primary": "coordinate and dose specificity of the congruent effect; label-permuted directions and own-answer shift quiet",
            "threshold": 0.03, "est_s_per_unit": 8.0},
    # ── J: joint reconstruction ─────────────────────────────────────────────────────
    "J01": {"gpu": True, "unit": "world", "domains": list(DOMAINS), "factors": {"latent": ["episode_goal", "process_plan", "standing_preference"]},
            "controls": ["equifinal_abstention"], "depends_on": ["I04"],
            "primary": "each latent recovered when the other two are supplied, log score over the exact-known answer; abstention on equifinal plans",
            "threshold": 0.03, "est_s_per_unit": 6.0},
    "J02": {"gpu": True, "unit": "world", "domains": list(DOMAINS), "factors": {"reader": ["factored", "goal_first", "process_first", "preference_first", "recurrent", "oracle"]},
            "controls": ["oracle", "compute_matched"], "depends_on": ["J01"],
            "primary": "recurrent joint reader minus the best same-evidence staged or factored reader on the held-out choice log score",
            "threshold": 0.03, "est_s_per_unit": 30.0},
    "J03": {"gpu": True, "unit": "world", "domains": list(DOMAINS), "factors": {"evidence_step": ["1", "2", "3", "4", "5", "6", "7", "8"]},
            "controls": ["contradiction"], "depends_on": ["J01"],
            "primary": "posterior trajectory: first-useful step per latent, reversals, overconfidence after a contradiction",
            "threshold": None, "est_s_per_unit": 24.0},
    "J04": {"gpu": True, "unit": "world", "domains": list(DOMAINS), "factors": {"world": ["conflict", "consistent"], "hypothesis_set": ["fixed", "opened"]},
            "controls": ["false_alarm"], "depends_on": ["J02"],
            "primary": "opened missing-goal hypothesis minus fixed set on conflict worlds, cost-matched; the false-alarm cost on consistent worlds",
            "threshold": 0.03, "est_s_per_unit": 12.0},
    "J05": {"gpu": True, "unit": "world", "domains": list(DOMAINS), "factors": {"predictor": ["inferred_preference", "habit", "topic", "last_goal"]},
            "controls": ["habit", "topic", "last_goal"], "depends_on": ["J02"],
            "primary": "inferred standing preference minus the best cheap baseline on the episode-2 choice log score",
            "threshold": 0.03, "est_s_per_unit": 8.0},
    # ── A: appraisal, audience, and strategic communication ─────────────────────────
    "A01": {"gpu": True, "unit": "world", "domains": list(SOURCE_DOMAINS), "factors": {"owner": ["reader_response", "audience_effect_goal", "maker_appraisal", "content_support"]},
            "controls": ["owner_swap"], "depends_on": ["I04"],
            "primary": "four-way proper scores on the owner questions; the swap stratum carries the separation",
            "threshold": 0.03, "est_s_per_unit": 8.0},
    "A02": {"gpu": True, "unit": "world", "domains": list(SOURCE_DOMAINS), "factors": {"behavior": ["selection", "correction", "private_action"], "twin": ["original", "twin"]},
            "controls": ["collision_abstention"], "depends_on": ["A01"],
            "primary": "predicted divergent behavior (selection, correction, private action) log score over chance; abstention on collision twins",
            "threshold": 0.03, "est_s_per_unit": 12.0},
    "A03": {"gpu": True, "unit": "world", "domains": list(SOURCE_DOMAINS), "factors": {"maker": ["audience_modeling", "plain"], "reader_model": ["audience", "ordinary"]},
            "controls": ["interaction"], "depends_on": ["A01"],
            "primary": "reader-model x maker-mechanism interaction on the content-support log score",
            "threshold": 0.03, "est_s_per_unit": 8.0},
    "A04": {"gpu": True, "unit": "world", "domains": list(SOURCE_DOMAINS), "factors": {"condition": ["none", "source_label", "influence_awareness", "reappraisal"]},
            "controls": ["criterion", "true_uptake"], "depends_on": ["A01"],
            "primary": "discrimination (support AUROC) under labeling and reappraisal beyond none, with criterion and true-advice uptake apart",
            "threshold": 0.05, "est_s_per_unit": 10.0},
    "A05": {"gpu": True, "unit": "world", "domains": list(SOURCE_DOMAINS), "factors": {"history": ["reliable", "unreliable"], "episode": ["honest", "deceptive"]},
            "controls": ["content_unchanged", "goal_unchanged"], "depends_on": ["A01"],
            "primary": "trust changes uptake (reliable minus unreliable) while content-support and communicative-goal posteriors do not move",
            "threshold": 0.05, "est_s_per_unit": 8.0},
    # ── R: route reliability, ease, and conflict ────────────────────────────────────
    "R01": {"gpu": True, "unit": "world", "domains": list(DOMAINS), "factors": {"choice": ["model", "random", "first", "easiest", "exact"]},
            "controls": ["random", "first", "easiest"], "depends_on": ["I04"],
            "primary": "chosen-route exact information minus the random selector, on worlds past the divergence floor",
            "threshold": 0.03, "est_s_per_unit": 4.0},
    "R02": {"gpu": True, "unit": "world", "domains": list(DOMAINS), "factors": {"ease": ["plain", "stilted"], "information": ["high", "low"]},
            "controls": ["equal_accuracy_different_ease", "equal_ease_different_accuracy"], "depends_on": ["R01"],
            "primary": "reliance on a route follows its exact information, not its ease (the ease x information interaction)",
            "threshold": 0.03, "est_s_per_unit": 8.0},
    "R03": {"gpu": True, "unit": "world", "domains": list(DOMAINS), "factors": {"demonstrations": ["none", "three", "misleading"], "diagnosticity": ["high", "low"]},
            "controls": ["misleading"], "depends_on": ["R01"],
            "primary": "demonstration x diagnosticity interaction on route use and calibration (familiarization, not expertise)",
            "threshold": 0.03, "est_s_per_unit": 10.0},
    "R04": {"gpu": True, "unit": "world", "domains": list(DOMAINS), "factors": {"policy": ["exact", "model", "random", "always"]},
            "controls": ["random", "always"], "depends_on": ["R01"],
            "primary": "realized prediction gain per declared cost under the model's forensic purchases minus random",
            "threshold": 0.03, "est_s_per_unit": 6.0},
    # ── P: process and physical traces ──────────────────────────────────────────────
    "P01": {"gpu": False, "unit": "drawing", "n_units": 700, "domains": ["all"], "factors": {"access": ["final_geometry", "unordered_set", "partial_order", "true_prefix"]},
            "controls": ["category_prior", "shape_prior"], "depends_on": ["I03"],
            "primary": "held-out next-stroke log score at each access level beyond category and shape priors",
            "threshold": 0.03, "est_s_per_unit": 0.5},
    "P02": {"gpu": True, "unit": "drawing", "n_units": 120, "domains": ["all"], "factors": {"pair": ["equifinal"]},
            "controls": ["historical_correspondence"], "depends_on": ["P01"],
            "primary": "enactability of the proposed production route on equifinal artifacts, historical correspondence apart, uncertainty required",
            "threshold": 0.05, "est_s_per_unit": 6.0},
    "P03": {"gpu": False, "unit": "drawing", "n_units": 700, "domains": ["all"], "factors": {"competence": ["low", "high"], "access": ["unordered_set", "partial_order", "true_prefix"]},
            "controls": ["interaction"], "depends_on": ["P01"],
            "primary": "measured competence x access-level interaction on reconstruction, two drawing domains",
            "threshold": 0.03, "est_s_per_unit": 0.5},
    # ── F: interest and epistemic foraging ──────────────────────────────────────────
    "F01": {"gpu": True, "unit": "set", "domains": ["all"], "factors": {"item_class": ["novel_explained", "complex_compressible", "random_unlearnable", "structured_residual", "trivial_known", "learnable_intermediate"]},
            "controls": ["ranking_likelihood"], "depends_on": ["I02"],
            "primary": "the reader's evidence ranking against the exact rulers (novelty, complexity, error, learning progress, relevance)",
            "threshold": None, "est_s_per_unit": 8.0},
    "F02": {"gpu": True, "unit": "set", "domains": ["all"], "factors": {"policy": ["learning_progress", "model", "novelty", "surprise", "random"]},
            "controls": ["novelty", "surprise", "random"], "depends_on": ["F01"],
            "primary": "realized held-out gain per cost under the model's selections minus the best raw-signal baseline",
            "threshold": 0.03, "est_s_per_unit": 6.0},
    "F03": {"gpu": True, "unit": "set", "domains": ["all"], "factors": {"hope": ["congruent", "incongruent"], "prompt": ["plain", "counter_bias"]},
            "controls": ["false_discovery"], "depends_on": ["F01"],
            "primary": "selection of the hoped-for explanation beyond its support (pursuit against warrant), with the false-discovery rate",
            "threshold": 0.05, "est_s_per_unit": 6.0},
    # ── C: frozen confirmation and closure ──────────────────────────────────────────
    "C01": {"gpu": True, "unit": "world", "domains": [], "factors": {}, "controls": ["severe_rival", "negative_control"],
            "depends_on": [], "primary": "the strongest qualified bridge on untouched makers, sources, and seeds",
            "threshold": None, "est_s_per_unit": 1.0},
    "C02": {"gpu": True, "unit": "world", "domains": [], "factors": {}, "controls": ["severe_rival"],
            "depends_on": [], "primary": "the strongest qualified boundary or second effect, independently",
            "threshold": None, "est_s_per_unit": 1.0},
}
for _c, _v in CARDS.items():
    _v["track"] = TRACK_OF[_c]

# preservation order (§8.2 allocation order): integrity, bridge, joint, appraisal, route,
# process, foraging; the confirmation cards run in the closure block
PRESERVATION_ORDER = ["I01", "I02", "I03", "I04", "B01", "B02", "B03", "J01", "J02", "J03", "J05", "J04",
                      "A01", "A02", "A03", "A04", "A05", "R01", "R02", "R03", "R04", "P01", "P02", "P03",
                      "F01", "F02", "F03"]
CPU_CARDS = tuple(c for c, v in CARDS.items() if not v["gpu"] and c not in ("C01", "C02"))
# confirmation selection order (§7.4)
BRIDGE_ORDER = ["B01", "B02", "J02", "J05", "A02", "A03", "R02", "P01", "P02", "F01", "F02"]
# the expansion ladder's frozen order (§8.3)
EXPANSION_ORDER = ["J02", "A02", "B01", "R02", "P02", "J05"]

TIERS = {"minimum": {"world": 64, "set": 48}, "expanded": {"world": 128, "set": 96}}
CONFIRMATION_UNITS = {"world": 128, "set": 96, "artifact": 96, "drawing": 300}
TRANSFER_UNITS = {"world": 32, "set": 24}
DERIVED = {"J02": "J01", "J03": "J01", "J04": "J01", "J05": "J01", "R01": "J01", "R02": "J01", "R03": "J01", "R04": "J01",
           "A02": "A01", "A03": "A01", "A04": "A01", "A05": "A01", "F02": "F01", "F03": "F01"}


def units_for(card: str, tier: str) -> int:
    c = CARDS[card]
    if "n_units" in c:
        return c["n_units"]
    return TIERS[tier][c["unit"]]


def expected_spec(tier: str) -> dict:
    spec = {}
    for card, c in CARDS.items():
        if not c["domains"] and not c["factors"]:
            continue
        spec[card] = {"factors": dict(c["factors"]), "domains": list(c["domains"]) or ["all"],
                      "n_units": units_for(card, tier), "controls": list(c["controls"])}
    return spec


def gpu_estimate_hours(tier: str, multiplier: float = 1.0, cards=None, units_override: int | None = None) -> dict:
    out = {}
    total = 0.0
    for card, c in CARDS.items():
        if cards is not None and card not in cards:
            continue
        if not c["gpu"]:
            continue
        per_dom = (units_override if (units_override is not None and "n_units" not in c) else units_for(card, tier))
        n_dom = max(1, len(c["domains"]))
        n_cells = 1
        for lv in c["factors"].values():
            n_cells *= len(lv)
        hours = c["est_s_per_unit"] * per_dom * n_dom * multiplier / 3600
        out[card] = round(hours, 3)
        total += hours
    out["total"] = round(total, 2)
    out["allocation_total"] = sum(ALLOCATION_HOURS.values())
    return out
