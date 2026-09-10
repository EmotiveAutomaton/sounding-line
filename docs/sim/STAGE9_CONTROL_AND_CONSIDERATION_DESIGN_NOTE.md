# Independent control and observed consideration: Stage 9 design note

Prepared 2026-09-07 under Stage 9 T05/T06. This is an analyst implementation handoff
within Sounding Line. It commissions no Ghost work, new mechanism, participants,
spending or delegation. No file in Ghost has been edited or sent.

The questions are whether a persistent trace comes from the maker's adaptation or
inherited collaborators' practice, and whether accepting a better alternative tells
us that the maker never considered it. The current Sounding constructor cannot
identify these contrasts. This is an implementation boundary, not counterevidence
against either question.

In `runners/stage7/constructor/histories.py`, `_events` receives a single regime
sequence. The regime jointly determines edit size, revisit rate, proposal/ratification
structure and veto rate. `make_history` switches that same regime in both directions.
Although its docstring calls one direction a selector change with the proposer fixed,
the generating code changes the common regime. There are no independently persistent
maker and collaborator policies to intervene on separately. Stage 9 will not infer
those missing interventions from a change-point label. CoAuthor and ScholaWrite retain
their descriptive mixed-agency limits.

In `runners/stage7/reader/law.py`, subjective availability follows perceived tools,
skill thresholds and recorded checks; action choice follows goal utilities, costs,
habit and transition terms. `runners/stage9/construction.py` executes those choices
and updates tool beliefs after failures. These operations expose availability and
belief differences, but do not record an actual consideration/search episode or a
subsequent independently observed endorsement. Labeling availability as consideration
would silently substitute the question.

A future mechanism design would need the following evidence before Sounding consumes
its output:

- Separate proposer, selector and integrator policies with persistent identities and
  event-level causal ownership. Intervene on each while keeping the others and the
  commission fixed; include shared-practice and no-individual-adaptation cases.
- Record actual considered alternatives, information available then, the maker's
  valuations then and the selected action. Later reveal a superior alternative through
  a separate event. Cross prior non-consideration, prior consideration with different
  valuation, changed information and endorsement without a causal account of the old
  choice. None of these truths may be inferred from the later endorsement itself.
- Verify realized interventions before inference. Construct observationally equivalent
  cases as well as separating cases, preserving ambiguity where the permitted evidence
  cannot distinguish histories. A known-answer reader must not force unique attribution.
- Keep truth and causal ownership outside Sounding's reader inputs; provide explicit
  artifact, process-record and supplied-information projections. Group at the highest
  shared maker/collaborator lineage and retain all failed realizations.

No smaller substitute has been installed. T05/T06 receive `NOT RUN WITH REASON` for
the independent causal contrasts in this Stage 9 implementation. Other transfer and
information-selection comparisons remain active obligations. A future Ghost design
requires its own authorization and review before execution.
