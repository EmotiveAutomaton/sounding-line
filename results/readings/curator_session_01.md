# Curator reading session 01 — plain text, blind

**2026-08-03.** First session in which the curator and the probe read the same object (C-21).
Slot 01 was read **unsanitised**; slots 02–10 were rebuilt and sanitised after this session began,
for the reason in §0.

---

## §0. The session broke on its second artifact, and the break is a result

The curator stopped at `artifact_02` without reading it:

> I can see things like *writing briefly*, *informal surveys of urls*. I see translations at the
> bottom. I can tell this is that same guy you had me reading yesterday... **And I can tell before
> I even read the words**, which is kind of a problem because it's just the format of it. The next
> line, the fact that the text hits the next line and making it a sort of paragraph makes it shaped
> the same.

It was Paul Graham, *Writing, Briefly*. **Recognition arrived through line shape, ahead of
content** — a hard wrap at a fixed column is an author fingerprint. The first export also drew a
second Graham essay and two artifacts from the Gate 2 calibration set the curator had already read.

Fixed in `report/sanitize.py` and `runners/reexport_for_reading.py`: one artifact per host, nothing
previously read, Wayback banner stripped, translation lists stripped, site name stripped from the
title, and the line shape reflowed. **This breaks C-21's "same bytes" deliberately** — the probe
read the raw extraction, the curator now reads something cleaner, and any disagreement has that gap
inside it.

**A finding rides along.** The archived half of the corpus carries the Wayback Machine's own
chrome — capture counts, timestamps, the origin URL — into the extraction. **The probe reads that
too**, on every archived artifact, which is disproportionately Half B. It was in the input for
Gate 2 and it is in the input for the Gate 3 run now going.

---

## §1. artifact_01 — `lethain.com/migrations/`, read raw

### The curator's reading

**What it was for — multifaceted, and one of the aims is not the maker's.**

> This person has a skill and they're interested in sharing it, and they want to share it in a way
> that's useful. They're kind of telling a story a little bit and dropping little bits of
> information that they think is relevant but is kind of not super relevant... **There's personality
> here.** But it does still feel corporately driven, which is interesting. **This is someone who was
> given a corporate task and then allowed themselves to be a little bit free with it.**

**The mechanism, and it is a sharpening of C-22:**

> Corporations would prefer everything be sanded down **unless that lack of sanding would provide
> value.** It drips personality out in little bits and pieces in safe ways.

**Two voices, and the count is the observation:**

> I can only detect really two voices in this. There's like a corporate layer and there's someone
> who put a lot of personality and even themselves into it. **And I can't detect a third person.**

The engagement prompt at the foot of the piece was read as a third party's addition — *"slapped on
kind of awkwardly... clearly an attempt to grab engagement"* — and identified as such **before**
knowing that a three-author byline had been stripped by extraction. The curator noted this himself:
*"I can't say that there were three people involved... You didn't insert that."*

**Maker present:** yes, clearly.
**Did they meet the goal:** yes. *"I would be interested in responding to this post if I had done
some migrations."*
**Surface over structure:** neither thin. *"Pretty thick on both ends... they relied on that
expertise to be the appeal. Like it was a controlled expertise or controlled personality that was
itself attractive."*
**Decision rejected:** *"I bet they probably got rid of a paragraph here or there that were a
little bit too personal."*

### The unlock answer, which arrived by contradicting itself

Asked whether settling on the purpose unlocked the method, the curator first said no — and then
demonstrated it inside the same breath:

> Maybe I got a little bit better at writing corporate speech by learning how to express myself in
> a safer way. That seems like the kind of thing that I'd be able to extract from this. And
> actually, it's interesting, as I say that, **I note that I was only able to arrive at the fact
> that I could extract that information from the fact that I know why they were choosing to write
> this way.**

That is E36's temporal claim, observed in a human, unprompted: the method became available *after*
the purpose settled. **It was not available to introspection until the purpose was named out loud.**

### The measurement problem the curator identified

> If you want to answer six, then you kind of need to find things that I don't understand and use
> that as the learning process. Otherwise what I'm getting is slight process improvements, little
> bits and pieces here and there, cumulative over time, and it's just hard to notice.

This is **E10** — reader skill caps extraction — pointing the other way. At high expertise the
unlock is real but sub-threshold for report, because the increment is small against an already
comprehensive decoder. It cannot be measured on a corpus where the reader is expert in everything.

**It also stands in direct tension with the earlier instruction** that the corpus be in a field
where the curator has expertise. Both are right and they constrain different measures: *fit* needs
expertise, *unlock* needs partial expertise. No single corpus serves both.

---

## §2. The scale the curator will actually produce

Offered a sort, the curator declined it and named the honest resolution instead:

> I'm not going to be able to sort them in terms of how much I can reconstruct... I will try to
> label all of them as **I can feel the maker** or **I cannot**, and **I think there's a human, but
> I'm not sure.** I think that's about the highest resolution I can be honest about.

Plus a 1–10 rating, integers only — *"if I give it a decimal point then it's going to be just
noise."*

**Taken as given.** Three categories and an integer rating is a coarser instrument than a ranking
and a more honest one, and refusing to emit precision he does not have is the same discipline the
simulation applies to itself: *quote directions and orderings, never multiples.*

---

## §3. Recorded objection

> I'm just consistently concerned about the lack of the ability to derive human-shaped goals or
> human-shaped maker goals. It feels like we don't have any analogs for neural architecture that
> would simplify things down into that space in any way.

Logged as **C-23**, unanswered.
