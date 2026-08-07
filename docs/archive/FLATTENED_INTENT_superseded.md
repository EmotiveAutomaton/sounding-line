# The flattened-intent hypothesis

**Logged 2026-08-03, while the Gate 3 run was still in progress and before any result was read.**
The curator raised it unprompted and chose to log it now precisely so it cannot be used to
reinterpret Gate 3 afterwards. That timing is what makes it evidence rather than commentary, and
the timestamp is the point of this file.

---

## §1. The claim, in the curator's words

> I don't think that it's the case that corporate work necessarily has less decision-making that
> went into it... what actually that means is that their motivation is immediately reconstructable
> and that motivation is always money. That's why corporate work seems soulless. **It's not quite
> the same as why AI work seems soulless, which is that you can't arrive at a motivation.**
>
> It could be that they chose contrasting colors because it would catch your eye which forces you
> to blah blah blah. But the decision making is still potentially quite dense.
>
> Humans can't really take action without intention. It's just that **corporations steal your
> intention and replace it with money.** Always money and basically nothing else... It is a
> flattening of human motivation, and that's why it's so repulsive to artists that live in a world
> of motivation extraction.

---

## §2. Why this matters more than it first appears

**It says the corpus split may be mis-specified.** This project has been treating commercial filler
as *low intent*. The claim is that it is **dense intent with a flattened terminal value** — many
real decisions, all of them instrumentally subordinate to one goal.

If that is right, "Half A vs Half B" is not high-intent vs low-intent. It is:

| | decision density | motivation | invertibility |
|---|---|---|---|
| **individual human** | high | many terminal values, layered | recoverable, multi-level |
| **corporate** | **also high** | **one terminal value** | **immediately recoverable, one level** |
| **machine** | ? | none coherent | **non-invertible** — the wall |

Three categories, not two. And the project has been running a two-category design.

---

## §3. It predicts Gate 2's result — which was recorded before this hypothesis existed

This is the part that gives it force. Gate 2 found, and I reported as a failure:

| artifact | purpose agreement |
|---|---|
| Eurogamer build guide | **1.00** |
| Glad brand page | **1.00** |
| plumber template | 0.67 |
| LocalThunk building his own game | **0.33** |

I read that as *"the probe converges on garbage because the garbage is well-organised — a quality
classifier with extra steps."* **Under this hypothesis it is the instrument working correctly.**
Commercial motivation is immediately reconstructable, so of course independent readings agree. An
individual's layered motivation is not, so readings differ.

**High agreement on commercial work is the predicted signature, not the bug.** F1.2 "reversing" may
have been the measurement succeeding against a mis-specified expectation.

I cannot claim that retrospectively — the hypothesis arrived after. What I can do is state it now,
before Gate 3's numbers, with predictions that can fail.

---

## §4. Predictions, recorded before Gate 3 results are read

If the flattened-intent account is right:

- **F-1.** Half B shows **higher** purpose agreement than Half A, not lower.
- **F-2.** Half B's purpose posterior concentrates on `sell` specifically — not merely on *some*
  purpose, but on a commercial one.
- **F-3.** Half B shows **lower purpose breadth** (normalised entropy of the purpose posterior)
  than Half A. This is the measure I removed from `fit` at Gate 2 for rewarding
  single-purposedness — under this hypothesis, single-purposedness is exactly the signal, and I
  removed the corporate discriminator for behaving like one.
- **F-4.** Half B's decision density is **not** systematically lower than Half A's.
- **F-5.** The machine case is separate and shows **low agreement AND low breadth** — no coherent
  maker-state to converge on, as against a flattened one.

**F-3 is the sharp one.** `purpose_breadth` is already computed and stored for every artifact. If
Half A shows higher breadth than Half B, the corporate discriminator has been sitting in the
results the whole time, demoted to a diagnostic on my reasoning that it "rewards simplicity."

---

## §5. What this would mean for the project

**A better instrument than the one being built.** SPEC §1's framing is *this is not an AI detector,
it is an intent detector.* The flattened-intent account suggests a third thing, and a more useful
one:

> It reports **what a maker's decisions were ultimately for**, and whether that terminal value is
> singular or layered.

That claim is more socially defensible than either detection or intent-density. It never says *a
machine wrote this* and it never says *this is low effort*. It says *every visible decision here
reduces to one aim* — a statement about the artifact, evidenced, and rebuttable.

It also explains the curator's own repulsion response from calibration 01 better than the
acquisition account did: what repels is not incompetence but **the recognition that the motivation
has been flattened** — motivation extraction performed on a reader who reads motivation for a
living.

---

## §6. Cautions

**"Always money and basically nothing else" is stronger than the evidence needs.** The defensible
form is structural: a corporate artifact has a *single terminal value* to which all instrumental
decisions reduce. Whether that value is always money is an empirical claim this project is not
positioned to make, and the instrument should measure *singularity of terminal value*, not
*presence of a profit motive*.

**This cannot rescue Gate 3.** If G3.1 fails, the locked stop condition applies. This hypothesis is
a candidate for a *successor* design, and the card is explicit that any successor requires a corpus
this project has not seen. Re-fitting to the current 51 artifacts would be unfalsifiable.

**F-3 is checkable on existing data**, which is both its strength and its risk. `purpose_breadth`
is already in the Gate 2 output. Checking it is legitimate; treating a confirmation as
establishing the hypothesis would not be, because the corpus has been read many times.

---

## §7. Status

**Hypothesis, logged before results, with five failable predictions.** Not a finding, not a
rescue, and not permitted to alter Gate 3's interpretation. Recorded as **C-22**.
