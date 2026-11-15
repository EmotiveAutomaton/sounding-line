# IN14 .h1: exact independent replay without large writer-dummy solves

Prospective engineering proposal only. No implementation or human computation
has occurred. Preserve the original dense solve and all original source/test
receipts. This changes the independent numerical implementation only; the person
secondary remains held on its failed nine-world qualification.

## Static finding and size limits

`week6_in14_math_v1.py:104-114` builds the weighted augmented matrix and calls
`numpy.linalg.lstsq(..., rcond=1e-11)` for every independent fit. `evaluate`
visits every panel, and `week6_in14_in16_run_v1.py:109,145-155` repeats this for
all 2,000 draw indices during independent verification, as well as the point
fit. No writer-dummy factorization is cached. Production's four-column fit is
already smaller; it is not the bottleneck identified here.

For panel j and draw b, let I be its writers with positive integer bootstrap
multiplicity, n_i its original retained rows, k=|I| and p the number of slope
terms. Exact allocated dimensions are N by (p+k), N=sum(n_i for i in I).
Multiplicity changes the row weight by sqrt(w_i); it does not replicate rows.
For ordinary carry-over panels p=4 and N=11 times retained pairs. The reach
panel has one retained row per eligible same-valence pair and p=2 plus its
observed second-prompt intercept columns. It must not be assigned p=4 silently.

There is no locally qualified IN14 support-count output yet. The supplied,
unverified all-report metadata `corpus/out/pf_h.txt` lines 4 and 6 reports
1,186 writers with consecutive pairs and 3,346 pairs in [0,10) minutes.
Those precede exact qualification, prompt exclusions and positive-gap filtering.
They give only an illustrative envelope: N=36,806, k<=1,186, p+k<=1,190.
No human source was evaluated to tighten it. The explicit X allocation at that
envelope is 350,393,120 bytes (334.16 MiB), plus 294,448 bytes for y. A second
full matrix copy would bring those two X copies to about 668.32 MiB; this is
not a total-memory cap. LAPACK workspace/copies, dataframe storage, all panel
blocks, interpreter and process overhead remain additional and unmeasured.

At this envelope a QR operation-count comparison is approximately
2*N*(p+k)^2 - 2*(p+k)^3/3 = 1.031e11 floating-point operations per fit,
or 2.062e14 over 2,000 fits of this one panel. The current SVD solve has
order N*(p+k)^2+(p+k)^3 work; the QR number is a scale illustration, not
an exact SVD count or a wall/CPU forecast. Actual draw dimensions and other
panels differ. No silent sample or reduced bootstrap count is proposed.

## Independent construction and unchanged weights

Use each panel's original `raw_blocks`, never production's demeaned blocks,
normal equations or solved coefficients. For each writer independently form
u=ones(n_i)/sqrt(n_i). A Householder reflector H maps u to the first basis
vector. Apply H separately to the raw slope matrix X_i and response y_i,
then remove their first row. This is an orthogonal basis for the within-writer
projection. It is algebraically weighted writer demeaning, implemented without
calling the production mean-subtraction calculation. Handle n_i=1 as a block
with zero remaining rows, retaining its intercept in the rank accounting.

Cache these independent projected rows once per panel. In each draw stack
sqrt(w_i) times the projected rows for exactly the writers with w_i>0, in the
same deterministic order. Solve the resulting (N-k) by p weighted row system
by a separate lstsq/SVD. Do not form production's cross-product matrix and do
not normalize counts by their sum. A writer sampled twice has multiplicity two,
not two new identities or two intercepts. Missing/omitted writers have no rows.
The identical weights apply to X and y. All original rating units, panel
membership, time thresholds, fixed source transformations and bootstrap seed
20261107 remain. No new centering across writers or column standardization.

This costs order N*p^2 per solve plus the small rank calculations. For the
illustrative primary envelope, the projected slope matrix is at most
35,620 by 4, about 1.09 MiB. Cache/storage of raw and transformed panel rows
is still counted. No seconds estimate is claimed without an admitted probe.

## Preserve the augmented matrix rank rule

The old reference accepts only full column rank under the unnormalized
augmented matrix's relative cutoff rcond=1e-11. Checking rank after merely
normalizing the intercept columns would change that rule. The reflector uses
normalized intercepts only to choose an orthogonal basis; the following bound
uses the original column units and multiplicities.

Let A=[X,D] denote the old weighted matrix, with D_i=sqrt(w_i)*ones(n_i)
in writer i's disjoint rows. Let C have raw writer means as its k by p rows,
and let Z=X-D*C. Then Z-transpose*D=0 and

    A = B*T,  B=[Z,D],  T=[[I_p,0],[C,I_k]].
    T_inverse=[[I_p,0],[-C,I_k]].

The singular values of B are those of the projected within-writer matrix Z
and sqrt(w_i*n_i). Therefore, if the within matrix has p nonzero singular values,

    sigma_min(A) >= min(sigma_min(Z), min_i sqrt(w_i*n_i)) / (1+norm(C,F)).
    sigma_max(A) <= norm(A,F).

The first bound follows from sigma_min(B*T)>=sigma_min(B)/norm(T_inverse,2)
and norm(T_inverse,2)<=1+norm(C,2)<=1+norm(C,F). The second is the Frobenius
upper bound. Norm(A,F)^2 is sum_i w_i*(norm(X_i,F)^2+n_i), in original units.
Use only a conservatively separated sufficient proof that the lower bound is
above 1e-11 times the upper bound, allowing roundoff margins. Any missing,
nonfinite, underdetermined, near-cutoff or otherwise unproven case falls back
to the unchanged dense oracle with its exact original rcond and rank test.
Never infer rank deficiency from this sufficient bound: failure to prove rank
means dense fallback, not unsupported. The fallback is also used if the projected
solve fails or would introduce an unsupported/nonfinite result absent in the
old path. Thus the bound controls computation choice only, not scientific support.

The implementation review must make the roundoff margins explicit before tests.
They may only increase dense fallback, never relax the old rank gate. Exact
floating-point bit identity is not promised. Retain the existing independent
comparison tolerance: absolute 1e-7, relative 0, recursively on every saved point,
draw, panel, summary and private preparation value; no tolerance changes after
fixture outcomes. Production's separate matrix_rank(xx,tol=1e-9) is unchanged.

## Versioning, scope and constructed acceptance

Suggested isolated scope: `week6_in14_replay_h1.py` for the reference solver and
retained dense oracle, `week6_in14_math_h1.py` for a copy changing only the
independent branch, and separately named IN14 run/entry wrappers selecting that
copy. Keep the existing common IN14/IN16 runner and all V1 source files untouched;
IN16 and the failed person-correction candidate must not inherit a source change.
A semantic diff must prove identical production/statistical functions, source
selection, output schema, report classification, seeds and all 2,000 draw indices.
Owner chooses the final versioned handler/plan identity before admission.

Before a numerical run, freeze a small constructed selector comparing old dense,
new dense and new projected reference outputs. Cover unequal writer lengths,
nonuniform multiplicities (including omitted and repeatedly sampled writers),
nonzero writer offsets, constant and exactly collinear columns, one-row writers,
insufficient rows, near-rcond singular values, large intercept/mean scaling,
all carry-over terms and shape-minus-mood, and reach panels with varying p.
Require matching rank/refusal decisions and all accepted coefficients at the
unchanged 1e-7 absolute tolerance. Exercise bound-pass and dense-fallback paths;
assert difficult cases actually take fallback. Preserve original tiny planted
and zero panel checks. No human data, outcome-derived tuning, large cost sweep
or rerun of the failed nine-world person calibration is authorized by this note.
