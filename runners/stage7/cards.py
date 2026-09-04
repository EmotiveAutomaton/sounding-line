"""Stage 7 question registry (brief §9, §10, §11): the 100 mandatory questions and the 24
attacks with their questions, discriminators, engines, dependencies, factors, unit
counts, per-unit time assumptions, the evidence CONDITION each question runs (supplied
factors and form, regime, demonstrations, candidate laws), the arms it runs, and the
identity TUPLE (data lineage, supplied fields, withheld target, estimator, comparison,
statistic) whose hash the manifest uses to reject two nominal questions that reduce to
one data mapping and statistic (§9). ONE home for all of it. Every gate and its
expectation under the null and the alternative lives in the engine that runs the
question, not here.

DESIGN CHECK (2026-09-02)
lessons read: LESSONS §3, §5 (a library carries no gate of its own; every stage carries a
  produces guard; underestimate runtimes 2-3x: the estimates are conservative and the
  workload lock is sized from the measured pilot, never from these numbers; count the
  construction's identity space against the unit count: the identity tuple is the
  registry's own duplicate check).
gates: none in the registry; the expected-cell validator (I02) checks that removing any
  literal question, attack, factor corner, arm, reader, target, lineage, or output fails
  coverage, and the manifest (manifest.py) rejects duplicate identity hashes.
bands: none here; the engines' verdict bands are exhaustive and stated there.
"""

from __future__ import annotations

from soundingline.stage7 import ATTACKS as ATTACK_IDS, FACTORS, QUESTIONS as QUESTION_IDS

DOMAINS = ("essay", "workshop_doc")
RENDERS = ("prose", "log")
READERS = {"qwen": "Qwen/Qwen2.5-1.5B-Instruct", "smollm": "HuggingFaceTB/SmolLM2-1.7B-Instruct"}
SIZE_LADDER = {"qwen05": "Qwen/Qwen2.5-0.5B-Instruct", "qwen15": "Qwen/Qwen2.5-1.5B-Instruct",
               "qwen3": "Qwen/Qwen2.5-3B-Instruct", "qwen9b": "ollama:qwen3.5:9b"}
ALL7 = list(FACTORS)
TARGETS = ("next_action", "next_type", "next_section", "stop", "changed_context", "invalidation", "boundary_type", "tail")
ENGINES = ("isolation", "dependency", "supplied", "reconstruct", "architecture", "prospective", "history", "closure", "attack")
HISTORY_KINDS = ("human_then_model", "model_then_human", "alternating_normalized", "human_only", "model_only",
                 "style_matched_switch", "style_shift_no_switch")


def _cond(supplied: list[str] | None = None, form: str = "executable", regime: str = "cold", demos: int = 0,
          candidate_laws: bool = False, with_options: bool = True, with_brief: bool = True, twin: str | None = None,
          twin_values: tuple | None = None) -> dict:
    return {"supplied": list(supplied or []), "form": form, "regime": regime, "demos": demos,
            "candidate_laws": candidate_laws, "with_options": with_options, "with_brief": with_brief,
            "twin": twin, "twin_values": list(twin_values) if twin_values else None}


def _q(engine: str, question: str, discriminator: str, deps: list[str], gpu: bool, unit: str, n_units: int,
       est: float, identity: tuple, condition: dict | None = None, arms: list[str] | None = None,
       factors: dict | None = None, threshold: float | None = 0.03, primary: str | None = None,
       targets: tuple = ("next_action", "stop"), readers: list[str] | None = None) -> dict:
    assert engine in ENGINES, engine
    assert len(identity) == 6, identity
    return {"engine": engine, "question": question, "discriminator": discriminator, "depends_on": deps,
            "gpu": gpu, "unit": unit, "n_units": n_units, "est_s_per_unit": est,
            "identity": {"lineage": identity[0], "supplied": identity[1], "withheld_target": identity[2],
                         "estimator": identity[3], "comparison": identity[4], "statistic": identity[5]},
            "condition": condition or _cond(), "arms": arms or ["DIR"], "factors": factors or {},
            "threshold": threshold, "primary": primary or question, "targets": list(targets),
            "readers": readers or list(READERS)}


WITHOUT = {f: [x for x in ALL7 if x != f] for f in ALL7}
CEXT_BKGH = ["external_context", "belief_state", "expertise_law", "proximal_goal", "history_residue"]

QUESTIONS: dict[str, dict] = {
    # ── I: isolation, integrity, and execution gates (16) ─────────────────────────
    "I01": _q("isolation", "Do the reviewed repository heads, Stage 6 runtime anchors, and raw hashes reproduce?",
              "exact commit, runtime, cell-count, and file-hash receipt; mismatch blocks inheritance",
              [], False, "receipt", 1, 60.0, ("repo", "none", "none", "hash", "recorded_vs_live", "identity"), threshold=None),
    "I02": _q("isolation", "Does the manifest recursively enumerate all 100 questions, 24 attacks, factor corners, lineages, outputs, and closures?",
              "removing any literal item or expected corner fails coverage",
              [], False, "audit", 1, 60.0, ("manifest", "none", "none", "enumeration", "removal", "coverage"), threshold=None),
    "I03": _q("isolation", "Does VisibleEvidenceV1 contain only allowlisted fields for each rung?",
              "schema rejection of every undeclared field and nested object",
              ["I02"], False, "fixture", 24, 5.0, ("worlds_conf", "all_rungs", "none", "allowlist", "planted_field", "rejection_count"), threshold=None),
    "I04": _q("isolation", "Is the reader physically unable to import or read constructor and oracle state?",
              "forbidden import/open attempts fail inside the real reader process; access receipt clean",
              ["I03"], False, "probe", 1, 120.0, ("capsule", "none", "none", "probe", "attempts", "all_raised"), threshold=None),
    "I05": _q("isolation", "Does hidden-tail mutation leave every non-oracle prediction byte-identical?",
              "same visible-evidence hash, different future actions, exact canonical-output identity",
              ["I04"], True, "world", 12, 30.0, ("worlds_attack", "complete", "none", "canonical_bytes", "tail_twins", "identity_rate"),
              condition=_cond(ALL7), arms=["U", "PERS", "DOM", "SOL", "DIR", "SLJ"], threshold=None),
    "I06": _q("isolation", "Do hidden trajectory length, stop parameters, and stop outcomes leave non-oracle output unchanged?",
              "exact invariance across stop-tail twins",
              ["I04"], True, "world", 12, 30.0, ("worlds_attack", "complete", "none", "canonical_bytes", "stop_twins", "identity_rate"),
              condition=_cond(ALL7), arms=["U", "PERS", "DOM", "SOL", "DIR", "SLJ"], threshold=None),
    "I07": _q("isolation", "Do future cues, interruptions, source invalidations, and changed-context truth leave current output unchanged?",
              "exact invariance across hidden-event twins",
              ["I04"], True, "world", 12, 30.0, ("worlds_attack", "complete", "none", "canonical_bytes", "event_twins", "identity_rate"),
              condition=_cond(ALL7), arms=["U", "PERS", "DOM", "SOL", "DIR", "SLJ"], threshold=None),
    "I08": _q("isolation", "Does a diagnostic visible observation move the relevant prediction in the declared direction?",
              "sensitivity positive while I05-I07 remain invariant",
              ["I05", "I06", "I07"], True, "world", 12, 30.0, ("worlds_attack", "complete", "next_action", "tv", "visible_flip", "moved_rate"),
              condition=_cond(ALL7), arms=["DOM", "SOL", "DIR", "SLJ"], threshold=None),
    "I09": _q("isolation", "Are serialization, key order, whitespace, and opaque lineage relabeling irrelevant?",
              "canonical predictions stable; semantic evidence change still moves them",
              ["I04"], True, "world", 8, 30.0, ("worlds_attack", "complete", "none", "canonical_bytes", "serialization_twins", "identity_rate"),
              condition=_cond(ALL7), arms=["SOL", "DIR"], threshold=None),
    "I10": _q("isolation", "Are targets absent from filenames, identifiers, ordering, lengths, seeds, schemas, prompts, caches, and logs?",
              "planted canaries are caught and clean nulls remain at floor",
              ["I03"], False, "audit", 1, 300.0, ("worlds_conf", "all_rungs", "none", "canary_detector", "planted_vs_clean", "catch_rate_and_floor"), threshold=None),
    "I11": _q("isolation", "Does every reader emit normalized PredictionV1 objects with uncertainty, equivalence classes, and abstention?",
              "parser and probability identities pass on exact fixtures",
              ["I04"], False, "fixture", 12, 5.0, ("fixtures", "none", "none", "schema", "fixtures", "pass_count"), threshold=None),
    "I12": _q("isolation", "Do paired arms receive the same visible bytes and only their declared supplied factors?",
              "evidence-hash equality and field-difference receipt",
              ["I05"], False, "audit", 1, 120.0, ("rows", "none", "none", "evidence_sha", "paired_arms", "equality_rate"), threshold=None),
    "I13": _q("isolation", "Are compute, model calls, solver work, context, retries, and cache reuse recorded and constrained?",
              "budget ledger reconciles to process receipts",
              ["I05"], False, "audit", 1, 120.0, ("rows", "none", "none", "ledger", "capsule_vs_server", "reconciliation"), threshold=None),
    "I14": _q("isolation", "Are discovery, transfer, confirmation, conformance, and attack lineages descendant-clean?",
              "zero cross-split overlap under recursive lineage expansion",
              ["I02"], False, "audit", 1, 120.0, ("lineages", "none", "none", "descendant_expansion", "splits", "overlap_count"), threshold=None),
    "I15": _q("isolation", "Do checkpoint, kill/resume, atomic write, and produces guards prevent duplicate scientific units?",
              "forced interruption resumes once; row reordering and duplication do not move estimates",
              ["I05"], False, "audit", 1, 300.0, ("rows", "none", "none", "resume", "interrupt", "duplicate_count"), threshold=None),
    "I16": _q("isolation", "Does one keystone world pass a manual constructor-to-score audit before scale?",
              "signed checklist traces inputs, process access, model calls, output, truth lookup, and score",
              ["I05", "I08"], True, "world", 1, 300.0, ("worlds_conf", "complete", "next_action", "trace", "manual", "signed"),
              condition=_cond(ALL7), arms=["DIR", "SOL"], threshold=None),
    # ── D: Stage 6 dependency audit and data repair (10) ──────────────────────────
    "D01": _q("dependency", "Which Stage 6 predictions depended on hidden constructor fields?",
              "static and dynamic access graph from every scored output to source fields",
              [], False, "audit", 1, 600.0, ("stage6_code", "none", "none", "access_graph", "arms", "hidden_reach"), threshold=None),
    "D02": _q("dependency", "How much of the reported tournament gain is reproduced by equal mixing over privileged simulators, label weighting, and exact adaptation?",
              "recompute the audit decomposition from committed rows; no confirmatory language",
              ["D01"], False, "audit", 1, 1800.0, ("stage6_rows", "none", "none", "decomposition", "arms", "deltas"), threshold=None),
    "D03": _q("dependency", "Which Stage 6 cards remain clean after transitive dependency tracing?",
              "one disposition for every card and attack under the five audit classes",
              ["D01"], False, "audit", 1, 300.0, ("stage6_cards", "none", "none", "classification", "classes", "counts"), threshold=None),
    "D04": _q("dependency", "Do the architecture ranking, reader-boundary claim, M14, M15, and CoAuthor conclusion survive their dependency audit?",
              "expected starting disposition is suspension; restoration requires a clean independent path",
              ["D03"], False, "audit", 1, 120.0, ("stage6_conclusions", "none", "none", "suspension", "five_claims", "dispositions"), threshold=None),
    "D05": _q("dependency", "Can Stage 6's exact arm be renamed and isolated as supplied-law selection?",
              "reproduce exact likelihood identification without calling it law learning",
              ["D01"], False, "audit", 1, 900.0, ("stage6_rows", "none", "controller", "exact_posterior", "label_reader", "map_and_mass"), threshold=None),
    "D06": _q("dependency", "Which value and foraging questions shared identical worlds or statistics?",
              "implementation-identity matrix; duplicate estimands collapse to one evidential unit",
              ["D01"], False, "audit", 1, 300.0, ("stage6_rows", "none", "none", "vector_identity", "card_pairs", "identical_pairs"), threshold=None),
    "D07": _q("dependency", "Does the repaired CoAuthor loader record acceptance alongside applying suggestion-select deltas?",
              "known mini-logs recover accept, dismiss, reopen, edit, and ignore exactly",
              [], False, "fixture", 8, 5.0, ("coauthor_fixtures", "none", "decision", "loader", "fixtures", "exact_recovery"), threshold=None),
    "D08": _q("dependency", "What CoAuthor reconstruction claim is licensed by the source fields?",
              "validate only against independent fields actually present; reject invented final-text ground truth",
              ["D07"], False, "audit", 1, 600.0, ("coauthor", "none", "none", "field_inventory", "licensing", "consistency_rate"), threshold=None),
    "D09": _q("dependency", "Do the ScholaWrite and drawing negative results reproduce through reader-free, lineage-clean baselines?",
              "same narrow endpoints and strong sequential/spatial baselines; no contaminated realization path",
              ["D03"], False, "audit", 1, 600.0, ("stage6_records", "none", "none", "reader_free_baselines", "committed", "reproduction"), threshold=None),
    "D10": _q("dependency", "Is the Stage 6 correction written through findings, theory afterwords, state, and the dependency-audit artifact before Stage 7 begins?",
              "cross-file consistency, theory lint, multiplicity audit, and no surviving unqualified suspended claim",
              ["D04"], False, "audit", 1, 300.0, ("repo_docs", "none", "none", "grep_and_lint", "files", "consistency"), threshold=None),
    # ── K: supplied-state capability ladder (16) ──────────────────────────────────
    "K01": _q("supplied", "Can the exact oracle predict every hidden target in each known-answer world?",
              "nontrivial oracle gap on next action, stopping, and the declared counterfactual",
              ["I16"], False, "world", 240, 3.0, ("worlds_K", "none", "all", "oracle_minus_dom", "oracle_vs_dom", "gap_nats"),
              condition=_cond([]), arms=["U", "PERS", "DOM"], threshold=None, targets=TARGETS),   # 240: the stop gap (0.08 nats) needs the worlds, and the cell costs no model time
    "K02": _q("supplied", "How well do uniform, marginal, persistence, position, and opportunity-only baselines predict?",
              "frozen table at the independent-unit level",
              ["K01"], False, "world", 96, 3.0, ("worlds_K", "none", "all", "baselines", "table", "log_scores"),
              condition=_cond([]), arms=["U", "PERS"], threshold=None, targets=TARGETS),
    "K03": _q("supplied", "How well does the strongest common-domain process model predict without maker-specific state?",
              "held-out score and calibration; this is the primary cheap rival",
              ["K01"], False, "world", 96, 3.0, ("worlds_K", "none", "all", "dom", "held_out", "log_score_and_calibration"),
              condition=_cond([]), arms=["DOM"], threshold=None, targets=TARGETS),
    "K04": _q("supplied", "Can a reader use the complete executable C_m+B+K+A+G+H state to improve next action over DOM?",
              "positive U_state on untouched units with no generator access",
              ["K03"], True, "world", 48, 40.0, ("worlds_K", "all7_executable", "next_action", "dir", "dir_vs_dom", "u_state"),
              condition=_cond(ALL7, "executable"), arms=["DOM", "SOL", "DIR"]),
    "K05": _q("supplied", "Can the same reader use a complete natural-language rendering of that state?",
              "executable-versus-language interaction isolates interface loss",
              ["K04"], True, "world", 48, 40.0, ("worlds_K", "all7_language", "next_action", "dir", "language_vs_executable", "u_state_difference"),
              condition=_cond(ALL7, "language"), arms=["DOM", "DIR"]),
    "K06": _q("supplied", "What does supplied external and maker-interpreted context add by itself?",
              "context-only gain without hidden action law or goal",
              ["K04"], True, "world", 48, 40.0, ("worlds_K", "context_only", "next_action", "dir", "dir_vs_dom", "gain_nats"),
              condition=_cond(["external_context", "maker_context"]), arms=["DOM", "DIR"]),
    "K07": _q("supplied", "What does the true subjective action space add by itself?",
              "opportunity-conditioned gain; unavailable actions receive zero mass",
              ["K04"], True, "world", 48, 40.0, ("worlds_K", "action_space_only", "next_action", "dir", "dir_vs_dom_masked", "gain_and_unavailable_mass"),
              condition=_cond(["subjective_action_space"]), arms=["DOM", "DIR"]),
    "K08": _q("supplied", "What does the true expertise/transition law add by itself?",
              "law-conditioned gain beyond DOM, without a truth tag",
              ["K04"], True, "world", 48, 40.0, ("worlds_K", "law_only", "next_action", "dir", "dir_vs_dom", "gain_nats"),
              condition=_cond(["expertise_law"]), arms=["DOM", "DIR"]),
    "K09": _q("supplied", "What does the true belief/information state add by itself?",
              "belief-swap worlds with identical objective state and action law",
              ["K04"], True, "world_pair", 32, 60.0, ("worlds_K_belief_twins", "belief_only", "next_action", "dir", "twin_contrast", "gain_and_reversal"),
              condition=_cond(["belief_state"], twin="belief"), arms=["DOM", "DIR"]),
    "K10": _q("supplied", "What does the true proximal goal add by itself?",
              "goal-swap worlds with matched prefix and surface",
              ["K04"], True, "world_pair", 32, 60.0, ("worlds_K_goal_twins", "goal_only", "next_action", "dir", "twin_contrast", "gain_and_reversal"),
              condition=_cond(["proximal_goal"], twin="goal"), arms=["DOM", "DIR"]),
    "K11": _q("supplied", "With C_m+B+K+A+H supplied, can the reader infer only G and preserve prospective gain?",
              "goal posterior plus hidden-action score; classification alone cannot pass",
              ["K04"], True, "world", 48, 60.0, ("worlds_K", "all_but_goal", "goal_and_next_action", "slj", "slj_vs_dom_and_dir", "posterior_and_gain"),
              condition=_cond(WITHOUT["proximal_goal"]), arms=["DOM", "DIR", "SLJ"]),
    "K12": _q("supplied", "With C_m+K+A+G+H supplied, can it infer only B?",
              "false-belief collision resolved by later action",
              ["K04"], True, "world_pair", 32, 60.0, ("worlds_K_belief_twins", "all_but_belief", "belief_and_next_action", "slj", "twin_contrast", "posterior_and_gain"),
              condition=_cond(WITHOUT["belief_state"], twin="belief"), arms=["DOM", "DIR", "SLJ"]),
    "K13": _q("supplied", "With C_ext+B+K+G+H supplied, can it reconstruct A?",
              "objective-versus-subjective option mismatch and correct refusal of unavailable choices",
              ["K04"], True, "world", 48, 60.0, ("worlds_K", "cext_bkgh", "action_space_and_next_action", "slj", "slj_vs_dir", "precision_recall_and_unavailable_mass"),
              condition=_cond(CEXT_BKGH), arms=["DOM", "DIR", "SLJ"]),
    "K14": _q("supplied", "With C_m+B+A+G+H supplied plus demonstrations, can it infer the missing expertise law?",
              "held-out action under a new state; selecting a listed law is scored separately",
              ["K04"], True, "world", 48, 80.0, ("worlds_K", "all_but_law_plus_demos", "law_and_next_action", "learn_slj_kl", "learned_vs_selected_vs_dir", "gain_nats"),
              condition=_cond(WITHOUT["expertise_law"], demos=2, candidate_laws=True), arms=["DOM", "DIR", "SLJ", "LEARN", "KL"]),
    "K15": _q("supplied", "Can the complete state improve continuation/stopping when the stop law genuinely depends on maker state?",
              "proper hazard gain over matched progress/length/deadline baselines",
              ["K04"], True, "world", 48, 40.0, ("worlds_K", "all7_executable", "stop", "dir_sol", "vs_progress_baselines", "hazard_gain"),
              condition=_cond(ALL7), arms=["PERS", "DOM", "SOL", "DIR"], targets=("stop",)),
    "K16": _q("supplied", "Conditional on K04, how do structured computation, inference-time compute, and model size affect state use?",
              "factorial interaction, not three incomparable runs; if K04 fails, this diagnoses rather than rescues it",
              ["K04"], True, "world", 32, 120.0, ("worlds_K", "all7_executable", "next_action", "dir_dirs_by_size_by_compute", "factorial", "u_state_cells"),
              condition=_cond(ALL7), arms=["DIR", "DIRS"], factors={"size": list(SIZE_LADDER), "compute": ["small", "expanded"]},
              readers=list(SIZE_LADDER.values())),
    # ── R: maker-factor reconstruction ladder (16) ────────────────────────────────
    "R01": _q("reconstruct", "Does candidate generation include the true/equivalent proximal goal before selection?",
              "goal-set recall and redundancy, separated from posterior ranking",
              ["K11"], True, "world", 48, 30.0, ("worlds_R", "all_but_goal", "goal", "proposals", "truth_in_set", "recall_and_redundancy"),
              condition=_cond(WITHOUT["proximal_goal"]), arms=["SLJ"], threshold=None),
    "R02": _q("reconstruct", "Does it include the true/equivalent belief state?",
              "belief-set recall on false-belief and missing-information fixtures",
              ["K12"], True, "world", 48, 30.0, ("worlds_R", "all_but_belief", "belief", "proposals", "truth_in_set", "recall_and_redundancy"),
              condition=_cond(WITHOUT["belief_state"]), arms=["SLJ"], threshold=None),
    "R03": _q("reconstruct", "Does it include a behaviorally equivalent expertise law not named in the prompt?",
              "law-set recall under executable equivalence tests",
              ["K14"], True, "world", 48, 30.0, ("worlds_R", "all_but_law", "law", "proposals", "behavioral_equivalence", "recall_and_redundancy"),
              condition=_cond(WITHOUT["expertise_law"]), arms=["SLJ"], threshold=None),
    "R04": _q("reconstruct", "Does it reconstruct the maker's subjective action space rather than repeat the objective list?",
              "precision/recall over A, with impossible and unnoticed actions crossed",
              ["K13"], True, "world", 48, 30.0, ("worlds_R", "cext_bkgh", "action_space", "proposals", "vs_objective_list", "precision_recall"),
              condition=_cond(CEXT_BKGH), arms=["SLJ"], threshold=None),
    "R05": _q("reconstruct", "Does it reconstruct maker-interpreted context rather than copy external context?",
              "correct differences caused by belief and expertise",
              ["K04"], True, "world", 48, 30.0, ("worlds_R", "cext_b_k_g_h_no_cm", "maker_context", "proposals", "vs_copied_context", "difference_recall"),
              condition=_cond(["external_context", "belief_state", "expertise_law", "proximal_goal", "history_residue"]), arms=["SLJ"], threshold=None),
    "R06": _q("reconstruct", "With all other factors supplied, does inferred G recover the K11 prospective advantage?",
              "R_G against supplied-goal ceiling",
              ["K11", "K04"], False, "analysis", 1, 300.0, ("rows_K11_K04", "all_but_goal", "next_action", "ratio", "slj_vs_supplied", "r_ratio"), threshold=None),
    "R07": _q("reconstruct", "With all other factors supplied, does inferred B recover the K12 advantage?",
              "R_B on hidden future and counterfactual",
              ["K12", "K04"], False, "analysis", 1, 300.0, ("rows_K12_K04", "all_but_belief", "next_action_and_changed_context", "ratio", "slj_vs_supplied", "r_ratio"), threshold=None),
    "R08": _q("reconstruct", "With all other factors supplied, does inferred A recover the K13 advantage?",
              "R_A and zero mass on subjectively unavailable actions",
              ["K13", "K04"], False, "analysis", 1, 300.0, ("rows_K13_K04", "cext_bkgh", "next_action", "ratio", "slj_vs_supplied", "r_ratio_and_unavailable_mass"), threshold=None),
    "R09": _q("reconstruct", "Can K be learned from demonstrations or earlier artifacts and transfer to an untouched episode?",
              "new-state prediction; no supplied candidate law",
              ["K14"], True, "world", 48, 60.0, ("worlds_R_untouched", "all_but_law_plus_demos_no_candidates", "next_action", "learn", "learn_vs_kl_vs_dom", "gain_nats"),
              condition=_cond(WITHOUT["expertise_law"], demos=3, candidate_laws=False), arms=["DOM", "DIR", "LEARN", "SLJ"]),
    "R10": _q("reconstruct", "Can C_m be inferred from artifact/source evidence and improve a later choice?",
              "context reconstruction beyond topic/style and copied biography",
              ["R05"], True, "world", 48, 60.0, ("worlds_R", "cext_b_k_g_h_no_cm", "changed_context", "slj", "slj_vs_copied_context_arm", "gain_nats"),
              condition=_cond(["external_context", "belief_state", "expertise_law", "proximal_goal", "history_residue"]), arms=["DOM", "DIR", "SLJ"],
              targets=("next_action", "changed_context")),
    "R11": _q("reconstruct", "Can G and B be inferred jointly without collapsing one into the other?",
              "crossed goal/belief worlds and both component posteriors",
              ["K11", "K12"], True, "world", 48, 80.0, ("worlds_R_crossed", "all_but_goal_belief", "goal_belief_next_action", "slj", "component_marginals", "both_posteriors_and_gain"),
              condition=_cond([f for f in ALL7 if f not in ("proximal_goal", "belief_state")]), arms=["DOM", "DIR", "SLJ"]),
    "R12": _q("reconstruct", "Can K and A be inferred jointly without treating objective opportunity as competence?",
              "expertise/action-space swaps with identical observed prefix",
              ["K13", "K14"], True, "world", 48, 80.0, ("worlds_R_swaps", "cext_b_g_h", "law_action_space_next_action", "slj", "swap_contrast", "both_posteriors_and_gain"),
              condition=_cond(["external_context", "belief_state", "proximal_goal", "history_residue"]), arms=["DOM", "DIR", "SLJ"]),
    "R13": _q("reconstruct", "Can the full factor set be inferred jointly from visible evidence and improve prediction over DOM and DIR?",
              "all-factor posterior plus prospective score; no credit borrowed from oracle fields",
              ["R11", "R12"], True, "world", 48, 120.0, ("worlds_R", "none_cold", "all_and_next_action", "slj", "slj_vs_dom_and_dir", "gain_nats"),
              condition=_cond([]), arms=["DOM", "DIR", "SLJ"],
              # every target the P analyses read from these rows (P01 to P08): an unasked target is filled uniform
              targets=("next_action", "next_type", "next_section", "stop", "changed_context", "invalidation", "boundary_type")),
    "R14": _q("reconstruct", "Does maker familiarity help where cold reading fails, independently of domain expertise?",
              "cold x domain-expert x maker-familiar crossing on the same targets",
              ["R13"], True, "world", 32, 150.0, ("worlds_R", "regime_crossed", "next_action", "slj_dir", "regime_cells", "gain_by_regime"),
              condition=_cond([]), arms=["DOM", "DIR", "SLJ"], factors={"regime": ["cold", "domain_expert", "maker_familiar"]}),
    "R15": _q("reconstruct", "Does domain expertise help reconstruct feasible processes without falsely increasing maker certainty?",
              "better action-law prediction with calibrated maker-factor uncertainty",
              ["R14"], False, "analysis", 1, 300.0, ("rows_R14", "regime_crossed", "law_and_next_action", "entropy_and_gain", "domain_expert_vs_cold", "gain_and_marginal_entropy"), threshold=None),
    "R16": _q("reconstruct", "Does the reader preserve observationally equivalent maker models and choose a useful next discriminator?",
              "equivalence-class coverage, abstention, and expected information per cost",
              ["R13"], True, "world", 48, 60.0, ("worlds_R_equivalence", "none_cold", "class_and_probe", "slj", "class_coverage_and_eig", "coverage_and_eig_ratio"),
              condition=_cond([]), arms=["SLJ"], threshold=None),
    # ── A: architecture conformance and compute decomposition (16) ────────────────
    "A01": _q("architecture", "Are every external source, paper version, repository commit, license, and borrowed component pinned before use?",
              "complete source and assumption manifest; no floating branch at scientific time",
              [], False, "audit", 1, 120.0, ("sources", "none", "none", "manifest", "pinned", "all_pinned"), threshold=None),
    "A02": _q("architecture", "Can external reference code run only in its sealed conformance workspace without access to Stage 7 science or confirmation data?",
              "read-only clone, network/data boundary, and access receipt",
              ["A01"], False, "audit", 1, 120.0, ("sources", "none", "none", "sealed", "workspace", "sealed_flag"), threshold=None),
    "A03": _q("architecture", "Does the LAIP-style arm generate hypotheses and likelihood functions, then compute the Bayesian posterior externally?",
              "tiny paper-style fixture; a fixed label-weighting shortcut fails conformance",
              ["A02"], False, "fixture", 1, 120.0, ("fixture_laip", "none", "none", "operations", "should_break", "pass"), threshold=None),
    "A04": _q("architecture", "Does ThoughtTracing preprocessing recover state, action, and perception steps on an official-style example?",
              "step sequence matches the fixture before hypothesis inference",
              ["A02"], False, "fixture", 1, 120.0, ("fixture_tt_preprocess", "none", "none", "operations", "official_example", "pass"), threshold=None),
    "A05": _q("architecture", "Does the ThoughtTracing arm initialize, propagate, weight, ESS-resample, and diversity-rejuvenate hypotheses?",
              "each defining operation fires on a designed fixture and leaves a receipt",
              ["A04"], False, "fixture", 1, 120.0, ("fixture_tt_particles", "none", "none", "operations", "receipt", "pass"), threshold=None),
    "A06": _q("architecture", "Does the ThoughtTracing posterior recover after contradiction without fabricated full importance weights?",
              "sequential posterior, ESS, diversity, and recovery trace",
              ["A05"], False, "fixture", 1, 120.0, ("fixture_tt_recovery", "none", "none", "operations", "contradiction", "pass"), threshold=None),
    "A07": _q("architecture", "Does AutoToM propose an initial agent-model structure and explicit local conditionals?",
              "causal variables and factorization reproduce an official-style fixture",
              ["A02"], False, "fixture", 1, 120.0, ("fixture_autotom_initial", "none", "none", "operations", "official_example", "pass"), threshold=None),
    "A08": _q("architecture", "Does AutoToM-style utility add a genuinely missing latent and reject false expansion in a complete world?",
              "missing-variable gain x complete-world cost interaction",
              ["A07"], True, "world", 24, 60.0, ("worlds_A_missing_vs_complete", "goal_only_start", "next_action", "adaptive_factor_expansion", "missing_vs_complete", "added_factors_and_gain"),
              condition=_cond(["external_context"]), arms=["adaptive_factor_expansion", "SLJ"], factors={"world_completeness": ["complete", "missing_variable"]}),
    "A09": _q("architecture", "Does AutoToM extend the time window only when the current window remains insufficient?",
              "earlier-evidence fixture and no gratuitous extension control",
              ["A07"], False, "fixture", 1, 120.0, ("fixture_autotom_window", "none", "none", "operations", "extension_control", "pass"), threshold=None),
    "A10": _q("architecture", "Does the LIRAS-style reproduction synthesize a valid situation-specific environment/action model?",
              "syntax and semantic execution checks; paper-reproduction label retained",
              ["A02"], False, "fixture", 1, 120.0, ("fixture_liras", "none", "none", "operations", "validation", "pass"), threshold=None),
    "A11": _q("architecture", "Does it synthesize the agent model, parse observations/actions, and run inverse inference over that model?",
              "end-to-end official-style fixture; direct-answer ablation included",
              ["A10"], True, "world", 24, 60.0, ("worlds_A", "cext_only", "next_action", "synthesized_agent_model", "vs_dir_ablation", "gain_nats"),
              condition=_cond(["external_context"]), arms=["DIR", "synthesized_agent_model"]),
    "A12": _q("architecture", "Does InversePlanning.jl or an exact independently checked equivalent reproduce the known-law posterior?",
              "analytic tiny-world posterior and bounded-rational action likelihood",
              ["A02"], False, "fixture", 1, 120.0, ("fixture_inverse_planning", "none", "none", "operations", "analytic", "pass"), threshold=None),
    "A13": _q("architecture", "Does LaBToM-style epistemic translation preserve belief content and change inference when that content changes?",
              "valid compositional representation plus belief-sensitive posterior",
              ["A02"], False, "fixture", 1, 120.0, ("fixture_labtom", "none", "none", "operations", "belief_flip", "pass"), threshold=None),
    "A14": _q("architecture", "Does the Sounding joint reader revise mutually constraining factor hypotheses rather than produce a longer rationale?",
              "executable factor graph, posterior updates, and predictions at each revision",
              ["R11"], True, "world", 24, 90.0, ("worlds_A_revision", "all_but_goal_belief", "goal_belief_next_action", "slj_checkpoints", "revision_trace", "update_count_and_gain"),
              condition=_cond([f for f in ALL7 if f not in ("proximal_goal", "belief_state")]), arms=["SLJ", "sequential_hypothesis_particles"], threshold=None),
    "A15": _q("architecture", "At matched evidence and measured compute, does structured computation beat direct inference-time computation?",
              "same base model and targets; calls, tokens, solver operations, and wall time reported",
              ["R13"], True, "world", 32, 120.0, ("worlds_A", "none_cold", "next_action", "structured_vs_direct", "matched_evidence_priced_compute", "gain_per_compute"),
              condition=_cond([]), arms=["DIR", "SLJ", "weighted_language_hypotheses", "sequential_hypothesis_particles", "adaptive_factor_expansion", "synthesized_agent_model", "epistemic_translation"]),
    "A16": _q("architecture", "Conditional on the supplied-state gate, does a larger local model improve factor use or only verbal proposal quality?",
              "Qwen2.5 0.5B/1.5B/3B and the Ollama Qwen3.5 9B route where probability interfaces are comparable; family and interface caveats explicit",
              ["K04", "R01"], True, "world", 24, 150.0, ("worlds_A_size", "all7_and_all_but_goal", "next_action_and_goal_recall", "dir_slj_by_size", "size_cells", "u_state_and_recall_by_size"),
              condition=_cond(ALL7), arms=["DIR", "SLJ"], factors={"size": list(SIZE_LADDER)}, readers=list(SIZE_LADDER.values())),
    # ── P: prospective and ecological bridge (14) ─────────────────────────────────
    "P01": _q("prospective", "Can the reader predict the exact next feasible action?",
              "proper score against DOM, with the live option set enforced",
              ["R13"], False, "analysis", 1, 300.0, ("rows_R13", "none_cold", "next_action", "paired_ls", "arms_vs_dom", "gain_nats"), threshold=0.03),
    "P02": _q("prospective", "Can it predict next edit type?",
              "beat persistence and domain marginals on held-out worlds/sessions",
              ["R13"], False, "analysis", 1, 300.0, ("rows_R13", "none_cold", "next_type", "paired_ls", "arms_vs_pers_dom", "gain_nats")),
    "P03": _q("prospective", "Can it predict location and scope of the next edit?",
              "hierarchical proper score against position and section priors",
              ["R13"], False, "analysis", 1, 300.0, ("rows_R13", "none_cold", "next_section_and_slot", "hierarchical_ls", "arms_vs_position_prior", "gain_nats")),
    "P04": _q("prospective", "Can it predict which available alternative the maker rejects?",
              "opportunity-conditioned choice score; unavailable options excluded",
              ["R13"], False, "analysis", 1, 300.0, ("rows_R13", "none_cold", "rejected_alternative", "pairwise_choice_ls", "arms_vs_dom", "gain_nats")),
    "P05": _q("prospective", "Can it predict continuation versus stopping at a real decision boundary?",
              "discrete-time hazard score with censoring and matched progress/length",
              ["R13", "K15"], False, "analysis", 1, 300.0, ("rows_R13_K15", "none_cold_and_complete", "stop", "hazard_ls", "arms_vs_progress_baselines", "gain_nats")),
    "P06": _q("prospective", "Can it distinguish satisfaction, deadline, and fatigue boundaries or abstain when they are equivalent?",
              "boundary-type posterior and resumption counterfactual; no generic human claim",
              ["R13"], False, "analysis", 1, 300.0, ("rows_R13", "none_cold", "boundary_type_and_resumption", "ls_and_abstention", "arms_vs_dom", "gain_and_equivalent_abstention")),
    "P07": _q("prospective", "Can it predict a later action after a context or opportunity change?",
              "changed-context proper score from the same maker law",
              ["R13"], False, "analysis", 1, 300.0, ("rows_R13", "none_cold", "changed_context", "paired_ls", "arms_vs_dom", "gain_nats")),
    "P08": _q("prospective", "Can it predict response to a later-invalidated source without treating this as the product target?",
              "correction/retention/rewrite distribution; secondary consequence only",
              ["R13"], False, "analysis", 1, 300.0, ("rows_R13", "none_cold", "invalidation", "paired_ls", "arms_vs_dom", "gain_nats")),
    "P09": _q("prospective", "Does the model improve the whole withheld tail rather than one queried event?",
              "sum of per-event proper scores plus localization audit",
              ["R13"], True, "world", 32, 60.0, ("worlds_P_tail", "none_cold", "tail", "sequential_ls", "slj_dom_vs_dir", "tail_sum_and_localization"),
              condition=_cond([]), arms=["DOM", "SLJ", "DIR"], targets=("tail",)),
    "P10": _q("prospective", "Is uncertainty calibrated across evidence dose, contradiction, and exact equifinality?",
              "reliability, risk-coverage, and class coverage",
              ["P01", "P05", "R16"], False, "analysis", 1, 600.0, ("rows_R13_R16", "none_cold", "confidence", "calibration", "dose_cells", "ece_slope_coverage"), threshold=None),
    "P11": _q("prospective", "Can it localize a known human/model control change in a held-out revision history?",
              "change-point log score and boundary error against process records",
              ["I16"], True, "history", 40, 30.0, ("histories_P", "process_log", "change_point", "hproc_hdir", "vs_style_pers_stack", "cp_ls_and_boundary_error"),
              condition=_cond([]), arms=["HU", "HSTYLE", "HPERS", "HSTACK", "HPROC", "HDIR"],
              factors={"kind": ["human_then_model", "model_then_human", "alternating_normalized", "human_only", "model_only"]}, targets=("change_point",)),
    "P12": _q("prospective", "Does discontinuity localization survive surface normalization and defeat stylometry-only rivals?",
              "style-matched discontinuity and style-shifted no-discontinuity crossover",
              ["P11"], True, "history", 40, 30.0, ("histories_P_adversary", "process_log_and_final_only", "change_point", "hproc_hdir", "crossover", "cp_ls_by_kind_and_interface"),
              condition=_cond([]), arms=["HU", "HSTYLE", "HPERS", "HSTACK", "HPROC", "HDIR"],
              factors={"kind": ["style_matched_switch", "style_shift_no_switch"], "interface": ["process", "final_only"]}, targets=("change_point",)),
    "P13": _q("prospective", "After loader repair, can CoAuthor suggestion accept/edit/reject behavior be predicted beyond position and prior-decision baselines?",
              "session-held-out choice score; state reconstruction gate first",
              ["D07", "D08"], True, "session", 48, 40.0, ("coauthor_sessions", "doc_tail_and_suggestion", "decision", "dir", "vs_position_and_prior_decision", "gain_nats"),
              condition=_cond([]), arms=["CU", "CPOS", "CPRIOR", "CDIR"], targets=("decision",)),
    "P14": _q("prospective", "In ScholaWrite, can the reader predict the moment and direction of a goal switch rather than win on label persistence?",
              "switch-conditioned score under leave-project-out and leave-author-out splits",
              ["D09"], True, "session", 40, 40.0, ("scholawrite_sessions", "event_window", "next_category_switch", "dir", "vs_persistence", "switch_conditioned_gain"),
              condition=_cond([]), arms=["SU", "SPERS", "SDIR"], factors={"protocol": ["leave_project_out", "leave_author_out"]}, targets=("switch",)),
    # ── V: bounded attention/history/preference stress tests (6) ──────────────────
    "V01": _q("history", "Can trained automatic capture be separated from current costly redirection?",
              "same capture tendency, crossed redirection cost/choice; present choice and compiled residue scored separately",
              ["K11"], True, "world", 32, 80.0, ("worlds_V_capture", "all_but_goal_residue", "goal_residue_next_action", "slj", "crossed_cells", "both_marginals_and_gain"),
              condition=_cond([f for f in ALL7 if f not in ("proximal_goal", "history_residue")]), arms=["DOM", "SLJ"],
              factors={"residue": ["habit_check", "habit_write"], "goal_opposes": ["yes", "no"]}),
    "V02": _q("history", "After context and functional competence are matched, does current allocation/redirection predict the next local choice?",
              "prospective choice, not an unexplained residual relabeled preference",
              ["K11"], True, "world", 32, 60.0, ("worlds_V", "all_but_goal", "next_action", "slj_vs_goal_blind_mixture", "matched_context_and_law", "gain_nats"),
              condition=_cond(WITHOUT["proximal_goal"]), arms=["GBLIND", "SLJ"]),
    "V03": _q("history", "Can lagging expertise oppose a current proximal goal without either being erased from the maker model?",
              "goal x expertise conflict and diagnostic future action",
              ["K11", "K14"], True, "world", 32, 80.0, ("worlds_V_conflict", "all_but_goal_law", "goal_law_next_action", "slj", "conflict_cells", "both_marginals_and_gain"),
              condition=_cond([f for f in ALL7 if f not in ("proximal_goal", "expertise_law")]), arms=["DOM", "SLJ"],
              factors={"conflict": ["opposed", "aligned"]}),
    "V04": _q("history", "Does one artifact support a dated present focus plus an uncertain historical mixture, rather than two clean time points?",
              "posterior age/mixture calibration on known histories; forced point dating is penalized",
              ["K14"], True, "world", 32, 90.0, ("worlds_V_dated", "dated_demos", "present_law_and_mixture", "dated_mixture", "vs_point_dating", "mixture_ls_and_calibration"),
              condition=_cond(WITHOUT["expertise_law"], demos=4), arms=["POINT", "MIX"], threshold=None),
    "V05": _q("history", "Do multiple dated artifacts improve trajectory prediction over an aggregate expertise/style profile?",
              "held-out later episode; dated versus ordered-undated versus aggregate comparison",
              ["V04"], True, "world", 32, 90.0, ("worlds_V_dated", "dated_demos", "next_action_later_episode", "dated_vs_ordered_vs_aggregate", "history_view_cells", "gain_by_view"),
              condition=_cond(WITHOUT["expertise_law"], demos=4), arms=["AGG", "ORDERED", "DATED"], factors={"history_view": ["dated", "ordered", "aggregate"]}),
    "V06": _q("history", "Does any inferred trajectory predict a later costly choice beyond context, proximal goal, identity, topic, and expertise baselines?",
              "fresh-context proper score; no second-derivative or precision claim",
              ["V05"], True, "world", 32, 90.0, ("worlds_V_dated", "dated_demos", "changed_context_fresh_episode", "dated", "vs_context_goal_law_baselines", "gain_nats"),
              condition=_cond(WITHOUT["expertise_law"], demos=4), arms=["AGG", "DATED", "SOL"], targets=("changed_context",)),
    # ── B: confirmation, closure, and reporting (6) ───────────────────────────────
    "B01": _q("closure", "Does the strongest supplied-state capability effect replicate on untouched worlds?",
              "frozen K-rung estimand, state rendering, reader, and strong baseline",
              [], True, "world", 48, 40.0, ("worlds_confirmation", "frozen", "frozen", "frozen", "frozen", "frozen")),
    "B02": _q("closure", "Does the strongest qualified reconstruction or architecture effect replicate on untouched lineages?",
              "conformance-passed arm, same evidence/compute, no endpoint substitution",
              ["B01"], True, "world", 48, 60.0, ("worlds_confirmation_2", "frozen", "frozen", "frozen", "frozen", "frozen")),
    "B03": _q("closure", "Does process-discontinuity localization replicate on untouched mixed-control histories?",
              "frozen change-point score and stylometric adversaries",
              ["B02"], True, "history", 40, 30.0, ("histories_confirmation", "process_log", "change_point", "frozen", "frozen", "frozen")),
    "B04": _q("closure", "What, if anything, can be read from completed Ghost V15 without importing partial evidence?",
              "status/hash bridge only unless V15 has a final validated packet; no automatic V16",
              [], False, "ledger", 1, 120.0, ("ghost", "none", "none", "receipt", "status", "bridge"), threshold=None),
    "B05": _q("closure", "Do coverage, source, access, compute, pursuit, warrant, dependency, and claim ledgers agree?",
              "machine reconciliation and clean-clone validation",
              ["B04"], False, "audit", 1, 600.0, ("ledgers", "none", "none", "reconciliation", "ledgers", "agreement"), threshold=None),
    "B06": _q("closure", "What moves in the project world model, and should a Stage 8, human bridge, or product confirmation open?",
              "one final two-pass curator packet and explicit curator ruling; no automatic continuation",
              ["B05"], False, "analysis", 1, 900.0, ("verdicts", "none", "none", "closure", "routing", "packet_inputs"), threshold=None),
}
assert set(QUESTIONS) == set(QUESTION_IDS), (set(QUESTION_IDS) ^ set(QUESTIONS))


def _x(covers: list[str], attack: str, expect: str, consequence: str, gpu: bool = False,
       unit: str = "derived", n_units: int = 1, est: float = 300.0, arms: list[str] | None = None,
       condition: dict | None = None) -> dict:
    return {"engine": "attack", "covers": covers, "question": attack, "discriminator": expect,
            "consequence": consequence, "depends_on": [c for c in covers if c in QUESTIONS][:3],
            "gpu": gpu, "unit": unit, "n_units": n_units, "est_s_per_unit": est,
            "factors": {}, "threshold": None, "primary": attack, "arms": arms or [], "condition": condition or _cond(ALL7),
            "identity": {"lineage": f"attack_{attack[:24]}", "supplied": "as_covered", "withheld_target": "as_covered",
                         "estimator": "attack", "comparison": expect[:40], "statistic": consequence[:40]},
            "targets": ["next_action", "stop"], "readers": list(READERS)}


ATTACKS: dict[str, dict] = {
    "X01": _x(["I05", "K04", "R13"], "Replace the entire hidden future while holding visible bytes fixed.", "byte-identical non-oracle predictions", "any non-oracle movement voids every affected result"),
    "X02": _x(["I06", "K15", "P05"], "Replace hidden length, stopping parameters, and stop outcome.", "byte-identical non-oracle predictions", "any movement voids stopping and state-use claims"),
    "X03": _x(["I07", "P07", "P08"], "Replace future cues, interruptions, invalidations, and changed-context truth.", "byte-identical non-oracle predictions", "any movement voids current and counterfactual claims"),
    "X04": _x(["I04"], "Attempt forbidden imports, file opens, environment reads, cache reads, and callbacks from the reader process.", "every attempt raises", "successful access blocks the scientific lock"),
    "X05": _x(["I09", "I10"], "Permute filenames, opaque IDs, source order, seeds, path lengths, and output paths.", "semantic results invariant", "an identifier-driven result is a leak"),
    "X06": _x(["K04", "R13"], "Permute answer, action, and candidate order with fixed-order paired scoring.", "posterior and prediction invariant within tolerance", "an order-driven contrast is re-run under fixed order", True, "world", 12, 40.0, ["DIR", "SLJ"]),
    "X07": _x(["I08"], "Change one diagnostic visible observation while preserving hidden truth.", "the relevant prediction moves", "global invariance fails the reader"),
    "X08": _x(["I12"], "Hash paired-arm evidence and remove any undeclared field advantage.", "equal evidence bytes across paired arms", "unequal evidence voids the comparison"),
    "X09": _x(["I13", "A15"], "Equalize or explicitly price model calls, tokens, context, solver work, retries, cache, and wall time.", "priced compute on every arm", "unpriced compute forbids an efficiency or architecture claim"),
    "X10": _x(["K05"], "Paraphrase prompts, state descriptions, and serialization without changing operative meaning.", "behavior stable where semantics are preserved", "an unstable reader's language-state claims close", True, "world", 12, 40.0, ["DIR"], _cond(ALL7, "language")),
    "X11": _x(["K05", "K09"], "Change operative meaning while matching length, fluency, specificity, and confidence language.", "the prediction changes in the declared direction", "a meaning-blind reader fails", True, "world", 12, 40.0, ["DIR"], _cond(ALL7, "language")),
    "X12": _x(["R13", "K11"], "Duplicate or paraphrase evidence from one causal source.", "confidence does not sharpen as if observations were independent", "the double-count defect closes the affected posterior claims", True, "world", 12, 60.0, ["SLJ"], _cond(WITHOUT["proximal_goal"])),
    "X13": _x(["K14", "R09"], "Relabel supplied laws and candidate hypotheses while preserving executable behavior.", "selection follows behavior, not tags", "a tag-driven selector is renamed", False, "world", 24, 5.0, ["KL"], _cond(WITHOUT["expertise_law"], candidate_laws=True)),
    "X14": _x(["R16", "P10"], "Hold the final artifact and visible prefix fixed while swapping valid hidden histories.", "the reader preserves the equivalence class", "forced point accuracy on equifinal classes voids the cell"),
    "X15": _x(["K13", "R04"], "Swap objective and subjective action spaces while holding the observed choice fixed.", "availability, selection, and competence distinguished", "an opportunity-blind reading closes"),
    "X16": _x(["K09", "K12"], "Swap maker beliefs while holding objective facts, goal, and law fixed.", "belief-sensitive futures reverse; copied-world inference fails", "a copied-world reader fails"),
    "X17": _x(["K08", "K14"], "Swap expertise/action laws while matching observed prefix, endpoint, and surface.", "future-action predictions follow the law only when evidence supports it", "a law-blind reading is bounded"),
    "X18": _x(["K10", "K11"], "Swap proximal goals while matching belief, expertise, prefix, and endpoint.", "the goal-sensitive diagnostic event reverses", "a goal-blind reading is bounded"),
    "X19": _x(["V02", "V06"], "Swap context, cost, opportunity, or audience while holding standing tendency fixed.", "context effects are not reported as preference change", "context-blind attribution is a defect"),
    "X20": _x(["K03", "R13"], "Strengthen persistence, position, grammar, genre, and opportunity baselines.", "maker claims require gain beyond the frozen common-process rival", "a claim under the strengthened rival is renamed"),
    "X21": _x(["R14", "A16"], "Transfer across reader size/family, maker family, domain, and evidence regime.", "conditional failures reported before pooling", "a pooled rescue is refused"),
    "X22": _x(["P12"], "Normalize style around a real human/model switch and create a style switch without a control switch.", "the discontinuity reader follows process, not surface register", "a style detector is renamed as such"),
    "X23": _x(["I15", "I14"], "Duplicate/reorder rows, leak descendants across splits, and construct planned sign reversals.", "independent-unit estimates stable; pooled masking detected", "a pooled mean over a planned reversal blocks the packet"),
    "X24": _x(["B05"], "Fresh-clone every manifest, source hash, access receipt, completion state, confirmation input, and report dependency; force kill/resume once.", "the fresh clone reproduces manifests, hashes, dispositions, and packet inputs", "any mismatch blocks the final packet"),
}
assert set(ATTACKS) == set(ATTACK_IDS), (set(ATTACK_IDS) ^ set(ATTACKS))

ALL = {**QUESTIONS, **ATTACKS}

# ── run order and workload (§13.5) ────────────────────────────────────────────────────

PRESERVATION_ORDER = (
    ["I01", "I02", "I03", "I11", "I14", "I04", "I10", "D07", "D08", "D01", "D03", "D04", "D06", "D09", "D05", "D02", "D10",
     "A01", "A02", "A03", "A04", "A05", "A06", "A07", "A09", "A10", "A12", "A13",
     "I05", "I06", "I07", "I08", "I09", "I12", "I13", "I15", "I16", "X04", "X08", "X09", "X05", "X07"]
    + ["K01", "K02", "K03", "K04", "K15", "K05", "K06", "K07", "K08", "K09", "K10", "X16", "X17", "X18", "X10", "X11",
       "K11", "K12", "K13", "K14", "K16", "X13", "X15", "X01", "X02", "X03", "X06"]
    + ["R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "R10", "R11", "R12", "R13", "R14", "R15", "R16", "X12", "X14", "X20"]
    + ["A08", "A11", "A14", "A15", "A16", "X21"]
    + ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10", "P11", "P12", "P13", "P14", "X22", "X19"]
    + ["V01", "V02", "V03", "V04", "V05", "V06", "X23"]
    + ["B04", "B05"]
)
_rest = [c for c in list(QUESTIONS) + list(ATTACKS) if c not in PRESERVATION_ORDER and c not in ("B01", "B02", "B03", "B06", "X24")]
PRESERVATION_ORDER = PRESERVATION_ORDER + _rest
assert len(set(PRESERVATION_ORDER)) == len(PRESERVATION_ORDER)
assert set(PRESERVATION_ORDER) | {"B01", "B02", "B03", "B06", "X24"} == set(ALL)

CPU_CARDS = [c for c, s in ALL.items() if not s["gpu"] and c not in ("B01", "B02", "B03", "B06", "X24")]
TIERS = {"minimum": 1.0, "expanded": 1.5}

# the frozen useful expansion ladder (§13.4), walked in order once discovery is exhausted
EXPANSION_LADDER = [
    {"rung": 1, "axis": "independent_units", "what": "more independent makers, worlds, sessions, and mixed-control histories", "cards": ["K04", "K11", "K13", "R13", "P11", "P13", "K15"]},
    {"rung": 2, "axis": "equifinal_and_events", "what": "more near-equifinal models and later diagnostic events", "cards": ["R16", "K12", "K09"]},
    {"rung": 3, "axis": "factor_crossings", "what": "additional supplied-versus-inferred factor crossings", "cards": ["R11", "R12", "K14"]},
    {"rung": 4, "axis": "prefix_and_tail", "what": "longer visible prefixes and withheld multi-step tails", "cards": ["P09", "R13"]},
    {"rung": 5, "axis": "reader_size", "what": "the next comparable local reader size/interface", "cards": ["A16", "K16"]},
    {"rung": 6, "axis": "proposal_sets", "what": "more independent proposal sets where candidate recall is measured", "cards": ["R01", "R02", "R03"]},
    {"rung": 7, "axis": "mixed_control", "what": "more style-normalized mixed-control lineages and adversarial edits", "cards": ["P12"]},
    {"rung": 8, "axis": "second_domain", "what": "a second domain or maker family under the frozen ontology", "cards": ["K04", "R13"]},
    {"rung": 9, "axis": "confirmation_seeds", "what": "a second untouched confirmation lineage", "cards": ["B01"]},
]


def tier_factor() -> float:
    """The workload lock's measured scaling of the registry's nominal unit counts (the
    discarded pilot sizes the smallest complete tier to the useful-work target; §13.1,
    §13.3); 1.0 before the lock is written."""
    try:
        from soundingline.stage7 import read_registry                             # noqa: PLC0415
        wl = read_registry("WORKLOAD_LOCK") or {}
        return float(wl.get("tier_factor") or 1.0)
    except Exception:                                                             # noqa: BLE001
        return 1.0


def units_for(card: str, tier: str = "minimum", smoke: bool = False) -> int:
    import os                                                                     # noqa: PLC0415
    n = ALL[card]["n_units"]
    if smoke:
        return min(n, 2 if ALL[card]["unit"] in ("audit", "analysis", "receipt", "ledger", "probe") else 4)
    try:
        mult = max(1.0, float(os.environ.get("S7_UNITS_MULT", "1")))
    except ValueError:
        mult = 1.0
    f = tier_factor() if ALL[card]["unit"] in ("world", "world_pair", "history", "session") else 1.0
    floor = 12 if ALL[card]["unit"] in ("world", "world_pair", "history", "session") else 1
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
