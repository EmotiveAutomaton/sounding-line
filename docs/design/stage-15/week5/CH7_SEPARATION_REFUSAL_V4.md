# CH7 own-player separation refusal

This isolated engineering repair follows the frozen numerical-v3 qualification.
It does not change the unpenalized logistic estimator, columns, source selection,
bootstrap or null count. The original math, handler, bridges, fixtures, design
and failed receipt remain preserved. The owner authorized this repair on
November 13, 2026. Prepared code remains unadmitted.

## DESIGN CHECK

LESSONS 3–5 apply: a finite optimizer stopping point is not proof that an
unpenalized maximum exists. Under overlapping labels the signed-margin linear
program has optimum zero and the original fit proceeds. Under complete or
quasi separation the optimum is positive and the own-player fit is unsupported.
This refusal is required under both a scientific null and an alternative;
it never repairs a scientific result, adds a penalty or discards the player.
An unknown or numerically ambiguous certificate also withholds the null's
calibrated bar and verdict through the original unsupported-fit path.

The preserved first qualification had 17 passing checks and one failure. Its
perfectly separated nuisance example was accepted by the original BFGS
gradient, coefficient-size and information-rank checks. The exact receipt is
the private `ch7-numerical-check-v3/RESULT.json`: 10.78125 native descendant CPU
seconds, 12.062534700147808 wall seconds, no driver exception and all thirty
pins unchanged. The failed expectation is retained, not weakened.

## Explicit certificate

For each nonconstant outcome, after the original column selection and scaling,
form rows `(2*y-1)*x`, each divided by its positive row norm. A separating
direction has all margins nonnegative and at least one positive. Any finite
direction can be scaled into the box `[-1,1]` without changing those signs.
Maximize the sum of margins within that box, subject to every margin being
nonnegative. Its positive optimum detects both complete and quasi separation;
zero is the overlapping-label case. This is a feasibility check, not a new
likelihood or fitted correction.

The successor calls SciPy's HiGHS dual-simplex solver with one native thread,
1e-9 primal and dual feasibility tolerances, and requires optimal status. A
margin below -1e-8 or a nonfinite certificate refuses the fit. A maximum total
margin above 1e-7 is separated; a value between 1e-9 and 1e-7 is numerically
ambiguous and also refuses. A certified value at most 1e-9 permits the unchanged
likelihood fit. Existing constant-outcome boundary probabilities remain explicit
as the original design requires; no interval is inferred from that boundary.

`week5_ch7_math_v3.py` contains this check plus the previously prepared session
reset/rank repairs. `week5_ch7_v3.py` and `week5_sg1_carried_v3.py` bind it without
mutating earlier modules. `week5_ch7_numerical_fixture_v4.py` retains every prior
case, draw, tolerance and independent formula. The nineteen-check successor
suite retains the old acceptance as a reproduction and adds a hand-checkable
quasi-separated example and an overlapping-label example. Source qualification
is not repeated. The same 180-wall/150-CPU/two-thread focused bounds apply.

No real-data mathematical definition is missing or substituted. All prior
native/production gates in `CH7_NUMERICAL_QUALIFICATION_V3.md` remain, including
three complete original constructed worlds, measured whole-run cost, largest
player and cohort peak, complete SG1 and owner admission. The new linear program
adds per-player work whose real-source cost is not yet measured. The smaller
route remains one complete constructed world per counted qualification attempt;
it does not omit separated players from the scientific cohort.
