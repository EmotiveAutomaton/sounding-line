# IN12: common self-report association and prompt-specific departures

Prospective implementation of the two-day packet, section 3B. The packet
authorizes this test. Its named R13–R15 supporting handoffs are absent locally;
their missing contents are not inferred. The common-band interpretation is the
thread's proposal awaiting ruling. This test does not equate a prompt with a
biological channel or distinguish one cause from several correlated systems.

## DESIGN CHECK

Read LESSONS sections 2–5 and CONTROLS sections 6–7. The case is a common
association across six prompted negative emotions versus uneven associations.
The exact two inventory items, their direction, a common planted slope 0.2,
mixed slopes 0.4/0.4/0/0/0/0 and a zero plant check the instrument first. All
supported panels use 2,000 complete writer resamples and independent row-level
replay. Original qualified appraisal tables remain unchanged. Smaller route:
only an owner-frozen whole-writer sample under amendment E after a measured
in-slot forecast; no silent subsampling or dropped failed draws.

## Documented source and privacy

The existing pinned Crowd-enVENT ZIP and complete original IN-source are the
inputs. Read only its new `anxious` and `calm` values with private text/writer
join keys; original intensity, confidence, prompt and nine response-style
items come from the qualified numeric table. No demographic columns, other
personality items, narrative text or prior-emotion columns are loaded.

The packaged readme cites Gosling et al. (2003), DOI
10.1016/S0092-6566(03)00046-1, and defines personality scores on a 1–7 agreement
scale. The blank generation questionnaire, round 2 anger, page 13, states
“Anxious, easily upset” and “Calm, emotionally stable.” Its member SHA-256 is
`51df6525820fc973d2e45019d316ed56d35198f5804491c31ee05d93b372a068`.
N = (anxious + 8 − calm) / 2, retaining the original 1–7 item points.
The readme documents source authors' copying/averaging of repeat respondents'
item answers. This implementation accepts one unique complete pair per writer,
uses it for that writer's qualified records and reports missing/conflicting
pairs separately. Conflicts are not resolved by an outcome-dependent choice.
All original qualified rows remain in the private projection with support flags.
Only aggregate dispositions are publishable. CC BY 4.0; cite
Troiano et al., DOI 10.1162/coli_a_00461; derived numeric projection acknowledged.

## Exact fits and units

Within each prompt, intensity is centered and divided by its sample SD among
writers with complete unambiguous two-item scores. These full-source scales
define the fixed metric for all resamples. Constant prompts are unsupported.
No personality z-scoring occurs. The primary slope therefore measures intensity
SD per one N item point, with the packet bar 0.10.

The pooled six-negative fit (anger, disgust, fear, guilt, sadness, shame) has
prompt intercepts, N, confidence and the mean of the original nine response-style
items: suddenness, familiarity, predict_event, goal_relevance,
chance_responsblt, self_responsblt, chance_control, attention, effort. It uses
every eligible report. Each resample carries every report from each sampled
writer and refits all slopes; prompt scales remain fixed. At least 20 independent
writers are required for a population claim. Fewer give a pooled descriptive
fit; fewer than two give unsupported. Missing negative prompts make the pooled
fit descriptive rather than the complete six-prompt primary.

Secondaries: the six separate negative slopes with the same controls; their RMS
departure from the pooled slope; joy and pride slopes. These are descriptive.
The owner accepted RMS and raw-N units prospectively, before any response read.

If at least 300 eligible writers supply two distinct negative prompts, average
standardized intensity within each writer/prompt first. Form all ordered
distinct-negative pairs and all negative–joy/pride pairs for those writers.
Each writer contributes unit total pair weight separately to each pairing.
Report weighted Pearson correlation for each pairing and their difference,
with whole-writer resampling. Record distinct contributing writers and pair
counts separately. Fewer than two independent writers in either pairing refuses
uncertainty; fewer than 20 is descriptive. This is cross-prompt paired-report
association, not a within-person time-series correlation or a mechanism.

## Computation, controls and interpretation

Production uses writer sufficient statistics and solves each weighted design;
independent replay constructs weighted individual rows and uses a separate
least-squares solver. Source joins/item construction and interval/SE formulas
also replay independently. A rank or numerical failure remains at its original
draw index. Any failed draw prevents that panel's interval; no replacement draw
or selected-valid-subset interval. The primary stays separate from missing
secondary support. P's sees/supports-at quantities use full bootstrap SE and
are explicitly normal approximations.

The constructed suite covers both packet plants and exact zero, complete
2,000-draw execute/replay banks with cooperative pause and reentry, private
source joins/conflicts/missingness, item direction, weighted fit equality,
paired support and equal writer weights, mutation refusal and small support.
No native fixture or human result is claimed by this unexecuted design note.

Record kind `claim`; tags `H15-T11`, `DISAGREE-6`; by_construction false for
real reports. Activation records FEAR, PANIC/GRIEF and RAGE as proposed prompt
relations, explicitly adult self-report and not identified biological systems.
Common response habits, prompted recollection and distress-overlapping item
wording remain rivals. A null with limited sensitivity is not absence.

## Owner admission and resource contract

Separate source and analysis phases share one 20,000 CPU-second IN12 ceiling,
including verification and all attempts. Source projection checkpoints whole
writers; the proposed first quantum is 330 (at least 5% of the archive's maximum
6,600 possible writers), then owner-measured continuation. Analysis starts with
100 of 2,000 resamples (5% of complete all-panel work), checkpoints every ten,
and independently replays all work. Each quantum yields at its whole-unit or
wall bound and on an owned yield/stop request. Source, implementation, semantic
and complete private-table bindings are sealed. Verifier partials explicitly
return verified false. Bound CPU-only work to two numerical threads and the
existing memory/commit guards. Forecast and remaining IN family allowance are
owner gates; this file grants no production launch, export or new research.
