# Week 3 choice intake and population-relative sensitivity

This is a build contract, not a corpus result. The October 25 packet commissions
CA0 and WD1. The runners expose `execute(output, inputs, config)` and
`verify(output, inputs, config)` for the owner's counted native runtime.

## CA0: establish the comparison population

The [paper's codebook](https://arxiv.org/html/2507.09650v2#A8) was read directly.
Its Appendix H describes conversation identifiers, participant identifiers, four
turns, candidate fields and preference/explanation fields. The current
[dataset card](https://huggingface.co/datasets/facebook/community-alignment-dataset/blob/97343c7f6399fcbea430ed0f37c1768281a78d56/README.md)
calls the codebook Appendix I; this numbering difference does not alter the
release schema. The older codebook's population counts are not substituted for
the retained v1.1 CSV. The release includes wave, but no conversation timestamp.

`week3_choice_intake.py` reads the existing pinned CSV. A usable comparison has
a prompt, four nonempty parsed candidates, a choice naming one of those four,
country/language, and a complete preceding conversation. Absent and incomplete
turns have separate counts. Duplicate conversation identities fail closed.
Eligibility requires at least 20 usable comparisons on 10 exact prompt texts.
The comparison is the unit; repeated comparisons are not independent people.

The packet's shared-prompt route uses exact current prompt text among eligible
annotators. An additional context-aware count distinguishes identical follow-up
prompts with different preceding conversations. CA1 must retain preceding context
and keep a complete conversation together across its fit/test split. These
counts may reveal an additional exchangeability limit; a high literal-prompt
overlap does not prove the preceding contexts are identical.

The CPU encoder is
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, pinned to
`e8f8c211226b894fcb81acc59f3b34ba3efd5f42` from
[the model owner's metadata](https://huggingface.co/api/models/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/revision/e8f8c211226b894fcb81acc59f3b34ba3efd5f42).
CA0 selects the immutable revision; it does not download its weights or run it.

The handler emits aggregate counts only. It emits no participant identifiers,
text, preferred-candidate distribution, inferred values or probability test.
Execution and verification each reconstruct the entire CSV census.

Six targeted checks pass: conversation/turn units, privacy, missing candidates
and choices, broken prior turns, shared-prompt eligibility, duplicates, source
pins and fresh replay. The initial fixture pass caught an invalid encoding alias;
the alias was corrected before any corpus launch. Native fixture validation and
actual corpus execution remain owner dispatch steps.

## WD1: separate lean from population-relative sensitivity

`week3_sdt.py` uses P4's frozen prechoice feature recipe, with previous-action
columns and the recent acceptance rate removed. P8 is refused. Each reference
is a fixed ridge logistic acceptance model; acceptance includes direct acceptance
and acceptance followed by editing. The recipient's entire set of sessions is
excluded from fitting, scaling and the 16-component PCA. No writer offset is fit.
This is a new population-only model, not reuse of P4's fitted backbone.

For each writer and disjoint whole-prompt half, a fixed weakly regularized probit
model regresses acceptance on the population reference's log-odds. Sensitivity
is its slope per log-odds unit. Criterion is minus its intercept, evaluated where
population acceptance probability is one half. Session-first/last-third changes
in these coordinates are descriptive secondary readouts. Four usable decisions
per half and four writers are minimum numerical support, not a power guarantee.

Every within-prompt, whole-session writer-label permutation rebuilds the
recipient-excluded reference, its preprocessing and the prompt-half profiles.
Reusing the original scores for fake writers would admit outcomes from the new
fake recipient into its own reference; this implementation avoids that shortcut.
The primary reports sensitivity correlation, the 1,000-draw permutation mean,
band and one-sided probability, and the real-minus-reference contrast with
2,000 paired writer bootstrap draws. Undefined correlations or changed supported
populations invalidate the comparison; no draws are silently discarded.

The full route cannot lower its 1,000-permutation requirement. The timing-only
pilot runs complete reference permutations without a scientific verdict. Its
projection must include full execution and fresh verification before admission
under the two-CPU-hour ceiling. Immutable per-permutation checkpoints permit
yielding; their hashes and bindings are checked on continuation, and fresh
verification refits every saved calculation before completion.

Eight targeted checks pass, including planted slope/criterion separation,
history-feature invariance, no effect of a recipient's labels on its own
reference, prompt-specific permutation counts, constant-profile refusal,
full-bank enforcement, actual execute/replay, and yield/continuation. Corpus
timing and full scientific execution remain unrun. Ghost N17's previously
received constructed-world prerequisite remains partial calibration, not a
substitute for these local checks or human ground truth.

**Scope is unchanged:** this measures population-relative behavior. It does
not identify independent quality, competence, payoffs or causal trust learning.
The curator's October 18 approved competence gap stays open.
