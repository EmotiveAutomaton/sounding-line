# Empathy as three coupled inference problems

**The curator, 2026-08-04, thought through at work and dictated on return.** Recorded close to
verbatim because it is a **formalisation of the theory that is sharper than anything currently
written down**, including the essay's appendix.

---

## §1. The claim

> I think empathy is effectively a variational inference problem — **three separate variational
> inference problems being solved in parallel, and each one bootstraps the others.** The more
> information you have in one, the easier it is to solve the others. They have relative strengths,
> relative difficulties, but they all help the other.
>
> 1. the extraction of the **proximal goal**
> 2. the extraction of the **process**
> 3. the extraction of the **values / drives**

And what it explains:

> This is why an expert can instantly understand what a novice was thinking as they were making
> something, in a way that another person cannot. This is why being close friends with someone, you
> can read their book and get more of a sense of why they made certain choices. **This is why
> information is passed more easily between people who are close.**

---

## §2. Why this is a correction and not a restatement

**E36 is one edge of the triangle, and the project has been treating it as the whole thing.**

E36 established goal → process *within a single encounter*, and Gate 3's entire primary was built
on it. The triangle says that is one of **six** directed edges, and that whichever vertex you can
reach first is the one you should enter by.

Which is exactly what the curator described doing when reading aloud, before he had this
formalisation:

> I'm trying to find some layer within which I can use my expertise, then use that expertise to
> solve the easy part, and then I use that to get the motivation, and then that I can use to
> reverse-engineer the rest of it that I don't understand. **Is it a three goddamn part process?**

**Three vertices, entered at whichever is cheapest, propagating to the other two.** The
simulation's S-4/S-5 result agrees and quantifies it: reordering cannot change the answer, only the
cost — reverse and anomaly-first both settle ~5% sooner.

**So the loop is not wrong. It is one traversal of a graph, hard-coded.**

---

## §3. What it predicts that nothing here measures

**Prior information on ANY vertex should improve recovery at the others.** That is a manipulable,
testable claim and it has never been run:

- tell a reader the maker's **values** → does process recovery improve?
- tell them the **process** → does goal recovery improve?
- tell them the **goal** → E36 says process improves, and that is the only edge tested

Six edges, one measured. **The other five are unclaimed** — and `EVIDENCE.md` already flags the
one that has been done as the sharpest forward prediction the parent project owns.

It also predicts **closeness is a measurable prior**: two readers, one who knows the maker and one
who does not, on the same artifact. That is a human study, and it is the cleanest form of the claim.

---

## §4. The open question, flagged by its author and not resolved

> I don't know if drives are values. They're probably not on their own... **I'm just saying out
> loud and I haven't thought of before.**

Left open deliberately. The distinction matters because vertex 3 is doing two jobs:

| | |
|---|---|
| **drives** | Panksepp's primary-process systems. Pre-linguistic, conserved, not chosen. |
| **values** | what a maker is willing to give up for what. Chosen, cultural, statable. |

**That is the leaked/emblematic split again, at the values vertex.** `family_v3.yaml` already
carries it for affect. If the same split applies here, vertex 3 is really two vertices and the
triangle is a tetrahedron — which would also explain why `trade_offs` (values as sacrifices) and
`performed_affect` (drives as leakage) have never sat comfortably in the same family.

**Not resolved. Recorded as the sharpest open question in the theory.**

---

## §5. Relative goal diversity — the second thought, and it supplies a mechanism

> When we talk about something having **soul**, what that means is **a variety of motivations**.
> And it tends to travel with expertise — because as processes are baked in with automaticity, you
> lose conscious access to them and they start to be tied more to your **drives**.

**This is a mechanism for why expertise produces soul, and the project did not have one.**

The chain: practice → automaticity → the decision leaves deliberate control → it is now made by
whatever is underneath → **what is underneath is drives** → an expert's artifact therefore carries
more drive-derived variety than a novice's, without the expert choosing that.

Three things follow.

**It inverts C-22 onto one axis with a mechanism at each end.** Flattened intent is *concentrated*
motivation; soul is *diverse* motivation. `purpose_breadth` measures the concentration — and the
simulation validated it at matched density (S-2). **The same measure, read the other way, is a soul
measure.** That was not visible before.

**It explains E43 rather than merely coexisting with it.** Compression removes a decision from the
maker's *report* — and the curator's addition is where the decision *goes*: to the drives. So the
expert cannot say why, and the artifact shows more of what they are, at the same time and for the
same reason.

**And it predicts diversity should rise with expertise while agreement about purpose stays flat** —
because the goal is still one goal; it is the motivational sources feeding it that multiply. That
is a two-measure prediction using quantities that already exist.

---

## §6. The third thought — the interpretability angle, stated as a testable asymmetry

> Finding divergence between lower-level and higher-level activation as an AI processes text...
> **AI text would not trigger that lower-level activation as frequently.**

The prediction, made precise: reading **human** text should produce *more* low-order affective
activation relative to high-order than reading **machine** text does.

That is the leaked/emblematic ratio measured in the reader, and it has a specific reason to work
that the displacement measure lacked: it is a **ratio between two layers of the same reader on the
same text**, so length, register and vocabulary — the three confounds that have killed five
measures — largely cancel.

**Status.** The wall test measured *distance from a resting state* and failed twice. It did **not**
measure the early/late ratio, which is a different quantity and the one the curator actually
proposed. `results/b/VERDICT.md` found affect directions are real at 4× chance and bimodally
distributed across depth — early and late loci with a dead middle — which is the structure this
prediction needs and has not yet been used.

**This is the highest-value untried thing in the project.**

---

## §7. Why these three arrived together

They are one idea seen from three sides.

The triangle says **goal, process and values are mutually bootstrapping.** Goal diversity says
**expertise moves decisions from process into drives**, which is a claim about traffic between two
of the vertices. And the interpretability angle says **a reader instantiates the vertices at
different depths**, low for drives and high for constructed goals.

**Same structure: three levels, coupled, with practice moving mass downward and reading moving it
back up.** Every part of the project that has survived contact with evidence sits somewhere on it.
Every part that died was measuring one vertex with an instrument that could not see the edges.
