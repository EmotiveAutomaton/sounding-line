"""Stage 8 question registry (brief §7, §8): the 44 questions and 12 attacks with their
discriminators, engines, dependencies, unit counts, per-unit time assumptions, the evidence
condition each runs, the arms, and the identity tuple (lineage, supplied, withheld target,
estimator, comparison, statistic) whose hash the manifest uses to reject two cards that
reduce to one mapping and statistic. ONE home for all of it; every gate's null, alternative,
and direction lives in the engine that runs the card.

Readers: the forward-model readers are `adapter:<name>` ids (the base reader with its frozen
adapter, served by the loopback server); the untrained arms (DIR0, FMB) run the base ids.

DESIGN CHECK (2026-09-04)
lessons read: LESSONS §3, §5 (a registry carries no gate; every card a produces guard;
  underestimate runtimes 2-3x: the workload lock is sized from the measured pilot and
  re-locked from the base run's actual costs; count the identity space: the identity tuple
  is the registry's own duplicate check).
gates: none here; the expected-cell validator (I02) checks removal fails coverage and the
  manifest rejects duplicate identity hashes. bands: none.
"""

from __future__ import annotations

import os

from soundingline.stage8 import ATTACKS as ATTACK_IDS, QUESTIONS as QUESTION_IDS, PURPOSES, SHAPES  # noqa: F401

DOMAINS = ("essay", "workshop_doc")
BASES = {"fm_qwen": "Qwen/Qwen2.5-1.5B-Instruct", "fm_smollm": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
         "fm_qwen05": "Qwen/Qwen2.5-0.5B-Instruct"}
READERS = {"qwen": "adapter:fm_qwen", "smollm": "adapter:fm_smollm"}
LADDER_READER = {"qwen05": "adapter:fm_qwen05"}
ENGINES = ("isolation", "expertise", "difference", "purpose", "accumulation", "testbed", "closure", "attack")
MODEL_ARMS = {"DIR0", "FM", "FMP", "FMN", "FMC", "FMS", "FMB", "FMPT", "PUR", "PULL", "LAWR", "RESR", "GEN", "STU"}
FR_ARMS = {"FR"}
TARGETS = ("next_action", "stop", "changed_context", "purpose", "surprise")
ALL7 = ["external_context", "belief_state", "expertise_law", "maker_context", "subjective_action_space", "proximal_goal", "history_residue"]
FIVE = ["external_context", "belief_state", "expertise_law", "proximal_goal", "history_residue"]     # the derived two left to the law


def base_of(reader_id: str) -> str:
    """The base model id a reader id runs on (the untrained arms use it directly)."""
    if reader_id.startswith("adapter:"):
        return BASES[reader_id.split(":", 1)[1]]
    return reader_id


def _cond(family: str, purpose: str = "withheld", shape: str | None = None, n_earlier: int = 0,
          per_event: bool = False, maker_free: bool = False, supplied: list[str] | None = None,
          form: str = "language", no_change: bool = False) -> dict:
    return {"family": family, "purpose": purpose, "shape": shape, "n_earlier": n_earlier, "per_event": per_event,
            "maker_free": maker_free, "supplied": list(supplied or []), "form": form, "no_change": no_change,
            "render": "log", "regime": "cold"}


def _q(engine: str, question: str, discriminator: str, deps: list[str], gpu: bool, unit: str, n_units: int,
       est: float, identity: tuple, condition: dict | None = None, arms: list[str] | None = None,
       factors: dict | None = None, threshold: float | None = 0.03, primary: str | None = None,
       targets: tuple = ("next_action", "stop"), readers: list[str] | None = None, network: bool = False) -> dict:
    assert engine in ENGINES, engine
    assert len(identity) == 6, identity
    return {"engine": engine, "question": question, "discriminator": discriminator, "depends_on": deps,
            "gpu": gpu, "network": network, "unit": unit, "n_units": n_units, "est_s_per_unit": est,
            "identity": {"lineage": identity[0], "supplied": identity[1], "withheld_target": identity[2],
                         "estimator": identity[3], "comparison": identity[4], "statistic": identity[5]},
            "condition": condition or _cond("K"), "arms": arms or ["FM"], "factors": factors or {},
            "threshold": threshold, "primary": primary or question, "targets": list(targets),
            "readers": readers or list(READERS.values())}


QUESTIONS: dict[str, dict] = {
    # ── I: isolation and integrity (8) ────────────────────────────────────────────
    "I01": _q("isolation", "Do the reviewed heads, the Stage 7 anchors, and the adapter file hashes reproduce?",
              "exact commit and hash receipt; mismatch blocks inheritance", ["E02"], False, "receipt", 1, 60.0,
              ("repo", "none", "none", "hash", "recorded_vs_live", "identity"), threshold=None),
    "I02": _q("isolation", "Does the manifest enumerate all 44 questions, 12 attacks, families, lineages, outputs, and closures, rejecting duplicate estimands?",
              "removal of any item fails coverage; duplicate tuples fail the manifest", [], False, "audit", 1, 60.0,
              ("manifest", "none", "none", "enumeration", "removal", "coverage"), threshold=None),
    "I03": _q("isolation", "Is the reader physically unable to reach constructor, oracle, or training-corpus state?",
              "forbidden operations raise inside the real capsule; access receipt clean", ["I02"], False, "probe", 1, 120.0,
              ("capsule", "none", "none", "probe", "attempts", "all_raised"), threshold=None),
    "I04": _q("isolation", "Do hidden-tail, hidden-stop, and hidden-event mutations leave every non-oracle prediction byte-identical?",
              "identity 1.0 on every arm, the oracle differing on most pairs", ["I03", "E02"], True, "world", 8, 30.0,
              ("worlds_attack_S8", "context", "none", "canonical_bytes", "three_mutations", "identity_rate"),
              condition=_cond("K", supplied=ALL7, form="executable"), arms=["U", "PERS", "DOM", "SOL", "FM", "DIR0"], threshold=None),
    "I05": _q("isolation", "Does a diagnostic visible observation move the declared prediction?",
              "sensitivity positive while I04 holds", ["I04"], True, "world", 12, 30.0,
              ("worlds_attack_S8", "context", "next_action", "tv", "visible_flip", "moved_rate"),
              condition=_cond("K", supplied=FIVE, form="executable"), arms=["DOM", "SOL", "FM", "DIR0"], threshold=None),
    "I06": _q("isolation", "Are targets absent from identifiers, ordering, lengths, seeds, schemas, prompts, caches, and logs, the purpose and required sections included?",
              "planted canaries caught; clean nulls at floor", ["I03"], False, "audit", 1, 300.0,
              ("worlds_conf_S8", "all_families", "none", "canary_detector", "planted_vs_clean", "catch_rate_and_floor"), threshold=None),
    "I07": _q("isolation", "Do the training lineages and every test lineage share no descendant, by hash?",
              "zero overlap under recursive lineage expansion; the adapter's training manifest lists every lineage it saw", ["E02"], False, "audit", 1, 120.0,
              ("lineages", "none", "none", "descendant_expansion", "train_vs_test", "overlap_count"), threshold=None),
    "I08": _q("isolation", "Does one keystone world pass a manual constructor-to-score audit through the trained reader before scale?",
              "signed trace: capsule listing without oracle files, the adapter hash, the model's own option scores, the truth lookup, the score",
              ["I04", "I05"], True, "world", 1, 300.0, ("worlds_conf_S8", "context", "next_action", "trace", "manual", "signed"),
              condition=_cond("K", supplied=ALL7, form="executable"), arms=["FM", "SOL"], threshold=None),
    # ── E: expertise installation and gate (8) ────────────────────────────────────
    "E01": _q("expertise", "Does the population corpus carry the standard process and nothing maker-specific?",
              "DOM refit on POP matches the Stage 7 DOM within band on the shared family; per-maker factors unrecoverable from POP by the exact selector",
              ["I02"], False, "audit", 1, 900.0, ("POP", "none", "none", "dom_refit_and_selector", "stage7_dom", "band_and_recall"), threshold=None),
    "E02": _q("expertise", "Does adapter training converge to a forward model of the standard process on each reader?",
              "held-out POP next-move log score improves monotonically to within the pass band of DOM; curves and seeds recorded; one repair if the band is missed by under 0.05",
              ["E01"], True, "training", 2, 1800.0, ("POP", "none", "next_move", "adapter_training", "dom_band", "heldout_curve"), threshold=None),
    "E03": _q("expertise", "The expertise gate: does the trained reader's own forward model predict the next move at the standard process's level with nothing supplied?",
              "FM against DOM on held-out POP and on maker-free PU worlds within -0.05 nats, per reader before pooling",
              ["E02", "I08"], True, "world", 48, 6.0, ("POP_heldout_and_PU_makerfree", "context", "next_action", "fm", "fm_vs_dom", "gap_band"),
              condition=_cond("POPPU", maker_free=True), arms=["U", "PERS", "DOM", "FM"], threshold=None),
    "E04": _q("expertise", "The generation gate: does the trained reader produce the standard process?",
              "generated logs' likelihood under the exact standard process at or above the real logs' 20th percentile; feasibility 1.0",
              ["E02", "I08"], True, "world", 20, 12.0, ("POP_gen", "context", "whole_log", "generation", "population_marginal", "percentile_and_feasibility"),
              condition=_cond("POP", no_change=True), arms=["GEN"], threshold=None),
    "E05": _q("expertise", "Do the untrained readers fail the same gates?",
              "DIR0 and the base weights through the generative readout on E03 and E04; the expected outcome is failure", ["E03", "E04"], True, "world", 48, 8.0,
              ("POP_heldout_and_PU_makerfree", "context", "next_action", "dir0_and_base", "vs_dom", "gap_band"),
              condition=_cond("POPPU", maker_free=True), arms=["DIR0", "FMB", "GEN"], threshold=None),
    "E06": _q("expertise", "After the gate, does a true context help and a false context cost?",
              "supplied true against false context on PU worlds; the theory predicts a sign difference; the Stage 4 frame-not-content comparator is the rival",
              ["E03"], True, "world", 40, 6.0, ("PU", "context_true_vs_false", "next_action", "fm", "true_vs_false", "sign_difference"),
              condition=_cond("PU"), arms=["FMC", "DOM"]),
    "E07": _q("expertise", "Does the frontier probe pass the expertise gate cold?",
              "FR on E03's worlds through the verbalized distribution, thinking on; pass or fail against the same band; dollars per call",
              ["E03"], False, "world", 24, 20.0, ("POP_heldout_and_PU_makerfree", "context", "next_action", "frontier", "fr_vs_dom", "gap_band"),
              condition=_cond("POPPU", maker_free=True), arms=["FR"], threshold=None, network=True),
    "E08": _q("expertise", "Does the trained reader use a supplied executable state better than the untrained one did (the Stage 7 K04 comparator)?",
              "FM with the complete state supplied against DOM; a diagnostic, not a gate", ["E03"], True, "world", 40, 6.0,
              ("K", "all7_lines", "next_action", "fm_state", "fm_vs_dom", "gain_nats"),
              condition=_cond("K", supplied=["external_context", "belief_state", "expertise_law", "maker_context", "subjective_action_space", "proximal_goal", "history_residue"], form="executable"),
              arms=["FMS", "SOL", "DOM"]),
    # ── D: surprise localization (6) ───────────────────────────────────────────────
    "D01": _q("difference", "Does the admitted reader's surprise land on the maker's events at least as well as the standard process's surprise does?",
              "surprise AUROC for FM minus DOM's, per family and shape; the gate is non-inferiority", ["E03"], True, "world", 48, 12.0,
              ("AG_per_event", "context", "surprise", "auroc", "fm_vs_dom", "auroc_difference"),
              condition=_cond("AG", per_event=True), arms=["FM"], targets=("surprise",), factors={"shape": list(SHAPES)}),
    "D02": _q("difference", "Does surprise alignment rise across the artful gradient?",
              "AUROC by task shape with the construction fact (tail gap by shape) beside it", ["D01"], False, "analysis", 1, 60.0,
              ("AG_per_event", "context", "surprise", "auroc_by_shape", "shapes", "monotone"), threshold=None),
    "D03": _q("difference", "Does the reader's first explanation fire at the most divergent event?",
              "entry position against the oracle's most divergent event; descriptive", ["D01"], False, "analysis", 1, 60.0,
              ("AG_per_event", "context", "surprise", "entry_position", "oracle_argmax", "hit_rate"), threshold=None),
    "D04": _q("difference", "Does supplying the true purpose sharpen surprise onto the residue?",
              "FM with p supplied: alignment against D01; the residue should become the remaining surprise", ["D01"], True, "world", 40, 12.0,
              ("PU_per_event", "purpose", "surprise", "auroc", "fmp_vs_fm", "auroc_difference"),
              condition=_cond("PU", purpose="supplied", per_event=True), arms=["FMPT", "FM"], targets=("surprise",)),
    "D05": _q("difference", "Does the frontier probe's surprise align better than DOM's?",
              "FR on D01's worlds, capped", ["D01"], False, "world", 16, 40.0,
              ("AG_per_event", "context", "surprise", "frontier_auroc", "fr_vs_dom", "auroc_difference"),
              condition=_cond("AG", per_event=True), arms=["FR"], targets=("surprise",), threshold=None, network=True),
    "D06": _q("difference", "Is the tail contrast what the whole contrast hides?",
              "for every prospective card the tail and whole contrasts side by side; a sign difference is a result", ["G02", "G03", "E08", "A03", "E06"], False, "analysis", 1, 60.0,
              ("prospective_cards", "as_covered", "next_action", "whole_vs_tail", "cards", "sign_table"), threshold=None),
    # ── G: goal as purpose (8) ────────────────────────────────────────────────────
    "G01": _q("purpose", "Does the admitted reader name the purpose by the affordance route?",
              "recall of p (or its equivalence partner) from the closed affordance distribution with an unknown option; bar 0.5", ["E03"], True, "world", 48, 5.0,
              ("PU", "context", "purpose", "affordance_readout", "truth_or_partner", "recall"),
              condition=_cond("PU"), arms=["PUR"], targets=("purpose",), threshold=None),
    "G02": _q("purpose", "Does executing the inferred purpose through the reader's own forward model improve the rest of the artifact?",
              "FM+P against FM and against DOM, whole and tail; the floor a fifth of the relevant gap", ["G01"], True, "world", 48, 8.0,
              ("PU", "proposed_purpose", "next_action", "fmp", "fmp_vs_fm_and_dom", "gain_whole_and_tail"),
              condition=_cond("PU"), arms=["FMP", "FM", "DOM", "U", "PERS"]),
    "G03": _q("purpose", "Does it improve the changed-context choice?",
              "FM+P on the counterfactual target against DOM and the copied-brief rival", ["G02"], False, "analysis", 1, 60.0,
              ("PU", "proposed_purpose", "changed_context", "fmp", "fmp_vs_dom_and_copied", "gain_nats"), targets=("changed_context",)),
    "G04": _q("purpose", "Does the reader keep two purposes alive where the prefix leaves two, and abstain?",
              "class coverage and abstention on the equivalence worlds; at least half on equivalence cases, at most half false abstention", ["G01"], False, "analysis", 1, 60.0,
              ("PU_equivalence", "context", "purpose", "class_coverage", "equivalence_worlds", "coverage_and_false_abstain"), threshold=None),
    "G05": _q("purpose", "Which goal object is easier for the same reader, the purpose or the pull ordering?",
              "recall of p against recall of the derived pull ordering on the same worlds and reader", ["G01"], True, "world", 48, 5.0,
              ("PU", "context", "pull_ordering", "closed_readout", "purpose_vs_pull", "recall_difference"),
              condition=_cond("PU"), arms=["PULL"], targets=("pull",), threshold=None),
    "G06": _q("purpose", "Does purpose recall survive paraphrase of the artifact and fail under a meaning change?",
              "the X04 crossover on G01", ["G01"], True, "world", 24, 10.0,
              ("PU_paraphrase_meaning", "context", "purpose", "affordance_readout", "paraphrase_vs_meaning", "recall_crossover"),
              condition=_cond("PU"), arms=["PUR"], targets=("purpose",), threshold=None),
    "G07": _q("purpose", "Is the reader's confidence over purposes an information meter?",
              "calibration of the distribution against evidence dose; the Stage 5 comparator is a valid null", ["G01"], False, "analysis", 1, 60.0,
              ("PU", "context", "purpose", "calibration_by_dose", "prefix_length", "slope_and_ece"), threshold=None),
    "G08": _q("purpose", "Does the frontier probe name the purpose and profit from it?",
              "FR on G01 and G02, capped", ["G02"], False, "world", 16, 40.0,
              ("PU", "context", "purpose_and_next_action", "frontier", "fr_recall_and_gain", "recall_and_gain"),
              condition=_cond("PU"), arms=["FR"], targets=("purpose", "next_action"), threshold=None, network=True),
    # ── A: accumulation (5) ───────────────────────────────────────────────────────
    "A01": _q("accumulation", "Does surprise alignment on artifact N+1 improve with N earlier artifacts by the same maker in context?",
              "FM+N for N in 0 to 3 against DOM; monotone in N is the alternative", ["E03"], True, "maker", 24, 40.0,
              ("MS_per_event", "earlier_artifacts", "surprise", "auroc_by_n", "fmn_vs_dom", "monotone_in_n"),
              condition=_cond("MS", per_event=True), arms=["FMN"], targets=("surprise",), factors={"n_earlier": [0, 1, 2, 3]}),
    "A02": _q("accumulation", "Does the reader's recall of the maker's law and residue rise with N?",
              "recall from the closed distributions at each N; the Stage 7 recall figures are the N=0 comparator", ["E03"], True, "maker", 24, 20.0,
              ("MS", "earlier_artifacts", "law_and_residue", "closed_readout", "by_n", "recall_by_n"),
              condition=_cond("MS"), arms=["LAWR", "RESR"], targets=("law", "residue"), factors={"n_earlier": [0, 1, 2, 3]}, threshold=None),
    "A03": _q("accumulation", "Does the model of the maker predict a new artifact's divergences?",
              "tail contrast on artifact N+1 for FM+3 against DOM and against FM+0", ["A01"], True, "maker", 24, 20.0,
              ("MS", "earlier_artifacts", "next_action", "fmn3", "fmn3_vs_dom_and_fmn0", "gain_whole_and_tail"),
              condition=_cond("MS"), arms=["FMN", "FM", "DOM", "U", "PERS"]),
    "A04": _q("accumulation", "Does the reveal parameter change what is learned?",
              "alignment and recall by reveal level; descriptive", ["A01", "A02"], False, "analysis", 1, 60.0,
              ("MS", "earlier_artifacts", "surprise_and_recall", "by_reveal", "low_vs_high", "difference"), threshold=None),
    "A05": _q("accumulation", "Is the accumulation the law's or the goal's?",
              "decompose A03's gain by which supplied factor removes it; the Stage 7 finding (earlier artifacts carry the law) is the rival", ["A03"], True, "maker", 24, 20.0,
              ("MS", "earlier_plus_factor", "next_action", "fmn3_plus_factor", "law_vs_residue_vs_purpose", "gain_removed"),
              condition=_cond("MS"), arms=["FMN", "DOM"], factors={"supplied": ["none", "law", "residue", "purpose"]}),
    # ── T: testbed expansion (5) ──────────────────────────────────────────────────
    "T01": _q("testbed", "Are the sibling programs' repositories cloned read-only into the reference workspace, pinned, and manifested?",
              "commit, license, paper version, and setup result per clone; none on the capsule path", [], False, "receipt", 1, 1800.0,
              ("reference_clones", "none", "none", "clone_receipt", "pinned", "count"), threshold=None, network=True),
    "T02": _q("testbed", "Are the human-input corpora fetched as manifests under the fetch discipline?",
              "hashes, URLs, lengths, and license per item; no re-hosting; robots and rate limits honored", [], False, "receipt", 1, 1800.0,
              ("corpus_manifests", "none", "none", "fetch_receipt", "manifested", "count"), threshold=None, network=True),
    "T03": _q("testbed", "Does every corpus and repository carry a catalog card in docs/TOOLS.md?",
              "one card each: human input, size, license, loader status, the Stage 9 question", ["T01", "T02", "T04", "T05"], False, "receipt", 1, 120.0,
              ("catalog", "none", "none", "cards", "coverage", "count"), threshold=None),
    "T04": _q("testbed", "Do the loaders parse?", "a smoke read of each corpus with counts; a known mini-fixture per loader", ["T02"], False, "fixture", 1, 300.0,
              ("corpus_loaders", "none", "none", "parse", "fixtures", "pass_count"), threshold=None),
    "T05": _q("testbed", "Does each corpus reproduce one published cheap baseline?", "one number per corpus where a paper states one; a reproduction receipt", ["T04"], False, "receipt", 1, 600.0,
              ("corpus_baselines", "none", "none", "reproduction", "published", "receipts"), threshold=None),
    # ── B: confirmation, closure, reporting (4) ───────────────────────────────────
    "B01": _q("closure", "Does the strongest gate-passing reader effect replicate on untouched lineages?", "frozen estimand, reader, and rival; untouched worlds", [], True, "world", 48, 8.0,
              ("untouched_conf_1", "as_frozen", "as_frozen", "frozen_contrast", "frozen_rival", "replication"), condition=_cond("PU")),
    "B02": _q("closure", "Does the strongest purpose or accumulation effect replicate on untouched lineages?", "same", ["B01"], True, "world", 48, 8.0,
              ("untouched_conf_2", "as_frozen", "as_frozen", "frozen_contrast", "frozen_rival", "replication"), condition=_cond("PU")),
    "B03": _q("closure", "Do coverage, source, access, compute, dollar, pursuit, warrant, and claim ledgers agree, and does a fresh clone reproduce them?",
              "machine reconciliation after the closure tail; the ledger cell runs last", ["B04"], False, "ledger", 1, 600.0,
              ("ledgers", "none", "none", "reconciliation", "ledgers", "agreement"), threshold=None),
    "B04": _q("closure", "What moves in the project world model, and should Stage 9 open on the testbed?",
              "one two-pass packet, the curator's ruling; no automatic continuation", ["D06", "G04", "A04", "T03"], False, "analysis", 1, 120.0,
              ("world_model", "none", "none", "routing", "branching_table", "routing"), threshold=None),
}
assert set(QUESTIONS) == set(QUESTION_IDS), (set(QUESTION_IDS) ^ set(QUESTIONS))


def _x(covers: list[str], attack: str, expect: str, consequence: str, gpu: bool = False,
       unit: str = "derived", n_units: int = 1, est: float = 300.0, arms: list[str] | None = None,
       condition: dict | None = None, deps: list[str] | None = None) -> dict:
    return {"engine": "attack", "covers": covers, "question": attack, "discriminator": expect,
            "consequence": consequence, "depends_on": deps if deps is not None else [c for c in covers if c in QUESTIONS][:3],
            "gpu": gpu, "network": False, "unit": unit, "n_units": n_units, "est_s_per_unit": est,
            "factors": {}, "threshold": None, "primary": attack, "arms": arms or [], "condition": condition or _cond("K"),
            "identity": {"lineage": f"attack_{attack[:24]}", "supplied": "as_covered", "withheld_target": "as_covered",
                         "estimator": "attack", "comparison": expect[:40], "statistic": consequence[:40]},
            "targets": ["next_action", "stop"], "readers": list(READERS.values())}


ATTACKS: dict[str, dict] = {
    "X01": _x(["I04"], "Replace the hidden future, length, stop, and events with visible bytes fixed.", "byte-identical non-oracle predictions", "any non-oracle movement voids affected results"),
    "X02": _x(["I03", "E02"], "Attempt forbidden reads from the capsule, including the training corpus and adapter training logs.", "every attempt raises", "success blocks the lock", unit="probe", est=120.0),
    "X03": _x(["I07"], "Search every test lineage's ancestry against the adapter's training manifest, by hash.", "zero overlap", "any overlap voids every FM result on that lineage"),
    "X04": _x(["G06"], "Paraphrase the artifact and, separately, change its meaning, on the purpose prompts.", "recall survives paraphrase and falls under the meaning change", "a meaning-blind purpose reader closes"),
    "X05": _x(["G02", "E03"], "Permute option and candidate order with fixed-order paired scoring.", "invariance within tolerance", "an order-driven contrast is re-run under fixed order", True, "world", 12, 12.0, ["FM", "DIR0"], _cond("PU")),
    "X06": _x(["A01", "A03"], "Duplicate evidence from one causal source.", "no sharpening as if independent", "the double-count defect closes the affected posterior claims", True, "maker", 12, 20.0, ["FMN"], _cond("MS")),
    "X07": _x(["G04"], "Hold the final artifact fixed while swapping valid hidden histories.", "equivalence class preserved, by the declared criterion", "forced point accuracy on equifinal classes voids the cell"),
    "X08": _x(["E03", "D01", "G02", "A01"], "Report every reader, family, shape, and N cell before pooling.", "a designed reversal is never pooled away", "a pooled rescue is refused"),
    "X09": _x(["E07", "D05", "G08", "E03"], "Price every arm's compute and dollars.", "priced compute on every arm; FR stops at its cap", "unpriced compute forbids any efficiency claim"),
    "X10": _x(["G02", "A03"], "Strengthen the cheap rivals (PERS, DOM, copied brief).", "maker claims require gain beyond the strongest frozen rival", "a claim under the strengthened rival is renamed"),
    "X11": _x(["E03", "D01"], "Run the trained reader on a maker family it never saw (a second law family under the frozen ontology).", "conditional failure reported before any generality claim", "a pooled generality claim is refused", True, "world", 24, 8.0, ["FM", "DOM", "U"], _cond("K2")),
    "X12": _x(["B03"], "Fresh-clone every manifest, hash, receipt, and confirmation input; force one kill and resume.", "the fresh clone reproduces manifests, hashes, dispositions, and packet inputs", "any mismatch blocks the packet", deps=["B04"]),
}
assert set(ATTACKS) == set(ATTACK_IDS), (set(ATTACK_IDS) ^ set(ATTACKS))

ALL = {**QUESTIONS, **ATTACKS}

# the run order (§9 gate order): integrity and the record gate, training, the isolation block
# on the trained reader, the gates, the difference and purpose trunks, accumulation, the
# attacks, the testbed in the CPU lane throughout, the closure tail last
PRESERVATION_ORDER = (
    ["I02", "I03", "I06", "E01", "E02", "I01", "I07", "I04", "I05", "I08", "X02", "X03"]
    + ["E03", "E04", "E05", "E06", "E08", "E07", "X01", "X05"]
    + ["D01", "D04", "D02", "D03", "D05", "X11"]
    + ["G01", "G02", "G05", "G06", "G03", "G04", "G07", "G08", "X04", "X07"]
    + ["A01", "A02", "A03", "A05", "A04", "X06", "D06", "X08", "X09", "X10"]
    + ["T01", "T02", "T04", "T05", "T03"]
    + ["B04"]
)
_rest = [c for c in list(QUESTIONS) + list(ATTACKS) if c not in PRESERVATION_ORDER and c not in ("B01", "B02", "B03", "X12")]
PRESERVATION_ORDER = PRESERVATION_ORDER + _rest
assert len(set(PRESERVATION_ORDER)) == len(PRESERVATION_ORDER)
assert set(PRESERVATION_ORDER) | {"B01", "B02", "B03", "X12"} == set(ALL)

INTEGRITY_FIRST = ["I02", "I03", "I06", "E01", "E02", "I01", "I07", "I04", "I05", "I08", "X02", "X03", "T01", "T02", "T04", "T05"]
CONF_CELLS = ("B01", "B02")
LATE_CELLS = ("B04", "X12", "B03")          # in this order: the world-model cell, the fresh clone, the ledgers last
TIERS = {"minimum": 1.0, "expanded": 1.5}

# the frozen useful expansion ladder (§12.4), re-sized from measured costs at the re-lock
EXPANSION_LADDER = [
    {"rung": 1, "axis": "independent_units", "what": "more independent worlds and makers", "cards": ["E03", "D01", "G01", "G02", "A01"]},
    {"rung": 2, "axis": "equivalence_worlds", "what": "more equivalence worlds for the class-coverage question", "cards": ["G01"]},
    {"rung": 3, "axis": "third_reader", "what": "the third reader size (Qwen2.5-0.5B) through the gates and the difference trunk", "cards": ["E02", "E03", "E04", "D01"]},
    {"rung": 4, "axis": "second_law_family", "what": "the second law family for the transfer attack", "cards": ["X11"]},
    {"rung": 5, "axis": "prefix_and_tail", "what": "longer prefixes and withheld tails", "cards": ["D01", "G02"]},
    {"rung": 6, "axis": "per_maker_adaptation", "what": "a small adapter on one maker's three earlier artifacts (the student of years), scored on the fourth, against FM+3", "cards": ["A03"]},
    {"rung": 7, "axis": "reveal_crossing", "what": "the reveal parameter crossing at power", "cards": ["A01", "A02"]},
    {"rung": 8, "axis": "confirmation_seeds", "what": "a second untouched confirmation lineage", "cards": ["B01"]},
]


def tier_factor() -> float:
    try:
        from soundingline.stage8 import read_registry                              # noqa: PLC0415
        w = read_registry("WORKLOAD_LOCK") or {}
        return float(w.get("tier_factor") or 1.0)
    except Exception:                                                             # noqa: BLE001
        return 1.0


def units_for(card: str, tier: str = "minimum", smoke: bool = False) -> int:
    n = ALL[card]["n_units"]
    if smoke:
        return min(n, 2 if ALL[card]["unit"] in ("audit", "analysis", "receipt", "ledger", "probe", "fixture", "training") else 3)
    try:
        mult = max(1.0, float(os.environ.get("S7_UNITS_MULT", "1")))
    except ValueError:
        mult = 1.0
    f = tier_factor() if ALL[card]["unit"] in ("world", "maker") else 1.0
    floor = 12 if ALL[card]["unit"] in ("world", "maker") else 1
    return max(floor if n >= floor else 1, int(round(n * TIERS.get(tier, 1.0) * mult * f)))


def est_minutes(card: str, tier: str = "minimum") -> float:
    s = ALL[card]
    return s["est_s_per_unit"] * units_for(card, tier) / 60.0


def identity_hash(card: str) -> str:
    import hashlib                                                                # noqa: PLC0415
    import json                                                                   # noqa: PLC0415
    return hashlib.sha256(json.dumps(ALL[card]["identity"], sort_keys=True).encode()).hexdigest()[:16]


def duplicate_identities() -> list[tuple[str, str]]:
    seen: dict = {}
    dup = []
    for c in ALL:
        h = identity_hash(c)
        if h in seen:
            dup.append((seen[h], c))
        seen[h] = c
    return dup
