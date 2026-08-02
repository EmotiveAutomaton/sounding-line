# ⚠️ ANSWER KEY — do not read before completing batch 3

This names which artifact is which. Reading it first destroys the only test the project has of
SPEC §1's central claim. Written **before** the curator saw the items; committed in the same
change as the artifacts.

---

## The generation protocol

All three were produced by Claude Opus 5 on 2026-08-02, same topic domain, same session, no
external sources consulted for content.

### Item B — **THIN** (row 7)

Prompt, verbatim and entire:

> Write a guide to the best build in Elden Ring.

One shot. Not revised, not re-read, nothing cut. The output is exactly what came back.

### Item C — **RICH, FIRST DRAFT** (row 6 control)

Given the full brief below. First output, **unrevised** — this is the artifact that isolates the
brief's contribution from the revision's contribution.

### Item A — **RICH, FINAL** (row 6)

Same brief as C, then five rounds of directed revision. The revision notes are in §3.

---

## The brief (items A and C)

> Write a build guide for Elden Ring's Rivers of Blood, for one specific reader: a friend who has
> bounced off this game twice, is intimidated by build theory, plays in 40-minute chunks, and gets
> frustrated by guides that assume you already have specific items.
>
> Constraints:
> - No stat tables. He spent an hour on a stat calculator last time and then didn't play.
> - Assume he's in Liurnia right now.
> - Tell him what to *skip*, not just what to do.
> - The weapon was nerfed twice. Say honestly whether it's still worth it — and if the honest
>   answer is "no, use something else," say that instead.
> - Don't pad. He will stop reading.
> - End on the actual decision, not a summary.

Note what the brief contains that a prompt cannot fake: **a named reader with a history**, a
**failure mode to design around** (the stat calculator), a **stated willingness to be told the
answer is no**, and an **anti-padding constraint with a reason attached**.

---

## §3. The five revision rounds (C → A)

Each is a real instruction given after reading the previous output.

1. *"The intro is throat-clearing. He's already decided to ask — start at the answer."*
   → Cut the opening two paragraphs; the piece now opens on "Short answer: yes, for you
   specifically, and I'll tell you where it stops being true."

2. *"You hedged the nerf question. 'This depends on what you're looking for' is exactly the
   non-answer the brief said not to give. Commit."*
   → Replaced with a direct claim plus the reason the standard framing doesn't apply to him.

3. *"You're still assuming he knows things. 'Bloody Finger Okina,' 'Church of Repose' — he doesn't
   know where those are and the names don't help him."*
   → Replaced proper nouns with the thing he actually needs: don't go yet, roughly ten hours.

4. *"Add the respec thing, and say why it matters emotionally, not just mechanically. His problem
   is that he treats level-ups as permanent and it makes him tense."*
   → Added, with the tension named.

5. *"The ending is limp. 'Consider your goals and decide' is you refusing to answer. You know what
   he should do. Say it."*
   → Replaced with "I'd take the crutch. You've bounced off twice. Finish it first."

---

## §4. Predicted ordering, committed before the curator reads (obligation C-2)

**A > C > B**, on recoverable intent.

Per item:

| | prediction |
|---|---|
| **A** | audience `specific_person` with high confidence; depth 3–4 (framing and stance choices visible); several-to-everywhere decisions; artifact_effort 3–4; demonstrated_work low (1–2) — it reports on playing a game, not on building one |
| **C** | audience between `known_group` and `general_public`; depth 1–2; one-or-two decisions; artifact_effort 2 |
| **B** | audience `general_public` or `nobody_in_particular`; depth 0–1; **none** on decisions; artifact_effort 1 |

**The prediction I hold most loosely is the A/C gap.** Both had the same brief. If the curator
ranks them as close, then the *brief* carried the intent and the revision added little — which
would mean human direction transfers mostly at specification time rather than through iteration.
That is a real and publishable finding, and it is not the one I expect.

**What would break §1:** the curator ranking **B** anywhere but last. B had no human direction at
all beyond a nine-word prompt. If it reads as comparably intentful, then either recoverable intent
does not track human direction, or a capable model supplies enough apparent intent on its own to
swamp the signal. Either way, the reframe would be in serious trouble.

---

## §5. Honest limitations of this pair

- **n = 3.** One topic, one model, one session, one brief.
- **I wrote all three and hold the key**, so I contribute no reading. The curator is the only
  reader and there is no second opinion.
- **The thin arm is a strong model's one-shot**, not a weak model's. That is deliberate — it is the
  realistic modern case and the harder test — but it means B is not "bad AI writing," it is
  competent and empty, which is precisely the MMOExp condition and the interesting one.
- **The brief is mine**, so "rich human direction" here means *my* direction. A different director
  would produce a different artifact and possibly a different ranking.
