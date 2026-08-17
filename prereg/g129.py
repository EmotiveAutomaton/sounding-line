"""Pre-registration for G129 — confirmatory event-level choice recovery on ArgRewrite.

Phase 2.0 sub-goal 2.0D (governing brief: docs/design/PHASE_2_0_CONTEXT.md §9). Theory group:
Decision Traces. Written before the confirmatory run; the freeze is the git commit that lands
this file, and the card's sha256 is recorded in the FINDINGS entry that reports the result.

WHAT THE PILOT CHAIN ESTABLISHED, AND WHAT REMAINS. The pilot (L62 -> L64 -> L65) built the
clean construction one leak at a time: uniform decoys (frequency-weighted decoys leak the label
prior), truth-balanced subsampling (makes the blind floor analytic at 1/k), delta stated
explicitly (sentence text alone encodes topic). Under that construction, recorded fine-grain
revision purposes recover at 0.477 against a verified 0.232 floor, 616 events. The collision
(L73) then showed that covariate matching moves the FLOOR (0.232 -> 0.402) rather than the
recovery (0.484), leaving a delta-specific margin of 8.2 points, real at exact McNemar
p = 4.5e-4 -- but the pilot prereg's verdict bands left 5-to-10 points silent, a defect on
record. This card is the powered, exhaustively-banded, fully-controlled confirmatory form.

LESSONS CODED IN (docs/method/LESSONS.md §3): analytic floors via truth balance; no silent band
between verdict thresholds; power computed before the run; the 19-dim change block as a declared
baseline the reader must beat (L85); every verdict statistic written to the output file; fixed
label lists in every averaged score; ties broken randomly; fresh seeds, no clobbering.
"""

from __future__ import annotations

CARD = {
    "id": "G129",
    "title": "Recorded revision purposes are recoverable from the delta by a bounded reader, "
             "beyond matched contextual alternatives and beyond a cheap change-feature baseline",
    "phase": "2.0D",
    "theory_group": "Decision Traces",
    "written_before_run": True,
    "depends_on": ["L56 harness VALID", "L62/L64 clean construction", "L65 pilot", "L73 collision"],

    # ------------------------------------------------------------------------------------------
    # The question, in plain language: given only the revision delta (old sentence -> new
    # sentence, additions and removals stated) and a bounded candidate set of purposes, can a
    # bounded reader pick the recorded purpose better than the measured floor, better than
    # context-only arms, and better than nineteen string-diff features -- on events matched so
    # that size, rarity, position, and difficulty cannot carry the answer?
    "hypotheses": {
        "H-A": "Full-set replication: at the powered n under the clean construction, the "
               "recovery margin over the analytic floor replicates the pilot's 22.7 points "
               "within its band.",
        "H-B": "Matched-set survival: on a fresh covariate-matched draw, a delta-specific "
               "margin over the measured (raised) floor survives at or above 8 points.",
        "H-C": "The reader beats the declared cheap baseline: zero-shot recovery accuracy "
               "exceeds the author-split change-block classifier on the identical events.",
        "H-D": "Floor decomposition: the matched blind floor's rise above 1/k is attributable "
               "to named covariates (reported, not banded -- this half is measurement).",
    },

    # ------------------------------------------------------------------------------------------
    "dataset": {
        "events": "results/arg_baselines/events.json (2,806 extracted events, v4 extractor, "
                  "composition pinned at source per L79/L80)",
        "grain": "fine, labels with >= 30 events (the pilot's eligibility rule, unchanged)",
        "construction": "truth-balanced subsample, uniform decoys, k = 4, seed 31 (fresh; the "
                        "pilot used 23), tie-break random within seed",
        "matched_draw": "CEM on insertion/deletion size, word-count change, word rarity shift, "
                        "sentence position, original-sentence difficulty -- the L66/L73 strata, "
                        "fresh seed 31, common support only, then TRUTH-BALANCED WITHIN the "
                        "matched support (equal events per label). The floor decomposition "
                        "(L126) showed 87% of the L73 matched floor rise was label-marginal "
                        "alignment with the reader's default guesses; balancing restores the "
                        "analytic 1/k floor and makes the matched margin directly readable",
    },

    # ------------------------------------------------------------------------------------------
    # Power, computed before the run. Detecting an 8-point margin over a 0.40 floor at
    # alpha 0.05 two-sided, power 0.80 (one-sample exact binomial against the measured floor):
    # n >= 283 scoreable matched events. The matched draw targets >= 300; if common support
    # yields fewer, the shortfall is reported and the verdict downgraded to the pilot's
    # evidence tier rather than silently accepted.
    "power": {"target_margin": 0.08, "alpha": 0.05, "power": 0.80, "n_required": 283},

    # ------------------------------------------------------------------------------------------
    # Arms. Every arm that sees a revision sees the delta EXPLICITLY (added and removed words).
    # The reader is the local model, zero-shot, temperature 0 -- untrained, so author leakage
    # into the reader is impossible by construction; the one TRAINED arm (change-block) uses
    # grouped-by-author cross-validation, never revision-split.
    "arms": {
        "A1_recovery": "delta + candidates (the claim arm)",
        "A2_blind": "candidates only -- the floor arm; must land within the exact binomial 95% "
                    "CI of the analytic 1/k on the balanced set, else the construction leaks "
                    "and the run is VOID",
        "A3_shuffle": "delta + candidates, truth replaced by another event's label -- must land "
                      "at chance, else the scoring leaks and the run is VOID",
        "A4_change_block": "the 19-dim change-feature block (change_features() of "
                           "run_arg_replication.py) -> gradient-boosted classifier over the "
                           "same candidate sets, author-grouped CV -- the DECLARED BASELINE "
                           "the reader must beat (L85)",
        "A5_brief_alone": "essay prompt/brief + candidates, no delta -- context-only control",
        "A6_source_alone": "original sentence + candidates, no delta -- topic-only control",
        "A7_unchanged": "pseudo-events from unchanged sentences (no-op delta) + candidate sets "
                        "-- correct behavior is chance-level assignment; above-chance here "
                        "means the reader invents decisions that were not made (the Taramsa "
                        "failure, G94's question, measured here on real text)",
    },

    # AMENDMENT 1 (2026-08-16, before any arm ran; the build pass). A7's chance-level design
    # measured nothing: with no true label, accuracy against an arbitrary pseudo-truth is 1/k
    # by construction whatever the reader does. Refined instrument: every A7 candidate set
    # carries an explicit extra option, "no revision was made", and the delta shown is the
    # honest no-op (nothing added, nothing removed, before = after). Correct behavior is
    # picking the no-revision option; the FABRICATION RATE is the share of unchanged events
    # where the reader asserts a purpose anyway. Symmetric control in the same arm: a matched
    # sample of REAL changed events gets the same extra option, and the miss rate (calling a
    # real revision "no revision") is reported beside the fabrication rate. Verdict band
    # updated: CLEAN = fabrication rate <= 0.10; OVER-READS = above, with the rate carried as
    # the reader's warning label. The changed-side miss rate is reported, not banded.

    # ------------------------------------------------------------------------------------------
    # Verdict bands -- EXHAUSTIVE, the L73 lesson. Margins are over the MEASURED floor of the
    # same population (analytic 1/k for the balanced full set; the blind arm's read for the
    # matched set). No gap between bands anywhere.
    "verdicts": {
        "full_set": {"REPLICATES": ">= 0.15", "PARTIAL": "[0.08, 0.15)", "FAILS": "< 0.08"},
        "matched_set": {"SURVIVES": ">= 0.08", "WEAKENED": "[0.04, 0.08)", "COLLAPSED": "< 0.04"},
        "reader_vs_block": "reader accuracy minus block accuracy on identical events, exact "
                           "McNemar; BEATS if positive at p < 0.05, TIES if not significant, "
                           "LOSES if negative at p < 0.05 -- all three named, no gap",
        "unchanged_arm": "WITHIN CI of chance = clean; above at p < 0.05 = OVER-READS, and the "
                         "over-read rate is reported as the reader's fabrication bound",
    },

    # ------------------------------------------------------------------------------------------
    # Stated responses to outcomes, recorded now so no null can be reframed afterwards.
    "responses": {
        "if_H-A_fails": "The pilot's headline was construction-bound; the 2.0D exit gate is "
                        "not met by this substrate and the phase leans on the harness + G131 "
                        "constructed tasks for its known-answer evidence. No detector fusion "
                        "proceeds on the strength of ArgRewrite recovery.",
        "if_H-B_collapses": "The delta-specific remainder was small-n artifact; recoverable "
                            "purpose information on this corpus is covariate information. "
                            "Roll-up: KILLS the real-text half of 2.0D's current evidence; "
                            "the representation redesigns before any stack work.",
        "if_H-C_loses": "The reader adds nothing over nineteen numbers; the decision layer's "
                        "compact features start from the change block, not the LLM reader, "
                        "and the reader returns to Reader Heuristics for redesign.",
        "if_A7_over_reads": "The fabrication bound is carried as a warning label on every "
                            "downstream use; abstention design becomes the next obligation.",
        "if_all_pass": "2.0D's real-text gate is met on this substrate; the next obligation "
                       "is G131's constructed factorial (the construct test), then the "
                       "detector-facing compact features (2.0F).",
    },

    # ------------------------------------------------------------------------------------------
    "reporting": {
        "confusion": "per fine purpose, declared label list, counts not just rates",
        "per_author": "recovery spread by author; error clustering by essay vs author "
                      "(hierarchical share, the G97 machinery when it lands)",
        "decoys": "per-decoy pick rates -- a decoy never chosen is a strawman and is named",
        "disk": "every statistic a verdict rests on is written to the output JSON",
        "multiplicity": "all new p-values registered in runners/audit_multiplicity.py same pass",
    },
}
