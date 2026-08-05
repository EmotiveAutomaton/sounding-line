# Calibration pass 02 — video games, high-resolution

**Recorded 2026-08-02, before any instrument run.** Eight artifacts read blind by the same curator,
in a domain where they hold high expertise. Companion to `CALIBRATION_01.md`.

Moving to a high-expertise domain worked. The batch-1 readings were confident about *whether* a
maker was present; these are confident about **where in the artifact the maker is**, which is a
different and much more useful resolution.

---

## §1. Artifacts, with the curator's own additions

Three items were directories; the curator selected and reported the specific artifact, which is
what makes them lockable.

| # | artifact | added by curator |
|---|---|---|
| 1 | Fextralife — *Fire Knight Impaler* build guide (full text supplied) | ✓ |
| 2 | MMOExp — Best Elden Ring Builds | |
| 3 | PCGamesN — The best Elden Ring builds | |
| 4a | Build Tier List — landing page | |
| 4b | [Build Tier List — *Best Build Malenia Without Mimic Tear*](https://buildtierlist.com/guides/best-build-malenia-without-mimic-tear.html) | ✓ |
| 5 | Eurogamer — Elden Ring best builds | |
| 6 | [Steam Community guide `3263916537`](https://steamcommunity.com/sharedfiles/filedetails/?id=3263916537) | ✓ |
| 7 | LocalThunk — The Balatro Timeline | |
| 8 | Game Developer — Postmortem: *The Suffering* | |

Item 9 (`monitor.biology.washington.edu`) was not reached. Still unverified.

---

## §2. The readings

**1 — Fextralife build guide.** *"Very definitely written by a human, 100%."* Effort **4**, counting
the whole chain: theorised the build, made it, played it, then wrote it up *"in a rather exhausting
fashion with a whole bunch of links that were manually put in."* The human tell was **suppressed
dithering** — *"They almost divert here and there a few times. They dither. They threaten to dither
and then they stop themselves."*
**Caveat volunteered:** *"there is an expertise wall. This could be from someone who is an expert
and is churning out various builds using a kind of rote response... it might have been more
boilerplate than I'm giving it credit for."*

**2 — MMOExp.** *"Immediately reads like slop to me. The first sentence kicks it out."* Effort
**1–2**. And the sentence that matters most in this document:

> *"None of it's inaccurate. I couldn't even tell you why I can't sense a human here, but I can't.
> I just. I don't get that vibe."*

**3 — PCGamesN.** Someone there, *"but it's sanded down on purpose."* Decided against including
themselves — *"and they failed to do so, actually. They're leaking. And I can see it."* Evidence:
naming a specific YouTuber. Effort **3**; research but no play-testing. Structural note: *"it kind
of starts out heavily, heavily corporate-y, but then it slowly kind of just lets itself go over
time. The further you go, the further you see it."*

**4a — Build Tier List landing page.** *"I don't think I can really extract intentionality from
this."* See §4 — this item produced the batch's most consequential observation.

**4b — Malenia guide (curator-selected).** *"Someone definitely made this."* Decided against
detail; wanted *"an efficient transfer of information... sort of like in an almanac format."*
Evidence cited: the stagger loop, and *"jump R2, critical jump R2, could chain it."* Effort
**3 if vibe-coded, 5 if hand-made** — and the curator could not tell which.

**5 — Eurogamer.** *"It felt rigid in the way that AI would be rigid, but it relaxed as it went
further."* Human confirmed at: *"it doesn't take long before someone mentions Blasphemous Blade in
a conversation about the best build in Elden Ring"* — *"that sentence is something that you'd have
to force an AI to say."* Decided against first person; deliberate third-person distance. Effort
**2**.

**6 — Steam guide (curator-selected).** A person, low expertise, *"kind of just wanting to be part
of the club."* Decided against giving justification — *"I can see their laziness at the end there
and it kind of makes the whole thing less valuable."* Effort **1–2**, *"because they probably
already made it."* Read a systematising signature off the punctuation.

**7 — LocalThunk, Balatro Timeline.** *"Deep, deep human at a five."* Decided against the less
interesting design decisions — selecting for what others could use, apparently on request. Effort:
**3 for the page, 5 for the work it reports.**

**8 — *The Suffering* postmortem.** Human on the first sentence: *"'So began the two-page pitch
document that marked the start of Surreal's development of The Suffering.' That is a human
sentence. No AI would have written that without prompting."* Decided against holding back — with a
hedge: *"the want to report on failure can often have that call where you don't want to mention
the embarrassing piece... they probably did, but I don't think I can tell which."* Effort:
**3 page / 5 work**, and — *"the fact that the work was a five is probably why they made it in the
first place. You kind of want to share the effort."*

---

## §3. F1 — the wall, observed directly

Item 2 is the closest thing this project has to a real-world sighting of its central construct.

E37 found that content on *familiar* features whose maker cannot be reconstructed produces a
signature neither ordinary condition does: **legible and empty**. Not *I cannot parse this* — the
complaint people actually make. The curator's report is that signature, verbatim, including the
part that makes it distinctive: **accuracy is intact, readability is intact, and the maker is
absent.** *"None of it's inaccurate."*

And the inarticulacy is not a weakness of the report, it is part of the finding. The curator
articulated *why* on all seven other artifacts, often at the level of specific sentences. Here,
alone, the cue would not come. A wall that announces itself as a felt absence rather than a
detected feature is exactly what a **non-invertibility** account predicts and what a
surface-feature account does not.

**This is the single most important calibration target in the set.** The instrument must return
low fit on item 2 while the text is fluent, accurate, and topically coherent. If fit tracks any of
those, it is a quality classifier and SPEC §7's first falsifier has fired.

---

## §4. F2 — vibe coding destroyed a cue the curator relied on

From item 4a, unprompted and self-diagnosed:

> *"The problem is that vibe coding makes it so fucking difficult. Because previously, when I was
> looking at a website construction, I would use things like the surface level to indicate how much
> people cared about it. The surface level prettiness of it, basically. Since I can't rely on that
> anymore, it's really kind of tricky."*

**This is E40 in the wild.** The simulation found that optimising the surface cue directly produces
a *third* failure mode — distinct from the crash and from the trust exploit — in which the reader
pays more and gets less. Here a reader reports the mechanism from the inside: a heuristic that
previously carried real information about maker investment has been decoupled from it by cheap
generative tooling, and the reader knows it and cannot replace it.

Three consequences:

- **The instrument is accidentally well-positioned.** Surface quality was never in the family, and
  fit is computed from posterior shape and evidence grounding rather than polish. What was a
  design choice on theoretical grounds is now load-bearing on empirical ones.
- **Human intent-reading is degrading on a schedule.** Whatever "a human reader can do this" meant
  in 2019, it means something weaker now, and the erosion is in a specific, nameable cue. Anyone
  citing older human-baseline work should date it.
- **Calibration data has a shelf life.** These readings are dated 2026 and use a cue set already
  missing one component. Recorded so a future comparison is not confounded by it.

---

## §5. F3 — effort is two quantities, and C-4 changes before it is built

Obligation C-4 was to add `effort` as a fifth dimension. **The curator's own data says one field is
wrong**, and this arrived before implementation.

Items 7 and 8 were both scored the same way, independently:

> *"The effort that went into this specific page was probably like a three... but the work that went
> into it was upwards of a five because it's demonstrating the work of a five. So it's a most-both
> thing sort of."*

Two separate quantities:

| | what it measures | example |
|---|---|---|
| **artifact effort** | work spent making *this object* | LocalThunk writing the timeline: 3 |
| **demonstrated work** | work spent on what the object *reports* | building Balatro: 5 |

Item 1 shows the same split resolving the other way: the Fextralife guide is a **4** only when the
whole chain is counted — theorise, build, play, write up. Score the page alone and it is lower.

And item 8 supplies a **causal link between them**: *"the fact that the work was a five is probably
why they made it in the first place. You kind of want to share the effort."* High demonstrated work
motivates artifact production. If that holds, the two are not independent and the instrument should
not treat them as such.

**Revised C-4: `artifact_effort` and `demonstrated_work` as two ordinal dimensions in family v2.**
Collapsing them would have destroyed the distinction that separates a postmortem from the work it
describes, which is precisely where this project's depth construct lives.

---

## §6. F4 — suppressed intent leaks progressively, and this predicts a chunking effect

Two items, independently, showed the same internal gradient:

- item 3 — *"it kind of starts out heavily, heavily corporate-y, but then it slowly kind of just
  lets itself go over time... The further you go, the further you see it. It's kind of interestingly
  obvious in the middle, but in the beginning, I was unsure."*
- item 5 — *"it felt rigid in the way that AI would be rigid, but it relaxed as it went further."*

Both are professional games media under an editorial register. **The register is strongest at the
opening and decays across the artifact**, and the maker becomes visible in the back half.

**This is a testable structural prediction and the instrument currently cannot see it.** The probe
reads a whole artifact and returns one reading. SPEC §5 defines convergence across *"different
chunks, orderings, seeds, framings"* — and this says chunk position is not exchangeable. Opening
chunks of professionally-edited text should read as lower-intent than closing chunks of the same
artifact, **systematically rather than noisily**.

If true, two things follow. Convergence measured across chunks partly measures this gradient rather
than reader disagreement, which is a confound in the headline measure. And the gradient is itself a
signal: a *machine*-produced artifact has no reason to relax, because there is no suppression to
decay. **Uniform register across an artifact may discriminate where the mean level does not.**

Recorded as a Gate 2 hypothesis. Not built now — but it is the most promising untested idea either
calibration pass produced.

---

## §7. F5 — effort is not readable without provenance

On item 4b the curator could not score effort at all without knowing the tooling: *"if they vibe
coded it, maybe like a three... but if they made it themselves more like a five."*

The artifact underdetermines the answer, and the missing information is **how it was made** — which
is precisely what this instrument refuses to claim (SPEC §1: never a claim about authorship).

So `artifact_effort` is only partially recoverable from text, by construction, and its expected
recovery ceiling is lower than depth's. Recording this now prevents a later null being read as an
instrument failure when it is a definitional limit.

---

## §8. F6 — the curator noticed themselves being the instrument

> *"I find it interesting that I'm using my own architecture to simulate them so much that I can
> feel like I'm making mistakes because of that. I would imagine they spent a lot of effort trying
> to stay on point... That's something I would do were I writing this. And so I might be
> overgeneralizing even, which is part of this model as well, of course."*

The framework's claim is that appreciation *is* inverse reinforcement learning run in wetware
against one's own architecture. The curator reports doing exactly that, notices the failure mode it
implies — projection onto the maker — and flags it against their own interest on their
highest-confidence reading.

Two consequences:

- **Curator readings of artifacts resembling the curator's own work are systematically suspect.**
  Item 1 is flagged. This bears directly on `CANDIDATES.md` §7's conflict of interest: the proposed
  row-6 artifact is a document the curator co-made, and projection there would be total.
- The instrument shares the flaw and cannot self-report it. A model reading an artifact runs its own
  generative process backwards; where the artifact resembles its training distribution, projection is
  invisible. **The curator can flag it; the probe cannot.** That asymmetry is an argument for the
  curator's continued involvement that has nothing to do with accuracy.

---

## §9. My committed predictions, scored

From `CURATION_BATCH_2.md` §6, committed before the batch was sent.

| # | I predicted | curator | verdict |
|---|---|---|---|
| 1 | collective/wiki, no single maker | single human, effort 4 | **wrong** |
| 2 | gold-seller content marketing; *"most likely to split us"* | slop, no human detectable, effort 1–2 | **right**, and it did not split us |
| 3 | real writer, *thin* decisions | real writer leaking through suppression, effort 3 | **partial** — "thin" was too dismissive |
| 4 | *"near-zero intent in prose, real intent in the system"* — flagged as my likeliest error | intent unreadable on the landing page, clearly present one level down | **partial, and interestingly so** |
| 5 | *more* editorial spine than item 3 | effort 2 versus item 3's 3 | **wrong — inverted** |
| 6 | genuine amateur, **high** effort | genuine amateur, effort 1–2 | **wrong — inverted** |
| 7 | real maker, unusually legible | *"deep, deep human at a five"* | **right** |
| 8 | real maker, high depth, names its own cut features | confirmed, plus a hedge about what was withheld | **right** |

**Three clean, two partial, three wrong.** Worth stating plainly: my priors are mediocre, and on
items 5 and 6 they were *inverted*, not merely imprecise.

That is the useful result. **If my priors were good the curator would be redundant**, and the
divergences are where the calibration set earns its cost. Item 1 is the instructive miss — I
reasoned from the *container* (a wiki, therefore many hands) when build guides on that wiki are
individually authored. The instrument will be able to make exactly that error, because it also
cannot see the container.

---

## §10. Obligations arising

| id | obligation | status |
|---|---|---|
| C-4 **revised** | `artifact_effort` **and** `demonstrated_work` as two dimensions, not one | before Gate 1 run |
| C-8 | Record the causal hypothesis: demonstrated work motivates artifact production | recorded |
| C-9 | Chunk-position gradient (F4) as a Gate 2 hypothesis; convergence-across-chunks is confounded by it | Gate 2 |
| C-10 | `artifact_effort` has a definitional recovery ceiling below depth's (F5) — a null there is not an instrument failure | recorded |
| C-11 | Flag curator readings of artifacts resembling the curator's own work; blocks the row-6 self-authored candidate | permanent |
| C-12 | Date the calibration set — the curator's cue set is missing surface-quality as of 2026 (F2) | recorded |
| C-3 | Row 3 re-source: **item 2 is the best specimen found so far**, better than eHow | partially discharged |
