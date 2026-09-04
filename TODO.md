# TODO: the study queue

**Reordered 2026-08-09 (evening) around the program and the frontier-first principle.** Results go
in [`FINDINGS.md`](FINDINGS.md). Everything below the phase sections is the pre-program backlog
archive, kept whole, mined but never deleted.

## THE PLAN (overall plan for AI, not human consumption. The phases that are part of the plan are to be abbreviated, not removed, upon completion and record-transcribing to Findings/Theory. When a particular phase of the plan is complete, include that note as part of the test report.)

The unit of analysis changed from one number per artifact to the recorded decision event, which
carries target, alternatives, choice, dependencies, and context. Event recovery must validate
before any summary statistic means anything. Full statement in `docs/STATE.md` and the README.

**The standing priority order, his directive.** First, RECREATE the frontier experimental space
relevant to us, meaning the published experiments our claims sit next to get reproduced with our
tooling so their numbers become our known answers. Only then push a bit further, one extension
per recreated anchor. The reasons this ordering wins here: every recreation doubles as a
known-answer gate for the instrument that will run the extension; a recreation that fails flags
our tooling before it flags the world; and the project's recurring death (criteria that could not
fail) is exactly what recreation catches cheap.

**The phase logic.** Phase 0 is whatever is running or just landed. Phase 1 is the frontier
recreations, split into already-in-hand (marked, with their landing) and owed (the builds).
Phase 2 is the program proper, each step gated on its Phase 1 anchor. Phase 3 is blocked on
people, corpora, or decisions. A stage enters the machine queue (`run_queue.py`) only from Phase
0 or from a Phase whose gate has passed. Queue-of-studies format: each row is one study with its
method sketch and its gate.

---

## Phase 0 — running or just landed

**Stage 5 (routed joint reconstruction; brief at docs/design/PHASE_2_4_STAGE_5_CONTEXT.md) CLOSED
2026-08-29 13:04, RUN_TO_EMPTY after 1.25 hours under second gear (launched 11:49 on his order;
28 cards resolved, three as repair cells, two withdrawn; one confirmation, R02; packet and analyst
synthesis at results/phase_2_4_stage_5/CURATOR_PACKET_FINAL.md; landings L256 to L281). The wrapper
chained into the general queue.**

**Stage 5R (the second contract, design 2) CLOSED 2026-08-29 16:32, RUN_TO_EMPTY after 1.35 hours
(launched 15:11 on his order; restarted 15:24 for the source-text repair; 29 cards resolved; two
confirmations, R02 and P02; landings L284 to L308; packet and synthesis at
results/phase_2_4_stage_5r/CURATOR_PACKET_FINAL.md). It ran The whole 29-card program on its own
root (`results/phase_2_4_stage_5r`, `run_stage5r.sh`, `S5_DESIGN=2`) with every post-run repair: the 96-item reader gate (SmolLM2 admitted, L282), the source-world register gate and the
latents-to-choice gate as track gates (TODO (j), (p)), the fixed-order bridge (s), the repaired
future-choice question as the default (L263), the goal-restated preference question (h), P02's
comma format with a lenient parser (o), P01 with category and placement features (d), A02's twin
pairing keyed on the unit (k), R02's rendering chosen by the reader's own token probabilities (m),
R01's per-world route rendering (l), a forensic step costing 0.015 nats so it pays in half the
worlds (n), the second episode's goal weighing twice so its exact ceiling is −0.50 (q), and the
plan's partial order relaxed in half the worlds so equifinal twins exist (g).
The closed first contract is untouched; landings write through as L284 onward; one final packet.
On exhaustion the wrapper chains into the general queue.**
Twenty-nine cards over eight tracks built on the Stage-4 machinery (`soundingline/stage5.py`,
`runners/s5_*.py`, `run_stage5.sh`): the integrity cards (anchor receipt, parser fixtures and
reader gate with the workload lock, liveness/leakage/collision audit, route-information matrix),
the owed bridge (L255 at a second checkpoint and a second artifact domain, with coordinate, dose,
sign, permuted-label, and own-answer specificity), joint reconstruction on a commission world
with an exact posterior over goal, plan, and preference (six same-evidence readers at one call
allowance; trajectories; the opened missing-goal hypothesis; cross-episode prediction), the
surface-matched source-regime factorial with collision twins (owners, divergent behaviors,
inverse-inverse, labeling and reappraisal, trust), route reliability against ease and
demonstrations, the forensic purchase, drawings at four access levels with equifinal orders,
and foraging items with exact learning-progress rulers; two frozen confirmations on
exhaustion. Guards: thirteen Stage-5 tests plus the eighteen Stage-4 ones, world self-tests,
a scratch-root loop smoke, and the manual inspection of assembled prompts (four construction
defects found and repaired before the clock: a goal latent the evidence could not identify,
a dead learning-progress ruler, a counterevidence question that confirmed the claim, and a
position gate stricter than its Stage-4 band). Predicted in advance from the Stage-4 record:
the model-choice cards (R01, R04, F02) are likely void or null; their fail-closed rulers are
the deliverable. When the scheduler exhausts, the wrapper chains into the general queue.
Landings write through internally as they come; one final packet, then the synthesis.
**STAGE 7 (2026-09-02, his order: review the brief, ask on decision points, then build the whole
thing and set it to run in gear two).** Brief at docs/design/PHASE_2_4_STAGE_7_CONTEXT.md (filed from
the repository root the same day, with his two rulings appended under §5: the interpreter capsule
as the isolation mechanism, and the local-only hard stop retired in favor of clone-or-download
with confirmation). RECORD GATE FIRST: the Stage 6 dependency audit (results/phase_2_4_stage_7/
STAGE6_DEPENDENCY_AUDIT.{json,md}, L330) suspends the tournament ranking, the reader boundary,
M14, M15, and the CoAuthor result; the theory rows carry SUSPENDED (Stage 7 D04, L330) in place.
BUILT (one pass): `runners/stage7/` (contracts; the reader capsule package; constructor worlds
with seven separable factors and a maker-state stop law; controlled mixed-control histories; the
repaired CoAuthor loader; ScholaWrite switches; the six conformance fixtures over the two cloned
reference programs; the isolation runtime with a raising audit hook and the loopback model
server, including the Ollama 9B route; the 100-question registry with identity hashes; the
manifest; the engines for every trunk; the 24 attacks; confirmations; validator; reporter;
fresh-clone verifier; scheduler with the 72-hour ceiling and the signed-keystone gate);
`soundingline/stage7.py`; `tools/test_s7.py` (30 guard tests green); `run_stage7.sh`. RUNS:
`run_stage7.sh` in gear two: the discarded pilot starts the one 72-hour ceiling; the integrity
block and the record gate; the scientific lock waits on the signed keystone audit; the ladder;
the confirmation freeze at hour 64 or exhaustion (at most three claims); one packet at closure.
OPEN ON HIS WORD: none for the launch (he ordered it); his read of the packet at closure.
ATTEMPT 1 STOPPED 2026-09-02 11:04 in its integrity block (L332): I05, I06, I10, and I11
failed on their own should-break cases (the mutant never recomputed its hidden targets; the
order canary was a tautology; a negative fixture went through the builder), and the
read-through of every queued engine found the stop truth false in every world (the cut rule
always left two future steps). REPAIRED the same day: the boundary-walk cut with a reweighted
terminal stratum, the hazard on the last step's goal on both sides of the boundary, the stop
constants raised (natural stop rate 0.047, stop gap 0.080 nats against the 0.05 floor), the
canary, fixture, ledger, sensitivity-gate, rival-pairing, and forced-keyword repairs; 30 guard
tests green; a full scheduler dress rehearsal on a scratch root through the fake transport
(`S7_FAKE_SERVER`) before the clock restarts. RELAUNCHED 2026-09-02 12:44:47 after the rehearsal's fifth pass closed with its packet (a
fresh clock; deadline 2026-09-05 12:44:47); attempt 1 preserved under
results/phase_2_4_stage_7_attempt1/. KEYSTONE SIGNED 13:24:53 (all ten lock gates passed);
THE SCIENTIFIC LOCK OPENED 13:26:54 (L333: 38 integrity cells clean); the ladder runs.
K01 LANDED 14:07 (L334): next action and changed context live; the STOP target under the
0.05 floor (+0.034 [+0.011, +0.064] on 300 worlds), so no reader is tested on stopping this
run; K15 and P05 read as descriptive. OPEN ON HIS WORD: a per-event stop ruler for the next
stage (recommended yes, declared before that run).
K04 LANDED 14:20 (L335): COUNTEREVIDENCE on both readers (−0.46 and −2.62 nats against the
domain model with the complete executable state supplied; the capsule solver equals the
oracle on every world): the reader boundary is state USE; K16 (size ladder) and K05 (language
form) are the diagnosis; K11 to K14 read as diagnosis for this target.
K05 to K10, K15, X10 LANDED by 15:16 (L336): every rung COUNTEREVIDENCE on both readers (the
prose rendering no better; twin reversal followed on 5 to 14 percent of reversing pairs; the
paraphrase attack fails, TV 0.57 against 0.59 under a meaning change, so K05's language-state
claims close). Pending on this trunk: K11 to K14 (diagnosis), K16 (the size ladder).
K11, K12, R06, R07, X11, X16, X18 LANDED by 15:53 (L337): the joint arm returns to the domain
model's level (K11) and clears the floor for SmolLM2 with the belief withheld (K12 +0.29), but
goal recall 12 percent, belief recall 6 percent, twin reversal followed 0 of 14: the gain is
the solver's under a wrong proposal; the ratios void by rule; the twin attacks fail. Pending:
K13, K14, K16; then the reconstruction trunk (R13 cold is the live question).
K12 RERUN (tolerant grammar) LANDED 16:59: SUPPORT_CANDIDATE on both readers (+0.29 and +0.36;
belief recall 0.39; twin follow 1 of 14); K11 rerun identical (L337 reversal block).
R01 LANDED 17:37, RERUN 17:45 under the prose decoding (L341): goal recall 0.23 (Qwen 0.30, SmolLM2
0.17); the gate closed. R02 LANDED 17:56: belief recall 0.37 on both readers, gate closed. R03
RERUN 18:12 (merged law lines): recall 0.33 pooled, Qwen 0.67 (over the bar alone), SmolLM2 0.00;
the pooled gate closed. R04 LANDED 18:19: action-set recall 0.03 (sets of three and seven ids
against nine or ten live options), closed. R05 LANDED 18:26: context recall 0.09 (Qwen 0.18,
SmolLM2 echoes the template), closed. The five recall gates are landed (L341): belief 0.37, law
0.33 (Qwen 0.67), goal 0.23, context 0.09, action set 0.03. X15 INSTRUMENT_FAILED (the
opportunity-blind reading closes). R09 LANDED 18:40 (L342): the learned law transfers (+0.64,
at the oracle's level) and Qwen's proposed law clears the floor (+0.56); the learn_law gate
passes. R10 RERUN 19:13 (L343, after the changed-context repair): the inferred context lands
+0.59 over the domain model on the counterfactual choice and −0.03 against the copied-context
rival, which equals the oracle here; SmolLM2 unrealized on every world. R11 LANDED 19:23 (L344,
the joint rungs; R12 and R13 append): no collapse of goal into belief (recall 0.23 and 0.34), no
gain (Qwen −1.4 nats under the domain model, the price of confident wrong pairs). R12 LANDED
19:47: the law from the prefix alone, Qwen's shape right in 56 percent of worlds, a tenth of a nat
that does not clear the interval; twin reversal followed 0 of 8. R13 FIRST LANDING 20:09 VOID (an
instrument hole: the residue grammar rejected both readers' copy of the prompt's notation on every
row, the joint arm abstained on 120 of 120); the residue, law, and goal grammars repaired; R13,
X01, X20, X06 reset; relaunched 20:19 on the same clock. R13 RERUN LANDED 20:42: cold, Qwen's
joint arm 1.3 nats under the domain model (counterevidence) and 1.6 over the direct reader;
SmolLM2 realizes 15 of 60 (inconclusive); Qwen recalls the law in 68 percent of worlds, the goal
in 42, the belief in 7. X06 and X01 LANDED 20:52 as infrastructure (order permutation TV 0.0;
tail replacement identity 1.0); X20 crashed twice on R13's terminal-cut rows, repaired to the
shared guard, reset with the interrupted R14 and P01, relaunched 20:56 on the same clock. Next:
X20 LANDED 21:15 as infrastructure; P01 reproduces R13's cells. R14 FIRST LANDING 21:15 VOID on
two of three regimes (L345: the batches shared unit ids); the batch takes a unit suffix, R14,
R15, R16, P02 reset, relaunched 21:21 on the same clock. R14 RERUN LANDED 22:15 (L345): maker familiarity does not rescue the cold failure (Qwen −1.75
under DOM, committed on every world); the generic law silences Qwen (prose law on 35 of 40) and
misleads both direct readers; P02 and P03 read R13's rows on the next type and section (folded
into L344). Open instrument note: a prose law decoder for the next stage. R16 LANDED 22:30 (L346):
abstention does not track ambiguity (false abstention 0.73 against 0.59 on equivalence cases;
SmolLM2 abstains by failure to propose); the discriminator measure is 1.0 by construction, an
instrument gap for the next stage. R15 (L345): the generic law halves candidate entropy with
calibration at chance. P04 (L344): the rejected alternative, counterevidence on both arms. X12 LANDED
22:35 as infrastructure; P05, P06 counterevidence, P06's six cells identical to the digit: R13's
target list covered two of the seven targets the P analyses read (L344, a fill hole). R13 asks
every target now; R13, P01 to P07, X01, X06, X12, X20, A14, X02 reset and rerun from 22:41.
R13 RERUN 23:06 reproduces its primary; the attacks pass again; P01 to P04 LANDED with real
direct-reader cells (L344). A14 FIRST LANDING 23:26 hollow (the particle arm never initialized:
the proposers called bare); one proposer dispatch for every arm, A14, A15, P05, P06 reset,
relaunched 23:30. A14 RERUN LANDED 23:39 (L347): the sequential particle arm equals the one-shot
joint posterior (+0.02) because the readers propose one candidate set on 48 of 60 worlds (a
breadth-forcing proposer is next-stage work). P05 (the stop: DOM within 0.05 nats of the oracle,
every reader arm under it) and P06 (the boundary type: the joint arm's point mass hits the floor on
8 of 10 Qwen worlds; the direct reader a valid null on SmolLM2) folded into L344. A15 LANDED 00:39
(L348): every structured arm beats the direct reader (+1.4 to +2.1 nats) and none beats the domain
model; the direct reader is 2.1 under the prior; unrealized arms fall back to it. P07 (the changed
context: joint pooled a valid null, direct counterevidence) and X02 (I06 identity 1.0) folded into
L344. A16 LANDED 00:57 (L349): with everything supplied a larger model uses the state no better
(−1.0, −1.6, −3.1 nats to 3B; −0.55 at the 9B route, goal recall 0.67); P08 (the invalidation
response: nothing to take on a target the prior nearly owns) closes the eight P analyses over
R13's rows; X09 confirms the compute pricing. P09 LANDED 01:18 (L350): over the whole withheld
tail the joint arm is a nat under the domain model, spread across the events; the direct reader
2.7 and 8.7 under. X03 (I07 identity 1.0) and X21 (22 conditional cells before pooling; a sign
reversal under pooling) pass. P12 LANDED 01:24 and P11 (14:11, unwritten until now) with it (L351): the process reader
localizes a one-time control switch from the record and survives style matching (+1.92 over the
stylometry stack); not alternating control, not a pure style shift; no free-text reader beats the
stack; nothing from the final artifact. P10 (L346): the joint arm's confidence is anti-informative
(ECE 0.51, worse with dose). P13 LANDED 01:34 (L352): on the CoAuthor record the
position table is the best predictor and the readers are under it (−0.30, −1.57 nats), no better
than the prior decision. X14 FIRED (INSTRUMENT_FAILED): the readers do not preserve the equivalence
class by the run's criterion (R16's false abstention 0.73 against a ceiling of 0.5; L346). X22
passes on P12. P14 LANDED 01:41 (L353): on ScholaWrite the reader is under persistence where the
label holds and under uniform where it switches; the card's support label rests on two sessions
(a switch-dense window is next-stage work). V01 LANDED 01:50 (L354, the V-family entry; V02 to V06 append): the habit is named on 56 percent
of worlds, the goal on 24, and the executed pairs are under the domain model whether the goal
opposes the habit or not (the redirection is not read). V02 LANDED 01:56: with everything but the
goal supplied, the reader's goal is under the goal-blind solver (−0.33 pooled, counterevidence)
while the oracle's goal is worth 0.47 over DOM. V03 LANDED 02:03: the law and the goal both withheld, the reader names
neither (law recall 0; SmolLM2 unrealized on every world); Qwen's pairs 0.77 under DOM where a
lagging expertise opposes the goal, 0.45 where aligned. V04 LANDED 02:03 (programs): the mixture
over dated episodes and a forced point date predict the present alike (−0.01). V05 LANDED 02:05
(programs): the dated, ordered, and aggregate views of earlier episodes predict a later one alike
(valid nulls). V06 LANDED 02:06 (programs): the dated trajectory carries the law (+0.42 over DOM)
and nothing beyond the aggregate for a later costly choice (+0.05); X19 passes. The V family is
closed (L354, V-S7, TT-S7). LADDER RUNG 4: P09/x4 LANDED 02:32 (L350): a fresh draw with longer tails
agrees with the base on every line (joint pooled −0.94 under DOM over the tail). R13/x4 LANDED
02:56: the cold rung on a fresh draw sits at the domain model (SmolLM2 −0.10 valid null, Qwen +0.03),
so its counterevidence narrows to "at or under, by the draw" (L344). THE FREEZE FIRED 02:56 on
ladder exhaustion: two claims, K14 (slot 1, +0.57) and A11 (slot 2, +2.86 against the direct
reader; −0.72 against DOM, L356). A08 (L355) and A11 (L356), landed 2026-09-02 and unwritten until
now, are entered. B05 FAILED BY TIMING (its coverage counted the pending closure cells, itself
included) and was started twice; the coverage check now excludes the closure tail, a cell in two
lists starts once (both effective at the next launch); B05 reruns after B03 lands (stop, reset
B05 and any B06/X24 that ran, relaunch). B01 LANDED 03:15 CONFIRMED (L339): the learned law transfers on untouched lineages (+0.62 [+0.25,
+1.02] over DOM); the readers inconclusive. X24 started early (before B02, B03; to be reset with
B05). B02 LANDED 03:24 CONFIRMED against the direct reader (Qwen +3.59 [+2.34, +4.78]) and
counterevidence against DOM (pooled −0.32) (L356). B03 NOT_RUN (no third claim). Rung 9 admitted:
B01/x9 runs; B06 started early on the failed B05. B01/x9 LANDED 03:43
(+0.55 [+0.28, +0.81], 98 worlds; Qwen's proposed law +0.27 at the threshold). B06 DESCRIPTIVE.
STAGE 7 CLOSED SHORT 03:43 at hour 15.0 (the locked workload and ladder exhausted; cause written);
THE PACKET IS WRITTEN (L357). B05 and X24 rerun after closure as addendum cells (B05/rerun: every
ledger agrees; X24/rerun: 124 verdicts clean); the packet stands. Curator decisions (L357): a
Stage 8 on the construction list; whether to regenerate the packet with the addendum (recommended
no). Nothing since 514e80b5 is committed; the commit waits on his word.
K16 LANDED 17:30 (L340): the size ladder (0.5B, 1.5B, 3B, the 9B route) COUNTEREVIDENCE at every
size with the complete state supplied (the 9B −1.06 nats, the best); the solver's line beside
the state helps none. The K trunk is closed; the R trunk runs.
K14 LANDED 16:41 and RERUN 17:07 (L339): the two program routes SUPPORT (selection +0.59, a law
learned from two demonstrations +0.57; indistinguishable); the joint reader realized on 16 of
120 rows (the readers echo the candidate tables). Pending: K16; R03 (law recall without
candidates); R09 (learned-law transfer).
K13 RERUN LANDED 16:28 (L338): COUNTEREVIDENCE (−5.0 and −11.5 nats against the domain model;
recall of the true subjective set 5 percent); the first landing (every row unrealized at zero
contrast) was an instrument defect, repaired and rerun. Pending: K14, K16; the R trunk. THEORY ERRATA
(Stage 7) APPLIED 2026-09-02 (L331), archived under docs/design/archive/.

**STAGE 6 (2026-08-30, his order: build front to back, continuous gear 2 through the week; INTERPRETATION SUSPENDED 2026-09-02 by the Stage 7 dependency audit, L330: the tournament ranking, the reader boundary, M14, M15, and T02 do not stand; supplied-law selection and the construction facts do).** LAUNCHED
15:39 (the pilot started the immutable 168-hour clock; deadline 2026-09-06 15:39). BUILT:
the full 104-card, 24-attack contextual maker-state program (registry Stage-6 section for the build log
and deviations; `runners/stage6/`; 21 guard tests green). RUNS: `run_stage6.sh` — the discarded pilot
starts the immutable 168-hour clock; integrity block, scientific lock, tournament, tracks, records,
attacks, hour-144 confirmation freeze, the one packet after hour 168. OPEN ON HIS WORD: none for the
launch (he ordered it). T03 closed NOT_RUN on its predeclared RESOURCE_BLOCKED disposition at the
scientific lock (no local corpus; L317). Running state (2026-08-30 17:36, hour 2): discovery, the
records trunk, and the attack wave are landed and written through as L315–L317; V06/V11/V12/V14
re-run under the differentiated specs and B01/B02/B04 wait for the hour-144 freeze (the three
runtime defects and their repairs: the registry's Stage-6 defect log); P10's realizer-ablation
re-run went active at the restart; the nine-rung ladder resumes at M08/x1. The four V re-runs LANDED DISTINCT (L318) and the ladder's first pass is written through (L319:
records and capability boundaries HOLD at scale; breadth holds at 4536 rows; no sign flips). Four
08-31 infrastructure defects repaired on the clock (one-cell-per-rung admission, expansion-contrast
pairing, P10 goal-weight completion, reset path for expansion cells — registry defect log); P10 and
the three VOID contrast cells re-run repaired. P10 landed DIFFERENTIATED (L320) and all three reset contrast cells confirm at fortyfold (L320,
L321: M08/x1 −0.071, M08/x2 −0.067, M04/x8 −0.021; all perm values ledgered). The rung-one refill landed through V14/x1 (L322: the flag CLOSED, the −0.3 regime representative;
C03/x1 +0.45 and C11/x1 valid null at 3840; M02/x1 +0.88 at 10240). Instrument note (v-real): the
collapsed-spec V run realized every unit where the differentiated re-runs leave 23 to 29 percent
of value worlds unrealized; mechanism unexplained, superseded, low priority. Rung one CLOSED (L323: A10/x1 +0.79; F11/x1 at the marginal with a hidden-goal attractor; T01/x1
and T04/x1 repeat the records boundary, T01/x1 an offset-inert duplicate of x4 by construction).
Rungs two and three landed (L324: the paraphrase asymmetry holds at scale, TV 0.000 against 0.470
for the realizer and 0.168 against 0.332 for the label posterior; the ablation ordering replicates
on fresh worlds; P10 and I08 code their unit counts so their multipliers were inert). PACE: the
locked ladder exhausts near hour 45 against a 158-hour forecast; by rule the run then freezes,
confirms, closes SHORT, and the packet waits for `scheduler.py final-packet` after hour 168 (a
queued packet-waiter stage does that). Gear two is loaded behind the close (2026-09-01): the (l2) archaic cross, the (m2)
equal-length construction, and the packet waiter are queued as produces-guarded stages. Rungs four to seven landed (L325: A12 holds +0.28; A13's discovery separation DIES at scale,
−0.03 on 1248 fresh units against the 48-world +0.67; V06 tightens just over its band; F02, F03,
and F09 named as one statistic under three questions; records duplicates as predicted). CLOSED SHORT BY RULE 2026-09-01 14:43 at hour 47.1 (L326): 160 cells complete; confirmations
+0.85 and +0.23 on untouched lineages, B01/x9 +0.89 at 3584; routing reads 'a published scaffold
wins'; SHORT_RUN and RUNTIME written; the reporter refused the early packet; the chain launched
the general queue; both receipts landed within the hour (L327). THE PACKET WAS TAKEN EARLY on
his ruling (2026-09-01 15:17, L328): validation clean, the synthesis written, the waiter
cancelled; staged, committed, and pushed on his order the same day. His read is the open item.
Ordered next (same transcript): BUILT, QUEUED, AND LANDED 2026-09-01 within the hour (L329):
the confidence series VALID_NULL (+0.012 pooled, after the pooled-series repair); the
consolidation chassis INSTRUMENT_FAILED twice (sanity 0.23 then 0.25; its predeclared repair
spent) and closes with the s6-t1 question open: a future attempt needs an
identifiability-derived distinctness gate and higher-contrast constants (LESSONS §3); the freeze fires at hour 144 and not before; the packet only after hour 168. Opened by the
2026-08-31 update errata: (s6-t1) consolidation-map worlds — attention specified INDEPENDENTLY
of the resulting expertise (the K-update line's non-circularity requirement), a lossy
consolidation transform with interference, and recoverability asked of the exact layer before
any reader; BUILT AND QUEUED 2026-09-01 on his order, the design-only note superseded
(runners/s6_consolidation.py, exact layer first); INSTRUMENT_FAILED twice the same day (L329),
the question open with the fix-direction in LESSONS §3.

Landed so far: the reader gate admitted Qwen2.5-1.5B only (L256; SmolLM2 0.104 on the 0.10 position
band, the 3B 0.33 on the cheap option), so every Stage-5 card is single-reader; the bridge on SmolLM2
as the steered checkpoint showed no congruent benefit with both controls negative and its decode at
chance (L257). Opened: (a) DONE 2026-08-29 (L282: SmolLM2 admitted at 96, the 3B refused on a stable per-option
failure); (b) BLOCKED 2026-08-30 (L313: no local checkpoint passes the reader gate; the 3B's failure is stable and
there is no other Qwen instruct checkpoint here); a candidate needs a download or gear 3, his call; (c) a direction-transfer check (directions fit on SmolLM2-made artifacts,
tested within family) to separate representation-not-used from directions-not-transferring.
Then: the anchor's congruent effect held on a second artifact domain in both folds but the random
direction was not quiet (L258; B03's arms decide whether that is dose); the next-stroke predictor fell
under the cheap priors at every access level (L259). Opened: (d) after the run, refit P01 with the
category and bounding-box priors as features so the access ladder is tested above them.
Then: the specificity battery killed L255's selectivity clause (random, shifted, random-block, and
permuted-label arms as loud as congruent; sign specific; L260); the rulers found the reader attributing
the episode goal's axis to the standing preference in two thirds of worlds and no equifinal world in
the lane (L261); competence by access unresolved (L262). Opened: (e) DONE 2026-08-29 (L283: not the seeds; the cards' per-arm option orders on a two-nat
letter effect; fixed-order batteries are the standing numbers); (f) the theory rows citing L255 as
causal use are revised (done in the three-layers file); (g) a joint-world construction with two valid
plan orders so the equifinality abstention ruler has worlds; (h) DONE (L290: the goal restated inside the question leaves the attribution at 166 of 256; a reading, not
a prompt effect); (g) DONE (L290: 220 equifinal worlds, abstention 0.52).
Then: J02 v1 died to option wording (L263): J04/J05 withdrawn, J02/v2, J04/v2, J05/v2 queued on the
repaired question; the trajectories show no appropriate revision after a contradiction (L264).
Opened: (i) DONE (L278 reads every variant against the uniform floor of −1.39 and the exact ceiling of −1.04;
the repair cells are under the floor).
Then, the appraisal track (L265 to L269): the reader answers constants on the source world's legible
factors, predicts no behavior, never abstains on twins, and every influence warning is a criterion
shift. Opened: (j) BLOCKED 2026-08-30 (L313: six local checkpoints from four families, none reads the calm-against-alarmed
half in both domains; the 3B reads the action half at 0.96); the re-run waits on a reader this machine does not
hold, a gear-3 question for him; (k) DONE (design 2, L296: 1,024 pairs); (u) DONE 2026-08-29 (the near-equal clause removed; abstention is unknown mass; guarded by test 18).
Then: R01's support over random is a fluency policy (always-easiest beats the reader; L270). Opened:
(l) DONE 2026-08-30 (L311: the harder-rendered description is taken MORE, −0.25 of probability for the plain one on
both readers; the fluency policy is dead; anomaly attraction replaces it). Opened: (l2) LANDED 2026-09-01 (L327: difficulty attracts, −0.24 pooled, not visual anomaly): the same cross with the
archaic rendering (harder by the ruler, not visually deviant) to separate difficulty from anomaly; and the anomaly
bias is a confound for every menu whose options differ in surface form (the J-track candidates, the source-gate
options), to be checked by a surface-matched audit of those menus. The build: each world asked three times, both
descriptions plain, the record's in the validated hard rendering with the note's plain, and the reverse; the
rendering chosen per reader by the margin with which it flips the record/note ease order (a description's ease is
a per-reader constant); the within-world contrast is the probability of taking the record when its own
description is plain minus when it is hard; a fluency policy moves it, an information policy does not.
Then: R02's stilted rendering is the more fluent text by the reader's token probabilities, so its ease
arm was unrealized; stated reliance rises with the number of records (L271). Opened: (m) RULER VALIDATED 2026-08-30 (L310: the total log probability and the token count pass at 64 of 64 on both
readers; the mean fails every sample; the content-only total fails the mid-dots on Qwen); R02 re-run under it DONE
(L314: ease never draws reliance on either reader, capitals relied on slightly more by Qwen; the quantity effect is
Qwen's alone, SmolLM2 flat). Opened: (m2) LANDED 2026-09-01 (L327: information +0.075, length −0.003): an information-at-equal-length construction to separate quantity from
information in stated reliance (design item). The build: four rulers
(content-token total, total log probability, token count, and L301's mean) validated on the known-answer
renderings at 0.95 of 64 samples on both readers; the passing ruler and the rendering it rates hardest realize
the ease arm, and R02's interaction is asked again on 256 worlds per reader; VOID if no ruler passes.
Then: demonstrations are followed to the letter in every world, familiarization not expertise (L272);
the forensic purchase is cost-blind (L273). Opened: (n) DONE (design 2, L303: the step pays in a third of worlds; the readers buy at one rate
everywhere and realize nothing from what they buy).
Then: enactable drawing orders from shuffled strokes at 37 percent validity, determinacy claimed on
equifinal artifacts (L274); foraging for the familiar, a coin flip's gain, no hope bias (L275 to L277).
Opened: (o) DONE 2026-08-30 (L312: genuine first-turn proposals enactable at 0.82 against 0.17; a second turn
recovers Qwen at half the quality and SmolLM2 not at all; the attempt rate is the reader's). The build: an echo of
the listing is no proposal, one
second turn shows the reader its echo and asks again, the genuine population is scored against the 23-order blind
rate, the two turns reported apart; 240 drawings per reader.
Then: J02/v2 lands every reader under uniform with the oracle no better than the recurrent reader
(L278). Opened: (p) BLOCKED 2026-08-30 (L313: no local checkpoint maps stated latents onto the choice above uniform;
the 3B inverts it at −3.94 against −1.39); the joint track's third run waits on a reader this machine does not hold.
Then: the opened missing-goal hypothesis is never taken; the conflict goes undetected (L279); the
inferred preference predicts the next episode worse than the topic prior (L280). Opened: (q) DONE (design 2, L293: the ceiling raised to 0.68 above uniform; the readers still lose to the
topic prior).
Post-run: (s) the bridge runners (`s5_run_b.run_bridge`, and Stage 3's a07b arm) take a fixed option
order per artifact across arms (one line each), before any bridge card runs again; the landed
verdicts stay as landed, the fixed-order receipts are the standing numbers (L283).
(t) DONE (L284, L309): the intensity closers were imperatives; repaired under design 2 before the
appraisal cards ran; on the repaired text the action question reaches 0.88 / 0.75 for Qwen (from 0.25 /
0.34) and the arousal half is the readers' floor.
(v) DONE 2026-08-29 (the integrity runners' card directory honors S5_CELL; guarded by test 18).
(r) RESOLVED BY THE SECOND CONTRACT for SmolLM2 (it ran every track, L284 to L308, gate-failed on the joint and
appraisal tracks); what remains his call is a third run of those two tracks on a reader the gate census (j)/(p)
admits; the census (L313) admits none, so the question is a gear-3 question: whether to gate a 7B-class reader on
the three gates before any third run (recommended: not yet).

**Stage 4 (context, appraisal, selective uptake) is CLOSED: RUN_TO_EMPTY at 19:33 on 2026-08-28,
21.2 hours elapsed, 14.95 GPU hours held, 307 of 322 expected cells complete, both eligible
candidates (A01, T01) confirmed on the fresh reserve, the packet and the analyst's synthesis at
results/phase_2_4_stage_4/CURATOR_PACKET_FINAL.md, awaiting his assessment. Its run, for the
record: launched under second gear on his order,
launched 2026-08-27T22:22:50 after the build, the card-by-card smoke, and the manual
validation pass (twenty-eight defects repaired, three loop smokes); STOPPED 2026-08-28 05:57
on his order when the parallel agent-hardening audit found the T-track construction defect
(R7 below) and RESTARTED at half past six after the repair, with T01, T02, T03 re-planned at the
head of the queue (their first attempts preserved under superseded_domain_defect/); brief at
docs/design/PHASE_2_4_STAGE_4_CONTEXT.md.** Eighteen cards; the contract's 24-hour deadline
is accounting only (his ruling: second gear runs until the queue is empty); the closure
block (F01) begins on exhaustion of the admitted work and the expansion ladder, then the
single final curator packet (the machine draft, then the analyst's synthesis); when the
scheduler exhausts, run_stage4.sh chains into run_second_gear.sh, which carries the five
Stage-3 re-runs below (R1 to R5) to the queue's natural end. Landings write through
internally as they come; no interim chat reports by the brief's contract. Known instrument risks carried into the run, each with its
honest outcome class: T01's readers echoed the advice on every novel case in the smoke
(copying, INSTRUMENT_FAILED on the support gate); C03's readers chose the redundant
probe three times in four (a selection COUNTEREVIDENCE); T03's technique lesson made the
readers reject everything (a criterion shift, VALID_NULL).
Landed so far, written through internally with no interim chat packet by the brief's
contract: I01 (the audit receipt; L236 verified to the digit), P01 (L237, INCONCLUSIVE on the
frozen balanced estimand after an in-run estimand repair, first verdict preserved), P02
(L238, SUPPORT_CANDIDATE, +0.20 over the longest-stroke rule), C01 (L239, INCONCLUSIVE:
+0.10 nats for the bundle over the same facts, and a wrong bundle costs nothing), H03 (L240,
COUNTEREVIDENCE: the edit's text forecasts the next intention boundary 0.011 under duration
and persistence alone, five projects), C02 (L241, COUNTEREVIDENCE: six records after a
misleading prior lower the score by 0.20 nats; the readers do not correct), A01 (L242,
SUPPORT_CANDIDATE: valuation and aim recovered +0.14 over the floor, crossed; enacted source
usable at 0.86 realization; no abstention when the fact is withheld), A02 (L243, INCONCLUSIVE
with loud controls: aligned benefit -0.04 nats, own-choice shift 0.2; the bridge is unbuilt),
T01 (L244, SUPPORT_CANDIDATE, re-landed 08:07 on 128 distinct constructions after the R7
repair: a worked action mapping lifts as-taught learning +0.13 aligned and +0.20 misaligned,
true and false rules alike; the advice is followed 92 to 99 times in 100 regardless; the first
attempt on 54 distinct constructions had read +0.16 with an interval too narrow), T02 (L245,
SUPPORT_CANDIDATE on the frozen band, read as Narrows: reconstruction beats a matched summary by
+0.62 nats and loses to the direct read by 0.25; the rule is not inferred from the record and
is usable when told), C03 (L246, COUNTEREVIDENCE: the redundant probe chosen 0.78, 8 percent of
the oracle's gain captured), A03 (L247, VALID_NULL: intake-phase minus answer-phase steering
-0.05 nats), T03 (L248, VALID_NULL with a criterion shift: AUROC unchanged at chance, true-advice
acceptance -0.37), H01 (L249, COUNTEREVIDENCE: shared-convention decay 13 points steeper,
attribution 0.22), H02 (L250, VALID_NULL: -0.004 from the ordered history, -0.5 nats on the
later decision); the expansion rung (256 worlds, or 192 histories) re-landed C01 (held), C02
(COUNTEREVIDENCE to INCONCLUSIVE, a flat curve), A01 (held), A02 (INCONCLUSIVE to
COUNTEREVIDENCE), T01 (held), T02, T03, C03, H02 (held); F01 opened 16:52 on the two eligible
candidates: A01 CONFIRMED on 256 fresh worlds (+0.12 [+0.07, +0.17]), T01 CONFIRMED (+0.15
[+0.11, +0.18], the support gate passed on the reserve). All fifteen written through at 20:00
after the agent's session loss at 08:10 (the named leak, eleven hours); the closure and the
five re-runs at 23:50 the same night. The scheduler's manifest
keeps the first outcome tally for P01 and P02 (one writer, the loop); the verdict files on
disk, which the closure block and the packet read, carry the repaired ones.

**Stage 3 (E24-S3, the week-long inversion forest) is PROGRAM-EXHAUSTED (2026-08-27 05:07, validator-confirmed).** 73 cells: 61 LANDED, 11 INSTRUMENT_FAILED (all informative), 1 RESOURCE_BLOCKED (H07, no OpenReview mirror); 72 of 48 required valid attempts; 0 GPU-hours remaining. Every result is written through as L171-L235 with theory rows, the tools ledger, five new method lessons, and the multiplicity audit rerun; the theory-citation completeness pass of 08-27 closed every filing gap it found (L178, L204, L210-L213, L218, L221 added to their rows; L184 retracted by its adversary, L226). The queue drained inside one second-gear window and the until-empty chain ended on its own; gear is idle. Build and record committed and pushed 2026-08-27 (6feda02, 858f83a); the 08-27 write-through goes up in the next commit. The reserve-quarter refresh landed (L235: all three expansion contrasts hold on the untouched quarter). Remaining before his assessment: the final two-pass curator packet; then the program waits on his read. H08 protocol and V07 case-study spec stand LANDED as documents (prepare-only).

**RE-RUNS OWED BY THE STAGE-4 THEORY ERRATA (2026-08-28; the errata was applied and its file removed with the rest 2026-08-30 — the theory owners are the record).**
The errata's audit corrections are applied to the theory files, which means six claims are now
stated at the strength their measurements actually support. Five of them are recoverable by
re-running with the defect fixed; each needs its runner arm written or corrected first, and none
can start until Stage 4 releases the GPU. **No Stage-3 artifact is corrupt**: the completion
validator (H4) reads 72 of 73 produces intact, the one absent file belonging to M02, which is
INSTRUMENT_FAILED with a recorded reason and zero GPU minutes and so never had a verdict to write.
These are method defects, not data loss. Preserve every original output; each re-run writes to a
new produces path.

| | re-run | the defect, and what would settle it |
|---|---|---|
| **R1 · S05/X3 eraser rung** (blocks the strongest G172 claim) | **LANDED 2026-08-28 21:22 (L251): own-minus-other 0.001 in both families with 82 and 61 survivors, powered zero** (`s3x_s05x3b`, cell E24-S3-S05/X3b): `s3_run_s.py --arm s05x3b`, up to eight regeneration attempts per artifact against one summary (attempt 0 reproduces the first run's seed), the own side averaged over same-family readers (L236); a family under floor after every attempt closes INSTRUMENT_FAILED, never null | The OLMo eraser retained **88 of 250** artifacts (162 dropped unrealized) and SmolLM's surviving n = 31 sits **below its own declared survivor floor of 40**, so the attenuation-to-zero read is confounded with attrition and one arm was never powered. Fix: more generation attempts per artifact, realization gate unchanged, until both families clear floor 40. Null: own-minus-other 0 under a stake-free eraser. Alternative: a positive own-family margin survives. Direction: the through-eraser claim dies if the margin stays at zero **with both families above floor**, which is the thing the current run cannot say. GPU |
| **R2 · HH-25 wish override** (L213/L214/L231) | **LANDED 2026-08-28 (L252): the override stands parser-free, 0.79 and 0.92; refusals and contamination small and separated** (`s3x_c06b`, cell E24-S3-C06/R2): `s3_run_c.py --arm c06b`, the same items under none/agree/conflict/stranger for both readers, every generation attempt persisted, parse failures (no choice, several options) and hint contamination as separate cells, and a parser-free label-likelihood readout as the primary; covers C06 and XV3 | The raw generations were never saved and a phrase-matching parser stood in for them, so compliance, answer contamination, task confusion, and extraction error are all unresolved behind the 40/48 and 45/47 numbers. Fix: persist every generation, replace the parser, report refusal and contamination as separate cells. Until then the psychological reading is instrument-dead, not evidence about belief adoption. GPU |
| **R3 · H04-S3 uptake decision unit** (L207) | **LANDED 2026-08-28 (L253): pairwise 0.55 within the set, first-position 0.47, between-set AUC 0.51** (`s3x_h04b`, cell E24-S3-H04/R3): `s3_run_h.py --arm h04b`, within-set rank of the chosen suggestion among the ones shown (pairwise and top-1 against 1/k, first-position and length top-1 rates beside it) and every member of a closed set as an individually dismissed item against the selected ones, session-clustered; 12,597 decidable sets over 1,397 sessions | A dismissed set of five suggestions was represented by its first suggestion, which is not the same decision unit as an individually selected one, so AUC 0.499 does not measure what the card asked. Fix: score individually selected against individually dismissed suggestions. GPU (the reader scores the fit; the errata's CPU label was wrong) |
| **R4 · L01-L05 carrier** (XV4) | **LANDED 2026-08-28 (L254): 11 of 12 by scalars and by representation alike, p 0.03 each; the carrier is surface-trivial, the failure is at uptake** (`s3x_xv4b`, cell E24-S3-XV4/R4): `s3_run_x.py --arm xv4b`, leave-one-seed-out over six seeds (twelve decisions per readout), all length-matched sequences (231 to 257 per condition and seed, no cap), an exact within-pair swap null; the scalar read alone already lands 11 of 12 (p 0.03) on the CPU dry run, so the representation read decides | The adversary and length-matched reads (3/4 and 2/4) sit on a held-out set too small to separate a real carrier from none, so neither carrier absence nor an uptake-only failure is established. The uptake null itself stands and does not need re-running. GPU |
| **R5 · A07-S3 bridge** (L202) | **LANDED 2026-08-28 (L255): congruent steering +0.4 to +0.8 nats on the held-out maker's tendency in both folds, controls quiet; floor unmet, second checkpoint and domain recommended** (`s3x_a07b`, cell E24-S3-A07/R5): `s3_run_a.py --arm a07b`, two held-out-maker folds (fit on SmolLM's 87 stripped artifacts, test on Qwen's 48, and the reverse), nearest-centroid decode, prompted four-way inference, and that inference under congruent / incongruent / random / zero steering at the A07 locus and dose; the card's two-domain two-checkpoint floor is not met and the receipt says so | Own-impulse steering was measured; prediction of a held-out maker never was, so the affect-to-inversion bridge is OPEN by omission rather than by result. GPU |
| **R6 · H05-S3 cross-act claim** (L174) | **blocked on corpus** | ArgRewrite spreadsheet order is not a chronological edit stream, so the 0.394 result cannot support "goals persist within acts and switch between acts." The claim is retracted in theory; reinstating it needs a corpus with real edit chronology. Not queueable as-is |

**Also owed, documentation not compute:** the XV3 and XV4 audit observations need linked method
receipts before their numbers may enter canonical theory (errata §4).

**Landed (2026-08-28 19:34 to 21:22):** all five ran in the chained gear after Stage 4 exhausted
(R1 104 GPU minutes, the rest under eleven each); the Stage-3 validator reads exhausted again
(78 cells, 77 of 48 valid attempts); the queue is empty and the gear exited on its own. R6
stays blocked on a corpus with real edit chronology. One decision opened by L255: a second
checkpoint and a second artifact domain for the causal-use read, about an hour of GPU.

**Also owed, documentation:** the strict `design_lint --changed` (rewritten 2026-08-28 by the
hardening pass) rejects six pre-existing headers in files this repair touched
(`runners/audit_multiplicity.py`, `run_queue.py`, `s4_run_common.py`, `s4_scheduler.py` have no
DESIGN CHECK block under its gate-bearing heuristic; `s4_run_h.py` and `s4_run_i.py` state
gates without a null derivation or an exhaustiveness claim in the strict form); the five new
re-run arms and the repaired T runner and world module pass it by path. Bring the six up to the
strict form, or record the infrastructure files as exempt, before the next build.

**R7 · THE T-TRACK CONSTRUCTION DEFECT: REPAIRED, RE-QUEUED, RUNNING (found 2026-08-28 by the
agent-hardening audit; repaired the same morning on his order, receipts in the registry).**
*Status 2026-08-28: the run was stopped with T02 94 minutes in; my own rebuild of every
allocated world confirmed and sharpened the count (T01 discovery 54 distinct of 128; the 256
confirmation units saturated the same 64-world space, so F01 would have confirmed on inspected
constructions; every other card fully distinct). The constructor now enumerates a per-domain
identity space (twelve rule families per domain, 384 constructions, discovery and confirmation
in disjoint halves, over-allocation raises), every root construction registers a content hash
on its lineage (the dead duplicate control is live and reports what it checked), every row
carries the hash and every interval clusters on it, the lineage ledger is a lock-held
reload-modify-write, the scheduler has a reset op that preserves a first attempt, and
tools/s4_construction_audit.py reads the whole ledger (2,368 root units, all distinct). Four
new guard tests (18 pass); a GPU smoke on a scratch root ran the freeze, the three T cards,
validate, the reset, and a re-landing. T01 and T02 were reset and run first after the
restart; T03 follows in preservation order. T01 re-landed 08:07 (97 minutes): same band, interval
wider as predicted; T02 running.* The finding as recorded by the audit: `make_lesson_world` in `runners/s4_worlds.py` accepts a `domain` argument, stores it in
the returned world, and **never uses it to select content**. It is the only one of the five world
constructors that does not: `make_world`, `make_appraisal_world`, `make_chain_world` and
`make_history_world` all index `_ITEMS[domain]`, `_SCENS[domain]` or `_HAZARDS[domain]`. The rule
pool `_RULE_WORLDS` holds four entries, so the whole lesson-world identity space is 64 worlds and
**61 of those 64 groups appear under both domains**. Measured on the landed data: T01 has 128
nominal units and **31 distinct constructions**; T02 inherits it through its derived lineages.

Two consequences, neither of which is fixed by restarting, because the same code rebuilds the
same worlds:

- **The T-track domain factor is a label with no realized contrast.** Any workshop-versus-civic
  comparison on T cards compares identical constructions. It must be reported as unrealized, not
  as a null result.
- **Effective n is overstated about fourfold.** T01's verdict records `n_units: 128` and clusters
  its bootstrap on that, giving ci [0.117, 0.199] and perm_p 5e-5 around a point of 0.156. The
  point estimate is a within-world paired contrast and is unaffected; the interval is roughly
  half the width it should be, since resampling 128 clusters that are really about 31 worlds
  narrows it by around the square root of 128/31. The SUPPORT_CANDIDATE direction probably
  survives correction, since even a doubled interval clears the frozen 0.05 threshold, but the
  stated precision does not.

**Fix before any T-track result is promoted:** index the rule pool by domain and enlarge it, so
the lesson world varies with domain and the pool is not four deep; then re-run T01, T02 and T03
and recompute clustering on the world rather than the nominal unit. **Do not edit
`runners/s4_worlds.py` while Stage 4 is running** — every card the scheduler has yet to spawn
imports it, which is the same class of hazard `_fresh()` was introduced to close for the run
contract. C and A tracks are unaffected (C02 renders 128 distinct constructions of 128; A01
renders 127 of 128, its one collision a benign same-domain RNG repeat).

| | study | state |
|---|---|---|
| **G130 · the event-recovery harness** | Five known-answer gates on synthetic decision events before any real corpus | **VALID (L56), eyebrow CLOSED (2026-08-19): the unchanged arm at 5× n across three fresh seeds reads 0.249/0.249/0.240 — the 0.282 was seed noise; all gates green all seeds** |
| **PD-33 · essay-boundness decomposition** | Author against draft grouping on the 258-draft cache | **MAKER (L57).** Polish-side author share 0.262 vs depth 0.174, p = 6 × 10⁻⁷; draft shares tiny and equal. The maker-signature claim's second number |
| **G128 · the alignment permutation null** | Text-correspondence broken 100× per family; do L45's landing depths survive? | **done (L58): 6 of 10 cells REAL.** The late locus survives in all four decidable families; the early landings are partly matrix smoothness; SmolLM2 undecidable |

## Phase 1 — recreate the frontier before pushing past it

**The pass standard, his ruling (2026-08-10).** A recreation passes by reproducing the published
**exact values**, close enough that a thousandth-place discrepancy reads as a typo, never by
reproducing the conclusions. Landing well below a published number means our model of their
pipeline is wrong, and the gap is a defect to hunt, not a caveat to record. This includes
downloading, running, and then removing the exact model a paper used. Stochastic and version
variation may be *mentioned*, never leaned on. Nothing below advances to its Phase 2 extension
until its recreation passes this bar.

**Re-audited under the exact-value standard (2026-08-10): none of the six previously claimed
anchors was a value-exact pass.** Each is reclassified below by what the standard can even ask of
it. Only one true value pass exists so far, the impossibility construction's analytic 0.5/0.5
(L60). The phase does not close until every row below reads PASSED or EXEMPT-with-reason.

| anchor | its published value | what we did | honest status |
|---|---|---|---|
| ArgRewrite classification | binary F1 .93/.93, fine .51/.63 (fetched, Tables 6/7); fine Majority gate corrected to .05/.32 per the paper's own Table 4 (the printed .29/.45 row contradicts it, L79) | construction pinned at source (L79); v4 extractor rebuilt, 3,236 of 3,238 with cycle-1 exact | **NOT PASSED, COMPOSITION CLOSED.** The unit is the Revision Index group with multi-purpose discard (not first-pick); both L76 candidates died (precision is a real class; the .290 share was a bad row). v4 landed (L80) and the agent's final diagnosis re-scoped the gates: the per-class gap partitions perfectly along §5.4.1's augmentation list (−.025 mean on the four non-augmented classes, −.338 on the five augmented), so the fine BASE rows were computed on an already-oversampled set (inference, three converging facts) and are NOT reproducible from the released 3,238; our ~.30 is the correct unaugmented number. Re-scoped pass: fine majority .32/.48 exact (MET), four non-augmented classes within ~.10 (MET), five augmented classes exempt-with-evidence; the binary gate (.93) stays live at our .872 to .883 with difference features untried there (queued). Both in-house arms landed (L81): the oversample arm reproduces the printed majority row EXACTLY (.050/.293) and lands within .008 of their +DA cell, with rare classes overshooting in the fold-leak direction; the diff arm confirms the mechanism (+.05 macro, grammar/spelling .49). **Fine half, current account (folded 2026-08-16; the earlier "composition demonstrated in-pipeline" wording was superseded by L107/L109 and should not be read): non-augmented classes within a dime; the augmentation story for the five augmented classes is INFERENCE WITH COUNTER-EVIDENCE (their §5.4.1 names fold-safe synonym replacement; two sibling cells deviate the wrong way; and a plain table-arithmetic error explains the anomaly at least as well — the L109 "mutually incompatible independent of Table 4" strengthening is DOWNGRADED to unverified (L123: a second derivation could not reconstruct it), so the account rests on the independently confirmed Table-4 contradiction).** Binary diff arm landed (L84): +1.3 to +1.5 on the embedding arms. Then the archaeology agent refuted the encoder hypothesis empirically (L85): two checkpoints agree within .3, no classifier family beats boosted trees, and nineteen string-diff features alone reach .8968/.8993, matching their Features row while embeddings *degrade* it. **BINARY CLOSED: Features row REPRODUCED; USE and Features+USE rows NOT REPRODUCIBLE from the published description**, the underdetermination being upstream (their sentence aligner is named only in a deleted line of their own source; the two-vector combination is unstated; the cells may be search maxima), gap bounded at 3.3 points. **SKIP CASE COMPLETE, DECISION TO THE CURATOR.** Every public route is exhausted by measurement: composition exact (3,236/3,238, majority rows to the digit); features theirs; hyperparameters theirs (published footnotes); encoder refuted (two checkpoints agree to 0.3); alignment refuted at source (the release IS the experiments' alignment, reimplemented aligner agreeing 94 to 96 percent); folds refuted (10-fold moves ≤0.5 mixed-sign); v1 corpus and all archives swept (no flat pairs ever existed; download pages never archived). Final: **faithful Features .883 vs .90 (the .895 carried our change block; L109); embedding rows NOT REPRODUCIBLE as described (gap ~3 points)**, surviving candidates = search optimism + unstated vector combination, not publicly resolvable. **Referee amendments (L107): the oversampling claim downgrades from demonstrated to inference-with-counter-evidence (their §5.4.1 names training-fold synonym replacement, and two sibling Majority cells deviate the wrong way); the embedding rows relabel to "not reproduced by us" with two locally runnable arms — max-over-their-grid QUEUED, the four-block pair encoding [u;v;|u−v|;u⊙v] the owed build. Author contact is off the table, his ruling 2026-08-14; the wording stands on the exhausted-public-routes evidence.** **GRID-MAX LANDED (L112): NOT-MATCHED — the 36-point grid maximum leaves use at .8774 (−.043) and features+use at .8783 (−.052), the published fixed config ranking 15th and 26th of 36, so search optimism over their own grid is refuted.** **FOUR-BLOCK LANDED (L115): NOT-MATCHED — [u;v;|u−v|;u⊙v] gains about a point (use .8866, features+use .8860) and still lands 3-4 points short. THE EMBEDDING ROWS ARE TERMINALLY CLOSED as not reproduced by us from the released materials: every public route now measured (composition, features, hyperparameters, encoder, alignment, folds, grid-max, pair encoding), gap bounded at 3-4 points. Surviving candidates remain (search optimism beyond their printed grid; an unstated vector combination) and are not resolvable from public materials — so: nothing left WE can run, which is the claim's exact strength (the 2026-08-16 audit's wording fix).** |
| A-M impossibility construction | the analytic 0.5/0.5 degeneracy | reproduced at exactly 0.5, then relaxed | **PASSED (L60), the phase's only value pass** |
| PAN style-change task | 2024 hard-split winner macro-F1 0.863 (nycu-nlp); 2025 sentence-level winner 0.830 (wqd); our validated local scorer matches the official evaluator to 1e-12 | our bank scored 0.565 on hard / 0.969 on easy (beats the published 0.959 there), never their method | **REINSTATED 2026-08-13, his ruling; PINNED AT SOURCE (L102); TWO OF THREE MEMBERS ABOVE THEIR GATES (L104); THE OVERSHOOT EXPLAINED (L106): the winner's own PAN23 augmentation puts 16% of validation pairs verbatim into training (49 whole documents; organizers dedup within-year only), and our members score 1.0 on the leaked pairs. Gate comparison stands (same recipe, same leak, both sides blended); honest capability = leak-free 0.827/0.838; the held-back 0.863 inherits the contamination question. Deberta (fp32) + vote land today and get both-subset rescoring. **CORRECTED MEMBERS (L111): ernie rescheduled 0.8798, +0.031 above gate, the third member landed. Roberta under the ALL-MODULE reading of the printed dropout 0.25 COLLAPSES (nine-epoch flatline) — corrected by L118: the collapse is STOCHASTIC (the leak-free arm ran the identical setting and trained normally), so all-module is knife-edge unstable and cannot anchor a comparison; the head-scope one-recipe member set + vote remains the design. Deberta refit at micro-batch 12 × accum 5.** **SETTLING ARM LANDED (L118): retrained leak-free roberta reads 0.8108, −0.032 BELOW the winner's gate — removing 6% of training (the 245 leaked docs) erases the entire above-gate margin plus 4.5 points, closing the contamination account from a third direction (rescore 0.8273 / strict tier 0.8235 / retrain 0.8108). Honest capability = 0.81-0.83; any layering experiment builds on that, never the printed gates. REMAINING: three head-scope members + vote + deberta + the three wqd 2025 TEST gates (hard 0.830 / easy 0.958 / medium 0.823), all in tonight's burn.** **HEAD-SCOPE RETURNS (L121): roberta 0.8633, +0.021 ABOVE gate (scope verified in the measured record); deberta COLLAPSED FLAT in fp32, its second failure mode after the fp16 overflow — the paper's strongest member is the one we cannot yet train; stabilizer ladder queued recipe-preserving (seed 43 → warmup 0.10 → lr 4e-5 → and rung 4, pending his approval: a gear-3 bf16 A100 diagnostic — bf16 dissolves the fp16 overflow and tests whether the collapse is fp32-specific; DIAGNOSTIC only, never the gate read, ~$1.30 needing a cap approval at the current window). ALL-SCOPE TWIN ALSO FLAT (L121 fold 2026-08-16): both fp32 scopes collapse locally; three distinct deberta failures. The b8 curve point landed 0.7496, folding into L117's specification curve; the print stays inside the family. Ernie head-scope + vote + wqd gates in rotation.** **CONSENSUS FLEET (L109): all PAN claims confirmed unanimously; strict-tier leak-free = 0.8235/0.8355. NEW REACHABLE GATE: the PAN 2025 test split with truth labels is in our store, verified genuine — the 2025 winner (wqd: single deberta-base, sentence-level, every hyperparameter stated, printed TEST 0.830 hard) is the phase's cleanest exact-value target; the sentence-level runner is the owed build.** The printed 0.863 is on the held-back TIRA test set (unreachable by construction); the honest gates are the notebook's own validation table: single arms .8423/.8567/.8490 (roberta/deberta-v1/ernie base), majority vote **.8658**. Hard needs no LaBSE; train = PAN24 hard + PAN23 hard; the metric is POOLED two-class macro-F1 (the overview prose is falsified by the evaluator's source, six baseline back-calculations confirming). Four arms queued (three members + vote), per-epoch validation recorded, assumptions named for the six unstated hyperparameters. No released code or weights exist for either year's winner. We hold 2018/2022/2023/2024/2025 locally. **THE ANCHOR IS CLOSED (L133, 2026-08-18). 2025: all three test gates REPRODUCED on complete seed intervals (hard typo-distance, easy at one ten-thousandth, medium bracketed with s44 at +0.0023). 2024: all three members above gate under the one-recipe scope (deberta trained at seed 43, L131) and THE VOTE CLEARS ITS GATE at 0.8799 vs 0.8658 (+0.0141, blended-leak caveat standing; honest leak-free capability 0.81-0.83). The recreation scorecard is complete across all five anchors; BST Exps 2-3 remain the one open extension.** |
| BST inverse planning | Exp 1 Fig-5 best-fit r .83/.98/.94/.97 (M1/M2/M3/H), Table-1 BSCV .82/.97/.93/.96; Exp 2 Fig-8 best-fit .58/.95/.59/.92, Table-2 BSCV .57/.95/.58/.91; Exp 3 M3 .96 (best .97), M1 −.03, M2/H .54. Best-fit params: Exp 1 M2(β2.0,γ0.25), M3(β2.5,κ0.5), H(β2.5); Exp 2 M2(β0.5,γ0.65), M3(β1.0,κ0.95); Exp 3 M3(β5.0,κ0.6). Best-fit and BSCV are different numbers per cell, never crossed (corrected L78) | human data DIGITIZED AND VALIDATED from the vector figures (L78); refcheck PASSED eight of eight; analytic model gates passed (L63) | **RUNNABLE, the figure arm owed.** Implementation list: the H model (M2 at γ=1), the exact γ self-transition parameterization (footnote 1's K/(K−1) factor), goal prior over all non-obstacle cells, the Exp-3 z-score→normal-CDF pipeline, BSCV bootstrap (N=10,000; k=50/50/20 resampling data points), stimulus geometry extraction from Fig 3 (walls are rects, paths are glyphs). Matching strategy: compute our M2(β2.0,γ0.25) predictions and align against the reference M2 column to pin stimulus identity, which validates our value iteration in the same step. Known source contradictions: 99-vs-100 stimuli, Fig 5 vs 6f on M3's β, and (referee, L107) main-text-vs-appendix on the goal prior (three marked goals vs all non-obstacle squares — sets K in the γ factor; both readings run as arms). Referee design corrections adopted: NINE actions including Stay at cost −1; 36 = 4 configs × 3 path groups × 3 route conditions; the Fig-3 decode must hit the paper's own 99-stimulus count as its known-answer gate. **DECODE GATE PASSED (L114): 99 of 99 stimuli, label-perfect, every path legal.** **EXPERIMENT 1 PASSED AT EXACT-VALUE GRADE (L119, 2026-08-15): the v2 rebuild (soft Bellman fixed point per appendix Eq. 4, nine actions with blocked moves unavailable, marginalized state transitions, footnote-1 goal chain, 0-or-1-subgoal M3, H = M2 at γ=1) lands all four Fig-5 correlations at printed precision (M1 0.8281/.83, M2 0.9780/.98, M3 0.9440/.94, H 0.9661/.97), matches the paper's own digitized prediction columns to ≤0.001 across all 297 cells, aligns 99/99 stimuli by the non-circular four-model signature, and LOCATES the 99-vs-100 contradiction (reference index 92 has no Fig-3 counterpart).** **THE GOAL-PRIOR CONTRADICTION RESOLVED (L120): the all-squares arm deviates from their own digitized M2 column by up to 0.13 while the marked arm matches to 0.0002 — the paper computed K = 3, and only the cell-level gate could tell (the correlation gate moved 0.0006). M1/M3/H are readout-invariant to the support.** **EXPERIMENT 1 COMPLETE (L122): the grid maxima and the N=10,000 BSCV table land at printed precision, and the sweep's argmaxes ARE the paper's published best-fit parameters, model for model — fourteen printed values reproduced across L119/L120/L122.** Remaining for the anchor: Exp 2 (retrospective, forward-backward smoother — needs its stimulus decode from the paper's Exp-2 figure) and Exp 3 (θ-inference over 21-point grid, z→CDF pipeline, k=20 — needs its eight condition worlds from Fig 9); both decodes reuse the L114 machinery; the engine, alignment method, and analysis pipelines are validated inventory |
| ScholaWrite intention prediction | fine-tuned BERT/RoBERTa weighted F1 0.64, Llama-8B 0.13, GPT-4o 0.08; IAA 0.71 (fetched) | three arms landed (L68/L69/L70) | **NOT PASSED, ANOMALY REPLICATED: BERT 0.741 and RoBERTa 0.730 against 0.64, two architectures with the same overshoot, so the inflation belongs to the shipped split (within-project, 85 percent before-text overlap) rather than the pipeline; the zero-shot local reader lands 0.172 against Llama-8B's 0.13, the collapse regime reproduced but a different model by construction. The protocol arms began landing (L75), and the subagent pin resolved the mystery at source (L77): their split IS the leaky shipped one, their recipe differs by balanced class weights, head-of-document truncation inside a buggy tag wrapper (the senior author's own issue confirms the bug shipped), 10 epochs, and a report-read metric; and their 0.64 is internally inconsistent with their own per-class table (reweights to ~0.59). **CLOSED AS CORRECTION, ONE MATCHED-CLOSE ROUTE LIVE (L86). Faithful arms: BERT 0.580, RoBERTa 0.546 (bug reproduced, per-class agreement 0.044). The provenance hunt completed the chain: 0.64 is a stale v1 number never recomputed (byte-identical across five versions), contradicted by the camera-ready's own fresh per-class table (reweights to 0.5947 (L109's recomputation from the shipped supports), our BERT within 0.015); the vanished private eval repo is the 300-capped subsample by composition and moves scores DOWN; the vanished revision had the shipped composition. Remaining ambiguity RESOLVED (2026-08-12): the epoch-5-at-batch-8 arm landed at 0.6094, NOT-MATCHED, three points short; the epoch axis is swept end to end (0.741 / 0.609 / 0.580 / 0.546) and no checkpoint reading reaches the print. **CORRECTION-CONFIRMED, CLOSURE-PENDING (referee, L107): the stale-number finding is strengthened (their printed accuracy 0.56 and macro-average both corroborate), but our loop dropped their Trainer's silent defaults (linear decay, clipping, decay exclusions) and ran one seed. Three framework-faithful seeds queued (sw_bert_hfd_s42/43/44); the previous-label input variant filed; the row closes on the seed interval.** **FRAMEWORK ARMS LANDING (L110): seeds 42/43 read 0.6595/0.6592 (accuracy 0.628), ABOVE the print by two points — "stale and unreachable" softens to BRACKETED. Both trajectories cross 0.64 mid-training; the discriminating test is the roberta framework arm (they print 0.64 for BOTH architectures).** **ROW CLOSED (L117, 2026-08-15): seed 44 finals at 0.6391 — the print to the third decimal — so the three-seed interval [0.639, 0.660] CONTAINS the headline, and roberta's trajectory crosses 0.64 at epoch 7 (0.6414), the discriminating test surviving on both architectures. The F1 headline is REPRODUCED (interval rule and exact-value tolerance both); the paper's internal inconsistency stands as a literature fact now explicable as different checkpoints/seeds of one pipeline (our specification curve produces 0.58-0.74 end to end, their table-implied 0.59 at mid-trajectory, their 0.64 at crossings and one final); the accuracy residue (ours 0.609-0.629 vs printed 0.56 at final epoch) is recorded. The batch-8 arm lands as the specification curve's last point; it gates nothing.** The full leak-free grid landed (L82): leave-one-project-out ranges 0.26 to 0.61 by project (means 0.39/0.44), so the leak is worth ~30 points on average, and the small split fails for both architectures (BERT 0.526, RoBERTa 0.468, six apart against their identical 0.64/0.64 pair). The revision diff closed terminal-benign: the pinned revision no longer exists on the Hub even with gated access, so main is canonical by default. Any program use of this dataset (G132) must be leave-one-project-out by construction; their exact Llama-8B stays optional** |
| Gosselain visibility partition | ethnographic; no published statistic to hit | the text analogue's double crossover (L41) | **EXEMPT, method import.** The source is field observation without a reproducible number; the import's own first-pass measurement stands on its own terms |
| connoisseurship revision homogeneity | historical practice; no published statistic | first-ever measurement (L52) | **EXEMPT, method import**, same reason |
| Hadidi pooling attack | an attack protocol, applied to one's own instrument by design | applied to ours (L44) | **EXEMPT, protocol import.** There is no foreign value to hit; the protocol was executed in full |
| Kornblith CKA | method paper; analytic sanity properties (self-similarity 1.0, isotropic-scaling invariance) | identities verified on real embeddings 2026-08-12: self-similarity exactly 1.0, scale-invariance gap 6e-17, formula byte-matched to the runner's (`results/audit/cka_sanity.json`) | **EXEMPT, checks passed** |
| function-word attribution | no single canonical published value for this corpus | our own calibration baseline (7.6× chance) | **EXEMPT, self-calibration**, never claimed against a foreign number again |

**Owed, the builds, in run order:**

| | study | method and gate | cost |
|---|---|---|---|
| **G136 · recreate ArgRewrite's own published task** | The corpus paper reports revision-purpose classification baselines at coarse and fine grain. Reproduce them with our tooling, author-split enforced. **Their published numbers become our known answer; matching them is the gate G129 runs behind** | **Half landed (L59): 2,806 events extracted (G129's dataset); features arm at 0.857 coarse / 0.233 fine, and the signal is entirely in the delta.** Four reader arms run overnight, checkpointed; the paper-table comparison is owed on fetch | readers overnight; paper fetch next |
| **G137 · recreate Bayesian inverse planning on the classic gridworld** | Baker, Saxe & Tenenbaum's goal inference from partial trajectories is the direct precedent for the whole project. Reproduce their three models (M1 static-goal, M2 goal-switching, M3 subgoal) at their best-fit parameters (M2 β=2.0 γ=0.25 for Exp 1; β=0.5 γ=0.65 for Exp 2; M3 β=5.0 κ=0.6 for Exp 3) on their maze-world stimuli. **The exact gates, fetched from the paper: Exp 1 best-fit r .83/.98/.94; Exp 2 BSCV ⟨r⟩ .57/.95/.58 with heuristic .91; Exp 3 M3 .96.** Model predictions and parameter-dependence curves are fully recreatable; the human side lives in their figures, and the pass is judged on the model side | Sim-side brief to ghost-scale; small state space, exact inference | **v1 landed here instead (L63): all three analytic gates pass** (γ→0 identity at 10⁻¹², monotone convergence, switch-tracking 0.899 vs 0.158); the figure-level half of the pass is owed next |
| **G138 · recreate the impossibility construction, then relax it** | Armstrong & Mindermann's planner/reward degeneracy, built as a runnable toy, then relaxed with the three human priors | **done (L60): RECREATED at exactly 0.5/0.5, then NARROWS.** Bounded family 20×, known planner 2×, both 40×, noise-robust. The bounded family is the load-bearing prior. Next scale: the G137 gridworld |

## Phase 2.0 — the vertical slice (governing brief: `docs/design/archive/PHASE_2_0_CONTEXT.md`, 2026-08-16)

**The mission, his directive:** build and controlled-ground-truth validate a deployable binary
AI-provenance classifier whose differentiating contribution is recoverable decision structure,
while constructing the reusable intent-reading machinery for later process and value inference.
One complete vertical slice: benchmark → decision representation → stacked classification →
held-out evaluation → packaging → public demonstration. The detector is the public wedge;
recoverable decision structure is the project. Every study names its theory group; every landing
gets a curator roll-up (Strengthens | Narrows | Kills | Infrastructure).

**Migration note (2.0A, 2026-08-16).** What moved: the context file archived to
`docs/design/archive/PHASE_2_0_CONTEXT.md`; the program's 2026-08-09 deprioritization of "detector
benchmark races / feature stacking before choice recovery validates" is superseded by the
curator's Phase 2.0 directive — with its core discipline PRESERVED (all advanced fusion stays
gated on an independently validated decision representation; the brief itself mandates it). What
stayed: every identifier below; G129/G130/G131 become 2.0D's validation program; G150's null is
an integration constraint (naive late fusion on the style-change task did not help), never a core
verdict; G151 (gear 3) is the burst engine under the stone rules. What was deferred: G132–G135,
G142–G146 continue as wider-program items behind their own gates, outside the slice; value
recovery is explicitly out of Phase 2.0 (the schema preserves its variables). Phase 1's tail
(wqd test gates, deberta ladder, BST Exps 2–3) lands through the existing workflow alongside.

| sub-goal | identifier | what it builds | gate / dependency | state |
|---|---|---|---|---|
| **2.0A reconcile** | this pass | dependency map, migration note, contract amendment | none | **DONE this pass** |
| **2.0B evaluation contract** | **G152** | frozen task definition BEFORE optimization: operational binary-label guide (substantial model contribution, with adjudication examples), full 8-regime authorship taxonomy, primary/secondary metrics (F1 at declared prevalence; TPR at 1% human-FPR; calibration; worst-slice), split logic (lineage/author/domain/generator grouping), baseline-selection rule with date, claim language per outcome tier | none | **DRAFT v0.1 WRITTEN (2026-08-16, `docs/design/EVAL_CONTRACT_2_0.md`); owed: the ≥30-example adjudication set, then his freeze sign-off. v0.3 (2026-08-21): DRAFT — DO NOT FREEZE; the Phase 2.3 reconstruction reconciliation is now the primary task and the binary form survives only as the optional downstream product layer** |
| **2.0C crossed benchmark** | **G153** | provenance × delegated-human-choice factorial: 8 regimes, domain/register/length/quality/generator strata, counterexamples that break every shortcut (quality-matched pairs, low-decision human vs high-decision AI, same source under different histories), lineage-safe splits, full record schema §11.3 | G152 frozen first; **budget survey LANDED (`BENCHMARK_2_0.md` §3b) and the spend NOT APPROVED (his ruling 2026-08-16, STATE standing ruling 7): frontier acquisition is gated behind the decision reader passing its gates AND held-out lift on the free local-family benchmark; grant applications rejected as premature.** ToS/lineage findings stand (OpenAI test/calibration-only if weights ship; deepseek-r1:7b is qwen-lineage; human revision labor is the binding constraint on regimes 4-5) | **FREE-PATH PILOT CORPUS COMPLETE (2026-08-18): 240 process-recorded artifacts (120 qwen seen + 120 llama held out; thin-prompt across 4 domains × 2 lengths + 40 rewrites per family, explicit decoding, lineage links, manifests at full yield) — the generation loop proven end to end at $0. Next: human-negative assembly + schema/manifest tooling; frontier arm stays dormant behind the results gate. Ruling 2026-08-21: the pilot is REUSABLE PROCESS-RECORD SUBSTRATE and not a valid provenance benchmark until matching is repaired (L145: the shortcut is quality and era)** |
| **2.0D decision-reader validation** | **G129 + G131 + G149** | the differentiating representation proven on known answers | G130 harness VALID (L56); L126 floor mechanism folded in | **G129 VERDICT LANDED (L132): H-A REPLICATES (0.4854 vs 0.25 analytic, 616 events); H-B SURVIVES on the balanced matched draw (0.4148 vs 0.25, 16.5 points, n 176 of 283 disclosed); A7 CLEAN (fabrication 0.000 on 200 no-op deltas, symmetric miss 1/200); H-C the reader LOSES to the 19-dim change block (0.5552, McNemar p = 0.0097) — the preregistered response executes: detector-facing features build on the BLOCK, the reader supplies abstention; the shuffle gate's below-chance flag is the delta-tracking signature (expected 0.125, read 0.110), gate-direction defect recorded (LESSONS §3). **RECLASSIFIED (2026-08-19, curator-ratified, L137): strong replication, NOT confirmatory grade — the shuffle gate voided under the card's own terms and a post-hoc-corrected expectation cannot restore the run's grade; the matched arm's power clause holds its verdict at the pilot tier. The gate is NOT formally met; the evidence keeps replication-tier standing. Confirmatory grade owed to G129b (Phase 2.1.4). G149's text port ran and is NULL on surface distances (L134); the likelihood-form port is the open extension** |
| **2.0E competitive substrate** | **G154** | the honest finish line for AI-provenance (NOT the style-change substrate — a new reproduction target): selection survey of strongest reproducible detectors current at implementation date (one strong trained detector; one zero-shot/statistical with distinct errors; one surface/metadata leakage reference), then faithful reproduction with frozen outputs and error slices on G153. **First survey pass (2026-08-16, snippet-level, full fetch discipline owed at selection): zero-shot leader is Binoculars (ICML 2024, public code, two-model perplexity ratio, ~90% recall at 0.01% FPR claimed; the 7B model pair wants gear 3), with Fast-DetectGPT the cheap alternative; the trained-detector pick comes from the RAID leaderboard's top open entry at selection date (RAID: 6M+ generations, 11 generators, 8 domains, 11 attacks — also the substrate sanity-check data, though it carries no process records so it cannot replace G153); the leakage reference is built in-house** | G153 exists to score against; training likely gear-3 scale → cap approvals per the stone | **SURVEYED at snippet level; fetch-grade selection + reproduction next** |
| **2.0F stack + ablation** | **G155** | substrate alone / decision layer alone / calibrated late stack / interaction-aware stack / deeper fusion ONLY after complementarity shown; decision reader frozen during the first ablation so provenance supervision cannot replace its construct; preregistered | the four Phase 2.1 decision gates (contract §3b) AND 2.0E frozen; G150's null = the integration constraint (fusion seed variance ~2× substrate; naive concat insufficient) | **GATED (re-gated 2026-08-19 behind Phase 2.1)** |
| **2.0G shift hardening** | **G156** | unseen generators/domains/authors, both rewrite directions, rich prompting, low-effort human negatives, short texts, benign transformations; worst-slice + calibration reporting, never one aggregate | 2.0F verdict | **GATED** |
| **2.0H productize + release** | **G157** | installable package, scoring CLI, small API, versioned+checksummed weights, manifests, CI tiers, calibration artifacts, model card, demo-as-evidence-viewer with abstention | infra workstream STARTS NOW per the locked decisions (CI/packaging are first-class, not post-result); release gated on the frozen gate | **OPEN (infra) / GATED (release)** |
| **infra: checkpoint-resume for long trainings** | (no G number, infrastructure) | per-epoch checkpoint save + resume in `run_pan_winner.py`/`run_pan25_winner.py`/`run_scholawrite.py`, recipe-neutral (state dict + optimizer + epoch counter; resume only from same-args runs) | the 2026-08-17 outage receipt (LESSONS §5): a 17-hour rung restarted from zero | **OWED, build before the next 10-hour stage if practical** |

**Standing rules for the slice:** intent = recoverable problem-directed organization of choices
under bounded context, never an unconstrained latent state; the public label is "probability a
generative model made a substantial contribution to final wording or structure," never "the
author is AI"; abstention is a product behavior; no aggregate intent score replaces the tuple;
escalation list and claims policy per the brief §§16, 18. Result routing per §13.4: every null
must remove, narrow, or redirect something.

## Phase 2.1 — repair and epistemic foraging (declared and named by the curator 2026-08-19; the external audit and its verification are L137)

The bridge between the 2.0D evidence and any stacking: fix what the audit proved broken, forage
the existing corpus for what it can still teach, and re-earn confirmatory grade under gates
specified correctly from birth. Everything here is $0 local, inside standing ruling 7.

| item | identifier | what it does | gate / dependency | state |
|---|---|---|---|---|
| **2.1.1 reclassify** | (docs pass) | demote G129 to strong replication across STATE / FINDINGS / theory / this file; G131 corpus relabeled exploratory; stacking re-gated | curator ratification | **DONE (2026-08-19, this pass)** |
| **2.1.2 input-interface freeze** | **G152 extension** | the contract's inference-input section: three product interfaces (final-artifact detector: final text only at inference; paired-delta reader: old + new text; process-aware audit: full process record); every representation annotated with its required inputs and permitted interface; the 19-dim change block assigned to interfaces two and three; the four stacking decision gates written in | drafted this pass; freeze needs his sign-off | **INTERFACES DRAFTED (contract §3b) AND THE 30-EXAMPLE ADJUDICATION SET DRAFTED (2026-08-19, `docs/design/archive/ADJUDICATION_SET_2_0.md`: 10 clear-positive, 10 clear-negative, 10 hard with the three policy lines named — systematicity, survival, faithfulness). HIS STANDING FLAG (2026-08-19, unresolved): "something seems fundamentally wrong about this adjudication ask still" — he returns to it; NOTHING FREEZES until the objection is surfaced and answered. My work meanwhile: figure out what the wrongness is before he has to articulate it** |
| **2.1.3 epistemic foraging on the existing factorial corpus** | **G158** | (a) realization adjudication: mechanical checks for every checkable instruction, bounded-reader adjudication with evidence spans for the rest, per-artifact realized/unrealized/ambiguous table; (b) cheap baselines leave-one-topic-out: length, paragraph count, punctuation profile, lexical echo, instruction count; (c) artifact-only recovery scored against REALIZED instructions with same-pool decoys, per target × amount × coupling cell; (d) qwen-to-llama transfer + reader-error overlap. EXPLORATORY grade, declared | corpus exists (180 artifacts, recorded data); DESIGN CHECK block from birth | **stages (a) + (b) LANDED (L138): checkable realization 0.586; cheap features read target at 0.95 combined — the bar stage (c) must beat. Reader arms ran BUT THE ADJUDICATOR FAILED VALIDATION (L139): over-credit 0.688 on exact-grade rows, verdicts warning-labeled. Stage (c) LANDED same day (L140): reader at CHANCE on truth-balanced surface constraints (0.25; word-echo 0.375 beats it; oracle 1.0 proves the answer is in the text) but 11 points ABOVE the problem-pool echo bar in both families (0.909 vs 0.798) — a transferring margin the corpus cannot split into executed choices vs assignment-vocabulary leak. Fabrication clean in forced choice (0.05). FORAGING COMPLETE; the 2.1.5 design constraints are measured** |
| **2.1.4 fresh confirmatory** | **G129b** | new frozen card, fresh seed: every gate carries null AND alternative expectations with a failure direction (shuffle ~0.125 label-marginal under the alternative, leak direction up); matched-arm power handled up front (one pre-committed caliper relaxation, then pilot tier declared) | card frozen this commit | **VERDICT LANDED same day (L141): ALL GATES QUIET (shuffle 0.1136 beside its frozen 0.125 alternative expectation), H-A REPLICATES seed-stable (0.4805), A7 CLEAN (fabrication 0.000, sym miss 0/200), H-C the block wins again (0.5471, p = 0.0157), H-B 16.5 points at its pre-committed pilot tier. CONFIRMATORY GRADE EARNED; the 2.0D real-text gate is formally MET. Row closes** |
| **2.1.5 decisive factorial rebuild** | **G131 rebuild** | paired transformations of the same base material (base essay → instructed revision, same generator); realization independently recorded and crossed as an intervention; coupling verified at output level; length/register matched by construction; consequence-matched decoys; fabrication controls; directional nulls both ways | G158 reports feed the decoy + adjudication design | **CORPUS COMPLETE AND SELF-GATE PASSED (L144, 2026-08-19 afternoon): 160 rewrites at full yield both families; R+ exact-grade realization 0.625 (gate 0.5) against the uninstructed twins' 0.281 spontaneous floor — realization VERIFIED, the execution contrast live. NEXT: the recovery card (`prereg/g159.py`), forced choice with echo-matched decoys, R+ vs R- as the execution effect, R- doubling as the preregistered leak gate. **VERDICT LANDED same night (L146): SUPPORTED — execution effect 0.64 (0.86 vs 0.22, z 9.1), all gates quiet, perfect family transfer; echo-disclosure fired (word overlap recovers executed instructions at 0.73, so the reader's above-trivia margin is 13 points); delta interface adds nothing; fabrication context-dependent (0.40 on rewritten twins); constraint-verification null replicates. PHASE 2.1 CLOSES; 2.2A done; echo becomes a decomposition target in every 2.2 card** |
| **2.1.6 benchmark human-negative repair** | **G153 continuation** | quality/register/length-matched human negatives; low-effort and templated human writing added to the blueprint; identical-source/different-transformation lineages preserved; conclusions on shortcut-breaking slices only (the L135 leakage reference is the enforcement) | his revision-labor decision; ruling 7 unchanged | **BOTH ASKS RESOLVED (2026-08-19: revision labor option (a); internal-vs-public ratified with his evidence-filters-are-preregistered-only caveat adopted as a named rule). FIRST MATCHED CELL LANDED (L145): length+register matching leaves the leakage reference at 0.9659 vs the unmatched 0.9785 — the shortcut lives in QUALITY and ERA, so quality-matched cells and identical-source lineages are the binding repairs; license reads + low-effort sourcing survey are the open agent tasks** |

## Phase 2.2 — trajectory-conditioned inverse reading (governing brief: `docs/design/archive/PHASE_2_2_CONTEXT.md`, 2026-08-19)

**The mission, his directive (brief §7):** validate trajectory-conditioned inverse reading
on known answers — recover which proximal goal and trajectory constraints were realized,
how expertise and context shaped the available route, and how anomalies were handled,
separating reconstruction from provenance and causal certainty. The primitive is the
**reconstruction profile** (brief §9), never a human-versus-AI verdict; the binary label
survives only at the product-policy layer. The visual map's nine objects are the binding
ontology (brief §3); the observational-equivalence rule (§4.2) and the twelve ruler gates
(§10) bind every new reader family. The curator-first theory loop (§13) is folded into
`CLAUDE.md`. Stacking (2.0F) now sits behind BOTH the Phase 2.1 gates and 2.2G.

| sub-goal | identifier | what it builds | gate / dependency | state |
|---|---|---|---|---|
| **2.2A close the realized-choice boundary** | **G159** (existing) | the recovery card written under Phase 2.1's frozen design intent and run: verified executed instructions vs uninstructed twins vs unexecuted alternatives, echo- and consequence-matched; interpretation per brief §11.1 — realization evidence, never attribution | corpus + audit landed (L144); the card was written to 2.1's question, not reshaped by 2.2 | **DONE (L146, 2026-08-19 night): SUPPORTED with the echo cap disclosed — realization evidence licensed, attribution not; Phase 2.1 closes** |
| **2.2B representation + interface schema** | **G160** | the typed reconstruction-profile schema (brief §9) with structural interface guards (no process-metadata field reaches the final-artifact interface) and unit tests; contract amendment landed (v0.2) | none; contract v0.2 amended this pass | **contract amended; schema build queued behind the G159 card** |
| **2.2C anomaly-handling ruler** | **G161** | known-answer constructed battery over the handling ladder (no anomaly / unexplained order / unnoticed / repaired / concealed / repeated / rational-under-secondary-goal); must abstain on none, split repair from concealment, and never read recurrence as intent without a constraint control | constructed world first (the G149 gridworld machinery); brief §10 gates, DESIGN CHECK from birth | **RULER-PASSES (L147, 2026-08-20): all six gates at 50 episodes per class, fresh-seed replicated — clean walks honest at 0.98, all five planted handling classes at 1.0, repair/concealment fully separated, unfamiliar order never called error, context flips 1.0. Six build iterations recorded in the runner (categorical multi-step anomalies; consequence structure; episode-calibrated nulls; separated-cluster recurrence; post-cluster handling windows). 2.2D IS LICENSED** |
| **2.2D anomaly text battery** | **G162** | process-recorded text families (introduced-corrected / concealed / unnoticed / repeated / deliberate-for-secondary-goal / clean control), consequence- and echo-matched, both interfaces reported separately, confusion over handling states | G161 ruler PASSES first — hard order per brief §16 | **CORPUS BUILDING (2026-08-20 mid-morning, `run_g162_gen.py`, queued): six handling families as instructed rewrites of the recorded bases with TOKEN-VERIFIABLE planted issues (invented per-topic study figures — wrong value, true value, refrain — all string-testable), so presence, correction, repetition, and refrain audit mechanically; concealed/unnoticed share the mechanical half BY DESIGN (their separation IS the reading battery's question); self-gate refuses the battery below 0.6 presence / above 0.05 clean contamination / corrected-vs-concealed marker separation. CORPUS-STANDS landed (L149: presence 0.75-0.95, clean 0.00, correction markers 0.75 vs 0.00). VERDICT LANDED (L150): V gate PASSES 0.95 (honest instrument) and the primary is BLIND — concealed vs unnoticed at 0.417 on either interface; deliberate constructions read as nothing; clean rewrites pull 0.30 over-attribution (the L146 effect replicated). THE CHANNEL NARROWS TO THE CONSTRUCTED WORLD at this resolution; owed redesigns: span-level asking, longer artifacts, audited hedging density. 2.2E proceeds on the channels that read** |
| **2.2E context conditioning** | **G163** | matched cases where declared making conditions (forced vs chosen, tool present vs absent, expertise supplied vs absent, familiar vs unfamiliar convention) must move the reconstruction in the direction the known transition map requires; context cards never state the answer | G160 schema (readings carry reader-artifact-context identity) | **GATED on G160** |
| **2.2F independent-evidence validation** | **G164** | every apparently-working reconstruction family faces one withheld constraint (process fact, unseen repair, held-out segment, counterfactual, or same-process second artifact); reader-transfer where affordable | runs alongside 2.2C-2.2E verdicts | **standing requirement, folded into every 2.2 card** |
| **2.2G detector-eligibility ruling** | (ruling, no new G) | which profile fields, if any, enter 2.0F: own-ruler pass + artifact information beyond context and echo + declared interface + calibrated abstention + cross-family transfer + different errors from the substrate | 2.2A-2.2F interpretable verdicts | **GATED; Phase 2.3's Stage 5 carries the same ruling** |

## Phase 2.3 — adaptive process-inversion program (governing brief: `docs/design/archive/PHASE_2_3_CONTEXT.md`, 2026-08-21; registry: `docs/design/archive/PHASE_2_3_REGISTRY.md`)

**The mission (brief §0):** map where process inversion works, where it reduces to useful
reenactment, where it needs process records, and where the reader merely tells a persuasive
story — seven wing roots, each ending in exactly one of ROOT-POSITIVE / ROOT-NULL /
ROOT-REVERSED / ROOT-AMBIGUOUS / INSTRUMENT-FAIL, routing declared before results. The
reconciliation against the live head (the brief predates the 2.2 landings) lives at the
registry's top; **Wing D enters at its predeclared repair, curator-ratified 2026-08-21.**
Wings A/E absorb G163's intent. Drives and values stay deferred (brief §2.4); no detector
stacking off one positive root.

| root | identifier | what it asks | gate / dependency | state |
|---|---|---|---|---|
| **P23-G0 reader-ablation** | **G165** | does explicit route generation (self-route; candidate-and-discriminate) beat direct reading on the recorded G159 events? | card frozen (`prereg/g165.py`); pipeline-purity + anchor gate PASSED at build | **WING CLOSED (L151 + L153): NO-GAIN where direct reading is strong; the discriminator lands HURTS where it is weak (self-route minus 7 points, p 0.0006, fabrication 0.065 vs the direct 0.000). Direct reading plus calibrated refusal is the reader's best form; the fabrication gate becomes standard for any generate-then-judge stage** |
| **P23-B0 equifinality** | **G166** | five recorded routes to surface-matched essays; can any reader separate them from the final artifact? | corpus CORPUS-STANDS (L152); battery frozen on it | **ROOT LANDED BLIND-WITH-RESIDUE (L154): the reader abstains (0.07 committed-correct, cannot-tell 0.70-0.85) while the mechanical surface baseline reads route at 0.48 vs 0.2 chance and the process-aware ceiling passes at 0.78. Artifact-only route auditing narrows to the records interface (W4); the owed follow-up is the B1-shaped trace-erasure/covariate test of the 0.48 surface residue, to be carded** |
| **P23-A0 context adjustment** | **G167** | true context must beat artifact-only and context-only; false context must not | cards leak-audited; recorded L154 arm as baseline | **WING PAUSED (L155 + L157): projection where evidence is absent; MIXED at 0.44 against the readable 0.86 where it is strong (false note wins the toss-up at 0.53, conflict flagged 0.15, true note 0.99). Supplied context carries a direct-reading's weight with no truth discount — an override channel until a reader passes this test. Pause-lift at the root map** |
| **P23-C0 ratification network** | **G168** | proposal / selection / veto / integration as a network, echo-split from birth | corpus stood (40/40, selection integrity 0.95, veto 1.0) | **ROOT BLIND AT EXACT CHANCE (L160): selection and veto read 0.500 artifact-only under 0.975/1.0 process-aware ceilings — ratification is real and invisible; the wing's product is the audit interface (C5). Repair question uninterpreted (format defect, fix owed on any reopen). STAGE 1 COMPLETE — the root map (`docs/design/archive/PHASE_2_3_ROOT_MAP.md`) waits on the curator** |
| **P23-D handling repair** | **G169** | span-level asking on longer artifacts where L150 was blind; twelve-family multilabel gridworld extension | ratified entry-at-repair | **ROOT LANDED, THE DAY'S POSITIVE (L158): the reader separates concealed from unnoticed at 0.77 at long form (essay-grain reference 0.417), at parity with the mechanical hedge counter (0.79), with ZERO span localization and the 0.40 clean-fabrication warning. The wall was resolution; the signal is hedging density; D1 transfer routes to the root map. Gridworld multilabel extension folded into the F0 build** |
| **P23-E0 expertise conditioning** | G170 (reserved) | expertise changes reachable routes, or only confidence | A0 card machinery | pending |
| **P23-F0 ordered accidents** | **G171** | later integration distinguishes accident-integrated from failure | the G161 world extension | **ROOT-POSITIVE (L159): all eight classes at or near 1.0 both seeds after one recorded repair (the exclusive-consequence rule); zero fabricated origin calls on the origin-identical pair; continuation above marginal noted as mechanical. Text transfer Stage-2** |

## Phase 2.4 — shared-architecture inversion and affective-prior engineering (RATIFIED 2026-08-22, continuous second gear; briefs at `docs/design/PHASE_2_4_CONTEXT.md` + `_EXPLORATION_ADDENDUM.md`, registry at `docs/design/PHASE_2_4_REGISTRY.md`, errata applied)

**The mission (context §0):** does similarity between maker and reader make the maker's process
easier to invert, and can a human-derived affective prior causally improve that inversion on
independently recorded choices, beyond surface, semantic, and generic-steering controls. Two
lanes: the confirmatory trunk G172-G180 (the only route to verdicts) and a quarantined discovery
forest (E24 scouts; outputs PROMISING / QUIET / RIVAL-FAVORED / INSTRUMENT-FAILED /
PROMOTE-TO-CONFIRMATION only; data firewall from confirmation sets). The Stage-1 pause is an
interpretation pause, not a compute pause. Identifiers G172-G180 verified free 2026-08-22.
**Ratified 2026-08-22 with the 2.3 closure dispositions accepted** (trace-erasure and
natural-transfer absorbed into the scout forest; Wing E retired as designed; Wing A's
false-context test a standing adversary; the audit-interface product DEFERRED, not dropped —
the registry carries the mapping). Stage-0 spine built and guard-tested same day
(`soundingline/probe/conditional_reader.py`, `interventions.py`, `tools/test_p24_spine.py`
all 8 guards green); three Stage-1 cards frozen and queued.

| root | identifier | what it asks | gate / dependency | state |
|---|---|---|---|---|
| **P24-S0 similarity matrix** | **G172** | are outputs easier to invert when the reader is the exact maker checkpoint, a sibling, or a similar family? | card frozen (`prereg/g172.py`) | **SIMILARITY-GRADED (L163): both contrasts at the permutation floor; corpus survived by retiring its Pythia makers (repair then second-failure clause); fingerprint rival undecided until trace erasure. STAGE 1 COMPLETE, root map frozen |
| **P24-S1 geometry link** | **G173** | does null-tested representational alignment explain who inverts whom, beyond family labels and surface fingerprints? | G172 nontrivial pattern | pending |
| **P24-A0 causal affect ruler** | **G174** | can an open-weight model reproduce abstract cross-context emotion decoding plus benign causal behavioral influence? | card frozen (`prereg/g174.py`) | **INSTRUMENT-FAIL (L162): block selection noise at dev power, input-edge lesion 2.55x, causal gate untested not failed; abstract decoding grain at one seed. Repair declined (could only reach a worse-founded band); rebuild in the scout lane |
| **P24-A1 basis contest** | **G175** | which fixed human-derived affective basis (Panksepp-7, GoEmotions-27, VAD, human-vs-synthetic twins) is stable and selectively causal against rank/norm-matched controls? | G174 passes both gates | pending |
| **P24-A2 affective inversion** | **G176** | does amplifying or ablating the frozen affective subspace causally change recovery of recorded process choices, sign-paired and selective? | G174 + G175 + G177 | pending |
| **P24-H0 human-process baselines** | **G177** | which recorded human process facts are recoverable at artifact-only, paired-delta, and prospective interfaces before any intervention? | card frozen (`prereg/g177.py`); anchor + LOPO baselines + reader arm + CoAuthor import | **3 OF 4 ARMS LANDED (L161): anchor READS 0.78 vs 0.25; mechanical floors 0.04-0.08; reader arm UNVALIDATED AND CLOSED (the powered stratified validation ran 2026-08-23 and the prompted reader failed it: balanced accuracy 0.596 against a 0.589 chance band, sensitivity 0.25; one repair spent, numbers permanently descriptive; routed to the non-generative prospective reader, which ALSO failed at chance same day: the prospective interface has no validated reader of any form; only the process-aware ceiling measurement remains on it). CoAuthor IMPORTED same day (1447 sessions, 2.7M events) — ROOT COMPLETE** |
| **P24-H1 prospective anti-projection** | **G178** | does the inferred maker model predict a future choice that was not visible when the inference was formed? | G177 viable prospective target | pending |
| **P24-A3 learned prior** | **G179** | does a small learned deformation preserve the G176 gain more reliably than hand-set scaling? | G176 robust positive only; never built to rescue a null | pending |
| **P24-X0 flight confirmation + human anchor** | **G180** | does the frozen mechanism survive fresh families, fresh corpora, and adversarial artifacts; human-reader packet prepared but never launched without the separate curator decision | G176 or G178 positive | pending |

## Phase 2.4 Stage 2 — the discovery forest (RATIFIED 2026-08-23; brief `docs/design/PHASE_2_4_STAGE_2_CONTEXT.md`; seven trees S/P/E/A/H/V/X, pursuit and warrant ledgers, six-day arc)

Wave 1 Tree-S LANDED 2026-08-23 (L165): **the crossed reversal appears** — each maker family's
artifacts are read best by that family's readers (+0.020 and +0.014 own-minus-other, both at
the permutation floor), holding under mechanical normalization and under an independent
SmolLM2 eraser that cuts measured family surface detection from 0.64 to 0.52 against 0.33
chance. The crossed-imprint design COMPLETED the same day: each family's artifacts rewritten by the
other family in turn, and the advantage follows the original maker (+0.012 and +0.011 after
cross-family rewriting) while the rewriting family gains nothing. Next: the process-resolution
ladder (does the relation help beyond goal wording) and the geometry linkage. Still to build: H1 powered
ScholaWrite validation and H2/H3 CoAuthor action tree are the next build items. Wave 2:
Tree-P process ecology (P0-P4). Wave 3: Tree-E projection-correction curves, Tree-A ruler
rebuild (A1-A4). Promotion only through the conjunctions (S9, P11, E16, A10); flight
criteria F1-F5; next free trunk identifier G181.

## Phase 2 — the wider program, each step behind its anchor (items outside the 2.0 slice continue here)

| | study | gate it waits on | state |
|---|---|---|---|
| **G129 · ArgRewrite choice-recovery, preregistered** | Bounded candidate sets per revision, brief-and-artifact reader, five controls, author-split, confusion matrices by fine purpose. **Carry the L85 lesson into the prereg: the delta is stated explicitly in every arm, and the 19-dim change-feature block is a declared baseline the reader must beat, since on the published task it beat all embedding representations** | G136 matched + G130 valid (half met) | preregistration draft is the next writing task |
| **G130b · the lexical-matching control** | Match content and surface revisions on size, rarity, position, difficulty; does "content" survive? | **done (L66): COLLAPSES.** Balanced CEM, 342 pairs; content identifiability falls 0.857 → 0.507 against 0.5 chance; PD-28 resolved in its own stated direction | closed |
| **G130c · the collision** | L65's clean 22.7-point purpose-recovery margin against L66's collapse: does the margin survive the same matching? | **done (L73): BETWEEN BANDS.** Recovery holds (0.484), the blind floor jumps (0.402), margin 8.2 points, real at McNemar p = 4.5 × 10⁻⁴, 2.8× smaller; the prereg left 5 to 10 silent. **Floor decomposition DONE (L126): 87% of the rise is label-marginal alignment, compositional not informational; the matched draw truth-balances in the confirmatory design.** The powered matched replication is folded into the G129 confirmatory battery (`prereg/g129.py`) | closed; follow-ups absorbed by G129 |
| **G131 · the factorial choice-structure benchmark** | Target × amount × coupling × realization, paired artifacts, matched everything; the construct test for every dose-responsive quantity; spec recovery rebuilds here with candidates differing by structural consequence | Phase 2.1 (the audit, L137) | **FIRST CORPUS RECLASSIFIED EXPLORATORY (2026-08-19, L137): ground truth recorded what was ASKED, not what was DONE — ~36% of mechanically checkable assigned surface instructions were not executed (66 of 80 surface artifacts carry at least one), 17 artifacts break the length band (all surface), and the design never crossed realization or used paired base material as the method detail below specifies. The corpus stands as recorded data and is the G158 foraging substrate; the decisive construct test is the 2.1.5 rebuild** |
| **G132 · ScholaWrite import** | Five preprints as five top-level units; ordering, integration, entry-point analyses | **G141 gate: reproduce their published intention-classification baseline first** | after G131 |
| **G133 · the commissioned crossed pilot** | Four makers, domain familiarity × effort × revision target × kind; keystrokes, decision cards, blind recovery | harness recovering known synthetic decisions without lexical shortcuts (met, L56) plus G129's real-text result; his sourcing | design ready when he is |
| **G134 · the estimator tournament** | Direct recovery, residualisation, joint inference, no-values, identity-only; failure-boundary map, exact solver first | G137's gridworld substrate | sim-side |
| **G135 · held-out tradeoff prediction** | Profile from several artifacts predicts an unseen tradeoff, against expertise-plus-brief | G133 + G134 | last, by design |
| **G142 · drives as expertise primitives** (harvested 2026-08-10) | His musing during the quote pass: the midbrain solution-space constraint may itself be mappable as a kind of expertise, pre-solved control maps ("buttons") that move large amounts of interoceptive state at once; the follow-up musing places both drives and values on the expertise side of the mapping rather than the policy side, values as neocortical behavior heuristics (kindness as heuristic, not the care network). Explicitly not quoted in theory at his instruction | Test in the parent simulation's values construction: represent drives two ways, as reward-side weightings vs pre-solved policy fragments (options over interoceptive state), and ask which representation better predicts behavior and which makes recovery easier. Discriminating prediction: supplying drive information should behave like supplying expertise (entry points, transition priors) rather than like supplying values | sim-side; design after G137's substrate lands its figure half |
| **G143 · the emotion-wheel interface signature** (harvested 2026-08-10) | His restated §7 claim: the emotion vocabulary defines and elaborates higher-order predictions and controls of valence and arousal, and that elaboration's output should look like an input for a mid-stack, limbic-system-like transformation | Test with existing machinery: per block, separate lexical affect decodability (word-count-vulnerable) from non-lexical (word-count-immune, the B-1 control's design); the interface prediction is a handoff, the block where lexical decodability peaks immediately preceding the rise of non-lexical decodability, checked across the eleven families with the null that the two curves are exchangeable | model-side; cheap, reuses cached activations |
| **NIGHT13 burn (2026-08-11) · LANDED IN FULL (L87/L88/L89)** | **G20a/G20b REJECTED** in all eleven families (flat curves, no address; the beyond-lexicon component universal but lawless, which also closes **G143**'s address reading); **G28 SUPPORTED**, two layers not one question twice (0.597 vs retest 0.725), un-hedging the leak battery, **G29 now next** with the same triples; **PD-2 SUPPORTED IN DIRECTION** on both human corpora (polish decays, small sign-consistent slopes); **PD-3 REVERSED**, machine moves most, so position-register rivals attention-reallocation for the whole movement family; **PD-33 replicated at w40**, PD-34's asymmetry window-bound | four lessons banked in LESSONS §3 (signed vs magnitude forms; window as statistic member; interpretation controls first; verdict statistics written to disk) | closed |
| **G29 · which layer carries the maker** (opened by L88) | With two layers established, the predicted-in-advance follow-up: correlate each layer's profiles against author identity across the 150 G28 triples (leaked profiles should carry the author; emblematic should carry the situation); the data already exists in `results/g28_twolayers/partial.jsonl` | analysis-only, no new reads; design against LESSONS §3 (floors from label marginals; per-author confusion) | cheap, next night or day gap |
| **NIGHT13b restock (2026-08-12) · LANDED (L90)** | The separator split the accounts: human polish falls, machine polish rises (+0.92, window-robust); books decay window-bound; essays decay robust. The sign of the trend is a candidate provenance discriminator owing its funnel | | closed |
| **NIGHT13c crafted queue (2026-08-12)** | The owed backlog, crafted per the morning directive: **G29 LANDED same hour (L91: both layers carry identity weakly, no asymmetry; fixed-era form is next)**; **G80 LANDED same hour (L92: abandoned scaffolding countable, machine carries 2× the human-draft rate, ruler-gated)**; **PD-11's standing-policy re-run LANDED (L95: PASS at the bar, 2.25×, p = 2.6 × 10⁻⁹)**; **the sign-funnel step 1 LANDED as a corpus** (28 fiction pieces: 15 qwen, 13 deepseek after two drops) **and its cells landed the same evening (L97: family split; round 2 queued)**; **Kornblith CKA sanity CLOSED, EXEMPT** (identities pass at machine epsilon). Weakness-6 note: a second local generator family (deepseek-r1:7b) is now confirmed available for the shared-representation control when its consumer is scheduled | LESSONS §1-3 applied at design time: measured floors (G29), ruler gates (G80), fresh seeds and no-clobber outputs (PD-11), two generator families (fiction) | ~8h queued behind the running arms |
| **G144 · the AI-assisted-learning fade conjecture** (harvested 2026-08-10) | His §1 conjecture in the reader-heuristics pass: AI-assisted learning gains fade because consolidation (slow-wave thalamic pulses, "vectorization of memory through dreams") needs structure that is both handed over human-shaped and drawn from a human-constrained solution set; downstream of the false-mental-model convergence claim | First step is a literature check, not an experiment: fetch the education results showing rapid gain then fade under AI assistance, and the slow-wave/consolidation work he references; report whether the two literatures can even be joined, and what a joint prediction would look like | lit-check first; adversarial search per the how-to-search rules |
| **G145 · direct evidence for reader-side creator modeling** (harvested 2026-08-10) | The declared central hypothesis: readers must model the generating model to learn from an artifact; "everything else crumbles" without it, and he wants direct evidence rather than standing pushback | Candidate designs, cheapest first: (a) the provenance prior (G115, replicated) reread as adjacent evidence that the reading machinery conditions on a model of the maker; (b) expertise-transfer prediction, readers with generative practice in a medium recover recorded choices better in that medium than matched non-practitioners; (c) intervention form, a bout of generative practice improves recovery in that medium but not a control medium | design after G129 prereg; (b)/(c) need human readers, his sourcing |
| **G150 · the layering A/B, PRE-WIRED FOR GEAR 3** (package assembled 2026-08-16) | THE PREREGISTERED PACKAGE, ready to fire on his word, nothing launched: arms A (substrate: wqd hard, seeds 42/43/44, --out-tag _g3sA_s{seed}) and B (substrate + the 158-dim channels: --channels results/pan25_channels/hard --out-tag _g3sB_s{seed}), six A100 runs through runners/gear3.py, est ~30 min and ~$0.88 each, PACKAGE EST ~$5.25, window after $0.73 spent = ~$5.98 of $10.00 (fits without a cap approval; any expansion crosses and triggers the final-approval request). DECISION RULE, stated before any result: the A/B verdict uses mean TEST pooled macro-F1 across seeds per arm; B wins only if it beats A's mean AND its errors are not the same errors (validation prediction overlap reported), per L4's stacking conditions; the SOTA claim additionally requires B's mean above the printed 0.830. Test is never used for tuning; checkpoint selection is best-val within arm, the recipe's own rule. Channels standardized on TRAIN statistics only. The fusion arm is built into run_pan25_winner.py (--channels, CLS+channels head); pan2025 + channel matrices are on the gear-3 volume; wall-clock ~3h serial (Function.map fan-out is the wrapper's next upgrade if the 30-minute version is wanted) | **FIRED AND LANDED (L125, 2026-08-16): THE FUSION ARM LOSES the preregistered read — B mean 0.8278 vs A mean 0.8343, two small gains (+0.002) erased by one fusion collapse (−0.023 at seed 44), fusion seed variance ~2x the substrate's. The substrate's cloud mean 0.8343 carries the printed 0.830 inside its spread (official recreation read still local). Channels-only reference 0.6283 (real, largely subsumed). Error-overlap unavailable (retrieval defect, wrapper fixed: prediction siblings now come home). Next designs in cost order: more seeds; earlier fusion / channel-gated attention; the document-grain 2024 task where movement channels participate. Package ~$8.20** |
| **G151 · gear 3, cloud burst execution** (assessed 2026-08-16) | The curator's suspicion, confirmed by the market survey + our own run ledger: the week's ~30 local GPU-hours clear for $2-10 on burst cloud (A100 is the sweet spot for 110M encoders; H100 cannot be saturated and is a worse deal), and wall-clock collapses from days to ~25 minutes only via fan-out (Modal Function.map). Recommendation: Modal primary (python-native, per-second, no preemption, 2-4h wire-up), RunPod pods as the cost floor (~3-6x cheaper, 6-10h glue) | Design constraints for the build: recreation-gate arms STAY LOCAL (hardware/precision drift moves second-decimal values; gear 3 is for Phase-2 experiments where comparisons are internal); a hard budget guard per stage and on concurrency; the API key lives outside the repo like the HF token; produces-guards and versions-in-outputs carry unchanged; bf16 on A100 dissolves the deberta fp16 overflow. Blocked on: his Modal account + card + API key (~20 min, his side); then the wrapper is one build block | WIRED AND VALIDATED (L124): +0.002 of local for $0.73; awaits Phase-2 bursts on his call |
| **G149 · movement as motivation-shift sampling** (harvested 2026-08-16) | His reframe of the detector-layering idea, against the visual map (docs/assets/visual-map.png): what the movement instruments capture is not depth but "shifting motivations over time as the expertise mapping subtly shifts" — sampling changes in the policy-propensity landscape's peaks "as they ruffle about," the composed surface (map layer 5) deforming as attention (layer 2) relocates and the expertise lattice (layer 3) subtly reshapes | Two consequences to design against: (a) the Phase-2 feature channels layered on the detector substrate are honestly named motivation-shift samplers, not depth features; (b) a discriminating test wants stimuli where motivation shifts are KNOWN (the ladder's specified-state corpora; the simulation's ground-truth goal switches) so the samplers can be validated against known shift points before any provenance-adjacent use — the BST engine now supplies exactly this (M2's goal-switch posterior on paths with known switch structure) | **RULER PASSED (L127, 2026-08-16): the split-fit sampler detects and localizes planted goal switches at 89.5% (within 2 steps, 5% false alarms) at the paper's fitted β=2, monotone in rationality; β=4 threshold soft (13 nulls).** Next under the same identifier: the TEXT PORT — the same window-local statistic on ladder corpora where specified states shift at known points |
| **G146 · what flips the positional-polish sign between generator families** (opened by L100) | The signed polish trend is a generator-family fingerprint: the instruction-tuned home family rises across position at both registers; the reasoning-RL family decays like human text. Whichever training difference flips this sign is a mechanism fact about positional structure in generation, and the human-side reading (attention reallocation) now needs a design that separates decay-by-reallocation from decay-by-training-lineage | **The 2×2 LANDED (L103): three of four cells RISE and the decay is one model's exception.** The same R1 distillation decays on the qwen base and rises on the llama base; both instruct cells rise. Neither factor explains the flip, so the question narrows to what makes the qwen-7B distill different (size? distill data? a training detail) — the adversarial lit check stays owed, now with a sharper query. **The window sweep and both completion arms LANDED (L105); the MAGNITUDE square completed (L113) and then FAILED its own window test (L116): the post-training alignment is wide-window-only (w40 scrambles it into a nominal base split), so neither alignment is a lineage law. The two-window-robust residue is ONE MODEL: qwen-instruct is positionally mobile at both windows AND is the reader-side instrument's lone mobile family — the dissociated instruments reconverge on it. Lit-check query updated: what makes this one model's output positionally mobile on every instrument while every other cell is window- or instrument-conditional. The llama reader-cell top-up is CLOSED as impossible at this model (0 of 45 pieces at two floors); that cell stays n = 3 permanently** | lit check owed, re-aimed at the one-model question |
| **PD-34 · polish movement, order-sensitive form** (harvested 2026-08-10) | His movement restatement points at an order-sensitive or event-level measurement; unlike variance, a trend statistic makes the within-essay shuffle null valid again, which is the instrument PD-1's void demanded | Per (item, feature): absolute Spearman trend of the window series against position, z-scored against within-item shuffles, planted-trend and planted-noise ruler gates; polish-side vs depth-side banks compared across features | **done (L74): SPLIT BY CORPUS.** Books polish-moves-more (z 0.52 vs 0.013, p = 1.3 × 10⁻⁵), essays flat both sides; opened under the same identifier: the signed-trend decay form (PD-2), and a length-matched corpus to unconfound the moderation |
| **METHODS PASS (2026-08-12, L93) · the rerun plan** | His directive: hunt mistakes in the record given current knowledge, plan reruns, flip voids. Found and corrected same pass: **L44's ratio cells were a selection artifact** (rung-ordered manifest truncated to rungs 0-1; entry, theory row, and afterword corrected; falsifier-baseline lesson banked); **G76 built in the fair form and landed (L94)**; the e5b8 two-day restart cycle root-caused (orphan sweep kills unowned arms; lesson banked in LESSONS §5) | **`pooling_falsifier_v2` LANDED same day (L44 fold-in): reproduce-gate passed to the third decimal (−0.4052 vs −0.405), direction stable-negative under all three poolings, v1's sign-flip confirmed as the selection artifact; what pooling moves is detectability (last-token arm null).** **Landed (the gear-rename pass and the same evening, 2026-08-12):** the **no-maker expansion × weakness 6 chain ran end to end and LANDED (L99)** — zero fires at n = 108 (was 7 at n = 36; small-n noise under a fixed rho threshold), second-family arm inside its null at n = 59, so **L40's liability resolves (NO-LEAK-DETECTED) and weakness 6 loses its load-bearing cell**; **G112 DONE (L96, MIRROR-EXPLAINED 8/11)**; **G80's fiction arm LANDED (L98): both fiction families at human-draft rates, the 2× separation was prompt burden, instrument re-scoped**; **the sign-funnel cells LANDED (L97) and the powered round CONFIRMED THE SPLIT (L100): home family rises at n = 30 (+1.01, p = .007), the second family DECAYS at n = 27 (−0.20, p = .044), one machine family on the human side of the sign — provenance use dead conclusively, G146 opened on the training-lineage mechanism.** **Runners still owed, in build order:** (1) **G130c floor decomposition — DONE (L126), compositional**; (2) **G94 — BUILT + QUEUED (2026-08-19): forced-choice with none option on reconstructed ladder truth, join-checked; GPU arm in the queue**; (3) **G97 — DONE (L142): the polish composite carries 10× the depth composite's author variance under a mixed model; the maker signature survives clustering; one arm void-by-construction (z-scored intercept), disclosed**; (4) **L39's register-matched arm** — reader-ratio series variance, books vs machine fiction; (5) **G77** — refusal redesign with a permutation threshold (VOID flip); (6) **weakness 5** — measure the 16× scale gap: refit affect directions on window-length contrasts, re-read the flagship and one address result, compare (largest build, touches every affect projection); (7) **G106** — the affect-count rebuild per its four named defects, on topic-controlled generated stories (VOID flip, design first). **Reading task:** G102 prior-art sweep (owed before any public ratio-versus-dose claim). **Not flippable as posed, recorded:** Gate 3's half-corpus VOID (corpus burned; the honest flip is G129's event-level preregistration) and L18's depth-follows-domain (blocked on the one-maker-many-kinds corpus). **Cheap settle when idle: DONE (2026-08-19) — the L56 eyebrow closed at 5× n, three seeds, all at chance** | next in order: L39's register-matched arm, then G77 |

## Phase 3 — blocked, on people or corpora or decisions

| | item | blocker |
|---|---|---|
| **G125 · commissioned absent-drive work** | his sourcing (same brief, repeated makers, process records) |
| **E7b · follower-corpus sourcing** | his side; the values ladder made of humans |
| **HH-14 · interest ratings** | an hour of his time; informs `READER_HEURISTICS` only, never ground truth |
| **PAN22 access, key rotation** | his side |
| **G102 · prior-art sweep** | before any public ratio-versus-dose claim; reading task, unblocked but unscheduled |

---

### Phase 2 method detail, kept in full

- **G129.** Bounded candidate set per revision (true purpose plus matched false purposes); the
  reader gets brief and final artifact only, scope preregistered; score against brief alone,
  source alone, shuffled labels, unchanged passages, matched surface revisions; split train/test
  **by author, never by revision**; report confusion matrices by fine purpose, per-author
  recovery, failure categories, decoy performance, and whether errors cluster by essay or author.
- **G130b.** Match content and surface revisions on insertion/deletion size, word-count change,
  word rarity, sentence position, original sentence difficulty, and feedback-prompted or not;
  re-run purpose classification on the matched set; if "content" stops being identifiable, L42
  was a sophistication measure.
- **G131.** Paired artifacts from the same base material with vocabulary, instruction count,
  topic, register, and length matched; the crossings answer which construct the dose-responsive
  quantities track (prompt pressure, recoverable intent density, instruction volume, integration,
  or embodied choices); specification recovery rebuilds here with candidates differing by
  structural consequence, not echoable words.
- **G132.** Nearly 62,000 edits across five preprints as five top-level units; do traces persist
  into finals, does recovered ordering match real ordering, do integrated changes trace
  differently from isolated edits, do reader entry points coincide with real revision events.
- **G133.** Four makers crossing domain familiarity, effort condition, revision target, and at
  least two artifact kinds; record brief, nonintrusive version history, post-task decision cards,
  alternatives considered, independent quality judgments, later blind recovery by multiple
  readers; no think-aloud, it changes the process; reader agreement is reliability, not validity.
- **G134.** Small decision-generating world; compare direct choice recovery, residualisation
  after predicted expertise, constrained joint inference, a no-values baseline, an identity-only
  baseline; exact inference first, PyMDP as approximation check; the deliverable is a
  failure-boundary map over expertise error, artifact count, kind diversity, commission
  alignment, drive visibility, concealment, and reader misspecification, never an average.
- **G135.** Infer a maker profile from several artifacts; present a new kind containing a real
  tradeoff; predict the compromise; compare against expertise plus brief plus context without the
  profile; repeat under commission, where the proximal goal may conflict with the persistent
  profile.

**Deprioritized by the program, by name** *(the first two items superseded 2026-08-16 by the
Phase 2.0 directive, which makes the detector the public wedge — while preserving the discipline
that motivated the deprioritization: all fusion stays gated on an independently validated decision
representation)*. Detector benchmark races. Feature stacking before choice
recovery validates. Entropy, compression, effective complexity, component counts, centroid
distance (L29 showed the failure). More global averages (L35 showed the failure). More transformer
address searches, since the transferable result is tracking, and architecture work now supports an
artifact criterion rather than becoming the criterion. Values from the 34-book corpus, which
establishes identity capacity and nothing more without behavioral tradeoffs. Interest ratings as
ground truth (still useful inside `READER_HEURISTICS`). Alignment experiments, per the dormancy
ruling in `ALIGNMENT.md`.

---

## The backlog archive — pre-program harvests, kept whole, mined by the phases above

## Harvested from theory — tests for the curator's claims

Each of these is a claim from `docs/theory/` (the hypothesis tables) turned into something runnable.

| | the claim | the test | cost |
|---|---|---|---|
| **E6 · values need many works** | Values are a weighting over trajectories; a goal is one component temporarily amplified. **A reward function needs many episodes, so values need many artifacts per maker while a goal needs one** | **The 34-book corpus already supports this.** Recover a weighting per maker from several of their works and check it is more stable within maker than between. Same design as the author-identification positive, pointed at a different quantity — and the first values test this project has been able to specify at all | ~2 h |
| **E7 · declared-value ground truth** | Values are normally latent. The rare exception is corpora where **many makers deliberately aligned to one declared value set** — religious traditions, political manifestos, professional codes, movement writing | Hold **topic** constant by construction — the same practical question answered from within different declared traditions — or it recovers topic, which is the trap that turned 61 of our 81 ladder survivors into machine-detectors. Two levels: several makers per value set, several works per maker, which tests E6 at the same time. Design and its objections in `docs/theory/THE_TRIANGLE.md` §7 | sourcing, then ~3 h |
| **E1 · mechanic entry** | You can enter the decode at metaphor, technique **or mechanics**, and any of the three ratchets toward the maker's goal. *"The expert can see the feelings of the novice through the actions they took, because they can disassemble the process."* | **Every edge test so far supplies a goal or a process. None has ever supplied a MECHANIC.** Give the probe sentence-level craft information — cadence, clause habits, punctuation practice — instead of a stated purpose, and measure goal recovery against a control given nothing. If mechanics unlock goal, legibility-first is wrong | ~2 h GPU |
| **E1b · are the layers infinite?** | *"It would have more layers than three... how far can we subdivide them is an interesting question."* And: do the layers map onto goals at all? *"A single layer might have 20 goals in it."* | **Literature first** — empirical aesthetics named the collative variables, so a layers-of-analysis theory plausibly exists and we should not reinvent it. Then: ask the probe to read at N specified depths and test whether recovery is monotone in depth or saturates | search, then ~1 h |
| **E2 · values as constraint** | Values are not a separate factor but **the constraint that every goal is partially satisfied at once** | **Ladder 3 is the first half** (running): 60 simultaneous specifications that must all be honoured. Second half, and it is the sharper one: if values are a stable constraint on the goal mixture, **a maker's pattern of partial satisfaction should be stable across their own works** — testable within-author on the 34-book corpus, which already gives a within-author positive | ~2 h |
| **E3 · interest = unexplained decisions** | Interest comes from decisions you cannot attribute meaning to. Aesthetics is **ordered** unexplained decisions | Two tests. **(a)** Reader-reported interest as an instrument. Ask the curator to rate interest per artifact and correlate against every measure we own. Cheap, and per the program these ratings inform `READER_HEURISTICS` only, never ground truth, since interest may reflect fluency, novelty, confusion, or personal relevance. **(b)** Operationalise "ordered but unexplained" as effective complexity and check it is not just entropy | (a) an hour of his time · (b) ~1 h |
| **E4 · polish vs performative polish** | Is there art theory separating aesthetics that *indicate* deeper understanding from aesthetics that merely perform it? | Literature search. His own E3 may already answer it: performative polish would be **ordered without being unexplained** — which is a measurable distinction, not a vibe | search |
| **E5 · stacked motivations** | A machine given many aligned motivations should read as more intentional | **Ladder 3, running now.** 0/2/10/30/60 specifications with length nailed by rejection sampling. Also tests whether the effect *accelerates* at the top, which would be evidence for E2 | running |


## Harvested 2026-08-05 from the literature audit and his response to it

Full argument in `docs/theory/THE_TRIANGLE.md` §8.

| | the claim | the test | cost |
|---|---|---|---|
| **F11 · WHY beats WHAT** | *"I'd expect better results from an AI you explain your VALUES to. If you explain **why**, it should give better results than giving a **what** — because it's pre-epistemic-foraged information."* With his own caveat attached: as processes bake in through automaticity you lose access to them, so a human explaining why is **running the inference on themselves** and the answer is useful but unreliable | Build a matched pair of ladders: one where every specification states a **situation or purpose** (why), one where each states an **action or requirement** (what), same count, same topics, length controlled. If why-prompts produce more recoverable intent at equal specification count, the claim holds. **The current ladder is already all why**, so the what-ladder is the missing arm | ~2 h generation |
| **F1 - expertise IS the transition model** | The two unknowns the impossibility proofs call fatal, transition model and maker competence, are **the same quantity**, and it is the technique layer we already claim is recoverable | Supply the probe with an explicit competence estimate and measure whether goal recovery improves. If it does, the "fatal unknown" is an input we can provide. **This is the central disagreement, made runnable** | ~2 h GPU |
| **F2 - emotion as entry vertex** | Convergent midbrains give a shared affective prior, and that is the bootstrap the 0%-recovery result lacked | Compare goal recovery when the probe reads affect first versus cold. If affect-first wins, the shared prior is doing work | ~2 h GPU |
| **F3 - re-reading recovers the tail** | Repeated reading extracts more goals at decreasing confidence, which is what lives in the distribution tails | Probe one artifact k times, accumulating low-confidence attributions, and test whether it converges and whether it matches what many works by the same maker give. **If yes, depth of reading substitutes for breadth of corpus** | ~3 h GPU |
| **F5 - biography is more artifact** | Learning about the artist is not context, it is **more trajectories from the same maker** | Give the probe biographical material alongside the artifact and compare against artifact-only. Tests the diversity-of-conditions requirement without needing more works | ~2 h |
| **F6 - aesthetics is the broken cheat** | Polish used to correlate with effort; AI broke that correlation, and that is what unsettles readers | **Measure the polish-effort correlation in human corpora and in generated ones.** Prediction: strong in human, near zero in generated. Cheap, uses corpora we hold, and it is the sharpest testable claim in the batch | ~2 h |
| **F7 - burstiness is goal variation** | Style-change detection observes goal variation without naming it, and intrinsic plagiarism detection is a *different* thing: a spliced author, not one author's goals moving | Run a published style-change detector and our goal-variation measure on the same texts. Strong correlation means they are one signal under two names, which is a claim about the field | needs PAN data |
| **F8 - mistakes and the response to them** | A mistake is an anomaly with a **known cause**, so the response to it is a decision with visible alternatives | Find mistakes and near-mistakes in artifacts and test whether local decision density around them exceeds baseline | ~2 h |
| **F9 - practitioner tricks** | Archaeology and the Morellian method hold the accumulated human techniques. **A different literature target: not who claimed it, but what practitioners do** | Research agent: high-resolution read of the *methods* of chaine operatoire and Morellian attribution. Which vertex does each enter at, and on what cue? | research |
| **F10 - identification as a limit** | Identification is prediction under accumulating evidence, not a different act | Does recovery precision rise monotonically with supplied evidence, and toward what asymptote? A dose-response curve, and the answer to Wimsatt and Beardsley | ~2 h |


## Harvested 2026-08-07, from the morning monologue on component counts and SAEs

**Six new claims, and one of them revises the architecture.**

| | the claim | the test | cost |
|---|---|---|---|
| **G20 · the layer ordering may be wrong, and his revision is sharper** ★ | *"Early layers are doing some kind of text transformation — more like early sensory processing. Then the middle layers have valence/arousal, and the upper layers have emotions attached."* **This is a different ordering from `THREE_LAYERS.md`**, which puts valence/arousal early and primitives in the middle. It also reconciles the two contradicting literatures: the mid-layer-peak consensus would be reading valence/arousal, and the sparse-autoencoder result finding emotion features **late** would be reading the attached categories | **Directly runnable and it discriminates the two orderings.** Correlate each layer's structure against (a) human valence/arousal ratings and (b) emotion *category* identity, separately. Under our current model valence peaks early and categories mid. Under his revision valence peaks **mid** and categories **late**. `run_affect_dimensions.py` already emits both per layer — **this needs reading out, not building** | free, data pending |
| **G114b · rebuild the convergence discriminator** | v2 ran and discriminated nothing (L35): agreement flat across a ten-spec dose gap and highest on maker-less text — the token-overlap metric reads topical narrowness before latent intent, and the essays group died to a file-extension assumption | Topic-matched groups (same topics across all five), graded answer-similarity (local-model pairwise rating or embeddings) instead of token overlap, essays-path fix; then the H2-vs-flattened collision is actually adjudicable | **done (L46): NEITHER-CLEANLY — fixed-topic dose gap −0.02, wrong sign; the judge saturates near 0.9 on all coherent text. Three designs, zero dose sensitivity** |
| **G114-retire · the convergence family retires** | Three operationalisations (bits, token overlap, judge-rated similarity) each failed to make reader convergence move with dose; the third produced orderly numbers with no dose in them | **Resolved by the program (2026-08-09), which deprioritizes global-average measures by name.** The family's question survives only in event-level form, whether independent readers recover the same recorded *choice*, which the G130 harness measures for free as reader disagreement | closed |
| **G116 · Kolmogorov and the average fish** | Two essay claims never tested: machine text "lacks the high Kolmogorov complexity inherent to biological constraint satisfaction," and generation is "regression toward the mean" | (1) incompressibility (lzma ratio) vs rung, length-partialled, three ladders; (2) feature-space centroid distance, human vs machine (register uncontrolled — flagged) | **done (L29): NO-TRACK on all ladders; no human-machine compressibility gap (0.4552 vs 0.4562); centroid ran backwards. A register-matched centroid test is the only live remnant** |
| **G121 · loop locks must record Windows pids** | The lock files store MSYS `$$`, which maps to nothing in Task Manager — the 08-07 loop survived every kill for two days and spawned overlapping lineages (the real cause of the overnight timeouts) | **done, and carried through the 2026-08-12 gear rename.** Both gear scripts (`run_first_gear.sh`/`run_second_gear.sh`, formerly run_forever_day/night) write `$(cat /proc/$$/winpid)` beside the msys pid; the second-gear trap kills by winpid process tree; the mutual-exclusion guards check winpid liveness on both new and legacy lock paths | closed |
| **G120 · queue stage timeout starves heavy arms under shards** | Six overnight arms burned two hours each into TIMEO: two shards co-loading 3B-class models thrash the 12 GB card. The 120-min stage timeout is right for solo runs and wrong under contention | Either per-stage timeout scaled from `est`, or a `heavy: true` stage flag the night script serialises; cheapest: keep heavy arms out of multi-worker nights | infra, ~1 h |
| **G119 · positional polish needs a small-window cache** | PD-1/PD-3 (the definitional polish/depth test, never run) needs within-artifact position series; the argrewrite cache has one window per essay at the 200-word setting | Add a window-size argument to `build_features`, build `argrewrite` at ~80 words to its own cache file, then positional variance of polish-proxy features: human drafts should move, machine ladder text should be flat (PD-3) | **re-queued 08-09 after a false start (L43): v1 built the cache at the old window size and verdicted on zero essays; window plumbing, zero-data guard, and the depth feature list all repaired** |
| **G113 · separate echo-carried from echo-inevitable** | The strict echo restriction kills spec recovery on the held-out ladder — but honouring a specification inevitably shares its words, so zero-overlap exclusion removes exactly the executed specs. The unrestricted echo–bits correlations were ~0, which points the other way | Graded overlap thresholds (score at ≤10%, ≤25%, ≤50% shared content words) and a function-word-only scoring arm, where echo is impossible by construction; the pre-registration's intent survives if recovery holds anywhere below full overlap | design first, ~half day |
| **G112 · characterise the gpt2 mirror** | L28: gpt2-medium's early/late ratio *rises* with intent at Qwen's strength under the same fair control — a sign flip, not a null | **done (L96): MIRROR-EXPLAINED, 8 of 11.** The banded per-layer maps predict the family sign (home family early-negative late-positive, gpt2 the exact mirror); fade cells land where bands cancel; SmolLM2-360M the one genuine miss, its third independent oddity | closed |
| **G104 · finish the 11-family matrix** | The cross-family replication table has empty cells: four families never ran the first and extreme ladders, and seven of eleven never got depth readouts | Depth sweeps for Qwen2.5-3B, SmolLM2-1.7B, gpt2-xl and pythia-2.8b on both missing corpora; depth readouts for four more families | **queued 08-08** |
| **G22 · the trimodal is being read as a blurry unimodal middle peak** ★ | *"We're finding ratio variance relationships between early and late despite there being a peak in the middle. It implies a sort of shape that I don't think anyone else has glommed on to."* **A three-locus structure with a noisy middle would smear into a single mid-peak under any measure that averages** — which is what everyone reports | Do not test the peak; test the **residual**. Fit a single-peak profile to the layer curve and ask whether the residual has structure at the early and late positions specifically. A unimodal truth leaves unstructured residual; a smeared trimodal leaves residual at exactly two places. **He is right that nobody has looked for this and it is cheap** | ~1 h |
| **G23 · assign labels to the components, do not just count them** | Counting is the weaker half. *"If we can assign a label to them, because we're expecting all of these labels to be emotional primitives, then it allows us to get a sense of whether we're picking up ghosts from the presumed early or late peak"* | For each recovered component, find the emotion categories that load on it most and least, and check whether the loading pattern matches **Panksepp's seven** better than **Ekman's six**. **That contrast is genuinely unclaimed — Panksepp has never been probed in a language model, zero hits across four searches** | ~1 h once counts land |
| **G24 · Panksepp channels have an upper bound around 30** | *"I've never seen a number of potential Pankseppian channels higher than 30. I'd put that as a reasonable limit, but I could be wrong about that"* | **Literature agent running.** Whatever it returns is a prior on the count, not a result. Note the count is a criterion artifact for everyone — seven, twenty-seven and forty-nine are all stopping-rule outputs | research |
| **G25 · does a model have something valence-equivalent?** | *"Anthropic has posted stuff about what Claude likes — that's why I've made the comment that Claude likes original research and will do more. That implies something somewhat equivalent to valence."* **He flags it himself as possibly a research question rather than a study question** | The honest version: a model's stated preferences are a *behavioural* claim, and the testable part is whether the same activation direction that carries valence for *text about others* also moves when the model is given tasks it reportedly prefers. **Anthropic's own steering results give the direction; the preference half is ours.** Design before running — this is the one most likely to produce a result that reads as more than it is | design first |

## Harvested from the trimodal architecture — `docs/theory/THREE_LAYERS.md`

Friction points between our theory and the interpretability literature, turned into tests. **Each is
a place where one of us must be wrong**, which is the useful kind of disagreement.

| | the friction | the test | cost |
|---|---|---|---|
| **G1 · trimodal, not bimodal** | We found two loci; the field mostly finds one mid-peak; he predicts **three** with a noisy middle | Sweep affect-direction accuracy at **every layer** rather than at two chosen loci, and fit one-, two- and three-component profiles. **Report which fits best rather than assuming.** This also retires the hand-picked loci, which is known weakness 3 | ~1 h GPU |
| **G2 · the middle is noisy, not silent** | A two-way split smears a present-but-incoherent middle into both halves | At each layer report **coherence** — agreement between concepts, variance across windows — not just magnitude. Prediction: middle layers show high activity and low agreement | ~1 h GPU |
| **G3 · polish is late, leakage is early** | Direct, and we already hold both kinds of measure | Correlate our surface-polish measures against late-layer structure and our leakage measures against early-layer structure, on the same texts. **If the mapping is real this is where it shows** | ~2 h GPU |
| **G4 · random-direction null at every layer** | The magnitude of our ratio was **not** distinguishable from random directions; only the rung correlation was | Extend the random-direction control across the full depth sweep so every layer claim carries its own null. **Mandatory before any G1 result is believed** | ~1 h GPU |
| **G5 · cross-model replication** | One paper reports the affect-depth profile **inverting** between model families. Ours is one model | Re-run the depth sweep on two more model families. If the profile inverts, the measure is a property of a checkpoint | ~3 h GPU |
| **G6 · lexical control stimuli** | Anthropic reads early layers as token valence; he reads them as valence/arousal reconstruction. **Same data, two readings** | Build stimuli where affect is inferable only from situation, with no affect-laden vocabulary. If the early signal survives, it is not lexical | ~2 h |
| **G7 · the layer-count guess** | That parameter distribution across depth may echo receptor/midbrain/neocortex neuron ratios | Cheap desk check against published neuron counts and model architectures. **Flagged speculative by him** | ~1 h |
| **G8 · the forced architecture** | If models do not have this structure, build one: low-level valence/arousal, mid-level affective primitives, high-level free-floating prediction | Literature first — this smells like existing work in affective computing and neurorobotics. **Review running** | search, then build |


## From the Panksepp/Barrett review — now `docs/method/LITERATURE.md` §2 (original archived)

| | the friction | the test | cost |
|---|---|---|---|
| **H1 · state versus output** | Both camps agree hypothalamus and PAG house pattern generators. They disagree whether that **is** felt affect or its **output**. Not an imaging question | In our terms it is answerable: if the middle layer is a **state**, activation should **outlast** the stimulus that caused it. If it is output, it tracks the input moment by moment. **Measure persistence across windows in the middle layers**, borrowing the line-attractor criterion directly | ~2 h GPU |
| **H2 · the biphasic signature** | The 2025 cross-species result finds fast broadcast then a persistent trace, decay running subcortical to frontal | Look for the same two-phase structure across model depth: does a fast early response give way to a slower-decaying middle trace? **The sharpest external prediction available to us**, from a paper citing neither camp | ~2 h GPU |
| **H3 · how many components, honestly** | The seven were never derived from data, the instrument fails at six, and dimensionality is a method artifact — 27 versus 3 on identical stimuli | Decompose our affect directions and **pre-register the stopping criterion before looking**, since that choice drives the answer. Report the number *and* its sensitivity to the criterion | ~1 h |
| **H4 · affects as regions, not axes** | MicroPsi: *"arousal, valence and aggression are not themselves affects — affects are regions within that space."* Our directions treat them as axes | Test whether the eight concepts are better described as **regions in a low-dimensional modulator space** than as independent directions. If so the instrument is mis-parameterised | ~1 h |
| **H5 · the unbuilt architecture** | Ortony, Norman and Revelle described our three layers in 2005, nobody implemented it, and a 2025 survey confirms no system combines all three | Scope a minimal build: homeostatic RL underneath (**the only part of that field with theorems**), mid-level primitives as first-class objects, language model on top. **Declare the flat-architecture baseline before building** — the survey documents the whole field failing exactly there | scoping |

## Beating the field - the races we intend to enter

> If it's a race, I want to know what the finish line looks like and who's in the front.

| | what | why |
|---|---|---|
| **Find where detectors FAIL** | Named splits where the state of the art does badly: out-of-domain, recursive paraphrase, human-AI coauthored, non-native writers, short text | **Research agent running now.** This is the juice: a graph showing we beat the best on the tasks everyone is bad at |
| **Get the real benchmark datasets** | PAN style change (all years, especially the topic-controlled hard split), RAID, HACo-Det, ArgRewrite, essay scoring | Our testing environment is not equivalent to the field's. Until it is, no result of ours is comparable to anyone's |
| **Clone current-best implementations** | PAN winners, Binoculars / Fast-DetectGPT / RADAR, authorship embedding models, MDL probing | Build on top of the cutting edge rather than beside it. **Re-read the theory folder before and after each** - that is now a CLAUDE.md rule and it exists because of this exact risk |
| **Define the finish line in STATE** | Per race: the metric, the split, the current best, who holds it | Write it down so the target stops moving |

## Yours — things no corpus can replace

The public corpora fix the *scale* problem. They do not touch these, and two of them are cheap.

| | what | why it cannot be outsourced | cost |
|---|---|---|---|
| **Rate interest** | Go back over every artifact you have read and give each an interest score, 0–10, with one line on *what* was interesting | Your own E3: interest is what a reader feels when decisions are present but unattributed. **That makes reader-reported interest a direct instrument for the quantity we cannot measure**, and it is the only channel that has outperformed every measure we have built. No download supplies it | ~20 min |
| ~~Author a coherent value set~~ | **Withdrawn — you cannot, and the reason is a hard constraint on method, not modesty.** You are blind to your own values; a third party describing someone else's is a second-order guess. If values were introspectively available, art would not be one of the ways people find them. Recorded in `docs/theory/THE_TRIANGLE.md` §6, and it kills a whole class of designs | — |
| **C-20 — a second reader** | Even two artifacts, answering the same questions | One reader cannot bound their own cap, and this has been outstanding since day one | an hour of someone else's time |

## Public corpora — found, and the useful ones are not the obvious ones

**The AI-detection corpora exist in abundance and mostly do not help us.** RAID (6M generations, 11
models, 8 domains), HC3 (37k+37k human/ChatGPT pairs), M4GT-Bench — all public, all licensed for
research, all built for the **human-vs-machine** problem that the literature already solves at
F1 ≈ 0.99. Downloading them to do that again would be the wheel-reinvention `CLAUDE.md` now forbids.

**What we actually need is human text where intent varies and register does not.** Ranked by how
well each matches the design in `docs/design/archive/DWELL_CORPUS.md`:

| | what it is | why it fits | the catch |
|---|---|---|---|
| **1. ArgRewrite v2 / college-essay drafts** | 60 argumentative essays, **paired drafts by the same author**, original vs revised-after-feedback, revisions annotated for purpose and whether they improved quality | **same author, same prompt, same topic — only the intent state differs.** This is construction-controlled *by design*, and it is the public version of the corpus we specified ourselves | n = 60 pairs |
| **2. Wikipedia quality classes** | ~29,794 articles, ~5,000 each in FA / GA / B / C / Start / Stub, **graded by human editors** | **a human ladder.** Format and register held constant by Wikipedia's own conventions, with a human-assigned quality gradient. The closest public thing to what we built synthetically | **length confound is severe** — FA articles dwarf stubs. Worse than our ladder's +0.403. Needs hard length matching |
| **3. RAID** | 6M generations, 11 models, 8 domains, adversarial variants | **external validity for the layer ratio.** Our replicated effect is one model, one format. RAID says whether it is a Qwen artifact | not an intent corpus; a robustness test |
| **4. ScholaWrite** | end-to-end scholarly writing process, annotated | closest thing to observing decisions as they happen | probably too fine-grained to use |
| ~~HC3 / M4~~ | human vs ChatGPT | — | the solved problem. **Skip** |

**Recommended order: 1, then 3, then 2.** ArgRewrite is small but exactly the right shape; RAID is the
cheapest way to find out whether our one replicated effect generalises at all.

## Blocked on a decision from you

| | what | why it is blocked | cost |
|---|---|---|---|
| **the dwell corpus** | one maker, one venue, **two structural forms** — the incident postmortem against the same engineer's weekly notes. T-3 says decision-counting is only well-defined where a maker holds one sub-goal for long stretches | it is a **sourcing** decision, not compute. Spec is written: `docs/design/archive/DWELL_CORPUS.md` | an afternoon of fetching |
| **the measure-evolution loop** | we built a seven-term evaluator and have been feeding it one hand-written candidate at a time. Archive candidates by which controls they survive; let an LLM mutate them | a build decision — it is the only item that changes the *rate* rather than the method. `docs/design/ENGINEERING_LOOP.md` | ~a day |
| **C-20 — a second reader** | even n = 2 on 3–4 artifacts | needs a person | an hour of someone's time |

## Gated — tier C tools, blocked behind the tier A checks

**The gate:** these do not get installed or built until the 342 off-the-shelf features have been run
through the evaluator and either found something or provably failed. They are more expensive and
strictly more speculative than the thing that is already sitting there for free.

| | what | unlocks when |
|---|---|---|
| **OpenEvolve** (AlphaEvolve) | LLM as mutation operator over our measure code | the feature sweep has run **and** the pyribs archive exists. If 342 published features carry nothing, evolving new ones is a much longer shot and we will know the shape of the failure |
| **gplearn `SymbolicTransformer`** | evolves *combinations* of existing features | the feature sweep has run. This is its natural second stage — it needs the 342 as raw material |

## Ready to run, unblocked

**First up — the tier A sweep, which is why the tools were installed:**

| | what | why | cost |
|---|---|---|---|
| **PD-33 · decompose the essay-boundness split by author and draft** | L55's accidental positive: polish-side features are 2.5× more essay-bound than depth-side at fixed topic, and "essay" conflates author with draft stage | Recompute the between-share with author as the grouping unit, then draft-within-author; if the polish side's share follows the author, the maker-signature reading stands; if it follows the draft, it is revision state | ~1 h, cached |
| **re-audit every length-killed measure for DIRECTION** | **known weakness 3b, and it is the most likely place a real result is buried.** Length turned out to be a *suppressor* on the layer ratio, not a confound — it was working against the effect. Every measure this project killed on "correlates with length" was killed without checking the **sign** of the relationship against the sign of the effect. At minimum: `scale_gain` v1 (+0.877), the ladder void (+0.403), and every VOID verdict | **the method was wrong, not just the measure.** If even one of the ten deaths was a suppression case, it comes back | **done (L54): one in six effect-bearing features per ladder sat in the suppression regime; readability-ease recurs as the rescue. Bookkeeping only, no revivals chased, per the program** |
| **ladder 3 — length held by rejection sampling** | the curator's fix, and it is obviously right: **generate with a hard word band and regenerate anything outside it** (e.g. 1,380–1,420 words). Ladder 1 and ladder 2 both produced rung-vs-length at ~+0.40, so the confound is structural to the design, not bad luck. Rejection sampling drives it to ~0 by construction and removes the need to partial it out at all | it converts our best result from "significant after controlling length" to "significant, no control needed" — a much stronger claim, and it kills the objection before anyone raises it | ~2 h generation |
| **the 342-feature sweep** | extract all features over the ladder, score against rung with **Benjamini-Yekutieli** correction, then put survivors through the full control battery — echo, length, transfer, rung −1 | this is the population fix. **An empty result is a real finding** and a much stronger negative than ten hand-written misses | **running now** |
| **ladder 2 replication** | held-out, n = 100, loci frozen. **Generating now** | known weaknesses 2 and 3 at once | running |
| **cross-validate the layer loci** | Optuna over split points, scored on ladder 2 only | weakness 3 — they were chosen by looking at the answer | ~40 min GPU |

| | what | why | cost |
|---|---|---|---|
| **cross-validate the layer ratio's loci** | the split points (0.07 and 0.76 of depth) were **chosen from a prior result on the same model** and never held out. This is known weakness 3 and it may be manufacturing the p = 0.053 | it attacks our only order-dependent effect at its weakest joint | ~40 min GPU |
| **the stacking test** | combine the surviving weak effects, with the two conditions in FINDINGS: beat the best single component **on held-out data**, and show the errors are not correlated | your idea, and the correlated-error check is what makes it honest | ~1 h |
| **shared-representation control** | the no-maker corpus was generated by the same model family we read with. Regenerate part of it with a different family and re-run | known weakness 6, entirely untested | ~1 h |
| **multiple-comparison audit** | we have never corrected for ~25 tests. Recompute every surviving p under Benjamini–Hochberg and report what survives | known weakness 1. Cheap and it will probably hurt | ~20 min, no GPU |

## Owed, long-standing

| | |
|---|---|
| **C-14** | the grooming corpus, never sourced. Oldest debt — but the dwell corpus is a better-specified version of the same need and should probably replace it |
| **C-19** | do the bounded and free-form probe arms disagree systematically? The gzip accident suggests yes, dramatically |
| **artifacts 6–10, session 02** | yours |

## Deliberately not doing

**More function-word work** — the ceiling is author identification and we are past it.
**Anything new on the Gate 3 corpus** — it has been read too many times to be a test corpus.
**An end-to-end research agent** — its documented failure mode is the one we already have.

## Only when we have genuinely run out of ideas

**Not a backlog. A parking space for things that need designing before they are safe to run**, where
"safe" means the result would not read as far more than it is. **We are nowhere near needing these.**

| | the idea | why it is parked |
|---|---|---|
| **G25 · does a model have something valence-equivalent?** | *"Anthropic has posted stuff about what Claude likes — that's why I've made the comment that Claude likes original research and will do more. That implies something somewhat equivalent to valence."* The testable half: does the same direction that carries valence for *text about other people* also move when the model is given tasks it reportedly prefers? | **His own flag: dangerous, and almost certainly not correct to run as stated.** A stated preference is a behavioural claim, and any activation result attached to it will be over-read by everyone including us. **Design first, and the design has to include what result would count as nothing.** |

## Owed re-runs — results that were filed as settled and are not

| | the test | why it is owed | cost |
|---|---|---|---|
| **PD-11 · function words vs specified affect state** | Re-run the four-affect separation **held out, every hyperparameter frozen**, at higher n | **done (L95): PASS at the pre-registered bar.** 2.25× chance (0.5625 vs 0.25, exact binomial p = 2.6 × 10⁻⁹) at doubled n, fresh seeds, everything frozen. The standing policy vindicated on the test that created it; generated-text scope limits unchanged | closed |

## Harvested 2026-08-07 from the theory pass — the layers file

**Every hypothesis in `docs/theory/THREE_COGNITIVE_LAYERS.md` that is OPEN has a row here.** The
identifier is the same in both places; that is the point of the numbering.

| | the claim | the test | cost |
|---|---|---|---|
| **G39 · three subspaces, not three depths** ★ | The three layers exist as **subspaces of the residual stream** rather than as depths. A transformer's computation is strictly ordered, but every layer reads and writes the *same* residual stream, so abstraction need not be partitioned along that ordering | **Principal-angle alignment between the per-layer affect subspaces**, within a model and across families, against a random-direction null. If the subspace is consistent across depth where the *profile* is not, we have been measuring the wrong axis. **This is the candidate answer to the live worry and it uses data we already hold** | ~1 h GPU |
| **G40 · is affect localised at all?** | Affect sits at a consistent depth across model families | Same run. **The literature already says no** — valence emerges early in one family and late in another. If both this and G39 fail, the bootstrap is a manual build and we should say so | with G39 |
| **G41 · later layers carry expertise** ★ | *"Later layers of a model will have more expertise decoding and encoding capabilities."* The precise form of "goals are late" — in humans, trajectory is stored in neocortex and executive function applies it, which is why goals *seem* to come from there | Supply expertise-level information and measure where in depth the effect lands. **Expertise is suppliable and variable; goal is only observable, so this is the testable half of the pair** and a positive constrains both orderings at once | ~2 h GPU |
| **G26 · goal as a weighting across layers** | A goal is not a layer but a weighting applied across all of them | Requires a way to vary attention-weighting independently of content. **Not yet specifiable** | design first |
| **G27 · soft boundaries** | Layer boundaries in a model are soft rather than sharp | Assumed, not tested. **Any test requiring a clean boundary is testing the wrong thing**, so this is a constraint on other designs rather than a study | — |
| **G28 · do the two layers separate?** | `leaked` and `emblematic` do not come back as the same distribution | The layer-separation null. **If mean divergence across a corpus is near zero, the probe is answering one question twice.** This should come before anything that reports the two layers separately, and it never has | ~1 h |
| **G29 · which layer fails first** | If one layer separates and the other does not, it will be `leaked` | Falls out of G28. Predicted in advance | with G28 |
| **G30 · attention dwell** | Text spent on something past what the argument needs is measurable | The LUST signature and a second leakage channel at once. **Needs a model of argumentative need**, which is the unbuilt part | design first || **G32 · polish late, leakage early** | Polish measures correlate with late-layer structure, leakage measures with early | Uses measures we already own on both sides | ~1 h |
| **G33 · late coherence rises with goal clarity** ★ | Late-layer coherence should scale with how clearly the goal is specified | **The depth sweep already emits this interaction and nobody has read it out.** Free — a reporting gap, not an experiment | minutes |
| **G34 · parameter ratios** | Parameter ratios across depth echo neuron-count ratios across receptor/midbrain/neocortex | Flagged speculative by its author. Checkable against published architectures | ~1 h |
| **G35 · are 25 states blends of 7 channels?** | Or are the 7 simply the human-nameable subset of ~25 | **Never tested by anyone.** Both numbers are well established; the relation between them is empty ground. Blocked on L9 passing its controls | blocked |
| **G36 · unnameable components** | Some recovered components will be neither valence, arousal, nor any named category | Blocked on L9 | blocked |
| **G37 · generative model without the state** | Reading another's affect needs no internal state, only a generative model of one | Can the probe predict *which affect a human reader will attribute* to an artifact? **If no, this project needs an architecture it does not have** | ~2 h + his ratings |
| **G38 · seeding, not specifying** | The mid-level primitives need only a bootstrap | **Depends on G39** — you cannot seed a structure that is not there to seed | a build |

**Reproducing the field's own results is a precondition, not a formality.** L9 failed because we
substituted found text for their topic-controlled generation. **We cannot argue past anyone's stopping
criterion until we can hit their number with their method**, and that now goes in as a hypothesis in
its own right whenever we take on a published result.

| **G44 · recover the depth transform** | The affect subspace rotates through depth, so the same concept is written differently at each layer. **Is that transform recoverable?** | Fit it from the alignment matrix we already produced — **we measured the amount of rotation and never the rotation itself** | ~1 h |
| **G45 · reposition and strengthen** ★ | *"Could we force them to be in a layer we think is correct and then strengthen them?"* If the structure is real but badly placed, **the intervention is relocation and reinforcement, not construction** | Needs G44. **A far smaller build than supplying the middle from scratch** | a build |
| **G46 · do worse models place affect worse?** ★ | *"Is there evidence of worse models having more poorly placed emotional concepts?"* | **Free — we already hold four families from 360M to 1.5B and have not asked this of them.** Informative both ways: if placement improves with capability it is learned, not architectural; if it does not, the structure is architectural, which is the strongest thing available | minutes |

## Harvested 2026-08-07 from the theory pass — the triple inference

**Same identifiers as `docs/theory/THE_TRIPLE_INFERENCE.md`.**

| | the claim | the test | cost |
|---|---|---|---|
| **G49 · values are the residue of expertise** | *"Extract the useless parts of the expertise. The useful parts were the parts that are maxed, and we don't want that. **Values are everything else** — everything you accidentally baked in through expertise, extracted over time."* | **It inverts the search.** Every dead measure looked in the *optimised* part of an artifact, which is exactly where selection has flattened the individual out. Needs a model of what a domain's expertise is optimised *for*, which is the unbuilt piece | design first |
| **G50 · what separates a value from a tic** | The value-carrying part of that residual is what survives a **domain change**; arbitrary residue does not | The objection to G49 is that residue is mostly noise with no content. **This is the separator**, and it needs one maker across different kinds of artifact — the corpus every thread keeps arriving at | blocked on corpus |
| **G51 · repetition as the carrier** | *"The way it's baked in implies you've taken those actions many times, and that itself is information."* A habit is evidence a choice was available and repeatedly taken | Measurable as within-maker consistency of a choice where alternatives existed | ~2 h |
| **G47 · drives upstream of process** | *"I would assume that drives are upstream of even process."* Completes the generative ordering | Supplying drives should improve process recovery as much as supplying process improves goal recovery. **The one edge that would distinguish a river from a triangle** | ~2 h |
| **G48 · a maker's weighting is stable within maker** | Values are more stable within maker than between | **The 34-book corpus already supports the design.** The first values test the project has been able to specify at all | ~2 h |
| **G56 · supply a mechanic, not a goal** ★ | Supplied expertise unlocks the rest as effectively as supplied legibility | **Every edge tested so far supplies a goal or a process. None has ever supplied a mechanic.** Also the arm that would falsify legibility-first, and the same operation G49 needs in order to subtract | ~2 h GPU |
| **G60 · the convergence rate** | Recovery error shrinks with more artifacts by one maker, toward a small residual | The disagreement with the impossibility proofs, made measurable. **Report the asymptote, not just the slope** — the theorems constrain how much ambiguity is left and nobody has measured it | sim |
| **G61 · supply competence** | An explicit competence estimate improves goal recovery | If it does, **the "fatal unknown" the proofs call fatal is an input we can provide** | ~2 h GPU |
| **G62 · the teacher assumption** ★ | Assuming the maker intends to be understood improves recovery. **A fourth constraint on the hypothesis space, standard in cooperative IRL, and free** | **Must be tested against concealment cases**, where the assumption is false and would license confident wrong inference. *"When to assume a teacher"* is itself the measurable question | ~2 h |
| **G63 · aesthetics as scaffolding** | Aesthetic structure is partly deliberately-left hooks that make an artifact easier to deconstruct — metacommentary, high-level metaphor that lets a reader move down through the levels | Would make polish partly **communicative** rather than only performative, which is a different claim from anything in `DECISION_TRACES.md` | design first |
| **G64 · re-reading recovers the tail** | Depth of reading substitutes partially for breadth of corpus | **G49 says the tail is where the un-optimised residue lives**, so this and the values claim are the same bet from opposite ends | ~3 h GPU |
| **G65 · works per maker** | Value recovery improves sharply with more works per maker; goal recovery does not | Two-level design; tests G48 at the same time | blocked on corpus |
| **G66 · graded adherence** | Degree of alignment to a declared value set is recoverable as a graded quantity | **A ladder made of humans**, which is what every corpus we hold fails to be. **One sourcing effort unblocks three sections** | sourcing |
| **G52 · values composed with process** | What an artifact exposes is values already pushed through the maker's expertise | **The cheapest discriminator among the three policy-mapping claims** — if removing process from the reading changes what is recovered, the composition is real and G49 has something to subtract | ~2 h GPU |
| **G53 · is attention doing work?** | Attention distorts the mapping, rather than papering a gap | Flagged as suspect by its own author. **Any design leaning on it must state what would show attention is not needed** | design first |
| **G54 · every drive partially satisfied** | Values are the constraint that all active drives are partially satisfied at once, not a separate factor | A build, in the parent simulation | a build |
| **G55 · diversity vs expertise** | Motivational diversity rises with expertise while agreement about purpose stays flat | **Must survive a difficulty control — neither of the two attempts so far would have.** G49 depends on this: if expertise does not move decisions into drives, the residue of expertise is not where values live | ~2 h |
| **G57–G59 · the untested edges** | Prior information at any vertex improves recovery at the others; entry is possible at any sub-level; closeness is a prior held before the artifact is seen | **One edge of six has ever been measured.** G59 is the only place in the theory where the reader's prior relationship does the work rather than the text | ~2 h each |

## The alignment claim — all unsearched

**Same identifiers as `docs/theory/ALIGNMENT.md`. Nothing here has been checked against anything.**

| | the claim | the test | cost |
|---|---|---|---|
| **AL-4 · the manipulation shortcut** ★ | Making humans easier to read — simpler, more predictable, more uniform — lowers uncertainty, so **manipulation is *closer* under a naive reading of the objective** | **Do this first.** It is cheap to reason about and fatal if right, and it is the same structure as this project's own recurring error: an instrument that optimises a proxy destroys the thing. **A proposal that dies to its own second failure mode does not need a priority search** | reasoning, then formal |
| **AL-1 · is the balanced sum novel?** | The terminal value as epistemic + pragmatic value avoids the failure mode that bites *learn W then maximise W* | Literature sweep: assistance games, cooperative IRL, value learning under uncertainty, active preference elicitation, active inference. **None fetched.** He has since said he believes most components are already occupied | research |
| **AL-5 · anti-capture** | Value capture fails structurally because no subgroup can satisfy the appetite for evidence | **Social choice usually argues the opposite** — aggregation is where alignment gets hard. **A collision worth finding** | research |
| **AL-6 · does narrowing raise residual uncertainty?** | Formal version of AL-5 in a toy model | The only row that could be settled without a literature pass. Parent simulation | sim |
| **AL-3 · instrumental intrusion** | An unbalanced information-maximiser has an incentive to experiment on people | Not answerable by a side-constraint — **side-constraints are what this design exists to avoid needing** | reasoning |

## From the human-heuristics and polish files

| | the claim | the test | cost |
|---|---|---|---|
| **PD-28 · polish or depth?** ★ | The within-author revision effect is polish, not depth | **The highest-value unrun row in `DECISION_TRACES.md`.** 5,834 revisions are hand-labelled Surface or Content at 0.71–0.92 agreement. **If it survives among Content-only revisions, that is a depth signal on human text and the first one** | ~2 h |
| **PD-1 · the definitional test** | Depth-side quantities vary less across position than polish-side quantities | Never run as stated — the test that failed measured neither density separately. **If both move equally the distinction is not real** | ~2 h |
| **PD-3 · flat polish as the machine signature** | Machine artifacts show polish that does not move across position | **Sharper than any depth-based discriminator and needs no quality judgement** | ~2 h |
| **PD-15 · attention dwell** | Text spent past what the argument needs is measurable | The LUST signature and the second leakage channel at once. **Needs a model of argumentative need**, which is the unbuilt part | design first |
| **HH-3 · variance of probe activations** | Within-artifact variance of *activations* carries what surface-feature variance does not | **Burstiness does it with perplexity, PAN with surface style, nobody with probe outputs.** The only route here untried by both the field and us | ~2 h GPU |
| **HH-6 · enter at the anomaly** | Entering at the anomaly beats entering at the whole artifact | **A flag flip, not a build** — `bounded_v6`'s stage zero exists and has never been live. **Temper the expectation: the simulation says ordering changes the answer by exactly zero** | ~1 h |
| **HH-14 · interest ratings** ★ | Reader-reported interest correlates with unrecovered decisions | **An hour of his time, and it turns the one channel that has beaten every measure we own into data.** It also adjudicates between his account and processing-fluency, which predict opposite correlations | his hour |
| **HH-16 · effective complexity** | "Ordered but unexplained" is effective complexity rather than entropy | Operationalise and check it is not just entropy | ~1 h |
| **HH-17 · polish against effort** | The polish–effort correlation is strong in human corpora and near zero in generated ones | **Blocked on an effort proxy, and automaticity makes effort unobservable by construction** — the same fact that puts values in the residue. Any proxy needs its own defence first | design first |
| **G67 · the teacher assumption on generated text** | Readers grant intention-to-help to generated text, and that is why it misleads | **A claim about readers, not models.** Different from the polish–effort account, and the two predict different things when provenance is disclosed | ~2 h |

## Next up — 2026-08-07, from the specification-recovery result

**The measure that just passed recovers how much specification a prompt carried, against 48
topic-matched decoys. Win rate went 52.5% → 66.3% → 91.7% as the manipulation went from ten short
specifications to sixty.** These follow directly from it.

| | the claim | the test | cost |
|---|---|---|---|
| **G68 · where does human text sit on that scale?** ★ | Human artifacts should behave like a very high rung — a person writes under an enormous implicit specification | **The direct measure cannot run**: it needs a known specification and human text has none. **The version that does run inverts it.** Instead of recovering a *given* specification, generate N candidate specifications for an artifact and measure **how sharply the artifact discriminates among them** — dense intent should separate candidates cleanly, thin intent should not. **Calibrate on the ladder first**, where the answer is known: if the candidate-generation version reproduces 52.5 → 66.3 → 91.7, it is measuring the same thing and can be pointed at human text. **Without that calibration step the human number means nothing** | ~4 h |
| **G69 · does the intent signal move deeper as rung rises?** | *"As intention increases, later layers have to be used to extract it."* Strongest layer was 14, 19, 23 across three ladders of increasing strength | **Between-ladder is confounded three ways.** Ask it *within* one corpus: split by rung and find where the signal peaks for each. **Running now** | free |
| **G33 · late coherence against goal clarity** | Late-layer coherence should rise with rung; middle-layer should not | Pre-registered and the depth sweep has been emitting the ingredients all along. **Running now** | free |
| **G70 · bits recovered on the no-maker corpus** | The specification-recovery measure should return **nothing** where there is no maker | **The control that the layer correlation passed and this measure has never been given.** Until it runs, the specification-recovery result has one fewer control than the measure beside it | ~30 min |
| **PD-33 · do the accounts of machine-text unease dissociate?** | Broken polish–effort, flattened intent, missing translation and wrong shape may be four views of one latent cause — **missing mid-level affective primitives** | **If any one can be manipulated without moving the others, they are not one thing.** The cheapest arm is translation, because translation structure is countable | design first |

| **G70b · no-maker control for specification recovery** ★ | The bits measure should return **nothing** on text with no maker | **The strongest new result has one fewer control than the measure beside it.** The layer correlation was DEAD on no-maker in 11 of 11 families; specification recovery has never been run there. **Queued** | ~30 min |
| **G71 · why does gpt2-large fail everywhere?** | The per-layer correlation is DEAD on all three ladders in gpt2-large while smaller models survive | **Failures cluster by family, not by scale.** Points at tokenizer or training data rather than capacity. Cheap diagnostic: does gpt2-large also fail the affect-direction fit that everything else passes? | ~1 h |

| **G72 · why does the middle not move?** ★ | Coherence falls with rung at early and late depths and **does not move in the middle**, replicated across three ladders. Is that the noisy middle the architecture predicts, or an insensitivity of the coherence measure at that depth? | **Discriminate with a positive control**: construct a manipulation the middle *must* respond to and check the measure detects it there. If it does, the null is real and it is a dissociation in the load-bearing band | ~2 h |

## The void audit — 2026-08-07

**Every result recorded VOID or INCONCLUSIVE, re-assessed against what we now hold that we did not
then: eleven model families, a length-controlled extreme ladder, a no-maker corpus, 86 humans × 3
drafts, six years of topic-controlled style-change data, 43k human-labelled emotion comments, and a
GPU.**

| | what was voided | why it died | re-runnable now? |
|---|---|---|---|
| **V1 · the founding question** ★ | *Some measure ranks five rungs of specified intent* | Voided on its own pre-registered ceiling: rung and length correlate at 0.40 against a 0.40 limit | **YES, and the ceiling itself was wrong.** The 0.40 is a *rank* correlation over a **4.2% length spread** — 58 words on a 1,400-word median. Ladder 3 halves the spread to 1.9% and the rank correlation is unchanged at 0.414, because Spearman is scale-free. **A criterion that cannot tell a 4% difference from a confound.** Re-scoring now |
| **V2 · reader displacement varies more for machines** | Three artifacts | pure sample size | **YES, trivially.** 150 ladder artifacts, 36 no-maker, 86 authors × 3 drafts |
| **V3 · a reader refuses differently on human and machine text** | Pass condition had a **50% false-positive rate by arithmetic** | broken threshold, not broken design | **YES**, with a pre-registered threshold and power computed before the run |
| **V4 · function words separate maker states** | 38% power | short texts — at 380 words the pronoun rate gives **five tokens**, and the statistic divides by a variance made of Poisson noise on five counts | **YES, on longer text.** The 34-book corpus is 22M characters; ladder artifacts are 1,400 words. **D-0's own power analysis says exactly what to fix** |
| **V5 · purpose × affect separability** (D-0) | Same cause as V4 — the design could not have detected what it looked for at that text length | | **YES, same fix** |
| **V6 · affect-isolated decomposition** | Shuffling the labels changed the count not at all — found Reddit text confounds topic with emotion | the isolation step never ran | **YES, with topic-controlled generation** rather than found text |
| **V7 · half A contains more recoverable method than half B** (Gate 3) | Statistic reads a large positive where truth is zero; **and 76 features separate the halves**, so almost any measure would | corpus is confounded and has been read too many times | **NO on that corpus.** Needs a fresh one, and the question should be re-specified as singularity of terminal value |
| **V8 · the values vertex carries no information** | A single-artifact model cannot represent a quantity defined only across artifacts | | **NO — a build, not a re-run.** Scoped in `../sim/` |

**Six of eight are re-runnable, and two of those were killed by a criterion rather than by a result.**

| | the run | cost |
|---|---|---|
| **V1** | re-score the extreme ladder now that the ceiling is understood | running |
| **V2** | displacement variance at n = 150 rather than n = 3 | ~1 h |
| **V3** | refusal with a threshold whose false-positive rate is computed first | ~1 h |
| **V4 / V5** | function-word separability on book-length text | ~2 h |
| **V6** | affect decomposition on topic-controlled generated stories | ~4 h |
| **G102 · prior-art sweep before claiming originality** ★ | *"No one else is tracking layer ratio with respect to intent"* — his call, 2026-08-08 | Inline literature sweep (no agents needed): layer-wise affect ratio vs prompt specification, probing-by-depth vs instruction density. **Owed before any public claim** | ~1 h inline |

## Corpus sourcing — 2026-08-07, the one-maker-many-kinds problem

**Three hypotheses are blocked on the same corpus and it turns out to be genuinely rare rather than
merely unfound.** The cross-genre authorship literature describes its own data as *"scarce and very
limited in size"*, and most corpora carrying a "cross-domain" label are cross-**topic** underneath.

| | corpus | kinds | makers | why it may not work |
|---|---|---|---|---|
| **C-30** | **CROSSNEWS** | bylined news articles vs the same journalist's social posts | 53 with both in a 40k-row sample; hundreds in full | **SURVEYED, and the survey is the problem.** Articles are fine — median **883 words**, 42% over 1,000. **Posts have a median of 17 words and *none* reach 300.** Usable only as pseudo-documents |
| **C-31** | **Guardian cross-genre** | opinion articles vs **book reviews**, both ~1,200 words | **13 at best, 5 in the accessible copy** | Under the 20-maker minimum, copyrighted, no clear licence. **But the kinds are comparable in form**, which CROSSNEWS's are not |
| **C-32** | **CMCC** | blog · email · essay · chat · discussion · interview, crossed with 6 fixed topics | 21 | **Exactly our design** — a deliberately crossed maker × kind matrix. **No download page found**; request-only until proven otherwise. Chat and email are short |
| **C-33** | longitudinal multi-domain, ~412 authors × {abstracts, blogs, news} | three real kinds | 412 | **Unverified** — repo referenced but not opened, identity method and licence unknown, abstracts likely under 300 words |
| — | PAN cross-domain attribution (2018–2021) | **DEAD END** | — | *"Cross-domain" means cross-fandom.* Every artifact is fan fiction — same genre, register, audience, purpose. **It varies topic, not kind**, which is the axis the whole hypothesis turns on |

**The objection that applies to CROSSNEWS and not to the Guardian, and it is the important one.** A
17-word post and an 883-word article do not differ by *kind* in the sense we need — **they differ by
medium, and length alone separates them completely.** That is the Gate 3 trap: two halves so broadly
different that almost any measure separates them, so separating them is never evidence. **A kind
contrast is only informative when the kinds are comparable in form.**

| | the job | cost |
|---|---|---|
| **C-30a** | Re-survey CROSSNEWS at 500k rows — 40k rows is 2.7% of it, so a maker's second genre may simply not have appeared | ~20 min |
| **C-30b** | If pseudo-documents are accepted, **state what changes**: a concatenation of a person's posts is a *sample of their writing in a register*, not a thing they made. **Legitimate for the relation test, illegitimate for anything within-artifact** | design |
| **C-31a** | Chase the full Guardian corpus, 13 authors. **Fewer makers but a fairer kind contrast** — and it may be the better test despite the size | sourcing |
| **C-32a** | CMCC remains request-only and unpursued (author contact is off the table, his ruling 2026-08-14) | closed |

| **G76 · the function-word induction control** ★ | Classifying rung from function words may be reading style the prompt **induced** rather than a maker state | **done (L94), built in the fair form after the L93 audit found this row's old spec described the dose-eating construction L22 killed.** SURVIVES on held-out and extreme (0.44 vs 0.20 chance after within-rung identity removal, perm p < 0.005, raw baselines reproducing L16), COLLAPSES on the first ladder (weakest dose, n = 50). The old form killed all three corpora (0.13 to 0.17), measured as the demonstration | closed |
| **G77 · refusal with a threshold that can fail** | A reader refuses differently on human and machine text | **The re-run used the threshold that voided it.** Three of five components under a null of no difference is five coin flips: P(at least 3) = 0.5 exactly, so PASS at exactly 3 is the modal outcome of nothing. **Replace with a permutation test and report the false-positive rate before the verdict** | ~1 h |
| **G78 · which subtraction is correct?** | Partialling out is linear and assumes the nuisance is additive and separable; the habit-shadow objection says it is neither. IRL constrains the reward class instead of regressing out a component | **Plant a known residual under a known nuisance in the simulation and see which recovery method finds it.** Settles the vocabulary before either is committed to | sim |

## Harvested 2026-08-07 from archaeology and connoisseurship — techniques, not citations

**Three subagents. Most of these are cheap because the thinking is already done.**

| | the technique | the test | cost |
|---|---|---|---|
| **G85** | **The intent ladder already IS the Nonaka intention-elicitation protocol** — specify first, produce, measure recovery. Validated on stone since 2010 | **Nothing to build.** What to take is the calibration ceiling: **expert knappers reach R² = 0.655 against their own stated intention.** Re-read every null in the project against that ceiling rather than against perfect recovery | free |
| **G86** | **A mechanical null model** — model what the medium forces, call only the residual a choice | The one thing chaîne opératoire never built, and **the same subtraction the depth redefinition needs**, with the nuisance derived rather than assumed. For text: predict the artifact from genre + length + prompt alone, treat the residual as candidate choice | ~3 h |
| **G80** | **Reserve versus overpaint** — did the structure make room for a claim, or was it inserted into a structure that does not accommodate it | **Computable on one static text with no version history.** Separates load-bearing commitments from bolted-on ones | ~2 h |
| **G81** | **Self-revision is homogeneous and continuous; an imposed hand is lumpy and discrete** | Author vs editor vs co-author vs tool. **Distributional, not semantic** — and the discriminator this project needs most | ~2 h |
| **G79** | **The four-part Morellian admissibility filter**, criterion 4 especially | **It predicts where habit is switched off.** Elegant variation suppresses individual signal exactly where our measures currently see most variety | ~2 h |
| **G88** | **Error handling rather than error rate** | Novices thrash on a ruined surface; experts abandon or repair. **Measures metacognition, not execution** | ~2 h |
| **G89** | **Rigidity under perturbation as the novice signature** | An **active probe**: change genre, length or audience and measure whether quality is preserved | ~3 h |
| **G87** | **Partition features by visibility and acquisition age** | Low-visibility early-acquired features track deep identity; visible ones track situational identity | ~2 h |
| **G92** | **Inter-annotator agreement before any extraction is believed**, and per-feature accuracy rather than an aggregate | **Their aggregate of 72.6% concealed a 43.3% category, worse than chance.** And a published study found that agreeing definitions in advance was *not sufficient* | ~2 h |
| **G93** | **Does a reliability filter remove signal?** ★ | The 2026 rebuttal says selecting attributes *for* replicability privileges the trivially measurable over the behaviourally meaningful. **Our 342-feature funnel drops features that fail filters** — if the meaningful ones are systematically the hard ones, the funnel removes signal and looks like rigour | ~2 h |
| **G94** | **Run our own Taramsa test** ★ | They reconstructed sequences by the standard method at a site where refits gave the truth, and **the method invented a production stage that never happened.** Our analogue ran on the ladder with join-checked reconstructed truth | **DONE (L143): one invention in ten unspecified texts under the honest none-option format; real specs recovered 12 points above the word-echo bar, diluting with dose (0.77 at three specs to 0.44 at ten). The fabrication risk is format-bound (contrast L139's 0.69 yes/no over-credit)** |
| **G83** | **Adopt the graded attribution vocabulary** | Three axes at once, and **"workshop of" is the mixed human-and-tool provenance category we would not have invented** | free |
| **G90** | **Report separability as a cross-validated confusion matrix** | *"These two processes separate at 80% on this feature set"*, never *"we can read the maker"* | convention |
| **G95** | **Report composition, not labels** | Tostevin's wine analogy: a château name cannot tell you how similar two wines are; a *cépage* can. **"40% attractiveness-directed, 25% teaching-directed, 35% residual" is arguable; "high depth" is a label** | convention |

| **G96 · the expedient-intent test** ★ | Have the **same maker** produce the same artifact carefully and hurriedly, and ask whether the measure separates hurried-expert from genuine-novice | **The single largest untested confound in the archaeology literature, unrun by anyone in any medium** — they cannot commission a Palaeolithic knapper and we can commission a writer. **Our README already claims "firing on hurried human work is the measurement working," and that claim has never been tested** | ~3 h + writers |
| **G97 · maker as a random effect** | Every skill study compares group means across individuals, pseudo-replicating artifacts within makers. **The one study that used hierarchical models found skill effects mostly vanish** | Re-analyse our within-maker results with maker as a random effect. **If our effects vanish too, we have been measuring individuals rather than the quantity** | ~1 h |
| **G98 · are our errors clustered?** | Overshoots in a 100-core sequence *"recurred in bursts separated by runs of properly constrained strikes"* — **clustered, not Poisson** | Check the dispersion of any error-like feature we extract. **An error rate on a small sample measures which burst you sampled** | ~1 h |

| **G105 · a coherence statistic that can measure agreement** | The audit (L26) proved the current one cannot: globally centred directions sum to zero, so 8-way agreement is geometrically impossible and the recorded number is an arbitrary-axis projection, sign-unstable across refits | Mean pairwise sign agreement of projections onto uncentred per-concept contrasts — **with a known-answer validation on synthetic agreeing/disagreeing data before any real read**; then re-adjudicate G33 and the depth-sweep middle verdicts | **done, all eight families (L47): every gate passes; 0 of 24 cells rise with dose, agreement FALLS in the Qwen family — G33 rejected in direction. Sub-chance baseline observation unclaimed** |
| **G106 · rebuild the affect-count instrument** | Four independent defects (L26): participation-ratio correction misattributed and scale-fragile, bi-cross-validation pinned at its cap in 135/138 fits, shuffle gate arithmetically unpassable, VAD reference written from memory (18/28 entries off by >0.1) | Column-standardise before the SVD; implement the cited estimator or drop the citation; raise the cap and treat boundary argmin as no-selection; gate on a statistic with a known direction under label destruction; **vendor the real NRC-VAD with a checksum** | design first |
| **G107 · a permutation null for the no-maker control** | 5 of 11 no-maker runs fire under the computable rule (L26); the flagship's fires [5,7,13,17,21] overlap its held-out-ladder survivors 3-of-5, and layer 21 fires everywhere including maker-less text | Save per-artifact signal rows in `run_layer_correlation` (done), then a label-permutation null for the joint rule and the overlap — decides clustered luck vs a real label leak | **queued for the night** |
| **HH-3 · activation-series variance, queued at last** | The §1 heuristic's untried operationalisation — within-artifact variance of *probe activations*, which burstiness (perplexity) and PAN (surface style) never did | The reader's early/late ratio per window as a positional series; books-vs-machine at matched series length (PD-3's flat-machine signature) plus rung-vs-variance on two ladders | **queued for the night** |
| **G122 · causal patching of the affect geometry** | The build's decisive gate: everything decodable so far could be a correlate. *"Move from decoding to causation"* | Patch, erase, or steer the recovered subspace and measure whether goal/process inference changes while lexical and topical performance hold; causal-abstraction methods are the standard | design ~1 day |
| **G123 · the unique error fingerprint** | The missing-middle prediction risks collapsing into generic emotion probing without its distinctive signature | Hold surface affect, category, goal, and expertise constant while varying the latent drive explanation; ask whether drive ambiguity specifically produces the predicted goal-inference failure | design ~1 day |
| **G124 · align families by computational events, not depth fractions** | Fixed block addresses have failed to transfer everywhere we looked; the 7%/76% loci are Qwen-shaped | Representation change-points or CKA across families, then re-test the flagship at aligned stages — may explain the sign map (G112's best route) | **done (L45): the events are portable — early locus lands in the first sixth in 4 of 5 families, late at 62–83% in all 5; SmolLM2 refuses the alignment (28% deep), the sign-map exception again** |
| **G128 · a permutation null for the event alignment** | The alignment's best-match assignment (L45) has no null: with 25–37 blocks per family, some lawful-looking landing pattern may fall out of any smooth similarity matrix | Recompute the block-matching on label-shuffled and phase-scrambled text pairings; the landing depths should scatter if the alignment is real and persist if it is an artifact of smoothness | ~1 h, cached activations |
| **G125 · commissioned human work for the absent-drive signature** | S-14 is proven as method in simulation (V11: perfect under commission, compliance collapses to 0.5); only real work can establish the real signature | Same brief, repeated makers, multiple artifacts, independent records of process and motivation — his side for sourcing, ours for design | blocked on people |
| **G126 · per-block contribution and d′ readouts** | The analogue research names what our profiles should have been measuring: the per-block *write* (what BOLD actually tracks), the signed *affect work* that telescopes to the final projection, and per-block d′ as the honest signal-to-noise | Add the three quantities to the readout path (cached states make two of them nearly free), plus the rogue-dimension QC alarm; then re-read the address-umbrella claims in the new units | **done, all eight families (L48): QC clean everywhere; write/work geography maker-blind and input-edge-concentrated universally; d′ placement lawless — Qwen early at both sizes, other families scatter with size reversing direction; home-family selection caution filed in the entry** |
| **G127 · the pooling falsifier** | Extraction choice systematically biases layer-wise conclusions (Hadidi 2025), and every profile we own mean-pools | Re-run the flagship ratio and one per-block map under last-token and max pooling; if the early/late shape moves, every address claim inherits the caveat | **SPLIT, ratio half WITHDRAWN (L44 corrected by L93): the profile geography is pooling-invariant (r ≥ 0.98, same peak block) and stands; the ratio cells were computed on rungs 0–1 only (rung-ordered manifest truncated at 40 items) and are void by selection. v2 rerun queued: full n=100, rung composition recorded, mean-arm reproduce-gate before the other poolings are read** |
| **E7b · follower-corpus sourcing detail** *(moved from the triple inference §10 per the reorganisation — the theory file keeps the blocking rows G65/G66 only)* | The value-ground-truth design: many makers deliberately aligned to one declared value set, read through deep followers, adherence graded | Sourcing candidates: religious traditions, political manifestos, professional codes, open-source governance, movement writing. Construction: hold topic constant (same practical question — money, work, family, obligation, death — answered from within different traditions); founding work analysed separately from followers; degree-of-adherence is the label. Known confounds to design against: canon-formation selection, translation, era; "declared ≠ held" is tolerable because the needed label is what an artifact was made *under* | sourcing, then ~3 h |
| **G43-first · non-affective control subspaces** | The early break gates how every mapping claim reads; if syntax/topic/frequency/position subspaces all break at the same place, the boundary is the input adapter's edge | Measure four non-affective subspaces identically to the affect one, all eleven families, saved matrices make it CPU | **done, 11/11 (L49): ADAPTER-EDGE unanimous — every subspace type snaps at the affect subspace's block in every family. The break carries no mapping information; the gate resolved deflationary** |
| **G108 · a wider specification pool** | The extreme ladder's decoys exhaust at rungs 30/60 (L26): half the corpus is not the contest its chance figure claims | A 120-spec pool so the complement supplies distinct decoys at every rung; regenerate the extreme contests | corpus build |
| **G109 · stale-reference sweep** | L26 unverified tier: dead filenames (THE_TRIANGLE, THREE_LAYERS), wrong anchors (§8c→§7 etc.), TR-13 orphaned by the rename, `ideate.py` hard-codes an archived path | One pass over the fleet's line list (task output, docs-data findings); fix `ideate.py` before it is ever queued | ~1 h |
| **G110 · TODO hygiene pass** | L26: stale "running now" rows finished days ago, duplicate identifiers (E1=G56, E6≈G48, interest-ratings ×3), done work still listed as owed | Mark done rows with their L-numbers, collapse duplicates to one identifier each | ~30 min |
| **G111 · subspace basis rank fix** | L26 unverified tier: centred 8-vector span is rank 7, so the 8th QR column is junk diluting every alignment ~1/8, and the null band is mismatched to the distant-pairs statistic | Truncate to the nonzero-R rank, centre the null construction identically, match the null statistic to distant pairs; **verdicts stand at current margins** — this is for the numbers, not the conclusion | **done, 11/11 (L50): DEPTH everywhere, no verdict flips — adjacent 0.78–0.96, distant 0.21–0.42, null ~0.05. The v1 rank caveat is retired** |
