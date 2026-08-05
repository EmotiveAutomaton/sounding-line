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
