# The finish line — what the field measures, who holds the record, and where they fail

**2026-08-05.** Every row below was verified by fetching the actual Zenodo record, task page or
dataset card. Where something is unverified it says so.

> *"If it's a race, I want to know what the finish line looks like and who's in the front."*

---

## §1. The race worth entering — PAN22 authorship verification

**This is the headline.** Cross-discourse-type authorship verification: is the same person writing an
email and a text message? 112 authors, four discourse types, 61% of pairs are email-to-text-message.

| | |
|---|---|
| best submission, 2022 | **0.587** |
| **a trivial character-n-gram-distance baseline** | **0.600** |

> **The state of the art lost to the baseline.** Nobody has a method that beats character n-grams on
> this task. Anything at or above 0.60 is genuinely competitive, and that is an extraordinarily low
> bar for a field that scores 0.95 on the easy version.

**And it is the right task for us, not just a soft target.** Same maker, different discourse type,
is precisely the *diversity of conditions* that `AGAINST_IMPOSSIBILITY.md` §1 says values recovery
requires. The field is failing at the exact comparison our framework says is the informative one.

**The access problem is real.** Zenodo record `6337151` has public metadata and **restricted files**;
access goes through Aston University's forensic linguistics databank
(`fold.aston.ac.uk/handle/123456789/17`). **Budget days, not minutes**, and there is no HuggingFace
mirror — a search for PAN22-and-later data found nothing.

**Contrast, so the 0.60 is read correctly:** PAN20/21 fanfiction authorship verification scores
**0.935 / 0.9545**. Do not sanity-check a PAN22 pipeline against those numbers.

## §2. Downloadable right now, no registration

| what | how to get it | scale | metric · best |
|---|---|---|---|
| **PAN20 + PAN21 authorship verification** | Zenodo record `5106099` — one record serves both years | 276k training pairs, 1,600 fandoms; tests 14,311 and 19,999 | mean of AUC, c@1, F1, F0.5u (+Brier from 2021) · **0.935 / 0.9545**, both Boenninghoff |
| same, easier route | HF `nllg/pan2020-authorship-verification` | 15.6 GB, ungated, configs for PAN20 / PAN21 / small | — |
| multi-corpus AV blend | HF `swan07/authorship-verification` | 251,713 pairs across PAN11/13/14/15/20, named entities replaced | — |
| **PAN21 author profiling** (hate-speech spreaders) | Zenodo `5637013` | small | accuracy · **0.790** |
| PAN17 / PAN18 / PAN19 profiling | Zenodo `3745980` / `3746006` / `3692340` | 53 MB / 7 GB / 38 MB | accuracy · 0.860 / 0.820 / 0.881 |
| **the official evaluator code** | `github.com/pan-webis-de/pan-code` — `clef20/` and `clef22/authorship-verification` | active, 733 commits | run our results through *their* scorer, not ours |

## §3. Traps, all verified the hard way

1. **`pan.webis.de/data.html` is dead for scraping.** Client-side rendering; a plain fetch returns
   *"None of our corpora match your filter."* Every `#panXX-` anchor lands there. **Use the Zenodo
   record numbers above.**
2. **One Zenodo record serves PAN20 and PAN21.** An older superseded record (`3716403`) still
   resolves and is what the PAN21 overview paper cites. Use `5106099`.
3. **PAN15 and PAN16 are practically dead.** Their zips are 1–6 MB because they contain **tweet URLs,
   not tweet text**, and the hydration route died with the free Twitter API.
4. **Post-2019 profiling is mostly gated** — 2020, 2022, 2023, 2024 all require a request with
   institution and stated purpose. Open: 2013–2019 and 2021.
5. **`sagteam/author_profiling` on HuggingFace is not PAN** — it is a Russian Yandex.Toloka corpus.
   Easy to grab by mistake.
6. **`nllg/pan2020-authorship-verification-test` is empty.** The card says so. Use the main record.
7. **No author-profiling task exists in 2024, 2025 or 2026.** The line ends in 2023. The recent PAN
   tasks are generative-AI detection, style change detection, detoxification and watermarking.
8. **TIRA** (`tira.io`) is live but serves a forum shell to fetchers, so it is not directly
   scrapable. PAN 2026 requires an account there; registration closes 2026-04-23.

## §4. What this changes

**Our testing environment is not equivalent to the field's, and until it is, none of our numbers are
comparable to anyone's.** That is the honest position and it is fixable this week for the ungated
sets.

**Two things to do in order:**

1. **Pull PAN20/21 through the HuggingFace mirror and run the official evaluator on it.** Not to
   compete — 0.95 is a solved task — but because **it is a positive control at field scale.** If our
   pipeline cannot reproduce a known-good number on a public benchmark with the field's own scorer,
   nothing else we report is trustworthy. This is the same logic as the author-identification gate,
   at a hundred times the sample size.
2. **Request PAN22 access from Aston.** It is the race worth entering, the bar is 0.60, and the task
   is the one our framework says is informative. Slow, so start it now.

**Still outstanding from the main research agent:** style change detection datasets (the
within-document variation task, which is where our veneer claim lives), RAID and HACo-Det
identifiers, and the list of code worth cloning.

---

## §5. ArgRewrite V.2 — fetched, verified, and it is the corpus we specified

**Downloaded and extracted to `corpora/public/argrewrite/`.** 4.6 MB.

    Draft1   86 essays   median 493 words
    Draft2   86 essays   median 562 words
    Draft3   86 essays   median 627 words

    participants with all three drafts:  86

> **Same author, same prompt, same topic, three revision states.** Maker, register and subject are
> held constant *by construction*; only the intent state moves. That is the design
> `docs/design/DWELL_CORPUS.md` specified before we knew this existed.

Also included: 3,238 sentential and 2,596 subsentential revisions, hand-annotated for **revision
purpose** on a 9-way taxonomy split into Surface (word usage, spelling/grammar, organization) and
Content (claim, evidence, reasoning, rebuttal, precision, development). Inter-annotator agreement
0.71–0.92.

**That annotation is the thing to notice.** Their Surface/Content split is our polish/depth split,
labelled by humans, with 5,834 instances. **Nobody has had to guess which is which.**

**The bar, from the paper:** binary Surface-vs-Content F1 **0.93** sentential, **0.90**
subsentential; 9-way fine-grained **0.51 / 0.67** against a majority baseline of 0.37 / 0.38. The
9-way numbers are the ones to beat.

**Two cautions.** Length rises across drafts (493 → 627 words, +27%), so the same length control
applies as everywhere else. And the annotations are `.xlsx` across a per-annotator directory tree,
not a flat table — budget parsing time. The repo also ships an Excel lock file (`~$Annotation_…`)
that will crash a naive glob.

**Every `*.cs.pitt.edu` URL in the literature for this dataset is NXDOMAIN.** The GitHub repo is the
only live source, and the GitHub `/raw/` redirect serves an HTML page — use
`raw.githubusercontent.com` directly.

## §6. Also verified available, not yet fetched

| | id | note |
|---|---|---|
| PERSUADE 2.0 | `github.com/scrosseye/persuade_corpus_2.0` | ~25k student essays, CC BY-NC-SA, test zip password `persuade_test` |
| ASAP 2.0 | `github.com/scrosseye/ASAP_2.0` | 24,278 essays, **CC BY 4.0** — looser licence than PERSUADE, overlaps it by 12,871 |
| ELLIPSE | `github.com/scrosseye/ELLIPSE-Corpus` | ~6,500 essays with six analytic scores |
| IBM argument quality | HF `ibm-research/argument_quality_ranking_30k` | 30,497 args, human quality ratings. **Best published Pearson 0.52** — another weak-SOTA task |
| Essays (Big Five) | HF `jingjietan/essays-big5` | 2,467 stream-of-consciousness essays with OCEAN scores. Field sits at **~58 macro-F1** |

**Dead ends confirmed, so nobody re-walks them:** IBM's argument-quality download page (404, and the
pairwise ArgQ sets have no live source anywhere), myPersonality (withdrawn April 2018; the domain
now fails TLS), PAN15/16 (tweet IDs only), and paperswithcode (redirects away — any doc citing its
leaderboards is stale).

**Licence trap worth stating once:** several HuggingFace reuploads of restricted corpora carry an
uploader-asserted permissive licence that the original terms do not grant — `pandora-big5` is
Apache-2.0-tagged Reddit text whose upstream forbids redistribution. Use the request forms for
anything that ships.
