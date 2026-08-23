# TOOLS — what is installed, what it does, and what it does not solve

**2026-08-05.** Installed after the engineering-scaffolding search. Everything here is verified
working in `.venv` on this machine, on real artifacts from `corpora/`, not just `pip install`-ed.

**The framing that chose these.** Data-science scaffolding — preregistration templates, research
compendia, multiverse analysis — went to the Ghost Scale Simulation, which is the repo doing
inference against ground truth. This repo is **trying to make something**, so what it needs is
scaffolding for **searching a design space**. See `design/ENGINEERING_LOOP.md`.

---

## The one-line version

| tool | what it gives us | status |
|---|---|---|
| **LFTK** | 220 handcrafted linguistic features | ✅ working, 220 extracted |
| **BiberPlus** | 96 Biber register/style tags | ✅ working — **after two bug fixes, see below** |
| **TextDescriptives** | 26 readability / syntactic-complexity metrics | ✅ working |
| **tsfresh** | Benjamini-Yekutieli false-discovery control | ✅ working, passes its own positive control |
| **pyribs** | MAP-Elites archives, emitters, schedulers | ✅ installed |
| **TransformerLens** | hooks on every activation, 50+ model families | ✅ installed, CUDA intact |
| **Optuna** | hyperparameter search with held-out scoring | ✅ installed |
| **scikit-learn, spaCy** | dependencies of the above, useful anyway | ✅ |

**342 features now extract from one artifact**, where before we had about ten hand-written ones.

---

## 1 · The feature libraries — LFTK, BiberPlus, TextDescriptives

**What they are.** Three independent collections of *handcrafted* linguistic measures, each
developed and validated by someone else, covering lexical richness, syntactic complexity,
readability, part-of-speech distributions, and Biber's register dimensions.

**What we use them for.** `soundingline/measures/features.py` wraps all three behind one call:

```python
from soundingline.measures.features import extract, extract_many
feats = extract(text)                       # -> {'lftk_t_word': 660.0, 'biber_ART': 28.79, ...}
names, matrix = extract_many(list_of_texts) # -> feature matrix over a corpus
```

**Why this is the most important install.** Ten measures were hand-written here and ten died.
`design/ENGINEERING_LOOP.md` names the cause — *a search with a population size of one*, run against
an evaluator that was already built and takes minutes. These libraries are the population, and none
of them are ours, which also removes our own bias from the candidate set.

**What they do NOT solve.** They are all **artifact-side** measures, and `FINDINGS.md` records that
every artifact-side measure so far has died to length, register, or vocabulary. Having 342 of them
does not change that; it changes how fast we find out. **They also cannot be scored honestly without
tool 2.**

### Two package bugs found and worked around — do not "fix" these back

Both are in `features.py`, documented at the call site.

1. **BiberPlus keys its constant dictionaries by file path.** On Windows that produces
   `constants\quantifiers` while the tagger asks for `quantifiers`, so **every** lookup raises
   `KeyError` — and at least four submodules import the builder directly, so patching one is not
   enough. `_patch_biber_paths()` walks the whole package and rebinds all of them.
2. **BiberPlus's aggregation is incompatible with pandas 3.** `update_tag_counts` calls
   `tagged_df.tags` on what pandas 3 hands it as a bare ndarray. Its tagger is fine; only the
   frequency counting is broken. We call `tag_text` and count ourselves, which also makes the
   normalisation *rates per 1,000 tokens*, matching `measures/leakage.py` instead of BiberPlus's
   per-100-token windows.

**Both failures were silent.** `calculate_tag_frequencies` wraps its body in a bare `except`, prints
the input text, and returns `None` — so a broken run looks like an empty result. Worth remembering
when a feature source suddenly returns nothing.

---

## 2 · tsfresh — false-discovery control, and it is not optional

**What it is.** A time-series feature library. **We do not use it for features.** We use its
`feature_selection` module, which is the FRESH procedure: pick an appropriate hypothesis test per
feature (Kendall rank / Kolmogorov-Smirnov / Fisher's exact), then apply **Benjamini-Yekutieli** to
the resulting p-values.

**What we use it for.** `soundingline/measures/select.py`:

```python
from soundingline.measures.select import summarise, significant
summarise(names, matrix, rungs)   # counts, incl. how many we WOULD have believed uncorrected
significant(names, matrix, rungs) # only what survives correction
```

**Why it ships with tool 1 and not separately.** Testing 342 features at p < 0.05 produces about
**17 false positives by construction.** Known weakness 1 in `FINDINGS.md` is that this project has
**never** corrected for multiple comparisons across ~25 tests. Installing the features without this
would manufacture exactly the kind of result we have spent three days learning to distrust.

**Benjamini-Yekutieli, not Benjamini-Hochberg, deliberately.** BH is only valid under independence
or positive dependence. Our three feature libraries count overlapping things on the same text, so
the dependence is strong and of unknown sign. BY is valid under arbitrary dependence. It is more
conservative and that is correct here.

**It passes its own positive control.** On synthetic data — 1 real feature, 99 noise, n = 50 —
uncorrected screening keeps 2; BY keeps exactly 1, the real one, at p = 6e-15.

**What it does NOT solve.** Correction controls false *discoveries*; it does nothing about the
ladder being 50 machine-written artifacts (weakness 4) or about fitted hyperparameters (weakness 3).

---

## 3 · pyribs — the archive

**What it is.** The reference implementation of quality-diversity optimisation: MAP-Elites, CMA-ME,
CMA-MAE. Three components — **archives** (store solutions indexed by behaviour), **emitters**
(propose new candidates), **schedulers** — with an ask/tell interface, so we keep control of
evaluation.

**What we use it for.** Not yet wired. The design is in `design/ENGINEERING_LOOP.md`: fitness is rho
against the ladder rungs, and **the behaviour descriptors already exist — they are the control
battery.** A candidate's coordinates are `(needs order?, length-clean?, echo-clean?, transfers?,
flat on no-maker?)`: a 5-bit, 32-cell archive.

**Why it matters.** Every one of the ten dead measures occupies a cell, and we have been **deleting
them**. An archive answers a question a sequence of deaths cannot: *which regions of measure-space
are occupiable at all?* If nothing ever lands in `(needs order, length-clean, echo-clean, transfers)`
after a thousand tries, that is a much stronger negative than ten hand-written misses.

**What it does NOT solve.** It will happily reward-hack. Length already tracks rung at +0.403, so the
length penalty must live **in the fitness function**, not in a post-hoc check.

---

## 4 · TransformerLens — reading the model properly

**What it is.** The standard mechanistic-interpretability library. `HookedTransformer` exposes a
hook on every activation, supports 50+ pretrained families, and provides activation patching, caching
and direct logit attribution.

**What we use it for.** We hand-rolled activation reading in `soundingline/probe/activations.py`, and
our two best results are reader-internal. The immediate job is **known weakness 3**: the layer ratio
splits the model at `0.07` and `0.76` of depth, and those loci were **chosen by looking at a prior
result on the same model** and never held out. TransformerLens makes sweeping all split points cheap
enough to do properly.

**Chosen over nnsight** because nnsight's advantage is remote execution of very large models, which
is irrelevant on a 12 GB local card, and TransformerLens is the standard for this exact task.

**What it does NOT solve.** Nothing about corpora. It makes reading the reader cheaper and more
rigorous; it does not give us controlled human artifacts.

**Note.** SAE tooling moved out of TransformerLens at v2 — if we ever want sparse autoencoders, that
is `SAELens`, not installed.

---

## 5 · Optuna — searching hyperparameters instead of picking them

**What it is.** A hyperparameter optimisation framework with pruning and persistent studies.

**What we use it for.** The layer loci again. They should have been *searched against a held-out set*,
not *chosen by looking at the answer*. Optuna plus `corpora/ladder2/` is that fix.

**Chosen over Ax/BoTorch** because Ax's advantage is constrained outcomes, which we do not need, and
it is much heavier. **Known caveat:** an Optuna sweep is not failure-resistant — one crashed trial can
take the sweep with it, so wrap objectives.

---

## Deliberately NOT installed

| | why |
|---|---|
| **PySR / gplearn / symbolic regression** | fits an equation to a target variable. **We do not have the target** — that is the entire problem. gplearn's `SymbolicTransformer` is queued in `TODO.md` behind the tier-A checks |
| **OpenEvolve** (AlphaEvolve) | queued behind tier A. The 342 free features are cheaper and may answer it first |
| **MLflow / DVC** | provenance tooling. `results/*/VERDICT.md` plus git is working, and this is data-science scaffolding → Ghost Scale |
| **specr / RobustiPy** (multiverse) | tempting for weakness 3, but it is analysis scaffolding → Ghost Scale. Optuna + held-out is our version |
| **Hydra, Ax, BoTorch** | indirection we do not need |
| **End-to-end research agents** | their documented failure mode — *thorough negative findings rather than new ideas* — is the one we already have |

---

## Environment notes

**numpy is pinned to 2.4.x and this is load-bearing.** Three-way conflict: `textdescriptives`
declares `numpy<2.0` (stale — it works fine on 2.4), `ribs` needs `>=2.0`, and `ribs`→`numba` needs
`<=2.4`. **2.4.6 is the only version that satisfies the ones that matter.** Do not let a later install
move it without re-running the import check:

```bash
./.venv/Scripts/python.exe -c "import numpy,torch,spacy,ribs,tsfresh,optuna,sklearn,biberplus,lftk,textdescriptives,transformer_lens; print(numpy.__version__, torch.cuda.is_available())"
```

Expected: `2.4.6 True`. `en_core_web_sm` 3.8.0 is required by all three feature libraries.


---

## Added or learned since 2026-08-05 (updated 2026-08-08)

| tool / infrastructure | what it gives us | status |
|---|---|---|
| **HuggingFace `datasets`** | streaming reads of GoEmotions, LLM-Emotion, CROSSNEWS — survey a 1.3 GB corpus without downloading it | ✅ used throughout the affect work |
| **the queue** (`runners/run_queue.py`) | output-guarded stages, pid lock, `--shard/--shards` for the night runner | ✅ hardened after the double-loop race |
| **`run_first_gear.sh` / `run_second_gear.sh`** (renamed from day/night 2026-08-12) | first gear: one job at a time, part of the CPU, the GPU mostly the curator's; second gear: sharded whole-machine mode with mutual exclusion and a deadline, loaded about a day deep | ✅ |
| **hash-lock ritual** | `soundingline/locks.py` verification before every commit; 5 gate files relocated (map in DEVIATIONS) | ✅ caught a deleted spec |
| **TransformerLens** | still installed, **still unused** — raw `transformers` + mean-pooled hidden states have sufficed | ⚠ candidate for removal |
| **per-artifact row caches** | `run_induction_v2` and `run_fair_features` save rows, so re-analyses are CPU-only | ✅ new convention: every GPU runner should |

---

## The instrument ledger — built-here tools and their validation state

*(Consolidated from `docs/method/INSTRUMENTS.md` 2026-08-10 at the curator's instruction; parallel documents are a fail state. Results that adjudicate claims go to `docs/theory/`; results that validate or break instruments land here, full records in `FINDINGS.md`.)*

| instrument | what it is | state |
|---|---|---|
| **the event-recovery harness** (`run_event_harness.py`, G130) | synthetic decision events, five known-answer gates, the code path every choice-recovery test runs through | **VALID (L56).** Two of its gates caught real faults during its own build (a mis-specified decoy arm; deterministic tie-breaking) |
| **candidate-set construction** (`run_arg_recovery.py`, G129 pilots) | bounded candidate sets for purpose recovery | **TWO LESSONS BANKED (L62/L64).** The blind floor follows the truth's label marginal regardless of decoy scheme; the estimand is the margin over the measured floor; truth-balanced subsampling (pilot-c) makes the floor analytic |
| **covariate matching** (`run_arg_matched.py`, G130b) | content/surface matching for the lexical-shortcut control | **v2 (coarsened exact) BALANCED AND DELIVERED (L66).** Worst standardized difference 0.20 after matching, 342 pairs on common support; the verdict it enabled was COLLAPSES. The G130c collision runner reconstructs the identical matched set by shared seed |
| **the ScholaWrite dataset** (gated, now held) | 61,504 keystroke edits, 10 writers, 5 preprints, 15 intention labels in 3 groups; splits train 49,212 / test 12,292 / test_small 3,238; columns include before/after text, label, high-level group | **ACQUIRED 2026-08-10** with his token (standard HF credential cache, outside the repo, never in git); local copy under `results/scholawrite/dataset`. **Split caveat banked the same day (L68): the shipped train/test split is within-project with 85 percent unique before-text overlap across the boundary, so any model evaluated on it is inflated; the paper's stricter protocol is still to be pinned before a gate can be claimed. The caveat is now replicated (L69): a second architecture fine-tuned identically overshoots to 0.730 against the same 0.64, within a point of the first, while the zero-shot arm (L70), which no train/test leak can inflate, lands at 0.172 against the published Llama-8B 0.13, a gap owned by the model difference. The protocol arms then bracketed the mystery (L75/L82): test_small undershoots at 0.468, the full leave-one-project-out grid runs 0.26 to 0.61 (means 0.39/0.44), so the within-project leak is worth about thirty points. **Resolved and replicated (L86): the faithful arms land at 0.580 and 0.546 under their exact protocol, bug reproduced, so the printed 0.64/0.64 pair is unreachable from the released materials under the authors' own code** |
| **the exact-replication pipeline** (`run_arg_replication.py`, G136; `run_arg_dedup_hunt.py`) | their features, their encoder, their classifier, their folds; extract_v4 implements the pinned Revision-Index construction | **COMPOSITION CLOSED (L79) after two dead ends (L76).** v4 lands 3,236 of their 3,238, cycle-1 exact, four classes exact, the residual a known label drift in the released corpus. Features corrected to their spec (POS-19, six transition-group counts, both positions), grid replaced by their published footnote hyperparameters, `--balanced` arm added for the rare-class suspect. The L76 candidates (drop-precision; the .290 share) were disconfirmed at source and withdrawn before running |
| **the movement statistic** (`run_pd34_movement.py`, PD-34) | per-item absolute Spearman trend of window series against position, z-scored on within-item shuffles; planted-trend and planted-noise ruler gates before data | **VALID AND DISCRIMINATING (L74).** Gates passed (trend z 4.8, noise 0.14); found the books/essays split on first use. The signed-trend variant is the unbuilt decay form |
| **candidate-set construction, pilot-c** (`run_arg_recovery.py --uniform --balance`) | truth-balanced subsampling, analytic floor | **CLEAN (L65).** Blind landed at 0.232 against the 0.25 analytic floor; the construction's two leak lessons are closed and the margin (22.7 points) is quotable |
| **the maze-world models** (`run_bst_gridworld.py`, G137) | exact value iteration, three inverse-planning models | **GATES-PASSED (L63).** Analytic gates all pass; the figure arm's implementation list is pinned (L78): H model, exact switch parameterization, wide prior, Exp-3 pipeline, stimulus geometry |
| **the BST 2009 reference data** (`results/bst2009_reference/`, with `run_bst_refcheck.py`) | human judgment means and best-fit model predictions digitized from the paper's pure-vector figures; extraction scripts kept for provenance | **VALIDATED (L78), refcheck PASS eight of eight.** Recomputed r reproduces every printed correlation; rating triples sum to 1.000; to our knowledge the first available ground truth for this paper anywhere (the 2026 external sweep found no released data, no independent replication, and no repo carrying the stimuli, with named access gaps: archive.org and MIT DSpace unreachable from here) |
| **the BST Fig-3 stimulus decode** (`sl_fig3_decode.py` + `sl_fig3_canon.py` → `fig3_stimuli_canon.json`) | line-aware text extraction of all 36 stimulus panels (the figure's text layer runs ~5.1 pt against its own 4.60 pt grid, so relative columns come from each line's character sequence, anchors from chain validity); exhaustive label-cost chaining; cross-panel identity at the glyph coordinate, not the snapped cell | **GATE PASSED (L114): 99 of 99 unique stimuli, label-perfect in all 36 panels, zero illegal steps.** 96 paths strictly legal as decoded, three repaired uniquely under one-column judgment-cell slack; the model rebuild's own alignment gate (the reference M2 column) still sits downstream as the independent check |
| **the impossibility toy** (`run_am_construction.py`, G138) | enumerable reward × planner posterior with prior relaxations | **RECREATED+NARROWS (L60), exact at the degeneracy** |
| **the gear scripts** (`run_first_gear.sh` / `run_second_gear.sh`, G121; renamed from run_forever_day/night 2026-08-12) | winpid locks (`.gear1.lock`/`.gear2.lock`, legacy paths checked through the transition), tree kills, orphan sweep, PATH self-repair | **HARDENED AND LIVE-VERIFIED.** Cross-session refusal works; a seven-process tree kill witnessed; the bare-launch PATH fault found when the first whole-machine launch died at birth and fixed in-script. The orphan sweep kills unowned standalone arms (LESSONS §5), so long trainings join the queue or pass their winpid to -Keep. Three 08-14 additions: `tools/regear2_when_idle.sh` waits for a lineage to fully drain (parent winpid dead AND no queue/stage python alive, via `tools/queue_drain_check.ps1`) then relaunches second gear detached, closing the deadline-idle gap — cancel it by FILE (`touch results/.regear.cancel`), never by pid, because a harness kill can leave the msys child alive and one fired its relaunch after being reported dead; the GPU lock's staleness window is 9h (`soundingline/gpulock.py`), after the 5h window reclaimed a live holder mid-training and collided two arms into the deberta OOM; and `run_queue.py --no-gpu` (wired into first gear) holds trainings and sustained generation for second gear, so a gear-one queue can never seize the card |
| **the window feature cache** (`build_features.py`) | corpus features at chosen window sizes | **REPAIRED TWICE (L43).** Default-argument binding and NaN guards; takes `--corpora` (plural), which one night stage learned the hard way |
| **the CKA implementation** (`run_cka_alignment.py` family) | linear CKA with permutation null | **SANITY-PASSED (L61)** at machine precision, with the regime caveat banked: independent noise scores 0.985 at thirty samples in two thousand dimensions, so only null-tested structure is ever quoted |
| **the change-feature block** (`run_arg_replication.py`, `change_features()`, 19 dims) | token Jaccard, character and token sequence ratios, insert/delete/replace/equal counts, length deltas both units, empty-side flags, added and removed token counts | **CARRIES THE PAIR TASK (L85), known-answer gated and confirmed in-house.** Alone it reaches .892/.895 on the binary task (the agent's independent build .8968/.8993), and it lifts the features arm to .895 against the published .90 while embeddings add nothing beyond it. Standing consequence: any instrument judging a revision states the delta explicitly or it is measuring the wrong thing |
| **the duplication probe** (`run_arg_replication.py --oversample`) | seeded pre-CV duplication of named classes, reproducing a published cell by deliberate fold contamination | **VALIDATED AS A DIAGNOSTIC (L81).** Reproduced the printed majority row to the digit and the +DA cell within .008; its signature is exact majority reproduction plus rare-class overshoot above the published band, which is what pre-evaluation duplication looks like from outside |
| **the paper self-consistency check** (practice, L83) | before gating on a published number, test it against every number in the paper that constrains it: the majority-F1 identity, class-distribution reweighting, subtotal sums | **THREE FOR THREE (L77/L78/L79).** Caught internal contradictions in every paper this phase recreated; now a standing step before any gate is adopted |
| **the theory-format linter** (`tools/theory_lint.py` + a PostToolUse hook in `.claude/settings.json`) | mechanical enforcement of the theory README's decidable rules: afterword under every hypothesis table, fixed Confidence vocabulary, the dash discipline; path-filtered inside the script per the subagent's version caveat | **INSTALLED 2026-08-10, self-tested clean on all five theory files.** Built on the Opus subagent's finding that prompt rules are requests while hooks are guarantees, and that per-directory CLAUDE.md dies at compaction; the judgment-shaped rules live in `.claude/rules/theory-format.md` (advisory) and the README stays canonical |
| **gear 3** (`runners/gear3.py` + the Modal volume `sounding-line-corpora`) | cloud burst execution behind the curator's stone rules: per-use approval required, the $10 window refuses with a final-approval-request template (no override flag), every run and approval in `results/gear3_ledger.json`, timeout kill, 1.4x estimate tax; corpora ship as one zip the container unpacks | **VALIDATED (L124) AND LIVE-FIRED (L125): the validation rerun landed within +0.002 of local for ~$0.73; the first package (six A/B arms, two parallel chains, ~$8.20) ran preregister-to-verdict in one afternoon.** Seven client-side defects fixed across the arc (path conversion, small-file uploads, cp1252, cwd drift, python-minor matching, a missing tokenizer dep, and produce siblings dying with containers — prediction files now come home with every produce). Launch-time spend reservation under a file lock makes the ceiling race-free. Recreation gates stay local; gear 3 is for Phase-2 bursts, rarely, on his call |
| **the pooled PAN scorer** (`pooled_macro_f1` in `run_pan_winner.py` / `run_pan25_winner.py`) | the official evaluator's exact form: pool every pair decision, two-class macro-F1, mismatched documents dropped silently | **VALIDATED THREE WAYS (L102/L109).** Matches the evaluator source read verbatim; six published baseline cells back-calculate exactly from class priors under this form (falsifying the overview papers' own prose); reproduces the printed 2025 test baselines from the on-disk split to 0.0004 |
| **the contamination gate** (`overlap()` in `run_pan25_winner.py`; the exact-hash practice of L106/L108) | pre-training overlap between every training source and every evaluation split, at document/paragraph/pair granularity, recorded in the arm's output; aborts above one percent | **VALIDATED IN BOTH DIRECTIONS.** Caught the 2024 cross-year leak (16% of pairs, members scoring 1.0 on the leaked subset) and passed the clean 2025 edition (0.4%); normalization sweep showed exact-hash tight on this corpus (near-dup residue nil). LESSONS §1d is the binding rule |
| **the consensus-ballot fleet** (practice, L109) | the convergence-shaped multi-agent audit he ordered: a fixed numbered claim ballot, each claim deep-verified at source by two independent agents plus a meta-auditor on the fix chain, new findings capped and severity-gated | **VALIDATED ON FIRST USE: 21 of 25 claims unanimous, zero agent-vs-agent disagreement, dissents localized to three record defects (all corrected), one major asset found (the labeled 2025 test split).** The preferred fleet shape over open-ended briefs, which each returned a new path |
| **the realization adjudicator** (`run_g158_adjudicate.py`, mechanical + reader arms) | per-instruction realization verdicts over the G131 exploratory corpus: string tests graded exact/approx for the decidable surface instructions, with each check's base rate measured on the zero-instruction control cells; the semantic remainder adjudicated by the local reader at temperature 0 with a required verbatim evidence span (verified against the text) and an explicit unrealized-with-no-span option, every record flagged model-judged and lineage-annotated | **MECHANICAL ARM LANDED 2026-08-19 (L137 follow-through): 324 of 880 assignments decidable, pass rate 0.586 (exact-grade 0.68, approx 0.51), base rates spanning 0.0 (the discriminating checks) to 0.5 (the punctuation-style instruction, weak by construction). Reader arm ran (556 verdicts, 95% realized both families) and its validation FAILED (L139): over-credit 0.725 overall and 0.688 on exact-grade rows, zero ambiguous calls in 636 judgments, evidence spans no protection — the reader arm's verdicts are warning-labeled raw records, the mechanical exact-grade subset is the only realization ground truth, and any future adjudication instrument must pass this validation before its verdicts are consumed** |
| **the reading-profile schema** (`soundingline/reading_profile.py` + `tools/test_reading_profile.py`) | the Phase 2.2 reconstruction profile as a typed structure: reading identity, proximal and trajectory reconstruction, historical traces (lifetime-history disclaimer enforced), anomaly profile split into presence (final-artifact) and observed handling (paired-delta), realization ground truth (process-aware only), and a mandatory four-statement claim boundary; interface access is ordered I1 < I2 < I3 and a reading raises `InterfaceLeak` on any section above its declared interface | **BUILT + GUARD-TESTED 2026-08-19 (G160): eight tests pass — process labels and delta-observed handling refuse to enter a final-artifact reading, inferred provenance is refused as a vocabulary violation, the claim boundary is mandatory. This is the structural form of contract §3b and 2.2's pre-mortem item 4** |
| **the anomaly-handling ruler** (`run_g161_ruler.py`, gridworld likelihood classifier) | three-tier per-step likelihood detection (episode-calibrated hard threshold, run detector for sustained mild deviation, mid-threshold recurrence) plus post-cluster handling classification (waypoint account, backtrack, arrival-and-adaptivity) over seven mechanically generated ground-truth classes | **VALIDATED (L147): all six preregistered gates pass and replicate on fresh seeds; six build iterations recorded in-file are the design knowledge (categorical multi-step anomalies, consequence structure, episode-level nulls, separated-cluster recurrence, post-cluster windows). Licenses the 2.2D text battery; constructed-world scope only** |
| **the Phase 2.3 process-record schemas** (`soundingline/process_record.py` + `tools/test_process_record.py`) | ProcessCase/ProcessEvent with a fixed operation vocabulary, the contribution network with per-actor roles that never sum (asking for an author-share scalar raises), and the multilabel anomaly trajectory; the curator's non-recognition ruling is structural — a notice event without perceptual access raises, and a case admits exactly one non-recognition decision at episode resolution | **BUILT + GUARD-TESTED 2026-08-21: twelve tests pass beside G160's eight; consumed by the G166 route logs and every Phase 2.3 construction** |
| **the route-varied process corpus** (`corpora/g166_routes/`, `run_g166_routes.py`) | five recorded production routes to surface-matched essays on identical briefs (direct / outline / rewrite / seeded-select / critique-revise), ten topics, two families, every intermediate logged as schema events; self-audit gates yield, length band, log completeness, and cross-route degeneracy | **CORPUS-STANDS (L152): 100/100 at full yield, zero violations on every gate, route length means within seven percent. The equifinality substrate; its reading battery decides whether anything separates the routes** |
| **the long-form handling corpus** (`corpora/g169_longform/`, `run_g169_longform.py`) | four handling families (corrected / concealed / unnoticed / clean) as 900-to-1300-word expansions with token-verifiable plants and the hedging-density audit; v2 carries ACCEPT-TIME verification (family criteria checked inside the generation loop) | **v1 REFUSED ITSELF (L156: concealment by omission, hedging under floor) and the accept-time repair landed v2 CORPUS-STANDS same day (plants 0.95-1.0, hedging 2.3x). The substrate on which L158 broke the L150 resolution wall** |
| **the role-randomized interaction corpus** (`corpora/g168_roles/`, `run_g168_roles.py`) | forty two-actor logged essay productions crossing proposer family, selection mode, and veto presence, every event a schema ProcessEvent with actors and alternatives; audit gates include SELECTION INTEGRITY (the chosen thesis must out-overlap every rejected one in the final essay) and veto integrity | **CORPUS-STANDS (L160 substrate): 40/40, selection integrity 0.95, veto integrity 1.0. The substrate on which ratification read at exactly chance under passed ceilings; the C5 audit-interface product reads its logs directly** |
| **the wake watcher** (`tools/wake_watcher.sh`) | a harness-tracked background task that exits the moment any watched produce appears or changes, re-invoking the agent — the gear engines are detached and cannot wake anything themselves | **IN SERVICE 2026-08-21 (found after two verdicts sat unreported for hours): six live triggers on its first day, median wake-to-write-through under ten minutes. Re-armed each pass with the next wave's produces** |
| **the ordered-accident ruler** (`run_g171_accidents.py`, gridworld pattern-violation classifier) | eight mechanically generated pattern-violation classes over an established waypoint rhythm; likelihood classification against the FITTED pattern account with episode-calibrated thresholds, post-cluster windows, an exclusive-consequence rule, and enforced origin abstention on the origin-identical pair | **VALIDATED (L159): all gates pass both seeds after one recorded repair; adoption identifiable at ceiling, origin honestly unresolved, unfamiliar convention never called error. Constructed-world scope; text transfer is Stage-2 behind the root map** |
| **the conditional-likelihood reader** (`soundingline/probe/conditional_reader.py`) | the Phase 2.4 non-generative inversion score: mean per-token log P(artifact given candidate) minus the neutral-conditioned arm, candidate and artifact tokenized separately so the boundary is exact; nothing leaving it crosses tokenizers (within-reader ranks, margins, paired deltas only) | **FIELD-VALIDATED 2026-08-22 (L161): guard battery all 8 green at build, then the anchor arm recovered the known-positive realized revisions at 0.78 vs the 0.25 floor (echo gate 16/16). The Phase 2.4 common scorer; every matrix and intervention number flows through it** |
| **the subspace intervention interface** (`soundingline/probe/interventions.py`) | block-local amplification/ablation of a frozen orthonormal subspace, per-family block registry, token-boundary discipline (never active while a candidate is read), guaranteed hook cleanup, full-configuration hashing | **GUARD-TESTED 2026-08-22 (same battery): causal boundary verified (pre-boundary positions byte-identical under intervention), alpha-zero a no-op, cleanup discriminates our hooks from transformers 5's own persistent recorder hooks — that discrimination was the build's one caught defect. The hook machinery held in the field; the first CAUSAL battery over it (G174, L162) instrument-failed on dev-power block selection, so no basis is yet validated as causally usable** |
