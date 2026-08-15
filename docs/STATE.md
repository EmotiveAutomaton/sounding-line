# STATE: the agent's operational file

> ## ⚠ IF YOU HAVE JUST BEEN COMPACTED: RELOAD THE THEORY FIRST
>
> Before any research, any literature reading, or any judgement about a result:
> **read the whole of `docs/theory/`, newest first, then `FINDINGS.md`, then this file.** A
> compaction preserves what happened and loses the framework's shape, which is exactly the state
> in which confident literature overwrites it. That has happened twice. See `CLAUDE.md`, first
> section. Then read `docs/method/LESSONS.md`'s trigger index before designing or building
> anything.

**Rewritten 2026-08-14, immediately before an expected compaction.** Everything below is current.

## ⚠ HARD CONSTRAINTS AND STANDING RULINGS, SET BY THE CURATOR

1. **SUBAGENTS ONLY WHEN HE ASKS.** He asks → spawn (recent asks have been Opus referees and a
   nine-agent consensus fleet, all his explicit orders); "ultracode" → Workflow tool; otherwise
   inline. The consensus-ballot form (fixed claims, dual coverage, capped findings channel) is
   the preferred fleet shape — he ordered it because open-ended agents each returned a new path.
2. **AUTHOR CONTACT IS OFF THE TABLE (2026-08-14).** Never suggest contacting a paper's authors
   for any purpose — not for irreproducibility, not for corpora. Irreproducibility wording
   stands on exhausted-public-routes evidence alone. This ruling is also in LESSONS §1c.
3. **The recreation pass standard (his ruling, 08-10):** a recreation passes only by reproducing
   published exact values; a large shortfall is a defect in our model of their pipeline, hunted
   not caveated. Refined by the referee arc: verdicts on fine-tune arms need the three-seed
   interval (§1c), faithful means the training framework not the printed hyperparameters (§1b),
   and underdetermined protocols report the specification curve.
4. **Token posture:** he opens budget explicitly when he wants fleets; otherwise dense and
   inline. Model is Fable at max effort.
5. **Gears, not day/night (renamed 2026-08-12).** First gear = his machine (serial, GPU mostly
   his); second gear = everything, loaded about a day deep, ONLY on his call, sized to his
   stated window. A deadline exit is a wake-and-decide event.

## The priority ladder, his words, in order

1. **`docs/theory/` files (not `essays/`) perfectly interpretable at a glance and very clean.**
   His quotations are the most valuable information in the project.
2. **The model and all the tests** (the record's integrity; the referee arc is this item).
3. **Minor errors**, prioritised at my discretion.

## The five-file contract and style rules (unchanged, binding)

    THE_TRIPLE_INFERENCE     what is inferred; dependencies among targets; identifiability
    THREE_COGNITIVE_LAYERS   what architecture might support the inference
    DECISION_TRACES          what observable traces the maker's decisions leave
    READER_HEURISTICS        how a bounded reader finds, combines, and calibrates those traces
    ALIGNMENT                what objective should govern a system after it can read them

Blockquotes are the curator's words only; his blockquotes are untouchable; structural changes
are proposals in chat first. No em/en dashes in prose in curated markdown; colons only in
headers and labels; no "it's not A, it's B" constructions. Reserved vocabulary: functional
level / region / block / subspace; "layer" unqualified is banned. Format spec and afterword
rules in `docs/theory/README.md`; the linter enforces the mechanical half.

## Where the program stands (2026-08-14)

**Phase 1 (frontier recreations) is one implementation and one queue-burn from his final
assessment.** The scorecard, settled by two adversarial Opus referees and a nine-agent
consensus fleet (L107, L108, L109 — 21 of 25 ballot claims unanimous):

- **Armstrong–Mindermann**: PASSED exactly (analytic 0.5/0.5), extended (bounded family 20×,
  both priors 40×).
- **ScholaWrite**: CORRECTION-CONFIRMED (the printed 0.64 is stale and contradicted by the
  paper's own v5 table, reweighting to 0.5947; its own printed accuracy corroborates),
  CLOSURE-PENDING on the framework-faithful three-seed arms now in the queue. The tag typo is
  inert (never a train/eval mismatch; ~89% truncation). The 0.741 cell is the non-faithful
  recipe.
- **ArgRewrite**: composition exact (3,236/3,238); binary Majority to the digit; the printed
  Majority rows are mutually incompatible with each other (fleet's strengthening), so the fine
  printed rows are unexplainable by any hidden dataset; the oversampling claim is inference
  only (their §5.4.1 names fold-safe synonym replacement); faithful Features arm .883 vs .90
  (the old ".895 reproduced" claim wrongly included our change block); embedding rows "not
  reproduced by us," with grid-max queued and the four-block encoding the owed build.
- **PAN 2024**: two members above their validation gates under the corrected recipe, but all
  validation numbers (theirs and ours) blend ~16% cross-year memorization (leaked pairs score
  1.0); strict leak-free capability 0.8235/0.8355. Corrected same-recipe members + vote +
  paragraph-keyed leak-free settling arm in the queue. **PAN 2025**: the labeled TEST split is
  on disk and verified genuine — the fully-specified 2025 winner (deberta-base, printed test
  0.830 hard) is queued as the phase's first reachable test-set exact-value gate (G148),
  contamination-gated at 0.4%, clean.
- **BST**: reference data validated (Exp 1 fully; Exp 2 fully after the fleet found the
  column-major grouping — stimulus i = rows i, i+95, i+190; all sums pass; my earlier
  narrowing was wrong and is reversed). Design corrected by the referees: NINE actions
  including Stay at cost −1, 36 = 4 goal configs × 3 path groups × 3 route conditions, the
  goal prior is a source contradiction (both readings run as arms; it sets K in the γ factor).
  **The Fig-3 decode gate PASSED (L114): 99 of 99 stimuli, label-perfect, every path a legal
  walk (fig3_stimuli_canon.json). The remaining block is the 9-action rebuild with
  marginalized path likelihoods and dual goal-prior arms.** Old 4-action results archived as
  summary_4action.json.

**Phase 2 waits on his ruling over that package.** Its head is the G129 choice-recovery
preregistration (the delta stated in every arm; the 19-dim change block as declared baseline).

**The artifact-side science meanwhile (the movement family, settled at four generator
families):** rising positional polish is the machine default (3 of 4 base × post-training
cells, window-robust in the llama cells), the lone human-direction decay is one model at one
window, the reader-side instrument dissociates from the artifact side (mobility is
qwen-instruct-specific), the scaffolding instrument measures prompt burden not provenance,
and the no-maker control is clean at n=108 with the reader family-neutral (weakness 6's
load-bearing cell closed, weakness 4 narrowed). The maker-signature results (PD-33 family)
stand untouched. Function words carry state at the pre-registered bar (PD-11 at power) and
survive the fair induction control on the two strong ladders (G76/L94).

## Queue / infrastructure state

- **Engines:** first gear `run_first_gear.sh` (serial), second gear `run_second_gear.sh
  [hours] [workers]` (sharded; locks `.gear1.lock`/`.gear2.lock`, winpid line 2; legacy lock
  paths still checked). Kill by winpid tree; sweep orphans; standalone GPU arms need queue
  membership, checkpoint-resume, or the sweep keep-list. The queue asserts produces-path
  uniqueness at load; a clean exit with no produce records FAILED.
- **In flight at rewrite time:** second gear mid-burn on the referee arms — pan deberta
  (fp32+warmup), roberta rerun (structural dropout), then ernie-sched, vote, leak-free arm,
  three framework-faithful ScholaWrite seeds + roberta arm + batch-8 reading, grid-max, the
  wqd 2025 test gate, w40/fiction completion cells, llama top-up round.
- **The audit-history index:** L26 (the first fleet), L61 (recreation re-audit), L93 (the
  methods pass), L107/L108 (the two referees), L109 (the consensus fleet). The old solo-audit
  scope table this file used to carry is superseded by that chain.

## Open decisions / owed

- **His:** the Phase-1 final assessment when the queue lands + BST rebuild finishes; the
  Phase-2 go; interest ratings (HH-14, informs READER_HEURISTICS only); PAN22 Aston access;
  rotate the early-project API key.
- **Mine, in order:** BST decode-to-99 then the 9-action rebuild; write-throughs as arms land;
  the four-block encoding arm; the specification-percentile function over arm files; TOOLS
  rows for the contamination gate and consensus-ballot practice.
- **The one-maker-many-kinds corpus problem** stands (CROSSNEWS pseudo-documents only;
  Guardian small; CMCC request-only); the program's G133 commissioned pilot leads this thread.
