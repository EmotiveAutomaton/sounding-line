# TR3 approved pre-execution reference correction

The curator approved: “Correct the unrun control; retain the original record.”
This supersedes only the fixed-history permutation clause of
[the original comparison freeze](TR3_COMPARISON_20261027.md). That file and all
completed source plans remain byte-identical. No primary, feature selection,
writer split, secondary contrast, bootstrap count, CPU ceiling or retry limit
changes. The primary and reference statistics have not been executed.

The original clause reassigns a writer's session typing vectors but keeps
history-based eligibility and matches fixed. That is inconsistent with the
rule excluding features the writer typed previously. For example, a feature
absent in session one but typed in session two becomes prior typing when the
vectors are swapped. A fixed eligibility mask can still call it never typed.
This is a flaw in the operator's unrun specification, not a newly observed
carryover result or a failure of the completed count instruments.

For each of the 200 within-writer, within-prompt permutations, reassign each
complete typing vector together with its character denominator. Keep the
observed exposure records and chronology fixed. Then reconstruct earlier
typing, accumulated practice, feature eligibility, all placebo and secondary
matches, and session/writer contrasts from that permuted source. Zero-character
records and unsupported chronology remain in the census; the same support
rules are applied anew. Report support for each reference, and do not replace
an undefined reference value with zero. Reference admission requires all 200
primary values and nonconstant primary permutation support. The paired
bootstrap stays conditional on the real matched gallery, with complete
recipient-writer records resampled together; its scope is not uncertainty in
learning a new dictionary or gathering new donor histories.

Known-answer validation includes a history-swap example that must change
eligibility, alongside exact matched-count, donor chronology, canonical
acceptance and unsupported-row checks. Before corpus inference, a fixed
constructed calibration uses 100 zero-effect worlds and 20 each with positive
and negative planted carryover, all with 20 test writers and four sessions per
writer. The reference and interval counts remain 200 and 2,000 in every world.
The control admits no more than ten positive or negative false routes combined
among the 100 null worlds and requires at least 18 correctly directed routes
among each 20 planted worlds. These are instrument checks with finite Monte
Carlo precision, not human evidence or proof of a universal error guarantee.
Every world is retained. A failed check stops this continuation; no further
automatic repair or renamed retry is authorized.

The constructed worlds use identical feature families/frequency bins, unique
writer-specific exposure features, independent future typing under the null,
and planted later use (or avoidance) of previously exposed features under the
alternatives. Writer and prompt baseline differences are shared by the seen
and placebo arms. Calibration must exercise the actual matching and reference
reconstruction, not only a closed-form shortcut for the final statistic.
Source preparation and comparison support do not themselves satisfy this gate.
