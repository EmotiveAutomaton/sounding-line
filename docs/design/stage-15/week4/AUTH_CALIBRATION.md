# AUTH initial known-answer calibration

Only the original first 100 argumentative pairs from the completed, sealed
[pair allocation](AUTH_PAIRS.md) may be sent. They contain 50 same-writer and
50 different-writer cases in matched prompt blocks. The source remains exact
final-surviving writer-typed text, with the recorded seams and 400-word cap.
Truth comes from recorded writer identity, not an agent's prose judgment.
No demographic, writer, session, prompt or genre metadata enters the request.

DESIGN CHECK: LESSONS 3–5 and CONTROLS 4–7 reread; G220 context retained.
Under a constant uninformative confidence, area under the receiver-operating
curve (AUC) is .5 and fails the .6 gate. Perfectly ordered known identity scores
yield 1 and pass; reversed ordering yields 0 and fails. Source integrity and
format are required under both null and alternative. All result bands are
covered, and ties count one half. This calibrates a reader, not a genre effect.

Ask the approved Haiku model for an integer from 0 (confidently different
writers) to 9 (confidently the same writer), as constrained JSON. Thinking stays
off and the packet's 32-token maximum is unchanged. The prompt explicitly treats
the supplied texts as data and asks for author consistency across different
topics, considering style and recurring expression without equating topic with
identity. No correction or alternative prompt is implemented in this version.

The fixed format floor is 98 valid whole messages out of 100. Invalid messages
are retained as abstentions, never converted into labels. To prevent selective
missing responses from improving discrimination, require the complete-cohort
worst-case AUC to reach .6: an absent positive loses to every negative, an absent
negative defeats every positive, and a pair of absent labels is also a loss.
Report valid-only AUC separately as a diagnostic. This worst-case quantity is a
bound, not imputed provider output. Fifty-by-fifty truth comparisons are all
accounted for. A failed rung permits only the already approved, separately
recorded correction on the frozen fresh hundred; a second failure stops AUTH.

**The case and its check.** Known identity and prompt-matched balanced cases can
test whether this reader distinguishes writers in the declared source. Software
checks cover perfect, constant and reversed scores, missing-response bounds,
ties, schema/stop-reason rejection, exact sample/source binding, altered truth,
budget calculation, uncertain submission and full response coverage.

**The smaller route.** No smaller paid sample or weaker criterion. Actual token
counts must admit this unchanged hundred within AUTH's $1 and campaign's $10.
Reserve through the existing Week 4 guard before the one generation POST. Keep
uncertain submissions reserved; no automatic retry. Retrieve finitely, recompute
all tokens and settle actual usage before any next paid node or phase.

Reserve 120 of the remaining 390 AUTH interface CPU seconds for source binding,
this implementation, targeted tests, request counting and complete replay. All
earlier FIC1 charges remain and the original shared 7,200-second ceiling stays.
No main batch, scientific comparison, new agent or GPU task is admitted here.
