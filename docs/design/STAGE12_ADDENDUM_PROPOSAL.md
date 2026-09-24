# Stage 12 addendum: validity, evidence revision and human-record breadth

**PROPOSAL, September 23, 2026. Planning only; not an execution manifest or new
compute authorization.** Requested by the curator before the Friday discussion.
Two bounded GPT-5.6 Terra engineering reviews informed this plan; their claims
were checked against source code, receipts and primary literature. No new model
call, fit, scientific score or paid invocation was made during planning.

## Recommendation and the failed pilot

Implement three local priorities: complete failure/dependency accounting,
broaden the human review/edit comparison, and test revision of an explicitly
saved answer against a fresh reading of the same updated evidence. A small
answer-binding control is a conditional fourth priority. Separately offer one
cap-only repair of the cloud human-history interface.

The failed human-history pilot was **Modal/Qwen3.5 27B**, not the local 9B test.
All twelve requests returned; one reached its 512-token output allowance before
finishing the probability distribution. The unchanged all-valid gate correctly
withheld all 159 main requests. The full archive and original $3 reservation
remain. This is an interface-validity failure, not a completed test of whether
human history helps. See the [pilot inspection](../../results/phase_2_4_stage_12/CLOUD_PILOT_INSPECTION.json)
and [implementation handoff](STAGE12_IMPLEMENTATION_HANDOFF.md).

The existing local roster is complete, with 88 completed job records audited,
48 Stage 12 tests passing and 21 locks verified in the latest completed audit.
That establishes record integrity for those jobs; it does not establish every
scientific hypothesis or fill the unavailable human-history comparison.

The original [week commission](PHASE_2_4_STAGE_12_CONTEXT.md) still controls:
Gear 2, original cumulative limits, single GPU owner, serial CPU work, shared-fit
ceiling and final-packet policy. Friday September 25 at 06:17 PDT is the recorded
interim review; Monday September 28 at 06:17 PDT is the final review, with
protected reporting beginning Sunday at 18:17 PDT. This proposal aims to make
useful complete comparisons ready Friday without silently changing that calendar.
The curator's reference to a Friday final check-in is awaiting clarification.

## What the additions would resolve

This table ranks proposed work. Calls are maximum new local requests, not
independent observations. Each comparison retains failures and its own source scope.

| Priority | Question and intended contribution | Proposed support | Calls |
|---|---|---|---:|
| A, required | Does the interpretation survive honest treatment of failures, dependencies and assistance? | Existing complete records and provider cases | 0 |
| B, core | Does the direct/account comparison survive broader human paper support and an honest lexical rival? | Up to 16 additional ARIES papers, one comment and one positive/negative pair per paper | 128 |
| C, core | Does a saved prior answer change the reader's response to genuinely diagnostic new evidence? | Eight constructed histories, direct/account, saved-answer/fresh read and three update types | 112 |
| D, conditional | Is successful supplied-answer use stable under labels, ordering and distractors? | Four constructed histories, two queries, six conditions | 48 |
| E, separate paid option | Can the original human-history comparison run through a valid, uniformly larger output interface? | Same 171-request human roster, new twelve-request pilot plus conditional 159-request main | 0 local; 171 cloud |

A failure or null is useful if the controls work. None of these cards is intended
to turn an unfavorable result into a favorable one. Known apparatus faults are
repaired prospectively; earlier attempts and their original judgments stay visible.

## A. Failure accounting, support map and interpretation cases

Build a zero-call consumer over the existing immutable records. Reuse the
source replay and five-arm human replay in `runners/stage12/studies.py`.

1. Join planned, attempted, returned, literal-valid, scored and whole-comparison
   counts. Identify selected recovery versus original incomplete attempt without
   counting both as independent support or hiding either cost.
2. Preserve original all-attempt penalties, infinite logarithmic losses and
   unavailable fields. Add a clearly secondary complete-pair view beside them;
   never replace the original estimand by conditioning away invalid responses.
3. Map each comparison to its actual support: writer/donor component where
   available, paper, constructed history, shared finite law, repeated request,
   coefficient reweighting or privileged supplied answer. New prompts and new
   seeds do not create new people or independent worlds.
4. Keep probability error, located supported events, unsupported claims, coverage
   and cost separate. Do not convert fluent explanations or self-reported
   confidence into independently verified reconstruction.
5. Assemble eight case slots selected by evidence condition and source identity,
   before inspecting addendum outcomes: artifact-only; correct context;
   misleading context; witnessed process; ambiguous process; cheap rival;
   supplied-answer execution; failed or invalid reading. Include the full source
   denominator and an outcome-independent case alongside any illustrative error.

The existing 254-case bundle remains unchanged; this is a linked interpretation
guide and audit, not a replacement sample. Keep passages private. Missing mental
goals remain unknown. This supplies useful texture even if every new GPU card
fails admission. Expected implementation/review effort: two to four active hours.

## B. Broader human review/edit correspondence

**Hypothesis:** the current account/direct contrast may be sensitive to the
small paper sample and to lexical matching. Method: preserve the two existing
question formulations and direct/account interfaces on prospectively selected
additional papers, with a common within-comment ranking comparison.

Source inspection found 42 papers and 196 test label rows. Thirty-six papers
retain at least one positive/negative comment group under the existing 4,200-byte
input rule. After excluding all previously compiled paper identities, 32 such
papers remain in this inventory. This is an eligibility count, not proof of
absence from every earlier exposure register; complete that join before freezing.
Do not expose candidate model outcomes during selection.

The primary paper identifies the expert-annotated test set and explicitly
defines its negative pairs. The separately named human-evaluation file is a
restricted-information human baseline, not a prerequisite for using test labels.
Train/dev silver omissions are not negatives. Pin the existing test file and
retain only its explicit negative IDs. No new human annotation or corpus is
needed. [ARIES, sections 4.3 and 5](https://arxiv.org/html/2306.12587v2),
[official data contract](https://github.com/allenai/aries#dataset).

Proposed freeze:

- Select up to sixteen additional eligible papers by a fixed seeded hash after
  the exposure census. Within each paper select one eligible comment and one
  explicit positive and one explicit negative edit by fixed hash. Keep a complete
  exclusion ledger, including insufficient length-qualified support.
- Run both question formulations crossed with direct/account: eight calls per
  paper, 128 maximum. Preserve the existing evidence projection, package,
  temperature, seed, output budget and parsing. Both formulations classify a
  supplied pair; neither generates a new edit.
- Retain prior four-paper outcomes as exposed development. Report new-paper and
  combined descriptive results separately. Paper weighting is primary for this
  extension; pair weighting is a visible sensitivity. Author components remain
  unavailable, so paper groups are not asserted to be independent people.
- Compare lexical overlap and all four model arms on exactly the same
  positive-versus-negative ranking pairs. Count ties explicitly. Lexical overlap
  is not a calibrated probability and gets no invented Brier score. Retain
  probability losses, invalid penalties and uniform references for model arms.
- Add offline controls: swapped paragraph indices, omitted back matter, duplicate
  edit IDs, unlabelled edits, null text and label leakage must fail or remain
  unknown as appropriate. Known lexical ties and perfect/reversed rankings
  validate the ranking consumer before unknown data are interpreted.

This increases human-record breadth and tests whether a cheap retrieval account
explains the result. It remains a small annotation-balanced descriptive sample,
not natural prevalence, private intention, author adoption or a powered test of
the original human-history primary margin. If the broader contrast reverses or
depends on weighting, preserve that instability; do not select a winning prompt.
Expected adapter/consumer work: roughly four to six active hours, reusing
`runners/stage12/aries.py` rather than adding another source adapter.

## C. Actual response revision versus fresh rereading

**Hypothesis:** new evidence can help a fresh reader while an explicit saved
answer obstructs or helps revision. The existing context battery makes fresh
independent requests; it cannot identify this difference.

Freeze eight additional constructed histories from the existing admitted family,
not eight repetitions of an identical endpoint request. Use one nonconstant
query per history. Assign four truthful and four misleading initial frames by
fixed counterbalancing before reader outcomes. The primary comparison is paired
within a history/frame; this design does not estimate a fully crossed causal
effect of frame truth across every history.

For each history and each of direct/account output modes:

1. Obtain and preserve one initial reply.
2. Form three later evidence snapshots: unchanged evidence; diagnostic additional
   observations; and length-matched irrelevant material that leaves the exact
   target unchanged.
3. At each snapshot compare a prompt quoting the exact saved initial reply with
   a fresh prompt containing the same task evidence and frame but no saved reply.
   All calls use the same fixed model, decoding and output limits. Saved replies
   are quoted as fallible previous output, not instructions or authoritative facts.

That is seven calls per output mode, fourteen per history, 112 maximum. Preserve
an invalid initial reply as an invalid response and quoted record; do not repair
it or silently drop its subsequent comparisons. Counterbalance condition order.
The treatment is explicit response carryover, including its added text; a
psychological anchoring mechanism or persistent hidden state is not isolated.

Before any reader dispatch, exact programs must establish that the diagnostic
update changes the relevant conditional distribution, the irrelevant update
does not, the initial frames have their stated relation to public evidence,
and the query/conditions have nonconstant dynamic range. Frame truth cannot be
defined solely by evaluator knowledge unavailable to the reader. Fail compilation
if these controls cannot be realized; do not relabel arbitrary extra text as
diagnostic evidence.

Score saved-versus-fresh loss at the **same later evidence snapshot**, plus excess
loss above that snapshot's exact reference floor. Separately retain movements
toward/away from the new reference, modal corrections/damage, invalids, zero
support and costs. Comparing raw pre/post losses alone confounds reader changes
with changes in target difficulty. Evidence correction, unchanged rereading and
irrelevant-text effects must remain distinct. Do not grade free-form psychological
claims with an unvalidated new extractor.

This can distinguish evidence-use failure from response carryover, including a
null where both routes behave alike. It cannot establish a human updating
mechanism or another source law. Expected implementation and control work:
roughly six to ten active hours; this is the highest-risk engineering card.
Use `context_battery.py`, exact references and the existing raw/handler replay
contracts. If the instrument fails its offline gate, land the scoped refusal and
continue A/B rather than spending the remaining week tuning it.

## D. Small answer-binding diagnostic, only after the core

Use four prospectively named histories and two queries each. Six paired
conditions: canonical full-bank copying; identical repeat; permuted bank-entry
order; consistently permuted output-label order; inserted irrelevant entry; and
a deliberately wrong supplied vector. Total 48 calls. Keep input transformations
and evaluator inverses exact, output budgets matched and every condition present.

The wrong vector is an assistance-quality negative control: faithful copying
should preserve the supplied vector while task correctness degrades. It is not
an instruction to expect the reader to discover that the supplied answer is
wrong. Score literal fidelity separately from inference loss. Validate exact
copy/permutation procedures first; ensure the wrong vector actually differs from
the target. This identifies fragile binding versus information availability,
not understanding or recovered maker state. Existing histories remain exposed
constructed diagnostics. Estimated engineering: three to five active hours.

## E. Optional cloud repair, a separate concrete decision

Change **only the output cap, 512 to 2,048**, uniformly on the same 171-request
roster. Keep model/image/server, evidence, prompts, schema, parser, seed and
`think=False` unchanged. Do not combine the old eleven valid pilot replies with
new-cap main replies. Use a new immutable interface version and namespace;
retain the old pilot and its charge as a failed attempt.

Proposed aggregate reservations remain at most **$20**: original $3 retained,
new pilot at most $3, conditional main at most $13, protected reserve $1. This is
a revised allocation, not permission inferred from the earlier conditional tree.
It requires a new exact per-use approval through `gear3.py`, fresh account and
provider-rate evidence, and a guard summing both old and new namespaces.

The retained reviewed resource rate is $2.301264/hour; it is not a fresh quote.
Existing cost code adds fifty cents to the rounded resource reservation. Under
that code, a new pilot's slowest call at most **79.2 seconds** permits a $13 main
reservation using the existing 1.5x timing allowance and 660-second fixed margin.
Enforce the computed dollar cap too; the rounded threshold is not a substitute.
The pilot must have twelve of twelve literal-valid replies and complete replay.
Otherwise stop, retain the whole reservation, and do not retry or start main.

The old pilot's retained call-wall total was about 125 seconds, excluding startup
and lifecycle; this is not an invoice or a guaranteed new runtime. A larger cap
can materially lengthen replies. The new pilot reservation is 65 minutes; the
$13 main is bounded at about 5.43 hours at the retained rate. Whole-job deadline
admission and fresh pricing can make this option unavailable.

Before approval is requested for dispatch, implement/review offline refusal
fixtures for truncated JSON, length termination, cap/version mixing, duplicate
invocation, changed raw archive, total reservations across both namespaces,
insufficient account headroom and expired deadlines. No new provider, wider
human upload, hidden evaluator labels or automatic second repair is proposed.

## Capacity, scheduling and review points

The [last completed capacity receipt](../../results/phase_2_4_stage_12/EXECUTION_COMPLETE_STATUS.json)
leaves about 24.05 CPU-process hours and 30.26 GPU-service hours after protected
reporting reserves. These are remaining original allocations, not new grants.
Reconcile fresh charges before execution. Keep the diagnostic one-hour ceiling
and original thermal, headroom, ownership and matched-throughput checks.

This table uses the existing conservative 330 seconds per call plus 120 seconds
per worker block. CPU allowances include a separate 600 seconds per GPU block;
wall limits retain the existing additional supervision allowance.

| Proposed local scope | Blocks | GPU reservation ceiling | CPU preparation/worker allowance |
|---|---:|---:|---:|
| A, setup and validation | CPU only | 0 | 3 hours total |
| B, sixteen paper blocks | 16 | 12.27 hours | 2.67 hours |
| C, eight complete history blocks | 8 | 10.53 hours | 1.33 hours |
| D, four optional history blocks | 4 | 4.53 hours | 0.67 hours |
| All proposed local work | 28 GPU blocks | 27.33 hours | 7.67 hours |

Thus even the conservative full local reservation leaves about 2.93 GPU hours
beyond the already protected reporting reserve. Any admission warm-up, failure
or recovery consumes that remainder and the applicable diagnostic allocation.
No fallback may spend the reporting reserve. These are service ceilings, not
elapsed completion promises or a requirement to occupy the device for that long.

For context, the completed access blocks took 78.6-83.9 seconds **per seventeen
calls**, roughly 4.6-4.9 seconds per call across their mixture. Historical healthy
account calls were longer. If comparable healthy classes persist, new model
service for the core should be on the order of one to a few hours; engineering,
source checks, replay and packet preparation are the larger calendar risks.
Do not plan from the mistaken interpretation of 80 seconds per individual call.

After implementation approval, freeze the full roster and conditional successor
order before outcomes. Start B in four-paper waves while C's offline controls
are prepared; then interleave complete C blocks with remaining B waves. Keep
CPU work serial and one native GPU owner. Reconcile actual charges and whole
next-wave worst-case wall fit at every boundary. Advancement depends on validity,
resources and time, never a favorable scientific effect. D is lowest priority.

Recommended Friday preparation target: finish new generation by Thursday
September 24 at 22:00 PDT, leaving about eight hours for reconciliation and the
06:17 review. This is an addendum scheduling target, not a rewrite of the original
week deadline. A late approval, slow calls or failed construction can prevent
the whole roster finishing by then. Do not promise otherwise or omit unfinished
cells; freeze the interim snapshot with explicit missing work. If Monday remains
the final cutoff, only the already frozen remainder may continue afterward,
subject to original admission and reporting protection. If Friday becomes final,
revise the finite admission before launch to fit it.

Review points for the curator:

- **Now:** choose the local core and whether the separately scoped cloud repair
  is wanted. Planning completion itself launches nothing.
- **After offline admission:** operational readiness or a concrete source/ruler
  blocker, ordinarily within the first working day after approval. Routine
  implementation does not require repeated approval.
- **Friday morning:** complete comparisons, eight source-bound cases, support
  map, failures and unavailable lanes. No unfinished per-artifact score reports.
- **Original final packet:** retain Monday unless the curator changes it.

Four-hour native queue-health inspections continue independently. New queues
must register completion/failure delivery, preserve cumulative accounting and
require full internal write-through before ACK. A healthy completed or deliberately
parked queue is not an invitation to launch unapproved work.

## Literature and rejected alternatives

Primary sources were fetched and read for the following scoped design checks;
this proposal makes no novelty claim and imports no replacement theory vocabulary.

- **ARIES** sections 4.3, 5 and 5.3-5.4: expert test labels, lexical/delta confusion,
  parsing artifacts and paper weighting motivate B and its source controls.
  The original paper already studies alignment; our question is the local
  account/direct contrast on broader support, not discovery of alignment itself.
  [READ](https://arxiv.org/html/2306.12587v2).
- **Lost in the Middle**, introduction and retrieval experiments: controlled
  placement effects and task differences motivate D. A short answer bank here is
  not a reproduction of its long-context experiments.
  [READ](https://arxiv.org/html/2307.03172v3).
- **Large Language Models Cannot Self-Correct Reasoning Yet**, experimental
  setup and discussion: distinguish intrinsic correction from supplied external
  evidence and use matched prompts/budgets.
  [READ](https://arxiv.org/html/2310.01798v2).
- **Large Language Models have Intrinsic Self-Correction Ability**, correction
  experiments and reported prompt/model dependence: counterweight to treating a
  negative correction result as universal. Card C tests a specified protocol,
  not the title-level dispute.
  [READ](https://arxiv.org/html/2406.15673v1).

Do not add another tiny-model fit, an unadmitted joint neural composition,
another provider/model sweep, invented negatives, a broad positional grid or
more coefficient-weighted copies of the same forecasts merely to fill time.
The strongest objection to this plan is that more local model diagnostics cannot
repair missing capable-reader human-history evidence or source independence.
That is why B adds actual paper support, E remains separately visible, and A/C/D
retain their narrower validity and interpretation roles. No theory definition
or existing scientific status changes on the strength of this proposal.
