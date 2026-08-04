# The accidental ablation: one artifact was never text

**Found mid-run, 2026-08-03, at artifact 34 of 51.** The monitor fired on `valid=0/5` and the
diagnosis is worth more than the defect.

---

## What happened

`b_a8a3e574` is **14,541 characters of undecompressed gzip**, stored as text.

```
'�\x08\x00\x00\x00\x00\x00\x00\x03���v�F� ...'
```

That leading `�\x08\x00...` is a **gzip magic header** — `\x1f\x8b\x08\x00` — decoded as UTF-8
with the undecodable bytes replaced. **44.5% of the file is replacement characters.** It is not
corrupt text. It was never text.

**Fetcher defect:** `fetch/fetcher.py` contains no handling of `Content-Encoding` at all. A server
returned a gzip body and it went into the store verbatim.

Corpus-wide: **2 of 51** artifacts contain replacement characters. The other, `a_470a2a91`, has
three of them in 2,306 characters — ordinary mojibake, harmless.

---

## The handling, which is pre-registered and stays

The Gate 3 card:

> An artifact with fewer than 2 valid samples is **dropped and counted in the report. No retries**:
> retrying biases the sample toward artifacts the model finds easy.

Bounded arm: **0 of 5 valid**, five `ValidationError`s. So it is dropped and counted, and the
corpus becomes n = 50 with the drop reported. **The manifest is locked and is not being repaired
mid-run.** Fixing the fetcher is a separate change for a future corpus.

---

## The accident, and it is the interesting part

**The bounded arm refused all five samples. The free-form arm returned five out of five.**

Free-form output on 14.5KB of binary noise:

| field | value |
|---|---|
| `purpose_agreement` | **0.60** — three of five readings agreed on a purpose |
| `max_depth` | **4** — the deepest level in the family |
| `machine` | 0.33 |
| `purpose_breadth` | 0.48 |
| `named_alternative_rate` | 0.00 |

**A free-form reader given gzip produced a confident, structured reading of a maker's purpose, at
maximum depth, with three of five samples agreeing on what it was for.**

This is SPEC §7's ablation — *does boundedness buy anything* — answered by accident, on the hardest
possible input, and in the direction Gate 0 predicted:

> An unbounded reader asked an open question **will always produce a coherent answer** — for
> anything, including sludge. Free-form intent attribution is not a measurement. It is confident
> fabrication with good grammar.

Written in the README before this run started. **The strongest available demonstration of it was a
fetcher bug.**

### What it is worth, stated honestly

**n = 1**, and unplanned, so it is an anecdote rather than a result. It cannot be cited as G3.3.

But it is an anecdote of a specific and unusual kind: **the two arms were given identical input and
disagreed about whether that input was readable at all.** The bounded arm's schema — evidence spans
that must locate in the artifact, decisions that must name a rejected alternative — could not be
satisfied by noise. Free-form prose had nothing to fail against.

**The one thing it does establish cleanly:** the bounded arm has a failure mode that means
*something*. `valid=0/5` is information. The free-form arm has no such state — it cannot report
that it was handed nothing.

---

## What changes

**Nothing in this run.** The card handles it and the handling is correct.

**For any future corpus:** the fetcher needs `Content-Encoding` handling, and the store needs a
text-plausibility check at write time — a replacement-character ratio above a few percent means the
fetch failed, whatever the HTTP status said.

**And G3.3 should be read with this beside it.** Whatever the planned ablation returns across 50
artifacts, one artifact where the arms disagreed about the existence of readable content is the
cleanest illustration of what the ablation is for.
