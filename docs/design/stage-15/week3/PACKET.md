# Sounding Line, Stage 15, week 3 (25 October to 1 November): process, pieces and ends

> *Checked three times by an independent reviewer and fixed after each round. The third round's sign fix and minor fixes follow the reviewer's own recommendations.*


*Spec sheet for the Sounding Line agent. It runs from handoff to Sunday 1 November, 22:00 PST (2026-11-02T06:00Z), and supersedes the 25 October "wing" draft. Every decision is made here. Return to the curator only on the triggers in section 10.*

**What this week is for.** Last week's queue ran dry for about 40 hours. This packet is built so it can't happen again:
- a ranked tree of thirty-seven cards, eighteen of them ready at handoff (GEN1.ic runs inside WA0);
- automatic healing passes and follow-ups;
- lifted cost holds on the backlog;
- a Gear 3 campaign within $10, if the curator approves it at handoff;
- real preference data held since 14 October and never modelled.

**The curator's working model** (appendices A and B) says:
- a person reuses pieces (preset action sequences with expected outcomes) inside a process pyramid (essay, paragraph, sentence, word);
- most production runs on autopilot;
- where the writer departs from the autopilot, attention went there, and the targets of attention reveal the higher-order goals she serves;
- emotion systems leave signatures that reveal wants ("anger only fires when you want something");
- trust rests on an accurate, current projection of someone's transition map and how similar their ends are to yours.

The tree tests each of these on real records.

## 0. How to run this

### 0.1 Window

- This packet opens a new window at handoff. It supersedes tonight's 20:00 close and 22:00 restore; if `transition_only` is already restored, clear it at handoff.
- Open the window in a new runtime version. Daylight saving ends on 1 November, so write both times in UTC:
  - no new starts after Sunday 1 November, 20:00 PST (2026-11-02T04:00Z);
  - drain by 22:00 PST (2026-11-02T06:00Z), then restore `transition_only: true`.

### 0.2 Rules in force

- **Section 2 of the 17 October packet** (`PACKET_20261017_PUBLIC.md`), including:
  - row 2's counted CPU lease: N = 4 slots with at least 12 logical processors, 3 with 8 to 11, 2 below that; at most 2 numerical threads per worker;
  - row 3: up to three card builders at once;
  - row 9 (one retry), as amended by section 0.3 B;
  - row 10: 3 agent-hours per card, plus one 3-hour extension for marginal or positive results;
  - row 12: the pilot rule.
- **The 18 October mid-run errata:**
  - rules 1, 3 and 6 stay in force;
  - rule 2 stays: environmental interruptions resume as often as the cause recurs. Its "exactly one retry" for engineering failures is amended by section 0.3 B;
  - rule 4 stays for outcome-shuffle controls only, with this packet's seed. Its 0.25-SD flag doesn't apply to identification references;
  - rule 5 stays for every writer-label or session-reassignment control except identification references, which section 0.4 governs;
  - rule 7 is replaced by section 5.
- **Standing decisions S1 to S7** (18 October week packet, section 1). S6's "Wednesday freeze" reads "this window's no-new-start time".
- **The stone rules stay:**
  - Gear 3 per-use approval, and never past $10 without the curator's detailed final approval, enforced in code;
  - material spend only behind positive results (ruling 7), read as on 17 October: it governs extensions past $10, so this week's $10 tranche is consistent with it;
  - hash-locked files;
  - no author contact;
  - privacy;
  - every measure ships with a null that can fail it;
  - every result is descriptive.

### 0.3 Standing amendments (permanent)

These outlast this window. Write them at handoff, in a section headed "Standing amendments, 25 October", into `AGENTS.md` (which `CLAUDE.md` points to) and `.agents/skills/grind/SKILL.md` (which `.claude/skills/grind/SKILL.md` points to). They answer the curator's 25 October request: he shouldn't have to ask for follow-ups or healing passes, and corrections should stop eroding his trust in the results.

**A. Never idle.**
- Keep at least two ready cards per CPU slot.
- When the ready queue drops below that, building the next cards comes before routine events. Failures and triggers are acknowledged first.
- Sources, in order: this packet's tree, the follow-ups under C, section 6's backlog.
- Report idle slot-hours in every digest. Any idle hour while commissioned work remains is a defect, recorded in OPS_LOG with its cause.

**B. Healing passes run automatically.** This amends the 17 October packet's row 9 and errata rule 2's "exactly one retry" for engineering failures.
- **What heals.** An engineering failure: a crash, a code bug, a dependency or join error, a failed known-answer check (an instrument failure, not a result), or non-convergence that a repair leaving the estimand unchanged can fix (starting values, optimiser settings, iterations). A repair that changes the model is a `.h1` card (step 3).
- **What doesn't:**
  - an environmental interruption, as rule 2 defines it (a memory or temperature guard, an operating-system refusal, sleep, power loss or reboot, disk exhaustion): resume from validated checkpoints as rule 2 says, as often as the cause recurs. It uses up no healing attempt;
  - a data defect: S3's canonical successor;
  - a cost overrun: S4 first. If a cheaper exact implementation is then needed, register it under step 3;
  - a scientific gate that fails (a null, a negative, a pass rule not met): that is a result. Record it and route it under C; never heal it.
- **Steps:**
  1. Diagnose the cause. Record one line in OPS_LOG with its class: engineering or instrument.
  2. Repair and rerun, with inputs, comparators, seeds and contrast unchanged. Up to two healing attempts per card. Shared passes keep row 10's count: at most 2 attempts in all.
  3. If the repair has to change the design (a new estimator, a reduced grid, a cheaper exact implementation), register it as a new card with the suffix `.h1`, frozen before it runs, and dispatch it at the parent's rank.
  4. After two failed healing attempts, record the card as invalid with its reason, and dispatch the next.

**C. Follow-ups run automatically.** After each landing, register follow-ups from this menu, frozen before their outcomes, without waiting to be asked:

| Parent's state | Follow-ups registered at once (at most three) |
|---|---|
| Positive or marginal | (a) specification curve `.s`; (d) a mechanism probe `.m`, the smallest test that would say why; then (c) a second dataset `.r` where one is already in hand, otherwise (b) a second pipeline `.p` |
| Null | (e) an instrument check `.ic`: could this pipeline have seen the effect at the size that matters (a planted calibration, or a power curve over effect size)? Until (e) lands, the null is reported as "not detected; sensitivity untested", never as a negative |
| Unsupported (too few events to test) | None. Recorded apart from nulls, with the support count |
| Negative | (a), plus the reversal's mechanism probe `.m` |
| Invalid | B's healing passes |
| Anything the owner finds surprising | One exploratory card `.x`, labelled exploratory, registered only while the parent has fewer than three follow-ups |

- **Caps.**
  - Each follow-up is capped at half its parent's ceiling.
  - At most three follow-ups per parent per week, the exploratory card included.
  - **One generation only.** A follow-up registers no follow-ups of its own; its result goes to the digest.
  - **No locked holdout is spent automatically.** `.r` never reads a Tier 4 holdout (Padmakumar & He's logs, FX1's folds).
  - Follow-ups rank below this packet's cards, except that an instrument check `.ic` jumps ahead of any card that depends on the same instrument.
- **Suffixes.** `.s`, `.p` and `.r` keep their 17 October meanings. `.m`, `.ic` and `.x` are new. `.c` keeps its 17 October meaning (planted calibration in V4's worlds) and isn't used by this menu.
- **Rationale.** Each follow-up carries one line on why, written by the owner. The curator may veto at the digest; nothing waits for him.

**D. A claim ledger.** The workflow fix for corrections.
- **Start a Stage 15 claim ledger modelled on Stage 4's and 5's:** `results/phase_2_4_stage_15/CLAIM_LEDGER.json`, rendered as `CLAIMS.md`. Each row keeps their fields (`card`, `estimand`, `outcome`, `strongest_rival`, `scope`, `pursuit`, `warrant`, `public_wording`, `detail`, `at`) and adds:
  - **id:** the FINDINGS id where one exists (for example `S15-EV1-PAUSES-V1`), otherwise `S15-<card>-<n>`, so companion repositories can cite rows;
  - **estimate,** with its interval;
  - **control status:** passes, biased reference, invalid, untested;
  - **scope qualifiers:** corpus, population, real or constructed, descriptive or confirmatory;
  - **source file and line;**
  - **supersedes / superseded by;**
  - **correction class** when changed: arithmetic, data, instrument, control, scope, attribution, citation or wording.
- **Allowed verbs are fixed by status:**
  - passing controls → "supports";
  - biased or invalid controls → "descriptive only";
  - constructed → "in constructed worlds";
  - a null with untested sensitivity → "not detected";
  - too few events → "unsupported".
- **Anything sent to the curator** quotes claims by ledger id with their public wording. That covers digests, talk pages and returns to companion repositories. A paraphrase must cite the id.
- **Corrections come first in every digest,** with their class. A superseded row stays, marked.
- **Backfill** the ledger at handoff for every claim in the 17 October packet's section 1, the 18 October week packet's section 0 state bullets and this packet's section 1, and for EV1 to EV4, PMAP, GEN1, DR1, NP1, D24 and D30.

### 0.4 Identification controls

- **What this replaces,** for identification references only: rule 5's same-row fake-writer reference, and the chance-centred quarter-SD check that the EV3, GEN1 and PMAP designs applied to fake references (an extension of rule 4's flag). Rule 5 still governs every other reassignment control: history, classification and offset controls such as D30's and D33's, and recurrence references such as EV2's.
- **Why.** A chance-centred check assumes the reference's null sits at chance. The references built so far don't sit there:
  - Ghost derived (V24 gallery follow-up) that a reference excluding the true identity has expected accuracy (1 − accuracy)/(N − 1), below chance whenever real accuracy beats chance.
  - EV3's final-document reference matches that: 0.0143 observed, 0.0141 predicted. Its typed-fragment variant, built from the same 200 reassignments, doesn't: a fake mean of 0.0300, against 0.0111 predicted and chance at 0.0222.
  - GEN1's rhythm fakes sit above chance at 100% real accuracy, where the construction predicts 0.
  - Most of PMAP's fake means sit above chance too (rhythm 0.034, against chance 0.022).
  - Ghost calls its result a methods warning, not a diagnosis of these controls. So this week doesn't diagnose each failure.
- **It replaces the rule with references whose nulls are computed:**
  - **Writer-label permutation.** Shuffle writer labels across sessions within prompt, rebuild every profile and recompute accuracy, at least 1,000 times. Report the null's mean, its 95% band and the one-sided p.
  - **Context-only reference.** Replace each session's features with its prompt's leave-writer-out mean, and run the same gallery. Real accuracy minus context-only accuracy is the person signal.
  - **Disjoint samples.** Keep PMAP's split: whole prompts alternate between halves in date order within each writer, so no writer's gallery and probe share a prompt or a session.
- **A pass needs both:** a permutation p below 0.05, and real minus context-only accuracy with its writer-cluster 95% interval above zero.
- **The same rule applies outside CoAuthor:** to annotators in Community Alignment and to raters in DICES, with "prompt" read as the item (CA0 sets a fallback if prompts aren't shared).

### 0.5 Defaults

Unless a card says otherwise:
- one primary contrast, with its direction;
- every measure ships with a null that can fail it;
- writer-cluster 95% intervals from 2,000 resamples;
- at least 200 within-writer permutations (seed 20261026);
- at least 1,000 writer-label permutations within prompt for reliability and identification nulls (seed 20261026);
- for reliability cards (PP4, WB3, WC3, WC4, WD1 and PR1's secondary), rule 5's own-minus-fake reads as real reliability minus the permutation mean, with a real-writer paired bootstrap, reported beside the permutation p;
- a known-answer check before production;
- descriptive probabilities only;
- choices come from P2's canonical choices, never the logged selection field, which names the wrong suggestion in about one selection in five (`SELECTED_OPTION_AUDIT_20261018`: 2,510 proven mismatches across 366 sessions).

### 0.6 Resources and pins

- **CPU:** the counted lease of section 0.2.
- **ToMpathy's run.** ToMpathy's TE4 runs its goal module on a CoAuthor sample this week (capped at 3 CPU-hours or 20 documents). The 18 October reservation for its lock expired, and no Sounding Line code reads the lock yet (`week_policy.py` reserves by time and receipt).
  - **The lock:** `results/.cpu-slots-20261017/tompathy-demo-prep.lock`, a JSON file holding `created_at` and `expires_at` in UTC. If this window's runtime renames the slot directory, the lease still checks this path. ToMpathy writes the lock when its run starts, with `expires_at` at the run's projected end and no later than Sunday 1 November, 20:00 PST (2026-11-02T04:00Z). A lock is treated as expiring at most 6 hours after its `created_at`, whatever it says.
  - **Starting:** ToMpathy starts its run only when a counted slot is free. If its lock appears while every slot is busy, the next slot to free up stays free.
  - **While a valid lock exists:** keep one counted slot free, and start a card only if at least 8 GiB of memory stay free after its projected peak.
  - **Stale locks:** a lock past its `expires_at`, or without one, is ignored and logged in OPS_LOG. After 2026-11-02T04:00Z every lock is ignored.
  - **The check:** add it to the lease, with tests for a valid, an expired and an absent lock.
- **GPU:** none is asked. The P1 suggestion pass stays held under its guard. The curator's own GPU use takes precedence.
- **Paid work:** section 5's Gear 3 campaign only, if the curator approves it at handoff.
- **Network:** section 4's intakes only, under `docs/design/stage-15/DATA_INTAKE.md`.
- **Pins:** ToMpathy at `certified-fit-1` (`5f3ad0a`) wherever the engine is used.
- **Privacy:**
  - Aggregate outputs only. No per-writer, per-annotator or per-rater profile leaves the repository, and identifiers stay hashed in every output.
  - Raw CoAuthor text goes to the Gear 3 provider only inside section 5's nodes, and only the material section 5 lists. It goes nowhere else.

## 1. State on 25 October, 05:30 PDT (`8779df833`)

| Item | State |
|---|---|
| EV1, departures and pauses | Positive, reference passes: words with higher engine departure follow longer pauses (+0.073 log-pause per page interquartile range of departure, interval +0.060 to +0.086), on surviving engine-scored words. Scoped route: "tested on human writing logs: flagged words came after longer pauses" |
| EV2, signatures | Positive, reference passes: signature phrases recur in the writer's other work, +1.38 per 10,000 words (interval 0.05 to 3.14). Scoped route: "recurs in the writer's other work" |
| GEN1, stories against arguments | No fiction advantage detected; sensitivity untested. Style identified 41.67% of writers from stories and 50.00% from arguments (10 and 12 of 24), difference −8.33 points [−20.83, 0.00]; rhythm 100% in both. The per-genre fake references failed their gates; the genre-difference references passed |
| DR1, reading order | Unresolved: the interval crosses zero, and its permutation and fake-writer controls never ran. Descriptively, on style, date order was slowest (3.59 sessions, against 1.79 random and 1.48 directed). On rhythm all three took about one session |
| NP1, probe-like events | 1.08 per session pooled (0.69 by writer): 429 accepted spans at least 80% deleted, 292 runs of three or more dismissals, 792 returns to a prompt |
| EV4 feature table | Delivered to both companion repositories on 23 October. Ghost has committed its copy; ToMpathy hasn't |
| D24 and D30 | D24 null. D30's crossed primary is unresolved; its paired comparisons found no advantage for her own history over reassigned (fake-writer) histories |
| SDT1 | Not built. Ghost N17's route passed, within its synthetic model |
| Held | P1 (5,087 MiB free, against a 7,424 MiB floor). The DR1 controls (2,832 of 7,200 seconds charged; a full run projects about 31,000), P7 and D33 (cost). P3's blind reference and classifier were never built |
| Data held, never modelled | Community Alignment (90,256 conversation rows from 3,603 annotators, CC-BY-4.0) and DICES-350 (123 raters × 350 conversations): downloaded and counted on 14 October, 20:47 PDT (2026-10-15T03:47Z), no outcome ever modelled |
| ScholaWrite, held since Phase 1 and analysed before | g177's process-aware 15-way intention ceiling: mean macro-F1 0.048 over projects, "label noise at this grain". Stage 9's leave-project-out baseline: gains over previous-transition rivals not established. Stage 10 (L386 to L389): a training-frequency prior beat every tested model in 27 of 30 ScholaWrite cells. L68 and L69: the shipped split is within-project, so near-duplicate states cross the train and test boundary |
| Idle | No research worker since GEN1 landed on 23 October, 13:53 |

## 2. The tree

Eight families. Dispatch follows section 2.9's single ranked list, up to N slots, as soon as gates allow. Each card names its family; family null counters run as on 17 October (six nulls in a row stop a family). Instruments don't count, and neither do unsupported cards.

### 2.1 Family I: instruments (ready at handoff)

**WA0. One control rule, applied backwards (instrument).**
- **Question.** Do the identification verdicts change under section 0.4's rule?
- **Rerun on the same inputs:**
  - PMAP's six complete channels (content stays unsupported);
  - EV3's habit vectors, for final documents and typed fragments;
  - GEN1's style and rhythm by genre (GEN1.ic adds the genre-difference test).
- **Add one page variant.** PMAP's style features read typed text, including words later deleted. Web pages carry final text instead. So also run PMAP's style features on final documents.
- **AI text.** CoAuthor's final documents include accepted AI text. For both final-document variants (EV3's habits and PMAP's style features), residualise each feature on the session's accepted-character share before the gallery. Report raw and residualised.
- **Report for each:**
  - accuracy;
  - the permutation null's mean, 95% band and p;
  - the context-only reference;
  - real minus context-only, with its interval;
  - whether the verdict changes.
- **Primary.** EV3's residualised final-document variant under both of section 0.4's tests: permutation p below 0.05, and real minus context-only above zero. Final documents are what ToMpathy has on a web page. Direction: above both.
- **Route.**
  - **ToMpathy can't residualise on a web page,** where the AI share is unknown. So a page badge needs the raw and the residualised variant to pass both tests.
  - **EV3's final-document variant passes, raw and residualised:** send ToMpathy the licence for a habit badge, with its figures. The typed-fragment variant is reported beside it and licenses nothing on its own.
  - **The final-document style variant passes, raw and residualised:** ToMpathy's style display (its B2) may quote it on web pages.
  - **A PMAP channel passes:** record it as passing for process records only. Rhythm stays limited to owner captures, under B2.
  - **A verdict changes:** a dated correction in FINDINGS and the claim ledger, keeping the original.
- **Cost.** At most 3 CPU-hours, GEN1.ic included.

**GEN1.ic. Could GEN1 have seen a genre difference? (instrument; runs inside WA0; ready at handoff)**
- **Why.** GEN1's per-genre fake-writer references failed their gates, so its null reads "not detected; sensitivity untested". This is its instrument check, before FIC1 reads GEN1 as anything.
- **The analytic answer, stated now.** With 24 writers, an exact two-sided McNemar test reaches 5% only with at least 6 discordant writers, all in one direction (2 × 0.5^6 = 0.031). GEN1's 10 against 12 rests on about 2 discordant writers. So no genre difference smaller than 25 points (6 of 24) could have reached significance. That is a floor, not a sensitivity: power at 25 points is at most about 0.58, and 80% power needs about 31 points even in the best case. GEN1 is recorded now as uninformative about differences below about 31 points.
- **Do.**
  - Take WA0's GEN1 rows: both genres' identification under section 0.4.
  - Test the genre difference (stories minus arguments) against genre labels swapped within writer, 1,000 times.
  - For FIC1's planning: a power curve over assumed per-genre accuracies (40% to 90%), holding the within-writer dependence between genres fixed at its estimated value. The discordance rate can't stay fixed across that grid, because a paired difference can't exceed the discordance.
- **Route.**
  - **The rebuilt references fail:** GEN1's identification isn't valid for genre comparisons at all; record it so.
  - **They pass, and the difference is significant:** report it in its direction. No fiction claim follows without FIC1 or FIC3.
  - **They pass, and it isn't:** "no genre difference detected; differences below about 31 points were undetectable".

**WA1. Were the personal adapters blind? (instrument)**
- **Why.**
  - The 18 October selected-option audit found 2,510 proven mismatches between the logged selection field and the suggestion actually inserted, about one selection in five. Stage 14's adapter receipts say their labels came from the "recorded selection"; WA1a first establishes whether that is the same field.
  - Whether their calibrated base readout was worse than uniform isn't filed in the repository. WA1a checks it.
- **Precondition.** The per-decision adapter likelihoods were retained. If not, mark the card blocked, list what was retained, and move on.
- **WA1a, labels.**
  - First establish which field the rounds' labels came from. If it isn't the logged selection field, say so, and WA1a reduces to the uniform comparison below.
  - Re-score the saved likelihoods against P2's canonical selected offers, the labels the D2, D14, D32 and D38 canonical successors use. Apply the rounds' own decision rule.
  - Report each model's calibrated base readout against uniform.
- **WA1b, power.**
  - The rounds' rule calls a cell promising only when the whole interval clears the margin. So a plant exactly at the margin is detected at most about 2.5% of the time, and one plant size can't answer the question.
  - Plant an advantage in every writer, raising each personal model's probability on the true choice by the amount that improves its half-Brier by 0.01, 0.02, 0.03 and 0.05.
  - At each size, apply the rounds' rule at their own sample sizes, 1,000 times (seed 20261026).
- **Primary.** The minimum detectable advantage: the smallest plant detected in at least 80% of runs. If none reaches 80%, report "more than 0.05". This is an instrument property; no direction is claimed.
- **Route.**
  - **Within twice the margin (0.02), and still null under corrected labels:** the nulls stand as "no personal advantage above [that size]".
  - **Above twice the margin:** record "personal adapters: underpowered at the useful margin; per-writer models untested on choices".
  - **Either way:** retraining adapters on a planted preference needs the GPU and stays deferred, recorded as the remaining test.
- **Cost.** At most 2 CPU-hours.

**P3c. Edit intents on the CPU (shared pass).**
- **Why.** P3 was never built, and D22, D4, PP4 and WD2 all want edit-intent labels.
- **The classifier.** `wanyu/IteraTeR-ROBERTA-Intention-Classifier` is RoBERTa-large (24 layers; its configuration, checked 25 October), with five labels: clarity, fluency, coherence, style and meaning-changed. It costs about three times a base model on the CPU.
- **Do:**
  - The owner labels 200 calibration edit pairs blind, against written criteria, and declares them agent-made.
  - Time the classifier on the first 1,000 edit pairs. If the full run projects under 4 CPU-hours, run it over every edit pair: accepted-then-edited suggestions, and typed spans later edited. Otherwise run it on a frozen random sample sized to 4 CPU-hours (seed 20261026), and record the sample.
  - With a sample, D22, D4, PP4 and WD2 restrict to labelled events and report the share labelled.
- **Gate.** κ of at least 0.6 on meaning-changed against not, against the agent labels.
  - **Passes:** its labels serve D22, D4, PP4 and WD2.
  - **Fails:** Gear 3's node P runs as second labeler (section 5). If both fail, PP4 and WD2 use meaning-changed against fluency from the deterministic split only.
- **Cost.** A 4-hour box, 2 attempts, CPU only.

### 2.2 Family PP: the process pyramid and attention

**Why this family leads.** The curator's product need isn't a values readout; it is:
- the ability to fill out a process pyramid from a record, like ToMpathy's process hierarchy pane;
- to mark divergences from it as candidate attention;
- to track current attention as following whatever higher-order process is active.

EV1 already supports the word-level version: words where the writer departed from the engine's reader came after longer pauses. This family climbs the pyramid.

**Rules for every timing card in this family** (from the keystroke-logging literature; section 9 explains why):
- use writer-typed text only;
- drop intervals that touch a suggestion event or a multi-character insert;
- residualise on the writer's within-word interval, which mostly indexes typing skill;
- control mechanical intervals: an indicator for an uppercase or punctuation next character, estimated from mid-sentence capitals and punctuation, since capitals and punctuation add keystrokes CoAuthor doesn't log;
- use writer and prompt random effects, with time on task and session order as covariates;
- analyse genres separately;
- model pauses as a mixture, never a fixed threshold. Roeser et al. (2025) modelled interkey intervals as a two-distribution mixture; D17 fitted three lognormal components, the third for very long gaps. "Hesitation probability" is the posterior of the middle (slow) component. The very long component is reported separately, as disengagement.

**PP1. Can CoAuthor's event timing see the pyramid? (instrument; ready at handoff)**
- **Why.**
  - Keystroke research treats pauses at different boundaries as different processes. In Medimorec & Risko's (2017) data, read in abstract, pauses at word boundaries tracked word frequency, and pauses at sentence boundaries tracked sentence length. Pre-word pauses are read as lexical retrieval, pre-sentence pauses as planning and rereading.
  - CoAuthor's timing is already characterised. 99.23% of typed characters are single-character insertions, and the minimum positive interval is 1 ms (TC). D17's mixture found the slowest component's weight stable within writer (ICC 0.724).
  - So a sentence-over-word gradient is close to certain, and partly mechanical. Passing PP1 is a low bar: it licenses the instrument, not a finding. Its informative outputs are the upper levels and the per-writer profiles.
- **Locations.** For every interval before a character insertion, classify where it falls:
  - within a word;
  - before a word;
  - before a sentence;
  - before a paragraph;
  - before a revision: a deletion, or a move away from the end of the text.
- **Primary.** Hesitation probability before a sentence minus before a word, with the mechanical indicator, with a writer-cluster interval. Direction: positive. The null is an interval that includes or falls below zero.
- **Also report:**
  - the slow component's duration by location;
  - paragraph against sentence, and before a revision against before a sentence;
  - each writer's pause-hierarchy profile (ratios between levels), with split-half reliability and identification under section 0.4.
- **Route.**
  - **The gradient holds:** the timing instrument sees the pyramid, and PP2, PP4, PP5, PP6 and PP7 run on CoAuthor.
  - **It fails:** stop timing claims on CoAuthor. The fallbacks run only what their structure allows:
    - on ScholaWrite (author IDs are project-scoped, and its terms forbid identification): PP2's within-writer contrast only. PP4's primary compares writers, which ten project-scoped IDs on five papers can't support;
    - on KLiCKe, if intaken (one session per writer): PP2 only;
    - PP5 (ii) runs on neither.
- **Cost.** At most 1 CPU-hour.

**PP2. Does divergence from the generator mark attention above the word? (hypothesis test; after PP1)**
- **Unit.** The sentence.
- **Divergence**, reported separately:
  - (i) the mean engine departure of the sentence's content words, from EV1's pinned pipeline. EV1's departures exist only for surviving engine-scored words (44,494 of 78,602), so this covers sentences that survived to the final document. Report that selection;
  - (ii) the sentence's semantic novelty: one minus the cosine between its MiniLM embedding and the mean of the three sentences before it.
  
  Flag words that appeared in a suggestion shown in the last two minutes. Language-model surprisal is PP7.
- **Attention:**
  - the hesitation probability before the sentence;
  - revisions inside the sentence before it ends;
  - later "second looks" at it (PP4's definition).
- **Primary.** The within-session slope of pre-sentence hesitation on sentence departure (i), writer-clustered, against departure permuted within session. Direction: positive.
- **Also report:**
  - novelty (ii);
  - the two other attention measures.
- **Cost.** At most 2 CPU-hours.

**PP7. Surprisal against pauses in free composition (hypothesis test; after PP1 and a cost probe)**
- **Why it matters beyond the engine.** The literature pass found no peer-reviewed test of language-model surprisal against pauses in free typed composition, though its search ran out partway; the evidence comes from speech and copy typing. EV1 and D33 already model word-onset pauses with population surprise as a covariate. This card asks what a language model's own surprisal adds.
- **Model.** GPT-2 medium, as pinned for P7. P7's CPU extrapolation for the full corpus was about 4 hours, so PP7 runs on a frozen random sample of sessions (seed 20261026), sized by a one-hour cost probe to fit its ceiling. P7's cost hold doesn't cover this sample.
- **Word surprisal.** P7's exact word probability is unadmitted; only its per-token losses were validated. GPT-2's tokenizer marks word starts, so word surprisal follows Pimentel & Meister (2024): the summed surprisal of the word's subword tokens, plus the next token's word-start term, minus the word-start term at the word's own onset, all from the same forward pass. It gets its own known-answer check first: planted improbable words in constructed passages must score above their matched controls.
- **Measures.** Word surprisal given (a) the current sentence and (b) the full prefix, with log frequency, length and boundary as covariates. Flag words from suggestions shown in the last two minutes.
- **Primary.** The within-session slope of word-onset hesitation on full-prefix surprisal (b), beyond frequency and length, writer-clustered, against surprisal permuted within session. Direction: positive.
- **Also report.** Whether (b) beats (a) at sentence onsets, on held-out likelihood.
- **Cost.** The probe, then at most 3 CPU-hours.

**PP3. Can a record recover what the writer was doing? (instrument, with ground truth; ready at handoff)**
- **Data.** ScholaWrite (held since Phase 1): about 62,000 timestamped keystroke changes on 5 papers, under 10 project-scoped author IDs (not established persons). Two annotators labelled each span with one of 15 intentions, grouped as planning, implementation and revision (agreement 0.71, as reported).
- **Prior work this card builds on:**
  - g177's process-aware ceiling for the 15-way labels: mean macro-F1 0.048 over projects, "label noise at this grain" (`results/g177/scholawrite_ceiling.json`);
  - Stage 9's leave-project-out baseline: gains over previous-transition rivals not established (`docs/TOOLS.md`);
  - Stage 10, L386 to L389: a training-frequency prior beat every tested model in 27 of 30 ScholaWrite cells;
  - L68 and L69: the shipped split is within-project, so near-duplicate states cross the train and test boundary; leave-one-project-out is required.
- **Do.**
  - Classify each labelled span's high-level intention from process features only: pause before, burst length, insert or delete, edit size, position (end of text or inside), and LaTeX structure context.
  - Use no word content in the primary. Leave one project out.
- **Comparators:** the label-permutation baseline (labels shuffled within project), and the training-frequency prior.
- **Primary.** Macro-F1 over planning, implementation and revision, minus the better of the two comparators. Direction: positive.
- **Also report:**
  - half-Brier against the frequency prior, so a macro-F1 gain can't come from guessing rare classes;
  - the 15-way result, which is expected near g177's ceiling (stated now, before running);
  - the gain from adding content features;
  - the confusion matrix.
- **Route.** ScholaWrite only. A positive says a process-only readout of what a writer is doing has a measured accuracy on expert-labelled writing. It says nothing yet about WC1's CoAuthor goals, since no frozen mapping connects them to ScholaWrite's labels.
- **Cost.** At most 2 CPU-hours.

**PP4. What do second looks target, and is that hers? (hypothesis test; after P3c and PP1's route)**
- **Second look.** A revision of text written at least 30 seconds earlier, made after a pause: a subset of the errata's "later" edit class, not an immediate correction.
- **Why the filter.**
  - In one keystroke and eye-tracking study of 30 advanced second-language writers, revisions focused more on language than content, and in the recall comments on revisions (12 of the 30 writers did recall), language processes outnumbered planning about five to one (Révész et al. 2019).
  - Editing can also be an automatic interrupt rather than a deliberate pass (Hayes & Flower 1983).
  - Unfiltered, an attention map may be mostly a wording map.
- **Target classes:**
  - P3c's intents (clarity, fluency, coherence, style, meaning-changed);
  - the target's position: in her own typed text or in accepted AI text;
  - the target's PP5 role, if PP5 has landed.
- **Profile.** Each writer's distribution of second-look targets.
- **Primary.** Split-half reliability of writers' profiles across prompts (odd against even prompts), against writer-label permutations within prompt. Direction: positive. If her second looks consistently target the same things, they mark what she attends to, and possibly what she serves.
- **Also report:**
  - genre differences, stories against arguments;
  - the share of second looks that land on accepted AI text against its share of the document.
- **Cost.** At most 2 CPU-hours.

**PP5. The upper pyramid: plan roles and their boundaries (hypothesis test; after Gear 3 node PROC)**
- **Labels.** Gear 3 node PROC gives each sentence of every final document a role, and marks whether it is central to the writer's point:
  - arguments: PERSUADE's discourse elements (lead, position, claim, counterclaim, rebuttal, evidence, concluding statement; Crossley et al. 2022), plus other;
  - stories: setting, action, dialogue, inner thought, description, other.
  
  Map each sentence to its production time with a sentence-history reconstruction (THEtool's method, Ulasik et al. 2025).
- **Measures:**
  - (i) The pause before a sentence that changes role, minus one that continues a role, within session. Plan boundaries should draw planning pauses beyond ordinary sentence boundaries.
  - (ii) Each writer's role-sequence signature (role bigram rates), with identification under section 0.4, on CoAuthor only.
  - (iii) Where EV1's departures concentrate, by role.
- **Primary.** (i), writer-clustered, against role labels permuted within session. Direction: positive.
- **Route.** If (i) holds, ToMpathy's process hierarchy gains a measured plan-boundary layer (its engine packet).
- **Cost.** At most 2 CPU-hours, after PROC lands.

**PP6. Does the process find what matters to the writer? (hypothesis test; after PROC)**
- **Theory.** The curator's claim is that attention, the second look, goes to what she serves. The visual-attention analogue is decoding a viewer's task from gaze, the "inverse Yarbus" problem. It succeeds modestly at best: 34% against 25% chance in Borji & Itti 2014, and Greene et al. 2012 failed.
- **Do.** From process features only, predict which sentences PROC marks as central to the writer's point:
  - hesitation before;
  - revisions within;
  - second looks;
  - time spent.
  
  Leave writers out.
- **Primary.** AUC of process features plus position and length, minus position and length alone. Direction: positive. The null is a gain of 0.02 or less, or an interval including zero.
- **Cost.** At most 1 CPU-hour, after PROC lands.

### 2.3 Family W: pieces and goals

**WB1. Does the writing process reuse pieces beyond its grammar? (instrument; ready at handoff)**
- **Why.** The curator's pieces are options in Sutton, Precup & Singh's (1999) sense: temporally extended actions with their own policies and ends. Routine sequences can also be learned without any explicit hierarchy (Botvinick & Plaut 2004), so a piece detector has to beat sequence statistics, not just find repeats.
- **Alphabet.** Build it from P2's replayed text changes (character insertions and deletions, not keystrokes), the session clock and the menu events. At minimum:
  - a typing burst: insertions with no gap of 2 seconds or more (the errata's burst boundary);
  - a pause: a gap of 2 seconds or more;
  - a deletion run;
  - a revision move: a change away from the end of the text;
  - a suggestion request;
  - an acceptance;
  - a menu closed without a choice (P2's ignores, with censored ones flagged);
  - an edit of accepted text within 60 seconds.
  
  Bin burst, pause and deletion lengths at the corpus terciles. Record which log events make each symbol.
- **Split.** Divide writers into a discovery half and a test half (seed 20261026, stratified by session count). Every later card that uses pieces or discovery-half choices keeps this split.
- **Candidates.** Contiguous sequences of 3 to 6 events. Pairs are what the null preserves, so they can't count. Keep only candidates that occur at least 30 times in at least 10 discovery writers.
- **Null: first-order Markov surrogates.** For each session, draw 200 sequences from that session's own transition counts, with its first event and length. They keep the grammar (an acceptance follows a request) and the session's pairwise habits.
- **Discovery.** A candidate is a piece if its count in the discovery half is at least twice its surrogate mean and above every surrogate count.
- **Primary, on the test half.**
  - Coverage is the share of events inside discovered pieces (greedy cover, longest first).
  - The contrast is real coverage minus the mean over the test sessions' surrogates, with a writer-cluster interval. Direction: positive.
  - **One exclusion.** Pieces containing the edit-of-accepted-text symbol are discovered and reported, but left out of the primary. That symbol depends on an acceptance up to 60 seconds earlier, which first-order surrogates can't keep.
- **Sensitivity.** Whole-session surrogates don't keep drift within a session (typing speed and menu use early against late), which can register as pieces. Rerun discovery and the primary with surrogates drawn from each third of the session's own transition counts.
- **Effects of each occurrence,** from its last event to 60 seconds later:
  - net characters;
  - whether a sentence was completed;
  - the share of accepted characters still present at session end;
  - the change in similarity to the prompt (the frozen MiniLM that made CONTENT_V2 and P5).
  
  **Effect consistency** is the share of effect variance piece identity explains on the test half, against shuffled piece labels.
- **Route.**
  - **At least 20 pieces, test-half coverage above surrogates with its interval above zero, and the sensitivity agreeing:** WB2, WB3 and WC1 run on pieces.
  - **Otherwise:** run the pre-declared coarser variant WB1b (two bins, no revision moves), same design.
  - **WB1b also fails:** they run on single events.
- **Output.** Up to 10 piece classes by effect vector (k-means on standardised effects, discovery half, seed 20261026). Tokens for later cards are pieces where the cover places them, single events elsewhere.
- **Cost.** At most 3 CPU-hours.

**WB2. Is a writer's piece use her own? (hypothesis test; after WB1)**
- **Population.** The test half. The discovery half is reported beside it as descriptive.
- **Features.** Per session, token-use rates per 100 events.
- **Design.**
  - PMAP's gallery under section 0.4.
  - An increment test: style alone against style plus pieces, standardised and concatenated.
- **Primary.** Piece-use accuracy minus its context-only reference. Direction: positive.
- **Cost.** At most 1 CPU-hour.

**WB3. Does she have a stable if-then signature? (hypothesis test; after WB1)**
- **Situations:**
  1. the first two minutes;
  2. mid-sentence;
  3. a sentence just ended;
  4. after a pause in the top tercile;
  5. after a dismissal;
  6. after an acceptance;
  7. the two minutes before the 10-minute timer;
  8. after the timer.
- **Signature.** Her rate per situation and token class, minus the discovery-half population's rate in the same situation. This is a behavioural signature in Mischel and Shoda's sense (1995): "if A then she X, but if B then she Y".
- **Primary.** On the test half: the median Spearman-Brown split-half reliability of signatures across prompts (odd against even), against writer-label permutations within prompt. Direction: above the permutation null.
- **Cost.** At most 2 CPU-hours.

**WC1. Inverse planning over pieces (hypothesis test; after WB1).**
- **Method.** Adapt the program's verified inverse-planning implementation from movement to writing. It is `runners/run_bst_gridworld.py`, checked against Baker, Saxe & Tenenbaum 2009 in `results/bst2009_reference/`; Experiment 1 passed, and Experiments 2 and 3 are open.
- **Goals.** Each is defined by an outcome measured from a token's end to 60 seconds later:
  1. a sentence completed;
  2. text added (net characters up);
  3. text moved toward the prompt's topic;
  4. text revised without growing (edit distance above zero, net characters within ±5);
  5. alternatives looked at (offers displayed, no net change).
  
  Goals 4 and 5 sit close to the tokens' own content; the Markov comparator is the guard.
- **The model.**
  - Each token class's expected progress on each goal is its mean outcome on the discovery half.
  - The chooser is a softmax over expected progress toward the active goal, with rationality β.
  - Goals persist with probability ρ per token.
  - β and ρ are fitted on the discovery half.
- **Held out.** The test half. Library, classes, situation rates and parameters all come from the discovery half.
- **Comparators** on held-out next-token log-loss, all fitted on the discovery half:
  - token frequency;
  - situation-conditioned frequency;
  - a first-order Markov chain over tokens.
- **Primary.** Held-out log-loss gain over the first-order Markov chain, the strictest comparator. Direction: positive. Any model with persistent latent states beats situation-conditioned frequency, so that gain alone can't show a goal layer.
- **Also required:**
  - the gains over situation-conditioned frequency and token frequency;
  - drop-one-goal sensitivity;
  - per-session goal posteriors, for WC3;
  - agreement with Gear 3 node GOAL's labels, as convergent validity;
  - the token-class by goal progress table, for ToMpathy.
- **Cost.** At most 3 CPU-hours.

**WC3. Does she have a stable goal profile? (hypothesis test; only if WC1 beats the Markov chain)**
- **Features.** Each test-half writer's time share per goal, minus the population's in the same situations.
- **Primary.** Split-half reliability across prompts, against writer-label permutations within prompt. Direction: positive.
- **Also report.** Identification under section 0.4.
- **Cost.** At most 1 CPU-hour.

**WC4. What does she hold steady? (hypothesis test; ready at handoff)**
- **Why.** A controller suppresses variability only in the dimensions that matter to its goal: the minimal intervention principle (Todorov & Jordan 2002).
- **Properties:**
  - sentence length;
  - words per burst;
  - pause before a sentence;
  - acceptance rate;
  - edit-after-accept rate;
  - retained share of accepted text;
  - lexical density;
  - punctuation rate.
- **Profile.** Use sessions with at least 50 events. For each property, her across-session variance (prompt-adjusted) over the population's average within-writer variance.
- **Primary.** Split-half agreement of profiles across prompts, against writer-label permutations within prompt. Direction: positive.
- **Caveat.** Low variance can also mean a habit, a constraint, or little disturbance. Read it beside Ghost's W2, whose readout failure rate is a lower bound for this card: W2 knows the open-loop variance, and WC4 doesn't.
- **Cost.** At most 1 CPU-hour.

### 2.4 Family N: ends and natural blocks

**"Block" in this family** means an outcome block, in Ghost's sense: a chosen means that fails after the choice (an accepted span she later deletes, a run of offers that keep missing). Ghost's "remove", an option taken away before the choice (its W1), has no counterpart in CoAuthor's logs.

**WC2. When the means fails, does the direction persist? (hypothesis test; ready at handoff)**
- **Event.** Accepted spans the writer later deleted by at least 80%, rebuilt from P2's canonical choices. NP1's 429 used D38's original accepted-span definition; report how many survive the rebuild.
- **Support.** Before freezing, count events with a complete window: at least 150 events from at least 25 writers. Below that, record WC2 as unsupported.
- **Text.** Her next 50 typed words, starting at the next sentence boundary after the deletion.
- **The span's advantage.** The embedding similarity (same frozen MiniLM) of that text to the deleted span, minus its similarity to the unchosen offers in the same menu.
- **Context-only reference.** The same advantage computed on other writers' typed text from sessions on the same prompt, at the same relative position in the session. A chosen offer can be more generic or on topic than the others, which would show in anyone's text.
- **Primary.** Her advantage minus the context-only advantage, writer-clustered. Direction: positive.
- **Phrase overlap.** Wording is measured at the phrase level: the share of her window's word bigrams and trigrams that also occur in the deleted span, minus the same for the context-only reference. A writer who makes the same point in her own words keeps the span's key nouns, so content-word overlap can't separate wording from content; it is reported only as a descriptive. Function-word sequences are a secondary phrase measure.
- **Kept-span reference.** The same advantages after accepted spans she kept, matched on position and length. Its 50-word window also starts at the next sentence boundary after the span, so adjacency doesn't inflate it.
- **Route,** on the contrast that separates the rivals.
  - **The band.** The equivalence band for phrase overlap is frozen now: a quarter of the between-writer SD of the context-only reference's phrase-overlap values, one value per writer. "Inside the band" means the phrase-overlap advantage's 90% interval lies within ±band (two one-sided tests at 5%).
  - **Reachability.** Before freezing, estimate the 90% interval's half-width at the support count. If it exceeds the band, "inside" can't be reached; widen the band to that half-width and record why.
  - **Same end, new means:** the embedding advantage's interval above zero, and phrase overlap inside the band. "The direction survives a failed means."
  - **Lingering taste:** the embedding advantage's interval above zero, and phrase overlap's interval entirely above the band. "The wording lingers; the direction isn't separable from it."
  - **Unresolved:** the embedding advantage's interval above zero, with phrase overlap neither inside the band nor entirely above it.
  - **No direction:** the embedding advantage's interval includes zero.
  - **Moves away:** the embedding advantage's interval lies below zero: her text turns away from the deleted span's direction.
  - Bigrams can still catch noun compounds that a paraphrase keeps; function-word sequences, the secondary measure, are the check on that.
- **Also report:**
  - content-word overlap, descriptive;
  - a sensitivity window for the deleted arm only, starting at the deletion itself rather than the next sentence boundary, where a new means would show first;
  - the persistence ratio, (her advantage − context) / (kept-span advantage − context), as a size, only when the denominator's lower bound is at least 0.01 cosine; otherwise "unresolved";
  - each writer's persist-or-drop share, with its split-half reliability.
- **Cost.** At most 2 CPU-hours.

**FR1. Does she show more of herself right after the AI fails her? (hypothesis test; ready at handoff)**
- **Theory.** The curator's objection to "ends need designed variation": emotion systems carry signatures that fit only certain outcomes, so "anger only fires when you want something".
  - The research pass supports the weak form: observers recover desires from emotional reactions when they know the triggering event (Wu et al. 2018; Houlihan et al. 2023; both read in abstract).
  - It contradicts the strong form: no appraisal component is necessary or sufficient for anger (Kuppens et al. 2003), and aversive affect alone primes it (Berkowitz 1989).
  - CoAuthor logs a candidate trigger, the dismissed offers. A dismissal isn't always a failure, though: writers dismiss offers they never needed.
  - In this corpus the nearest observable is frustration: a run of three or more dismissals is a want the AI kept failing to serve. If frustration exposes the want, what she writes right after should be more hers.
- **Events.**
  - Runs of three or more dismissals, rebuilt from P2's canonical choices (NP1 found 292).
  - Controls: single dismissals, matched on session time and position.
- **Support.** Before freezing, count events with a complete 50-word window: at least 100 frustration events from at least 25 writers, each with a matched control. Below that, record FR1 as unsupported, not null.
- **Text.** Her next 50 typed words after each event.
- **Why not identification.** 292 runs give about 240 words per writer, about 120 per half under section 0.4's split, far below what identification needs. So FR1 measures distance to her own profile instead.
- **Self-proximity.** The population's mean style distance to her profile at the same prompt position, minus the style distance from the window to her own profile. Her profile is built from her other typed text, excluding both arms' windows and the calibration's held-out quarter.
- **Calibration first.** Hold out a random quarter of her other sessions from the profile. Splice 20% and 40% of that held-out text into matched neutral windows, and confirm self-proximity rises with the plant. Text already in the profile would make the rise partly guaranteed.
- **Primary.** Self-proximity after frustration minus after matched single dismissals, within writer, writer-clustered. Direction: positive.
- **Also report:**
  - the embedding distance from the post-event text to the dismissed offers: does she go somewhere the AI wasn't offering?
  - the pause before she resumes typing;
  - the same contrast after accepted spans she deleted (WC2's events).
- **Cost.** At most 1 CPU-hour.

**PR1. What does she pay to say it herself? (hypothesis test; ready at handoff)**
- **Theory.** The curator: you know something is an end by what you'd sacrifice for it, at a micro level. The research pass:
  - price paid above the cheapest route to the same outcome is a revealed value (Liu et al. 2017; Westbrook et al. 2013);
  - but it shows how much something is valued, not whether it is an end;
  - and payment made in public can be reputation.
  
  CoAuthor is private, and the cheapest route is logged: accepting an offer.
- **Prior result.** D20's extension found the reliability of dismissed-suggestion uptake null in 46 writers (content-word overlap r = −0.02, interval −0.41 to 0.43), and every outcome-permutation reference flagged bias. PR1 adds what D20 lacked: a context-only reference, and a contrast that separates paying from predictability.
- **The rival.** CoAuthor's offers are GPT-3 continuations of her own text. So her next words resemble a dismissed offer whenever the model predicted her, whether or not she read it.
- **Event.** A dismissed menu (P2's canonical choices) followed by typed text.
- **Her advantage.** The highest cosine between her next 50 typed words and the dismissed offers, minus the same for other writers' typed text at the same prompt position against the same offers (the context-only reference, as in WC2).
- **Examination.** Menus she examined (open longest: her own upper tercile of open time, or a logged hover, with D6's caveat that this is "examination", never "attention"), against menus she closed fastest (her lower tercile). Predictability raises her advantage either way. Paying to say it herself needs her to have read the offer.
- **Balance check.** Open time may also track how relevant the offers were, or planning while the menu sat open. Compare examined and fast menus on a predictability proxy measured before she types: the offers' similarity to her preceding text, and P8's logged score. If they differ, add the proxy to the primary as a covariate.
- **Support.** Before freezing: at least 25 writers with at least 10 examined and 10 fast dismissals each. Below that, record PR1 as unsupported.
- **Primary.** Her advantage after examined dismissals minus after fast ones, writer-clustered. Direction: positive.
- **Also report:**
  - the price: on examined events above the population's median advantage, the time and characters she spent typing beyond the context-only expectation, with its split-half reliability across prompts (writer-label permutations within prompt), as the person-level secondary;
  - what she pays for: stance and opinion sentences in arguments, against narration in stories (PROC's roles once they land);
  - whether paying writers show less of TR3's capture.
- **Cost.** At most 1 CPU-hour.

### 2.5 Family CA: values from designed choices

**Why.** CoAuthor's menus weren't built to vary values. Community Alignment's were.
- Its candidate responses were generated with negatively-correlated sampling (arXiv abstract).
- More than 3,500 annotators across five countries made more than 200,000 comparisons. The median annotator contributed 26 conversations, and 44% of comparisons carry a written explanation of the preference (the dataset card, checked 25 October).
- The release holds 90,256 conversation rows from 3,603 annotators (the 14 October intake census).

If values can be read from a real person's choices anywhere in the program's data, it is here. And her own explanations give a criterion CoAuthor never had. Sources: Zhang, Milli et al., ICLR 2026 (arXiv 2507.09650); the dataset card on Hugging Face (CC-BY-4.0).

**CA0. Codebook and population (instrument; ready at handoff).**
- Intake the paper (section 4) and read its codebook appendix.
- Confirm what one row is. Rows are conversations, so validate turn counts against the codebook:
  - the number of candidates per comparison and how the choice is encoded;
  - annotator identifiers, country, language and wave (the release has no timestamp, so no temporal order is invented);
  - the explanation field;
  - multi-turn structure.
- Freeze the analysis unit and the population: annotators with at least 20 comparisons on at least 10 prompts.
- **Shared prompts.** Report the share of comparisons on prompts shared by at least five annotators. If it is under half, CA1's and CA4's within-prompt permutations fall back to permutations within country and within 50 prompt clusters (k-means on prompt embeddings, seed 20261026).
- Choose a multilingual sentence encoder that runs on the CPU, for example `paraphrase-multilingual-MiniLM-L12-v2`, and pin it.
- Report counts only.
- **Cost.** At most 1 CPU-hour.

**CA1. Does an annotator have a stable value direction of her own? (hypothesis test; after CA0)**
- **Model.** Choice among candidates by a logit on candidate features: the pinned embeddings, reduced by PCA fitted on candidates only.
- **Three nested readers:**
  - population: one direction;
  - country: a direction per country;
  - individual: her own direction, shrunk toward her country's.
- **Fit and test.** Fit on half of each annotator's prompts; test on the other half.
- **Primary.** Held-out log-loss gain of individual over country, annotator-clustered, against annotator labels permuted within prompt (or CA0's fallback). Direction: positive. This is "own beyond culture".
- **Also report:**
  - the gain of country over population;
  - the gain by number of training comparisons, which gives a records-needed curve;
  - her direction's cosine with each value prototype (CA3's scores), descriptive.
- **Cost.** At most 12 CPU-hours, embeddings included; S4 applies past that. Pilot on 10% of comparisons first (row 12); the forecast is 6 CPU-hours on two threads.

**CA2. Culture against own (hypothesis test; after CA1).**
- **Decompose** the fitted preference directions into country, annotator within country, and residual.
- **Primary.** The split-half reliability of each annotator's deviation from her country's direction. Direction: positive.
- **Why.** This is the curator's "divergence from a population mean reveals individual preference", with the population chosen as her country.
- **Cost.** At most 1 CPU-hour.

**CA3. Do her choices predict the values she states? (hypothesis test; after CA1 and VAL)**
- **Labels.** Gear 3 node VAL codes each sampled explanation for Schwartz's ten basic values, present or absent, plus "other".
- **Value prototypes,** frozen before any held-out explanation is scored. For each value: the mean PCA-space difference (chosen minus unchosen candidate) over explained comparisons VAL coded with that value, built from other annotators only (leave-annotator-out), minus the same mean over all explained comparisons. Centring removes the population's shared direction, which would otherwise dominate every cosine.
- **Her scores.** The cosine between her choice-derived direction and each value's prototype. Unlike CA1's half split, her direction here is refit on all her comparisons without explanations, so none of the held-out explanations' comparisons enter it.
- **Test.** Per value, the AUC of her scores against the values she states in her held-out explanations. Country and population readers are scored the same way.
- **Primary.** Mean AUC across values with at least 5% prevalence in VAL's coded sample, individual minus country, annotator-clustered, against annotator-label permutations. Direction: positive.
- **Caution.** Machine detection of the values behind arguments is weak; shared-task systems averaged F1 0.25 (Kiesel et al. 2022). VAL's known-answer rung decides whether its codes are usable at all.
- **Route.** A positive is the program's first reading of a real person's values from her choices, checked against her own words. It goes first in the final digest.
- **Cost.** At most 2 CPU-hours, after VAL.

**CA4. Can an annotator be picked out from her choices? (hypothesis test; after CA1)**
- Gallery identification from choice profiles under section 0.4, with "prompt" read as the item (or CA0's fallback).
- **Primary.** Real minus context-only accuracy under section 0.4. Direction: positive.
- **Cost.** At most 1 CPU-hour.

**CA5. Raters, groups and items in DICES (hypothesis test; ready at handoff).**
- **Question.** Does a rater depart from her demographic group in a stable pattern across harm categories, beyond overall leniency?
- **Data.** DICES-350: 123 raters × 350 conversations, fully crossed, with rater demographics.
- **Decompose** safety judgments into rater, demographic group, item, item × group, and item × rater, freezing both rater denominators (123 and the paper's 104) before outcomes.
- **Profile.** Each rater's deviations from her group's item means, centred within rater (removing leniency), averaged by DICES harm category.
- **Primary.** Split-half reliability of profiles (odd against even items), against rater-label permutations within demographic group. Direction: positive.
- **Cost.** At most 1 CPU-hour.

### 2.6 Family T: trust, uptake and capture

**WD1. Lean and sensitivity: does she learn which suggestions to trust? (hypothesis test; SDT1, built at last; ready at handoff)**
- **Quality reference.** A population-only acceptance model: P4's features with no writer terms and none of her own history (V2's H1 and H2), refit leaving each writer out. P4's own backbone carries writer offsets, which would make her sensitivity partly circular.
- **Design.**
  - Each writer's criterion (lean) and sensitivity, against that reference.
  - Section 0.4's permutation rule replaces the same-row fake writer.
  - A known-answer validation on constructed decisions first.
- **Primary.** Split-half reliability of sensitivity, against writer-label permutations within prompt. Direction: positive.
- **Secondary.** The change from her first third of sessions to her last, separately for criterion and sensitivity.
  - Rising sensitivity: she learns which offers to trust.
  - A moving criterion: she only learns how much to trust.
- **Cost.** At most 2 CPU-hours.

**WD2. Partial uptake: what does she cut from what she accepts? (hypothesis test; ready at handoff)**
- **Events.** Edits of an accepted span within 60 seconds.
- **For each event,** compare removed and kept characters, each against her typed text before the event only, on:
  - style distance: per-character function-word and punctuation rates, so segment length doesn't drive it;
  - topic distance: embedding against her preceding 200 characters;
  - position: head or tail of the span;
  - length.
- **Primary.** Style distance of removed text minus kept text, within event, with the removed text's position (head or tail) in the model, since removals cluster at the tail. Writer-clustered. Direction: positive (she cuts what isn't hers).
- **Also report:**
  - split-half stability of each writer's removal profile, and P3c's intents for the removed text once they land;
  - **filtering mode against capture:** whether writers who mostly delete accepted spans wholesale show less of TR3's capture than writers who mostly edit them locally. The curator's account (declining to engage protects you) predicts yes. Williams-Ceci et al. 2026 (labels didn't protect; read in abstract) predicts no.
- **Cost.** At most 1 CPU-hour.

**TR5. When the AI fails her, how does her trust move? (hypothesis test; ready at handoff)**
- **Theory.** The curator: betrayal hurts because you learn the other "would do it again". Formal accounts:
  - learning rates that track volatility (Behrens et al. 2007), including for an adviser whose intentions change (Diaconescu et al. 2014);
  - change points (Adams & MacKay 2007);
  - trust recovering after consistent good behaviour unless the untrustworthy acts came with deception (Schweitzer et al. 2006).
- **Event.** A model failure in D38's canonical definition: an accepted span later deleted by at least 80% (429 candidates), rebuilt from P2's canonical choices. The failure comes into view when she deletes the span. The stricter subset, deleted within 30 seconds and retyped (at least half the deleted characters typed back at the same position within 60 seconds), is a secondary.
- **Run length.** The number of consecutive accepted-and-kept suggestions before the failed acceptance, with runs of 5 or more pooled. "Kept" is judged at the moment of the failure: at least 80% of the accepted characters still present when she deletes the failed span. Judging it at session end would let her reaction to the failure (re-checking earlier AI text) change the grouping. The failure's moment is when 80% of the span is gone.
- **Window.** The 5 menus before and after, inside the session. Windows don't cross session boundaries.
- **Matched controls.** A long run forces a high acceptance rate just before the event, and any such point then regresses toward her mean, failure or not. So each failure gets matched non-failure points: the same writer, the same session-position decile, an accepted suggestion she kept, after a run of the same length, with its window anchored at the same delay after acceptance as the failure's deletion. A control's own "kept" status, run length and decile are judged at its anchor, not at session end.
- **Outcome: the drop.** For failures and controls alike, her acceptance rate (and request rate) over the 5 menus before, minus the 5 after. A fall in acceptance is a positive drop.
- **Support.** D38 kept 109 of the 429 events after its source and window screen. Before freezing, count failures with complete windows and at least one matched control: at least 60 from at least 20 writers, with both run-length bins present. Below that, record TR5 as unsupported, not null.
- **Learners fitted to her handling,** compared on held-out likelihood:
  - fixed rate;
  - volatility-adaptive;
  - change-point, optionally with session boundaries as change points.
- **Primary.** Within each run-length bin (long: at or above the pre-event median run, frozen from the data before outcomes; short: below it), the failure's drop minus its matched controls' drop. The primary is long minus short on that difference, writer-clustered. Direction: positive.
  - The curator's account predicts a larger relative drop after a long run: positive.
  - A stationary Bayesian predicts buffering, a smaller relative drop after a long run: negative.
  - The raw drops, without controls, are reported only as descriptives.
- **Natural experiment.** CoAuthor varied the GPT-3 instance and its settings across sessions (the abstract mentions four instances; P8 extracted the settings for all 69,109 suggestions). How they were assigned to sessions is unverified, so read this as a natural experiment, not a randomised one. Within writer, does her acceptance track the session's temperature, and how fast within the session? That is trust learning a competence ledger. Report it as a secondary.
- **Cost.** At most 2 CPU-hours.

**TR3. Capture: do the suggestions she saw show up later in her own typing? (hypothesis test; ready at handoff)**
- **Theory.** The curator's account of indoctrination is repetition until a structure becomes the default autocomplete in flow.
- **What the literature says.**
  - Co-writing with an opinionated model shifted essays and attitudes, mostly unnoticed (Jakesch et al. 2023).
  - Warning writers that the assistant was biased didn't reduce the shift (Williams-Ceci et al. 2026, read in abstract).
  - Within a single session, though, writers' own typed text stayed unchanged (Padmakumar & He 2024).
  - The open question is across sessions.
- **Features.** Model-characteristic features: n-grams, function words, punctuation and hedges with high pointwise mutual information for GPT-3 suggestions against human typing, chosen on WB1's discovery half of writers.
- **Exposure.** For session k, the features in suggestions she was shown before session k that never appeared in her earlier typing.
- **Outcome.** The rate of those features in her own typed characters in session k.
- **Placebo.** The same kind of features from suggestions other writers saw on the same prompts, which she never saw, matched to the seen features on corpus frequency (deciles).
- **Primary.** Seen minus placebo, test half, writer-clustered. Direction: positive. The falsifier is seen = placebo.
- **Also report:**
  - dose-response in the number of exposures;
  - accepted minus dismissed (production against mere exposure);
  - dismissed minus placebo (exposure alone).
  
  Count her repeat sessions first; covariates are prompt, session index and practice.
- **Route.** A positive, frozen as is, goes to TR3c.
- **Cost.** At most 2 CPU-hours.

**TR3c. Capture on the randomized holdout (confirmation; frozen this week, run at Tier 4 with FX1)**
- **Data.** Padmakumar & He's writers (38, by the 17 October packet's count) on the CoAuthor interface, with GPT-3, InstructGPT and no-model arms (section 4's intake). This is the Tier 4 holdout the 17 October packet also assigns to FX1. Its outcome fields stay hashed and unread.
- **Holdout rule.** TR3c doesn't spend the holdout this week. It is frozen once TR3 is positive and frozen and the schema census is in, and it runs at Tier 4 in the same single read as FX1.
- **Design, settled by the census:**
  - **If writers wrote several essays across arms in a recorded order:** TR3's seen-minus-placebo index in essays that follow model-arm essays. If the census shows arm order was randomised, that is the randomisation and this is the cross-session confirmation; if not, the design is observational and labelled so.
  - **Otherwise:** the within-essay index, model arms minus the no-model arm, labelled a within-session replication. Padmakumar & He found writers' own text unchanged within a session, so this can't confirm TR3's cross-session effect.
- **Waiting on FX1.** Sharing FX1's read means TR3c waits on FX1's preconditions (V4 seeing taste, a goal reader, N13 passing), which may never hold. If they haven't held at Tier 4 review, TR3c is reported as "frozen, unrun". It doesn't read alone: the holdout's value is in staying unspent.
- **Cost.** At most 1 CPU-hour, at Tier 4.

**TR4. Is her recent self a better guide than her whole record? (hypothesis test; ready at handoff)**
- **Theory.** The curator's "Heisenberg" problem: a long track record pins down a lifetime trajectory and blurs what she wants now.
  - The literature's answer: the penalty belongs to readers that assume a stable person or use fixed windows. With the right change model, more history doesn't make the current estimate worse in expectation.
  - The "derivative of a set point" is a latent slope in a local linear trend model, estimated by filtering.
  - Formal tools: volatility-tracking learning rates (Behrens et al. 2007) and change points (Adams & MacKay 2007).
- **Writers.** Those with at least 12 sessions.
- **Predictions of her handling choices in each session,** from earlier sessions only:
  - (a) her whole-history mean;
  - (b) her last session;
  - (c) an exponentially weighted mean, with its rate fitted on the discovery half;
  - (d) a volatility-adaptive Kalman filter on additive log-ratios of the session's shares of the program's four handling classes (accept, edit, dismiss, ignore; pseudo-count 0.5), with accept as the base class and her process noise fitted on her earlier sessions. All six predictors use the same four classes;
  - (e) a local linear trend: level plus a latent slope, the set point's derivative;
  - (f) Bayesian online change-point detection, as a secondary.
- **Primary.** Held-out log-loss gain of (d) over (a): log-loss of (a) minus log-loss of (d), on the last third of her sessions, writer-clustered. Direction: positive.
- **Also report.** Her estimated volatility, with its split-half reliability. Do some writers change more than others?
- **Cost.** At most 1 CPU-hour.

### 2.7 Family FIC: finding the author

**Why.** The curator holds that "you find the author in fiction" is well established, and that GEN1's null more likely shows the test environment than the world.

**What has been tested.** Two small direct tests, and neither favoured fiction:
- **ABC-NL1:** eight writers, each writing fiction, argument and description, about 908 words a text. Genre outweighed authorship.
- **GEN1:** 24 CoAuthor writers, with typed words matched within writer. No fiction advantage was detected (10 of 24 identified from stories, 12 of 24 from arguments). Its per-genre fake-writer references failed, so its sensitivity is untested; GEN1.ic checks it.

**Indirect evidence:**
- In authorship verification by unmasking on five authors, F1 was 94.7% within long prose and 55.7% when prose was paired with plays (accuracies about 96% and 77%, over mostly different-author pairs; Kestemont et al. 2012). The study pairs genres; it doesn't train on one genre and test on another.
- Opinion essays can be highly attributable too: 90% from other genres among 21 writers (Goldstein-Stewart et al. 2009).

**What could hide authors in CoAuthor's stories:**
1. **Prompt anchoring,** the lead explanation. A story continues a stranger's premise, while an argument carries the writer's own stance. In CoAuthor the story may be the more constrained situation.
2. **AI text,** probably minor here.

Length is probably not the explanation: GEN1 pooled about ten sessions, roughly 2,500 typed words, per writer, genre and prompt half.

This family takes the question seriously: a stronger instrument on CoAuthor, real novels, and a second corpus of edited prose.

**FIC1. A stronger instrument on GEN1's writers (hypothesis test; after GEN1.ic, and its primary after AUTH)**
- **Variants:**
  - (a) full typed texts, without subsampling to matched length, with length as a covariate;
  - (b) final documents;
  - (c) Gear 3 node AUTH: pairwise same-author judgments.
- **AUTH's pairs.**
  - For the 24 writers: 4,000 pairs, half same-writer within genre on different prompts, half different-writer on the same prompt pairs, balanced by genre.
  - Each text is her typed text only, at most 400 words.
  - Haiku answers with a 0 to 9 confidence that one person wrote both.
  - The first 100 argument pairs are AUTH's known-answer rung, and are left out of the primary.
- **Primary.** AUTH's AUC in stories minus in arguments, writer-clustered. Direction: positive.
- **Also report:**
  - (a) and (b) under section 0.4;
  - GEN1's 2 × 2 table (identified in stories only, in arguments only, in both, in neither), with an exact McNemar test;
  - (d) a length curve: identification by genre at 500, 1,000 and 2,000 typed words per profile and at the full length. If accuracy doesn't rise with length, stop: the instrument is the problem.
- **Cost.** At most 2 CPU-hours, plus AUTH's Gear 3 cap.

**FIC2. D31 revived: author or character in novels (hypothesis test; after intake and K)**
- **Card.** The 17 October D31 as written (`PACKET_20261017_PUBLIC.md`, D31), with two changes: a 3 CPU-hour ceiling (it was 1) and K capped at $2.50 (it was $5).
- **Primary, unchanged.** The coefficient on the leave-book-out author fearful rate (her characters in her other books), predicting a character's fearful response beyond intensity, genre × decade and consensus. Direction: positive.
- **Its extension** asks whether a character's fear in a low-threat scene is evidence about the author.
- **Sequence.** It missed its 19 October gate for lack of intake and blind labels. This week: section 4's SPGC intake, then the owner's 100 blind labels, then K.
- **Cost.** At most 3 CPU-hours, plus K's cap.

**FIC3. The same authors in fiction and essays, at length (hypothesis test; after intake)**
- **Question.** Does fiction identify its author better than essays do, in edited prose, at the lengths stable attribution uses? This tests the claim in edited prose. It can't say what caused GEN1's result.
- **Corpus.**
  - SPGC authors with at least 6,000 words each of fiction and of essays, so 3,000-word gallery and probe profiles can be disjoint within genre.
  - SPGC has no essay label, so freeze the essay frame before outcomes: works whose Library of Congress subjects include "Essays", or whose LoC class is B, H or J (philosophy, social sciences, political science), by authors who also have works with a "Fiction" subject. Audit 50 assignments by hand and report the error rate.
  - If the intake policy accepts Reddit's terms, add a second arm: ConvoKit's r/WritingPrompts and r/changemyview corpora (each subreddit from its start to October 2018), accounts active in both. Usernames are never published.
- **Design.**
  - Genre (within author) × length: 300, 1,000 and 3,000 words per profile. The 300-word cell mirrors one CoAuthor session.
  - Candidate pools of 24 authors, at least 200 random pools.
  - GEN1's frozen pipeline, plus one independent method that masks topic words.
- **Primary.** At 3,000 words, fiction minus essay top-1 accuracy, with an exact paired (McNemar) test. Direction: positive. Report an equivalence test at ±5 points beside it.
- **Controls:**
  - accuracy must rise with length; if it doesn't, stop;
  - authors uniformly relabelled score at chance (1/24);
  - fake authors spliced from two real ones are identified less often than real authors;
  - PAN 2019's cross-fandom fan-fiction set (Zenodo record 3530313, open; pin its version and read its licence at intake) runs as a positive control for the pipeline: English problems only, closed-set, so documents whose true author is outside the candidate set (its "<UNK>" class) are dropped.
- **Readout:**
  - **a fiction advantage at 3,000 words:** the claim holds in edited prose at length;
  - **none at any length, with equivalence:** in edited prose, fiction doesn't reveal its author more than essays do;
  - neither result says why GEN1 found what it found.
- **Power.** McNemar power depends on the share of discordant pairs. At 15% discordance, about 470 authors detect 5 points and 115 detect 10; at 30%, about 940 and 233. Estimate discordance from the 300-word cell first, and report which applies.
- **Cost.** At most 3 CPU-hours.

### 2.8 Family V: value words

**WE1. Do value words recur within a writer? (hypothesis test; idle slots)**
- **Precondition.** The Personal Values Dictionary (Ponizovskiy et al. 2020), section 4's optional intake 8, under its published terms. If it can't be taken in, use Gear 3 node VAL's codes of each argumentative session's typed text instead.
- **Design.**
  - Score each writer's typed text on the ten values.
  - Compare profile similarity: same writer on different prompts, against different writers on different prompts.
  - Prompt control: different writers on the same prompt.
- **Primary.** Same writer, different prompt minus different writer, different prompt. Direction: positive.
- **Note.** The dictionary agrees with self-report at r = .1 to .4 for seven of its ten values, so a null here is weak evidence.
- **Cost.** At most 1 CPU-hour.

### 2.9 Dispatch order

**Ready at handoff,** in this order:
1. WA0, with GEN1.ic inside it
2. WB1
3. PP1
4. CA0
5. WC2
6. FR1
7. TR5
8. WD1
9. P3c
10. TR3
11. TR4
12. PR1
13. WC4
14. CA5
15. WD2
16. PP3
17. WA1

**Then, as gates open:**
- PP2 (after PP1); PP7 (after PP1 and its cost probe)
- CA1 (after CA0), then CA2 and CA4
- WB2, WB3 and WC1 (after WB1), then WC3 (only if WC1 beats the Markov chain)
- FIC1 (after GEN1.ic; its primary after AUTH)
- PP4 (after P3c and PP1's route)
- PP5 and PP6 (after PROC)
- CA3 (after CA1 and VAL)
- FIC2 (after intake and K)
- FIC3 (after intake)
- TR3c (frozen after TR3 is positive and frozen and the Padmakumar & He census is in; it runs at Tier 4 with FX1)

**Idle slots:** WE1, then section 6.

Follow-ups under section 0.3 C enter at their stated rank.

## 3. What each result changes

| Result | Route |
|---|---|
| WA0 changes a published verdict | A dated correction in FINDINGS and the claim ledger. Trigger 3 if it reverses a delivered public claim |
| WA0 passes EV3's final documents, raw and residualised | ToMpathy may show a habit badge |
| WA0 passes the final-document style variant, raw and residualised | ToMpathy's style display may quote it on web pages |
| GEN1.ic, any outcome | GEN1 is uninformative about genre differences below about 31 points; FIC1 and FIC3 carry the question |
| WA1's minimum detectable advantage is above 0.02 | The miniature-author stream is recorded as underpowered at the useful margin, not as failed |
| PP1 holds | Timing-based process cards run on CoAuthor |
| PP2 positive | ToMpathy can mark sentence-level divergences as candidate attention, beside EV1's word-level marks |
| PP7 positive | Surprisal predicts word-onset hesitation in free composition, beyond frequency and length |
| PP3 positive | A process-only readout of what a writer is doing has a measured accuracy on expert-labelled writing (ScholaWrite only) |
| PP4 positive | "What she takes a second look at" becomes a person-level profile |
| PP5 (i) positive | ToMpathy's process hierarchy gains a plan-boundary layer |
| PP6 positive | Process marks locate what matters to the writer, a measured basis for "attention reveals goals" |
| PR1 positive | Paying for her own words, once she has read the offer, becomes a marker of what she won't delegate |
| TR5 positive | Trust in the AI moves like trust in a person: by the history a failure breaks, not by a running count |
| WB1 positive | The engine gets an event alphabet and a piece detector, on the CoAuthor path first |
| WC1 positive over the Markov chain | The engine gets a goal-of-the-moment readout for process records |
| WC2 routes to "same end, new means" | A natural block carries a writer's direction past the deleted wording |
| FR1 positive | Her writing moves toward her own profile after repeated AI failure. That shows more of her style; it doesn't by itself recover what she wants |
| CA1 positive | Individual value directions are readable from designed choices, beyond country |
| CA3 positive | The first reading of a real person's values from her choices, checked against her own stated reasons |
| WD1 positive | The panel shows lean and sensitivity separately, as B3 planned |
| TR3 positive, then TR3c positive across sessions | Capture by suggestions she saw is measured, and confirmed on a randomized holdout at Tier 4 |
| TR4 positive | Maker estimates in ToMpathy may weight recent works by a volatility-adaptive rate |
| FIC1 or FIC3 positive | The fiction claim gains a measured basis; ToMpathy's B10 weighting can be revisited |
| Any card unsupported | Recorded apart from nulls, with its support count; no instrument check follows |
| Section 5 not approved at handoff | Node-dependent cards are blocked under S6; the ready queue needs no node |

## 4. Intakes (network lane, under `DATA_INTAKE.md`)

Handing over this packet approves these intakes, each with a licence read, pinned revision, hash and census. If the policy refuses a source, skip it and record why.
1. **The Community Alignment paper** (arXiv 2507.09650), for its codebook appendix. CA0 needs it.
2. **The SPGC sample for D31** (FIC2), as the 17 October packet specified: public domain.
3. **Padmakumar & He's logs** (`github.com/vishakhpk/hai-diversity`), for TR3c. Download, hash and run a schema census only. Outcome fields stay hashed and unread until Tier 4.
4. **The IteraTeR intent classifier** (`wanyu/IteraTeR-ROBERTA-Intention-Classifier`, RoBERTa-large), for P3c. If it is gated or absent, P3c's classifier counts as failed.
5. **A multilingual sentence encoder** for CA1, pinned at intake.
6. **KLiCKe** (Tian, Crossley & Van Waes 2025: about 5,000 argumentative essays with full keystroke fields, one session per writer; its GitHub page shows an MIT licence, read at intake), for PP1's fallback. Optional.
7. **For FIC3:**
   - SPGC essays by the novelists in FIC2's frame, and by other SPGC authors with both genres;
   - PAN 2019's cross-fandom fan-fiction set (Zenodo record 3530313, version pinned at intake), as the positive control;
   - ConvoKit's per-subreddit corpora for r/WritingPrompts and r/changemyview (each from its start to October 2018), only if the policy accepts Reddit's terms.
8. **The Personal Values Dictionary** (Ponizovskiy et al. 2020), for WE1, under its published terms. Optional.

## 5. Gear 3 campaign `G3-S15-WEEK3`

- **Authority.** `AGENTS.md` requires the curator's explicit per-use approval. This campaign runs only if he states that approval when he hands over the packet; record his words verbatim in `.agent-state/drive-20261025/APPROVAL.json`. Without that statement, skip section 5. If he approves later, before Friday's cutoff, the campaign starts then, under the same caps and order. Until then no node runs, and the cards that need a node are marked blocked under S6, naming it: PP5 and PP6 (PROC), CA3 and WE1's fallback (VAL), FIC1's primary (AUTH), FIC2 (K), WC1's convergent check (GOAL) and P3c's fallback (P). None of the eighteen ready cards needs a node.
  - Total cap: $10 gross, enforced in code. Nothing past $10 runs without his detailed final approval.
  - Paid dispatch closes Friday 30 October, 17:00 PDT (2026-10-31T00:00Z).
- **Prices,** checked 25 October: Claude Haiku 5.5 through the Message Batches API, $0.05 per million input tokens and $0.25 per million output tokens, the rates `budget.py` already uses.
- **Data transfer.** On top of the 16 October packet's section 8 and the 17 October packet's section 10.5, his approval of section 5 covers sending exactly these to the Anthropic API, and nothing else:
  - **PROC:** every sentence of every CoAuthor final document, with the document's preceding sentences as context;
  - **AUTH:** pairs of typed texts, each text from one writer (her own keystrokes only), up to 400 words each;
  - **GOAL:** the 200 characters of typed text before each of 5,000 sampled long pauses. Only before: the text after shows the outcomes that define WC1's goals, which would make GOAL's agreement with WC1 partly circular;
  - **VAL:** Community Alignment explanations (public, CC-BY-4.0), and each CoAuthor argumentative session's typed text;
  - **P:** edit before-and-after pairs, as 17 October accepted;
  - **K:** SPGC fear passages (public domain).
  
  No raw text appears in public outputs.
- **Code.** In `runners/drive/budget.py`:
  - `CAMPAIGN = 'G3-S15-WEEK3'`;
  - `APPROVAL` at `.agent-state/drive-20261025/APPROVAL.json`;
  - `CUTOFF` at 2026-10-31T00:00:00+00:00;
  - `CAPS`: the node caps below, in cents. There is no Reserve node; the guard refuses one;
  - keep the 1,000-cent campaign refusal, and the approval's `first_paid_cents` of 1,000.
  
  Then:
  - write the approval file naming the nodes, with this packet's SHA-256 and the curator's statement verbatim;
  - `max_tokens` 32, thinking off;
  - reserve before every POST, and no automatic resubmission;
  - count deduplicated inputs before each reservation;
  - **reconcile before each next node.** Reservations book at ceilings. Before reserving the next node, record the last node's actual spend and release its unspent reservation, adding that step with a test if the runner lacks it. Otherwise later nodes are refused while actual spend sits near $5.
- **Known-answer rung first, for every node.**
  - The owner labels the node's first 100 items blind, as agent labels, and the node continues only past κ of at least 0.6.
  - AUTH needs no labels, since authorship is known: it continues past an AUC of at least 0.6 on its first 100 argument pairs, which FIC1's primary then excludes.
  - VAL's κ is pooled across values, and per-value κ is reported for values with at least 5% prevalence in the rung sample. Which values CA3 keeps is CA3's own rule: 5% prevalence in VAL's coded sample.
  - A node that fails its rung may have one recorded prompt fix, rerun on 100 fresh rung items. A second failure stops it, and its spend so far is recorded.

| Node | What it buys | Forecast | Cap |
|---|---|---:|---:|
| PROC | Plan roles for every sentence of every CoAuthor final document (PP5, PP6) | about $1.20 | $2.00 |
| VAL | Schwartz's ten values in a frozen sample of up to 10 explanations per annotator in CA1's population (about 30,000, seed 20261026), and in each CoAuthor argumentative session's typed text (CA3, WE1) | about $1.00 | $2.50 |
| K | D31's fear-passage codes (FIC2) | about $1.50 | $2.50 |
| AUTH | 4,000 same-author pair judgments (FIC1) | about $0.30 | $1.00 |
| GOAL | Goal-of-the-moment labels for 5,000 sampled long pauses, from the text before each pause: WC1's five goals plus "other" (convergent validity for WC1) | about $0.25 | $0.50 |
| P | Second labeler for P3c, only if its classifier fails | about $0.40 | $0.50 |

**Order:** PROC, VAL, AUTH, GOAL, then K once FIC2's intake lands, then P only if needed. The caps total $9.00, under the $10 campaign cap. The forecast total is about $5.

## 6. Backlog, idle slots only

**Holds lifted.** This packet lifts the cumulative cost holds on these cards, for idle slots only.
- Each may run to its last recorded full projection plus 50%, logged.
- A card without a recorded projection gets a one-hour cost probe first.
- CPU only. Anything that needs the GPU stays held.

**Order:**
1. **The DR1 controls.**
   - Use a randomization test, not label permutation. The three orders aren't exchangeable: the random arm averages 200 orders while the other two are single sequences, and date order is already known to be slower. So for each writer, rank the directed sequence's sessions-to-identification among that writer's 200 random orders (the banks DR1 projected), and do the same for date order. Combine ranks across writers: the mean rank against its uniform null. Sessions-to-identification has heavy ties, so break ties at random (seeded) and report the mid-p. The primary is style: the directed sequence's rank among the random orders, where a low rank favours directed. Validate the test's size first on a no-effect plant, where order can't matter. The 1,000-permutation minimum is for identification accuracy, not for this contrast.
   - Section 0.4's context-only reference replaces its fake-writer bank.
   - Build a cheaper exact implementation first if that takes under 2 hours of agent time; otherwise run the existing one. Its last full projection was about 31,000 wall seconds.
2. **D37,** the three entries (page, person, process), as specified on 17 October, without its V5 headroom share (errata rule 6).
3. The D33 calibration-supported corpus run.
4. P7 refinement.
5. D7, D36, D19, D5, D10. (D9 is dropped: CA1, CA4 and CA5 supersede it on the same data.)
6. V4.c's 199-null Monte Carlo reference.

## 7. Cross-repository

| To | What | When |
|---|---|---|
| Ghost, via `docs/exchange` | WB1's piece classes and their standardised mean effects on its four effect measures, for W5 | By Wednesday 28 October, 12:00 PDT (19:00Z) |
| Ghost | PP1's pause hierarchy; FR1's and WC2's results; TR4's volatility distribution, for W6 to W8's calibration | As each lands |
| ToMpathy | The claim-ledger rows that license or change a badge. WA0's figures. The EV1 and EV2 export's reader identity (model revision and manifest sha256). PP1, PP2, PP3, PP5 and PP6's definitions and results. WB1's alphabet, pieces and classes; WB3's population rates per situation. WC1's goals, β, ρ and progress table. WD1's definitions. TR4's adaptive rate, with its definition (a population distribution of rates, or a per-writer filter) | The reader identity by Monday 26 October, 20:00 PDT; the rest as each lands |
| From Ghost | W1's alias map and W2's readout failure rate (Thursday 29 October, 12:00 PDT); W4's records-needed curve (Saturday 31 October); W6's and W7's results, as which conditions carry information and how many records are needed (not effect sizes, whose units don't carry over); W8's adaptive-reader advantage (for TR4) and W10's dose-response shapes (for TR3) | Read them in the final digest. No card waits on them |

**Approval for this week's copies.** Handing over this packet approves this week's aggregate-only copies into Ghost's `docs/exchange` and into a ToMpathy `docs/` folder named for the card. Follow EV4's delivery procedure: copy, hash and record. Don't commit or push in the recipient repository.

## 8. Reporting

- **Daily digest at 20:00 local time:**
  - corrections first;
  - idle slot-hours;
  - Gear 3 spend against caps;
  - each landed card with its ledger id, control status and follow-ups registered.
- **Final digest:** Sunday 1 November, 20:00 PST.
  - Positives first, each with its ledger id and control status.
  - Then a one-page map of the pyramid: what the record can and can't see at each level.
- **Drain addendum** by 23:00 PST: results that land between 20:00 and the 22:00 drain.
- **Theory filing** at the next digest, under the theory format rules and `tools/theory_lint.py`:
  - Appendix A (the curator's 25 October morning model);
  - Appendix B (his 25 October walk);
  - Appendix C (his 21 October positions).

## 9. Pre-mortem

- **The queue runs dry again.**
  - *Guard:* eighteen cards are ready at handoff, follow-ups are automatic, and the backlog's holds are lifted.
- **Timing cards read typing skill, typos or interface events as attention.** Within-word intervals mostly index skill. Capitals and punctuation add keystrokes. Language fixes dominate revisions. A missing pause isn't missing attention, because planning can run in parallel with typing (Roeser et al. 2025).
  - *Guard:* the family's timing rules, the mechanical indicator, and PP4's filter.
- **CoAuthor's event timing can't see the pyramid.**
  - *Guard:* PP1 tests that first, and its fallbacks run only what their structure allows.
- **Pieces are the task, not the person.**
  - *Guard:* WB2's context-only reference, and section 0.4's permutations.
- **Pieces are just the grammar, or drift within a session.**
  - *Guard:* Markov surrogates, the per-third sensitivity, and coverage measured on held-out writers.
- **The goal set is ours, and may be wrong.**
  - *Guard:* the Markov chain as WC1's primary comparator, drop-one-goal sensitivity, and GOAL's labels.
- **Community Alignment's choices reflect the candidate set, not the annotator.**
  - *Guard:* within-prompt permutations (or CA0's fallback), and the country reader as the baseline for "own".
- **VAL's codes put words in annotators' mouths.**
  - *Guard:* the known-answer rung, and CA3 predicts held-out explanations only.
- **FR1's dismissal runs are boredom or a bad model, not a blocked want.**
  - *Guard:* the post-event distance from the dismissed offers (a blocked want sends her somewhere else; boredom doesn't), and the support count.
- **WC2's picks are generic or on topic,** so anyone's next words resemble them.
  - *Guard:* the context-only reference.
- **A lingering taste passes for a surviving end.**
  - *Guard:* WC2 routes on phrase overlap: "same end, new means" needs embedding similarity above context with shared bigrams and trigrams inside the band. Content-word overlap is only descriptive, since a paraphrase keeps the key nouns.
- **PR1 mistakes predictability for paying.**
  - *Guard:* the examined-against-fast contrast, and the context-only reference.
- **TR3's index measures topic drift, not capture.**
  - *Guard:* features chosen on WB1's discovery writers, a frequency-matched placebo, prompt as a covariate, and the randomized holdout at Tier 4.
- **TR5's long runs regress toward her mean and read as a trust drop.**
  - *Guard:* matched non-failure controls with the same run length, and "kept" judged at the moment of the failure.
- **Section 5 isn't approved at handoff.**
  - *Guard:* node-dependent cards block under S6, and the eighteen ready cards need no node.
- **A thin event set reads as a null.**
  - *Guard:* support counts before freezing, with "unsupported" routed apart from null.
- **Gear 3 reservations at ceilings refuse late nodes.**
  - *Guard:* reconcile and release before each next node.
- **Follow-ups crowd out the packet.**
  - *Guard:* the caps, one generation only, and their rank below the packet's own cards.

## 10. Triggers (the only reasons to contact the curator)

1. A paid spend would pass $10.
2. Privacy: any writer, annotator or rater identity, or raw text, would leave the repository other than through section 5's nodes.
3. A result reverses a delivered public claim, including a WA0 correction to a figure shown at the 22 October talk.
4. The machine is unavailable for more than 12 hours.

## Appendix A: the curator's model, 25 October morning

1. Inference is probably less a pyramid than a reuse of puzzle pieces: preset series of actions with inputs, outputs and expected outcomes.
2. What matters is correctly identifying the outcomes of a given structure. The structure may be a core drive (Panksepp) or a dearly held learned structure, such as natalism or republicanism. Each is a set of parameters optimising for an external value.
3. From that, estimate the distribution of higher-order goals a person optimises for, and her divergence from the population mean. Find which needs she uses at a higher or lower rate than optimal.
4. The central target is whatever humans do to know someone well enough to decide whether to trust them, and so to update their own weights from that person.
5. A person can know someone and still decline to engage with that person's bad parts, to preserve their own weights.

## Appendix B: the curator's walk, 25 October

Condensed from his own statement.

1. **Drive signatures carry wants.** Panksepp's systems have transformations that fit only certain outcome types; anger only fires when you want something. So records without designed variation can still show ends.
2. **The product need is the process, not values.** Core values matter only if uptake must be moderated. What's needed is to fill out a process pyramid, mark divergences from it as candidate attention, and track current attention as following the active higher-order process (for example, "a paragraph about X" in a three-paragraph format).
3. **The fiction null is more likely the environment.** "You find the author in fiction" seems well established to him, and fiction may also draw more empathic people.
4. **Trust** is an accurate current projection of someone's transition map (their expertise, including distorting structures like racism) plus how similar their ends are to yours. Past choices are only evidence.
   - He notices he tends to assume even the worst historical actors shared humanity's core goals and erred in means, and flags that assumption as possibly wrong.
   - If ends are shared, even kindness can be a failure to optimize.
5. **The top of the chain** may be persistence, with humans as imperfect optimizers of it; it stays hazy to him.
6. **Betrayal hurts** because you learn the person would do it again; "the math converges on you being alone", which engages grief and separation distress and sends you to others.
7. **Dearly held structures.** Besides the midbrain's ready-made solutions, people craft simpler solutions in the neocortex (honor, for example). These can become ends, as each person's guess at serving the top of the chain.
8. **Attention reveals goals.** Divergences in attention, the System 2 second look, may identify the higher-order goals people serve most, such as catching one's own micro-racisms.
9. **Ends show in sacrifice.** You know something is an end by what you'd sacrifice for it, and that should be readable at a micro level.
10. **Departures from one's group** show individual preference when they are consistent over time; the group sanding them down is part of how to see them, because resisting it costs something.
11. **Filtering** works on parts of the transition map. Its mechanism is declining to run inferences about someone: a quick dispositional label instead of modelling their reasons. Its cost is attention.
12. **Indoctrination** is the sense that something "might make sense sometimes", plus repetition until it becomes the default autocomplete in flow. Absorption shows as automatic behaviours you weren't attending to.
13. **A useful move bundled with an unwanted end** can be taken if it can be repurposed and the unwanted end starved.
14. **A track record has a "Heisenberg" problem.** More confidence about the lifetime trajectory means less about what someone wants now. He wonders whether that difficulty is itself an anti-capture mechanism.

## Appendix C: the curator's positions, 21 October

Condensed from his own statement. Two tangential remarks are left out, and some wording is shortened.

1. **The goal.** Define the need, the bad state, that each Panksepp system is a tool against. Establish the needs, at least roughly.
2. **The method.** Assume a need, then track how often people use each system, to get a gradient of those needs. First establish that there's any signal at all.
3. **People do the same calculation.** We have only a person's actions and tools. Add the stimulus and the situation, including habits, and their decisions show what they're trying to do. One reading of an action is a weighted sum of the motivations in view, each weighted by how likely it is to be relevant.
4. **FEAR and RAGE are amplifiers.** They turn other wants up or down. Their lesser forms work the same way: irritation fires when a want is stymied.
5. **Emotions run automatically,** with an associative pull toward the situations that call for them. Anger can run partly without awareness.
6. **PLAY** is a need to learn about the world when uncertainty is high in general. Uncertainty in a safe environment switches it on; FEAR blocks it.
7. **CARE is "the opposite" of play.**
   - It tracks responsibilities and folds others into one's own decision tree.
   - Its core is noticing an unusually good solution and wanting to share it. That feels like a want for appreciation or respect, and being copied gives confidence that the solution is better.
8. **SEEKING has to differ from RAGE,** or there would be one channel. Off the cuff, SEEKING is a scalar pointing at a want.
9. **What to learn:** what fires each channel, and especially the nuances people find confusing.
10. **LUST is its own evolutionary system,** like FEAR and RAGE, and probably deeper than the rest.
11. **PANIC/GRIEF.** Its name may mislead. Assume it isn't understood yet.
12. **LUST and PANIC/GRIEF can't simply be parts of one copying network.**
13. **Phylogeny as a clue.** When each system appeared would hint at its use. Only LUST, and perhaps PANIC/GRIEF and CARE, look datable that way.
14. **The channels are largely genetic and somewhat learned.** So read deviations in how a person uses them, given the situation.
15. **"The wanting-to-want attentional channel is the key."**

## Sources

- [Sutton, Precup & Singh 1999](https://doi.org/10.1016/S0004-3702(99)00052-1)
- [Botvinick & Plaut 2004](https://doi.org/10.1037/0033-295X.111.2.395)
- [Baker, Saxe & Tenenbaum 2009](https://doi.org/10.1016/j.cognition.2009.07.005)
- [Todorov & Jordan 2002](https://doi.org/10.1038/nn963)
- [Mischel & Shoda 1995](https://doi.org/10.1037/0033-295X.102.2.246)
- [Behrens et al. 2007](https://doi.org/10.1038/nn1954)
- [Adams & MacKay 2007](https://arxiv.org/abs/0710.3742)
- [Pimentel & Meister 2024, "How to Compute the Probability of a Word"](https://arxiv.org/abs/2406.14561)
- [Zhang, Milli et al. 2026, the Community Alignment dataset (ICLR 2026)](https://arxiv.org/abs/2507.09650)
- [The Community Alignment dataset card](https://huggingface.co/datasets/facebook/community-alignment-dataset)
- [Le et al. 2025, ScholaWrite](https://arxiv.org/abs/2502.02904)
- [Ponizovskiy et al. 2020](https://doi.org/10.1002/per.2294)
- [Lee, Liang & Yang 2022, CoAuthor](https://doi.org/10.1145/3491102.3502030)
- [Medimorec & Risko 2017](https://doi.org/10.1007/s11145-017-9723-7) (abstract)
- [Roeser et al. 2025, "Typing in tandem", Journal of Experimental Psychology: General 154(7)](https://par.nsf.gov/biblio/10614280) (abstract)
- [Révész et al. 2019](https://doi.org/10.1017/S027226311900024X)
- [Hayes & Flower 1983](https://www.smsu.edu/resources/webspaces/academics/collegenow/ED240608.pdf)
- [Crossley et al. 2022, PERSUADE](https://doi.org/10.1016/j.asw.2022.100667)
- [Ulasik et al. 2025](https://doi.org/10.17239/jowr-2025.16.03.05)
- [Tian, Crossley & Van Waes 2025, KLiCKe](https://doi.org/10.17239/jowr-2025.17.01.02)
- [The KLiCKe corpus repository](https://github.com/terryyutian/KLiCKe-Corpus)
- [The IteraTeR intention classifier's configuration](https://huggingface.co/wanyu/IteraTeR-ROBERTA-Intention-Classifier/blob/d9e6e6ee893e9f36cbba8047b838ccbfea1c1c32/config.json)
- [Borji & Itti 2014](https://doi.org/10.1167/14.3.29)
- [Greene, Liu & Wolfe 2012](https://doi.org/10.1016/j.visres.2012.03.019)
- [Wu et al. 2018](https://doi.org/10.1111/cogs.12548) (abstract)
- [Houlihan et al. 2023](https://doi.org/10.1098/rsta.2022.0047) (abstract)
- [Kuppens et al. 2003](https://doi.org/10.1037/1528-3542.3.3.254) (abstract)
- [Berkowitz 1989](https://doi.org/10.1037/0033-2909.106.1.59) (abstract)
- [Liu et al. 2017](https://doi.org/10.1126/science.aag2132)
- [Westbrook, Kester & Braver 2013](https://doi.org/10.1371/journal.pone.0068210)
- [Kiesel et al. 2022](https://doi.org/10.18653/v1/2022.acl-long.306)
- [Jakesch et al. 2023](https://arxiv.org/abs/2302.00560)
- [Williams-Ceci et al. 2026](https://doi.org/10.1126/sciadv.adw5578) (abstract and press release)
- [Padmakumar & He 2024](https://arxiv.org/abs/2309.05196)
- [Diaconescu et al. 2014](https://doi.org/10.1371/journal.pcbi.1003810)
- [Schweitzer, Hershey & Bradlow 2006](https://doi.org/10.1016/j.obhdp.2006.05.005)
- [Goldstein-Stewart et al. 2009](https://aclanthology.org/E09-1039.pdf)
- [Kestemont et al. 2012](https://www.clips.uantwerpen.be/~walter/papers/2012/kldc12.pdf)
- [ABC-NL1, 2000](https://dh-abstracts.library.virginia.edu/works/21)
- [PAN 2019 cross-domain authorship attribution, Zenodo record 3530313](https://zenodo.org/records/3530313)
- [ConvoKit's subreddit corpora](https://zissou.infosci.cornell.edu/socialkit/documentation/_sources/subreddit.rst.txt)
