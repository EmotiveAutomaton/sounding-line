# Literature — what the field holds, verified at source

One file for what used to be four (the audit, the Panksepp/Barrett review, the affect-in-text
review, the benchmarks survey), consolidated 2026-08-11. Each section keeps its original date and
its READ/SNIPPET discipline; the originals are preserved whole in `../archive/method/`. Reach for
this before claiming novelty, before adopting a field framing, and before choosing a corpus or
benchmark.

> ## ⚠ Standing warning, carried from the audit
>
> Two literature returns each produced a recommendation to adopt the field's framing over the
> project's, and both were wrong (Bullot & Reber's ordering; dropping Panksepp). The curator:
> *"Panksepp in general may not be precise, but the idea of midbrain-localised solutions is
> absolutely load-bearing. If you drop that, we have what everyone else has, which is the wrong
> part. You did it again."* **Occupied ground is a fact; a recommendation to abandon a premise
> because the ground is crowded is an inference, and it has a 0-for-2 record.** When accounts
> conflict, extract a test from the friction.

---

## §1. The occupied/refuted map (audit, 2026-08-05)

Three subagents, adversarial search, every claim READ or SNIPPET at source.

**The three levels are Bullot & Reber (2013), not Dennett or Marr.** Their basic exposure →
artistic design stance → artistic understanding is our mechanics/technique/purpose axis, in a BBS
target article. Two things cut our way: they assert a **strict ordering** (design stance
*"requisite for"* understanding), which directly contradicts enter-anywhere-and-ratchet, and
their framework tests at **26% support, 56% none** over 34 experiments (Chmiel & Schubert 2019,
READ). The contradiction is the contribution surface. Dennett's intentional stance is
instrumentalist by design, so it licenses prediction, not identification; Rasmussen's abstraction
hierarchy (means-ends diagnosis from any level) is the best unexplored formal match. The standing
humanities objection to name in any write-up: Wimsatt & Beardsley's Intentional Fallacy.

**"Values need many artifacts" is a theorem; unconditional recovery is refuted.** Amin, Jiang &
Singh (NeurIPS 2017, READ): impossible to identify the intrinsic reward from one task. Armstrong
& Mindermann (2018, READ), Skalse et al. (2023), Cao et al. (2021): rewards are only partially
identifiable **in the infinite-data limit**. The operative variable is not the COUNT of artifacts
but the **DIVERSITY of conditions** under which they were made; N artifacts under identical
conditions are informationally one. Our bounded human-shaped hypothesis family is the normative
assumption the proofs say you cannot do without, and should be labelled as such. (The project's
response and its first toy number live in `../theory/THE_TRIPLE_INFERENCE.md` §7.)

**Value blindness, strong form, is false as stated.** Boer & Fischer (k=91, N≈30k): self-reported
values do predict behaviour moderately. The defensible version is domain-specific self-knowledge
(Vazire's SOKA). The art-specific mechanism, making an artifact improves the maker's accuracy
about their own values, is **unclaimed, unevidenced, cheap, and testable**. (The theory file now
carries the softened access claim in the curator's own words.)

**Interest as unexplained decisions is occupied**: Graf & Landwehr's Pleasure-Interest Model is
the claim with a mechanism; the best-evidenced live account is **learning progress** (Ten et al.,
Nat. Comms 2021, READ); Silvia's two-appraisal model says high novelty + low coping = confusion,
so say "detected but not yet attributed." Miall & Kuiken (1994, READ) supplies the usable
protocol: segment-level reading time against stylistic deviation, r = .22-.45, no moderation by
literary competence. Berlyne is abandoned; do not cite him as backing.

**Followers as a value corpus**: graded ideology scaling is 23 years old (Wordscores, Wordfish,
TBIP), so graded-vs-binary is not the novelty; scoring followers against a founder's text for
value uptake is open, but the reason is a validity hole (removing the anchor collapses into
unsupervised scaling, which fails; Bruinsma & Gemenis, READ). Nearest precedent measures topical
persistence, not value uptake (Barron et al., PNAS 2018). **Do not build on Moral Foundations
dictionaries** (Rehbein et al., ACL 2025, READ: "dictionaries are not a valid approach").

**About our own method**: the intent ladder's apparatus is published (CS4, 2024, different DV);
prompt constraint count swings machine-detector F1 by up to 14.4 SD ("How You Prompt Matters!",
READ), so the specification variable is structurally entangled with detector-ness and the funnel
must keep existing; machine-detector filters are corpus-specific (HACo-Det: metric detectors at
0.462 F1 vs 0.433 random on co-authored text), so run the funnel on two disjoint corpora;
keystroke logging (Inputlog) is the field that measures writers' decisions directly, and a
keystroke corpus is the validation target every dead artifact-side measure lacked.

**The deep vulnerability, named in two literatures at once**: archaeology's equifinality and
IRL's partial identifiability are the same problem, and the IRL side supplies the formal
vocabulary.

## §2. Panksepp versus Barrett (review, 2026-08-05)

~45 sources, most READ in full. No recommendation; evidence for the curator to weigh.

- **The debate cannot be settled by imaging** — Vytal & Hamann vs Lindquist et al. is a criterion
  difference, not a data difference, and Clark-Polner et al. (READ) is a general defeater for
  decoding claims in both directions. Do not wait for it to resolve.
- **The evidence has moved toward the middle-level claim since Panksepp died**, from outside both
  camps: hypothalamic **line attractors** encoding intensity and persistence of an affective
  state (Nature 2024); conserved **biphasic** dynamics with a ketamine dissociation of the
  persistent trace, humans and mice (Science 2025); decoding results "incompatible with theories
  postulating that specific emotions emerge from the neural coding of valence and arousal"
  (Kragel & LaBar, TiCS 2016).
- **The real disagreement is narrow.** Both camps put coordinated pattern generators in
  hypothalamus and PAG; they disagree on whether activity there *constitutes felt affect* or
  reports it. The structural claim of a distinct mid-level stage is not actually contested; the
  name for what happens there is.
- **The seven systems are a design vocabulary, not an empirical count.** Never derived from a
  dimensional analysis; the ANPS instrument tests six (LUST dropped), fails its own factor
  structure (TLI .752 vs .90), and dimensional counts in general are stopping-rule artifacts
  (Lin et al. 2025: 27 vs 3 on the same stimuli). The curator conceded this before the review
  ran, and the review confirms him.
- **Substrate**: hypothalamus for state, PAG for integrated action/autonomic patterns; in our
  mapping "early" means input-to-the-reconstruction, which is the opposite end of the arrow from
  the neuroscientist's "output" — do not collapse the two senses.
- **The reconciliation position** (basic emotion theories describe emotion; constructed emotion
  describes feeling) has a name (van Heijst, Kret & Ploeger), allies on both flanks (Davis &
  Montag say it almost verbatim from the Panksepp side), and a sixteen-author Barrett rejection.
  **Argue it, never assume it.**
- **Nobody has built the three-layer architecture.** Described by Ortony, Norman & Revelle
  (2005), never implemented; MicroPsi converges without citing Panksepp and lacks the mid-level
  primitives; Solms' proposal is unbuilt; the 2025 survey says the combination does not exist.
  The field-level warning to obey when we build: everyone makes a bespoke gridworld and beats a
  strawman, so pre-declare the fair non-emotional baseline (Moerland et al.).

## §3. Affect in text (review, 2026-08-03)

- **No published mapping exists from Panksepp's systems to textual signatures.** The instrument
  built on the systems (ANPS) is self-report. The unclaimed position: primary-process systems
  recovered **from artifacts** rather than self-report, as evidence about a maker rather than a
  respondent.
- **The adjacent solved problem is implicit motive coding** (McClelland): dictionaries agree with
  human coders at r ≈ 0.35-0.54 and cannot keep three motives apart (inter-motive r up to 0.49);
  supervised transformers reach r ≈ 0.85. An unsupervised LLM asked for an affective label is a
  marker-word-class instrument; expect the 0.4 band, and expect the **discriminant failure**
  before the sensitivity failure.
- That failure mode is why **N-AFF-2** exists (pairwise correlation of the eight value weights
  across artifacts must stay under 0.6 for two-thirds of pairs, or the probe is reporting one
  number under eight names).
- The field's own convention drops LUST (social desirability), so the curator's
  justification-based route to it, which does not depend on self-report, is a potential
  contribution, not an idiosyncrasy.
- Live alternative if the eight-way read fails discriminance: **appraisal dimensions**,
  continuous, fewer, with annotation protocols and LLM baselines already published.

## §4. Benchmarks and corpora (survey, 2026-08-05; recreation rows now live in TODO Phase 1)

The recreation-phase gates (ArgRewrite, ScholaWrite, BST, PAN style) moved to `TODO.md` Phase 1
with exact fetched values; this section keeps the field map and the traps.

**Verified records worth knowing**: PAN22 cross-genre authorship verification, best submission
0.587 **against a character-n-gram baseline of 0.600**, the race where SOTA lost to the baseline
and the task is exactly cross-condition identity (access via Aston, slow); PAN20/21 fanfiction AV
0.935/0.9545 (do not confuse the two regimes); word-level co-authorship detection 0.462 F1 vs
0.433 random, and real human-LLM co-writing logs AUC 0.491, the openings where detectors sit at
chance; non-native writers false-positive at 61.2% (the fairness result to cite).

**PAN multi-author style analysis, corrected at source during the recreation (L102, L106, L108,
L109; externally verified L123 — the evaluator re-read verbatim in all three years with no
reconciling reading, the contamination unclaimed anywhere through the 2026 overview, and the
same organizing group's own SPIRE-22 paper documents the identical cross-benchmark leakage
mechanism in a different task family)**: the earlier "PAN26" labels here were wrong (the
editions on disk are 2018/2022-2025).
The metric is POOLED two-class macro-F1 over all pairs, against every overview paper's own
prose (evaluator source + six baseline back-calculations). Winner records: 2024 hard 0.863
(nycu-nlp, three-base-encoder vote; its validation table blends ~16 percent cross-year
memorization from the PAN23 augmentation its own recipe uses); 2025 hard 0.830 (wqd, single
deberta-base, fully specified). Test splits are TIRA-held-back EXCEPT 2025, whose labeled test
split is on disk and verified genuine (printed baselines reproduce to 0.0004) — the one
reachable test-set gate. Contamination map: 2024↔2023 cross-year 15.8 percent of hard
validation pairs; 2024 easy/medium leak within-year (19 percent of easy paragraphs, 13.5
percent of medium pairs) while 2024 hard and all of 2025 are within-year clean (0.2-0.4
percent). Any blended-edition training obeys LESSONS §1d.

**Corpora on disk**: ArgRewrite V.2 (`corpora/public/argrewrite/`, 86 authors × 3 drafts,
purpose-annotated; the construction subtleties are now pinned in FINDINGS L79); PAN
multi-author style 2018/2022/2023/2024/2025 (`corpora/public/pan_style/`, 2025 including its
labeled test split). Verified available: PERSUADE 2.0, ASAP 2.0 (CC BY 4.0), ELLIPSE,
IBM argument quality (best published Pearson 0.52), Essays/Big-Five (~58 macro-F1 field bar).

**Traps, each verified the hard way**: `pan.webis.de/data.html` is unscrapable (use Zenodo record
numbers); PAN15/16 ship tweet IDs, not text; post-2019 profiling is gated; HuggingFace reuploads
can carry licences the upstream never granted (`pandora-big5`); `npc_gzip` reports top-2 accuracy
due to a tie-handling bug; RADAR is 355M with non-commercial weights despite its card; winning
PAN repos often ship **no license file** at all. Code worth cloning, still: `ryuryukke/mint` (15
detectors, one harness), `liamdugan/raid`, `StyleDistance/styledistance`, `EleutherAI/mdl`,
`pan-webis-de/pan-code` (their scorer, never ours).
