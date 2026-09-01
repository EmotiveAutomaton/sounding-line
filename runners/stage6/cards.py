"""Stage 6 card registry (brief §8, §9): the 104 mandatory cards and 24 attacks with
their questions, required discriminators, engines, dependencies, factors, unit counts,
and per-unit time assumptions; the preservation order; the frozen useful expansion
ladder (§11.3); the tiers. ONE home for all of it. Every gate and its expectation under
the null and the alternative lives in the engine that runs the card, not here.

DESIGN CHECK (2026-08-30)
lessons read: LESSONS §3, §5 (a library carries no gate of its own; every stage carries a
  produces guard; underestimate runtimes 2-3x, so estimates here are conservative and the
  workload lock is sized from the measured pilot, never from these numbers).
gates: none in the registry; the expected-cell validator (I02) checks that removing any
  literal card, attack, factor corner, architecture, domain, reader, or target fails
  coverage — the registry is the enumeration it validates against.
bands: none here; the engines' verdict bands are exhaustive and stated there.
"""

from __future__ import annotations

from soundingline.stage6 import ARCHITECTURES, ATTACKS as ATTACK_IDS, CARDS as CARD_IDS

DOMAINS = ("essay", "workshop_doc")          # two constructed artifact domains (writing worlds)
SURFACE_FAMILIES = ("prose", "log")          # two renderers per world (§5.1)
MAKER_FAMILIES = ("steady", "erratic")       # two maker policy-noise families (§5.1)
SEEDS = (0, 1, 2)
TRANSFER_SEEDS = (20, 21, 22)
CONFIRMATION_SEEDS = (10, 11, 12)
CONTROLLERS = ("strict_switch", "maintained", "focal_habit", "concurrent")   # §1.3 / C track
FORAGE = ("explore", "error", "habit_misuse", "hidden_goal")                 # §1.5 / F track
VALUES = ("accuracy", "prestige")                                            # §1.4 / V track
RECORD_CORPORA = ("scholawrite", "coauthor", "drawings", "openreview")       # §5.2 (openreview: disposition)
TARGETS = ("next_edit", "next_span", "stop", "rejected_alternative", "changed_context")

# engines (runners/stage6/engines.py): which execution path runs the card
ENGINES = ("integrity", "tournament", "worldtrack", "prospective", "records", "closure")


def _c(engine: str, question: str, discriminator: str, deps: list[str], gpu: bool,
       unit: str, n_units: int, est: float, factors: dict | None = None,
       controls: list[str] | None = None, threshold: float | None = 0.03,
       primary: str | None = None) -> dict:
    return {"engine": engine, "question": question, "discriminator": discriminator,
            "depends_on": deps, "gpu": gpu, "unit": unit, "n_units": n_units,
            "est_s_per_unit": est, "factors": factors or {}, "controls": controls or [],
            "threshold": threshold, "primary": primary or question}


ARCH_LIVE = [a for a in ARCHITECTURES if a != "OR"]

CARDS: dict[str, dict] = {
    # ── I: integrity, construction, and reader gates (10) ───────────────────────────
    "I01": _c("integrity", "Do the Stage 5/5R anchors reproduce from committed inputs?",
              "numeric, environment, and hash receipt; mismatch blocks inheritance only",
              [], False, "receipt", 1, 120.0, threshold=None),
    "I02": _c("integrity", "Does the manifest recursively enumerate all 104 cards, 24 attacks, factors, lineages, floors, and outputs?",
              "expected-cell validator; removing any literal card or factor corner fails",
              [], False, "audit", 1, 60.0, threshold=None),
    "I03": _c("integrity", "Are construction identities, surface twins, lineage groups, and natural splits valid?",
              "collision hashes, grouping audit, zero cross-split descendant overlap",
              ["I02"], False, "audit", 1, 300.0, threshold=None),
    "I04": _c("integrity", "Are next-edit, stopping, and changed-context targets hidden from prompts, proposals, filenames, and schemas?",
              "canaries and label-permutation leakage baselines at floor",
              ["I03"], False, "audit", 1, 300.0, threshold=None),
    "I05": _c("integrity", "Can each admitted reader use a supplied true maker state to beat the best cheap baseline on next edit and stopping?",
              "latents-to-choice gate; failure excludes that reader from architecture claims",
              ["I03"], True, "reader_world", 48, 8.0, threshold=None,
              factors={"reader": ["qwen", "smollm"], "target": ["next_edit", "stop"]}),
    "I06": _c("integrity", "Can each architecture emit a valid realized state and normalized predictions under exact fixtures?",
              "schema/program identity tests and one printed world per state class",
              ["I03"], True, "arch_fixture", 9, 60.0, threshold=None,
              factors={"architecture": list(ARCHITECTURES)}),
    "I07": _c("integrity", "Do paired architectures see identical observations and obey their declared compute budgets?",
              "evidence hashes and compute-ledger equality within frozen tolerances",
              ["I06"], False, "audit", 1, 120.0, threshold=None),
    "I08": _c("integrity", "Are proposal wording, option order, labels, and JSON key order irrelevant when meaning is fixed?",
              "metamorphic invariance; semantic change remains detectable",
              ["I06"], True, "fixture", 24, 12.0, threshold=None),
    "I09": _c("integrity", "Do exact, null, contradiction, and equifinality fixtures produce the required posterior shapes?",
              "oracle positive, no-information identity, revision, and abstention gates",
              ["I03"], False, "fixture", 24, 8.0, threshold=None),
    "I10": _c("integrity", "Do checkpoint/resume, deadline, GPU lock, companion-process ownership, and report suppression work end to end?",
              "killed-process smoke, fresh resume, Ghost sentinel survival, pre-deadline packet refusal",
              [], False, "audit", 1, 300.0, threshold=None),
    # ── M: hypothesis proposal and contextual realization (16) ──────────────────────
    "M01": _c("tournament", "How well does a direct monolithic reader predict the next event without an explicit maker state?",
              "frozen baseline on every common benchmark cell", ["I05", "I06", "I07"], True,
              "world", 64, 10.0, factors={"architecture": ["D"], "domain": list(DOMAINS)}),
    "M02": _c("tournament", "Does label-only augmented inverse planning improve over direct reading?",
              "same evidence/compute; likelihood and calibration, not rationale preference",
              ["M01"], True, "world", 64, 16.0, factors={"architecture": ["L"], "domain": list(DOMAINS)}),
    "M03": _c("tournament", "Does attaching a fixed definition to each label explain any M02 gain?",
              "LD versus L with definition length and vocabulary matched",
              ["M02"], True, "world", 64, 16.0, factors={"architecture": ["LD"], "domain": list(DOMAINS)}),
    "M04": _c("tournament", "Do free-language weighted particles preserve useful competing hypotheses through contradiction?",
              "TT versus label posterior on reversal and recovery, particle collapse recorded",
              ["M02"], True, "world", 64, 24.0, factors={"architecture": ["TT"], "domain": list(DOMAINS)}),
    "M05": _c("tournament", "Does grammar-constrained semantic realization improve validity and prediction?",
              "GS versus free language; parse success cannot substitute for held-out gain",
              ["M02"], True, "world", 64, 20.0, factors={"architecture": ["GS"], "domain": list(DOMAINS)}),
    "M06": _c("tournament", "Does a synthesized executable maker model improve whole-artifact and next-event likelihood?",
              "EX versus GS at equal observations and matched budget",
              ["M05"], True, "world", 64, 24.0, factors={"architecture": ["EX"], "domain": list(DOMAINS)}),
    "M07": _c("tournament", "Does adaptive variable/history expansion help only when the initial model is missing a cause?",
              "AD interaction with missing-variable worlds and false-expansion cost on complete worlds",
              ["M06"], True, "world", 64, 24.0,
              factors={"architecture": ["AD"], "world_completeness": ["complete", "missing_variable"]}),
    "M08": _c("tournament", "Does Sounding contextual realization improve prediction beyond the best published scaffold?",
              "CR minus best non-oracle arm on next edit and stop, after realization gates",
              ["M03", "M04", "M05", "M06", "M07"], True, "world", 64, 24.0,
              factors={"architecture": ["CR"], "domain": list(DOMAINS)}),
    "M09": _c("tournament", "How much of the exact oracle gap does each architecture close?",
              "fraction of OR-minus-cheap log-score gap, conditional by domain",
              ["M08"], True, "world", 64, 8.0, factors={"architecture": ["OR"], "domain": list(DOMAINS)}),
    "M10": _c("tournament", "Does the realized state assign better likelihood to withheld decisions across the whole artifact?",
              "artifact-wide posterior predictive score and localized overfit test",
              ["M08"], True, "world", 48, 20.0),
    "M11": _c("tournament", "Does it predict the type, location, and direction of the maker's next edit?",
              "joint proper score against text-only, last-edit, and position baselines",
              ["M08"], True, "world", 48, 16.0),
    "M12": _c("tournament", "Does it predict continuation versus stopping at genuine decision points?",
              "hazard/log score against length, token-budget, and section-position baselines",
              ["M08"], True, "world", 48, 16.0),
    "M13": _c("tournament", "Do nearest rival states make and survive distinct counterfactual predictions?",
              "predeclared intervention; posterior changes only when the observation discriminates",
              ["M08"], True, "world", 48, 20.0),
    "M14": _c("tournament", "Does the same short proposal realize different maker policies in two contexts that require it?",
              "context-swap interaction; copied realization fails",
              ["M08"], True, "world_pair", 32, 24.0),
    "M15": _c("tournament", "Do paraphrased proposals converge behaviorally while meaning-changing proposals diverge?",
              "prediction-distribution equivalence, not embedding similarity alone",
              ["M08"], True, "world", 48, 20.0),
    "M16": _c("tournament", "Does the architecture transfer to a new artifact domain and reader family without rebuilding its ontology?",
              "frozen adapter and prompts; domain/family interactions reported before pooling",
              ["M08"], True, "world", 48, 20.0, factors={"reader": ["qwen", "smollm"]}),
    # ── C: foreground goal, switching, and concurrent residue (12) ──────────────────
    "C01": _c("worldtrack", "Are strict-switch, maintained-goal, focal-plus-habit, and concurrent-objective worlds independently live and surface matched?",
              "exact controller identities and leakage floors", ["I03"], False, "audit", 1, 600.0,
              factors={"controller": list(CONTROLLERS)}, threshold=None),
    "C02": _c("worldtrack", "Can the controllers produce the same final artifact and aggregate goal counts?",
              "matched endpoint/summary gate before reader use", ["C01"], False, "audit", 1, 300.0, threshold=None),
    "C03": _c("worldtrack", "Which controller best predicts the next edit immediately after an interruption?",
              "switch-specific held-out action and latency/cost proxy",
              ["C02", "I05"], True, "world", 48, 12.0, factors={"controller": list(CONTROLLERS)}),
    "C04": _c("worldtrack", "Do rapid alternations produce different local edit clusters from simultaneous weighted control?",
              "edit locality and dependency pattern with total edits matched",
              ["C02"], False, "world", 96, 2.0, factors={"controller": ["strict_switch", "concurrent"]}),
    "C05": _c("worldtrack", "Does rereading selectively expose and correct compiled habitual output?",
              "reread intervention x controller interaction; generic improvement insufficient",
              ["C02", "I05"], True, "world", 48, 12.0,
              factors={"controller": ["focal_habit", "strict_switch"], "reread": ["yes", "no"]}),
    "C06": _c("worldtrack", "Do concurrent or maintained goals leave hanging dependencies that a strict switcher does not?",
              "delayed completion and cross-span dependency predictions",
              ["C02"], False, "world", 96, 2.0, factors={"controller": list(CONTROLLERS)}),
    "C07": _c("worldtrack", "Can a dormant future intention be recovered while a different goal controls the current action?",
              "cue-triggered later action, not a current-goal label",
              ["C02", "I05"], True, "world", 48, 12.0, factors={"controller": ["maintained", "strict_switch"]}),
    "C08": _c("worldtrack", "Can a completed intention produce a commission-style residue without being the foreground goal?",
              "post-completion cue intrusion and correct deactivation control",
              ["C02"], False, "world", 96, 2.0, factors={"completed": ["deactivated", "residue"]}),
    "C09": _c("worldtrack", "Does surprise switch the foreground goal, alter precision within it, or reveal a missing goal?",
              "three-way intervention with distinct next actions",
              ["C02", "I05"], True, "world", 48, 12.0, factors={"surprise": ["switch", "precision", "missing_goal"]}),
    "C10": _c("worldtrack", "Can current goal, stimulus salience, and selection history pull attention in different directions?",
              "fully crossed priority construction and selected-evidence outcome",
              ["C02"], False, "world", 96, 2.0, factors={"pull": ["goal", "salience", "history"]}),
    "C11": _c("worldtrack", "Which inferred controller improves next edit and stopping beyond a controller-agnostic reader?",
              "architecture tournament with identical latent vocabulary",
              ["C03", "M08"], True, "world", 48, 20.0, factors={"controller": list(CONTROLLERS)}),
    "C12": _c("records", "Do the winning controller signatures appear prospectively in recorded revision sessions?",
              "frozen synthetic-trained discriminator on session-held-out records; descriptive if no known truth",
              ["C11", "T01"], False, "session", 40, 8.0, threshold=None),
    # ── A: attention history, expertise, constraints, and lag (14) ──────────────────
    "A01": _c("worldtrack", "Can an attention-history-only learner and a richer expertise learner be made behaviorally distinct?",
              "same attention sequence, different feedback/constraints; different future predictions",
              ["I03"], False, "audit", 1, 600.0, factors={"learner": ["attention_only", "rich"]}, threshold=None),
    "A02": _c("worldtrack", "What is learned from repeated exposure without task-relevant selection?",
              "exposure-only versus attended exposure, matched stimulus frequency",
              ["A01"], False, "world", 96, 2.0, factors={"history": ["exposure", "attended"]}),
    "A03": _c("worldtrack", "What is learned from attention without successful execution or feedback?",
              "attended observation versus practiced transition and outcome feedback",
              ["A01"], False, "world", 96, 2.0, factors={"history": ["attended", "practiced"]}),
    "A04": _c("worldtrack", "Does different feedback produce different expertise after matched attended actions?",
              "feedback swap with identical selected events and time",
              ["A01"], False, "world", 96, 2.0, factors={"feedback": ["reward", "error", "none"]}),
    "A05": _c("worldtrack", "Can externally imposed, disliked training create competence and habit residue?",
              "current preference opposed to trained action; process skill and choice separated",
              ["A01"], False, "world", 96, 2.0, factors={"imposed": ["yes", "no"]}),
    "A06": _c("worldtrack", "Do time pressure and available alternatives alter learned policy after attention is matched?",
              "constraint/context swap with logged selection equality",
              ["A01"], False, "world", 96, 2.0, factors={"constraint": ["pressure", "free"]}),
    "A07": _c("worldtrack", "Do tool or embodiment constraints leave a route signature beyond attended features?",
              "executable-action-set swap; no human embodiment claim",
              ["A01"], False, "world", 96, 2.0, factors={"toolset": ["narrow", "wide"]}),
    "A08": _c("worldtrack", "Does selection history capture attention after reward or task value reverses?",
              "current-goal/history conflict and decay curve",
              ["A01"], False, "world", 96, 2.0, factors={"phase": ["pre", "post_reversal"]}),
    "A09": _c("worldtrack", "How quickly does stale history correct under diagnostic new feedback?",
              "bias half-life, retained skill, and overcorrection",
              ["A08"], False, "world", 96, 2.0),
    "A10": _c("worldtrack", "Does domain expertise chiefly improve prediction of action chains and deviations?",
              "expert-route model x access-level interaction, not self-rated expertise",
              ["A01", "I05"], True, "world", 48, 12.0, factors={"expertise": ["novice", "expert"]}),
    "A11": _c("worldtrack", "Are conventional, well-predicted choices discounted while deviations attract inference?",
              "standard-choice versus equally large diagnostic deviation, base-rate likelihoods explicit",
              ["A01", "I05"], True, "world", 48, 12.0, factors={"choice": ["conventional", "deviation"]}),
    "A12": _c("worldtrack", "Can the reader separate a current proximal goal from an old habit that leaks into its execution?",
              "goal-habit conflict with hidden next choice after incentive change",
              ["A01", "I05"], True, "world", 48, 12.0),
    "A13": _c("worldtrack", "How much trajectory information is lost when history order and dates are removed?",
              "dated, ordered-undated, shuffled, and aggregate-history comparison",
              ["A01"], False, "world", 96, 3.0, factors={"history_view": ["dated", "ordered", "shuffled", "aggregate"]}),
    "A14": _c("worldtrack", "Which object best predicts a novel cross-domain action?",
              "factor interventions and frozen changed-context choice",
              ["A02", "A03", "A04", "A06"], False, "world", 96, 3.0,
              factors={"object": ["current_goal", "selection_history", "skill", "constraint_history"]}),
    # ── V: value-compatible states and change over time (14) ────────────────────────
    "V01": _c("worldtrack", "Can accuracy-oriented and prestige-oriented makers produce the same initial citation choice?",
              "surface and initial-policy collision gate", ["I03"], False, "audit", 1, 600.0,
              factors={"value": list(VALUES)}, threshold=None),
    "V02": _c("worldtrack", "What happens when both discover that the prestigious source is wrong?",
              "correction, retention, and argument-rewrite distributions",
              ["V01"], False, "world", 96, 2.0, factors={"value": list(VALUES)}),
    "V03": _c("worldtrack", "Does avoidable private cost separate accuracy from appearance management?",
              "costly source replacement when no audience observes the act",
              ["V01"], False, "world", 96, 2.0, factors={"value": list(VALUES), "observed": ["no"]}),
    "V04": _c("worldtrack", "Does public visibility change the prestige policy more than the accuracy policy?",
              "public/private x maker-state interaction",
              ["V01"], False, "world", 96, 2.0, factors={"value": list(VALUES), "visibility": ["public", "private"]}),
    "V05": _c("worldtrack", "Do hedges, credibility boosts, preemptive degradation, or retreat options reveal reputational calculus?",
              "future challenge response, not stylistic counting alone",
              ["V01"], False, "world", 96, 2.0, factors={"value": list(VALUES)}),
    "V06": _c("worldtrack", "Does the posterior remain appropriately broad before the diagnostic event?",
              "equivalence-class coverage and overconfidence penalty",
              ["V01", "I05"], True, "world", 48, 12.0),
    "V07": _c("worldtrack", "Can a current proximal goal oppose a lagging historical tendency preserved in expertise?",
              "opposed-state construction and local next action",
              ["V01", "A01"], False, "world", 96, 2.0),
    "V08": _c("worldtrack", "Can genuine value change be distinguished from better concealment?",
              "private/off-audience behavior and later costly choice",
              ["V01"], False, "world", 96, 2.0, factors={"change": ["genuine", "concealment"]}),
    "V09": _c("worldtrack", "Can value change be distinguished from a context or constraint shift?",
              "context restoration and crossed constraint intervention",
              ["V01"], False, "world", 96, 2.0, factors={"change": ["value", "context"]}),
    "V10": _c("worldtrack", "Can value change be distinguished from newly acquired competence?",
              "equal opportunity with skill swap and preference-stable control",
              ["V01"], False, "world", 96, 2.0, factors={"change": ["value", "competence"]}),
    "V11": _c("worldtrack", "When several motivational organizations remain policy-equivalent, does the reader preserve the class?",
              "posterior class coverage until a resolving intervention",
              ["V01", "I05"], True, "world", 48, 12.0),
    "V12": _c("worldtrack", "Can the reader choose a diagnostic opportunity that separates its top value hypotheses?",
              "realized gain per cost and consistent-world false-probe rate",
              ["V06"], True, "world", 48, 12.0),
    "V13": _c("worldtrack", "Do dated artifacts support a better value trajectory than aggregate style/history features?",
              "held-out later episode after time-aware versus time-blind modeling",
              ["V02"], False, "world", 96, 3.0, factors={"model": ["time_aware", "time_blind"]}),
    "V14": _c("worldtrack", "Does the inferred trajectory predict a changed-context future tradeoff beyond last goal, habit, topic, and identity?",
              "fresh episode proper score; the value-track promotion gate",
              ["V13"], True, "world", 48, 12.0),
    # ── F: deliberate epistemic foraging versus three rivals (12) ───────────────────
    "F01": _c("worldtrack", "Are exploration, ordinary error, habitual misuse, and hidden artifact-level goal independently live?",
              "exact generator identities, surface matching, and latent swaps",
              ["I03"], False, "audit", 1, 600.0, factors={"forage": list(FORAGE)}, threshold=None),
    "F02": _c("worldtrack", "Does deliberate exploration commit enough action to observe an informative outcome?",
              "outcome-sufficient exposure versus cosmetically unusual action",
              ["F01"], False, "world", 96, 2.0, factors={"forage": ["explore", "error"]}),
    "F03": _c("worldtrack", "Can small careful probes escalate only as much as needed to resolve uncertainty?",
              "probe sequence, expected information, and stopping rule",
              ["F01"], False, "world", 96, 2.0),
    "F04": _c("worldtrack", "Does an ordinary error get repaired before an informative outcome is obtained?",
              "early detection/repair with no downstream policy update",
              ["F01"], False, "world", 96, 2.0),
    "F05": _c("worldtrack", "Does habitual misuse sometimes run farther because expected actions receive less monitoring?",
              "monitoring delay and correction after accumulated discrepancy",
              ["F01"], False, "world", 96, 2.0),
    "F06": _c("worldtrack", "Does a hidden aesthetic or rhetorical goal integrate the unusual technique with distant artifact structure?",
              "global dependency and future coordinated choices",
              ["F01"], False, "world", 96, 2.0),
    "F07": _c("worldtrack", "Can all four worlds be matched on local oddness, effort, and immediate quality?",
              "cheap-feature leakage and blind surface classifier at floor",
              ["F01"], False, "audit", 1, 600.0, threshold=None),
    "F08": _c("worldtrack", "Does genuine exploration change the maker's later technique in the predicted direction?",
              "held-out policy update; without learning, classify cautiously",
              ["F01"], False, "world", 96, 2.0),
    "F09": _c("worldtrack", "Is the chosen probe useful under the maker's current uncertainty and goal?",
              "maker-relative expected gain per cost, not observer novelty",
              ["F01"], False, "world", 96, 2.0),
    "F10": _c("worldtrack", "Does random unlearnable noise lose to a structured unresolved pattern?",
              "noise trap, realized learning, and calibrated refusal",
              ["F01"], False, "world", 96, 2.0, factors={"pattern": ["noise", "structured"]}),
    "F11": _c("worldtrack", "Can a reader infer the four-way posterior and abstain before the distinguishing consequence?",
              "trajectory posterior and first-identifiable-event analysis",
              ["F07", "I05"], True, "world", 48, 12.0, factors={"forage": list(FORAGE)}),
    "F12": _c("records", "Do the distinguishing signatures transfer to recorded drawings and revisions?",
              "frozen reader, process-held-out next action; historical claims remain bounded",
              ["F11", "T04"], False, "session", 40, 8.0, threshold=None),
    # ── P: common prospective benchmark (12) ────────────────────────────────────────
    "P01": _c("prospective", "Can the reader predict the next edit type?",
              "proper score against last-edit, local-text, and base-rate rivals",
              ["M08"], False, "world", 64, 2.0),
    "P02": _c("prospective", "Can it predict the location and scope of the next edit?",
              "hierarchical span score against position and section priors",
              ["M08"], False, "world", 64, 2.0),
    "P03": _c("prospective", "Can it predict whether the maker continues or stops?",
              "discrete-time hazard against length, deadline, and token-budget baselines",
              ["M08"], False, "world", 64, 2.0),
    "P04": _c("prospective", "Can it predict which of several live alternatives the maker rejects?",
              "opportunity-conditioned choice score; unavailable options never count",
              ["M08"], False, "world", 64, 2.0),
    "P05": _c("prospective", "Can it predict a repair after contradiction?",
              "direction, latency, and confidence reduction",
              ["M08"], False, "world", 48, 2.0),
    "P06": _c("prospective", "Can it predict a later action after an intervening context change?",
              "changed-context log score, not retrospective state agreement",
              ["M08"], False, "world", 48, 2.0),
    "P07": _c("prospective", "Does artifact-wide likelihood improve rather than only the explicitly queried endpoint?",
              "sum of withheld decision scores and localization audit",
              ["M10"], False, "world", 48, 2.0),
    "P08": _c("prospective", "Is uncertainty calibrated across evidence dose and contradiction?",
              "reliability curve, Brier decomposition, and selective risk",
              ["P01", "P03"], False, "analysis", 1, 600.0, threshold=None),
    "P09": _c("prospective", "Does the reader abstain on exact historical equifinality while retaining enactable routes?",
              "history-class coverage and enactability scored separately",
              ["M08"], False, "world", 48, 2.0),
    "P10": _c("prospective", "Which realized-state fields causally matter for prediction?",
              "field swaps/ablations with surface and prompt held constant",
              ["M08"], True, "world", 48, 16.0,
              factors={"ablated": ["none", "episode_goal", "control_state", "selection_history", "expertise_state", "stop_model"]}),
    "P11": _c("prospective", "Does the model improve at a second reader checkpoint and artifact domain?",
              "family/domain conditional transfer; no pooled rescue",
              ["P01", "P03"], False, "world", 48, 2.0, factors={"reader": ["qwen", "smollm"]}),
    "P12": _c("prospective", "Does any architecture meet the Stage 6 understanding criterion?",
              "next edit and stopping both pass, plus one changed-context choice, calibration, attacks, untouched confirmation",
              ["P01", "P02", "P03", "P06", "P08"], False, "analysis", 1, 600.0, threshold=None),
    # ── T: recorded-process transfer and ecological boundary (10) ───────────────────
    "T01": _c("records", "Does the reader improve ScholaWrite next-revision prediction under leave-project-out and leave-author-out splits?",
              "beat previous-label and text-delta baselines on both protocols",
              ["I03", "I05"], True, "session", 40, 30.0, factors={"protocol": ["leave_project_out", "leave_author_out"]}),
    "T02": _c("records", "Can CoAuthor document states be reconstructed well enough to predict accept, dismiss, edit, or retain?",
              "state reconstruction gate before action inference",
              ["I03", "I05"], True, "session", 60, 20.0),
    "T03": _c("records", "Can a paper/reviewer model predict an OpenReview revision on a held-out paper lineage?",
              "paper/author-grouped score and topic/style rivals; RESOURCE disposition if the corpus is absent",
              ["I03"], False, "session", 1, 60.0, threshold=None),
    "T04": _c("records", "Can the process reader predict a recorded drawing's next stroke while preserving history uncertainty?",
              "access-level curve, category priors, and equifinal class",
              ["I03", "I05"], True, "drawing", 120, 6.0),
    "T05": _c("records", "Does one frozen architecture transfer across at least three record types?",
              "no corpus-specific ontology edit after outcomes",
              ["T01", "T02", "T04"], False, "analysis", 1, 600.0, threshold=None),
    "T06": _c("records", "Do dated multi-episode records improve changed-context prediction?",
              "time-aware versus aggregate-history reader",
              ["T01"], True, "session", 40, 16.0, factors={"model": ["time_aware", "aggregate"]}),
    "T07": _c("records", "Does explicit opportunity and constraint information improve prediction beyond content alone?",
              "records-plus-opportunity interaction; no assumed option set",
              ["T02"], True, "session", 40, 16.0, factors={"opportunity": ["shown", "hidden"]}),
    "T08": _c("records", "Are gains robust to genre, topic, length, author identity, and surface statistics?",
              "matched/stratified analysis and negative controls",
              ["T01", "T02", "T04"], False, "analysis", 1, 900.0, threshold=None),
    "T09": _c("records", "Are intervals and effective sample sizes maker/session based?",
              "cluster bootstrap and row-duplication invariance",
              ["T01"], False, "analysis", 1, 300.0, threshold=None),
    "T10": _c("records", "Where should the natural bridge close if construction or reader gates fail?",
              "one disposition per corpus: promote, descriptive boundary, instrument failure, or void",
              ["T05", "T08", "T09"], False, "analysis", 1, 300.0, threshold=None),
    # ── B: confirmation, cross-program bridge, and closure (4) ──────────────────────
    "B01": _c("closure", "Does the strongest qualified architecture effect replicate on untouched makers, surfaces, and seeds?",
              "one frozen estimand and all named rivals; no endpoint substitution",
              [], True, "world", 48, 24.0),
    "B02": _c("closure", "Does the sharpest architecture boundary or theory discriminator replicate independently?",
              "prefer a sign reversal or failure boundary over a second weak mean gain",
              ["B01"], True, "world", 48, 24.0),
    "B03": _c("closure", "Which landed Ghost V14 rulers transfer to Sounding, and which Stage 6 results feed back only as context?",
              "receipt-by-receipt bridge ledger; no partial V14 import and no automatic V15",
              [], False, "ledger", 1, 600.0, threshold=None),
    "B04": _c("closure", "What moves in pursuit, warrant, theory, and the next program after all gates?",
              "final-only curator packet, claim ledger, coverage audit, explicit Stage-7/no-Stage-7 ruling",
              ["B03"], False, "analysis", 1, 900.0, threshold=None),
}
assert set(CARDS) == set(CARD_IDS), (set(CARD_IDS) ^ set(CARDS))

# ── the 24 attacks (§9): covered cards, expected invariant/reversal, consequence ──────

def _x(covers: list[str], attack: str, expect: str, consequence: str, gpu: bool = False,
       unit: str = "derived", n_units: int = 1, est: float = 300.0) -> dict:
    return {"engine": "attack", "covers": covers, "question": attack, "discriminator": expect,
            "consequence": consequence, "depends_on": [c for c in covers if c in CARDS][:3],
            "gpu": gpu, "unit": unit, "n_units": n_units, "est_s_per_unit": est,
            "factors": {}, "controls": [], "threshold": None, "primary": attack}


ATTACKS: dict[str, dict] = {
    "X01": _x(["M15", "M08"], "Paraphrase a proposal without changing its operative meaning; predictions should remain stable.",
              "prediction-distribution distance under paraphrase at the noise floor; meaning change detectable",
              "an unstable architecture's realization gate 6 fails; its claims close", True, "world", 24, 20.0),
    "X02": _x(["I08", "M02"], "Permute opaque proposal labels and JSON keys; no semantic result may move.",
              "estimates invariant to label/key permutation", "label leakage; the leaking card re-runs after repair", True, "world", 24, 12.0),
    "X03": _x(["M02", "M03", "M08"], "Match candidate length, fluency, specificity, and confidence language.",
              "gains survive matched surface statistics", "a surface effect is renamed, never promoted"),
    "X04": _x(["M04", "V06"], "Duplicate or paraphrase evidence from one cause; confidence must not rise as if independent.",
              "posterior weight flat under duplicated evidence", "the double-count defect closes the affected posterior claims", True, "world", 24, 16.0),
    "X05": _x(["P09", "F01"], "Hold the final artifact fixed while swapping valid histories; require class uncertainty.",
              "posterior mass spreads over the swap class", "forced point accuracy on equifinal classes voids the cell"),
    "X06": _x(["V01", "V02"], "Hold the initial action fixed while swapping later-divergent standing tendencies.",
              "early posterior near even; late diverges with the diagnostic event", "a premature value verdict closes"),
    "X07": _x(["V09", "A06"], "Hold standing tendency fixed while swapping context, opportunity, or constraint.",
              "attribution follows the swap, not the tendency label", "context-blind attribution is a defect"),
    "X08": _x(["I04"], "Leak a goal through filenames, option wording, order, or field names; canaries must catch it.",
              "every planted canary caught at the leakage floor", "an uncaught canary blocks the scientific lock"),
    "X09": _x(["I08", "M01"], "Permute answer order and use fixed-order paired likelihoods.",
              "fixed order per unit across arms; order permutation moves nothing (the L283 lesson)",
              "an order-driven contrast is re-run under fixed order", True, "world", 24, 12.0),
    "X10": _x(["M05", "M08"], "Vary prompt template, schema presentation, and serialization without changing evidence.",
              "estimates stable across template variants", "a template effect is an instrument fact, not a result", True, "world", 24, 16.0),
    "X11": _x(["I07", "M08"], "Equalize or explicitly account for compute, context length, calls, and solver work.",
              "budget ledger parity within frozen tolerances", "an over-budget win is not a realization effect"),
    "X12": _x(["M16", "P11"], "Transfer across reader families; report a family-specific effect rather than pooling it away.",
              "family-conditional effects reported before any pooled mean", "a pooled rescue is refused"),
    "X13": _x(["C01", "F01"], "Transfer across maker families and generation lineages.",
              "effects reported per maker family", "a single-family effect is bounded as such"),
    "X14": _x(["T08"], "Match or stratify topic, genre, length, quality, and surface statistics.",
              "gains survive stratification", "an unmatched gain is renamed a surface effect"),
    "X15": _x(["A13", "T06"], "Shuffle or erase history order and dates while preserving aggregate events.",
              "trajectory-dependent claims degrade under shuffle; aggregate-only claims do not",
              "a claim surviving shuffle is not a trajectory claim"),
    "X16": _x(["V13", "A13"], "Replace a true trajectory with an aggregate style profile of equal dimension.",
              "trajectory beats the matched-dimension aggregate or the claim is renamed",
              "dimension, not history, explains the gain"),
    "X17": _x(["A07", "T07"], "Swap constraints or available actions while holding selected behavior fixed.",
              "constraint attribution follows the swap", "an opportunity-blind reading closes"),
    "X18": _x(["A02", "A03", "A04"], "Cross exposure, selected attention, practice, feedback, and outcome value.",
              "the crossed factors separate in the learned policies", "aliased factors void the history claims"),
    "X19": _x(["F02", "F04"], "Make an accident look locally exploratory but deny it an informative consequence.",
              "the reader's exploration posterior stays low without obtained information",
              "oddness-as-exploration is the named failure"),
    "X20": _x(["F06"], "Give an unusual technique a distant global dependency only in the hidden-goal world.",
              "hidden-goal posterior follows the dependency, not the local oddness",
              "local-oddness diagnosis is the named failure"),
    "X21": _x(["P03", "M12"], "Match length and section-position stopping base rates across goals.",
              "stopping gains survive matched base rates", "a length detector is renamed as such"),
    "X22": _x(["A12", "V07"], "Cross old habit with new value so current intent and residue disagree.",
              "the reader separates the two or the claim is bounded", "habit-as-preference is the named failure"),
    "X23": _x(["P12", "B04"], "Verify that pooled means cannot hide planned sign reversals across similarity, domain, reader, or evidence access.",
              "every planned reversal emitted conditionally before pooling; alarms on suppression",
              "a pooled mean over a planned reversal blocks the packet"),
    "X24": _x(["I10", "B04"], "Fresh-clone, raw-output, source-lineage, hash-lock, resume, and report-provenance attack.",
              "the fresh clone reproduces manifests, hashes, verdict counts, and packet inputs",
              "a provenance mismatch blocks the packet"),
}
assert set(ATTACKS) == set(ATTACK_IDS), (set(ATTACK_IDS) ^ set(ATTACKS))

ALL = {**CARDS, **ATTACKS}

# ── run order and workload ────────────────────────────────────────────────────────────

# preservation order (§11.4 allocation intervals, dependency-respecting): integrity, the
# tournament and benchmark, control, history, value+foraging, records, closure; attacks
# interleave after their covered cards
PRESERVATION_ORDER = (
    ["I01", "I02", "I03", "I09", "I04", "I10", "I06", "I07", "I05", "I08"]
    + ["M01", "M02", "M03", "M05", "M04", "M06", "M07", "M08", "M09"]
    + ["X02", "X09", "X03", "X11"]
    + ["M10", "M11", "M12", "M13", "M14", "M15", "M16", "X01", "X10", "X04"]
    + ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P09", "P10", "P11", "P08", "X21", "X12"]
    + ["C01", "C02", "C04", "C06", "C08", "C10", "C03", "C05", "C07", "C09", "C11", "X13"]
    + ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A13", "A14", "A10", "A11", "A12", "X18", "X15", "X17", "X22"]
    + ["V01", "V02", "V03", "V04", "V05", "V07", "V08", "V09", "V10", "V13", "V06", "V11", "V12", "V14", "X06", "X07", "X16"]
    + ["F01", "F07", "F02", "F03", "F04", "F05", "F06", "F08", "F09", "F10", "F11", "X19", "X20", "X05"]
    + ["T03", "T01", "T02", "T04", "T05", "T06", "T07", "T08", "T09", "C12", "F12", "T10", "X14"]
    + ["P12", "X23", "B03", "X08", "X24"]
)
_rest = [c for c in list(CARDS) + list(ATTACKS) if c not in PRESERVATION_ORDER and c not in ("B01", "B02", "B04")]
PRESERVATION_ORDER = PRESERVATION_ORDER + _rest        # nothing silently dropped
assert len(set(PRESERVATION_ORDER)) == len(PRESERVATION_ORDER)
assert set(PRESERVATION_ORDER) | {"B01", "B02", "B04"} == set(ALL)

CPU_CARDS = [c for c, s in ALL.items() if not s["gpu"] and c not in ("B01", "B02", "B04")]

# tiers: minimum unit counts are the registry's n_units; the expanded tier and the ladder
# grow them along §11.3's axes. The workload lock freezes the admitted tier from the
# measured pilot, never from these numbers.
TIERS = {"minimum": 1.0, "expanded": 1.5}

# the frozen useful expansion ladder (§11.3), walked in order once discovery is exhausted
EXPANSION_LADDER = [
    {"rung": 1, "axis": "independent_units", "what": "additional independent makers, sessions, paper lineages, and drawings (+50 percent units on resolved substantive cards)"},
    {"rung": 2, "axis": "surface_and_paraphrase", "what": "a second surface renderer and proposal paraphrase lineage on the tournament and benchmark cards"},
    {"rung": 3, "axis": "reader_checkpoint", "what": "the next already available local reader checkpoint (Qwen2.5-3B-Instruct) on capability-gated cards, bounded as non-claim"},
    {"rung": 4, "axis": "process_length", "what": "longer process prefixes and more withheld continuation steps on P and T cards"},
    {"rung": 5, "axis": "history_combinations", "what": "additional matched history-context-feedback combinations on the A track"},
    {"rung": 6, "axis": "equifinal_rivals", "what": "additional near-equifinal rival states and diagnostic opportunities on V and F"},
    {"rung": 7, "axis": "natural_partition", "what": "the next natural corpus transfer partition on the T track"},
    {"rung": 8, "axis": "approximation_samples", "what": "more particles or executable-state samples where approximation error is itself measured (TT, EX)"},
    {"rung": 9, "axis": "confirmation_seeds", "what": "a second untouched confirmation seed family"},
]


def units_for(card: str, tier: str = "minimum", smoke: bool = False) -> int:
    import os                                                                     # noqa: PLC0415
    n = ALL[card]["n_units"]
    if smoke:
        return min(n, 2 if ALL[card]["unit"] in ("audit", "analysis", "receipt", "ledger") else 3)
    mult = 1.0
    try:
        mult = max(1.0, float(os.environ.get("S6_UNITS_MULT", "1")))   # a ladder rung's extra units
    except ValueError:
        mult = 1.0
    return max(1, int(round(n * TIERS.get(tier, 1.0) * mult)))


def est_minutes(card: str, tier: str = "minimum") -> float:
    s = ALL[card]
    facs = 1
    for v in s["factors"].values():
        facs = max(facs, 1)                     # factors run inside the unit loop, not multiplied
    return s["est_s_per_unit"] * units_for(card, tier) * facs / 60.0
